import re

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

try:
    from stdnum.isin import is_valid as isin_is_valid
except ImportError:  # pragma: no cover - stdnum je součástí obrazu Odoo
    isin_is_valid = None

APPROVER_GROUP = "investra_entity.group_valuation_approver"
CFI_RE = re.compile(r"^[A-Z]{6}$")
# Po potvrzení klasifikace se tato pole mění jen průvodcem „Změnit klasifikaci“ (plán 3.4).
CONFIRMED_LOCKED = ("ba0088_id", "cfi_code", "isin", "issuer_id")


class InvestraCfiBa0088Map(models.Model):
    """Mapa začátku kódu CFI na druh BA0088; slouží jen k upozornění u nástroje (plán 3.2)."""

    _name = "investra.cfi.ba0088.map"
    _description = "Mapa CFI na BA0088"
    _order = "cfi_prefix"

    cfi_prefix = fields.Char("Začátek CFI", required=True)
    ba0088_id = fields.Many2one("investra.ba0088.code", "Druh CP (BA0088)", required=True, ondelete="restrict")
    valid_from = fields.Date("Platí od")
    valid_to = fields.Date("Platí do")
    source = fields.Char("Zdroj")


class InvestraInstrumentType(models.Model):
    _inherit = "investra.instrument.type"

    ba0088_required = fields.Boolean(
        "Vyžaduje BA0088", default=True,
        help="Typ, u kterého se při potvrzení klasifikace vyžaduje druh cenného papíru podle BA0088.")


