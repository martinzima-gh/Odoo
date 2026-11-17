from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import ValidationError


PRICE_ROUNDING = [("down", "Dolů"), ("half_up", "Matematicky"), ("up", "Nahoru")]
# Úpisy a odkupy (rozhodnutí „Úpisy a odkupy (bod 8 UX)“, 2026-11-11): parametry fondu, třída je při založení převezme
# a smí je přepsat – stejně jako desetinná místa kurzu.
ROUNDING_OWNER = [("fund", "Zůstává ve fondu"), ("investor", "Vrací se investorovi")]
# Příjemce poplatku (rozhodnutí 2026-11-13 „Příjemce vstupního a výstupního poplatku“, upřesněno 2026-11-13
# „Příjemce poplatku jedním výběrem“): obhospodařovatel a distributor = závazek, poplatek se platí ven; fond = výnos
# celého fondu, dělí se mezi třídy poměrem; třída = celý jen třídě pohybu, jako výnos, nebo jako kapitál třídy.
# Fond do kapitálu nejde: kapitál je vždy kapitál třídy, poměrem se dělí jen výnosy a náklady.
FEE_RECIPIENT = [
    ("manager", "Obhospodařovatel"), ("distributor", "Distributor"), ("fund", "Fond – výnos"),
    ("class_income", "Třída – výnos"), ("class_capital", "Třída – kapitál"),
]
CLASS_RECIPIENTS = ("class_income", "class_capital")
INTERNAL_RECIPIENTS = ("fund",) + CLASS_RECIPIENTS
# Vstupní a výstupní poplatek jsou jen na třídě (rozhodnutí 2026-11-17 „Poplatky fondu a tříd“, ZJ-03); fond je nemá
# a třída je při založení nepřebírá.
MOVEMENT_PARAMS = ("unit_digits", "unit_rounding", "rounding_owner")
FEE_FIELDS = (
    "entry_fee_rate", "entry_fee_recipient", "entry_fee_statute_ref", "entry_fee_note",
    "exit_fee_rate", "exit_fee_recipient", "exit_fee_statute_ref", "exit_fee_note",
)
FEE_HELP = (
    "Obhospodařovatel a Distributor: závazek, platí se ven. Fond – výnos: výnos celého fondu, dělí se mezi třídy poměrem. "
    "Třída – výnos / Třída – kapitál: celý poplatek jen třídě pohybu jako výnos, nebo kapitál třídy; řídí se statutem."
)


def isin_is_valid(isin):
    """ISIN podle ISO 6166: 2 velká písmena (kód země), 9 velkých písmen nebo číslic a kontrolní číslice (Luhn).

    Pomocná funkce je tady, aby ji mohly použít i nástroje (dnes kontrolují jen přítomnost ISIN); kontrolu mezer
    a velikosti písmen neopravuje, jen ji odmítne.
    """
    if not isin or len(isin) != 12 or not isin.isascii() or not isin.isalnum() or isin != isin.upper():
        return False
    if not isin[:2].isalpha() or not isin[11].isdigit():
        return False
    digits = "".join(str(int(char, 36)) for char in isin)
    total = 0
    for index, char in enumerate(reversed(digits)):
        number = int(char) * (2 if index % 2 == 1 else 1)
        total += number - 9 if number > 9 else number
    return total % 10 == 0


