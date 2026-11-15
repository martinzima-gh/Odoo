from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.investra_instruments.models.instrument import IFRS9_CATEGORY
from odoo.addons.investra_instruments.models.portfolio import (
    DESIGNATION, MANDATORY_BASIS, NATURE, SPPI, SPPI_CATEGORY_NATURES, SPPI_INSTRUMENT_FIELDS, SPPI_STATUS, SPPI_VERSION,
)

APPROVER_GROUP = "investra_entity.group_valuation_approver"
# Portfolio určuje oceňovací kategorii (plán docs/navrh-evidence-nastroju.md, oddíl 1 bod 3, oddíl 3.5).
# Kategorie × obchodní model: AC ⇒ Držet pro inkaso; FVOCI_D ⇒ Inkaso i prodej; FVOCI_E ⇒ Nepoužije se; FVTPL ⇒ cokoli.
CATEGORY_MODEL = {"AC": "hold_to_collect", "FVOCI_D": "hold_collect_sell", "FVOCI_E": "na"}
SPPI_CATEGORIES = {"AC", "FVOCI_D"}
# Po prvním obchodu portfolia tato pole změní jen reklasifikace (mimo rozsah etapy).
LOCKED_PORTFOLIO = ("measurement_category_id", "business_model", "classification_reason_id", "fund_id")
# Stav a schválení zapisují jen tlačítka Schválit a Uzavřít.
STATE_FIELDS = {"state", "approved_by", "approved_on"}
_BUTTON_OK = object()


