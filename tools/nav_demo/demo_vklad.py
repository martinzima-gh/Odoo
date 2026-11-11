"""Ukázka termínovaného vkladu a emitenta v investra_test. Všechna čísla, názvy a LEI jsou smyšlené.

Spuštění: odoo shell -d investra_test < tools/nav_demo/demo_vklad.py
Výstup: fond Delta se zveřejněným zářijovým a spočteným říjnovým oceněním; vklad nese naběhlý úrok.
"""
from datetime import date

NAME = "Ukázkový fond Delta (smyšlený)"
if env["res.company"].search_count([("name", "=", NAME)]):
    raise SystemExit("Ukázka už existuje.")
czk = env.ref("base.CZK")
admin = env.ref("base.user_admin")
book = env["investra.entity"].create_book(NAME, "fund", "cas501", czk, "investra_fund")
company = book.company_id
admin.write({"company_ids": [(4, company.id)]})
base = [env.ref("base.group_user").id, env.ref("account.group_account_manager").id]


def make_user(suffix, xmlid):
    return env["res.users"].create({
        "name": f"delta_{suffix}", "login": f"delta_{suffix}", "company_id": company.id, "company_ids": [(6, 0, company.ids)],
        "group_ids": [(6, 0, base + [env.ref(xmlid).id])],
    })


preparer = make_user("priprava", "investra_entity.group_valuation_preparer")
approver = make_user("schvaleni", "investra_entity.group_valuation_approver")
scoped = env(context=dict(env.context, allowed_company_ids=[company.id]))
fund = scoped["investra.fund"].create({"entity_id": book.id, "launch_date": "2026-08-31"})
fund_class = scoped["investra.fund.class"].create({"fund_id": fund.id, "code": "CZK", "name": "Třída CZK", "currency_id": czk.id})
scoped["investra.class.movement"].create({
    "class_id": fund_class.id, "date": "2026-09-01", "movement_type": "subscription", "amount": 10000000, "units": 10000000,
})._book()

# Emitent: údaje platné od data; sektor a země jsou to, co později potřebují výkazy.
bank = env["res.partner"].create({"name": "Ukázková banka (smyšlená)", "is_company": True})
env["investra.counterparty.profile"].create({
    "partner_id": bank.id, "valid_from": "2026-01-01", "country_id": env.ref("base.cz").id,
    "sector_id": env.ref("investra_counterparty.esa_1220000").id, "lei": "INVSTRUKAZKABANKA036",
})

# Vklad: kalendář toků se vygeneruje z jistiny, sazby a konvence.
deposit = scoped["investra.instrument"].create({
    "name": "Ukázkový termínovaný vklad", "currency_id": czk.id, "type_id": env.ref("investra_instruments.type_deposit").id,
    "issuer_id": bank.id, "principal": 5000000, "start_date": "2026-09-15", "maturity_date": "2026-12-15",
    "coupon_rate": 3.6, "day_count": "act360",
})
deposit.action_generate_schedule()
# Vklad v modelu Držet pro inkaso se splněným testem SPPI: naběhlá hodnota (rozhodnutí 2026-11-11).
held = scoped["investra.fund.portfolio"].create({"fund_id": fund.id, "name": "Držet pro inkaso", "business_model": "hold_to_collect"})
scoped["investra.portfolio.classification"].create({
    "portfolio_id": held.id, "instrument_id": deposit.id, "valid_from": "2026-09-15", "sppi": "pass",
})
scoped["investra.trade"].create({
    "fund_id": fund.id, "portfolio_id": held.id, "instrument_id": deposit.id, "trade_date": "2026-09-15", "quantity": 1, "price": 5000000,
})._book()

september, october = date(2026, 9, 30), date(2026, 10, 31)
first = scoped["investra.valuation"].with_user(preparer).create({"fund_id": fund.id, "date": september})
first.action_compute()
first.action_submit()
first.with_user(approver).action_approve()
first.action_post()
first.action_send_depositary()
first.with_user(approver).action_depositary_confirm()
first.action_build_package()
first.with_user(approver).action_publish()
second = scoped["investra.valuation"].with_user(preparer).create({"fund_id": fund.id, "date": october})
second.action_compute()
env.cr.commit()
print("TOKY", [(str(f.date), f.flow_type, f.amount) for f in deposit.cashflow_ids])
print("HODNOTA", deposit._accrued_value(fund, september, held), deposit._accrued_value(fund, october, held))
for valuation in (first, second):
    print(valuation.date, valuation.state, valuation.fund_capital, [(c.code, c.status) for c in valuation.check_ids])
print("HOTOVO")
