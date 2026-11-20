from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestFundFiscalYearEnd(NavCase):
    """ZJ-20 B: konec účetního období se mění ve formuláři fondu do prvního zaúčtovaného ocenění; zapisuje se do knihy fondu."""

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2027-01-01", 1000, 10)
        # Správce fondu smí do knihy fondu (pravidlo podle společnosti), ale společnost sám měnit nesmí.
        self.admin_user.company_ids = [(4, self.fund.company_id.id)]
        self.admin_user.group_ids = [(4, self.env.ref("account.group_account_manager").id)]

    def test_form_changes_book_before_first_valuation(self):
        company = self.fund.company_id
        self.assertEqual((company.fiscalyear_last_day, company.fiscalyear_last_month), (31, "12"))
        form = Form(self.fund.with_user(self.admin_user))
        self.assertFalse(form.fiscal_year_locked)
        form.fiscal_year_last_day = 30
        form.fiscal_year_last_month = "6"
        form.save()
        company.invalidate_recordset()
        self.assertEqual((company.fiscalyear_last_day, company.fiscalyear_last_month), (30, "6"))
        self.assertEqual(self.fund._fiscal_year_dates("2027-03-15")[1].isoformat(), "2027-06-30")
        self.assertIn("31. 12. → 30. 6.", " ".join(self.fund.message_ids.mapped(lambda m: m.body or "")).replace("\xa0", " "))

    def test_invalid_day_is_rejected_by_book(self):
        with self.assertRaises(ValidationError):
            self.fund.with_user(self.admin_user).write({"fiscal_year_last_day": 31, "fiscal_year_last_month": "6"})

    def test_locked_after_posted_valuation(self):
        self.run_to_posted(self.valuation(self.fund, "2027-01-31"))
        self.fund.invalidate_recordset(["fiscal_year_locked"])
        self.assertTrue(self.fund.fiscal_year_locked)
        with self.assertRaisesRegex(UserError, "nejde změnit"):
            self.fund.with_user(self.admin_user).write({"fiscal_year_last_month": "6", "fiscal_year_last_day": 30})
        # Zápis stejné hodnoty (uložení formuláře beze změny) zámek nezastaví.
        self.fund.with_user(self.admin_user).write({"fiscal_year_last_day": 31, "fiscal_year_last_month": "12"})
        self.assertEqual(self.fund.company_id.fiscalyear_last_month, "12")

    def test_draft_valuation_does_not_lock(self):
        self.valuation(self.fund, "2027-01-31")
        self.fund.invalidate_recordset(["fiscal_year_locked"])
        self.assertFalse(self.fund.fiscal_year_locked)
        self.fund.with_user(self.admin_user).write({"fiscal_year_last_month": "6", "fiscal_year_last_day": 30})
        self.assertEqual(self.fund.company_id.fiscalyear_last_month, "6")
