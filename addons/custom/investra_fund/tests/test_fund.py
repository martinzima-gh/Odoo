from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


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
