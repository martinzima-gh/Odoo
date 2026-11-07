import json
from decimal import Decimal

from odoo.tests import tagged

from .common import NavCase, load_scenarios


@tagged("post_install", "-at_install")
class TestScenarios(NavCase):
    """Odoo musí z účetních řádků dojít ke stejným číslům jako referenční výpočet mimo Odoo."""

    def run_scenario(self, path):
        data = json.loads(path.read_text(encoding="utf-8"))
        classes = [{
            "code": c["code"],
            "price_digits": c["price_digits"],
            "currency_id": (self.eur if c.get("currency") == "EUR" else self.czk).id,
        } for c in data["classes"]]
        fund = self.make_fund(launch=data["launch"], classes=classes)
        for c in data["classes"]:
            self.subscribe(self.cls(fund, c["code"]), "2027-01-01", c["opening_capital"], c["opening_units"])
        Rule = self.env["investra.fee.rule"]
        first = data["valuations"][0]
        rules = {}
        if any(v.get("mgmt_fee") for v in data["valuations"]):
            fee = first["mgmt_fee"]
            rules["mgmt"] = Rule.create({
                "fund_id": fund.id, "name": "Úplata", "sequence": 10, "kind": "periodic", "basis": "act365",
                "base_mode": fee.get("base", "before"), "expense_role": "expense_management",
                "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": float(fee["rate"])})],
            })
        for code, fee in first.get("perf_fee", {}).items():
            Rule.create({
                "fund_id": fund.id, "name": f"Odměna {code}", "sequence": 20, "kind": "performance",
                "class_ids": [(6, 0, self.cls(fund, code).ids)], "expense_role": "expense_performance",
                "crystallisation": "none",
                "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": float(fee["rate"]), "perf_measure": "unit",
                                        "initial_reference": float(fee["hwm"])})],
            })
        if first.get("tax"):
            Rule.create({
                "fund_id": fund.id, "name": "Daň", "sequence": 30, "kind": "tax",
                "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": float(first["tax"]["rate"])})],
            })
        for index, (val, expected) in enumerate(zip(data["valuations"], data["expected"])):
            day = val["date"]
            for currency, value in val.get("fx", {}).items():
                self.rate(day, value, currency)
            for code, item in val.get("subscriptions", {}).items():
                self.subscribe(self.cls(fund, code), day, item["amount"], item["units"])
            for code, item in val.get("redemptions", {}).items():
                self.subscribe(self.cls(fund, code), day, item["amount"], item["units"], "redemption")
            if val.get("common_result"):
                self.common_result(fund, f"common{index}", day, val["common_result"])
            for code, amount in val.get("specific", {}).items():
                self.specific(fund, self.cls(fund, code), f"spec{index}{code}", day, amount)
            valuation = self.run_to_posted(self.valuation(fund, day))
            self.assertAlmostEqual(valuation.fund_capital, float(expected["fk"]), places=2, msg=f"FK {day}")
            for code, value in expected["fkt"].items():
                line = self.result(valuation, code)
                self.assertAlmostEqual(line.capital, float(value), places=2, msg=f"{path.name} {code} {day}")
                self.assertEqual(Decimal(line.price), Decimal(expected["price"][code]), f"{path.name} kurz {code} {day}")
                self.assertAlmostEqual(line.units, float(expected["units"][code]), places=6)
            self.assertFalse(valuation.check_ids.filtered(lambda c: c.status == "stop"))

    def test_all_scenarios_have_expected_results(self):
        paths = load_scenarios()
        self.assertEqual(len(paths), 5)
        for path in paths:
            self.assertTrue(json.loads(path.read_text(encoding="utf-8")).get("expected"), path.name)

    def test_s1(self):
        self.run_scenario(load_scenarios()[0])

    def test_s2(self):
        self.run_scenario(load_scenarios()[1])

    def test_s3(self):
        self.run_scenario(load_scenarios()[2])

    def test_s4(self):
        self.run_scenario(load_scenarios()[3])

    def test_s5(self):
        self.run_scenario(load_scenarios()[4])
