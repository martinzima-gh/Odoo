from datetime import date
from decimal import Decimal

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.investra_rates.models.rate import parse_cnb

CNB = """06.11.2026 #216
země|měna|množství|kód|kurz
EMU|euro|1|EUR|24,345
Japonsko|jen|100|JPY|15,123
"""


@tagged("post_install", "-at_install")
class TestRateValidity(TransactionCase):
    """Platnost kurzů podle lístku a měny (rozhodnutí 2026-11-11 „Platnost kurzů a smíšené kurzy“)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Rate = cls.env["investra.rate"]
        cls.Validity = cls.env["investra.rate.validity"]
        cls.eur, cls.jpy = cls.env.ref("base.EUR"), cls.env.ref("base.JPY")
        (cls.eur | cls.jpy).active = True
        cls.Rate._store("cnb", *parse_cnb(CNB), CNB)
        cls.cnb_daily = cls.env.ref("investra_rates.validity_cnb_daily")
        cls.approver = cls._user("validity_approver", "investra_entity.group_valuation_approver")
        cls.accountant = cls._user("validity_accountant", "account.group_account_manager")

    @classmethod
    def _user(cls, login, group):
        return cls.env["res.users"].create({
            "name": login, "login": login,
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id, cls.env.ref(group).id])],
        })

    def exception(self, currency, days, user=None):
        return self.Validity.with_user(user or self.approver).create({
            "source": "cnb", "periodicity": "daily", "currency_id": currency.id, "max_age_days": days,
        })

    def test_default_rows(self):
        rows = {(r.source, r.periodicity, r.currency_id.id): r.max_age_days for r in self.Validity.search([])}
        self.assertEqual(rows[("cnb", "daily", False)], 5)
        self.assertEqual(rows[("cnb", "monthly", False)], 35)
        self.assertEqual(rows[("ecb", "daily", False)], 5)

    def test_default_of_sheet_applies(self):
        self.assertEqual(self.Rate.get_rate("cnb", self.eur, date(2026, 11, 11)), Decimal("24.345"))
        with self.assertRaises(UserError):
            self.Rate.get_rate("cnb", self.eur, date(2026, 11, 12))

    def test_change_of_default_applies(self):
        self.cnb_daily.with_user(self.approver).max_age_days = 10
        self.assertEqual(self.Rate.get_rate("cnb", self.eur, date(2026, 11, 16)), Decimal("24.345"))

    def test_currency_exception_overrides_default(self):
        self.exception(self.jpy, 20)
        self.assertEqual(self.Rate.get_rate("cnb", self.jpy, date(2026, 11, 20)), Decimal("0.15123"))
        with self.assertRaises(UserError):
            self.Rate.get_rate("cnb", self.eur, date(2026, 11, 20))

    def test_exception_can_be_stricter(self):
        self.exception(self.jpy, 0)
        self.assertEqual(self.Rate.get_rate("cnb", self.jpy, date(2026, 11, 6)), Decimal("0.15123"))
        with self.assertRaises(UserError):
            self.Rate.get_rate("cnb", self.jpy, date(2026, 11, 7))

    def test_archived_exception_falls_back_to_default(self):
        row = self.exception(self.jpy, 20)
        row.with_user(self.approver).active = False
        with self.assertRaises(UserError):
            self.Rate.get_rate("cnb", self.jpy, date(2026, 11, 20))

    def test_missing_setting_is_error(self):
        self.cnb_daily.active = False
        with self.assertRaisesRegex(UserError, "Chybí nastavení platnosti kurzu"):
            self.Rate.get_rate("cnb", self.eur, date(2026, 11, 6))

    def test_duplicate_is_refused(self):
        self.exception(self.jpy, 20)
        with self.assertRaises(ValidationError):
            self.exception(self.jpy, 30)
        with self.assertRaises(ValidationError):
            self.Validity.create({"source": "cnb", "periodicity": "daily", "max_age_days": 7})

    def test_ecb_has_only_daily_sheet_and_age_not_negative(self):
        with self.assertRaises(ValidationError):
            self.Validity.create({"source": "ecb", "periodicity": "monthly", "max_age_days": 35})
        with self.assertRaises(ValidationError):
            self.exception(self.jpy, -1)

    def test_only_approver_changes_and_nobody_deletes(self):
        with self.assertRaises(AccessError):
            self.exception(self.jpy, 20, user=self.accountant)
        with self.assertRaises(AccessError):
            self.cnb_daily.with_user(self.accountant).max_age_days = 10
        with self.assertRaises(UserError):
            self.cnb_daily.with_user(self.approver).unlink()
        self.assertEqual(self.cnb_daily.max_age_days, 5)
