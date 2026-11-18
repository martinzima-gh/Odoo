from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# Typy knih, jejichž deníky mají od založení neměnné zápisy (hash je nevratný).
HASHED_TYPES = ("sicav", "fund", "subfund")
# Kurz se řídí měnou účetnictví, § 24d odst. 1 zákona o účetnictví.
RATE_SOURCE_BY_CURRENCY = {"CZK": "cnb", "EUR": "ecb"}
# Jiná funkční měna je povolená, ale zdroj kurzů pro ni není implementován (MN-08, rozhodnutí 2026-11-16 bod 5a):
# kde je kurz potřeba, výpočet skončí chybou a nepoužije tiše kurz ČNB.
RATE_SOURCE_NONE = "none"
RATE_SOURCES = [("cnb", "ČNB"), ("ecb", "ECB"), (RATE_SOURCE_NONE, "Neimplementováno")]


def rate_source_for(currency):
    """Zdroj kurzů podle funkční měny: CZK – ČNB, EUR – ECB, jiná – Neimplementováno."""
    return RATE_SOURCE_BY_CURRENCY.get(currency.name, RATE_SOURCE_NONE)


def raise_no_rate_source(env, book_name, currency):
    raise UserError(env._(
        "Kniha %(book)s nemá zdroj kurzů pro funkční měnu %(currency)s (není implementováno).",
        book=book_name, currency=currency.name,
    ))




ICO_KEY = "CZ_EN"  # klíč IČO v additional_identifiers kontaktu (Odoo 20)


def ico_is_valid(ico):
    """IČO: 8 číslic, poslední je kontrolní (součet číslic 1–7 s váhami 8…2, modulo 11)."""
    if not ico or len(ico) != 8 or not ico.isascii() or not ico.isdigit():
        return False
    remainder = sum(int(digit) * weight for digit, weight in zip(ico, range(8, 1, -1))) % 11
    return int(ico[7]) == {0: 1, 1: 0}.get(remainder, 11 - remainder)


