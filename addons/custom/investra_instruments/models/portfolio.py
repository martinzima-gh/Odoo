from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .instrument import IFRS9_CATEGORY, VALUATION_METHOD


BUSINESS_MODEL = [
    ("hold_to_collect", "Držet pro inkaso"),
    ("hold_collect_sell", "Držet pro inkaso i prodej"),
    ("other", "Ostatní – řízení na reálnou hodnotu"),
]
SPPI = [("pass", "Splněn"), ("fail", "Nesplněn"), ("na", "Nehodnotí se")]
DESIGNATION = [
    ("none", "Žádné"),
    ("fvo", "FVTPL určením (IFRS 9 4.1.5)"),
    ("fvoci_equity", "FVOCI kapitálového nástroje (IFRS 9 5.7.5)"),
]
DEBT_KINDS = {"bond", "loan", "deposit", "repo"}
EQUITY_KINDS = {"equity", "fund", "participation", "other_holding"}
# Pole zařazení, na kterých stojí zaúčtované hodnoty; po prvním obchodu je změní jen reklasifikace.
LOCKED_CLASSIFICATION = {
    "portfolio_id", "instrument_id", "valid_from", "ifrs9_category", "valuation_method", "role_id", "sppi", "designation",
}


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
    business_model = fields.Selection(BUSINESS_MODEL, required=True, default="other", string="Obchodní model", tracking=True)
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
    """Zařazení nástroje v portfoliu fondu: kategorie IFRS 9, způsob ocenění a role účtu s platností od.

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
    business_model = fields.Selection(related="portfolio_id.business_model", string="Obchodní model")
    instrument_id = fields.Many2one("investra.instrument", required=True, ondelete="restrict", index=True, string="Nástroj")
    instrument_kind = fields.Selection(related="instrument_id.type_id.kind", string="Druh")
    valid_from = fields.Date(required=True, default=fields.Date.context_today, string="Platí od", tracking=True)
    valid_to = fields.Date(readonly=True, string="Platí do", help="Vyplní jen reklasifikace.")
    sppi = fields.Selection(
        SPPI, required=True, default="na", string="Test SPPI", tracking=True,
        help="Smluvní peněžní toky jsou jen splátky jistiny a úroku (IFRS 9 4.1.2 b). U kapitálových nástrojů a derivátů se nehodnotí.",
    )
    designation = fields.Selection(DESIGNATION, required=True, default="none", string="Určení", tracking=True)
    ifrs9_category = fields.Selection(IFRS9_CATEGORY, required=True, string="Kategorie IFRS 9", tracking=True)
    valuation_method = fields.Selection(VALUATION_METHOD, required=True, string="Způsob ocenění", tracking=True)
    role_id = fields.Many2one("investra.account.role", required=True, ondelete="restrict", string="Role účtu", tracking=True)
    note = fields.Char(string="Zdůvodnění", tracking=True)
    deviates_from_proposal = fields.Boolean(compute="_compute_deviates", string="Odchylka od návrhu")

    _uniq = models.Constraint("unique(portfolio_id, instrument_id, valid_from)", "Zařazení nástroje k tomuto dni už existuje.")

    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.instrument_id.name} – {record.portfolio_id.name}"

    # --- návrh -------------------------------------------------------------------------------

    @api.model
    def _proposal(self, instrument, portfolio, sppi="na", designation="none"):
        """Výchozí kategorie podle druhu nástroje a obchodního modelu (IFRS 9 4.1.1 až 4.1.5, 5.7.5); rozhoduje účetní."""
        kind = instrument.type_id
        model = portfolio.business_model
        if kind.kind in EQUITY_KINDS:
            category = "fvoci" if designation == "fvoci_equity" else "fvtpl"
        elif kind.kind in DEBT_KINDS and sppi == "pass" and designation != "fvo":
            category = {"hold_to_collect": "amortised", "hold_collect_sell": "fvoci"}.get(model, "fvtpl")
        else:
            category = "fvtpl"
        if category == "amortised":
            method = "amortised"
        elif kind.valuation_method == "amortised":
            # Dluhový nástroj mimo naběhlou hodnotu se oceňuje modelem (diskontované toky); účetní může změnit.
            method = "model"
        else:
            method = kind.valuation_method
        return {"ifrs9_category": category, "valuation_method": method, "role_id": kind.role_id.id}

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            instrument = self.env["investra.instrument"].browse(vals.get("instrument_id"))
            portfolio = self.env["investra.fund.portfolio"].browse(vals.get("portfolio_id"))
            if instrument and portfolio:
                proposal = self._proposal(instrument, portfolio, vals.get("sppi", "na"), vals.get("designation", "none"))
                for field, value in proposal.items():
                    vals.setdefault(field, value)
        return super().create(vals_list)

    @api.onchange("instrument_id", "portfolio_id", "sppi", "designation")
    def _onchange_proposal(self):
        if self.instrument_id and self.portfolio_id:
            self.update(self._proposal(self.instrument_id, self.portfolio_id, self.sppi, self.designation))

    @api.depends("instrument_id", "portfolio_id", "sppi", "designation", "ifrs9_category", "valuation_method", "role_id")
    def _compute_deviates(self):
        for record in self:
            if not (record.instrument_id and record.portfolio_id):
                record.deviates_from_proposal = False
                continue
            proposal = record._proposal(record.instrument_id, record.portfolio_id, record.sppi, record.designation)
            record.deviates_from_proposal = (
                (record.ifrs9_category, record.valuation_method, record.role_id.id)
                != (proposal["ifrs9_category"], proposal["valuation_method"], proposal["role_id"])
            )

    # --- kontroly ----------------------------------------------------------------------------

    @api.constrains("ifrs9_category", "valuation_method", "sppi", "designation", "portfolio_id", "instrument_id")
    def _check_classification(self):
        for record in self:
            name = record.display_name
            kind = record.instrument_id.type_id.kind
            category = record.ifrs9_category
            if (category == "amortised") != (record.valuation_method == "amortised"):
                raise ValidationError(self.env._("Naběhlou hodnotou se oceňuje právě kategorie Naběhlá hodnota: %s.", name))
            if kind not in DEBT_KINDS and record.sppi != "na":
                raise ValidationError(self.env._("Test SPPI se hodnotí jen u dluhových nástrojů: %s.", name))
            if category == "amortised" and not (
                kind in DEBT_KINDS and record.sppi == "pass" and record.business_model == "hold_to_collect"
            ):
                raise ValidationError(self.env._(
                    "Naběhlá hodnota je jen u dluhového nástroje se splněným testem SPPI v modelu Držet pro inkaso (IFRS 9 4.1.2): %s.",
                    name,
                ))
            if category == "fvoci":
                if kind in DEBT_KINDS and not (record.sppi == "pass" and record.business_model == "hold_collect_sell"):
                    raise ValidationError(self.env._(
                        "FVOCI dluhového nástroje je jen se splněným testem SPPI v modelu Držet pro inkaso i prodej (IFRS 9 4.1.2A): %s.",
                        name,
                    ))
                if kind not in DEBT_KINDS and record.designation != "fvoci_equity":
                    raise ValidationError(self.env._(
                        "FVOCI kapitálového nástroje je jen s určením podle IFRS 9 5.7.5: %s.", name,
                    ))
            if record.designation == "fvoci_equity" and not (kind in EQUITY_KINDS and category == "fvoci"):
                raise ValidationError(self.env._("Určení podle IFRS 9 5.7.5 je jen u kapitálového nástroje v FVOCI: %s.", name))
            if record.designation == "fvo" and not (kind in DEBT_KINDS and category == "fvtpl"):
                raise ValidationError(self.env._("Určení podle IFRS 9 4.1.5 je jen u dluhového nástroje v FVTPL: %s.", name))

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
        if not self.env.su and LOCKED_CLASSIFICATION & set(vals) and self._trades():
            raise UserError(self.env._(
                "Po prvním obchodu nejde zařazení změnit; změna je reklasifikace (IFRS 9 4.4.1), která zatím není podporovaná."
            ))
        return super().write(vals)

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
        # Rozhodnutí 2026-11-11: nový fond dostane portfolio „Hlavní“ s modelem Ostatní (FVTPL).
        self.env["investra.fund.portfolio"].sudo().create([{
            "fund_id": fund.id, "name": "Hlavní", "business_model": "other", "assessment": "Výchozí portfolio fondu.",
        } for fund in funds])
        return funds

    def _default_portfolio(self):
        """Jediné aktivní portfolio fondu, jinak prázdný záznam (pak se musí vybrat)."""
        self.ensure_one()
        portfolios = self.env["investra.fund.portfolio"].sudo().search([("fund_id", "=", self.id)])
        return portfolios if len(portfolios) == 1 else portfolios.browse()
