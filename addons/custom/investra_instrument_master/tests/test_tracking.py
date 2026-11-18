from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestInstrumentMasterTracking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.role1 = cls.env["investra.account.role"].create({
            "code": "test_master_role1",
            "name": "Role 1",
            "category": "asset",
        })
        cls.role2 = cls.env["investra.account.role"].create({
            "code": "test_master_role2",
            "name": "Role 2",
            "category": "asset",
        })
        cls.ba_group = cls.env["investra.ba0088.group"].create({
            "code": "TEST_G",
            "name": "Testovací skupina BA0088",
        })
        cls.ba_code = cls.env["investra.ba0088.code"].create({
            "code": "999",
            "name": "Testovací kód BA0088",
            "group_id": cls.ba_group.id,
        })
        cls.profile = cls.env["investra.accounting.profile"].create({
            "code": "TEST_PROF",
            "name": "Testovací profil",
            "role_id": cls.role1.id,
            "note": "Původní poznámka",
        })
        cls.cfi_map = cls.env["investra.cfi.ba0088.map"].create({
            "cfi_prefix": "ZZ",
            "ba0088_id": cls.ba_code.id,
            "source": "Původní zdroj",
        })

    def flush_tracking(self):
        """Vyvolá zápis tracking zpráv v předcommitové fázi bez volání commit()."""
        self.env.flush_all()
        if hasattr(self.env.cr, "precommit"):
            self.env.cr.precommit.run()

    def test_accounting_profile_tracking(self):
        """Změna sledovaného pole účetního profilu vytvoří tracking zprávu."""
        self.flush_tracking()
        msg_count_before = len(self.profile.message_ids)

        self.profile.write({
            "role_id": self.role2.id,
            "note": "Nová poznámka",
        })
        self.flush_tracking()

        self.assertGreater(len(self.profile.message_ids), msg_count_before)
        new_msgs = self.profile.message_ids[:len(self.profile.message_ids) - msg_count_before]
        bodies = [m.body or "" for m in new_msgs]
        self.assertTrue(any("(Role účtu)" in b for b in bodies))
        self.assertTrue(any("(Poznámka)" in b and "Nová poznámka" in b for b in bodies))

    def test_cfi_ba0088_map_tracking(self):
        """Změna sledovaného pole mapy CFI na BA0088 vytvoří tracking zprávu."""
        self.flush_tracking()
        msg_count_before = len(self.cfi_map.message_ids)

        self.cfi_map.write({
            "cfi_prefix": "ZX",
            "source": "Nový zdroj",
        })
        self.flush_tracking()

        self.assertGreater(len(self.cfi_map.message_ids), msg_count_before)
        new_msgs = self.cfi_map.message_ids[:len(self.cfi_map.message_ids) - msg_count_before]
        bodies = [m.body or "" for m in new_msgs]
        self.assertTrue(any("(Začátek CFI)" in b and "ZX" in b for b in bodies))
        self.assertTrue(any("(Zdroj)" in b and "Nový zdroj" in b for b in bodies))

    def test_tracking_disable_context(self):
        """Kontext tracking_disable=True potlačí zápis do chatteru."""
        self.flush_tracking()
        msg_count_prof = len(self.profile.message_ids)
        msg_count_cfi = len(self.cfi_map.message_ids)

        self.profile.with_context(tracking_disable=True).write({"note": "Tichá poznámka"})
        self.cfi_map.with_context(tracking_disable=True).write({"source": "Tichý zdroj"})
        self.flush_tracking()

        self.assertEqual(len(self.profile.message_ids), msg_count_prof)
        self.assertEqual(len(self.cfi_map.message_ids), msg_count_cfi)
