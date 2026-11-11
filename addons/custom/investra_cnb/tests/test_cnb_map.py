from datetime import date

from odoo.tests import tagged

from odoo.addons.investra_nav.tests.common import NavCase


class CnbMapCase(NavCase):
    """Fond s úpisem 100 000, dluhopisem za 40 000 přeceněným na 42 000; rok 2038 jen pro tyto testy."""

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.company = self.fund.company_id
        self.day = date(2038, 1, 31)
        self.Map = self.env["investra.cnb.map"]
        self.subscribe(self.cls(self.fund, "A"), "2038-01-01", 100000, 1000)
        self.bond = self.env["investra.instrument"].create({
            "name": "Dluhopis", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_bond").id,
        })
        self.classify(self.fund, self.bond)
        self.env["investra.trade"].create({
            "fund_id": self.fund.id, "instrument_id": self.bond.id, "trade_date": "2038-01-05", "quantity": 400, "price": 100,
        })._book()
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": self.bond.id, "date": self.day, "price": 105, "source": "Test",
        })
        price.with_user(self.approver).action_approve()
        self._before_valuation()
        self.run_to_posted(self.valuation(self.fund, self.day))

    def _before_valuation(self):
        """Doklady s datem v období ocenění; po zaúčtování ocenění je zámek ocenění (vrstva 1) odmítne."""

    def value(self, sheet, row, column=1):
        return self.Map._sheet_values(self.company, sheet, self.day).get((row, column), 0)


@tagged("post_install", "-at_install")
class TestCnbMap(CnbMapCase):

    def test_assets_by_row(self):
        self.assertEqual(self.value("ROFO10_11", 4), 60000)
        self.assertEqual(self.value("ROFO10_11", 6), 42000)
        self.assertEqual(self.value("ROFO10_11", 1), 102000)

    def test_balance_sheet_balances(self):
        self.assertEqual(self.value("ROFO10_21", 1), self.value("ROFO10_11", 1))

    def test_result_reaches_equity_and_income_statement(self):
        self.assertEqual(self.value("ROFO10_21", 46), 2000)
        self.assertEqual(self.value("VYFO20_11", 30), 2000)
        self.assertEqual(self.value("VYFO20_11", 58), 2000)

    def test_statistical_sheets(self):
        self.assertEqual(self.value("RIS30_01", 10), 42000)
        self.assertEqual(self.value("RIS30_01", 1), self.value("RIS30_03", 1))

    def test_classification_changes_row(self):
        # Řádek bere kategorii ze zařazení na řádku dokladu, ne z nástroje (rozhodnutí 2026-11-11).
        self.assertEqual(self.value("ROFO10_11", 8), 0)
        classification = self.bond.classification_ids
        self.env.cr.execute(
            "UPDATE investra_portfolio_classification SET ifrs9_category = 'fvoci' WHERE id = %s", (classification.id,)
        )
        classification.invalidate_recordset(["ifrs9_category"])
        self.assertEqual(self.value("ROFO10_11", 8), 42000)
        self.assertEqual(self.value("ROFO10_11", 6), 0)


    def test_nothing_is_unmapped(self):
        sheets = ("ROFO10_11", "ROFO10_21", "VYFO20_11")
        self.assertFalse(self.Map._unmapped_roles(self.company, sheets, self.day))

    def test_every_chart_role_is_mapped(self):
        covered = self.Map.search([("sheet", "in", ("ROFO10_11", "ROFO10_21", "VYFO20_11"))]).role_id
        roles = self.env["investra.role.account"].sudo().search([("company_id", "=", self.company.id)]).role_id
        self.assertFalse((roles - covered).mapped("code"))

    def test_missing_map_is_reported(self):
        entries = self.Map.search([("sheet", "=", "ROFO10_11"), ("role_id.code", "=", "bank")])
        entries.write({"valid_to": "2030-01-01"})
        missing = self.Map._unmapped_roles(self.company, ("ROFO10_11",), self.day)
        self.assertIn("bank", missing.mapped("code"))

    def test_expired_map_is_not_used(self):
        self.Map.search([("sheet", "=", "ROFO10_11"), ("role_id.code", "=", "bank")]).write({"valid_to": "2030-01-01"})
        self.assertEqual(self.value("ROFO10_11", 4), 0)

    def test_other_company_is_isolated(self):
        other = self.make_fund(classes=[{"code": "A"}])
        self.assertFalse(any(self.Map._sheet_values(other.company_id, "ROFO10_11", self.day).values()))


@tagged("post_install", "-at_install")
class TestCnbMapTwoModels(CnbMapCase):
    """Stejný dluhopis i v portfoliu Držet pro inkaso; obchod se zaúčtuje před oceněním (zámek ocenění)."""

    def _before_valuation(self):
        held = self.portfolio(self.fund, "hold_to_collect")
        self.bond.cashflow_ids = [(0, 0, {"date": "2040-01-01", "amount": 100})]
        self.classify(self.fund, self.bond, "hold_to_collect")
        self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": held.id, "instrument_id": self.bond.id, "trade_date": "2038-01-20",
            "quantity": 100, "price": 100,
        })._book()

    def test_same_bond_in_two_models_splits_rows(self):
        self.assertEqual(self.value("ROFO10_11", 6), 42000)
        self.assertEqual(self.value("ROFO10_11", 10), 10000)
