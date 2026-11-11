"""Ukázková data v investra_test. Všechna čísla a názvy jsou smyšlené.

Spuštění: odoo shell -d investra_test < tools/nav_demo/demo.py
Výstup: fond se zveřejněným lednovým a spočteným únorovým oceněním.
"""
from datetime import date
from decimal import Decimal

NAME = "Ukázkový fond Alfa (smyšlený)"
if env["res.company"].search_count([("name", "=", NAME)]):
    raise SystemExit("Ukázka už existuje.")
czk, eur = env.ref("base.CZK"), env.ref("base.EUR")
(czk | eur).active = True
book = env["investra.entity"].create_book(NAME, "fund", "cas501", czk, "investra_fund")
company = book.company_id
groups = [env.ref("base.group_user").id, env.ref("account.group_account_manager").id]


def make_user(login, xmlid):
    return env["res.users"].create({
        "name": login, "login": login, "company_id": company.id, "company_ids": [(6, 0, company.ids)],
        "group_ids": [(6, 0, groups + [env.ref(xmlid).id])],
    })


preparer = make_user("alfa_priprava", "investra_entity.group_valuation_preparer")
approver = make_user("alfa_schvaleni", "investra_entity.group_valuation_approver")
admin = env.ref("base.user_admin")
admin.write({"company_ids": [(4, company.id)], "group_ids": [(4, env.ref("investra_entity.group_valuation_preparer").id), (4, env.ref("account.group_account_manager").id)]})
E_ = env(context=dict(env.context, allowed_company_ids=[company.id]))
fund = E_["investra.fund"].create({"entity_id": book.id, "launch_date": "2026-12-31"})
A = E_["investra.fund.class"].create({"fund_id": fund.id, "code": "CZK", "name": "Třída CZK", "currency_id": czk.id})
B = E_["investra.fund.class"].create({"fund_id": fund.id, "code": "EUR", "name": "Třída EUR", "currency_id": eur.id, "price_digits": 5})
for cls, amount, units in ((A, 60000000, 60000000), (B, 40000000, 16000)):
    E_["investra.class.movement"].create({"class_id": cls.id, "date": "2027-01-04", "movement_type": "subscription", "amount": amount, "units": units})._book()
Rate = E_["investra.rate"]
for day, value in ((date(2027, 1, 4), "25.000"), (date(2027, 1, 29), "25.200"), (date(2027, 2, 26), "24.900")):
    Rate._store("cnb", day, {"EUR": (Decimal(1), Decimal(value))}, f"ukazka{day}{value}")
bond = E_["investra.instrument"].create({"name": "Ukázkový dluhopis", "isin": "CZ0000000001", "currency_id": czk.id, "type_id": env.ref("investra_instruments.type_bond").id, "fair_value_level": "2"})
share = E_["investra.instrument"].create({"name": "Ukázková akcie", "isin": "XS0000000001", "currency_id": eur.id, "type_id": env.ref("investra_instruments.type_equity").id, "fair_value_level": "1"})
conversion = E_["investra.accounting.event"]._create_event(company, "fx-nakup", "Nákup EUR", date(2027, 1, 5), "fx", [
    {"role": "bank", "amount": "37500000", "currency_id": eur.id, "amount_currency": "1500000", "movement_type": "transaction"},
    {"role": "bank", "amount": "-37500000", "movement_type": "transaction"},
])
conversion._lock_events()
conversion._post_events()
# Zařazení v portfoliu Hlavní (model Ostatní, FVTPL); bez zařazení obchod nejde zaúčtovat (rozhodnutí 2026-11-11).
for instrument in (bond, share):
    E_["investra.portfolio.classification"].create({"portfolio_id": fund.portfolio_ids.id, "instrument_id": instrument.id, "valid_from": "2027-01-01"})
for instrument, quantity, price, fx in ((bond, 3000, 10000, 1), (share, 10000, 100, 25)):
    E_["investra.trade"].create({"fund_id": fund.id, "instrument_id": instrument.id, "trade_date": "2027-01-06", "quantity": quantity, "price": price, "fx_rate": fx})._book()
Rule = E_["investra.fee.rule"]
Rule.create({"fund_id": fund.id, "name": "Úplata za obhospodařování", "sequence": 10, "kind": "periodic", "expense_role": "expense_management",
             "statute_ref": "čl. 7.1", "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.015}), (0, 0, {"valid_from": "2027-02-15", "rate": 0.012, "decision_ref": "Rozhodnutí 2/2027"})]})
Rule.create({"fund_id": fund.id, "name": "Úplata za administraci", "sequence": 20, "kind": "periodic", "expense_role": "expense_administration", "statute_ref": "čl. 7.2",
             "version_ids": [(0, 0, {"valid_from": "2020-01-01", "fixed_monthly": 58000, "fixed_mode": "started_month", "rate": 0.0008, "threshold": 280000000})]})
Rule.create({"fund_id": fund.id, "name": "Výkonnostní odměna třídy CZK", "sequence": 30, "kind": "performance", "expense_role": "expense_performance",
             "class_ids": [(6, 0, A.ids)], "crystallisation": "year", "statute_ref": "čl. 7.3",
             "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.2, "perf_measure": "unit", "initial_reference": 1})]})
Rule.create({"fund_id": fund.id, "name": "Očekávaná daň", "sequence": 40, "kind": "tax", "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.05})]})


def price(instrument, day, value):
    record = E_["investra.instrument.price"].with_user(preparer).create(
        {"fund_id": fund.id, "instrument_id": instrument.id, "date": day, "price": value, "source": "Ukázkový zdroj"}
    )
    record.with_user(approver).action_approve()


jan, feb = date(2027, 1, 31), date(2027, 2, 28)
price(bond, jan, 10080); price(share, jan, 104)
valuation = E_["investra.valuation"].with_user(preparer).create({"fund_id": fund.id, "date": jan})
valuation.action_compute(); valuation.action_submit()
valuation.with_user(approver).action_approve()
valuation.action_post(); valuation.action_send_depositary()
valuation.with_user(approver).action_depositary_confirm()
valuation.action_build_package()
print("LEDEN", valuation.state, valuation.fund_capital, [(l.class_id.code, l.capital, l.price) for l in valuation.class_line_ids])
print("KONTROLY", [(c.code, c.status) for c in valuation.check_ids])
valuation.with_user(approver).action_publish()
price(bond, feb, 10120); price(share, feb, 101)
second = E_["investra.valuation"].with_user(preparer).create({"fund_id": fund.id, "date": feb})
second.action_compute()
print("UNOR", second.state, second.fund_capital, [(l.class_id.code, l.capital, l.price) for l in second.class_line_ids])
print("UPLATY", [(l.rule_id.name, l.amount) for l in second.fee_line_ids])
print("PACKAGE", valuation.package_id.id)
import base64
print("XLSXB64", base64.b64encode(valuation.sudo().package_id.raw).decode())
env.cr.commit()
print("HOTOVO")