class InvestraFund(models.Model):
    _name = "investra.fund"
    _description = "Fond"
    _order = "name"
    _check_company_auto = True

    name = fields.Char(related="entity_id.name", store=True)
    entity_id = fields.Many2one("investra.entity", required=True, ondelete="restrict", string="Účetní kniha")
    company_id = fields.Many2one(related="entity_id.company_id", store=True, index=True)
    currency_id = fields.Many2one(related="entity_id.currency_id")
    class_ids = fields.One2many("investra.fund.class", "fund_id", string="Třídy")
    valuation_frequency = fields.Selection(
        [("daily", "Denně"), ("weekly", "Týdně"), ("monthly", "Měsíčně"), ("quarterly", "Čtvrtletně"), ("yearly", "Ročně")],
        required=True,
        default="monthly",
        string="Frekvence ocenění",
        help="Plánovaná četnost ocenění fondu (denně až ročně). Z ní se u fondu počítá očekávané datum dalšího ocenění: měsíčně, čtvrtletně a ročně poslední den následujícího období, týdně nejbližší další pátek, denně nejbližší další pracovní den (pondělí až pátek; státní svátky se zatím neberou).",
    )
    # Druhou osobu určuje schvalovací matice (rozhodnutí 2026-11-11); dřívější pole second_person_required
    # převedla migrace investra_nav 20.0.0.6.0, sloupec v databázi zůstává jen pro historii.
    manager_id = fields.Many2one(
        "investra.entity", ondelete="restrict", domain=[("entity_type", "=", "manager")], string="Obhospodařovatel",
        help="Investiční společnost, která fond obhospodařuje (údaj o fondu). Schvalovací matice je společná a na obhospodařovateli nezávisí.",
    )
    price_digits = fields.Integer(default=4, required=True, string="Výchozí desetinná místa kurzu")
    price_rounding = fields.Selection(PRICE_ROUNDING, required=True, default="down", string="Výchozí zaokrouhlení kurzu")
    unit_digits = fields.Integer(default=6, required=True, string="Výchozí desetinná místa kusů")
    unit_rounding = fields.Selection(PRICE_ROUNDING, required=True, default="down", string="Výchozí zaokrouhlení kusů")
    rounding_owner = fields.Selection(
        ROUNDING_OWNER, required=True, default="fund", string="Výchozí: rozdíl ze zaokrouhlení kusů",
        help="Zůstává ve fondu = kapitál třídy; vrací se investorovi = závazek, výplatu zadává IS.",
    )
    # Výchozí vstupní a výstupní poplatek fondu zrušilo ZJ-03 (rozhodnutí 2026-11-17 „Poplatky fondu a tříd“): výpočet
    # četl jen třídu, fond hodnoty jen kopíroval do nové třídy. Sloupce entry/exit_fee_rate a entry/exit_fee_recipient
    # fondu Odoo při upgradu odstraní.
    trade_recognition = fields.Selection(
        [("trade_date", "Trade date accounting"), ("settlement_date", "Settlement date accounting")],
        required=True,
        default="trade_date",
        string="Zaúčtování obchodu",
        help="IFRS 9 odst. 3.1.2. Po prvním obchodu fondu nejde změnit.",
    )
    accrual_method = fields.Selection(
        [("eir", "Efektivní úroková míra"), ("linear", "Lineárně")],
        required=True,
        default="eir",
        string="Úročení nástrojů v naběhlé hodnotě",
        help="Způsob, jakým se počítá naběhlý výnos nástrojů v naběhlé hodnotě: efektivní úroková míra, nebo lineárně. Lineární úročení vyžaduje zdůvodnění.",
    )
    accrual_note = fields.Char(string="Zdůvodnění lineárního úročení")

    _entity_uniq = models.Constraint("unique(entity_id)", "Kniha může mít jen jeden fond.")

    @api.constrains("accrual_method", "accrual_note")
    def _check_accrual_note(self):
        for fund in self:
            if fund.accrual_method == "linear" and not fund.accrual_note:
                raise ValidationError(self.env._("Lineární úročení fondu musí mít zdůvodnění."))

    @api.constrains("manager_id")
    def _check_manager(self):
        for fund in self:
            if fund.manager_id and fund.manager_id.entity_type != "manager":
                raise ValidationError(self.env._("Obhospodařovatel musí být kniha druhu Investiční společnost."))

    @api.constrains("entity_id")
    def _check_entity_type(self):
        for fund in self:
            if fund.entity_id.entity_type not in ("fund", "subfund", "sicav"):
                raise ValidationError(self.env._("Fond musí stát na knize fondu, podfondu nebo SICAV."))