class InvestraInstrument(models.Model):
    """Rozšíření nástroje o druh ČNB (BA0088), CFI, doplňkové atributy a potvrzení klasifikace (plán 3.4)."""

    _inherit = "investra.instrument"

    ba0088_id = fields.Many2one(
        "investra.ba0088.code", "Druh ČNB (BA0088)", ondelete="restrict", index=True, tracking=True,
        domain="[('selectable', '=', True)]")
    asset_family = fields.Selection(related="ba0088_id.asset_family", string="Rodina", store=True)
    cfi_code = fields.Char("CFI", tracking=True, help="Šest velkých písmen A–Z (ISO 10962).")
    ba0088_requires_justification = fields.Boolean(related="ba0088_id.requires_justification")
    ba0088_leverage_rule = fields.Selection(related="ba0088_id.leverage_rule")
    ba0088_note = fields.Text("Zdůvodnění druhu", tracking=True)
    leverage_flag = fields.Boolean("Pákový", tracking=True)
    issue_date = fields.Date("Datum emise")
    nominal_value = fields.Monetary("Nominál", currency_field="currency_id")
    coupon_type = fields.Selection([
        ("none", "Bez kupónu"), ("fixed", "Pevný"), ("floating", "Pohyblivý"), ("zero", "Bezkuponový"), ("other", "Jiný"),
    ], "Druh kupónu")
    seniority = fields.Selection([
        ("senior", "Přednostní"), ("subordinated", "Podřízený"), ("at1", "AT1"), ("other", "Jiný"),
    ], "Pořadí pohledávky")
    convertible = fields.Boolean("Vyměnitelný")
    perpetual = fields.Boolean("Bez splatnosti")
    underlying_description = fields.Char("Podkladové aktivum")
    underlying_instrument_id = fields.Many2one(
        "investra.instrument", "Podkladový nástroj", ondelete="restrict", help="Např. dluhopis, ze kterého jsou samostatné kupóny.")
    isin_warning = fields.Char("Upozornění na ISIN", compute="_compute_isin_warning")
    cfi_warning = fields.Char("Upozornění na CFI", compute="_compute_cfi_warning")
    classification_gap = fields.Char("Chybějící údaje klasifikace", compute="_compute_classification_gap")
    master_source = fields.Selection(
        [("manual", "Ručně"), ("import", "Import"), ("lei", "LEI"), ("sdat", "SDAT")], "Zdroj údajů", default="manual")
    review_state = fields.Selection(
        [("draft", "Ke kontrole"), ("reviewed", "Potvrzeno")], "Stav klasifikace",
        default="draft", required=True, copy=False, tracking=True)
    reviewed_by = fields.Many2one("res.users", "Potvrdil", readonly=True, copy=False)
    reviewed_on = fields.Date("Potvrzeno dne", readonly=True, copy=False)

    # --- odvozené údaje a upozornění --------------------------------------------------------------------------------

    @api.depends("isin")
    def _compute_isin_warning(self):
        for instrument in self:
            bad = bool(instrument.isin) and isin_is_valid is not None and not isin_is_valid(instrument.isin)
            instrument.isin_warning = self.env._("ISIN %s nemá platnou kontrolní číslici.", instrument.isin) if bad else False

    @api.depends("cfi_code", "ba0088_id")
    def _compute_cfi_warning(self):
        today = fields.Date.context_today(self)
        maps = self.env["investra.cfi.ba0088.map"].sudo().search([
            "|", ("valid_from", "=", False), ("valid_from", "<=", today),
            "|", ("valid_to", "=", False), ("valid_to", ">=", today)])
        for instrument in self:
            instrument.cfi_warning = False
            if not (instrument.cfi_code and instrument.ba0088_id):
                continue
            matching = maps.filtered(lambda m: instrument.cfi_code.startswith(m.cfi_prefix.upper()))
            if matching and instrument.ba0088_id not in matching.ba0088_id:
                instrument.cfi_warning = self.env._(
                    "CFI %(cfi)s odpovídá druhu %(expected)s, nástroj má druh %(actual)s.",
                    cfi=instrument.cfi_code, expected=", ".join(matching.ba0088_id.mapped("display_name")),
                    actual=instrument.ba0088_id.display_name)

    def _missing_for_confirmation(self):
        """Údaje, které chybí k potvrzení klasifikace (BA0088 podle typu, emitent a splatnost podle BA0088)."""
        self.ensure_one()
        missing = []
        if self.type_id.ba0088_required and not self.ba0088_id:
            missing.append(self.env._("druh ČNB (BA0088)"))
        if self.ba0088_id.requires_issuer and not self.issuer_id:
            missing.append(self.env._("emitent"))
        if self.ba0088_id.requires_maturity and not self.maturity_date and not self.perpetual:
            missing.append(self.env._("splatnost"))
        return missing

    @api.depends("type_id.ba0088_required", "ba0088_id.requires_issuer", "ba0088_id.requires_maturity",
                 "issuer_id", "maturity_date", "perpetual")
    def _compute_classification_gap(self):
        # Posouzení SPPI doplní úkol IM-05; zde jen údaje klasifikace ČNB.
        for instrument in self:
            missing = instrument._missing_for_confirmation()
            instrument.classification_gap = (
                self.env._("Chybí: %s.", ", ".join(missing)) if missing else False)

    # --- kontroly ---------------------------------------------------------------------------------------------------

    @api.constrains("cfi_code")
    def _check_cfi_code(self):
        for instrument in self.filtered("cfi_code"):
            if not CFI_RE.match(instrument.cfi_code):
                raise ValidationError(self.env._("CFI musí mít přesně 6 velkých písmen A–Z: %s.", instrument.cfi_code))

    @api.constrains("ba0088_id", "leverage_flag")
    def _check_leverage(self):
        for instrument in self.filtered("ba0088_id"):
            rule = instrument.ba0088_id.leverage_rule
            if rule == "must_true" and not instrument.leverage_flag:
                raise ValidationError(self.env._("Druh %s vyžaduje zaškrtnutou páku.", instrument.ba0088_id.display_name))
            if rule == "must_false" and instrument.leverage_flag:
                raise ValidationError(self.env._("Druh %s páku nepřipouští.", instrument.ba0088_id.display_name))

    @api.constrains("ba0088_id", "ba0088_note")
    def _check_justification(self):
        for instrument in self.filtered("ba0088_id"):
            if instrument.ba0088_id.requires_justification and not (instrument.ba0088_note or "").strip():
                raise ValidationError(self.env._("Druh %s vyžaduje zdůvodnění.", instrument.ba0088_id.display_name))

    @api.constrains("issue_date", "maturity_date", "nominal_value")
    def _check_issue_attributes(self):
        for instrument in self:
            if instrument.issue_date and instrument.maturity_date and instrument.issue_date > instrument.maturity_date:
                raise ValidationError(self.env._("Datum emise nesmí být po splatnosti: %s.", instrument.name))
            if instrument.nominal_value < 0:
                raise ValidationError(self.env._("Nominál nemůže být záporný: %s.", instrument.name))

    # --- zápis a zámek po potvrzení ---------------------------------------------------------------------------------

    @api.model
    def _normalize_cfi(self, vals):
        if "cfi_code" in vals:
            vals["cfi_code"] = (vals["cfi_code"] or "").strip().upper() or False

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [dict(vals) for vals in vals_list]
        for vals in vals_list:
            self._normalize_cfi(vals)
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        self._normalize_cfi(vals)
        if not self.env.su and set(CONFIRMED_LOCKED) & set(vals):
            normalized = dict(vals)
            self._normalize_identifiers(normalized)
            for instrument in self.filtered(lambda i: i.review_state == "reviewed"):
                for name in set(CONFIRMED_LOCKED) & set(normalized):
                    current = instrument[name].id if name.endswith("_id") else instrument[name]
                    if (current or False) != (normalized[name] or False):
                        raise UserError(self.env._("Klasifikace je potvrzená. Použijte Změnit klasifikaci a uveďte důvod."))
        return super().write(vals)

    # --- potvrzení klasifikace --------------------------------------------------------------------------------------

    def action_confirm_classification(self):
        if not self.env.user.has_group(APPROVER_GROUP):
            raise UserError(self.env._("Klasifikaci nástroje potvrzuje jen schvalovatel."))
        for instrument in self:
            missing = instrument._missing_for_confirmation()
            if missing:
                raise UserError(self.env._("Před potvrzením doplňte: %s.", ", ".join(missing)))
        # Zápis jako superuživatel: schvalovatel nemá právo zápisu na nástroj, potvrzení je jeho jediná změna.
        self.sudo().filtered(lambda i: i.review_state == "draft").write({
            "review_state": "reviewed", "reviewed_by": self.env.user.id, "reviewed_on": fields.Date.context_today(self)})
        return True

    def action_change_classification(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "name": self.env._("Změnit klasifikaci"),
            "res_model": "investra.masterdata.change.wizard", "view_mode": "form", "target": "new",
            "context": {"default_instrument_id": self.id},
        }
