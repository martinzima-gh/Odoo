from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestInstrumentTracking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.role = cls.env["investra.account.role"].create({
            "code": "test_inst_type_role",
            "name": "Role pro typ nástroje",
            "category": "asset",
        })
        cls.instrument_type = cls.env["investra.instrument.type"].create({
            "code": "TEST_TYPE",
            "name": "Testovací typ",
            "group": "debt",
            "kind": "bond",
            "ifrs9_category": "amortised",
            "valuation_method": "price",
            "role_id": cls.role.id,
        })

    def flush_tracking(self):
        """Vyvolá zápis tracking zpráv v předcommitové fázi bez volání commit()."""
        self.env.flush_all()
        if hasattr(self.env.cr, "precommit"):
            self.env.cr.precommit.run()

    def test_instrument_type_tracking(self):
        """Změna sledovaného pole typu nástroje vytvoří tracking zprávu."""
        self.flush_tracking()
        msg_count_before = len(self.instrument_type.message_ids)

        self.instrument_type.write({
            "name": "Upravený typ",
            "valuation_method": "model",
        })
        self.flush_tracking()

        self.assertGreater(len(self.instrument_type.message_ids), msg_count_before)
        new_msgs = self.instrument_type.message_ids[:len(self.instrument_type.message_ids) - msg_count_before]
        bodies = [m.body or "" for m in new_msgs]
        self.assertTrue(any("(Název)" in b and "Upravený typ" in b for b in bodies))
        self.assertTrue(any("(Navržený způsob ocenění)" in b and "Model nebo znalec" in b for b in bodies))

    def test_tracking_disable_context(self):
        """Kontext tracking_disable=True potlačí zápis do chatteru."""
        self.flush_tracking()
        msg_count = len(self.instrument_type.message_ids)

        self.instrument_type.with_context(tracking_disable=True).write({"name": "Tichá změna typu"})
        self.flush_tracking()

        self.assertEqual(len(self.instrument_type.message_ids), msg_count)
