"""Ruční kontrolní příklady: očekávaná čísla jsou spočítaná mimo kód."""
import unittest
from decimal import Decimal

from nav_reference import compute, split_with_remainder


def fund(classes, valuations):
    return {"currency": "CZK", "classes": classes, "valuations": valuations}


def cls(code, capital, units, **kw):
    return {"code": code, "opening_capital": capital, "opening_units": units, "price_digits": 4, **kw}


class Reference(unittest.TestCase):
    def test_architecture_example(self):
        # Třídy po 100, fee A 10, společný výnos 19: 0,5 × 219 − 10 = 99,5; 0,5 × 219 = 109,5
        row = compute(fund([cls("A", 100, 100), cls("B", 100, 100)], [
            {"date": "2027-01-31", "common_result": 19, "specific": {"A": -10}},
        ]))[0]
        self.assertEqual(row["fk"], "209.00")
        self.assertEqual(row["nfk"], "219.00")
        self.assertEqual(row["fkt"], {"A": "99.50", "B": "109.50"})

    def test_delta_restarts_after_valuation(self):
        # Druhé ocenění: poměr 99,5 : 109,5, výnos 20,9 → 109,45 a 120,45... ΔT už nevstupuje znovu
        rows = compute(fund([cls("A", 100, 100), cls("B", 100, 100)], [
            {"date": "2027-01-31", "common_result": 19, "specific": {"A": -10}},
            {"date": "2027-02-28", "common_result": "20.9"},
        ]))
        self.assertEqual(rows[1]["fkt"], {"A": "109.45", "B": "120.45"})

    def test_subscription_enters_ratio(self):
        # A 100 + úpis 100, B 100: poměr 2 : 1, výnos 30 → 220 a 110
        row = compute(fund([cls("A", 100, 100), cls("B", 100, 100)], [
            {"date": "2027-01-31", "common_result": 30,
             "subscriptions": {"A": {"amount": 100, "units": 100}}},
        ]))[0]
        self.assertEqual(row["fkt"], {"A": "220.00", "B": "110.00"})
        self.assertEqual(row["price"], {"A": "1.1000", "B": "1.1000"})

    def test_price_rounds_down(self):
        row = compute(fund([cls("A", 100, 3)], [{"date": "2027-01-31"}]))[0]
        self.assertEqual(row["price"]["A"], "33.3333")

    def test_eur_class(self):
        # 2 534,50 CZK / 25,345 = 100 EUR, 10 kusů = 10 EUR
        row = compute(fund([cls("E", "2534.50", 10, currency="EUR", price_digits=5)], [
            {"date": "2027-01-31", "fx": {"EUR": "25.345"}},
        ]))[0]
        self.assertEqual(row["price"]["E"], "10.00000")

    def test_fee_on_base_after_fee(self):
        # FK 1 010 po úplatě 1 % z FK po úplatě: 1 000 + 10
        row = compute(fund([cls("A", 1010, 100)], [
            {"date": "2027-01-31", "mgmt_fee": {"rate": "0.01", "days": 365, "basis": 365, "base": "after"}},
        ]))[0]
        self.assertEqual(row["mgmt_fee"], "10.00")
        self.assertEqual(row["fk"], "1000.00")

    def test_performance_fee_top_up_goes_negative(self):
        # Kusů 100, HWM 1: kurz 1,5 → 20 % × 0,5 × 100 = 10; zisk se ztratí → doplatek −10
        rows = compute(fund([cls("A", 100, 100)], [
            {"date": "2027-01-31", "common_result": 50, "perf_fee": {"A": {"rate": "0.2", "hwm": 1}}},
            {"date": "2027-02-28", "common_result": -50, "perf_fee": {"A": {"rate": "0.2", "hwm": 1}}},
        ]))
        self.assertEqual(rows[0]["perf_moves"]["A"], "10.00")
        self.assertEqual(rows[0]["fkt"]["A"], "140.00")
        self.assertEqual(rows[1]["perf_moves"]["A"], "-10.00")
        self.assertEqual(rows[1]["fkt"]["A"], "100.00")

    def test_tax_top_up_never_below_zero(self):
        # Zisk 100 při 5 % = 5; ztráta 200 → základ záporný, daň se vrací na 0
        rows = compute(fund([cls("A", 1000, 100)], [
            {"date": "2027-01-31", "common_result": 100, "tax": {"rate": "0.05"}},
            {"date": "2027-02-28", "common_result": -200, "tax": {"rate": "0.05"}},
        ]))
        self.assertEqual(rows[0]["tax_move"], "5.00")
        self.assertEqual(rows[1]["tax_move"], "-5.00")
        self.assertEqual(rows[1]["fk"], "900.00")

    def test_remainder_goes_to_largest_class(self):
        split = split_with_remainder({"A": Decimal("33.335"), "B": Decimal("33.335"), "C": Decimal("33.33")})
        self.assertEqual(sum(split.values()), Decimal("100.00"))


if __name__ == "__main__":
    unittest.main()
