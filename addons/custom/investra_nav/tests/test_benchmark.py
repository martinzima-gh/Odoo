import logging
import time
from datetime import date

from odoo.tests import tagged

from .common import NavCase
from odoo.addons.investra_instruments.tests.common import with_ids

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install", "-standard", "nav_benchmark")
class TestBenchmark(NavCase):
    """Měření dotazů a času ocenění. Spouští se jen výslovně tagem nav_benchmark."""

    def prepare(self, instruments, classes):
        fund = self.make_fund(classes=[{"code": f"T{i}"} for i in range(classes)])
        for fund_class in fund.class_ids:
            self.subscribe(fund_class, "2036-01-01", 10000000, 100000)
        Rule = self.env["investra.fee.rule"]
        for sequence, role in enumerate(("expense_management", "expense_administration", "expense_depositary")):
            Rule.create({
                "fund_id": fund.id, "name": role, "sequence": sequence, "kind": "periodic", "expense_role": role,
                "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.01})],
            })
        for fund_class in fund.class_ids:
            Rule.create({
                "fund_id": fund.id, "name": f"Odměna {fund_class.code}", "sequence": 50, "kind": "performance",
                "expense_role": "expense_performance", "class_ids": [(6, 0, fund_class.ids)], "crystallisation": "year",
                "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.2, "perf_measure": "unit", "initial_reference": 1})],
            })
        kind = self.env.ref("investra_instruments.type_equity")
        day = date(2036, 1, 31)
        for index in range(instruments):
            item = self.env["investra.instrument"].create(with_ids(self.env, {"name": f"N{fund.id}-{index}", "currency_id": self.czk.id, "type_id": kind.id}, fund))
            self.classify(fund, item)
            self.env["investra.trade"].create({
                "fund_id": fund.id, "instrument_id": item.id, "trade_date": "2036-01-05", "quantity": 1, "price": 100,
            })._book()
            price = self.env["investra.instrument.price"].with_user(self.preparer).create({
                "fund_id": fund.id, "instrument_id": item.id, "date": day, "price": 101, "source": "Test",
            })
            price.with_user(self.approver).action_approve()
        return self.valuation(fund, day)

    def measure(self, instruments, classes):
        valuation = self.prepare(instruments, classes).with_user(self.preparer)
        self.env.flush_all()
        before, started = self.env.cr.sql_log_count, time.perf_counter()
        valuation.action_compute()
        self.env.flush_all()
        _logger.warning(
            "BENCH nastroje=%s tridy=%s dotazy=%s cas=%.2f", instruments, classes,
            self.env.cr.sql_log_count - before, time.perf_counter() - started,
        )

    def test_scaling(self):
        for instruments, classes in ((5, 2), (50, 2), (200, 2), (5, 10), (5, 30)):
            self.measure(instruments, classes)
