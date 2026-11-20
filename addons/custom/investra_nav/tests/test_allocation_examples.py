from datetime import date
from decimal import Decimal

from odoo.tests import tagged

from .. import engine
from .common import NavCase

M = Decimal(1_000_000)


@tagged("post_install", "-at_install")
class TestAllocationExamples(NavCase):
    """Čísla podkladu manuálu, kapitola 10 (docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md, oddíl 10):
    „Alokační schéma“ (P = prioritní, V = výkonnostní, P 80 mil., V 20 mil., období 1 rok) a „Třída bez podílu“."""

    def waterfall(self, change, capitals, tiers, residual, pro_rata=0, loss_order=()):
        result = engine.waterfall(Decimal(change) * M, {k: Decimal(v) * M for k, v in capitals.items()},
                                  [{k: Decimal(str(v)) * M for k, v in tier.items()} for tier in tiers],
                                  residual, Decimal(str(pro_rata)), loss_order)
        return {k: v / M for k, v in result.items()}

    def basic(self, change):
        # P: pořadí 1, cíl 6 % → 80 × 6 % = 4,8; V: podíl na zbytku 1,0, pořadí ve ztrátě 1.
        return self.waterfall(change, {"P": 80, "V": 20}, [{"P": 4.8}], {"V": 1}, loss_order=["V"])

    def test_basic_scheme(self):
        self.assertEqual(self.basic(10), {"P": Decimal("4.8"), "V": Decimal("5.2")})
        # Proti poměru 8,0 / 2,0 přesun 3,2 mil. z P do V.
        self.assertEqual(Decimal("8.0") - self.basic(10)["P"], Decimal("3.2"))
        self.assertEqual(self.basic(3), {"P": Decimal("3"), "V": Decimal("0")})
        self.assertEqual(self.basic(3)["P"] - Decimal("2.4"), Decimal("0.6"))  # přesun 0,6 z V do P
        self.assertEqual(self.basic(-5), {"P": Decimal("0"), "V": Decimal("-5")})
        self.assertEqual(self.basic(-30), {"P": Decimal("-10"), "V": Decimal("-20")})

    def test_half_residual_pro_rata(self):
        result = self.waterfall(10, {"P": 80, "V": 20}, [{"P": 4.8}], {"V": 1}, pro_rata=0.5, loss_order=["V"])
        self.assertEqual(result, {"P": Decimal("6.88"), "V": Decimal("3.12")})

    def test_two_priority_classes(self):
        # P1 50 mil. pořadí 1 cíl 5 % = 2,5; P2 30 mil. pořadí 2 cíl 7 % = 2,1; V 20 mil. zbytek.
        result = self.waterfall(3, {"P1": 50, "P2": 30, "V": 20}, [{"P1": 2.5}, {"P2": 2.1}], {"V": 1})
        self.assertEqual(result, {"P1": Decimal("2.5"), "P2": Decimal("0.5"), "V": Decimal("0")})

    def test_monthly_target(self):
        # Cíl za měsíc = kapitál × 6 % × 31/365 (část roku od minulého ocenění, act365).
        fraction = engine.year_fraction(date(2027, 1, 31), date(2027, 3, 3), "act365")
        self.assertEqual(fraction, Decimal(31) / Decimal(365))

    def test_basic_scheme_in_valuation(self):
        """Základní příklad v ocenění: zisk 10 mil. za rok → P 84,8, V 25,2 (přesun podle pořadí nároků 3,2 mil.)."""
        fund = self.make_fund(classes=[{"code": "P"}, {"code": "V"}])
        p, v = self.cls(fund, "P"), self.cls(fund, "V")
        self.subscribe(p, "2027-01-01", 80_000_000, 80_000_000)
        self.subscribe(v, "2027-01-01", 20_000_000, 20_000_000)
        self.common_result(fund, "zisk", "2027-06-01", 10_000_000)
        self.env["investra.allocation.scheme"].create({"fund_id": fund.id, "valid_from": "2020-01-01", "method": "waterfall", "line_ids": [
            (0, 0, {"class_id": p.id, "rank": 1, "target_rate": 0.06}),
            (0, 0, {"class_id": v.id, "rank": 2, "residual_share": 1, "loss_rank": 1}),
        ]})
        valuation = self.valuation(fund, date(2027, 12, 31))
        valuation.action_compute()
        self.assertAlmostEqual(self.result(valuation, "P").capital, 84_800_000, places=2)
        self.assertAlmostEqual(self.result(valuation, "V").capital, 25_200_000, places=2)
        self.assertAlmostEqual(self.result(valuation, "V").allocation_amount, 3_200_000, places=2)

    def test_class_without_share_example(self):
        """A 60, B 40, M 2 (bez podílu), zisk 10 mil.: bez volby by M dostala 0,196 mil.; s volbou A +6, B +4, M 0."""
        self.assertEqual(round(Decimal(10) * 2 / 102, 3), Decimal("0.196"))
        fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}, {"code": "M", "shares_common": False}])
        for code, amount in (("A", 60), ("B", 40), ("M", 2)):
            self.subscribe(self.cls(fund, code), "2027-01-01", amount * 1_000_000, amount * 1_000_000)
        self.common_result(fund, "zisk", "2027-01-15", 10_000_000)
        valuation = self.valuation(fund, date(2027, 1, 31))
        valuation.action_compute()
        self.assertEqual({l.class_id.code: l.capital for l in valuation.class_line_ids},
                         {"A": 66_000_000, "B": 44_000_000, "M": 2_000_000})
