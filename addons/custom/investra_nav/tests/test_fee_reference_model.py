"""ZJ-12 krok 1: referenční model společného dopočtu (příloha A) v Pythonu; výsledek musí sedět s výstupem A.1."""

from odoo.tests import BaseCase, tagged

from . import ref_fee_model as model


@tagged("post_install", "-at_install")
class TestFeeReferenceModel(BaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.result = model.run_all()

    def test_matches_attachment_a1(self):
        # Výstup posledního běhu referenčního modelu v PowerShellu (docs/ukoly/ZJ-12/README.md, A.1).
        result = self.result
        self.assertEqual(result["failures"][:5], [])
        self.assertEqual(result["corrections"], 1152)
        self.assertEqual(result["combinations"], 720)
        self.assertEqual(result["today_checked"], 40)
        self.assertEqual(result["passed"], 12013)
        self.assertEqual(result["max_steps"], 33)
        self.assertLess(result["max_residual"], 1e-12)

    def test_closed_examples(self):
        expected = {
            "C1 obě úplaty S1: obhospodařování": 9891.1968, "C1 obě úplaty S1: administrace": 989.1197,
            "C2 S0 + S1: obhospodařování": 10000.0, "C2 S0 + S1: administrace": 989.011,
            "C3 odměna po dani: odměna": 19.1919, "C3 odměna po dani: daň": 4.0404,
            "C4 úplata po dani: úplata": 10846.9539, "C4 úplata po dani: daň": 4457.6523,
            "C5 daňový efekt: odměna A": 10000.0, "C5 daňový efekt: daň fondu": 4500.0,
            "C5 daňový efekt: kapitál A": 1038000.0, "C5 daňový efekt: kapitál B": 1047500.0,
            "C6 ztráta: daň": 0.0, "C6 ztráta: daň třídy A": 0.0,
            "C7 přechod přes nulu: úplata A": 10025.0, "C7 přechod přes nulu: daň fondu": 0.0,
            "C7 přechod přes nulu: daň třídy A": -125.0, "C7 přechod přes nulu: daň třídy B": 125.0,
            "C8 oprava úplaty S1: vypočteno bez opravy": 9900.9901, "C8 oprava úplaty S1: výsledek": 9800.9901,
            "C8 oprava úplaty S1: FK": 990199.0099,
        }
        self.assertEqual(set(self.result["closed"]), set(expected))
        for name, value in expected.items():
            self.assertAlmostEqual(self.result["closed"][name][0], value, places=3, msg=name)
