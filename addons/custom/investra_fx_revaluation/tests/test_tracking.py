from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestFxProfileTracking(TransactionCase):
    """ZJ-10 fáze 2: změny profilu přecenění v jeho chatteru."""

    def flush_tracking(self):
        self.env.flush_all()
        self.env.cr.precommit.run()

    def mark(self, profile):
        self.flush_tracking()
        return set(profile.message_ids.ids)

    def text(self, profile, mark):
        self.flush_tracking()
        return "\n".join(m.body or "" for m in profile.message_ids.filtered(lambda m: m.id not in mark))

    def test_name_change(self):
        profile = self.env["investra.fx.profile"].create({"name": "Profil A"})
        mark = self.mark(profile)
        profile.write({"name": "Profil B"})
        text = self.text(profile, mark)
        self.assertIn("Profil A", text)
        self.assertIn("Profil B", text)
        self.assertIn("(Název)", text)

    def test_accounts_many2many(self):
        profile = self.env["investra.fx.profile"].create({"name": "Profil"})
        account = self.env["account.account"].create({"name": "Pohledávka EUR", "code": "999111", "account_type": "asset_receivable", "reconcile": True})
        mark = self.mark(profile)
        profile.write({"account_ids": [Command.set(account.ids)]})
        self.assertIn("(Přeceňované účty)", self.text(profile, mark))

    def test_multiple_fields_one_message(self):
        profile = self.env["investra.fx.profile"].create({"name": "Profil"})
        mark = self.mark(profile)
        profile.write({"name": "Nový", "active": False})
        self.flush_tracking()
        new = profile.message_ids.filtered(lambda m: m.id not in mark)
        self.assertEqual(len(new), 1)
        self.assertIn("(Název)", new.body)
        self.assertIn("(Aktivní)", new.body)

    def test_tracking_disable(self):
        profile = self.env["investra.fx.profile"].with_context(tracking_disable=True, mail_create_nolog=True).create({"name": "Auto"})
        mark = self.mark(profile)
        profile.with_context(tracking_disable=True).write({"name": "Auto 2"})
        self.assertEqual(self.text(profile, mark), "")
        self.assertFalse(profile.message_ids)

    def test_single_chatter_in_form(self):
        arch = self.env["investra.fx.profile"].get_view(view_id=self.env.ref("investra_fx_revaluation.view_fx_profile_form").id)["arch"]
        self.assertEqual(arch.count("<chatter"), 1)
