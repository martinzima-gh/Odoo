from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from odoo.addons.investra_nav.tests.common import NavCase


@tagged("post_install", "-at_install")
class TestDashboardTracking(NavCase):
    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.today = fields.Date.context_today(self.fund)
        self.deadline = self.env["investra.regulatory.deadline"].create({
            "fund_id": self.fund.id,
            "report": "TEST_REP",
            "period_end": self.today,
            "due_date": self.today + timedelta(days=10),
            "state": "open",
        })

    def flush_tracking(self):
        """Vyvolá zápis tracking zpráv v předcommitové fázi bez volání commit()."""
        self.env.flush_all()
        if hasattr(self.env.cr, "precommit"):
            self.env.cr.precommit.run()

    def test_regulatory_deadline_tracking(self):
        """Změna sledovaného pole termínu ČNB vytvoří tracking zprávu."""
        self.flush_tracking()
        msg_count_before = len(self.deadline.message_ids)

        self.deadline.write({
            "report": "NOVY_REP",
            "state": "submitted",
        })
        self.flush_tracking()

        self.assertGreater(len(self.deadline.message_ids), msg_count_before)
        new_msgs = self.deadline.message_ids[:len(self.deadline.message_ids) - msg_count_before]
        bodies = [m.body or "" for m in new_msgs]
        self.assertTrue(any("(Výkaz)" in b and "NOVY_REP" in b for b in bodies))
        self.assertTrue(any("(Stav)" in b and "Podáno" in b for b in bodies))

    def test_tracking_disable_context(self):
        """Kontext tracking_disable=True potlačí zápis do chatteru."""
        self.flush_tracking()
        msg_count = len(self.deadline.message_ids)

        self.deadline.with_context(tracking_disable=True).write({"report": "TICHO_REP"})
        self.flush_tracking()

        self.assertEqual(len(self.deadline.message_ids), msg_count)
