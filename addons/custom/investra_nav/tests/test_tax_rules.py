import importlib.util
import io
import json
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import NavCase

DAY = date(2031, 3, 31)


@tagged("post_install", "-at_install")
class TestTaxRules(NavCase):
    """ZJ-07 výpočet daně po pravidlech (docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md, 9.1 referenční příklad, plán C5, C7).

    Jedna třída, výchozí Daň ZIF 5 %, krok 3; výsledek od začátku účetního období 100 000: ostatní výnos 84 000, penále 2 000
    (667300), tuzemské dividendy 10 000 (714100), zahraniční 5 000 (714200), dceřiné 3 000 (714300); běžné výjimky.
    Doklady jsou z roku 2031 (jako testy obchodů), ocenění 31. 3. 2031.
    """

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2031-01-02", 1_000_000, 1000)
        self.zif = self.env.ref("investra_nav.tax_rule_zif_5")
        self.separate = self.env.ref("investra_nav.tax_rule_separate_15")
        self.exempt = self.env.ref("investra_nav.tax_rule_exempt")
        self.carrier = self.fund_tax(self.fund, rule=self.zif)

    # --- pomocné -------------------------------------------------------------------------------------------------

    def account(self, code, fund=None):
        return self.env["account.account"].search([("code", "=", code),
                                                   ("company_ids", "in", (fund or self.fund).company_id.ids)])

    def post_to(self, code, amount, role, day="2031-02-15", fund=None, fund_class=None, key=None):
        """Doklad na účet (kladně výnos, záporně náklad) proti bance."""
        fund = fund or self.fund
        amount = Decimal(str(amount))
        line = {"role": role, "amount": str(-amount)}
        if code:
            line["extra"] = {"account_id": self.account(code, fund).id}
        bank = {"role": "bank", "amount": str(amount)}
        if fund_class:
            line["class_id"] = bank["class_id"] = fund_class.id
        self.book(fund, key or f"{code}:{amount}:{day}:{fund.id}", date.fromisoformat(day), [line, bank])

    def reference(self, fund=None, other=84000):
        fund = fund or self.fund
        self.post_to(None, other, "income_other", fund=fund)
        self.post_to("667300", -2000, "expense_other", fund=fund)
        self.post_to("714100", 10000, "income_dividend", fund=fund)
        self.post_to("714200", 5000, "income_dividend", fund=fund)
        self.post_to("714300", 3000, "income_dividend", fund=fund)

    def common_exceptions(self, fund=None, pct=True):
        fund = fund or self.fund
        fund.action_add_common_tax_exceptions()
        if not pct:
            fund.tax_exception_ids.write({"nondeductible_pct": 0})

    def compute(self, fund=None, day=DAY):
        fund = fund or self.fund
        self.env = self.env(context=dict(self.env.context, allowed_company_ids=[fund.company_id.id]))
        valuation = self.valuation(fund, day)
        valuation.action_compute()
        return valuation

    def rules(self, valuation):
        line = valuation.fee_line_ids.filtered(lambda l: l.rule_id.kind == "tax")
        return {row["name"]: row for row in json.loads(line.detail)["rules"]}

    def required(self, valuation, rule):
        return Decimal(self.rules(valuation)[rule.name]["required"])

    def move_balance(self, valuation, code):
        lines = valuation.event_ids.move_id.line_ids.filtered(lambda l: l.account_id == self.account(code, valuation.fund_id))
        return Decimal(str(round(sum(lines.mapped("balance")), 2)))

    # --- referenční příklad ----------------------------------------------------------------------------------------

    def test_reference_without_nondeductible(self):
        self.reference()
        self.common_exceptions(pct=False)
        valuation = self.compute()
        self.assertEqual(Decimal(self.rules(valuation)[self.zif.name]["base"]), Decimal("84000.00"))
        self.assertEqual(self.required(valuation, self.zif), Decimal("4200.00"))
        self.assertEqual(self.required(valuation, self.separate), Decimal("750.00"))
        self.assertEqual((self.move_balance(valuation, "681000"), self.move_balance(valuation, "347000")), (4200, -4200))
        self.assertEqual((self.move_balance(valuation, "681300"), self.move_balance(valuation, "347300")), (750, -750))
        self.assertTrue(valuation.tax_breakdown_html)
        self.assertIn(self.separate.name, valuation.tax_breakdown_html)

    def test_package_has_tax_sheet(self):
        """XLS pro depozitáře: list Daň z téhož snímku jako rozpad v ocenění (ZJ-07 E)."""
        self.reference()
        self.common_exceptions()
        valuation = self.compute()
        rows, exceptions, step = valuation._package_rows_tax()
        by_name = {row["name"]: row for row in rows}
        self.assertEqual(by_name[self.zif.name]["required"], 4237.5)
        self.assertEqual(by_name[self.separate.name]["required"], 750.0)
        self.assertTrue(exceptions)
        self.assertEqual(step, "3")
        self.run_to_posted(valuation)
        data = zipfile.ZipFile(io.BytesIO(valuation.action_build_package().raw))
        self.assertIn("Daň", data.read("xl/workbook.xml").decode())

    def test_reference_with_nondeductible(self):
        self.reference()
        self.common_exceptions()
        valuation = self.compute()
        row = self.rules(valuation)[self.zif.name]
        self.assertEqual((Decimal(row["base"]), Decimal(row["nondeductible"])), (Decimal("84750.00"), Decimal("750.00")))
        self.assertEqual(self.required(valuation, self.zif), Decimal("4237.50"))

    def test_foreign_tax_credit_and_lost_credit(self):
        self.reference()
        self.common_exceptions(pct=False)
        self.post_to("681400", -750, "expense_tax")
        valuation = self.compute()
        self.assertEqual(self.required(valuation, self.separate), 0)
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "tax_credit_lost").status, "ok")
        self.post_to("681400", -150, "expense_tax", key="credit-more")
        valuation = self.compute(day=date(2031, 4, 30))
        row = self.rules(valuation)[self.separate.name]
        self.assertEqual((Decimal(row["required"]), Decimal(row["credit_used"]), Decimal(row["credit_lost"])),
                         (0, Decimal("750.00"), Decimal("150.00")))
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "tax_credit_lost").status, "warning")

    def test_withholding_and_prior_year_do_not_change_tax(self):
        """Srážková daň (681100) a doměrek minulých let (681200) se nepočítají do základu ani do zaúčtované daně."""
        self.reference()
        self.common_exceptions(pct=False)
        self.post_to("681100", -1500, "expense_tax")
        self.post_to("681200", -300, "expense_tax")
        valuation = self.compute()
        self.assertEqual(self.required(valuation, self.zif), Decimal("4200.00"))
        self.assertEqual(Decimal(self.rules(valuation)[self.zif.name]["move"]), Decimal("4200.00"))

    def test_loss(self):
        self.reference(other=-36000)  # výsledek −20 000
        self.common_exceptions(pct=False)
        valuation = self.compute()
        self.assertEqual(Decimal(self.rules(valuation)[self.zif.name]["base"]), Decimal("-36000.00"))
        self.assertEqual(self.required(valuation, self.zif), 0)
        self.assertEqual(self.required(valuation, self.separate), Decimal("750.00"))
        self.common_exceptions()  # existující výjimky nepřepíše
        self.fund.tax_exception_ids.filtered(lambda e: e.account_id.code in ("714100", "714200")).nondeductible_pct = 5
        valuation = self.compute(day=date(2031, 4, 30))
        self.assertEqual(Decimal(self.rules(valuation)[self.zif.name]["base"]), Decimal("-35250.00"))

    def test_austrian_dividend(self):
        """Hrubá 7 000, sraženo 27,5 % (1 925), smluvní 10 %: 700 na 681400, 1 225 pohledávka → samostatný 1 050 − 700 = 350."""
        self.common_exceptions(pct=False)
        self.book(self.fund, "at-dividend", date(2031, 2, 15), [
            {"role": "income_dividend", "amount": "-7000", "extra": {"account_id": self.account("714200").id}},
            {"role": "expense_tax", "amount": "700", "extra": {"account_id": self.account("681400").id}},
            {"role": "receivable_other", "amount": "1225", "extra": {"account_id": self.account("341220").id}},
            {"role": "bank", "amount": "5075"},
        ])
        valuation = self.compute()
        self.assertEqual(self.required(valuation, self.separate), Decimal("350.00"))
        tax_expense = self.move_balance(valuation, "681300") + Decimal("700")
        self.assertEqual(tax_expense, Decimal("1050.00"))

    def test_deferred_tax_on_equity_account(self):
        deferred = self.env.ref("investra_nav.tax_rule_deferred_fvoci_5")
        reserve = self.account("564300")
        self.env["investra.fund.tax.exception"].create({"fund_id": self.fund.id, "account_id": reserve.id,
                                                        "tax_rule_id": deferred.id})
        self.book(self.fund, "reserve", date(2031, 2, 15), [
            {"role": "revaluation_reserve", "amount": "-40000"}, {"role": "bank", "amount": "40000"}])
        valuation = self.compute()
        self.assertEqual(self.required(valuation, deferred), Decimal("2000.00"))
        self.assertEqual((self.move_balance(valuation, "564400"), self.move_balance(valuation, "348000")), (2000, -2000))
        self.run_to_posted(valuation)
        self.book(self.fund, "reserve-down", date(2031, 4, 15), [
            {"role": "revaluation_reserve", "amount": "50000"}, {"role": "bank", "amount": "-50000"}])
        april = self.compute(day=date(2031, 4, 30))
        # Zůstatek −10 000 bez „Vykázat i pohledávku“ → 0: rozpuštění 2 000.
        self.assertEqual(self.required(april, deferred), 0)
        self.assertEqual(self.move_balance(april, "348000"), 2000)

    def test_fee_exception_share_beats_step(self):
        """Krácení: ručně doložená úplata 40 000 na účet obhospodařování, daň po kroku 1; výjimka Mimo základ s podílem."""
        self.carrier.base_step = "1"
        self.post_to(None, 100000, "income_other")
        management = self.expense_account(self.fund, "expense_management")
        valuation = self.valuation(self.fund, DAY)
        self.manual_fee(valuation, 40000, account_id=management.id)
        valuation.action_compute()
        self.assertEqual(self.required(valuation, self.zif), Decimal("5000.00"))  # bez výjimky po kroku 1 základ nesnižuje
        exception = self.env["investra.fund.tax.exception"].create({
            "fund_id": self.fund.id, "account_id": management.id, "tax_rule_id": self.exempt.id, "share": 0.25})
        valuation.action_compute()
        self.assertEqual(self.required(valuation, self.zif), Decimal("3500.00"))  # 100 000 − 30 000
        exception.share = 0.10
        valuation.action_compute()
        self.assertEqual(self.required(valuation, self.zif), Decimal("3200.00"))  # 100 000 − 36 000

    def test_fee_exception_nondeductible_pct_on_expense(self):
        """ZJ-23: procento neuznatelnosti na nákladovém účtu – úplata 40 000, 25 % se přičte zpět: 100 000 − 40 000 + 10 000."""
        self.carrier.base_step = "1"
        self.post_to(None, 100000, "income_other")
        management = self.expense_account(self.fund, "expense_management")
        valuation = self.valuation(self.fund, DAY)
        self.manual_fee(valuation, 40000, account_id=management.id)
        self.env["investra.fund.tax.exception"].create({
            "fund_id": self.fund.id, "account_id": management.id, "tax_rule_id": self.zif.id, "nondeductible_pct": 25})
        valuation.action_compute()
        self.assertEqual(self.required(valuation, self.zif), Decimal("3500.00"))  # základ 70 000 × 5 %

    # --- třídy -----------------------------------------------------------------------------------------------------

    def two_class_fund(self):
        fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        a, b = self.cls(fund, "A"), self.cls(fund, "B")
        self.subscribe(a, "2031-01-02", 500_000, 500)
        self.subscribe(b, "2031-01-02", 500_000, 500)
        self.fund_tax(fund, rule=self.zif)
        self.common_exceptions(fund, pct=False)
        self.post_to(None, 100000, "income_other", fund=fund)
        return fund, a, b

    def transfers(self, valuation):
        detail = json.loads(valuation.fee_line_ids.filtered(lambda l: l.rule_id.kind == "tax").detail)
        return {int(k): Decimal(v) for k, v in detail["transfers"].items()}

    def test_class_effect_exempt_penalty(self):
        """Třídy 50/50, penále 2 000 jen A je Mimo základ → daňový efekt 0."""
        fund, a, _b = self.two_class_fund()
        self.post_to("667300", -2000, "expense_other", fund=fund, fund_class=a)
        self.assertEqual(self.transfers(self.compute(fund)), {})

    def test_class_effect_separate_rule(self):
        """Třídy 50/50, zahraniční dividenda 5 000 jen A: A nese celou samostatnou daň 750 (375 poměrem + přesun 375)."""
        fund, a, b = self.two_class_fund()
        self.post_to("714200", 5000, "income_dividend", fund=fund, fund_class=a)
        valuation = self.compute(fund)
        self.assertEqual(self.required(valuation, self.separate), Decimal("750.00"))
        self.assertEqual(self.transfers(valuation), {a.id: Decimal("-375.00"), b.id: Decimal("375.00")})

    def test_class_effect_portfolio_of_class(self):
        """Realizovaný zisk z portfolia třídy B (ZJ-09 A): specifický výnos B 500 → e = 5 %, E_B = −25 → přesun B −12,50, A +12,50."""
        from odoo.addons.investra_instruments.tests.common import with_ids
        fund, a, b = self.two_class_fund()
        portfolio = self.portfolio(fund, "trading")
        portfolio.class_id = b
        equity = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Akcie třídy B {fund.id}", "currency_id": self.czk.id,
            "type_id": self.env.ref("investra_instruments.type_equity").id}, fund))
        self.classify(fund, equity, "trading")
        for quantity, price, day in ((10, 100, "2031-03-02"), (-10, 150, "2031-03-10")):
            self.env["investra.trade"].create({
                "fund_id": fund.id, "portfolio_id": portfolio.id, "instrument_id": equity.id, "trade_date": day,
                "settlement_date": day, "quantity": quantity, "price": price}).with_user(self.preparer).action_book()
        valuation = self.compute(fund)
        self.assertEqual(self.transfers(valuation), {a.id: Decimal("12.50"), b.id: Decimal("-12.50")})

    def test_class_effect_manual_fee_of_class(self):
        """Ručně doložená úplata 1 000 jen třídy A (krok 2 ≤ krok daně 3) snižuje základ → efekt A +50 → přesun A +25, B −25."""
        fund, a, b = self.two_class_fund()
        self.env = self.env(context=dict(self.env.context, allowed_company_ids=[fund.company_id.id]))
        valuation = self.valuation(fund, DAY)
        self.manual_fee(valuation, 1000, class_id=a.id)
        valuation.action_compute()
        self.assertEqual(self.required(valuation, self.zif), Decimal("4950.00"))
        self.assertEqual(self.transfers(valuation), {a.id: Decimal("25.00"), b.id: Decimal("-25.00")})

    # --- sdílené pravidlo, opravy, kontroly --------------------------------------------------------------------------

    def test_shared_rule_in_two_funds(self):
        other = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(other, "A"), "2031-01-02", 1_000_000, 1000)
        self.fund_tax(other, rule=self.zif)
        self.post_to(None, 10000, "income_other")
        self.post_to(None, 20000, "income_other", fund=other)
        self.assertEqual(self.required(self.compute(), self.zif), Decimal("500.00"))
        self.assertEqual(self.required(self.compute(other), self.zif), Decimal("1000.00"))

    def test_corrections_per_rule_carried_to_year_end(self):
        self.reference()
        self.common_exceptions(pct=False)
        valuation = self.valuation(self.fund, DAY)
        self.manual_fee(valuation, 1000, note="Poradce", account_id=False, corrects_rule_id=self.carrier.id,
                        correction_target="base", tax_rule_id=self.separate.id)
        entry = self.manual_fee(valuation, 100, note="Poradce", account_id=False, corrects_rule_id=self.carrier.id)
        self.assertEqual(entry.tax_rule_id, self.zif)  # výchozí pravidlo fondu
        self.run_to_posted(valuation)
        self.assertEqual(self.required(valuation, self.separate), Decimal("900.00"))  # 15 % × (5 000 + 1 000)
        self.assertEqual(self.move_balance(valuation, "681000"), Decimal("4300.00"))  # 4 200 + oprava 100
        april = self.compute(day=date(2031, 4, 30))
        rows = self.rules(april)
        self.assertEqual(Decimal(rows[self.separate.name]["base_correction"]), Decimal("1000.00"))
        self.assertEqual(Decimal(rows[self.zif.name]["carried"]), Decimal("100.00"))
        self.assertEqual(Decimal(rows[self.zif.name]["move"]), Decimal("100.00") - Decimal("100.00"))

    def test_correction_requires_rule_used_in_fund(self):
        valuation = self.valuation(self.fund, DAY)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.manual_fee(valuation, 100, note="x", account_id=False, corrects_rule_id=self.carrier.id,
                            tax_rule_id=self.separate.id)

    def test_missing_account_stops(self):
        rule = self.shared_tax_rule(0.05, name="Daň bez účtu", tax_account_code="681900")
        self.fund.tax_rule_id = rule
        with self.assertRaisesRegex(UserError, "681900"):
            self.compute()

    def test_no_default_rule_warns(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(fund, "A"), "2031-01-02", 1000, 10)
        valuation = self.compute(fund)
        self.assertEqual(valuation.check_ids.filtered(lambda c: c.code == "tax_no_rule").status, "warning")
        self.assertFalse(valuation.fee_line_ids)

    def test_carrier_only_from_fund(self):
        with self.assertRaises(UserError):
            self.env["investra.fee.rule"].create({"fund_id": self.fund.id, "name": "Daň", "kind": "tax"})
        periodic = self.env["investra.fee.rule"].create({
            "fund_id": self.fund.id, "name": "Úplata", "kind": "periodic",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.01})]})
        with self.assertRaises(UserError):
            periodic.kind = "tax"

    def test_archive_guard_sums_rule_accounts(self):
        """Pojistka archivace nosiče: zaúčtovaná daň na účtech všech použitých pravidel (i samostatný základ)."""
        self.common_exceptions(pct=False)
        self.post_to("714200", 5000, "income_dividend")
        self.run_to_posted(self.compute())
        with self.assertRaises(UserError):
            self.fund.tax_rule_id = False

    def test_version_used_in_valuation_is_locked(self):
        rule = self.shared_tax_rule(0.05, name="Daň zámek")
        self.fund.tax_rule_id = rule
        self.post_to(None, 10000, "income_other")
        self.run_to_posted(self.compute())
        with self.assertRaises(UserError):
            rule.version_ids.rate = 0.06

    # --- migrace C5 --------------------------------------------------------------------------------------------------

    def _migration(self):
        path = Path(__file__).resolve().parents[1] / "migrations" / "20.0.0.39.0" / "post-migration.py"
        spec = importlib.util.spec_from_file_location("investra_nav_migration_39", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_migration_moves_carrier_rates_to_rules(self):
        Fee = self.env["investra.fee.rule"].with_context(investra_tax_carrier=True)
        funds = {}
        for code, rate in (("zif", 0.05), ("full", 0.21), ("own", 0.19)):
            fund = self.make_fund(classes=[{"code": "A"}])
            Fee.create({"fund_id": fund.id, "name": "Daň", "kind": "tax", "base_step": "2",
                        "version_ids": [(0, 0, {"valid_from": "2025-01-01", "rate": rate})]})
            funds[code] = fund
        self._migration()._tax_rules(self.env)
        self.assertEqual(funds["zif"].tax_rule_id, self.zif)
        self.assertEqual(funds["full"].tax_rule_id, self.env.ref("investra_nav.tax_rule_21"))
        own = funds["own"].tax_rule_id
        self.assertEqual((own.name, own.tax_account_code, own.balance_account_code, own.version_ids.rate),
                         (f"Daň {funds['own'].name}", "681000", "347000", 0.19))
        self.assertEqual(funds["zif"].tax_base_step, "2")
        self._migration()._tax_rules(self.env)  # opakovatelné
        self.assertEqual(self.env["investra.tax.rule"].search_count([("name", "=", f"Daň {funds['own'].name}")]), 1)
