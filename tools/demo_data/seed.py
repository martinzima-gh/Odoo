"""Ukázková data pracovní databáze `investra` (úkol IM-13). Všechny názvy, čísla, ISIN a LEI jsou smyšlené.

Spuštění (z ~/odoo-dev), databáze musí být nová a bez ukázek:
    docker compose -f docker-compose.investra.yml run --rm --no-deps -T odoo odoo shell \
      --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/custom \
      -d investra --db-filter='^investra$' --no-http --max-cron-threads=0 < tools/demo_data/seed.py

Zápis jen přes ORM a metody tlačítek (Zaúčtovat, Schválit, Potvrdit, Zadat novou sazbu, Návrhy podle kalendáře …),
žádné SQL. Všechny kroky dělá jeden pracovní uživatel `admin`; schvalovací matice investiční společnosti je proto
nastavená na „jeden člověk“ (pokyn Martina 15. 11. 2026, krok 4a úkolu). Výchozí řádky matice modulu se nemění.
Opakované spuštění nad naplněnou databází skončí hláškou a nic nezmění.
"""
import random
from datetime import date, timedelta
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.addons.investra_fund.models.approval_matrix import ACTIVITIES, BUILTIN

DB = env.cr.dbname
if DB != "investra" and not DB.startswith("investra_ci_"):
    raise SystemExit(f"Ukázková data patří jen do databáze investra nebo dočasné investra_ci_*, ne do {DB}.")

MANAGER = "Ukázková investiční společnost (smyšlená)"
NAMES = {
    "A": "Fond A – akcie a podílové listy (smyšlený)",
    "B": "Fond B – dluhopisy (smyšlený)",
    "C": "Fond C – úvěry a vklady EUR (smyšlený)",
    "D": "Fond D – smíšený (smyšlený)",
    "E": "Fond E – nový fond (smyšlený)",
}
if env["res.company"].search_count([("name", "in", [MANAGER, *NAMES.values()])]):
    raise SystemExit("Ukázková data už v databázi jsou; nic se nezměnilo.")

CURRENCY = {"M": "CZK", "A": "CZK", "B": "CZK", "C": "EUR", "D": "CZK", "E": "CZK"}
env.ref("base.EUR").active = True
env.flush_all()
# První načtení osnovy na čisté databázi doinstaluje account_peppol (a závislosti) a přenačte registr uprostřed
# transakce; databáze se proto zakládá s account_peppol (README). Kontrola, ať skript nepadá nejasně:
if env["ir.module.module"].search_count([("name", "=", "account_peppol"), ("state", "!=", "installed")]):
    raise SystemExit("Nejdřív nainstalujte account_peppol (viz tools/demo_data/README.md); nic se nezměnilo.")
BOOK_IDS = {}
for key, currency in CURRENCY.items():
    BOOK_IDS[key] = env["investra.entity"].create_book(
        MANAGER if key == "M" else NAMES[key], "manager" if key == "M" else "fund", "cas501",
        env.ref(f"base.{currency}"), "cz" if key == "M" else "investra_fund").id
    env.invalidate_all()
    if env["investra.entity"].browse(BOOK_IDS[key]).company_id.currency_id.name != currency:
        raise SystemExit(f"Kniha {key}: funkční měna v databázi není {currency}; zastaveno.")

random.seed(20261115)
TODAY = fields.Date.context_today(env.user)
CZK, EUR = env.ref("base.CZK"), env.ref("base.EUR")
(CZK | EUR).active = True
NOTE = "Ukázková data (smyšlená)"
D = Decimal


def money(value):
    return D(str(value)).quantize(D("0.01"), rounding=ROUND_HALF_UP)


def month_ends(first, count, step=1):
    day = date.fromisoformat(first)
    return [(day + relativedelta(months=step * i, day=31)) for i in range(count)]


def plus_workdays(day, count):
    day = date.fromisoformat(day) if isinstance(day, str) else day
    while count:
        day += timedelta(days=1)
        if day.weekday() < 5:
            count -= 1
    return day


def isin(body):
    """ISIN s kontrolní číslicí (ISO 6166, Luhn); předpona ZZ za kódem země, aby nevznikl skutečný kód."""
    digits = "".join(str(int(c, 36)) for c in body)
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch) * (2 if i % 2 == 0 else 1)
        total += n - 9 if n > 9 else n
    return body + str((10 - total % 10) % 10)


def lei(base):
    """LEI s kontrolními číslicemi mod 97 (ISO 17442); předpona ZZZZ00 je smyšlená."""
    return base + f"{98 - int(''.join(str(int(c, 36)) for c in base + '00')) % 97:02d}"


# --- pracovní uživatel ---------------------------------------------------------------------------------------------
admin = env.ref("base.user_admin")
admin.write({
    "lang": "cs_CZ", "tz": "Europe/Prague",
    "group_ids": [(4, env.ref(x).id) for x in (
        "base.group_user", "account.group_account_manager", "investra_entity.group_valuation_preparer",
        "investra_entity.group_valuation_approver", "investra_instrument_master.group_codelist_manager",
    )],
})
UA = env(user=admin.id, context=dict(env.context, lang="cs_CZ", tz="Europe/Prague"))

