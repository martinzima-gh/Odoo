from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, TransactionCase, tagged
from odoo.tools import mute_logger

from odoo.addons.investra_fund.models.fund import isin_is_valid


@tagged("post_install", "-at_install")
class TestFund(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.czk = cls.env.ref("base.CZK")
        cls.czk.active = True
        Entity = cls.env["investra.entity"]
        cls.book_a = Entity.create_book("Fond A", "fund", "cas501", cls.czk, "cz")
        cls.book_b = Entity.create_book("Fond B", "fund", "cas501", cls.czk, "cz")
        cls.fund_a = cls.env["investra.fund"].create({"entity_id": cls.book_a.id})
        cls.fund_b = cls.env["investra.fund"].create({"entity_id": cls.book_b.id})
        cls.user_b = cls.env["res.users"].create({
            "name": "Čtenář B",
            "login": "fund_reader_b",
            "company_id": cls.book_b.company_id.id,
            "company_ids": [(6, 0, [cls.book_b.company_id.id])],
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id, cls.env.ref("account.group_account_readonly").id])],
        })

    def _class(self, fund, code="A", **values):
        return self.env["investra.fund.class"].create(
            {"fund_id": fund.id, "code": code, "name": code, "currency_id": self.czk.id, **values}
        )

    def test_service_book_cannot_be_fund(self):
        book = self.env["investra.entity"].create_book("Služby", "service", "cas500", self.czk, "cz")
        with self.assertRaises(ValidationError):
            self.env["investra.fund"].create({"entity_id": book.id})

    def test_class_defaults_follow_statute_default(self):
        record = self._class(self.fund_a)
        self.assertEqual((record.price_digits, record.price_rounding), (4, "down"))

    def test_class_takes_rounding_from_fund(self):
        self.fund_b.write({"price_digits": 6, "price_rounding": "half_up"})
        record = self._class(self.fund_b, "F")
        self.assertEqual((record.price_digits, record.price_rounding), (6, "half_up"))

    def test_class_can_override_fund(self):
        self.fund_b.write({"price_digits": 6, "price_rounding": "half_up"})
        record = self._class(self.fund_b, "G", price_digits=2, price_rounding="up")
        self.assertEqual((record.price_digits, record.price_rounding), (2, "up"))

    def test_zero_digits_is_kept_not_replaced_by_fund(self):
        self.assertEqual(self._class(self.fund_a, "H", price_digits=0).price_digits, 0)

    def test_digits_out_of_range_rejected(self):
        with self.assertRaises(ValidationError):
            self._class(self.fund_a, "I", price_digits=19)

    def test_duplicate_class_code_rejected(self):
        self._class(self.fund_a)
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError), self.cr.savepoint():
            self._class(self.fund_a)

    def test_same_code_in_other_fund_allowed(self):
        self._class(self.fund_a)
        self.assertTrue(self._class(self.fund_b))

    def test_user_sees_only_own_book(self):
        visible = self.env["investra.fund"].with_user(self.user_b).search([])
        self.assertEqual(visible, self.fund_b)
        with self.assertRaises(AccessError):
            self.fund_a.with_user(self.user_b).read(["name"])

    def test_reader_cannot_create_class(self):
        with self.assertRaises(AccessError):
            self.env["investra.fund.class"].with_user(self.user_b).create({
                "fund_id": self.fund_b.id, "code": "X", "name": "X", "currency_id": self.czk.id,
            })

    def test_class_row_in_fund_form_gets_price_params(self):
        """MN-03: nový řádek třídy ve formuláři fondu dostane kurz a zaokrouhlení z fondu (ne 0)."""
        self.fund_b.write({"price_digits": 5, "price_rounding": "half_up"})
        form = Form(self.fund_b)
        with form.class_ids.new() as line:
            line.code = "N"
            line.name = "Nová"
            line.currency_id = self.czk
        form.save()
        record = self.fund_b.class_ids.filtered(lambda c: c.code == "N")
        self.assertEqual((record.price_digits, record.price_rounding), (5, "half_up"))

    def test_isin_check(self):
        """MN-07: ISIN podle ISO 6166 (země, 9 znaků, kontrolní číslice Luhn)."""
        for valid in ("US0378331005", "CZ0003551251", "DE000BAY0017"):
            self.assertTrue(isin_is_valid(valid), valid)
        for invalid in ("US0378331006", "US037833100", "us0378331005", "1S0378331005", "US037833100A", "US 378331005", "", None):
            self.assertFalse(isin_is_valid(invalid), invalid)

    def test_class_isin_is_validated(self):
        record = self._class(self.fund_a, "I1", isin="US0378331005")
        self.assertEqual(record.isin, "US0378331005")
        self.assertTrue(self._class(self.fund_a, "I2").isin is False)  # ISIN je nepovinný
        with self.assertRaisesRegex(ValidationError, "Neplatný ISIN"):
            record.isin = "US0378331006"
        with self.assertRaisesRegex(ValidationError, "Neplatný ISIN"):
            self._class(self.fund_a, "I3", isin="XX123")



@tagged("post_install", "-at_install")
class TestFundBookDomain(TransactionCase):
    def test_book_field_offers_only_fund_books(self):
        """Pole Účetní kniha ve formuláři fondu nabízí jen druh fond, podfond a SICAV (MN-05, nález MN-02 5)."""
        from lxml import etree
        arch = etree.fromstring(self.env["investra.fund"].get_view(view_type="form")["arch"])
        domain = arch.xpath("//field[@name='entity_id']")[0].get("domain")
        for entity_type in ("fund", "subfund", "sicav"):
            self.assertIn(entity_type, domain)
        self.assertNotIn("manager", domain)
        self.assertNotIn("service", domain)
