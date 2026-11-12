from datetime import date

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .instrument import IFRS9_CATEGORY, VALUATION_METHOD


# Rozhodovací strom IFRS 9 podle dodatku plánu docs/navrh-klasifikace-ifrs9.md; body 1–5 ověřil uživatel 11. 11. 2026
# vůči IFRS přijatým EU. Zařazení drží odděleně: (a) povahu nástroje, (b) test SPPI, (c) obchodní model,
# (d) povinnou klasifikaci, (e) určení nebo volbu a (f) výslednou kategorii se zdůvodněním.
BUSINESS_MODEL = [
    ("hold_to_collect", "Držet pro inkaso"),
    ("hold_collect_sell", "Držet pro inkaso i prodej"),
    ("fair_value", "Řízení na reálnou hodnotu"),
    ("trading", "Obchodování"),
]
SPPI_MODELS = {"hold_to_collect", "hold_collect_sell"}
NATURE = [
    ("debt", "Dluhový nástroj"),
    ("equity", "Kapitálový nástroj (IAS 32.11)"),
    ("puttable", "Podílový list s právem odkupu / závazek emitenta"),
    ("derivative", "Derivát"),
    ("participation", "Účast (dceřiný, přidružený, společný podnik)"),
]
# Povaha podle druhu typu nástroje; podílový list otevřeného fondu se bere jako puttable (IAS 32 16A–16D), dokud účetní
# neposoudí jinak.
NATURE_BY_KIND = {
    "bond": "debt", "loan": "debt", "deposit": "debt", "repo": "debt",
    "equity": "equity", "other_holding": "equity", "fund": "puttable",
    "derivative": "derivative", "participation": "participation",
}
# Povahy, u nichž se hodnotí SPPI: pro držitele dluhový nástroj (podílový list s právem odkupu typicky SPPI nesplní).
SPPI_NATURES = {"debt", "puttable"}
SPPI = [("pass", "Splněn"), ("fail", "Nesplněn"), ("na", "Nehodnotí se")]
SPPI_VERSION = [
    ("pre_2025_1047", "IFRS 9 před novelou (EU) 2025/1047"),
    ("eu_2025_1047", "IFRS 9 ve znění nařízení (EU) 2025/1047"),
]
# Novela klasifikace a oceňování je povinná od prvního účetního období začínajícího 1. 1. 2026 nebo později
# (nařízení Komise (EU) 2025/1047; ověřeno ze sekundárního zdroje, EUR-Lex nedostupný).
AMENDMENT_FROM = date(2026, 1, 1)
DESIGNATION = [
    ("none", "Žádné"),
    ("fvo", "FVTPL určením (IFRS 9 4.1.5)"),
    ("fvoci_equity", "FVOCI kapitálového nástroje (IFRS 9 5.7.5)"),
]
MANDATORY_BASIS = {
    ("debt", "amortised"): "IFRS 9 4.1.2", ("debt", "fvoci"): "IFRS 9 4.1.2A", ("debt", "fvtpl"): "IFRS 9 4.1.4",
    ("puttable", "amortised"): "IFRS 9 4.1.2", ("puttable", "fvoci"): "IFRS 9 4.1.2A",
    ("puttable", "fvtpl"): "IFRS 9 4.1.4; pro držitele není kapitálovým nástrojem (IAS 32 16A–16D), volba 5.7.5 není",
    ("equity", "fvtpl"): "IFRS 9 4.1.4", ("derivative", "fvtpl"): "IFRS 9 4.1.4 (držen k obchodování)",
    ("participation", "fvtpl"): "IFRS 10.31 (investiční jednotka), IAS 28.18",
}
# Pole zařazení, na kterých stojí zaúčtované hodnoty a jejich zdůvodnění; po prvním obchodu je změní jen reklasifikace.
LOCKED_CLASSIFICATION = {
    "portfolio_id", "instrument_id", "valid_from", "instrument_nature", "nature_note", "sppi", "sppi_note", "sppi_version",
    "designation", "designation_note", "category_override", "override_note", "valuation_method", "role_id",
}
# Ruční kategorii zapisuje jen krok podle schvalovací matice (rozhodnutí 2026-11-11); hodnotu nejde poslat přes API.
_OVERRIDE_OK = object()
COMPUTED_CLASSIFICATION = {"ifrs9_category", "mandatory_category", "computed_category", "classification_basis"}