# --- investiční společnost a schvalovací matice „jeden člověk“ (krok 4a) ---------------------------------------------
manager = env["investra.entity"].browse(BOOK_IDS["M"])
admin.write({"company_ids": [(4, manager.company_id.id)], "company_id": manager.company_id.id})
UA = UA(context=dict(UA.context, allowed_company_ids=[manager.company_id.id]))
UA["investra.approval.matrix"].create([{
    "activity": activity, "manager_id": manager.id, "valid_from": TODAY, "performer_role": BUILTIN[activity][0],
    "second_person": "no", "note": "Pracovní databáze: schvaluje jeden uživatel (pokyn 15. 11. 2026)",
} for activity, _label in ACTIVITIES])

# --- kurzy ČNB EUR (smyšlené, pracovní dny) ------------------------------------------------------------------------
RATE = {}
value, day = 24.60, date(2025, 8, 1)
while day <= TODAY:
    if day.weekday() < 5:
        value = round(min(25.40, max(24.10, value + random.gauss(0, 0.04))), 3)
        RATE[day] = value
        # Uložit a promítnout do kurzů Odoo jako cron stahování (_cron_fetch), jinak by doklady v cizí měně
        # zadané v UI (mimo výpočty fondů, které čtou evidenci kurzů) přepočítaly Odoo kurzem 1.
        env["investra.rate"]._store("cnb", day, {"EUR": (D(1), D(str(value)))}, f"ukazka-cnb-{day}")._publish()
        # Kniha v EUR (fond C) má zdroj ECB: jednotky CZK za 1 EUR (zjednodušeně stejná smyšlená hodnota).
        env["investra.rate"]._store("ecb", day, {"CZK": (D(1), D(str(value)))}, f"ukazka-ecb-{day}")._publish()
    day += timedelta(days=1)


def rate_at(day):
    while day not in RATE:
        day -= timedelta(days=1)
    return RATE[day]


# --- emitenti ------------------------------------------------------------------------------------------------------
def issuer(name, country, esa, lei_base):
    partner = UA["res.partner"].create({"name": name, "is_company": True, "country_id": env.ref(f"base.{country}").id})
    profile = UA["investra.counterparty.profile"].create({
        "partner_id": partner.id, "country_id": env.ref(f"base.{country}").id,
        "esa_code_id": env["investra.esa.code"].search([("code", "=", esa)]).id, "lei": lei(lei_base),
    })
    profile.action_review()
    return partner


ISSUERS = {
    "energie": issuer("Severní energie a.s. (smyšlená)", "cz", "1100200", "ZZZZ00UKAZKAENER01"),
    "strojirny": issuer("Moravské strojírny a.s. (smyšlené)", "cz", "1100300", "ZZZZ00UKAZKASTRO01"),
    "rhein": issuer("Rheinische Technik AG (smyšlená)", "de", "2001002", "ZZZZ00UKAZKARHTE01"),
    "fondy": issuer("Ukázkové fondy investiční společnost a.s. (smyšlená)", "cz", "1240200", "ZZZZ00UKAZKAFOND01"),
    "infra": issuer("Česká infrastruktura a.s. (smyšlená)", "cz", "1100100", "ZZZZ00UKAZKAINFR01"),
    "banka": issuer("Moravská banka a.s. (smyšlená)", "cz", "1221200", "ZZZZ00UKAZKABANK01"),
    "stat": issuer("Ministerstvo financí Ukázkové republiky (smyšlené)", "cz", "1311000", "ZZZZ00UKAZKASTAT01"),
    "stavby": issuer("Pražské stavby s.r.o. (smyšlené)", "cz", "1100200", "ZZZZ00UKAZKASTAV01"),
    "logistika": issuer("Logistika Brno s.r.o. (smyšlená)", "cz", "1100200", "ZZZZ00UKAZKALOGI01"),
    "rheinbank": issuer("Rheinbank AG (smyšlená)", "de", "2002212", "ZZZZ00UKAZKARHBA01"),
}
BA = {code: env["investra.ba0088.code"].search([("code", "=", code)]) for code in ("141", "149", "211", "226")}


def type_(code):
    return env.ref(f"investra_instruments.type_{code}")


def confirm(instrument, schedule=False):
    if schedule:
        instrument.action_generate_schedule()
    instrument.action_confirm_classification()
    return instrument


# --- sdílené nástroje (s ISIN, kniha investiční společnosti) ---------------------------------------------------------
def shared(vals, sppi=("na", "")):
    status, note = sppi
    vals = {"currency_id": CZK.id, **vals}
    if status != "not_assessed":
        vals.update({"sppi_status": status, "sppi_note": note or False, "sppi_assessed_on": "2025-08-15"})
    return UA["investra.instrument"].create(vals)


