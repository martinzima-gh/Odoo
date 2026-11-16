from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

CZ_CODE = "CZ"
APPROVER_GROUP = "investra_entity.group_valuation_approver"
# Údaje, jejichž změna vrací potvrzený záznam na „Ke kontrole“ (MN-09).
DATA_FIELDS = ("partner_id", "country_id", "sector_id", "esa_code_id", "lei")


class InvestraCounterpartyProfile(models.Model):
    """Rozšíření profilu protistrany o detailní ESA kód, odvozené údaje a kontrolu (plán 3.3). Bez verzí (MN-09):
    změna údaje potvrzeného záznamu vyžaduje důvod změny a vrací stav na „Ke kontrole“."""

    _inherit = "investra.counterparty.profile"

    # Povinnost ESA kódu je jen ve formuláři (view), ne v databázi: profily založené dříve ESA kód nemají.
    esa_code_id = fields.Many2one("investra.esa.code", "Kód sektoru ESA", ondelete="restrict", index=True, tracking=True)
    code_sector_id = fields.Many2one(
        related="esa_code_id.esa2010_sector_id", string="Sektor podle kódu ESA",
        help="Sektor ESA 2010, který určuje zvolený kód. Je-li vyplněný, sektor profilu se z něj doplní a nejde ručně změnit.")
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
    reviewed_by = fields.Many2one("res.users", "Zkontroloval", readonly=True, copy=False, tracking=True)
    reviewed_on = fields.Date("Zkontrolováno dne", readonly=True, copy=False, tracking=True)
    change_reason = fields.Char("Důvod změny", tracking=True)
    source = fields.Selection(
        [("manual", "Ručně"), ("import", "Import"), ("lei", "LEI"), ("sdat", "SDAT")], "Zdroj", default="manual",
        tracking=True)

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

    # --- zápis: změna potvrzeného záznamu ---------------------------------------------------------------------------

    @api.model
    def _vals_with_code_sector(self, vals):
        """Sektor ESA 2010 profilu se doplní z kódu sektoru ESA (MN-06, pozn. 12), i při importu; výslovně zadaný
        sektor se nepřepisuje (formulář ho po výběru kódu posílá už odvozený). Kód bez vazby na sektor: sektor se
        zadá ručně, jinak chyba."""
        if not vals.get("esa_code_id") or vals.get("sector_id"):
            return vals
        code = self.env["investra.esa.code"].browse(vals["esa_code_id"])
        if code.esa2010_sector_id:
            return dict(vals, sector_id=code.esa2010_sector_id.id)
        raise ValidationError(self.env._(
            "ESA kód %s nemá přiřazený sektor ESA 2010; zadejte sektor ručně.", code.code))

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._vals_with_code_sector(dict(vals)) for vals in vals_list])

    def _data_changed(self, vals):
        """Záznamy, u kterých zápis skutečně mění některý z údajů DATA_FIELDS."""
        fields_ = [name for name in DATA_FIELDS if name in vals]
        if not fields_:
            return self.browse()
        return self.filtered(lambda p: any(
            p._fields[name].convert_to_write(p[name], p) != (vals[name] or False) for name in fields_))

    def write(self, vals):
        # Odchylka od stavu před MN-09: potvrzený záznam už není zamčený (nová verze s datem neexistuje). Změna údaje
        # vyžaduje důvod změny a vrací stav na „Ke kontrole“; stará a nová hodnota zůstávají v historii záznamu.
        if vals.get("esa_code_id") and not vals.get("sector_id") and not self.env["investra.esa.code"].browse(
                vals["esa_code_id"]).esa2010_sector_id and len(self) == 1 and self.sector_id:
            vals = dict(vals, sector_id=self.sector_id.id)  # kód bez vazby: stávající sektor zůstává
        vals = self._vals_with_code_sector(vals)
        reopened = self._data_changed(vals).filtered(lambda p: p.review_state == "reviewed")
        if reopened and not vals.get("change_reason"):
            raise UserError(self.env._(
                "Údaje protistrany %s jsou potvrzené; při změně doplňte nový důvod změny.",
                ", ".join(reopened.partner_id.mapped("display_name"))))
        res = super().write(vals)
        if reopened:
            # Zápis jako superuživatel: stav kontroly a Zkontroloval nejsou pro přípravu zapisovatelné ve formuláři.
            super(InvestraCounterpartyProfile, reopened.sudo()).write(
                {"review_state": "draft", "reviewed_by": False, "reviewed_on": False})
        return res

    def unlink(self):
        if not self.env.su and self.filtered(lambda p: p.review_state == "reviewed"):
            raise UserError(self.env._("Potvrzené údaje protistrany nejde smazat."))
        return super().unlink()

    # --- potvrzení --------------------------------------------------------------------------------------------------

    def action_review(self):
        if not self.env.user.has_group(APPROVER_GROUP):
            raise UserError(self.env._("Údaje protistrany potvrzuje jen schvalovatel."))
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
