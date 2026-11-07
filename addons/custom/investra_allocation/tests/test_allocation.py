from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAllocation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        czk = cls.env.ref("base.CZK")
        czk.active = True
        Entity = cls.env["investra.entity"]
        cls.fund = cls.env["investra.fund"].create({"entity_id": Entity.create_book("A", "fund", "cas501", czk, "cz").id})
        cls.other = cls.env["investra.fund"].create({"entity_id": Entity.create_book("B", "fund", "cas501", czk, "cz").id})
        cls.foreign_class = cls.env["investra.fund.class"].create(
            {"fund_id": cls.other.id, "code": "X", "name": "X", "currency_id": czk.id}
        )
        cls.Scheme = cls.env["investra.allocation.scheme"]

    def test_latest_valid_version_is_used(self):
        old = self.Scheme.create({"fund_id": self.fund.id, "valid_from": "2026-01-01"})
        new = self.Scheme.create({"fund_id": self.fund.id, "valid_from": "2026-07-01", "method": "waterfall"})
        self.assertEqual(self.Scheme._for_date(self.fund, date(2026, 6, 30)), old)
        self.assertEqual(self.Scheme._for_date(self.fund, date(2026, 7, 1)), new)

    def test_no_scheme_before_first_version(self):
        self.Scheme.create({"fund_id": self.fund.id, "valid_from": "2026-01-01"})
        self.assertFalse(self.Scheme._for_date(self.fund, date(2025, 12, 31)))

    def test_class_must_belong_to_fund(self):
        scheme = self.Scheme.create({"fund_id": self.fund.id, "valid_from": "2026-01-01"})
        with self.assertRaises(ValidationError):
            self.env["investra.allocation.line"].create({"scheme_id": scheme.id, "class_id": self.foreign_class.id})