EQUITY_SPPI = ("na", "Kapitálový nástroj, SPPI se nehodnotí")
SH_ENERGIE = confirm(shared({
    "name": "Akcie Severní energie (smyšlená)", "isin": isin("CZZZ0000001"), "type_id": type_("equity").id,
    "ba0088_id": BA["211"].id, "cfi_code": "ESVUFR", "issuer_id": ISSUERS["energie"].id, "fair_value_level": "1",
}, EQUITY_SPPI))
SH_STROJ = confirm(shared({
    "name": "Akcie Moravské strojírny (smyšlené)", "isin": isin("CZZZ0000002"), "type_id": type_("equity").id,
    "ba0088_id": BA["211"].id, "cfi_code": "ESVUFR", "issuer_id": ISSUERS["strojirny"].id, "fair_value_level": "1",
}, EQUITY_SPPI))
SH_RHEIN = confirm(shared({
    "name": "Akcie Rheinische Technik (smyšlená)", "isin": isin("DEZZ0000003"), "currency_id": EUR.id,
    "type_id": type_("equity").id, "ba0088_id": BA["211"].id, "cfi_code": "ESVUFB",
    "issuer_id": ISSUERS["rhein"].id, "fair_value_level": "1",
}, EQUITY_SPPI))
FUND_UNIT = confirm(shared({
    "name": "Podílový list Ukázkový fond Stabilita (smyšlený)", "isin": isin("CZZZ0000004"), "type_id": type_("fund").id,
    "ba0088_id": BA["226"].id, "cfi_code": "CIOGMU", "issuer_id": ISSUERS["fondy"].id, "fair_value_level": "2",
}, ("fail", "Výnos závisí na výkonnosti fondu, toky nejsou jen jistina a úrok")))
BOND_SHARED = confirm(shared({
    "name": "Dluhopis Česká infrastruktura 4,50/2029 (smyšlený)", "isin": isin("CZZZ0000005"), "type_id": type_("bond").id,
    "ba0088_id": BA["149"].id, "cfi_code": "DBFUFR", "issuer_id": ISSUERS["infra"].id, "fair_value_level": "2",
    "issue_date": "2025-06-15", "maturity_date": "2029-06-15", "nominal_value": 10000, "coupon_type": "fixed",
    "seniority": "senior", "principal": 10000, "start_date": "2025-06-15", "coupon_rate": 4.5,
    "coupon_frequency": "annual", "day_count": "act365",
}, ("pass", "Pevný kupón a jistina ve splatnosti, bez páky a podmíněných toků")), schedule=True)
BOND_VARIABLE = confirm(shared({
    "name": "Dluhopis Moravská banka PRIBOR+1,20/2028 (smyšlený)", "isin": isin("CZZZ0000006"), "type_id": type_("bond").id,
    "ba0088_id": BA["149"].id, "cfi_code": "DBVUFR", "issuer_id": ISSUERS["banka"].id, "fair_value_level": "2",
    "issue_date": "2025-09-01", "maturity_date": "2028-09-01", "nominal_value": 10000, "coupon_type": "floating",
    "seniority": "senior", "principal": 10000, "start_date": "2025-09-01", "coupon_rate": 5.0, "rate_type": "variable",
    "coupon_frequency": "semiannual", "day_count": "act360",
}, ("pass", "Pohyblivá sazba 6M PRIBOR + pevná marže, bez páky")), schedule=True)
BOND_STATE = confirm(shared({
    "name": "Státní dluhopis 3,00/2030 (smyšlený)", "isin": isin("CZZZ0000007"), "type_id": type_("bond").id,
    "ba0088_id": BA["141"].id, "cfi_code": "DBFTFR", "issuer_id": ISSUERS["stat"].id, "fair_value_level": "1",
    "issue_date": "2025-04-01", "maturity_date": "2030-04-01", "nominal_value": 10000, "coupon_type": "fixed",
    "seniority": "senior", "principal": 10000, "start_date": "2025-04-01", "coupon_rate": 3.0,
    "coupon_frequency": "annual", "day_count": "act_act",
}, ("pass", "Pevný kupón a jistina ve splatnosti")), schedule=True)
BOND_IRREGULAR = shared({
    "name": "Dluhopis Pražské stavby nepravidelný 2027 (smyšlený)", "isin": isin("CZZZ0000008"), "type_id": type_("bond").id,
    "ba0088_id": BA["149"].id, "cfi_code": "DBFUFR", "issuer_id": ISSUERS["stavby"].id, "fair_value_level": "3",
    "issue_date": "2025-10-01", "maturity_date": "2027-10-01", "nominal_value": 10000, "coupon_type": "other",
    "seniority": "senior", "principal": 10000, "start_date": "2025-10-01", "coupon_rate": 6.0,
    "coupon_frequency": "irregular", "day_count": "act365",
}, ("pass", "Úrok podle smluvního kalendáře, jistina ve splatnosti"))
# Výplata Nepravidelně: toky ručně na záložce Smluvní peněžní toky (IM-10).
BOND_IRREGULAR.cashflow_ids = [
    (0, 0, {"date": "2026-02-15", "amount": 250, "flow_type": "interest"}),
    (0, 0, {"date": "2026-08-31", "amount": 330, "flow_type": "interest"}),
    (0, 0, {"date": "2027-03-31", "amount": 300, "flow_type": "interest"}),
    (0, 0, {"date": "2027-10-01", "amount": 300, "flow_type": "interest"}),
    (0, 0, {"date": "2027-10-01", "amount": 10000, "flow_type": "principal"}),
]
confirm(BOND_IRREGULAR)

