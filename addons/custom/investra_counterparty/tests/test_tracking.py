from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCounterpartyTracking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sector = cls.env["investra.esa.sector"].create({
            "code": "9999999",
            "name": "Testovací sektor ESA",
        })

    def flush_tracking(self):
        """Vyvolá zápis tracking zpráv v předcommitové fázi bez volání commit()."""
        self.env.flush_all()
        if hasattr(self.env.cr, "precommit"):
            self.env.cr.precommit.run()

    def test_esa_sector_tracking(self):
        """Změna sledovaného pole sektoru ESA vytvoří tracking zprávu."""
        self.flush_tracking()
        msg_count_before = len(self.sector.message_ids)

        self.sector.write({"name": "Upravený sektor ESA"})
        self.flush_tracking()

        self.assertGreater(len(self.sector.message_ids), msg_count_before)
        new_msgs = self.sector.message_ids[:len(self.sector.message_ids) - msg_count_before]
        bodies = [m.body or "" for m in new_msgs]
        self.assertTrue(any("(Název)" in b and "Upravený sektor ESA" in b for b in bodies))

    def test_tracking_disable_context(self):
        """Kontext tracking_disable=True potlačí zápis do chatteru."""
        self.flush_tracking()
        msg_count = len(self.sector.message_ids)

        self.sector.with_context(tracking_disable=True).write({"name": "Tichá změna sektoru"})
        self.flush_tracking()

        self.assertEqual(len(self.sector.message_ids), msg_count)