class InvestraFundPortfolioMaster(models.Model):
    _inherit = "investra.fund.portfolio"

    code = fields.Char(string="Kód", tracking=True)
    measurement_category_id = fields.Many2one(
        "investra.measurement.category", ondelete="restrict", string="Oceňovací kategorie", tracking=True,
        help="Kategorie IFRS 9, kterou portfolio určuje. Zařadit do něj jde jen nástroj, který podle rozhodovacího stromu "
             "IFRS 9 vychází stejně. Po prvním obchodu se nemění.",
    )
    business_model = fields.Selection(selection_add=[("na", "Nepoužije se")], ondelete={"na": "set default"})
    classification_reason_id = fields.Many2one(
        "investra.classification.reason", ondelete="restrict", string="Důvod klasifikace", tracking=True,
    )
    reason_help = fields.Text(related="classification_reason_id.help_text", string="Vysvětlení důvodu")
    strategy_description = fields.Text(string="Strategie portfolia", tracking=True)
    sales_policy_description = fields.Text(string="Pravidla prodejů", tracking=True)
    valid_from = fields.Date(string="Platí od", tracking=True)
    valid_to = fields.Date(string="Platí do", tracking=True)
    state = fields.Selection(
        [("draft", "Návrh"), ("approved", "Schváleno"), ("closed", "Uzavřeno")],
        default="draft", readonly=True, string="Stav", tracking=True,
    )
    approved_by = fields.Many2one("res.users", readonly=True, ondelete="restrict", string="Schválil")
    approved_on = fields.Datetime(readonly=True, string="Schváleno dne")
    review_frequency = fields.Selection(
        [("annual", "Ročně"), ("semiannual", "Pololetně"), ("ad_hoc", "Podle potřeby")], string="Frekvence revize",
    )
    last_review_date = fields.Date(string="Poslední revize")
    next_review_date = fields.Date(string="Příští revize")
    is_locked = fields.Boolean(compute="_compute_lock", string="Uzamčeno")
    lock_date = fields.Date(compute="_compute_lock", string="V užívání od")

    _code_uniq = models.UniqueIndex("(fund_id, code) WHERE code IS NOT NULL", "Fond už má portfolio s tímto kódem.")

    def _compute_lock(self):
        """Zámek z prvního obchodu portfolia; obchod se nemění, jen se čte (sudo: připravovatel nemusí obchody vidět)."""
        ids = [record._origin.id for record in self if record._origin.id]
        first = {}
        if ids:
            first = {portfolio.id: day for portfolio, day in self.env["investra.trade"].sudo()._read_group(
                [("portfolio_id", "in", ids)], ["portfolio_id"], ["trade_date:min"])}
        for record in self:
            record.lock_date = first.get(record._origin.id, False)
            record.is_locked = bool(record.lock_date)

    @api.constrains("measurement_category_id", "business_model")
    def _check_category_model(self):
        models_ = dict(self._fields["business_model"]._description_selection(self.env))
        for portfolio in self:
            required = CATEGORY_MODEL.get(portfolio.measurement_category_id.code)
            if required and portfolio.business_model != required:
                raise ValidationError(self.env._(
                    "Kategorie %s vyžaduje obchodní model %s.", portfolio.measurement_category_id.display_name, models_[required],
                ))

    @api.constrains("valid_from", "valid_to")
    def _check_validity(self):
        for portfolio in self:
            if portfolio.valid_from and portfolio.valid_to and portfolio.valid_to < portfolio.valid_from:
                raise ValidationError(self.env._("Platnost portfolia %s končí dřív, než začíná.", portfolio.display_name))

    def _check_state_write(self, vals):
        if not self.env.su and self.env.context.get("investra_portfolio_button") is not _BUTTON_OK and STATE_FIELDS & set(vals):
            raise UserError(self.env._("Stav portfolia mění jen tlačítka Schválit a Uzavřít."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_state_write(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._check_state_write(vals)
        if not self.env.su and set(LOCKED_PORTFOLIO) & set(vals):
            for portfolio in self.filtered("is_locked"):
                for name in set(LOCKED_PORTFOLIO) & set(vals):
                    field = portfolio._fields[name]
                    if field.convert_to_cache(portfolio[name], portfolio) != field.convert_to_cache(vals[name], portfolio):
                        raise UserError(self.env._(
                            "Po prvním obchodu nejde změnit kategorii, obchodní model ani důvod klasifikace."
                        ))
        result = super().write(vals)
        # Kontrola kompatibility je na zařazení; při změně kategorie nebo modelu portfolia ji spustí portfolio
        # (@api.constrains se při přepočtu kategorie zařazení nespouští, plán oddíl 2).
        if {"measurement_category_id", "business_model"} & set(vals):
            self.classification_ids._check_category_compatibility()
        return result

    # --- schválení a uzavření ---------------------------------------------------------------------------------------

    def _missing_for_approval(self):
        self.ensure_one()
        required = ("code", "measurement_category_id", "classification_reason_id", "assessment", "valid_from")
        return [self._fields[name].string for name in required if not self[name]]

    def _check_approver(self):
        if not self.env.user.has_group(APPROVER_GROUP):
            raise UserError(self.env._("Portfolio schvaluje a uzavírá jen schvalovatel."))

    def action_approve(self):
        self._check_approver()
        for portfolio in self:
            if portfolio.state != "draft":
                raise UserError(self.env._("Schválit jde jen portfolio ve stavu Návrh: %s.", portfolio.display_name))
            missing = portfolio._missing_for_approval()
            if missing:
                raise UserError(self.env._("Před schválením doplňte: %s.", ", ".join(missing)))
        # Zápis jako superuživatel: schvalovatel nemá právo zápisu na portfolio, schválení je jeho jediná změna.
        self.sudo().with_context(investra_portfolio_button=_BUTTON_OK).write({
            "state": "approved", "approved_by": self.env.user.id, "approved_on": fields.Datetime.now(),
        })
        return True

    def action_close(self):
        self._check_approver()
        for portfolio in self.filtered(lambda p: p.state != "closed"):
            portfolio.sudo().with_context(investra_portfolio_button=_BUTTON_OK).write({
                "state": "closed", "valid_to": portfolio.valid_to or fields.Date.context_today(self),
            })
        return True


class InvestraPortfolioClassificationMaster(models.Model):
    _inherit = "investra.portfolio.classification"

    def _compute_category(self):
        """Model „Nepoužije se“ (portfolio FVOCI_E) nezná popisky v investra_instruments; jinak beze změny.

        Pro tento model platí stejný strom jako pro model mimo SPPI (povinně FVTPL, volbou 5.7.5 FVOCI);
        zdůvodnění se skládá stejně jako v investra_instruments, liší se jen řádek (c).
        """
        na = self.filtered(lambda r: r.portfolio_id.business_model == "na")
        super(InvestraPortfolioClassificationMaster, self - na)._compute_category()
        labels = {
            "nature": dict(NATURE), "sppi": dict(SPPI), "version": dict(SPPI_VERSION), "category": dict(IFRS9_CATEGORY),
            "designation": dict(DESIGNATION),
        }
        for record in na:
            nature = record.instrument_nature
            mandatory = record._mandatory(nature, "na", record.sppi)
            computed = record._final(mandatory, record.designation)
            final = record.category_override or computed
            record.mandatory_category, record.computed_category, record.ifrs9_category = mandatory, computed, final
            if not nature:
                record.classification_basis = False
                continue
            lines = [f"(a) Povaha: {labels['nature'][nature]} (typ {record.instrument_id.type_id.name})"
                     + (f"; posouzení: {record.nature_note}" if record.nature_note else "")]
            if record.sppi == "na":
                lines.append("(b) Test SPPI: nehodnotí se")
            else:
                lines.append(f"(b) Test SPPI: {labels['sppi'][record.sppi]}"
                             + (f" ({labels['version'][record.sppi_version]})" if record.sppi_version else "")
                             + (f"; {record.sppi_note}" if record.sppi_note else ""))
            lines.append(f"(c) Obchodní model: Nepoužije se (portfolio {record.portfolio_id.name})")
            reference = MANDATORY_BASIS.get((nature, mandatory), "")
            lines.append(f"(d) Povinná klasifikace: {labels['category'][mandatory]}" + (f" – {reference}" if reference else ""))
            if record.designation == "none":
                lines.append("(e) Určení / volba: žádné")
            else:
                lines.append(f"(e) Určení / volba: {labels['designation'][record.designation]}"
                             + (f"; {record.designation_note}" if record.designation_note else ""))
            if record.category_override:
                lines.append(
                    f"(f) Kategorie IFRS 9: {labels['category'][final]} – RUČNÍ PŘEPSÁNÍ, odchylka od rozhodovacího stromu "
                    f"IFRS 9 (vypočtená: {labels['category'][computed]}); zdůvodnění: {record.override_note or ''}"
                )
            else:
                lines.append(f"(f) Kategorie IFRS 9: {labels['category'][final]}")
            record.classification_basis = "\n".join(lines)

    def _measurement_code(self):
        """Oceňovací kategorie, jak ji zařazení vychází podle rozhodovacího stromu IFRS 9 (včetně určení a volby)."""
        self.ensure_one()
        if self.ifrs9_category == "fvoci":
            return "FVOCI_E" if self.designation == "fvoci_equity" else "FVOCI_D"
        return {"amortised": "AC", "fvtpl": "FVTPL"}.get(self.ifrs9_category)

    # Kontroly navázané na vstupní pole zařazení (plán oddíl 2); při změně SPPI ji spustí nástroj, při změně kategorie
    # nebo modelu portfolio. Platí jen pro portfolio s kategorií: portfolio bez ní se chová jako dosud.
    @api.constrains("portfolio_id", "instrument_id", "instrument_nature", "designation", "category_override")
    def _check_category_compatibility(self):
        Category = self.env["investra.measurement.category"].sudo().with_context(active_test=False)
        sppi_labels = dict(SPPI_STATUS)
        for record in self:
            category = record.portfolio_id.measurement_category_id
            if not category:
                continue
            portfolio, instrument = record.portfolio_id.display_name, record.instrument_id.display_name
            if category.code in SPPI_CATEGORIES and record.instrument_nature == "puttable":
                raise ValidationError(self.env._(
                    "Podílový list s právem odkupu se oceňuje vždy reálnou hodnotou do výsledku; zařaďte ho do portfolia "
                    "FVTPL: %s.", instrument,
                ))
            if category.code in SPPI_CATEGORIES and record.instrument_nature in SPPI_CATEGORY_NATURES:
                status = record.instrument_id.sppi_status
                if status == "fail":
                    raise ValidationError(self.env._(
                        "Nástroj s nesplněným testem SPPI nelze zařadit do portfolia %s. Zařaďte ho do portfolia FVTPL.", portfolio,
                    ))
                if status != "pass":
                    raise ValidationError(self.env._(
                        "Portfolio %s vyžaduje u nástroje splněný test SPPI; nástroj %s ho má %s.",
                        portfolio, instrument, sppi_labels.get(status, status),
                    ))
            if category.code == "FVOCI_E" and record.designation != "fvoci_equity":
                raise ValidationError(self.env._(
                    "Do portfolia FVOCI kapitálových nástrojů patří jen kapitálový nástroj s volbou podle IFRS 9 5.7.5."
                ))
            derived = record._measurement_code()
            compatible = record.ifrs9_category == category.ifrs9_category and (
                category.code not in CATEGORY_MODEL or derived == category.code
            )
            if not compatible:
                derived_name = Category.search([("code", "=", derived)], limit=1).display_name or derived
                raise ValidationError(self.env._(
                    "Nástroj %(n)s vychází podle IFRS 9 jako %(c)s, portfolio %(p)s je %(k)s. "
                    "Zařaďte ho do portfolia s kategorií %(c)s.",
                    n=instrument, c=derived_name, p=portfolio, k=category.display_name,
                ))


class InvestraInstrumentPortfolioCheck(models.Model):
    _inherit = "investra.instrument"

    def write(self, vals):
        result = super().write(vals)
        # Zařazení přebírá SPPI jako uložené pole; kompatibilitu s kategorií portfolia je potřeba ověřit znovu.
        if SPPI_INSTRUMENT_FIELDS & set(vals):
            self.classification_ids._check_category_compatibility()
        return result