# Tržní ceny (sdílené): náhodná procházka k sjednání a ke každému konci měsíce.
PRICED = {  # nástroj: (počáteční cena, měsíční volatilita, desetinná místa)
    SH_ENERGIE: (900.0, 0.05, 2), SH_STROJ: (1200.0, 0.06, 2), SH_RHEIN: (150.0, 0.05, 2), FUND_UNIT: (1.25, 0.012, 4),
    BOND_SHARED: (9880.0, 0.004, 2), BOND_VARIABLE: (10050.0, 0.002, 2), BOND_STATE: (9700.0, 0.005, 2),
}
PRICE = {}
for instrument, (start, vol, digits) in PRICED.items():
    price = start
    for day in month_ends("2025-08-31", 15):
        price = round(price * (1 + random.gauss(0.003, vol)), digits)
        PRICE[instrument, day] = price
PRICES_DONE = set()


def market_price(instrument, day):
    """Schválená sdílená cena k datu; zadává a schvaluje pracovní uživatel (matice: jeden člověk)."""
    if (instrument, day) in PRICES_DONE:
        return
    record = UA["investra.instrument.price"].create({
        "instrument_id": instrument.id, "date": day, "price": PRICE[instrument, day], "source": "Ukázkový zdroj (smyšlený)",
    })
    record.action_approve()
    PRICES_DONE.add((instrument, day))


def last_price(instrument, day):
    key = max(d for (i, d) in PRICE if i == instrument and d <= day)
    return PRICE[instrument, key]


# --- fondy ---------------------------------------------------------------------------------------------------------
REASONS = {k: env.ref(f"investra_instrument_master.reason_{k}") for k in ("business_model", "mandatory_fvtpl", "sppi_fail")}
CATEGORY = {k: env.ref(f"investra_instrument_master.measurement_{k}") for k in ("ac", "fvtpl")}


class Fund:
    def __init__(self, key, currency, launch, frequency, classes):
        self.key = key
        book = env["investra.entity"].browse(BOOK_IDS[key])
        self.company = book.company_id
        admin.write({"company_ids": [(4, self.company.id)]})
        self.env = UA(context=dict(UA.context, allowed_company_ids=[self.company.id, manager.company_id.id]))
        self.fund = self.env["investra.fund"].create({
            "entity_id": book.id, "launch_date": launch, "valuation_frequency": frequency, "manager_id": manager.id,
        })
        self.launch = date.fromisoformat(launch)
        self.classes = {}
        for code, name, cur, digits in classes:
            self.classes[code] = self.env["investra.fund.class"].create({
                "fund_id": self.fund.id, "code": code, "name": name, "currency_id": cur.id, "price_digits": digits,
            })
        self.portfolios = {}
        self.valuations = []

    def portfolio(self, code, name, category, model, reason, strategy):
        vals = {
            "code": code, "name": name, "measurement_category_id": CATEGORY[category].id, "business_model": model,
            "classification_reason_id": REASONS[reason].id, "valid_from": self.launch,
            "assessment": f"Obchodní model určilo představenstvo obhospodařovatele při založení fondu ({NOTE}).",
            "strategy_description": strategy, "review_frequency": "annual",
        }
        main = self.fund.portfolio_ids.filtered(lambda p: not p.code)[:1] if not self.portfolios else None
        record = main.with_env(self.env) if main else self.env["investra.fund.portfolio"].create({"fund_id": self.fund.id, **vals})
        if main:
            record.write(vals)
        record.action_approve()
        self.portfolios[code] = record
        return record

    def classify(self, portfolio, instrument):
        return self.env["investra.portfolio.classification"].create({
            "portfolio_id": self.portfolios[portfolio].id, "instrument_id": instrument.id, "valid_from": self.launch,
        })

    def own(self, vals, sppi, schedule=True):
        """Nástroj fondu bez ISIN (úvěr, vklad): identifikuje ho číslo smlouvy."""
        status, note = sppi
        instrument = self.env["investra.instrument"].create({
            "currency_id": self.fund.currency_id.id, "fund_id": self.fund.id, "identifier_kind": "contract",
            "sppi_status": status, "sppi_note": note, "sppi_assessed_on": vals["start_date"], **vals,
        })
        return confirm(instrument, schedule=schedule)

    def fees(self, rules):
        for vals in rules:
            self.env["investra.fee.rule"].create({"fund_id": self.fund.id, **vals})

    # --- pohyby investorů (data z IS zadaná ručně) ---------------------------------------------------------------
    def published_price(self, fund_class, day):
        valuation = self.env["investra.valuation"].search([
            ("fund_id", "=", self.fund.id), ("state", "=", "published"), ("date", "<=", day)],
            order="date desc, version desc", limit=1)
        line = valuation.class_line_ids.filtered(lambda l: l.class_id == fund_class)[:1]
        return D(str(line.price)) if line else None

    def movement(self, code, day, kind, gross=None, units=None, initial_price=None):
        fund_class = self.classes[code]
        price = self.published_price(fund_class, day)
        vals = {"class_id": fund_class.id, "date": day, "movement_type": kind, "manual_reason": NOTE}
        if price is None:
            price = D(str(initial_price))
            vals["price_reason"] = "Počáteční kurz třídy podle statutu (smyšlený)"
        digits = D(1).scaleb(-fund_class.unit_digits)
        if kind == "subscription":
            gross = money(gross)
            units = (gross / price).quantize(digits, rounding=ROUND_DOWN)
            vals["rounding_amount_class"] = float(gross - money(units * price))
        else:
            units = D(str(units))
            gross = money(units * price)
        foreign = fund_class.currency_id != self.fund.currency_id
        vals.update({"price": float(price), "units": float(units), ("amount_class" if foreign else "amount"): float(gross)})
        movement = self.env["investra.class.movement"].create(vals)
        movement.action_book()
        return movement

    # --- obchody -------------------------------------------------------------------------------------------------
    def trade(self, portfolio, instrument, day, quantity, price=None):
        day = date.fromisoformat(day)
        price = price if price is not None else last_price(instrument, day)
        fx = rate_at(day) if instrument.currency_id != self.fund.currency_id else 1
        trade = self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolios[portfolio].id, "instrument_id": instrument.id,
            "trade_date": day, "settlement_date": plus_workdays(day, 2), "quantity": quantity, "price": price, "fx_rate": fx,
        })
        trade.action_book()
        if trade.state == "unsettled":
            trade.action_settle()
        return trade

    # --- ocenění -------------------------------------------------------------------------------------------------
    def valuation(self, day, finish=True):
        # Splátky a kupóny podle kalendáře: tlačítko Návrhy podle kalendáře a Zaúčtovat.
        self.env["investra.instrument.repayment.drafts.wizard"].create({"date_to": day}).action_confirm()
        drafts = self.env["investra.instrument.repayment"].search(
            [("fund_id", "=", self.fund.id), ("state", "=", "draft"), ("date", "<=", day)], order="date, id")
        for draft in drafts:
            draft.action_book()
        for (instrument, price_day) in [(i, d) for (i, d) in PRICE if d == day]:
            if self.holds(instrument, day):
                market_price(instrument, day)
        valuation = self.env["investra.valuation"].create({"fund_id": self.fund.id, "date": day})
        valuation.action_compute()
        self.valuations.append(valuation)
        if not finish:
            return valuation
        valuation.action_submit()
        valuation.action_approve()
        valuation.action_post()
        valuation.action_send_depositary()
        valuation.action_depositary_confirm()
        valuation.action_build_package()
        valuation.action_publish()
        return valuation

    def holds(self, instrument, day):
        trades = self.env["investra.trade"].search([
            ("fund_id", "=", self.fund.id), ("instrument_id", "=", instrument.id), ("trade_date", "<=", day),
            ("state", "!=", "reversed")])
        return sum(trades.mapped("quantity")) > 0


