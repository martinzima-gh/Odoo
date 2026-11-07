"""Ukázka stavů přehledu fondů v investra_test. Všechna čísla, názvy a termíny jsou smyšlené.

Spuštění: odoo shell -d investra_test < tools/nav_demo/demo_prehled.py
Výstup: Beta vyžaduje zásah, Gama má upozornění. Termíny jsou obecné příklady, ne termíny ČNB.
"""
from datetime import date

BETA, GAMA = "Ukázkový fond Beta (smyšlený)", "Ukázkový fond Gama (smyšlený)"
if env["res.company"].search_count([("name", "in", [BETA, GAMA])]):
    raise SystemExit("Ukázka už existuje.")
czk = env.ref("base.CZK")
admin = env.ref("base.user_admin")


def make_fund(name, prefix):
    book = env["investra.entity"].create_book(name, "fund", "cas501", czk, "investra_fund")
    company = book.company_id
    admin.write({"company_ids": [(4, company.id)]})
    base = [env.ref("base.group_user").id, env.ref("account.group_account_manager").id]

    def user(suffix, xmlid):
        return env["res.users"].create({
            "name": f"{prefix}_{suffix}", "login": f"{prefix}_{suffix}", "company_id": company.id, "company_ids": [(6, 0, company.ids)],
            "group_ids": [(6, 0, base + [env.ref(xmlid).id])],
        })

    preparer = user("priprava", "investra_entity.group_valuation_preparer")
    approver = user("schvaleni", "investra_entity.group_valuation_approver")
    scoped = env(context=dict(env.context, allowed_company_ids=[company.id]))
    fund = scoped["investra.fund"].create({"entity_id": book.id, "launch_date": "2026-08-31"})
    fund_class = scoped["investra.fund.class"].create({"fund_id": fund.id, "code": "CZK", "name": "Třída CZK", "currency_id": czk.id})
    scoped["investra.class.movement"].create({
        "class_id": fund_class.id, "date": "2026-09-01", "movement_type": "subscription", "amount": 10000000, "units": 10000000,
    })._book()
    return scoped, fund, preparer, approver


def instrument(scoped, name):
    return scoped["investra.instrument"].create({
        "name": name, "currency_id": czk.id, "type_id": env.ref("investra_instruments.type_bond").id, "fair_value_level": "2",
    })


def example(scoped, fund, report, period_end, due_date):
    scoped["investra.regulatory.deadline"].create({
        "fund_id": fund.id, "report": report, "period_end": period_end, "due_date": due_date, "source": "example",
    })


def approved_price(scoped, fund, bond, day, value, preparer, approver):
    record = scoped["investra.instrument.price"].with_user(preparer).create({
        "fund_id": fund.id, "instrument_id": bond.id, "date": day, "price": value, "source": "Ukázkový zdroj",
    })
    record.with_user(approver).action_approve()


# Beta: zářijové ocenění zveřejněné, říjnové po termínu, obchod po termínu vypořádání, termín po lhůtě.
scoped, fund, preparer, approver = make_fund(BETA, "beta")
bond = instrument(scoped, "Ukázkový dluhopis Beta")
scoped["investra.trade"].create({"fund_id": fund.id, "instrument_id": bond.id, "trade_date": "2026-09-10", "quantity": 500, "price": 10000})._book()
september, october = date(2026, 9, 30), date(2026, 10, 31)
scoped["investra.valuation.calendar"].create([
    {"fund_id": fund.id, "date": september, "published_on": "2026-10-05"},
    {"fund_id": fund.id, "date": october, "published_on": "2026-11-05"},
])
approved_price(scoped, fund, bond, september, 10050, preparer, approver)
first = scoped["investra.valuation"].with_user(preparer).create({"fund_id": fund.id, "date": september})
first.action_compute()
first.action_submit()
first.with_user(approver).action_approve()
first.action_post()
first.action_send_depositary()
first.with_user(approver).action_depositary_confirm()
first.action_build_package()
first.with_user(approver).action_publish()
scoped["investra.trade"].create({
    "fund_id": fund.id, "instrument_id": bond.id, "trade_date": "2026-10-28", "settlement_date": "2026-11-02", "quantity": 100, "price": 10060,
})._book()
approved_price(scoped, fund, bond, october, 10080, preparer, approver)
scoped["investra.valuation"].with_user(preparer).create({"fund_id": fund.id, "date": october}).action_compute()
example(scoped, fund, "Příklad: měsíční výkaz", september, "2026-10-25")
example(scoped, fund, "Příklad: roční výkaz", date(2026, 12, 31), "2027-04-30")

# Gama: bez ocenění, cena čekající na schválení a blízký termín.
scoped, fund, preparer, approver = make_fund(GAMA, "gama")
bond = instrument(scoped, "Ukázkový dluhopis Gama")
scoped["investra.instrument.price"].with_user(preparer).create({
    "fund_id": fund.id, "instrument_id": bond.id, "date": "2026-10-31", "price": 9950, "source": "Ukázkový zdroj",
})
example(scoped, fund, "Příklad: měsíční výkaz", date(2026, 10, 31), "2026-11-12")

env.cr.commit()
all_funds = env["investra.fund"].with_context(allowed_company_ids=env["res.company"].search([]).ids).search([])
for row in all_funds.read(["name", "dashboard_status", "dashboard_date", "dashboard_state", "dashboard_capital", "dashboard_next_deadline", "dashboard_exceptions"]):
    print(row)
print("HOTOVO")