class InvestraFundPortfolio(models.Model):
    """Portfolio fondu s jedním obchodním modelem (IFRS 9 B4.1.2: model se určuje za skupinu aktiv)."""

    _name = "investra.fund.portfolio"
    _inherit = ["investra.record.guard", "mail.thread"]
    _description = "Obchodní model fondu"
    _order = "fund_id, sequence, id"
    _book_fields = ("fund_id",)

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    name = fields.Char(required=True, string="Název", tracking=True)
    sequence = fields.Integer(default=10, string="Pořadí")
    business_model = fields.Selection(BUSINESS_MODEL, required=True, default="fair_value", string="Obchodní model", tracking=True)
    assessment = fields.Text(string="Posouzení modelu", tracking=True, help="Kdo a proč obchodní model určil (IFRS 9 B4.1.1).")
    active = fields.Boolean(default=True, string="Aktivní")
    classification_ids = fields.One2many("investra.portfolio.classification", "portfolio_id", string="Zařazení nástrojů")

    _name_uniq = models.Constraint("unique(fund_id, name)", "Fond už má portfolio s tímto názvem.")

    def _has_trades(self):
        return bool(self.env["investra.trade"].sudo().search_count([("portfolio_id", "in", self.ids)], limit=1))

    def write(self, vals):
        if not self.env.su and "business_model" in vals and self._has_trades():
            raise UserError(self.env._(
                "Po prvním obchodu nejde obchodní model portfolia změnit; změna modelu je reklasifikace (IFRS 9 4.4.1), "
                "která zatím není podporovaná."
            ))
        return super().write(vals)

    def unlink(self):
        if self._has_trades():
            raise UserError(self.env._("Portfolio s obchody nejde smazat."))
        return super().unlink()


