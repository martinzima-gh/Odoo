from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import NavCase
from odoo.addons.investra_instruments.tests.common import with_ids


@tagged("post_install", "-at_install")
class TestDraftDelete(NavCase):
    """ZJ-20 A: návrh obchodu smaže zpracovatel (role, která smí obchod vytvářet); zaúčtovaný nebo stornovaný obchod ne."""

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2029-01-01", 50000, 500)
        self.equity = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"akcie {self.fund.id}", "currency_id": self.czk.id,
            "type_id": self.env.ref("investra_instruments.type_equity").id,
        }, self.fund))
        self.classify(self.fund, self.equity)

    def trade(self):
        return self.env["investra.trade"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "portfolio_id": self.portfolio(self.fund).id, "instrument_id": self.equity.id,
            "trade_date": "2029-02-01", "quantity": 10, "price": 100,
        })

    def test_preparer_deletes_draft(self):
        trade = self.trade()
        trade.unlink()
        self.assertFalse(trade.exists())

    def test_booked_trade_cannot_be_deleted(self):
        trade = self.trade()
        trade.action_book()
        with self.assertRaisesRegex(UserError, "stornem"):
            trade.unlink()
        self.assertTrue(trade.exists())

    def test_preparer_may_delete_other_drafts(self):
        # Návrh splátky, dividendy a derivátu: právo smazat má stejná role; model smaže jen návrh.
        models = ["investra.instrument.repayment", "investra.dividend", "investra.class.movement"]
        if "investra.derivative" in self.env:
            models.append("investra.derivative")
        for name in models:
            with self.subTest(model=name):
                try:
                    self.env[name].with_user(self.preparer).check_access("unlink")
                except AccessError as error:  # pragma: no cover - ukáže, který model právo nemá
                    self.fail(f"{name}: {error}")
