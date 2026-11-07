"""Testy výpočetního jádra. Očekávané hodnoty jsou spočítané ručně, v komentáři je výpočet."""
import importlib.util
import unittest
from datetime import date
from decimal import Decimal as D
from pathlib import Path

path = Path(__file__).resolve().parents[2] / "addons/custom/investra_nav/engine.py"
spec = importlib.util.spec_from_file_location("engine", path)
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)

JAN1, DEC31_25, DEC31_26 = date(2026, 1, 1), date(2025, 12, 31), date(2026, 12, 31)
V = lambda **k: {"valid_from": date(2020, 1, 1), **k}


class Periodic(unittest.TestCase):
    def test_percent_year(self):
        r = e.periodic_fee({"versions": [V(rate="0.02")]}, DEC31_25, DEC31_26, 1000000)
        self.assertEqual(r["amount"], D("20000.00"))

    def test_rate_change_mid_period(self):
        # 2 % do 30. 6. (181 dní), 1 % od 1. 7. (184 dní): 1 000 000 × (0,02×181 + 0,01×184) / 365
        rule = {"versions": [V(rate="0.02"), {"valid_from": date(2026, 7, 1), "rate": "0.01"}]}
        r = e.periodic_fee(rule, DEC31_25, DEC31_26, 1000000)
        self.assertEqual(len(r["segments"]), 2)
        self.assertEqual(r["amount"], D("14958.90"))

    def test_missing_rate_is_error(self):
        with self.assertRaises(ValueError):
            e.periodic_fee({"versions": [{"valid_from": date(2026, 7, 1), "rate": "0.01"}]}, DEC31_25, DEC31_26, 1)

    def test_fixed_plus_percent_above_threshold(self):
        # 58 000 × 12 + 0,08 % z (500 − 280 mil.) = 696 000 + 176 000
        rule = {"versions": [V(fixed_monthly=58000, rate="0.0008", threshold=280000000)]}
        self.assertEqual(e.periodic_fee(rule, DEC31_25, DEC31_26, 500000000)["amount"], D("872000.00"))

    def test_sliding_tiers(self):
        # 0 do 300 mil., 0,30 % z 200 mil., 0,25 % z 100 mil.: 600 000 + 250 000
        rule = {"versions": [V(tiers=[{"from": 0, "rate": 0}, {"from": 300000000, "rate": "0.003"},
                                      {"from": 500000000, "rate": "0.0025"}])]}
        self.assertEqual(e.periodic_fee(rule, DEC31_25, DEC31_26, 600000000)["amount"], D("850000.00"))

    def test_step_price(self):
        # 45 000 do 500 mil., +10 000 za každých započatých 500 mil.; 1,2 mld. = dvě pásma navíc = 65 000
        rule = {"versions": [V(fixed_monthly=45000, step_size=500000000, step_amount=10000)]}
        rule["versions"][0]["fixed_mode"] = "started_month"
        self.assertEqual(e.periodic_fee(rule, date(2026, 1, 31), date(2026, 2, 28), 1200000000)["amount"], D("65000.00"))

    def test_min_and_max_per_year(self):
        # 0,1 % s minimem 200 000 a maximem 1 250 000 ročně
        rule = {"versions": [V(rate="0.001", min_annual=200000, max_annual=1250000)]}
        self.assertEqual(e.periodic_fee(rule, DEC31_25, DEC31_26, 100000000)["amount"], D("200000.00"))
        self.assertEqual(e.periodic_fee(rule, DEC31_25, DEC31_26, 5000000000)["amount"], D("1250000.00"))
        self.assertEqual(e.periodic_fee(rule, DEC31_25, DEC31_26, 500000000)["amount"], D("500000.00"))

    def test_extra_class_surcharge(self):
        # 30 000 + 10 000 za pátou a další třídu; 6 tříd: 50 000 měsíčně
        rule = {"versions": [V(fixed_monthly=30000, included_classes=4, extra_class_monthly=10000,
                               fixed_mode="started_month")]}
        self.assertEqual(e.periodic_fee(rule, date(2026, 1, 31), date(2026, 2, 28), 0, classes_count=6)["amount"],
                         D("50000.00"))

    def test_base_after_fee_iterates(self):
        # 1 % z FK po úplatě: 1 010 = 1 000 + 10
        r = e.periodic_fee({"base_mode": "after", "versions": [V(rate="0.01")]}, DEC31_25, DEC31_26, 1010)
        self.assertEqual(r["amount"], D("10.00"))
        self.assertGreater(r["steps"], 1)

    def test_months_basis(self):
        # 1,5 % p.a. × 3/12 z 1 000 000
        rule = {"basis": "months", "versions": [V(rate="0.015")]}
        self.assertEqual(e.periodic_fee(rule, date(2026, 3, 31), date(2026, 6, 30), 1000000)["amount"], D("3750.00"))

    def test_leap_year_act_act(self):
        self.assertEqual(e.year_fraction(date(2027, 12, 31), date(2028, 12, 31), "act_act"), D(1))