class InvestraPortfolioClassification(models.Model):
    """Zařazení nástroje v portfoliu fondu s platností od a doložitelným zdůvodněním klasifikace IFRS 9.

    Rozhodnutí 2026-11-09 a 2026-11-11: klasifikace není vlastností sdíleného nástroje, určuje ji obchodní model fondu.
    """

    _name = "investra.portfolio.classification"
    _inherit = ["investra.record.guard", "mail.thread"]
    _description = "Zařazení nástroje"
    _order = "fund_id, portfolio_id, instrument_id, valid_from desc"
    _book_fields = ("portfolio_id",)
    _rec_names_search = ["instrument_id", "portfolio_id"]

    portfolio_id = fields.Many2one("investra.fund.portfolio", required=True, ondelete="restrict", index=True, string="Portfolio")
    fund_id = fields.Many2one(related="portfolio_id.fund_id", store=True, index=True, string="Fond")
    company_id = fields.Many2one(related="portfolio_id.company_id", store=True, index=True)
    instrument_id = fields.Many2one("investra.instrument", required=True, ondelete="restrict", index=True, string="Nástroj")
    instrument_kind = fields.Selection(related="instrument_id.type_id.kind", string="Druh")
    valid_from = fields.Date(required=True, default=fields.Date.context_today, string="Platí od", tracking=True)
    valid_to = fields.Date(readonly=True, string="Platí do", help="Vyplní jen reklasifikace.")
    # (a) povaha nástroje pro IFRS 9
    instrument_nature = fields.Selection(NATURE, required=True, string="Povaha nástroje", tracking=True)
    nature_note = fields.Char(
        string="Posouzení povahy", tracking=True,
        help="Povinné, když se povaha liší od druhu typu (např. podílový list posouzený podle IAS 32 jako kapitálový nástroj).",
    )
    # (b) test SPPI
    sppi = fields.Selection(
        SPPI, required=True, default="na", string="Test SPPI", tracking=True,
        help="Smluvní peněžní toky jsou jen splátky jistiny a úroku (IFRS 9 4.1.2 b). Hodnotí se u dluhových nástrojů a podílových listů.",
    )
    sppi_note = fields.Char(string="Odůvodnění SPPI", tracking=True)
    sppi_version = fields.Selection(SPPI_VERSION, string="Znění IFRS 9 pro SPPI", tracking=True)
    # (c) obchodní model z portfolia
    business_model = fields.Selection(related="portfolio_id.business_model", string="Obchodní model")
    # (d) povinná klasifikace
    mandatory_category = fields.Selection(
        IFRS9_CATEGORY, compute="_compute_category", store=True, string="Povinná klasifikace",
        help="Klasifikace bez určení a volby: plyne z povahy nástroje, testu SPPI a obchodního modelu.",
    )
    # (e) určení nebo volba
    designation = fields.Selection(DESIGNATION, required=True, default="none", string="Určení / volba", tracking=True)
    designation_note = fields.Char(string="Odůvodnění určení", tracking=True)
    # (f) výsledek a zdůvodnění; ruční přepsání je odchylka od rozhodovacího stromu IFRS 9 (rozhodnutí uživatele 2026-11-11)
    category_override = fields.Selection(
        IFRS9_CATEGORY, string="Ruční kategorie", tracking=True,
        help="Přepíše vypočtenou kategorii. Odchylka od rozhodovacího stromu IFRS 9; vyžaduje zdůvodnění a ukáže se v ocenění.",
    )
    override_note = fields.Char(string="Zdůvodnění přepsání", tracking=True)
    computed_category = fields.Selection(
        IFRS9_CATEGORY, compute="_compute_category", store=True, string="Vypočtená kategorie",
        help="Kategorie podle rozhodovacího stromu IFRS 9 po určení / volbě, bez ručního přepsání.",
    )
    ifrs9_category = fields.Selection(
        IFRS9_CATEGORY, compute="_compute_category", store=True, string="Kategorie IFRS 9", tracking=True,
    )
    classification_basis = fields.Text(compute="_compute_category", store=True, string="Zdůvodnění klasifikace", tracking=True)
    valuation_method = fields.Selection(VALUATION_METHOD, required=True, string="Způsob ocenění", tracking=True)
    role_id = fields.Many2one("investra.account.role", required=True, ondelete="restrict", string="Role účtu", tracking=True)
    note = fields.Char(string="Poznámka", tracking=True)
    deviates_from_proposal = fields.Boolean(compute="_compute_deviates", string="Odchylka od návrhu")

    _uniq = models.Constraint("unique(portfolio_id, instrument_id, valid_from)", "Zařazení nástroje k tomuto dni už existuje.")

    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.instrument_id.name} – {record.portfolio_id.name}"

    # --- (d) a (f): klasifikace ----------------------------------------------------------------

    @api.model
    def _mandatory(self, nature, model, sppi):
        """Povinná klasifikace bez určení a volby (IFRS 9 4.1.2, 4.1.2A, 4.1.4)."""
        if nature in SPPI_NATURES and model in SPPI_MODELS and sppi == "pass":
            return "amortised" if model == "hold_to_collect" else "fvoci"
        return "fvtpl"

    @api.model
    def _final(self, mandatory, designation):
        """Výsledná kategorie po určení 4.1.5 nebo volbě 5.7.5."""
        if designation == "fvo":
            return "fvtpl"
        if designation == "fvoci_equity":
            return "fvoci"
        return mandatory

    @api.depends(
        "instrument_nature", "nature_note", "sppi", "sppi_note", "sppi_version", "portfolio_id.business_model",
        "portfolio_id.name", "designation", "designation_note", "instrument_id.type_id", "category_override", "override_note",
    )
    def _compute_category(self):
        labels = {
            "nature": dict(NATURE), "sppi": dict(SPPI), "version": dict(SPPI_VERSION), "model": dict(BUSINESS_MODEL),
            "category": dict(IFRS9_CATEGORY), "designation": dict(DESIGNATION),
        }
        for record in self:
            nature, model = record.instrument_nature, record.portfolio_id.business_model
            mandatory = record._mandatory(nature, model, record.sppi)
            computed = record._final(mandatory, record.designation)
            final = record.category_override or computed
            record.mandatory_category = mandatory
            record.computed_category = computed
            record.ifrs9_category = final
            if not (nature and model):
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
            lines.append(f"(c) Obchodní model: {labels['model'][model]} (portfolio {record.portfolio_id.name})")
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

    # --- návrh -----------------------------------------------------------------------------------

    @api.model
    def _default_nature(self, instrument):
        return NATURE_BY_KIND.get(instrument.type_id.kind, "equity")

    @api.model
    def _default_sppi_version(self, portfolio, valid_from):
        """Znění pro SPPI podle začátku účetního období, do kterého spadá den platnosti."""
        if not (portfolio and valid_from):
            return "eu_2025_1047"
        company = portfolio.fund_id.company_id
        start = company.compute_fiscalyear_dates(fields.Date.to_date(valid_from))["date_from"]
        return "eu_2025_1047" if start >= AMENDMENT_FROM else "pre_2025_1047"

    @api.model
    def _proposal(self, instrument, portfolio, nature, sppi="na", designation="none", override=False, valid_from=None):
        """Návrh způsobu ocenění a role z typu; naběhlá hodnota jen u výsledné kategorie Naběhlá hodnota."""
        kind = instrument.type_id
        final = override or self._final(self._mandatory(nature, portfolio.business_model, sppi), designation)
        if final == "amortised":
            method = "amortised"
        elif kind.valuation_method == "amortised":
            # Dluhový nástroj mimo naběhlou hodnotu se oceňuje modelem (diskontované toky); účetní může změnit.
            method = "model"
        else:
            method = kind.valuation_method
        return {"valuation_method": method, "role_id": self._proposal_role(instrument, kind.role_id, final, valid_from).id}

    @api.model
    def _proposal_role(self, instrument, role, category, valid_from):
        """Účast v reálné hodnotě do výsledku má vlastní roli (účet 413100), ostatní účasti roli participation (413200)
        (rozhodnutí 2026-11-11 a 2026-11-12). Repo podle protistrany doplňuje modul protistran."""
        if role == self.env.ref("investra_entity.role_participation") and category == "fvtpl":
            return self.env.ref("investra_entity.role_participation_fv")
        return role

    def _override_gate(self, funds, record=None):
        """Ruční kategorie podle matice: jeden člověk = zapíše se; čtyři oči = jen žádostí („Ruční kategorie…“)."""
        if self.env.su or self.env.context.get("investra_override") is _OVERRIDE_OK:
            return
        Matrix = self.env["investra.approval.matrix"]
        rule = Matrix._rule("classification_override", funds)
        rule.check_performer(self.env)
        if rule.persons > 1:
            raise UserError(self.env._(
                "Ruční kategorie IFRS 9 vyžaduje podle schvalovací matice potvrzení druhou osobou. "
                "Uložte zařazení bez ní a použijte tlačítko „Ruční kategorie…“."
            ))
        return rule

    def _log_override(self, rule):
        if rule:
            for record in self:
                self.env["investra.approval.matrix"]._log_alone(rule, record)

    def request_category_override(self, category_override, override_note):
        """Žádost o ruční kategorii; po potvrzení (nebo hned u jednoho člověka) ji zapíše."""
        self.ensure_one()
        Matrix = self.env["investra.approval.matrix"]
        label = dict(IFRS9_CATEGORY).get(category_override, category_override or "bez ruční kategorie")
        request = Matrix._gate(
            "classification_override", self, "request_category_override", self.sudo().fund_id,
            {"category_override": category_override, "override_note": override_note},
            summary=self.env._("Ruční kategorie %(cat)s: %(note)s", cat=label, note=override_note or ""),
        )
        if request:
            return request._action_open()
        self.with_context(investra_override=_OVERRIDE_OK).write({
            "category_override": category_override, "override_note": override_note,
        })
        return True

    @api.model_create_multi
    def create(self, vals_list):
        overrides = [vals for vals in vals_list if vals.get("category_override")]
        if overrides:
            portfolios = self.env["investra.fund.portfolio"].sudo().browse([v.get("portfolio_id") for v in overrides])
            rule = self._override_gate(portfolios.fund_id)
        for vals in vals_list:
            if COMPUTED_CLASSIFICATION & set(vals):
                raise UserError(self.env._("Klasifikace se určuje z povahy nástroje, testu SPPI, obchodního modelu a určení."))
            instrument = self.env["investra.instrument"].browse(vals.get("instrument_id"))
            portfolio = self.env["investra.fund.portfolio"].browse(vals.get("portfolio_id"))
            if instrument:
                vals.setdefault("instrument_nature", self._default_nature(instrument))
            if vals.get("sppi", "na") != "na":
                vals.setdefault("sppi_version", self._default_sppi_version(portfolio, vals.get("valid_from") or fields.Date.today()))
            if instrument and portfolio:
                proposal = self._proposal(
                    instrument, portfolio, vals["instrument_nature"], vals.get("sppi", "na"), vals.get("designation", "none"),
                    vals.get("category_override"), vals.get("valid_from") or fields.Date.context_today(self),
                )
                for field, value in proposal.items():
                    vals.setdefault(field, value)
        records = super().create(vals_list)
        if overrides:
            records.filtered("category_override")._log_override(rule)
        return records

    @api.onchange("instrument_id")
    def _onchange_instrument_nature(self):
        if self.instrument_id:
            self.instrument_nature = self._default_nature(self.instrument_id)

    @api.onchange("instrument_id", "portfolio_id", "instrument_nature", "sppi", "designation", "category_override", "valid_from")
    def _onchange_proposal(self):
        if self.sppi == "na":
            self.sppi_version = False
        elif not self.sppi_version:
            self.sppi_version = self._default_sppi_version(self.portfolio_id, self.valid_from)
        if self.instrument_id and self.portfolio_id and self.instrument_nature:
            self.update(self._proposal(
                self.instrument_id, self.portfolio_id, self.instrument_nature, self.sppi, self.designation, self.category_override,
                self.valid_from,
            ))

    @api.depends(
        "instrument_id", "portfolio_id", "instrument_nature", "sppi", "designation", "category_override", "valuation_method", "role_id",
        "valid_from",
    )
    def _compute_deviates(self):
        for record in self:
            if not (record.instrument_id and record.portfolio_id and record.instrument_nature):
                record.deviates_from_proposal = False
                continue
            proposal = record._proposal(
                record.instrument_id, record.portfolio_id, record.instrument_nature, record.sppi, record.designation,
                record.category_override, record.valid_from,
            )
            record.deviates_from_proposal = (
                (record.valuation_method, record.role_id.id) != (proposal["valuation_method"], proposal["role_id"])
            )

    # --- kontroly ----------------------------------------------------------------------------

    @api.constrains(
        "instrument_nature", "nature_note", "sppi", "sppi_note", "sppi_version", "designation", "designation_note",
        "category_override", "override_note", "valuation_method", "portfolio_id", "instrument_id", "valid_from",
    )
    def _check_classification(self):
        """Jen kombinace, které IFRS 9 připouští, a každá volba s odůvodněním (dodatek plánu 2026-11-11)."""
        for record in self:
            name = record.display_name
            nature = record.instrument_nature
            model = record.business_model
            # (a) povaha
            if nature != record._default_nature(record.instrument_id) and not record.nature_note:
                raise ValidationError(self.env._("Povaha nástroje se liší od druhu typu; doplňte posouzení povahy: %s.", name))
            # (b) SPPI
            if nature not in SPPI_NATURES and record.sppi != "na":
                raise ValidationError(self.env._("Test SPPI se hodnotí jen u dluhových nástrojů a podílových listů: %s.", name))
            if nature in SPPI_NATURES and model in SPPI_MODELS and record.sppi == "na":
                raise ValidationError(self.env._(
                    "V modelu Držet pro inkaso nebo Inkaso i prodej musí mít nástroj vyhodnocený test SPPI (IFRS 9 4.1.2): %s.", name,
                ))
            if record.sppi == "na" and record.sppi_version:
                raise ValidationError(self.env._("Znění IFRS 9 se uvádí jen u vyhodnoceného testu SPPI: %s.", name))
            if record.sppi != "na":
                if not (record.sppi_note and record.sppi_version):
                    raise ValidationError(self.env._("Vyhodnocený test SPPI musí mít odůvodnění a znění IFRS 9: %s.", name))
                required = record._default_sppi_version(record.portfolio_id, record.valid_from)
                if required == "eu_2025_1047" and record.sppi_version != required:
                    raise ValidationError(self.env._(
                        "Pro účetní období od 1. 1. 2026 se SPPI posuzuje podle IFRS 9 ve znění nařízení (EU) 2025/1047: %s.", name,
                    ))
            # (e) určení a volba
            if record.designation != "none" and not record.designation_note:
                raise ValidationError(self.env._("Určení nebo volba musí mít odůvodnění: %s.", name))
            if record.designation == "fvo" and record.mandatory_category not in ("amortised", "fvoci"):
                raise ValidationError(self.env._(
                    "Určení do FVTPL (IFRS 9 4.1.5) je jen u nástroje, který by byl v naběhlé hodnotě nebo FVOCI; "
                    "jinak je ve FVTPL sám: %s.", name,
                ))
            if record.designation == "fvoci_equity":
                if nature != "equity":
                    raise ValidationError(self.env._(
                        "Volba FVOCI (IFRS 9 5.7.5) je jen u kapitálového nástroje podle IAS 32.11; podílový list s právem "
                        "odkupu, účast, derivát ani dluhový nástroj ji nemají: %s.", name,
                    ))
                if model == "trading":
                    raise ValidationError(self.env._(
                        "Volba FVOCI (IFRS 9 5.7.5) není možná u nástroje drženého k obchodování: %s.", name,
                    ))
            # (f) ruční přepsání a způsob ocenění podle výsledné kategorie
            if record.category_override:
                if not record.override_note:
                    raise ValidationError(self.env._("Ruční přepsání kategorie musí mít zdůvodnění: %s.", name))
                if record.category_override == record.computed_category:
                    raise ValidationError(self.env._(
                        "Ruční kategorie se shoduje s vypočtenou; přepsání není potřeba: %s.", name,
                    ))
            if (record.ifrs9_category == "amortised") != (record.valuation_method == "amortised"):
                raise ValidationError(self.env._("Naběhlou hodnotou se oceňuje právě kategorie Naběhlá hodnota: %s.", name))

    @api.constrains("portfolio_id", "instrument_id")
    def _check_instrument_fund(self):
        for record in self:
            own = record.instrument_id.fund_id
            if own and own != record.fund_id:
                raise ValidationError(self.env._(
                    "Nástroj %(name)s patří jen fondu %(fund)s; zařadit ho jde jen do jeho portfolia.",
                    name=record.instrument_id.name, fund=own.display_name,
                ))

    @api.constrains("portfolio_id", "instrument_id", "valid_from", "valid_to")
    def _check_overlap(self):
        for record in self:
            others = self.search([
                ("id", "!=", record.id), ("portfolio_id", "=", record.portfolio_id.id), ("instrument_id", "=", record.instrument_id.id),
                "|", ("valid_to", "=", False), ("valid_to", ">=", record.valid_from),
            ])
            if others.filtered(lambda o: not record.valid_to or o.valid_from <= record.valid_to):
                raise ValidationError(self.env._(
                    "Nástroj %s už má v tomto portfoliu zařazení; změna po prvním obchodu je reklasifikace, která zatím není podporovaná.",
                    record.instrument_id.name,
                ))

    def _trades(self):
        return self.env["investra.trade"].sudo().search([
            ("portfolio_id", "in", self.portfolio_id.ids), ("instrument_id", "in", self.instrument_id.ids),
        ]).filtered(lambda t: any(c.portfolio_id == t.portfolio_id and c.instrument_id == t.instrument_id for c in self))

    def write(self, vals):
        if not self.env.su and COMPUTED_CLASSIFICATION & set(vals):
            raise UserError(self.env._("Klasifikace se určuje z povahy nástroje, testu SPPI, obchodního modelu a určení."))
        if not self.env.su and LOCKED_CLASSIFICATION & set(vals) and self._trades():
            raise UserError(self.env._(
                "Po prvním obchodu nejde zařazení změnit; změna je reklasifikace (IFRS 9 4.4.1), která zatím není podporovaná."
            ))
        # Nastavení nebo změna ruční kategorie jde podle matice; zrušení (návrat k rozhodovacímu stromu) ne.
        changed = vals.get("category_override") and self.filtered(lambda r: r.category_override != vals["category_override"])
        rule = changed and self._override_gate(self.sudo().fund_id)
        result = super().write(vals)
        if changed:
            changed._log_override(rule)
        return result

    def unlink(self):
        if self._trades():
            raise UserError(self.env._("Zařazení s obchody nejde smazat."))
        return super().unlink()

    @api.model
    def _valid(self, portfolio, instrument, day):
        """Zařazení nástroje v portfoliu platné k datu, nebo prázdný záznam."""
        return self.sudo().search([
            ("portfolio_id", "=", portfolio.id), ("instrument_id", "=", instrument.id), ("valid_from", "<=", day),
            "|", ("valid_to", "=", False), ("valid_to", ">=", day),
        ], order="valid_from desc", limit=1)


class InvestraFund(models.Model):
    _inherit = "investra.fund"

    portfolio_ids = fields.One2many("investra.fund.portfolio", "fund_id", string="Obchodní modely")

    @api.model_create_multi
    def create(self, vals_list):
        funds = super().create(vals_list)
        # Rozhodnutí 2026-11-11: nový fond dostane portfolio „Hlavní“ s modelem Řízení na reálnou hodnotu.
        # Obchodní model je posouzení fondu; text posouzení je potřeba doplnit (IFRS 9 B4.1.1).
        self.env["investra.fund.portfolio"].sudo().create([{
            "fund_id": fund.id, "name": "Hlavní", "business_model": "fair_value",
            "assessment": "Výchozí portfolio fondu – obchodní model je potřeba posoudit a doložit.",
        } for fund in funds])
        return funds

    def _default_portfolio(self):
        """Jediné aktivní portfolio fondu, jinak prázdný záznam (pak se musí vybrat)."""
        self.ensure_one()
        portfolios = self.env["investra.fund.portfolio"].sudo().search([("fund_id", "=", self.id)])
        return portfolios if len(portfolios) == 1 else portfolios.browse()
