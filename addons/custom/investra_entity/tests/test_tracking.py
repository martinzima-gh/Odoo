from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEntityTracking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.czk = cls.env.ref("base.CZK")
        cls.czk.active = True
        cls.entity = cls.env["investra.entity"].create_book("Kniha Tracking", "fund", "cas501", cls.czk, "cz")
        cls.account_role = cls.env["investra.account.role"].create({
            "code": "test_role_tracking",
            "name": "Testovací role",
            "category": "asset",
        })
        cls.account = cls.env["account.account"].create({
            "name": "Testovací účet",
            "code": "379999",
            "account_type": "liability_current",
            "company_ids": [(6, 0, cls.entity.company_id.ids)],
        })
        cls.account2 = cls.env["account.account"].create({
            "name": "Testovací účet 2",
            "code": "379998",
            "account_type": "liability_current",
            "company_ids": [(6, 0, cls.entity.company_id.ids)],
        })
        cls.extra_account = cls.env["account.account"].create({
            "name": "Testovací další účet",
            "code": "379997",
            "account_type": "liability_current",
            "company_ids": [(6, 0, cls.entity.company_id.ids)],
        })
        cls.role_account = cls.env["investra.role.account"].create({
            "company_id": cls.entity.company_id.id,
            "role_id": cls.account_role.id,
            "account_id": cls.account.id,
        })

    def flush_tracking(self):
        """Vyvolá zápis tracking zpráv v předcommitové fázi bez volání commit()."""
        self.env.flush_all()
        if hasattr(self.env.cr, "precommit"):
            self.env.cr.precommit.run()

    def test_entity_tracking(self):
        """Změna sledovaného pole účetní knihy vytvoří tracking zprávu."""
        self.flush_tracking()
        msg_count_before = len(self.entity.message_ids)

        self.entity.write({"entity_type": "sicav"})
        self.flush_tracking()

        self.assertGreater(len(self.entity.message_ids), msg_count_before)
        new_msgs = self.entity.message_ids[:len(self.entity.message_ids) - msg_count_before]
        bodies = [m.body or "" for m in new_msgs]
        self.assertTrue(any("(Druh jednotky)" in b and "SICAV" in b for b in bodies))

        # Změna rámce (v knize bez zaúčtovaných dokladů)
        msg_count_before = len(self.entity.message_ids)
        self.entity.write({"framework": "ifrs"})
        self.flush_tracking()

        new_msgs = self.entity.message_ids[:len(self.entity.message_ids) - msg_count_before]
        bodies = [m.body or "" for m in new_msgs]
        self.assertTrue(any("(Účetní rámec)" in b and "IFRS přijaté EU" in b for b in bodies))

    def test_account_role_tracking(self):
        """Změna sledovaného pole role účtu vytvoří tracking zprávu."""
        self.flush_tracking()
        msg_count_before = len(self.account_role.message_ids)

        self.account_role.write({
            "name": "Změněná role",
            "category": "liability",
        })
        self.flush_tracking()

        self.assertGreater(len(self.account_role.message_ids), msg_count_before)
        new_msgs = self.account_role.message_ids[:len(self.account_role.message_ids) - msg_count_before]
        bodies = [m.body or "" for m in new_msgs]
        self.assertTrue(any("(Název)" in b and "Změněná role" in b for b in bodies))
        self.assertTrue(any("(Druh)" in b and "Závazek" in b for b in bodies))

    def test_role_account_tracking(self):
        """Změna sledovaného pole účtu role vytvoří tracking zprávu."""
        self.flush_tracking()
        msg_count_before = len(self.role_account.message_ids)

        self.role_account.write({"account_id": self.account2.id})
        self.flush_tracking()

        self.assertGreater(len(self.role_account.message_ids), msg_count_before)
        new_msgs = self.role_account.message_ids[:len(self.role_account.message_ids) - msg_count_before]
        bodies = [m.body or "" for m in new_msgs]
        self.assertTrue(any("(Účet)" in b for b in bodies))

    def test_role_account_extra_accounts_tracking(self):
        """Ověření, zda se v chatteru ukáže změna Many2many extra_account_ids (bod 6 zadání)."""
        self.flush_tracking()
        msg_count_before = len(self.role_account.message_ids)

        self.role_account.write({"extra_account_ids": [(4, self.extra_account.id)]})
        self.flush_tracking()

        new_msgs = self.role_account.message_ids[:len(self.role_account.message_ids) - msg_count_before]
        bodies = [m.body or "" for m in new_msgs]
        # Odoo 20 sleduje i Many2many (mail_track_mixin, typy one2many/many2many/tags); změna se musí v chatteru ukázat.
        # Převzetí ZJ-10 1b (Claude): původní test prošel v obou případech, nic neověřoval.
        self.assertTrue(any("(Další účty)" in b for b in bodies), bodies)

    def test_tracking_disable_context(self):
        """Kontext tracking_disable=True potlačí zápis do chatteru."""
        self.flush_tracking()
        msg_count_entity = len(self.entity.message_ids)
        msg_count_role = len(self.account_role.message_ids)

        self.entity.with_context(tracking_disable=True).write({"entity_type": "manager"})
        self.account_role.with_context(tracking_disable=True).write({"name": "Tichá změna"})
        self.flush_tracking()

        self.assertEqual(len(self.entity.message_ids), msg_count_entity)
        self.assertEqual(len(self.account_role.message_ids), msg_count_role)