class DayCount(unittest.TestCase):
    def test_30_360_full_year(self):
        self.assertEqual(e.year_fraction(date(2026, 1, 15), date(2027, 1, 15), "thirty360_eu"), D(1))

    def test_30e_treats_31_as_30(self):
        # 31. 1. → 31. 3.: 60 dní
        self.assertEqual(e.year_fraction(date(2026, 1, 31), date(2026, 3, 31), "thirty360_eu"), D(60) / 360)

    def test_us_keeps_31_when_start_before_30(self):
        # 15. 1. → 31. 3.: americká 76 dní, evropská 75 dní
        self.assertEqual(e.year_fraction(date(2026, 1, 15), date(2026, 3, 31), "thirty360_us"), D(76) / 360)
        self.assertEqual(e.year_fraction(date(2026, 1, 15), date(2026, 3, 31), "thirty360_eu"), D(75) / 360)

    def test_february_end_in_30e(self):
        # 28. 2. → 31. 3.: 32 dní
        self.assertEqual(e.year_fraction(date(2026, 2, 28), date(2026, 3, 31), "thirty360_eu"), D(32) / 360)

    def test_act360_is_longer_than_year(self):
        self.assertEqual(e.year_fraction(DEC31_25, DEC31_26, "act360"), D(365) / 360)

    def test_act_act_splits_leap_year(self):
        # 30. 6. 2027 → 30. 6. 2028: 184/365 + 182/366
        self.assertEqual(e.year_fraction(date(2027, 6, 30), date(2028, 6, 30), "act_act"), D(184) / 365 + D(182) / 366)


    def test_act_act_icma_full_coupon_is_one_over_frequency(self):
        # Pololetní kupón: celé období je 1/2 roku bez ohledu na délku období
        self.assertEqual(e.act_act_icma(date(2026, 1, 1), date(2026, 7, 1), date(2026, 1, 1), date(2026, 7, 1), 2), D("0.5"))

    def test_act_act_icma_part_of_coupon(self):
        # 90 dní z 181denního období, dva kupóny ročně: 90 / (181 × 2)
        self.assertEqual(e.act_act_icma(date(2026, 1, 1), date(2026, 4, 1), date(2026, 1, 1), date(2026, 7, 1), 2), D(90) / D(362))


class EffectiveRate(unittest.TestCase):
    ZERO = [(date(2026, 1, 1), -950), (date(2027, 1, 1), 1000)]
    BOND = [(date(2026, 1, 1), -1000), (date(2027, 1, 1), 50), (date(2028, 1, 1), 1050)]

    def test_discount_instrument(self):
        # 1 000 / 950 − 1 = 5,263158 %
        self.assertAlmostEqual(float(e.effective_rate(self.ZERO)), 1000 / 950 - 1, places=6)

    def test_par_bond_equals_coupon(self):
        # Přestupný rok v druhém období dává jen malou odchylku proti kupónu 5 %
        self.assertAlmostEqual(float(e.effective_rate(self.BOND)), 0.05, places=3)

    def test_amortised_cost_at_start_and_maturity(self):
        self.assertEqual(e.amortised_cost(self.ZERO, date(2026, 1, 1)), D("950.00"))
        self.assertEqual(e.amortised_cost(self.ZERO, date(2026, 12, 31)), D("999.86"))

    def test_eir_differs_from_linear_midway(self):
        # Polovina doby: 950 × 1,05263^(181/365) = 974,47; lineárně 950 + 50 × 181/365 = 974,79
        day = date(2026, 7, 1)
        self.assertEqual(e.amortised_cost(self.ZERO, day), D("974.47"))
        self.assertEqual(e.linear_accrual(950, 1000, date(2026, 1, 1), date(2027, 1, 1), day), D("974.79"))

    def test_no_solution_is_error(self):
        with self.assertRaises(ValueError):
            e.effective_rate([(date(2026, 1, 1), 100), (date(2027, 1, 1), 100)])


