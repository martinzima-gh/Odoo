"""ZJ-14: úplata z průměrného FK po třídách (pravidlo s base_source = average_fk a vyplněnými Platí třídy).

Referenční příklad spočetl Martin ručně (docs/ukoly/ZJ-14): 3,65 % p. a., ACT/365, bez pevných částek; ocenění 31. 1., 28. 2.,
31. 3. 2027. V Odoo běží s krokem 2: dnešní bod je hodnota třídy po vlastní úplatě a rovná se uloženému kapitálu, takže body
průměru jsou přesně ruční čísla (u kroku 1 je dnešní bod před úplatou a uložený kapitál po ní, obě čísla ručního příkladu by
nemohla platit zároveň; krok 1 ověřuje samostatný test). Hodnotu třídy nastavují specifické výsledky třídy.
Fond vzniká 30. 12. 2026 a úpisy A a C jsou 31. 12. 2026: úpis ke dni vzniku by do prvního období nespadl, začátek nároku
je přesto 31. 12. 2026 (nejpozdější z 31. 12. minulého roku a prvního úpisu), tedy 31 dní v lednu jako v ručním příkladu.
"""

import json
from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import NavCase

JANUARY, FEBRUARY, MARCH = date(2027, 1, 31), date(2027, 2, 28), date(2027, 3, 31)