class InvestraEntity(models.Model):
    """Účetní kniha: jedna hlavní společnost Odoo. Hierarchie je vlastní, ne pobočky."""

    _name = "investra.entity"
    _inherit = ["mail.thread"]
    _description = "Účetní kniha"
    _order = "name"

    name = fields.Char(related="company_id.name", store=True)
    # Výchozí je aktivní firma a nabízejí se jen firmy zaškrtnuté v přepínači: pravidlo
    # „Knihy podle společnosti“ jinou firmu stejně nepustí (rozhodnutí 2026-11-13).
    company_id = fields.Many2one(
        "res.company",
        required=True,
        ondelete="restrict",
        string="Společnost",
        default=lambda self: self.env.company,
        domain="[('id', 'in', allowed_company_ids)]",
        tracking=True,
    )
    currency_id = fields.Many2one(related="company_id.currency_id", string="Funkční měna")
    # IČO a DIČ patří kontaktu společnosti; zapisuje je jen ten, kdo smí měnit společnost (formulář má pro ostatní pole
    # jen pro čtení, MN-06). Odchylka od zadání: Odoo 20 nemá pole company_registry, IČO je v additional_identifiers
    # kontaktu pod klíčem CZ_EN (standard, čtou ho i sestavy l10n_cz), proto vypočtené pole s inverzí.
    company_registry = fields.Char(
        compute="_compute_company_registry", inverse="_inverse_company_registry", string="IČO")
    vat = fields.Char(related="company_id.vat", readonly=False, string="DIČ")
    entity_type = fields.Selection(
        [
            ("service", "Servisní společnost"),
            ("manager", "Investiční společnost"),
            ("sicav", "SICAV"),
            ("fund", "Fond"),
            ("subfund", "Podfond"),
        ],
        required=True,
        string="Druh jednotky",
        tracking=True,
        help="Servisní a investiční společnost jsou obecné jednotky; SICAV, fond a podfond mají osnovu fondu "
             "a neměnné zápisy v deníku. Podfond patří pod SICAV.",
    )
    framework = fields.Selection(
        [
            ("cas500", "Vyhláška 500/2002"),
            ("cas501", "Vyhláška 501/2002"),
            ("ifrs", "IFRS přijaté EU"),
        ],
        required=True,
        string="Účetní rámec",
        tracking=True,
        help="Podle vyhlášky: servisní společnost 500/2002, investiční společnost, SICAV, fond a podfond 501/2002. "
             "Rámce se nemíchají a po prvním zaúčtování se nemění.",
    )
    # Výchozí podle funkční měny aktivní firmy, onchange a create podle zvolené společnosti (dřív pevně ČNB, MN-08).
    rate_source = fields.Selection(
        RATE_SOURCES, required=True, string="Zdroj kurzů",
        default=lambda self: rate_source_for(self.env.company.currency_id),
        tracking=True,
        help="Řídí se funkční měnou knihy (§ 24d zákona o účetnictví): CZK – ČNB, EUR – ECB. Pro jinou funkční měnu "
             "zdroj kurzů není implementován: přecenění, ocenění i pohyb třídy v cizí měně skončí chybou.",
    )
    parent_id = fields.Many2one(
        "investra.entity", string="Nadřazená kniha", ondelete="restrict",
        domain="[('entity_type', '=', 'sicav')]",
        tracking=True,
        help="Jen u podfondu: SICAV, jehož je podfond součástí.",
    )

    _company_uniq = models.Constraint("unique(company_id)", "Společnost může mít jen jednu knihu.")

    @api.depends("company_id.partner_id.additional_identifiers")
    def _compute_company_registry(self):
        for entity in self:
            entity.company_registry = entity.company_id.partner_id._get_additional_identifier(ICO_KEY) or False

    def _inverse_company_registry(self):
        for entity in self:
            entity.company_id.partner_id._set_additional_identifier(ICO_KEY, (entity.company_registry or "").strip())

    @api.onchange("company_id")
    def _onchange_company_rate_source(self):
        for record in self:
            record.rate_source = rate_source_for(record.company_id.currency_id)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("rate_source"):
                company = self.env["res.company"].browse(vals.get("company_id")) if vals.get("company_id") else self.env.company
                vals["rate_source"] = rate_source_for(company.currency_id)
        return super().create(vals_list)

    @api.constrains("rate_source", "company_id")
    def _check_rate_source(self):
        for entity in self:
            if entity.rate_source != rate_source_for(entity.company_id.currency_id):
                raise ValidationError(self.env._("Zdroj kurzu se řídí měnou účetnictví: %s.", entity.company_id.currency_id.name))

    def _require_rate_source(self):
        """Zdroj kurzů knihy pro výpočet s kurzem; bez implementovaného zdroje výpočet zastaví (MN-08)."""
        self.ensure_one()
        if self.rate_source == RATE_SOURCE_NONE:
            raise_no_rate_source(self.env, self.name, self.company_id.currency_id)
        return self.rate_source

    @api.constrains("company_registry")
    def _check_company_registry(self):
        czech = self.filtered(lambda e: e.company_registry and e.company_id.country_id.code == "CZ")
        for entity in czech:
            if not ico_is_valid(entity.company_registry):
                raise ValidationError(self.env._(
                    "Neplatné IČO %s: musí mít 8 číslic se správnou kontrolní číslicí.", entity.company_registry))

    @api.constrains("parent_id")
    def _check_parent(self):
        if self._has_cycle():
            raise ValidationError(self.env._("Hierarchie knih nesmí být kruhová."))
        for entity in self:
            if entity.entity_type == "subfund" and (not entity.parent_id or entity.parent_id.entity_type != "sicav"):
                raise ValidationError(self.env._("Podfond musí mít nadřazený SICAV."))

    def write(self, vals):
        if "framework" in vals or "company_id" in vals:
            booked = self.env["account.move"].sudo().search_count(
                [("company_id", "in", self.company_id.ids), ("posted_before", "=", True)], limit=1
            )
            if booked:
                raise UserError(self.env._("Rámec ani společnost nejde změnit v knize se zaúčtovanými doklady."))
        return super().write(vals)

    @api.model
    def create_book(self, name, entity_type, framework, currency, template, country=None, partner=None, **values):
        """Založí společnost s osnovou a povinným nastavením.

        Nepovinný `partner` je existující kontakt, který se stane kontaktem nové společnosti (MN-06); bez něj se
        kontakt založí podle názvu jako dřív.

        Načtení osnovy přepíše měnu společnosti měnou šablony, proto se měna nastaví znovu
        a výsledek se zkontroluje. První načtení šablony může potvrdit transakci.

        Společnost se zakládá s kontextem chart_template_load: jinak Odoo při založení společnosti
        se zemí odloží vlastní načtení odhadnuté osnovy na commit (account, res.company.install_l10n_modules)
        a to by po commitu přepsalo osnovu i funkční měnu. Funkční měna se nastavuje jen tady
        při založení knihy (rozhodnutí 2026-11-15).
        """
        values.setdefault("rate_source", rate_source_for(currency))
        Company = self.env["res.company"].sudo()
        company_vals = {
            "name": name,
            "currency_id": currency.id,
            "country_id": ((partner.country_id if partner else None) or country or self.env.ref("base.cz")).id,
        }
        if partner:
            # Kontakt převezme společnost; vidět ho mají mít všechny firmy, proto se vyprázdní jeho firma.
            partner.sudo().write({"company_id": False})
            company_vals["partner_id"] = partner.id
        company = Company.browse(Company.with_context(chart_template_load=True).create(company_vals).id)
        self.env["account.chart.template"].sudo().try_loading(template, company=company, install_demo=False)
        if company.currency_id != currency:
            company.currency_id = currency
        if company.currency_id != currency:
            raise UserError(self.env._("Funkční měna knihy %s nesouhlasí se zadáním.", name))
        company.write({"restrictive_audit_trail": True, "autopost_bills": False})
        if entity_type in HASHED_TYPES:
            journals = self.env["account.journal"].sudo().search([("company_id", "=", company.id)])
            journals.filtered(lambda j: j.type == "general").write({"restrict_mode_hash_table": True})
        # Prohlížeč posílá allowed_company_ids bez nové společnosti; pravidlo „Knihy podle společnosti“ by
        # zápis knihy odmítlo (MN-05), proto se kniha zakládá v prostředí nové společnosti.
        return self.with_company(company).create({
            "company_id": company.id,
            "entity_type": entity_type,
            "framework": framework,
            **values,
        })
