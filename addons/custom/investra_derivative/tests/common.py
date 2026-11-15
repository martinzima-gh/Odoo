from odoo.addons.investra_nav.tests.common import NavCase


class DerivativeCase(NavCase):
    """Společný základ testů FX derivátů: fond v CZK, protistrana, zakládání smluv."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.usd = cls.env.ref("base.USD")
        cls.usd.active = True
        cls.bank = cls.env["res.partner"].create({"name": "Banka protistrana", "is_company": True})

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])

    @staticmethod
    def leg(day, buy_currency, buy_amount, sell_currency, sell_amount):
        return (0, 0, {
            "settlement_date": day, "buy_currency_id": buy_currency.id, "buy_amount": buy_amount,
            "sell_currency_id": sell_currency.id, "sell_amount": sell_amount,
        })

    def derivative(self, kind, legs, fund=None, ref="FX-1", day="2026-09-30", user=None):
        Derivative = self.env["investra.derivative"].with_user(user or self.preparer)
        return Derivative.create({
            "fund_id": (fund or self.fund).id, "partner_id": self.bank.id, "kind": kind, "trade_date": day,
            "contract_ref": ref, "leg_ids": legs,
        })

    def forward(self, **kwargs):
        """Forward z příkladu návrhu: prodej 1 000 000 EUR za 24 900 000 Kč k 31. 12. 2026."""
        return self.derivative("forward", [self.leg("2026-12-31", self.czk, 24_900_000, self.eur, 1_000_000)], **kwargs)

    def swap(self, **kwargs):
        """Swap z příkladu návrhu: blízká noha koupě EUR 2. 10., vzdálená prodej EUR 31. 12. 2026."""
        return self.derivative("swap", [
            self.leg("2026-10-02", self.eur, 1_000_000, self.czk, 25_000_000),
            self.leg("2026-12-31", self.czk, 24_900_000, self.eur, 1_000_000),
        ], **kwargs)