class Performance(unittest.TestCase):
    Y = dict(start=DEC31_25, end=DEC31_26)

    def test_hwm_only_capital(self):
        # 20 % z (120 − 100)
        r = e.performance_fee({"rate": "0.2", "reference": 100, "hwm": 100}, gross=120, **self.Y)
        self.assertEqual(r["required"], D("4.00"))

    def test_no_fee_below_hwm(self):
        r = e.performance_fee({"rate": "0.2", "reference": 100, "hwm": 130}, gross=120, **self.Y)
        self.assertEqual(r["required"], D("0.00"))

    def test_top_up_can_be_negative(self):
        r = e.performance_fee({"rate": "0.2", "reference": 100, "hwm": 100}, gross=110, accrued=4, **self.Y)
        self.assertEqual(r["move"], D("-2.00"))

    def test_hard_hurdle_with_flows(self):
        # Kapitál 1 000, hurdle 5 %, vstup 100 k 30. 6. (184 dní): cíl 1 050 + 100 × (1 + 0,05 × 184/365) = 1 152,52
        # hrubě 1 200, přebytek 47,48; při 100 % odměna 47,48
        r = e.performance_fee({"rate": 1, "reference": 1000, "hurdle_kind": "fixed", "hurdle_rate": "0.05"},
                              gross=1200, flows=[(date(2026, 6, 30), 100)], **self.Y)
        self.assertEqual(r["required"], D("47.48"))

    def test_shortfall_reported_for_cover(self):
        # Cíl 1 052,50 (5,25 %), hrubě 1 030: chybí 22,50
        r = e.performance_fee({"rate": 1, "reference": 1000, "hurdle_kind": "fixed", "hurdle_rate": "0.0525"},
                              gross=1030, **self.Y)
        self.assertEqual(r["required"], D("0.00"))
        self.assertEqual(r["shortfall"], D("22.50"))

    def test_soft_hurdle_with_full_catch_up(self):
        # 8 % hurdle, zisk 30 z 100: 20 % z celého zisku = 6
        spec = {"rate": "0.2", "reference": 100, "hurdle_kind": "fixed", "hurdle_rate": "0.08",
                "hurdle_type": "soft", "catch_up": 1}
        self.assertEqual(e.performance_fee(spec, gross=130, **self.Y)["required"], D("6.00"))
        # Zisk 9: dohánění omezí na přebytek 1
        self.assertEqual(e.performance_fee(spec, gross=109, **self.Y)["required"], D("1.00"))

    def test_index_benchmark_with_margin(self):
        # Index 100 → 104, marže 2 %: faktor 1,06; 100 → 110: 20 % ze 4
        spec = {"rate": "0.2", "reference": 100, "hurdle_kind": "index", "index_start": 100, "index_end": 104,
                "hurdle_margin": "0.02"}
        self.assertEqual(e.performance_fee(spec, gross=110, **self.Y)["required"], D("0.80"))

    def test_high_on_high_example_from_public_statute(self):
        # Příklad z veřejného statutu: referenční hodnota 1 000, sazba 20 %
        spec = {"measure": "unit", "rate": "0.2", "reference": 1000, "hwm": 1000}
        fee = lambda value, s=spec: e.performance_fee(s, gross=value, units=1, **self.Y)["required"]
        self.assertEqual(1100 - fee(1100), D("1080.00"))
        self.assertEqual(800 - fee(800), D("800.00"))
        self.assertEqual(1050 - fee(1050), D("1040.00"))
        # Po krystalizaci je referencí hodnota po odměně 1 040
        following = {**spec, "reference": 1040, "hwm": 1040}
        self.assertEqual(1200 - fee(1200, following), D("1168.00"))

    def test_negative_benchmark_floored_to_zero(self):
        # Index −10 %, fond +5 %: s podlahou se platí jen z kladné výkonnosti, 30 % z 5
        spec = {"rate": "0.3", "reference": 100, "hurdle_kind": "index", "index_start": 100, "index_end": 90,
                "hurdle_floor_zero": True}
        self.assertEqual(e.performance_fee(spec, gross=105, **self.Y)["required"], D("1.50"))

    def test_hwm_limits_fee_when_closer_than_benchmark(self):
        # Etalon 110 by dal přebytek 10, ale HWM 115 omezí přebytek na 5
        spec = {"rate": "0.3", "reference": 100, "hwm": 115, "hurdle_kind": "fixed", "hurdle_rate": "0.1"}
        self.assertEqual(e.performance_fee(spec, gross=120, **self.Y)["required"], D("1.50"))

    def test_benchmark_fee_allowed_on_negative_return(self):
        # Index −10 %, fond −5 %: 12 % z 5 i při záporné výkonnosti
        spec = {"rate": "0.12", "reference": 100, "hurdle_kind": "index", "index_start": 100, "index_end": 90}
        self.assertEqual(e.performance_fee(spec, gross=95, **self.Y)["required"], D("0.60"))
        spec["require_positive_return"] = True
        self.assertEqual(e.performance_fee(spec, gross=95, **self.Y)["required"], D("0.00"))

    def test_unit_measure_multiplies_units(self):
        # Kus 100 → 110, 1 000 kusů, 20 %: 2 000
        r = e.performance_fee({"measure": "unit", "rate": "0.2", "reference": 100, "hwm": 100},
                              gross=110000, units=1000, **self.Y)
        self.assertEqual(r["required"], D("2000.00"))

    def test_average_nav_base(self):
        # Kus 100 → 104, benchmark 1 %, přebytek 3 %, průměrný NAV 1 020 000: 20 % × 3 % × 1 020 000 = 6 120
        spec = {"measure": "unit", "rate": "0.2", "reference": 100, "hurdle_kind": "index", "index_start": 100,
                "index_end": 101, "average_base": 1020000}
        self.assertEqual(e.performance_fee(spec, gross=1040000, units=10000, **self.Y)["required"], D("6120.00"))

    def test_probability_weighting(self):
        spec = {"rate": "0.2", "reference": 100, "hwm": 100, "probability": "0.5"}
        self.assertEqual(e.performance_fee(spec, gross=120, **self.Y)["required"], D("2.00"))

    def test_net_floor_waiver(self):
        # Odměna by byla 4, ale čistá hodnota nesmí klesnout pod 118
        spec = {"rate": "0.2", "reference": 100, "hwm": 100, "net_floor": 118}
        self.assertEqual(e.performance_fee(spec, gross=120, **self.Y)["required"], D("2.00"))

    def test_redemption_crystallises_share(self):
        self.assertEqual(e.crystallise_on_redemption(100, 25, 100), D("25.00"))


