from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

CZ_CODE = "CZ"
APPROVER_GROUP = "investra_entity.group_valuation_approver"


class InvestraCounterpartyProfile(models.Model):
    """Rozšíření profilu protistrany o detailní ESA kód, odvozené údaje a potvrzení verze (plán 3.3)."""

    _inherit = "investra.counterparty.profile"

    # Povinnost ESA kódu je jen ve formuláři (view), ne v databázi: profily založené dříve ESA kód nemají.
    esa_code_id = fields.Many2one("investra.esa.code", "Kód sektoru ESA", ondelete="restrict", index=True, tracking=True)
    resident_status = fields.Selection(related="esa_code_id.residency", string="Rezidentství", store=True)
    issuer_type_id = fields.Many2one(
        related="esa_code_id.aggregate_sector_id", string="Typ emitenta", store=True, index=True)
    eu_status = fields.Selection([
        ("cz", "Česko"), ("eu", "EU"), ("eea", "EHP mimo EU"), ("non_eu", "Mimo EU"), ("unknown", "Neznámý"),
    ], "Region", compute="_compute_eu_status", store=True)
    derivation_note = fields.Char("Odvození", compute="_compute_derivation_note")
    review_state = fields.Selection(
        [("draft", "Ke kontrole"), ("reviewed", "Zkontrolováno")], "Stav kontroly",
        default="draft", required=True, copy=False, tracking=True)
    reviewed_by = fields.Many2one("res.users", "Zkontroloval", readonly=True, copy=False)
    reviewed_on = fields.Date("Zkontrolováno dne", readonly=True, copy=False)
    change_reason = fields.Char("Důvod změny", tracking=True)
    source = fields.Selection(
        [("manual", "Ručně"), ("import", "Import"), ("lei", "LEI"), ("sdat", "SDAT")], "Zdroj", default="manual")
    is_latest = fields.Boolean("Aktuální verze", copy=False, index=True)

    # --- odvozené údaje ---------------------------------------------------------------------------------------------

    def _eu_status_at(self, day):
        """Region emitenta k datu podle země profilu a členství zemí (ne podle ESA kódu)."""
        self.ensure_one()
        country = self.country_id
        if not country:
            return "unknown"
        if country.code == CZ_CODE:
            return "cz"
        memberships = self.env["investra.country.group.membership"].sudo().search([
            ("country_id", "=", country.id), ("valid_from", "<=", day),
            "|", ("valid_to", "=", False), ("valid_to", ">=", day),
        ])
        groups = set(memberships.mapped("group"))
        for group in ("eu", "eea"):
            if group in groups:
                return group
        return "non_eu"

    @api.depends("country_id")
    def _compute_eu_status(self):
        today = fields.Date.context_today(self)
        for profile in self:
            profile.eu_status = profile._eu_status_at(today)

    @api.depends("esa_code_id", "country_id", "eu_status")
    def _compute_derivation_note(self):
        labels = dict(self._fields["eu_status"].selection)
        for profile in self:
            if not profile.esa_code_id:
                profile.derivation_note = False
                continue
            region = (
                self.env._("region ze země %(country)s a členství: %(region)s",
                           country=profile.country_id.name or "?", region=labels.get(profile.eu_status, "?"))
            )
            profile.derivation_note = self.env._(
                "Odvozeno z ESA %(code)s; %(region)s", code=profile.esa_code_id.code, region=region)

    @api.onchange("esa_code_id")
    def _onchange_esa_code_id(self):
        sector = self.esa_code_id.esa2010_sector_id
        if sector:
            self.sector_id = sector

    # --- kontroly ---------------------------------------------------------------------------------------------------

    @api.constrains("esa_code_id", "country_id")
    def _check_esa_country(self):
        for profile in self:
            code = profile.esa_code_id
            if not code or code.any_country or not profile.country_id:
                continue
            is_cz = profile.country_id.code == CZ_CODE
            if code.residency == "r" and not is_cz:
                raise ValidationError(self.env._(
                    "ESA kód %s je pro rezidenty; země emitenta musí být Česká republika.", code.code))
            if code.residency == "nr" and is_cz:
                raise ValidationError(self.env._(
                    "ESA kód %s je pro nerezidenty; země emitenta nesmí být Česká republika.", code.code))

    @api.constrains("lei")
    def _check_lei_unique(self):
        for profile in self.filtered("lei"):
            other = self.sudo().search(
                [("lei", "=", profile.lei), ("partner_id", "!=", profile.partner_id.id)], limit=1)
            if other:
                raise ValidationError(self.env._("LEI %s už má protistrana %s.", profile.lei, other.partner_id.display_name))

    @api.constrains("esa_code_id", "change_reason", "partner_id", "valid_from")
    def _check_change_reason(self):
        # Jen u verzí s ESA kódem: starší profily bez ESA kódu se zakládaly bez důvodu změny.
        for profile in self.filtered("esa_code_id"):
            if profile.change_reason:
                continue
            earlier = self.sudo().search_count([
                ("partner_id", "=", profile.partner_id.id), ("id", "!=", profile.id),
                ("valid_from", "<", profile.valid_from)])
            if earlier:
                raise ValidationError(self.env._(
                    "Protistrana %s už má dřívější verzi údajů; doplňte důvod změny.", profile.partner_id.display_name))

    # --- zápis, zámek potvrzené verze, příznak aktuální verze -------------------------------------------------------

    @api.model
    def _sector_from_esa(self, esa_code):
        sector = esa_code.esa2010_sector_id
        if not sector:
            raise ValidationError(self.env._(
                "ESA kód %s nemá přiřazený sektor ESA 2010; zadejte sektor ručně.", esa_code.code))
        return sector.id

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [dict(vals) for vals in vals_list]
        for vals in vals_list:
            if vals.get("esa_code_id") and not vals.get("sector_id"):
                vals["sector_id"] = self._sector_from_esa(self.env["investra.esa.code"].browse(vals["esa_code_id"]))
        records = super().create(vals_list)
        records._refresh_latest(records.partner_id.ids)
        return records

    def write(self, vals):
        if not self.env.su and set(vals) - {"is_latest"} and self.filtered(lambda p: p.review_state == "reviewed"):
            raise UserError(self.env._(
                "Potvrzenou verzi nejde změnit. Založte novou verzi s datem „Platí od“ a důvodem změny."))
        if vals.get("esa_code_id") and not vals.get("sector_id"):
            vals = dict(vals, sector_id=self._sector_from_esa(self.env["investra.esa.code"].browse(vals["esa_code_id"])))
        partner_ids = self.partner_id.ids if {"partner_id", "valid_from"} & set(vals) else []
        res = super().write(vals)
        if partner_ids:
            self._refresh_latest(partner_ids + self.partner_id.ids)
        return res

    def unlink(self):
        if not self.env.su and self.filtered(lambda p: p.review_state == "reviewed"):
            raise UserError(self.env._("Potvrzenou verzi nejde smazat."))
        partner_ids = self.partner_id.ids
        res = super().unlink()
        self._refresh_latest(partner_ids)
        return res

    @api.model
    def _refresh_latest(self, partner_ids):
        """Nejnovější verze (největší „Platí od“) každé z protistran dostane is_latest, ostatní ne."""
        profiles = self.sudo().search([("partner_id", "in", list(set(partner_ids)))], order="valid_from desc, id desc")
        latest, seen = profiles.browse(), set()
        for profile in profiles:
            if profile.partner_id.id not in seen:
                seen.add(profile.partner_id.id)
                latest |= profile
        (profiles - latest).filtered("is_latest").write({"is_latest": False})
        latest.filtered(lambda p: not p.is_latest).write({"is_latest": True})

    # --- potvrzení verze --------------------------------------------------------------------------------------------

    def action_review(self):
        if not self.env.user.has_group(APPROVER_GROUP):
            raise UserError(self.env._("Verzi údajů protistrany potvrzuje jen schvalovatel."))
        for profile in self:
            if not profile.esa_code_id:
                raise UserError(self.env._("Před potvrzením doplňte: %s.", self.env._("kód sektoru ESA")))
        # Zápis jako superuživatel: schvalovatel nemá právo zápisu na profil, potvrzení je jeho jediná změna.
        self.sudo().filtered(lambda p: p.review_state == "draft").write({
            "review_state": "reviewed", "reviewed_by": self.env.user.id, "reviewed_on": fields.Date.context_today(self)})
        return True


class InvestraCountryGroupMembership(models.Model):
    _inherit = "investra.country.group.membership"

    def _recompute_profile_regions(self, countries):
        profiles = self.env["investra.counterparty.profile"].sudo().search([("country_id", "in", countries.ids)])
        self.env.add_to_compute(profiles._fields["eu_status"], profiles)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._recompute_profile_regions(records.country_id)
        return records

    def write(self, vals):
        countries = self.country_id
        res = super().write(vals)
        self._recompute_profile_regions(countries | self.country_id)
        return res

    def unlink(self):
        countries = self.country_id
        res = super().unlink()
        self._recompute_profile_regions(countries)
        return res