@tagged("post_install", "-at_install")
class TestAverageByClass(NavCase):
    def setUp(self):
        super().setUp()
        self.Rule = self.env["investra.fee.rule"]

    def fund(self, classes=("A", "B", "C")):
        return self.make_fund(launch="2026-12-30", classes=[{"code": c} for c in classes])

    def rule(self, fund, codes, step="2", **values):
        classes = fund.class_ids.filtered(lambda c: c.code in codes)
        return self.Rule.create({
            "fund_id": fund.id, "name": "Obhospodařování", "kind": "periodic", "base_source": "average_fk",
            "base_step": step, "expense_role": "expense_management", "class_ids": [(6, 0, classes.ids)],
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.0365})], **values})

    def lines(self, valuation, rule):
        return {line.class_id.code: (line, json.loads(line.detail))
                for line in valuation.fee_line_ids.filtered(lambda l: l.rule_id == rule)}

    def check(self, valuation, code):
        return valuation.check_ids.filtered(lambda c: c.code == code)

    def consistent(self, valuation):
        self.assertEqual(self.check(valuation, "fee_consistency").status, "ok", self.check(valuation, "fee_consistency").detail)

    def assertDetail(self, detail, start, points, today, average, entitlement, booked):
        self.assertTrue(detail["per_class"])
        self.assertEqual(detail["start"], start)
        self.assertEqual([[day, round(float(value), 2)] for day, value in detail["points"]], points)
        self.assertAlmostEqual(float(detail["today"]), today, places=2)
        self.assertAlmostEqual(float(detail["average"]), average, places=2)
        self.assertAlmostEqual(float(detail["entitlement"]), entitlement, places=2)
        self.assertAlmostEqual(float(detail["booked"]), booked, places=2)

    # --- referenční příklad -------------------------------------------------------------------------------------------

    def test_reference_example(self):
        fund = self.fund()
        a, b, c = (self.cls(fund, code) for code in "ABC")
        self.subscribe(a, "2026-12-31", 1000000, 1000)
        self.subscribe(c, "2026-12-31", 300000, 300)
        rule = self.rule(fund, ("A", "B"))

        # 31. 1.: A průměr 1 000 000, 31 dní → 3 100 (hodnota třídy před úplatou 1 003 100). B ještě nemá úpis.
        self.specific(fund, a, "a1", "2027-01-20", 3100)
        january = self.run_to_posted(self.valuation(fund, JANUARY))
        lines = self.lines(january, rule)
        self.assertEqual(set(lines), {"A"})
        line, detail = lines["A"]
        self.assertAlmostEqual(line.amount, 3100, places=2)
        self.assertDetail(detail, "2026-12-31", [], 1000000, 1000000, 3100, 0)
        self.assertAlmostEqual(self.result(january, "A").capital, 1000000, places=2)
        self.consistent(january)

        # 28. 2.: A body [1 000 000], dnes 1 010 000 → průměr 1 005 000, 59 dní, nárok 5 929,50, pohyb 2 829,50.
        # B úpis 15. 2. 500 000: dnes 500 000, 13 dní → 650.
        self.specific(fund, a, "a2", "2027-02-20", 12829.50)
        self.subscribe(b, "2027-02-15", 500000, 500)
        self.specific(fund, b, "b2", "2027-02-20", 650)
        february = self.run_to_posted(self.valuation(fund, FEBRUARY))
        lines = self.lines(february, rule)
        line, detail = lines["A"]
        self.assertAlmostEqual(line.amount, 2829.50, places=2)
        self.assertDetail(detail, "2026-12-31", [["2027-01-31", 1000000]], 1010000, 1005000, 5929.50, 3100)
        line, detail = lines["B"]
        self.assertAlmostEqual(line.amount, 650, places=2)
        self.assertDetail(detail, "2027-02-15", [], 500000, 500000, 650, 0)
        self.assertAlmostEqual(self.result(february, "A").capital, 1010000, places=2)
        self.assertAlmostEqual(self.result(february, "B").capital, 500000, places=2)
        self.consistent(february)

        # C do pravidla po ocenění 28. 2.
        rule.class_ids = [(4, c.id)]
        # 31. 3.: A body [1 000 000; 1 010 000], dnes 1 020 000 → průměr 1 010 000, 90 dní, nárok 9 090, pohyb 3 160,50.
        # B body [500 000], dnes 505 000 → průměr 502 500, 44 dní, nárok 2 211, pohyb 1 561.
        # C začátek 28. 2. (zařazení), jen dnešní bod 300 000, 31 dní → 930.
        self.specific(fund, a, "a3", "2027-03-20", 13160.50)
        self.specific(fund, b, "b3", "2027-03-20", 6561)
        self.specific(fund, c, "c3", "2027-03-20", 930)
        march = self.valuation(fund, MARCH)
        march.action_compute()
        lines = self.lines(march, rule)
        line, detail = lines["A"]
        self.assertAlmostEqual(line.amount, 3160.50, places=2)
        self.assertDetail(detail, "2026-12-31", [["2027-01-31", 1000000], ["2027-02-28", 1010000]],
                          1020000, 1010000, 9090, 5929.50)
        line, detail = lines["B"]
        self.assertAlmostEqual(line.amount, 1561, places=2)
        self.assertDetail(detail, "2027-02-15", [["2027-02-28", 500000]], 505000, 502500, 2211, 650)
        line, detail = lines["C"]
        self.assertAlmostEqual(line.amount, 930, places=2)
        self.assertDetail(detail, "2027-02-28", [], 300000, 300000, 930, 0)
        for code, capital in (("A", 1020000), ("B", 505000), ("C", 300000)):
            self.assertAlmostEqual(self.result(march, code).capital, capital, places=2)
        self.consistent(march)
        self.assertEqual(self.check(march, "average_class_gap").status, "ok")
        # Úplata třídy: doklad za každou třídu s třídou na řádcích (daňový efekt), přemostění v Úplatách třídy.
        for code, amount in (("A", 3160.50), ("B", 1561), ("C", 930)):
            fund_class = self.cls(fund, code)
            event = march.event_ids.filtered(lambda e: e.key.endswith(f":fee:{rule.id}:{fund_class.id}"))
            self.assertEqual(len(event), 1)
            self.assertEqual(event.move_id.line_ids.mapped("investra_class_id"), fund_class)
            self.assertAlmostEqual(self.result(march, code).fee_amount, -amount, places=2)

    def test_step_1_today_point_before_fee(self):
        # Krok 1: dnešní bod je hodnota třídy před úplatou; dřívější bod je uložený kapitál (po úplatě).
        # Leden 1 000 000 → 3 100, kapitál 996 900. Únor +10 000: dnes 1 006 900, průměr 1 001 900, 59 dní
        # → nárok 1 001 900 × 0,0059 = 5 911,21, pohyb 2 811,21.
        fund = self.fund(("A",))
        a = self.cls(fund, "A")
        self.subscribe(a, "2026-12-31", 1000000, 1000)
        rule = self.rule(fund, ("A",), step="1")
        january = self.run_to_posted(self.valuation(fund, JANUARY))
        self.assertAlmostEqual(self.lines(january, rule)["A"][0].amount, 3100, places=2)
        self.specific(fund, a, "a2", "2027-02-20", 10000)
        february = self.valuation(fund, FEBRUARY)
        february.action_compute()
        line, detail = self.lines(february, rule)["A"]
        self.assertDetail(detail, "2026-12-31", [["2027-01-31", 996900]], 1006900, 1001900, 5911.21, 3100)
        self.assertAlmostEqual(line.amount, 2811.21, places=2)

    # --- pojistky a upozornění ----------------------------------------------------------------------------------------

    def test_switch_from_fund_to_classes_in_year_stops(self):
        fund = self.fund(("A",))
        self.subscribe(self.cls(fund, "A"), "2026-12-31", 1000000, 1000)
        rule = self.rule(fund, ())
        self.run_to_posted(self.valuation(fund, JANUARY))
        rule.class_ids = fund.class_ids
        with self.assertRaisesRegex(UserError, "bylo letos počítáno za celý fond"):
            self.valuation(fund, FEBRUARY).action_compute()

    def test_switch_from_classes_to_fund_in_year_stops(self):
        fund = self.fund(("A",))
        self.subscribe(self.cls(fund, "A"), "2026-12-31", 1000000, 1000)
        rule = self.rule(fund, ("A",))
        self.run_to_posted(self.valuation(fund, JANUARY))
        rule.class_ids = False
        with self.assertRaisesRegex(UserError, "bylo letos počítáno po třídách"):
            self.valuation(fund, FEBRUARY).action_compute()

    def test_interrupted_class_warns_and_skips_points(self):
        # A v pravidle v lednu, v únoru ne, v březnu znovu: únorový bod se nepočítá, začátek zůstává 31. 12.,
        # booked jen lednový řádek; kontrola upozorní.
        fund = self.fund(("A", "B"))
        a, b = self.cls(fund, "A"), self.cls(fund, "B")
        self.subscribe(a, "2026-12-31", 1000000, 1000)
        self.subscribe(b, "2026-12-31", 1000000, 1000)
        rule = self.rule(fund, ("A", "B"), step="1")
        january = self.run_to_posted(self.valuation(fund, JANUARY))
        rule.class_ids = [(3, a.id)]
        february = self.run_to_posted(self.valuation(fund, FEBRUARY))
        self.assertEqual(set(self.lines(february, rule)), {"B"})
        rule.class_ids = [(4, a.id)]
        march = self.valuation(fund, MARCH)
        march.action_compute()
        line, detail = self.lines(march, rule)["A"]
        capital = self.result(january, "A").capital
        self.assertEqual(detail["start"], "2026-12-31")
        self.assertEqual([day for day, _value in detail["points"]], ["2027-01-31"])
        self.assertAlmostEqual(float(detail["points"][0][1]), capital, places=2)
        self.assertAlmostEqual(float(detail["booked"]), 3100, places=2)
        today = float(detail["today"])
        entitlement = round((capital + today) / 2 * 0.0365 * 90 / 365, 2)
        self.assertAlmostEqual(float(detail["entitlement"]), entitlement, places=2)
        self.assertAlmostEqual(line.amount, entitlement - 3100, places=2)
        gap = self.check(march, "average_class_gap")
        self.assertEqual(gap.status, "warning")
        self.assertIn("Třída A byla v pravidle Obhospodařování letos přerušeně", gap.detail)

    # --- opravy, příjemci ---------------------------------------------------------------------------------------------

    def correction(self, valuation, rule, code, amount, target="amount"):
        return self.manual_fee(valuation, amount, note="Dohoda s depozitářem", account_id=False,
                               corrects_rule_id=rule.id, class_id=self.cls(valuation.fund_id, code).id,
                               correction_target=target, validity="period")

    def test_base_correction_of_class_carried_to_year_end(self):
        # Oprava základu třídy A +1 000 000 v lednu: lednový průměr A 2 000 000 (6 200); únor ji převezme do průměru A.
        # Třída B opravu nemá.
        fund = self.fund(("A", "B"))
        a, b = self.cls(fund, "A"), self.cls(fund, "B")
        self.subscribe(a, "2026-12-31", 1000000, 1000)
        self.subscribe(b, "2026-12-31", 1000000, 1000)
        rule = self.rule(fund, ("A", "B"), step="1")
        january = self.valuation(fund, JANUARY)
        entry = self.correction(january, rule, "A", 1000000, target="base")
        self.run_to_posted(january)
        lines = self.lines(january, rule)
        self.assertAlmostEqual(float(lines["A"][1]["average"]), 2000000, places=2)
        self.assertAlmostEqual(lines["A"][0].amount, 6200, places=2)
        self.assertAlmostEqual(lines["B"][0].amount, 3100, places=2)
        february = self.valuation(fund, FEBRUARY)
        february.action_compute()
        lines = self.lines(february, rule)
        detail = lines["A"][1]
        self.assertEqual(detail["base_correction_ids"], entry.ids)
        points = [float(v) for _d, v in detail["points"]]
        self.assertAlmostEqual(float(detail["average"]), (sum(points) + float(detail["today"])) / 2 + 1000000, places=2)
        self.assertNotIn("base_correction", lines["B"][1])
        self.consistent(february)

    def test_amount_correction_of_class_is_permanent(self):
        # Oprava částky A −500 v lednu: řádek pravidla 3 100 + oprava −500. Únor odečte jen řádek pravidla (booked 3 100),
        # oprava platí trvale (ZJ-11).
        fund = self.fund(("A",))
        self.subscribe(self.cls(fund, "A"), "2026-12-31", 1000000, 1000)
        rule = self.rule(fund, ("A",), step="1")
        january = self.valuation(fund, JANUARY)
        self.correction(january, rule, "A", -500)
        self.run_to_posted(january)
        self.assertAlmostEqual(self.lines(january, rule)["A"][0].amount, 3100, places=2)
        self.assertAlmostEqual(sum(january.fee_line_ids.mapped("amount")), 2600, places=2)
        self.assertAlmostEqual(self.result(january, "A").capital, 997400, places=2)
        february = self.valuation(fund, FEBRUARY)
        february.action_compute()
        line, detail = self.lines(february, rule)["A"]
        self.assertAlmostEqual(float(detail["booked"]), 3100, places=2)
        self.assertAlmostEqual(float(detail["points"][0][1]), 997400, places=2)
        self.assertAlmostEqual(line.amount, float(detail["entitlement"]) - 3100, places=2)

    def test_recipient_share(self):
        # A platí, polovina jde třídě B (jediný příjemce): přesun 1 550, náklad 1 550; dopočet konzistentní.
        fund = self.fund(("A", "B"))
        a, b = self.cls(fund, "A"), self.cls(fund, "B")
        self.subscribe(a, "2026-12-31", 1000000, 1000)
        self.subscribe(b, "2026-12-31", 1000000, 1000)
        rule = self.rule(fund, ("A",), step="1", recipient_share=0.5, recipient_class_ids=[(6, 0, b.ids)])
        january = self.valuation(fund, JANUARY)
        january.action_compute()
        line, detail = self.lines(january, rule)["A"]
        self.assertAlmostEqual(line.amount, 3100, places=2)
        self.assertAlmostEqual(float(detail["expense"]), 1550, places=2)
        self.assertEqual({k: float(v) for k, v in detail["borne"].items()}, {str(a.id): 3100.0, str(b.id): -1550.0})
        self.assertAlmostEqual(self.result(january, "A").capital, 996900, places=2)
        self.assertAlmostEqual(self.result(january, "B").capital, 1001550, places=2)
        self.consistent(january)

    def test_rule_without_classes_unchanged(self):
        # Bez Platí třídy zůstává úplata celého fondu (B.6): jeden řádek bez třídy, bez `per_class`.
        fund = self.fund(("A", "B"))
        self.subscribe(self.cls(fund, "A"), "2026-12-31", 500000, 500)
        self.subscribe(self.cls(fund, "B"), "2026-12-31", 500000, 500)
        rule = self.rule(fund, ())
        january = self.valuation(fund, JANUARY)
        january.action_compute()
        line = january.fee_line_ids.filtered(lambda l: l.rule_id == rule)
        self.assertEqual(len(line), 1)
        self.assertFalse(line.class_id)
        self.assertNotIn("per_class", json.loads(line.detail))
        self.assertFalse(self.check(january, "average_class_gap"))

    def test_scheme_preview_per_class(self):
        fund = self.fund(("A", "B"))
        self.rule(fund, ("A", "B"))
        fund.invalidate_recordset(["fee_scheme_preview"])
        preview = str(fund.fee_scheme_preview)
        self.assertIn("bez historie ocenění", preview)
        self.assertEqual(preview.count("Obhospodařování</td>"), 2)
        self.assertFalse(self.rule(fund, ("A",), name="Jiné").class_base_warning)
