from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCnbTracking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.role = cls.env["investra.account.role"].create({
            "code": "test_cnb_map_role",
            "name": "Role pro ČNB mapu",
            "category": "asset",
        })
        cls.cnb_map = cls.env["investra.cnb.map"].create({
            "sheet": "ROFO10_11",
            "row": 999,
            "column": 1,
            "source": "role",
            "role_id": cls.role.id,
        })

    def flush_tracking(self):
        """Vyvolá zápis tracking zpráv v předcommitové fázi bez volání commit()."""
        self.env.flush_all()
        if hasattr(self.env.cr, "precommit"):
            self.env.cr.precommit.run()

    def test_cnb_map_tracking(self):
        """Změna sledovaného pole převodní tabulky ČNB vytvoří tracking zprávu."""
        self.flush_tracking()
        msg_count_before = len(self.cnb_map.message_ids)

        self.cnb_map.write({
            "sheet": "ROFO10_21",
            "source": "result",
        })
        self.flush_tracking()

        self.assertGreater(len(self.cnb_map.message_ids), msg_count_before)
        new_msgs = self.cnb_map.message_ids[:len(self.cnb_map.message_ids) - msg_count_before]
        bodies = [m.body or "" for m in new_msgs]
        self.assertTrue(any("(List)" in b and "ROFO10_21" in b for b in bodies))
        self.assertTrue(any("(Zdroj)" in b and "Výsledek běžného období" in b for b in bodies))

    def test_tracking_disable_context(self):
        """Kontext tracking_disable=True potlačí zápis do chatteru."""
        self.flush_tracking()
        msg_count = len(self.cnb_map.message_ids)

        self.cnb_map.with_context(tracking_disable=True).write({"sheet": "ROFO10_99"})
        self.flush_tracking()

        self.assertEqual(len(self.cnb_map.message_ids), msg_count)