class InvestraFundClass(models.Model):
    _name = "investra.fund.class"
    _inherit = ["mail.thread"]
    _description = "Třída fondu"
    _order = "fund_id, sequence, code"

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    code = fields.Char(required=True, string="Kód", help="Značka třídy, ve fondu jedinečná. Po prvním zaúčtovaném úpisu nebo odkupu třídy nejde změnit.")
    name = fields.Char(required=True, string="Název", help="Název třídy pro uživatele; kdykoli jde změnit.")
    sequence = fields.Integer(default=10, string="Pořadí", help="Pořadí tříd ve fondu; přetažením úchytu v seznamu se změní.")
    active = fields.Boolean(default=True, string="Aktivní", help="Archivovaná třída se nenabízí v seznamech; účetní historie zůstává.")
    currency_id = fields.Many2one(
        "res.currency", required=True, string="Měna zveřejnění kurzu", help="V této měně se zveřejňuje kurz a probíhají úpisy a odkupy. NAV fondu a kapitál třídy zůstávají ve funkční měně."
    )
    isin = fields.Char(
        string="ISIN", help="12 znaků: kód země (2 velká písmena), 9 znaků a kontrolní číslice podle ISO 6166. Nepovinné; formát se kontroluje.")
    price_digits = fields.Integer(required=True, string="Desetinná místa kurzu", help="Bez zadání platí hodnota fondu.")
    price_rounding = fields.Selection(PRICE_ROUNDING, required=True, string="Zaokrouhlení kurzu", help="Bez zadání platí hodnota fondu.")
    distribution = fields.Selection([("growth", "Růstová"), ("dividend", "Dividendová")], default="growth", required=True, string="Rozdělování výnosu",
        help="Růstová, nebo dividendová třída. U dividendové třídy účtuje Odoo hrubou dividendu, výplatu a srážky řeší IS (rozhodnutí 2026-11-04).")
    unit_digits = fields.Integer(required=True, string="Desetinná místa kusů", help="Bez zadání platí hodnota fondu.")
    unit_rounding = fields.Selection(PRICE_ROUNDING, required=True, string="Zaokrouhlení kusů", help="Bez zadání platí hodnota fondu.")
    rounding_owner = fields.Selection(ROUNDING_OWNER, required=True, string="Rozdíl ze zaokrouhlení kusů", help="Bez zadání platí hodnota fondu.")
    # Poplatky jen na třídě (ZJ-03); změny sazby, příjemce, článku statutu a poznámky zapíše write() do historie
    # třídy, bez verzí. Atribut tracking Odoo 20 bez modulu mail_tracking změny polí neukládá (ověřeno testem).
    entry_fee_rate = fields.Float(digits=(7, 4), required=True, default=0.0, string="Vstupní poplatek (%)",
                                  help="Sazba z hrubé platby úpisu.")
    entry_fee_recipient = fields.Selection(FEE_RECIPIENT, required=True, default="manager",
                                           string="Příjemce vstupního poplatku", help=FEE_HELP)
    entry_fee_statute_ref = fields.Char(string="Vstupní poplatek – článek statutu")
    entry_fee_note = fields.Text(string="Vstupní poplatek – poznámka")
    exit_fee_rate = fields.Float(digits=(7, 4), required=True, default=0.0, string="Výstupní poplatek (%)",
                                 help="Sazba z hrubé částky odkupu (kusy × cena).")
    exit_fee_recipient = fields.Selection(FEE_RECIPIENT, required=True, default="manager",
                                          string="Příjemce výstupního poplatku", help=FEE_HELP)
    exit_fee_statute_ref = fields.Char(string="Výstupní poplatek – článek statutu")
    exit_fee_note = fields.Text(string="Výstupní poplatek – poznámka")

    _fund_code_uniq = models.Constraint("unique(fund_id, code)", "Kód třídy musí být ve fondu jedinečný.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            fund = self.env["investra.fund"].browse(vals.get("fund_id"))
            vals.setdefault("price_digits", fund.price_digits)
            vals.setdefault("price_rounding", fund.price_rounding)
            for name in MOVEMENT_PARAMS:
                vals.setdefault(name, fund[name])
        return super().create(vals_list)

    def write(self, vals):
        changed = [name for name in FEE_FIELDS if name in vals]
        before = {record.id: {name: record._fee_value(name) for name in changed} for record in self} if changed else {}
        result = super().write(vals)
        for record in self.filtered(lambda r: r.id in before):
            rows = [
                (record._fields[name].string, before[record.id][name], record._fee_value(name))
                for name in changed if before[record.id][name] != record._fee_value(name)
            ]
            if rows:
                record.message_post(body=Markup("<ul>%s</ul>") % Markup().join(
                    Markup("<li>%s: %s → %s</li>") % (label, old or "–", new or "–") for label, old, new in rows
                ))
        return result

    def _fee_value(self, name):
        field = self._fields[name]
        value = self[name]
        if field.type == "selection":
            return dict(field._description_selection(self.env)).get(value, value or "")
        if field.type == "float":
            return f"{value:g} %"
        return value or ""

    @api.depends("code", "fund_id.name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.fund_id.name} / {record.code}"

    @api.constrains("isin")
    def _check_isin(self):
        for record in self.filtered("isin"):
            if not isin_is_valid(record.isin):
                raise ValidationError(self.env._(
                    "Neplatný ISIN třídy %(code)s: %(isin)s. Očekává se 12 znaků velkými písmeny: kód země, 9 znaků a kontrolní číslice.",
                    code=record.code, isin=record.isin))

    @api.constrains("price_digits")
    def _check_digits(self):
        for record in self:
            if not 0 <= record.price_digits <= 18:
                raise ValidationError(self.env._("Počet desetinných míst kurzu musí být 0 až 18."))

    @api.constrains("unit_digits", "entry_fee_rate", "exit_fee_rate")
    def _check_movement_params(self):
        for record in self:
            # Kusy se ukládají na 6 desetinných míst (pohyb i výsledek ocenění).
            if not 0 <= record.unit_digits <= 6:
                raise ValidationError(self.env._("Počet desetinných míst kusů musí být 0 až 6."))
            if not (0 <= record.entry_fee_rate <= 100 and 0 <= record.exit_fee_rate <= 100):
                raise ValidationError(self.env._("Sazba poplatku musí být 0 až 100 %."))
