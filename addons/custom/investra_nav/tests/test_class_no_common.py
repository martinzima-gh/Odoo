from datetime import date
from decimal import Decimal

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestClassNoCommon(NavCase):
    """ZJ-08 body 1–3 a D6: třída bez podílu na společných položkách (docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md, oddíl 3).

    Příklad z podkladu manuálu (oddíl 10): A 60 mil., B 40 mil., M 2 mil. (bez podílu), úpisy 1. 1. 2027.
    """

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}, {"code": "M", "shares_common": False}])
        self.a, self.b, self.m = (self.cls(self.fund, code) for code in ("A", "B", "M"))
        self.subscribe(self.a, "2027-01-01", 60_000_000, 60_000_000)
        self.subscribe(self.b, "2027-01-01", 40_000_000, 40_000_000)
        self.subscribe(self.m, "2027-01-01", 2_000_000, 2_000_000)

    def capitals(self, valuation):
        return {line.class_id.code: Decimal(str(line.capital)) for line in valuation.class_line_ids}

    def post(self, day):
        return self.run_to_posted(self.valuation(self.fund, date.fromisoformat(day)))

    def transfer_to_m(self, key, day, from_a, from_b):
        """Přesun hodnoty do M přes vnitřní zúčtování (jako podíl příjemcům z odměny A a B)."""
        self.book(self.fund, key, day, [
            {"role": "internal_clearing", "amount": str(-from_a), "class_id": self.a.id, "movement_type": "class_transfer"},
            {"role": "internal_clearing", "amount": str(-from_b), "class_id": self.b.id, "movement_type": "class_transfer"},
            {"role": "internal_clearing", "amount": str(from_a + from_b), "class_id": self.m.id, "movement_type": "class_transfer"},
        ])

    def test_gain_and_loss_do_not_change_m(self):
        self.common_result(self.fund, "zisk", "2027-01-15", 10_000_000)
        january = self.post("2027-01-31")
        self.assertEqual(self.capitals(january), {"A": 66_000_000, "B": 44_000_000, "M": 2_000_000})
        m = self.result(january, "M")
        self.assertEqual((m.ratio, m.shared_result, m.rounding_amount), (0, 0, 0))
        self.assertEqual(Decimal(str(january.neutral_capital)), 110_000_000)  # sdílená část bez M
        self.common_result(self.fund, "ztrata", "2027-02-15", -10_000_000)
        february = self.post("2027-02-28")
        self.assertEqual(self.capitals(february), {"A": 60_000_000, "B": 40_000_000, "M": 2_000_000})
        self.assertFalse(february.check_ids.filtered(lambda c: c.status == "stop"))

    def test_received_fee_only_in_m_and_tax_borne_by_others(self):
        """Odměna 2 mil. z A a B do M: M 4 mil.; daň 21 % ze sdíleného zisku nesou A a B (D13)."""
        self.env["investra.fee.rule"].create({"fund_id": self.fund.id, "name": "Daň", "kind": "tax",
                                              "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.21})]})
        self.common_result(self.fund, "zisk", "2027-01-15", 10_000_000)
        self.transfer_to_m("odmena", "2027-01-20", 1_200_000, 800_000)
        january = self.post("2027-01-31")
        capitals = self.capitals(january)
        self.assertEqual(capitals["M"], 4_000_000)
        # Sdílený zisk 10 mil. − daň 2,1 mil. = 7,9 mil. poměrem 60/40; přesun do M nese A 1,2 a B 0,8.
        self.assertEqual(capitals["A"], Decimal("60000000") + Decimal("4740000") - Decimal("1200000"))
        self.assertEqual(capitals["B"], Decimal("40000000") + Decimal("3160000") - Decimal("800000"))
        self.assertEqual(sum(capitals.values()), Decimal(str(january.fund_capital)))

    def test_recipient_rule_gives_whole_share_to_m(self):
        """Pravidlo úplaty tříd A a B s podílem příjemcům 100 % do M: M dostane celou úplatu, náklad fondu žádný."""
        rule = self.env["investra.fee.rule"].create({
            "fund_id": self.fund.id, "name": "Odměna manažera", "kind": "periodic",
            "class_ids": [Command.set((self.a | self.b).ids)], "recipient_share": 1,
            "recipient_class_ids": [Command.set(self.m.ids)],
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.01})],
        })
        self.assertFalse(rule.no_common_class_warning)
        january = self.post("2027-01-31")
        capitals = self.capitals(january)
        self.assertGreater(capitals["M"], 2_000_000)
        self.assertEqual(sum(capitals.values()), 102_000_000)
        self.assertEqual(capitals["M"] - 2_000_000, (100_000_000 - capitals["A"] - capitals["B"]))
        check = january.check_ids.filtered(lambda c: c.code == "fee_no_common_class")
        self.assertEqual(check.status, "ok")

    def test_symbolic_subscription_redemption_and_manual_fee(self):
        fund = self.make_fund(classes=[{"code": "A"}, {"code": "M", "shares_common": False}])
        a, m = self.cls(fund, "A"), self.cls(fund, "M")
        self.subscribe(a, "2027-01-01", 1_000_000, 1_000_000)
        self.subscribe(m, "2027-01-01", 1, 1)
        self.common_result(fund, "zisk", "2027-01-15", 50_000)
        january = self.run_to_posted(self.valuation(fund, date(2027, 1, 31)))
        self.assertEqual(self.capitals(january), {"A": 1_050_000, "M": 1})
        self.subscribe(m, "2027-02-10", 2_000, 2_000)
        self.subscribe(m, "2027-02-20", 1_000, 1_000, kind="redemption")
        february = self.valuation(fund, date(2027, 2, 28))
        self.manual_fee(february, 100, class_id=m.id)
        self.run_to_posted(february)
        # Ruční úplata na M je jediná ztráta M; úpis a odkup M jen mění její kapitál.
        self.assertEqual(self.capitals(february), {"A": 1_050_000, "M": 1 + 2_000 - 1_000 - 100})

    def test_waterfall_only_between_sharing_classes(self):
        Scheme = self.env["investra.allocation.scheme"]
        with self.assertRaises(ValidationError):
            Scheme.create({"fund_id": self.fund.id, "valid_from": "2020-01-01", "method": "waterfall",
                           "line_ids": [(0, 0, {"class_id": self.m.id, "residual_share": 1})]})
        Scheme.create({"fund_id": self.fund.id, "valid_from": "2020-01-01", "method": "waterfall", "line_ids": [
            (0, 0, {"class_id": self.a.id, "rank": 1, "target_rate": 0.06}),
            (0, 0, {"class_id": self.b.id, "rank": 2, "residual_share": 1, "loss_rank": 1}),
        ]})
        self.common_result(self.fund, "zisk", "2027-06-01", 10_000_000)
        december = self.valuation(self.fund, date(2027, 12, 31))
        december.action_compute()
        # Cíl A = 60 mil. × 6 % (rok) = 3,6 mil., zbytek 6,4 mil. B; M beze změny.
        self.assertEqual(self.capitals(december), {"A": 63_600_000, "B": 46_400_000, "M": 2_000_000})
        with self.assertRaises(ValidationError):
            self.b.shares_common = False

    def test_zero_capital_of_sharing_classes_stops(self):
        fund = self.make_fund(classes=[{"code": "A"}, {"code": "M", "shares_common": False}])
        self.subscribe(self.cls(fund, "M"), "2027-01-01", 1000, 1000)
        valuation = self.valuation(fund, date(2027, 1, 31))
        with self.assertRaisesRegex(UserError, "podílejí na společných položkách"):
            valuation.action_compute()

    def test_lock_after_posted_valuation_and_at_least_one_sharing_class(self):
        with self.assertRaises(ValidationError):
            (self.a | self.b).write({"shares_common": False})
        self.b.shares_common = False  # před prvním zaúčtovaným oceněním jde změnit
        self.b.shares_common = True
        self.post("2027-01-31")
        with self.assertRaises(UserError):
            self.m.shares_common = True
        self.m.name = "Manažerská"  # jiná pole zámek nedrží

    def test_warning_for_fee_paid_by_class_without_share(self):
        fund_rule = self.env["investra.fee.rule"].create({
            "fund_id": self.fund.id, "name": "Obhospodařování", "kind": "periodic",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.01})],
        })
        self.assertIn("Třída M se nepodílí na společných položkách", fund_rule.no_common_class_warning)
        class_rule = self.env["investra.fee.rule"].create({
            "fund_id": self.fund.id, "name": "Úplata A", "kind": "periodic", "class_ids": [Command.set(self.a.ids)],
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.01})],
        })
        self.assertFalse(class_rule.no_common_class_warning)
        valuation = self.valuation(self.fund, date(2027, 1, 31))
        valuation.action_compute()
        check = valuation.check_ids.filtered(lambda c: c.code == "fee_no_common_class")
        self.assertEqual(check.status, "warning")
        self.assertIn("Obhospodařování", check.detail)
        # Úplatu celého fondu nese M nulovým poměrem: M beze změny.
        self.assertEqual(self.capitals(valuation)["M"], 2_000_000)

    def test_fund_without_such_class_has_no_new_check(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 1000, 1000)
        valuation = self.valuation(fund, date(2027, 1, 31))
        valuation.action_compute()
        self.assertFalse(valuation.check_ids.filtered(lambda c: c.code == "fee_no_common_class"))
