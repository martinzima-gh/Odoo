from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestFxProfile(TransactionCase):
    def test_defaults(self):
        profile = self.env["investra.fx.profile"].create({"name": "Test"})

        self.assertTrue(profile.active)
        self.assertEqual(profile.company_id, self.env.company)
