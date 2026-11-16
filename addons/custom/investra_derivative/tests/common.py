from decimal import Decimal

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
        # Fond vznikl před příkladem (2025), aby ocenění v roce 2025 mělo kapitál z úpisu.
        self.fund = self.make_fund(launch="2024-12-31", classes=[{"code": "A"}])

    @staticmethod
    def leg(day, buy_currency, buy_amount, sell_currency, sell_amount):
        return (0, 0, {
            "settlement_date": day, "buy_currency_id": buy_currency.id, "buy_amount": buy_amount,
            "sell_currency_id": sell_currency.id, "sell_amount": sell_amount,
        })

    def derivative(self, kind, legs, fund=None, ref="FX-1", day="2026-09-30", user=None):
        if isinstance(day, int):
            day = f"{day}-09-30"
        Derivative = self.env["investra.derivative"].with_user(user or self.preparer)
        return Derivative.create({
            "fund_id": (fund or self.fund).id, "partner_id": self.bank.id, "kind": kind, "trade_date": day,
            "contract_ref": ref, "leg_ids": legs,
        })

    def forward(self, year=2026, kind="forward", **kwargs):
        """Forward z příkladu návrhu: prodej 1 000 000 EUR za 24 900 000 Kč k 31. 12.; sjednáno 30. 9. (92 dnů).

        Testy účtování používají rok 2025: nohu jde vypořádat nejdřív v den vypořádání a ten nesmí být v budoucnu.
        """
        return self.derivative(kind, [self.leg(f"{year}-12-31", self.czk, 24_900_000, self.eur, 1_000_000)],
                               day=year, **kwargs)

    def swap(self, year=2026, **kwargs):
        """Swap z příkladu návrhu: blízká noha koupě EUR 2. 10., vzdálená prodej EUR 31. 12."""
        return self.derivative("swap", [
            self.leg(f"{year}-10-02", self.eur, 1_000_000, self.czk, 25_000_000),
            self.leg(f"{year}-12-31", self.czk, 24_900_000, self.eur, 1_000_000),
        ], day=year, **kwargs)

    # --- účtování (DE-03) -------------------------------------------------------------------------------------------

    def example_rates(self):
        """Kurzy příkladu návrhu (CZK za EUR), rok 2025."""
        for day, value in (("2025-09-30", 25.00), ("2025-10-02", 25.00), ("2025-10-31", 24.80), ("2025-11-30", 25.10),
                           ("2025-12-31", 25.20)):
            self.rate(day, value)

    def role_balance(self, role, fund=None, day="2100-01-01"):
        company = (fund or self.fund).company_id
        accounts = self.env["investra.account.role"].accounts_for(company, role)
        lines = self.env["account.move.line"].sudo().search([
            ("company_id", "=", company.id), ("account_id", "in", accounts.ids), ("parent_state", "=", "posted"),
            ("date", "<=", day)])
        return Decimal(str(round(sum(lines.mapped("balance")), 2)))

    def net_assets(self, fund=None):
        """FK z rozvahy: aktiva + závazky (závazky záporně), stejně jako ocenění; podrozvaha do něj nevstupuje."""
        company = (fund or self.fund).company_id
        lines = self.env["account.move.line"].sudo().search([
            ("company_id", "=", company.id), ("parent_state", "=", "posted"),
            "|", ("account_id.account_type", "=like", "asset%"), ("account_id.account_type", "=like", "liability%")])
        return Decimal(str(round(sum(lines.mapped("balance")), 2)))

    @staticmethod
    def move_rows(move):
        return sorted((line.account_id.code, round(line.debit, 2), round(line.credit, 2)) for line in move.line_ids)