def standard_fees(f, management, admin_monthly, extra=()):
    f.fees([
        {"name": "Úplata za obhospodařování", "sequence": 10, "kind": "periodic", "expense_role": "expense_management",
         "statute_ref": "čl. 8.1 statutu (smyšlený)", "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": management})]},
        {"name": "Úplata za administraci", "sequence": 20, "kind": "periodic", "expense_role": "expense_administration",
         "statute_ref": "čl. 8.2 statutu (smyšlený)",
         "version_ids": [(0, 0, {"valid_from": "2020-01-01", "fixed_monthly": admin_monthly, "fixed_mode": "started_month",
                                 "rate": 0.0005, "threshold": 200000000})]},
        *extra,
    ])


# Fond A: akcie a podílové listy, funkční měna CZK, třídy CZK a EUR, 14 měsíčních ocenění.
A = Fund("A", CZK, "2025-08-31", "monthly", [("CZK", "Třída CZK", CZK, 4), ("EUR", "Třída EUR", EUR, 4)])
A.portfolio("A-FV", "Akcie a fondy", "fvtpl", "fair_value", "mandatory_fvtpl",
            "Kótované akcie a podílové listy řízené na reálnou hodnotu (smyšlené).")
for instrument in (SH_ENERGIE, SH_STROJ, SH_RHEIN, FUND_UNIT):
    A.classify("A-FV", instrument)
