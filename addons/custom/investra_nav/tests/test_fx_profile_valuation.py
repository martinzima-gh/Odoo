from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestFxProfileValuation(NavCase):
    """Ocenění přeceňuje účty profilu přecenění knihy fondu (rozhodnutí 2026-11-13, varianta A)."""

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2027-01-01", 100000, 100)
        self.day = date(2027, 1, 31)
        self.rate("2027-01-10", 25)
        self.rate("2027-01-31", 26)
        self.Role = self.env["investra.account.role"]
        self.profile = self.env["investra.fx.profile"].sudo().search([("fund_id", "=", self.fund.id)])

    def fx_lines(self, valuation):
        lines = valuation.sudo().event_ids.move_id.line_ids
        return lines.filtered(lambda l: l.investra_movement_type == "fx_revaluation")

    def test_new_fund_gets_profile_with_bank_and_fee_payable(self):
        company = self.fund.company_id
        self.assertEqual(len(self.profile), 1)
        self.assertEqual(self.profile.company_id, company)
        expected = self.Role.accounts_for(company, "bank") | self.Role.accounts_for(company, "fee_payable")
        self.assertEqual(self.profile.account_ids, expected)
        self.assertEqual(self.profile.gain_account_id, self.Role.account_for(company, "gain_fx"))
        self.assertEqual(self.profile.loss_account_id, self.Role.account_for(company, "loss_fx"))
        self.fund._ensure_fx_profile()
        self.assertEqual(self.env["investra.fx.profile"].sudo().search_count([("fund_id", "=", self.fund.id)]), 1)

    def test_fee_payable_in_foreign_currency_is_revalued(self):
        # Závazek 1 000 EUR po 25 = 25 000 Kč; k datu ocenění po 26 = 26 000 Kč, kurzová ztráta 1 000 Kč
        self.book(self.fund, "faktura", "2027-01-10", [
            {"role": "expense_other", "amount": "25000"},
            {"role": "fee_payable", "amount": "-25000", "currency_id": self.eur.id, "amount_currency": "-1000"},
        ])
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        payable = self.Role.account_for(self.fund.company_id, "fee_payable")
        lines = self.fx_lines(valuation)
        self.assertEqual(lines.filtered(lambda l: l.account_id == payable).balance, -1000)
        self.assertEqual(lines.filtered(lambda l: l.account_id == self.Role.account_for(self.fund.company_id, "loss_fx")).balance, 1000)
        self.assertAlmostEqual(valuation.fund_capital, 100000 - 25000 - 1000, places=2)

    def test_bank_line_unchanged_main_account_without_partner(self):
        partner = self.env["res.partner"].create({"name": "Banka test"})
        self.book(self.fund, "banka", "2027-01-10", [
            {"role": "bank", "amount": "25000", "currency_id": self.eur.id, "amount_currency": "1000", "partner_id": partner.id},
            {"role": "income_other", "amount": "-25000"},
        ])
        valuation = self.valuation(self.fund, self.day)
        valuation.action_compute()
        bank = self.Role.account_for(self.fund.company_id, "bank")
        line = self.fx_lines(valuation).filtered(lambda l: l.account_id == bank)
        self.assertEqual(len(line), 1)
        self.assertEqual(line.balance, 1000)
        self.assertFalse(line.partner_id)

    def test_profile_account_without_role_stops_valuation(self):
        company = self.fund.company_id
        account = self.env["account.account"].sudo().create({
            "name": "Bez role", "code": "378900", "account_type": "asset_current", "company_ids": [(6, 0, company.ids)],
        })
        self.profile.account_ids = [(4, account.id)]
        self.book(self.fund, "pohledavka", "2027-01-10", [
            {"role": "income_other", "amount": "-25000"},
            {"role": "bank", "amount": "25000", "extra": {"account_id": account.id},
             "currency_id": self.eur.id, "amount_currency": "1000"},
        ])
        with self.assertRaises(UserError):
            self.valuation(self.fund, self.day).action_compute()
