from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestCompanyAccess(NavCase):
    """Uživatel bez přístupu do společnosti fondu nespustí nad jeho oceněním žádný krok."""

    def setUp(self):
        super().setUp()
        own = self.make_fund(classes=[{"code": "A"}])
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.own_company = own.company_id
        self.outsider = self.env["res.users"].create({
            "name": "cizi_uzivatel", "login": "cizi_uzivatel", "company_id": self.own_company.id, "company_ids": [(6, 0, self.own_company.ids)],
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id, self.env.ref("investra_entity.group_valuation_preparer").id,
                                  self.env.ref("investra_entity.group_valuation_approver").id])],
        })
        self.foreign = self.valuation(self.fund, "2037-01-31")

    def as_outsider(self, record):
        return record.with_user(self.outsider).with_context(allowed_company_ids=self.own_company.ids)

    def test_outsider_cannot_compute(self):
        with self.assertRaises(AccessError):
            self.as_outsider(self.foreign).action_compute()
        self.assertEqual(self.foreign.state, "draft")

    def test_outsider_cannot_approve(self):
        with self.assertRaises(AccessError):
            self.as_outsider(self.foreign).action_approve()

    def test_outsider_cannot_approve_price(self):
        instrument = self.env["investra.instrument"].create({
            "name": "Akcie", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_equity").id,
        })
        price = self.env["investra.instrument.price"].with_user(self.preparer).create({
            "fund_id": self.fund.id, "instrument_id": instrument.id, "date": "2037-01-31", "price": 1, "source": "Test",
        })
        with self.assertRaises(AccessError):
            self.as_outsider(price).action_approve()
        self.assertEqual(price.state, "draft")