standard_fees(A, 0.015, 45000, [
    {"name": "Výkonnostní odměna třídy CZK", "sequence": 30, "kind": "performance", "expense_role": "expense_performance",
     "class_ids": [(6, 0, A.classes["CZK"].ids)], "crystallisation": "year", "statute_ref": "čl. 8.3 statutu (smyšlený)",
     "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.15, "perf_measure": "unit", "initial_reference": 1})]},
    {"name": "Očekávaná daň", "sequence": 40, "kind": "tax", "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.05})]},
])

# Fond B: dluhopisy, portfolia AC a FVTPL, 12 měsíčních ocenění.
B = Fund("B", CZK, "2025-10-31", "monthly", [("CZK", "Třída CZK", CZK, 4)])
B.portfolio("B-FV", "Dluhopisy v reálné hodnotě", "fvtpl", "fair_value", "business_model",
            "Dluhopisy řízené a vykazované vedení na reálnou hodnotu (smyšlené).")
B.portfolio("B-AC", "Dluhopisy držené do splatnosti", "ac", "hold_to_collect", "business_model",
            "Dluhopisy držené pro inkaso smluvních toků do splatnosti (smyšlené).")
for portfolio, instrument in (("B-AC", BOND_SHARED), ("B-AC", BOND_IRREGULAR), ("B-FV", BOND_VARIABLE), ("B-FV", BOND_STATE)):
    B.classify(portfolio, instrument)
standard_fees(B, 0.01, 35000, [
    {"name": "Očekávaná daň", "sequence": 40, "kind": "tax", "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.05})]},
])

# Fond C: úvěry a vklady v naběhlé hodnotě, funkční měna EUR, 6 ocenění.
C = Fund("C", EUR, "2026-04-30", "monthly", [("EUR", "Třída EUR", EUR, 4)])
C.portfolio("C-UV", "Úvěry", "ac", "hold_to_collect", "business_model", "Poskytnuté úvěry držené do splatnosti (smyšlené).")
C.portfolio("C-VK", "Termínované vklady", "ac", "hold_to_collect", "business_model", "Vklady u bank do splatnosti (smyšlené).")
DEBT_SPPI = ("pass", "Pevná sazba, jistina a úrok, bez páky")
LOAN = C.own({"name": "Úvěr Logistika Brno 2029 (smyšlený)", "type_id": type_("loan").id, "identifier": "UV-C-2026-001",
              "issuer_id": ISSUERS["logistika"].id, "principal": 1, "start_date": "2026-05-06", "maturity_date": "2029-05-06",
              "coupon_rate": 5.5, "coupon_frequency": "quarterly", "day_count": "act360"}, DEBT_SPPI)
DEPOSIT_1 = C.own({"name": "Termínovaný vklad Rheinbank 05–08/2026 (smyšlený)", "type_id": type_("deposit").id,
                   "identifier": "TV-C-2026-001", "issuer_id": ISSUERS["rheinbank"].id, "principal": 1,
                   "start_date": "2026-05-06", "maturity_date": "2026-08-06", "coupon_rate": 2.8, "day_count": "act360"}, DEBT_SPPI)
DEPOSIT_2 = C.own({"name": "Termínovaný vklad Rheinbank 08–11/2026 (smyšlený)", "type_id": type_("deposit").id,
                   "identifier": "TV-C-2026-002", "issuer_id": ISSUERS["rheinbank"].id, "principal": 1,
                   "start_date": "2026-08-10", "maturity_date": "2026-11-10", "coupon_rate": 2.6, "day_count": "act360"}, DEBT_SPPI)
C.classify("C-UV", LOAN)
C.classify("C-VK", DEPOSIT_1)
C.classify("C-VK", DEPOSIT_2)
standard_fees(C, 0.008, 1500)

# Fond D: smíšený, drží stejný dluhopis jako B v reálné hodnotě; 4 čtvrtletní ocenění.
D_ = Fund("D", CZK, "2025-11-30", "quarterly", [("CZK", "Třída CZK", CZK, 4)])
D_.portfolio("D-FV", "Smíšené portfolio", "fvtpl", "fair_value", "business_model",
             "Akcie, fondy a dluhopisy řízené na reálnou hodnotu (smyšlené).")
D_.portfolio("D-AC", "Vklady", "ac", "hold_to_collect", "business_model", "Termínované vklady do splatnosti (smyšlené).")
for instrument in (BOND_SHARED, SH_ENERGIE, FUND_UNIT):
    D_.classify("D-FV", instrument)
DEPOSIT_D1 = D_.own({"name": "Termínovaný vklad Moravská banka 01–07/2026 (smyšlený)", "type_id": type_("deposit").id,
                     "identifier": "TV-D-2026-001", "issuer_id": ISSUERS["banka"].id, "principal": 1,
                     "start_date": "2026-01-05", "maturity_date": "2026-07-06", "coupon_rate": 3.2, "day_count": "act360"}, DEBT_SPPI)
DEPOSIT_D2 = D_.own({"name": "Termínovaný vklad Moravská banka 07/2026–01/2027 (smyšlený)", "type_id": type_("deposit").id,
                     "identifier": "TV-D-2026-002", "issuer_id": ISSUERS["banka"].id, "principal": 1,
                     "start_date": "2026-07-08", "maturity_date": "2027-01-08", "coupon_rate": 3.0, "day_count": "act360"}, DEBT_SPPI)
D_.classify("D-AC", DEPOSIT_D1)
D_.classify("D-AC", DEPOSIT_D2)
standard_fees(D_, 0.012, 30000)

# Fond E: nový fond, jen úpisy a první obchody; 1 ocenění.
E = Fund("E", CZK, "2026-09-30", "monthly", [("CZK", "Třída CZK", CZK, 4)])
E.portfolio("E-FV", "Akcie a fondy", "fvtpl", "fair_value", "mandatory_fvtpl", "Akcie a podílové listy (smyšlené).")
for instrument in (SH_ENERGIE, FUND_UNIT):
    E.classify("E-FV", instrument)
standard_fees(E, 0.015, 25000)

# --- účetní profily a přiřazení (jen zobrazení, neúčtuje se podle nich) ----------------------------------------------
PROFILES = {}
for code, name, role in (("AP-AKCIE", "Akcie a podílové listy", "instrument"), ("AP-DLUH", "Dluhové cenné papíry", "instrument_debt"),
                         ("AP-VKLAD", "Termínované vklady", "deposit"), ("AP-UVER", "Poskytnuté úvěry", "loan_given")):
    PROFILES[role] = UA["investra.accounting.profile"].create({
        "code": code, "name": name, "role_id": env.ref(f"investra_entity.role_{role}").id})
for f in (A, B, C, D_, E):
    seen = {}
    for record in f.env["investra.portfolio.classification"].search([("fund_id", "=", f.fund.id)]):
        ba0088 = record.instrument_id.ba0088_id
        key = (ba0088.id, False) if ba0088 else (False, record.portfolio_id.id)
        role = record.role_id.code
        if key in seen:
            if seen[key] != role:
                raise SystemExit(f"Účetní profil: {record.display_name} má jinou roli než ostatní nástroje stejného druhu.")
            continue
        seen[key] = role
        f.env["investra.accounting.profile.assignment"].create({
            "company_id": f.company.id, "ba0088_id": key[0], "portfolio_id": key[1],
            "accounting_profile_id": PROFILES[role].id, "valid_from": f.launch,
        })

# --- časová osa: všechny kroky chronologicky (zveřejnění ocenění zamyká období) ----------------------------------------
EVENTS = []


def at(day, order, fn, *args, **kwargs):
    EVENTS.append((date.fromisoformat(day) if isinstance(day, str) else day, order, len(EVENTS), fn, args, kwargs))


def new_rate(instrument, day, rate, note):
    wizard = UA["investra.instrument.rate.wizard"].create(
        {"instrument_id": instrument.id, "valid_from": day, "rate": rate, "note": note})
    wizard.action_confirm()


SUB, TRADE, VAL = 1, 2, 5
# Fond A
at("2025-09-01", SUB, A.movement, "CZK", "2025-09-01", "subscription", gross=80000000, initial_price=1)
at("2025-09-01", SUB, A.movement, "EUR", "2025-09-01", "subscription", gross=1000000, initial_price=100)
for instrument, qty in ((SH_ENERGIE, 40000), (SH_STROJ, 20000), (SH_RHEIN, 5000), (FUND_UNIT, 8000000)):
    at("2025-09-03", TRADE, A.trade, "A-FV", instrument, "2025-09-03", qty, price=PRICED[instrument][0])
at("2026-01-15", SUB, A.movement, "CZK", "2026-01-15", "subscription", gross=5000000)
at("2026-03-10", TRADE, A.trade, "A-FV", SH_STROJ, "2026-03-10", -8000)
at("2026-04-15", SUB, A.movement, "CZK", "2026-04-15", "redemption", units=2000000)
at("2026-06-15", SUB, A.movement, "EUR", "2026-06-15", "subscription", gross=200000)
at("2026-07-08", TRADE, A.trade, "A-FV", SH_RHEIN, "2026-07-08", 1500)
at("2026-09-15", SUB, A.movement, "EUR", "2026-09-15", "redemption", units=300)
# FX swap fondu A (DE-05): sjednání 28. 9., blízká noha 30. 9. (vypořádaná před 1. oceněním), vzdálená 30. 12. otevřená
# přes poslední dvě ocenění (30. 9. zveřejněné, 31. 10. rozpracované). K ocenění 31. 10. ruční hodnota z banky (rozdíl
# v toleranci). Postup a čísla: docs/navrh-fx-derivaty.md; účtuje se jen tlačítky Sjednat a Vypořádat.
FX_BANK = env["res.partner"].create({"name": "Ukázková banka (smyšlená)", "is_company": True})
FX_AMOUNT, FX_POINTS = 500000, 0.15  # EUR; forwardové body CZK za EUR (smyšlené)


def fx_swap_agree():
    spot = D(str(rate_at(date(2026, 9, 28))))
    leg = lambda day, buy, buy_amount, sell, sell_amount: (0, 0, {
        "settlement_date": day, "buy_currency_id": buy.id, "buy_amount": float(buy_amount),
        "sell_currency_id": sell.id, "sell_amount": float(sell_amount)})
    swap = A.env["investra.derivative"].create({
        "fund_id": A.fund.id, "partner_id": FX_BANK.id, "kind": "swap", "trade_date": "2026-09-28",
        "contract_ref": "FX-SWAP-A-001",
        "leg_ids": [leg("2026-09-30", EUR, FX_AMOUNT, CZK, money(FX_AMOUNT * spot)),
                    leg("2026-12-30", CZK, money(FX_AMOUNT * (spot + D(str(FX_POINTS)))), EUR, FX_AMOUNT)]})
    swap.action_agree()
    A.swap = swap


def fx_swap_settle_near():
    A.swap.leg_ids.sorted("settlement_date")[0].action_settle()


def fx_swap_manual_value():
    far = A.swap.leg_ids.sorted("settlement_date")[1]
    left, total = far._days(date(2026, 10, 31))
    k = float(rate_at(date(2026, 10, 31)))
    computed = far.buy_amount - far.sell_amount * k - far.b0 * left / total
    A.env["investra.derivative.value"].create({
        "derivative_id": A.swap.id, "date": "2026-10-31", "amount": round(computed + 2500, 2),
        "currency_id": CZK.id, "source": "Potvrzení banky o reálné hodnotě k 31. 10. 2026 (smyšlené)",
        "reason": "Banka oceňuje podle vlastní křivky forwardových bodů; rozdíl proti výpočtu fondu je v toleranci."})


at("2026-09-28", TRADE, fx_swap_agree)
at("2026-09-30", TRADE, fx_swap_settle_near)
at("2026-10-30", 0, fx_swap_manual_value)
A_DAYS = month_ends("2025-09-30", 14)
for i, day in enumerate(A_DAYS):
    at(day, VAL, A.valuation, day, finish=i < len(A_DAYS) - 1)
# Fond B
at("2025-11-03", SUB, B.movement, "CZK", "2025-11-03", "subscription", gross=150000000, initial_price=1)
at("2025-11-05", TRADE, B.trade, "B-AC", BOND_SHARED, "2025-11-05", 5000, price=9850)
at("2025-11-05", TRADE, B.trade, "B-FV", BOND_VARIABLE, "2025-11-05", 3000, price=10050)
at("2025-11-10", TRADE, B.trade, "B-AC", BOND_IRREGULAR, "2025-11-10", 2000, price=10000)
at("2026-01-12", TRADE, B.trade, "B-FV", BOND_STATE, "2026-01-12", 3000)
at("2026-02-16", SUB, B.movement, "CZK", "2026-02-16", "subscription", gross=10000000)
at("2026-03-01", 0, new_rate, BOND_VARIABLE, "2026-03-01", 4.6, "6M PRIBOR 3,40 + marže 1,20 (smyšlené)")
at("2026-07-15", SUB, B.movement, "CZK", "2026-07-15", "redemption", units=4000000)
at("2026-08-12", TRADE, B.trade, "B-FV", BOND_STATE, "2026-08-12", -1000)
at("2026-09-01", 0, new_rate, BOND_VARIABLE, "2026-09-01", 4.2, "6M PRIBOR 3,00 + marže 1,20 (smyšlené)")
B_DAYS = month_ends("2025-11-30", 12)
for i, day in enumerate(B_DAYS):
    at(day, VAL, B.valuation, day, finish=i < len(B_DAYS) - 1)
# Fond C (EUR)
at("2026-05-04", SUB, C.movement, "EUR", "2026-05-04", "subscription", gross=20000000, initial_price=100)
at("2026-05-06", TRADE, C.trade, "C-UV", LOAN, "2026-05-06", 8000000, price=1)
at("2026-05-06", TRADE, C.trade, "C-VK", DEPOSIT_1, "2026-05-06", 5000000, price=1)
at("2026-07-15", SUB, C.movement, "EUR", "2026-07-15", "subscription", gross=1000000)
at("2026-08-10", TRADE, C.trade, "C-VK", DEPOSIT_2, "2026-08-10", 6000000, price=1)
at("2026-09-15", SUB, C.movement, "EUR", "2026-09-15", "redemption", units=5000)
for day in month_ends("2026-05-31", 6):
    at(day, VAL, C.valuation, day)
# Fond D (čtvrtletně)
at("2025-12-01", SUB, D_.movement, "CZK", "2025-12-01", "subscription", gross=60000000, initial_price=1)
at("2025-12-03", TRADE, D_.trade, "D-FV", BOND_SHARED, "2025-12-03", 2000)
at("2025-12-03", TRADE, D_.trade, "D-FV", SH_ENERGIE, "2025-12-03", 10000)
at("2025-12-03", TRADE, D_.trade, "D-FV", FUND_UNIT, "2025-12-03", 4000000)
at("2026-01-05", TRADE, D_.trade, "D-AC", DEPOSIT_D1, "2026-01-05", 10000000, price=1)
at("2026-04-15", SUB, D_.movement, "CZK", "2026-04-15", "subscription", gross=3000000)
at("2026-07-08", TRADE, D_.trade, "D-AC", DEPOSIT_D2, "2026-07-08", 8000000, price=1)
at("2026-08-17", SUB, D_.movement, "CZK", "2026-08-17", "redemption", units=1500000)
for day in month_ends("2025-12-31", 4, step=3):
    at(day, VAL, D_.valuation, day)
# Fond E
at("2026-10-01", SUB, E.movement, "CZK", "2026-10-01", "subscription", gross=25000000, initial_price=1)
at("2026-10-05", TRADE, E.trade, "E-FV", SH_ENERGIE, "2026-10-05", 12000)
at("2026-10-05", TRADE, E.trade, "E-FV", FUND_UNIT, "2026-10-05", 6000000)
at("2026-10-15", SUB, E.movement, "CZK", "2026-10-15", "subscription", gross=4000000, initial_price=1)
at("2026-10-31", VAL, E.valuation, date(2026, 10, 31))

for when, order, _n, fn, args, kwargs in sorted(EVENTS, key=lambda e: e[:3]):
    try:
        fn(*args, **kwargs)
    except Exception as error:
        import traceback
        traceback.print_exc()
        raise SystemExit(f"Chyba při kroku {when} {getattr(fn, '__qualname__', fn)} {args[:3]}: {error}") from error

env.cr.commit()

# --- souhrn ----------------------------------------------------------------------------------------------------------
for f in (A, B, C, D_, E):
    vals = f.valuations
    last = vals[-1]
    print("FOND", f.key, f.fund.name, "| ocenění:", len(vals), [v.state for v in vals][-2:],
          "| FK", last.fund_capital, "| třídy", [(l.class_id.code, l.price) for l in last.class_line_ids])
    warnings = sorted({c.name for v in vals for c in v.check_ids if c.status != "ok"})
    print("  KONTROLY ne-OK:", sorted({(c.name, c.status) for v in vals for c in v.check_ids if c.status != "ok"}))
print("HOTOVO")
