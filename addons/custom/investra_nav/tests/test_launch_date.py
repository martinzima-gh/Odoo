from datetime import date

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestLaunchDate(NavCase):
    """MN-03: datum vzniku ve formuláři fondu a zámek po prvním (nestornovaném) ocenění."""

    def test_launch_date_in_form(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        form = Form(fund)
        form.launch_date = date(2027, 1, 1)
        form.save()
        self.assertEqual(fund.launch_date, date(2027, 1, 1))

    def test_locked_after_valuation_unlocked_after_reverse(self):
        fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(fund, "A"), "2027-01-01", 1000, 10)
        fund.launch_date = date(2026, 12, 1)  # bez ocenění jde měnit
        valuation = self.valuation(fund, date(2027, 1, 31))
        fund.invalidate_recordset(["launch_locked"])  # nestored compute: cache z předchozího zápisu
        self.assertTrue(fund.launch_locked)
        with self.assertRaisesRegex(UserError, "nejde změnit"):
            fund.launch_date = date(2026, 12, 15)
        valuation.sudo().write({"state": "reversed"})
        fund.invalidate_recordset()
        self.assertFalse(fund.launch_locked)
        fund.launch_date = date(2026, 12, 15)
        self.assertEqual(fund.launch_date, date(2026, 12, 15))
