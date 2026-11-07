import json
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from odoo.tests import TransactionCase

SCENARIOS = Path(__file__).parent / "scenarios"


class NavCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.czk = cls.env.ref("base.CZK")
        cls.eur = cls.env.ref("base.EUR")
        (cls.czk | cls.eur).active = True
        cls.preparer = cls._make_user("nav_preparer", "investra_entity.group_valuation_preparer")
        cls.approver = cls._make_user("nav_approver", "investra_entity.group_valuation_approver")
        cls.approver2 = cls._make_user("nav_approver2", "investra_entity.group_valuation_approver")

    @classmethod
    def _make_user(cls, login, group):
        return cls.env["res.users"].create({
            "name": login, "login": login,
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id, cls.env.ref(group).id])],
        })

    def make_fund(self, currency=None, launch="2026-12-31", classes=()):
        book = self.env["investra.entity"].create_book(
            f"Fond {self.id()[-30:]}", "fund", "cas501", currency or self.czk, "investra_fund"
        )
        company = book.company_id
        for user in (self.preparer, self.approver, self.approver2):
            user.write({"company_ids": [(4, company.id)], "company_id": company.id})
        self.env = self.env(context=dict(self.env.context, allowed_company_ids=[company.id]))
        fund = self.env["investra.fund"].create({"entity_id": book.id, "launch_date": launch})
        for values in classes:
            self.env["investra.fund.class"].create({
                "fund_id": fund.id, "name": values["code"], "currency_id": self.czk.id, **values,
            })
        return fund

    def cls(self, fund, code):
        return fund.class_ids.filtered(lambda c: c.code == code)

    def subscribe(self, fund_class, day, amount, units, kind="subscription"):
        movement = self.env["investra.class.movement"].create({
            "class_id": fund_class.id, "date": day, "movement_type": kind, "amount": amount, "units": units,
        })
        movement._book()
        return movement

    def book(self, fund, key, day, lines):
        event = self.env["investra.accounting.event"]._create_event(fund.company_id, key, key, day, "test", lines)
        event._lock_events()
        event._post_events()
        return event

    def common_result(self, fund, key, day, amount):
        self.book(fund, key, day, [
            {"role": "bank", "amount": str(amount)},
            {"role": "income_other", "amount": str(-Decimal(str(amount)))},
        ])

    def specific(self, fund, fund_class, key, day, amount):
        self.book(fund, key, day, [
            {"role": "expense_other", "amount": str(-Decimal(str(amount))), "class_id": fund_class.id},
            {"role": "fee_payable", "amount": str(amount), "class_id": fund_class.id},
        ])

    def valuation(self, fund, day, version=1):
        return self.env["investra.valuation"].with_user(self.preparer).create(
            {"fund_id": fund.id, "date": day, "version": version}
        )

    def run_to_posted(self, valuation):
        valuation.action_compute()
        valuation.action_submit()
        valuation.with_user(self.approver).action_approve()
        valuation.action_post()
        return valuation

    def run_to_published(self, valuation):
        self.run_to_posted(valuation)
        valuation.action_send_depositary()
        valuation.with_user(self.approver).action_depositary_confirm()
        valuation.with_user(self.approver).action_publish()
        return valuation

    def result(self, valuation, code):
        return valuation.class_line_ids.filtered(lambda l: l.class_id.code == code)

    def rate(self, day, value, currency="EUR"):
        self.env["investra.rate"]._store("cnb", date.fromisoformat(day), {currency: (Decimal(1), Decimal(str(value)))}, f"{day}{value}")


def load_scenarios():
    return sorted(SCENARIOS.glob("*.json"))


def previous_day(day):
    return (date.fromisoformat(day) - timedelta(days=1)).isoformat()