class ClassSplit(unittest.TestCase):
    def test_split_keeps_total(self):
        parts = e.split_amount("100.00", {"A": 1, "B": 1, "C": 1})
        self.assertEqual(sum(parts.values()), D("100.00"))

    def test_priority_paid_then_residual(self):
        # Zisk 100: PIA nárok 60, zbytek 40 na VIA a MIA 74 : 26
        r = e.waterfall(100, {"PIA": 1000, "VIA": 100, "MIA": 50}, [{"PIA": 60}], {"VIA": "0.74", "MIA": "0.26"})
        self.assertEqual(r, {"PIA": D("60.00"), "VIA": D("29.60"), "MIA": D("10.40")})

    def test_priority_short_is_pro_rata_between_targets(self):
        # Zisk 30, nároky 40 a 20: dělí se 2 : 1
        r = e.waterfall(30, {"P1": 1, "P2": 1, "V": 1}, [{"P1": 40, "P2": 20}], {"V": 1})
        self.assertEqual(r, {"P1": D("20.00"), "P2": D("10.00"), "V": D("0")})

    def test_half_residual_by_capital(self):
        # Zbytek 100: polovina podle kapitálů 3 : 1, polovina na VIA
        r = e.waterfall(100, {"P": 300, "V": 100}, [], {"V": 1}, residual_pro_rata="0.5")
        self.assertEqual(r, {"P": D("37.50"), "V": D("62.50")})

    def test_loss_hits_junior_first_until_exhausted(self):
        # Ztráta 150: VIA 100 vyčerpána, zbytek 50 nese PIA
        r = e.waterfall(-150, {"PIA": 1000, "VIA": 100}, [], loss_order=["VIA"])
        self.assertEqual(r, {"PIA": D("-50.00"), "VIA": D("-100")})

    def test_loss_pro_rata(self):
        r = e.waterfall(-100, {"A": 300, "B": 100}, [])
        self.assertEqual(r, {"A": D("-75.00"), "B": D("-25.00")})


if __name__ == "__main__":
    unittest.main()
