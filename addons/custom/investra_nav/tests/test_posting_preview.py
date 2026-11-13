from odoo.tests import Form, tagged

from .common import NavCase


class PreviewMixin:
    """Porovnání náhledu se skutečným dokladem (rozhodnutí 2026-11-13 „Náhled zaúčtování u splátek, úpisů a odkupů“)."""

    @staticmethod
    def rows(documents, currency=False):
        """Řádky dokladů bez nadpisu: (účet s popisem, MD, D[, částka v měně]) seřazené."""
        result = []
        for _caption, day, rows in documents:
            result.append((day, sorted(
                (account, round(float(debit), 2), round(float(credit), 2))
                + ((round(float(ccy or 0), 2),) if currency else ())
                for account, debit, credit, ccy in rows
            )))
        return result


@tagged("post_install", "-at_install")
class TestRepaymentPreview(PreviewMixin, NavCase):
    """Náhled zaúčtování splátky: stejné řádky jako Zaúčtovat (`_book_lines`), po zaúčtování skutečný doklad a storno.

    Vklad 1000 ks × 1 nakoupený 1. 1. 2029, splátka 1. 6. 2029. Roky 2029 se nepřekrývají s jinými testy splátek.
    """

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2029-01-01", 50000, 500)

    def deposit(self, currency=None, fx_rate=1):
        deposit = self.env["investra.instrument"].create({
            "name": f"deposit {self.fund.id}", "currency_id": (currency or self.czk).id,
            "type_id": self.env.ref("investra_instruments.type_deposit").id,
        })
        deposit.cashflow_ids = [(0, 0, {"date": "2029-06-01", "amount": 1, "flow_type": "principal"})]
        self.classify(self.fund, deposit)
        self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": deposit.id,
            "trade_date": "2029-01-01", "quantity": 1000, "price": 1, "fx_rate": fx_rate,
        })._book()
        return deposit

    def repayment(self, deposit, principal, **vals):
        return self.env["investra.instrument.repayment"].create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": deposit.id,
            "date": "2029-06-01", "principal_amount": principal, **vals,
        })

    def roles(self, move):
        mapping = self.env["investra.role.account"].sudo().search([("company_id", "=", move.company_id.id)])
        accounts = {m.account_id: m.role_id.code for m in mapping}
        result = {}
        for line in move.line_ids:
            role = accounts[line.account_id]
            result[role] = round(result.get(role, 0) + line.balance, 2)
        return result

    def test_preview_matches_booked_document(self):
        deposit = self.deposit()
        repayment = self.repayment(deposit, 1000, interest_amount=30, fee_amount=5)
        self.assertIn("Jen náhled", repayment.posting_preview)
        preview = repayment._preview_documents()
        self.assertEqual([(caption, day) for caption, day, _rows in preview], [("Při zaúčtování", repayment.date)])
        repayment.with_user(self.preparer).action_book()
        self.assertEqual(self.rows(preview), self.rows(repayment._booked_documents()))
        # Řádky dokladu jsou stejné jako před vyjmutím `_book_lines` z `_book`.
        lines = self.roles(repayment.event_id.move_id)
        self.assertEqual(lines.pop("cash_in_transit_receipt"), 1025)
        self.assertEqual(lines.pop("expense_bank_fee"), 5)
        self.assertEqual(list(lines.values()), [-1030])  # nástroj: jistina 1000 a úrok 30
        self.assertIn("Zaúčtované doklady splátky", repayment.posting_preview)
        self.assertNotIn("Jen náhled", repayment.posting_preview)

    def test_preview_shows_reversal(self):
        deposit = self.deposit()
        repayment = self.repayment(deposit, 1000)
        repayment.with_user(self.preparer).action_book()
        repayment.with_user(self.preparer).action_reverse("Chybná částka")
        repayment.invalidate_recordset(["posting_preview"])
        self.assertIn("stornováno dokladem", repayment.posting_preview)
        self.assertIn(repayment.event_id.sudo().reversal_move_id.name, repayment.posting_preview)

    def test_foreign_currency_column(self):
        deposit = self.deposit(currency=self.eur, fx_rate=25)
        repayment = self.repayment(deposit, 1000, fx_rate=27)
        self.assertIn("V měně EUR", repayment.posting_preview)
        preview = repayment._preview_documents()
        repayment.with_user(self.preparer).action_book()
        self.assertEqual(self.rows(preview, currency=True), self.rows(repayment._booked_documents(), currency=True))
        self.assertIn((27000.0, 0.0, 1000.0), [row[1:] for row in self.rows(preview, currency=True)[0][1]])

    def test_form_preview_and_warning_before_save(self):
        deposit = self.deposit()
        form = Form(self.env["investra.instrument.repayment"].with_user(self.preparer))
        form.fund_id = self.fund
        form.date = "2029-06-01"
        form.instrument_id = deposit
        form.principal_amount = 400
        self.assertIn("Jen náhled", form.posting_preview)
        self.assertRegex(str(form.posting_preview), r"400[,.]00")
        # Kontrola zaúčtování se ukáže v náhledu místo dokladu; záznam se neuloží.
        form.principal_amount = 2000
        self.assertIn("alert-warning", form.posting_preview)
        self.assertIn("vyšší než zbývající jistina", form.posting_preview)
