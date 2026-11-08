from odoo.tests import TransactionCase, tagged

from odoo.addons.investra_vat_identified.models.company import SPECS


@tagged("post_install", "-at_install")
class TestIdentifiedVat(TransactionCase):
    """Potřebuje databázi s českou osnovou (Investra Services); v databázi fondů se přeskočí."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].search([("chart_template", "=", "cz")], limit=1)
        if not cls.company:
            cls.skipTest(cls, "Není společnost s českou osnovou.")
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=[cls.company.id]))
        cls.company = cls.company.with_env(cls.env)
        cls.taxes = cls.company._setup_identified_vat_taxes()

    def account(self, code):
        return self.env["account.account"].with_company(self.company).search([("code", "=", code)], limit=1)

    def tax(self, rate, origin="eu"):
        label = "z EU" if origin == "eu" else "ze třetí země"
        return self.taxes.filtered(lambda t: t.amount == rate and t.name.endswith(label))

    def invoice(self, move_type, rate, price=1000.0, expense="518100", origin="eu"):
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "purchase")], limit=1
        )
        partner = self.env["res.partner"].create({"name": "Dodavatel EU TEST", "country_id": self.env.ref("base.de").id})
        move = self.env["account.move"].create({
            "move_type": move_type, "partner_id": partner.id, "journal_id": journal.id, "invoice_date": "2026-11-10",
            "invoice_line_ids": [(0, 0, {
                "name": "Služba", "account_id": self.account(expense).id, "quantity": 1, "price_unit": price,
                "tax_ids": [(6, 0, self.tax(rate, origin).ids)],
            })],
        })
        return move

    def balances(self, move):
        """Součty podle účtu; daň zvyšující náklad je na účtu nákladu jako zvláštní řádek."""
        totals = {}
        for line in move.line_ids:
            totals[line.account_id.code] = round(totals.get(line.account_id.code, 0.0) + line.balance, 2)
        return set(totals.items())

    def test_two_taxes_created_once(self):
        self.assertEqual(len(self.taxes), len(SPECS))
        self.assertEqual(self.company._setup_identified_vat_taxes(), self.taxes)
        self.assertTrue(all(t.active for t in self.taxes))

    def test_invoice_21_adds_vat_to_cost_and_payable(self):
        move = self.invoice("in_invoice", 21)
        self.assertEqual(self.balances(move), {("518100", 1210.0), ("343221", -210.0), ("321000", -1000.0)})
        self.assertEqual(round(move.amount_total, 2), 1000.0)

    def test_invoice_12(self):
        move = self.invoice("in_invoice", 12)
        self.assertEqual(self.balances(move), {("518100", 1120.0), ("343212", -120.0), ("321000", -1000.0)})

    def test_refund_reverses(self):
        move = self.invoice("in_refund", 21)
        self.assertEqual(self.balances(move), {("518100", -1210.0), ("343221", 210.0), ("321000", 1000.0)})

    def test_no_input_vat_leg(self):
        move = self.invoice("in_invoice", 21)
        self.assertNotIn("343121", {line.account_id.code for line in move.line_ids})

    def test_move_posts_balanced(self):
        move = self.invoice("in_invoice", 21)
        move.action_post()
        self.assertEqual(move.state, "posted")
        self.assertEqual(round(sum(move.line_ids.mapped("balance")), 2), 0.0)

    def test_non_eu_service_posts_like_eu(self):
        for rate, vat_account, vat in ((21, "343221", 210.0), (12, "343212", 120.0)):
            move = self.invoice("in_invoice", rate, origin="non_eu")
            self.assertEqual(self.balances(move), {("518100", 1000.0 + vat), (vat_account, -vat), ("321000", -1000.0)})

    def test_origins_use_different_base_tags(self):
        for rate in (21, 12):
            eu = self.tax(rate, "eu").invoice_repartition_line_ids.filtered(lambda r: r.repartition_type == "base").tag_ids
            non_eu = self.tax(rate, "non_eu").invoice_repartition_line_ids.filtered(lambda r: r.repartition_type == "base").tag_ids
            self.assertTrue(eu and non_eu)
            self.assertFalse(eu & non_eu)
