from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestFxProfile(TransactionCase):
    def test_defaults(self):
        profile = self.env["investra.fx.profile"].create({"name": "Test"})

        self.assertTrue(profile.active)
        self.assertEqual(profile.company_id, self.env.company)

    def test_rate_source_follows_company_currency(self):
        company = self.env["res.company"].create({"name": "Zdroj CZK", "currency_id": self.env.ref("base.CZK").id})
        Profile = self.env["investra.fx.profile"]
        self.assertEqual(Profile.create({"name": "ČNB", "company_id": company.id}).rate_source, "cnb")
        with self.assertRaises(ValidationError):
            Profile.create({"name": "ECB", "company_id": company.id, "rate_source": "ecb"})


@tagged("post_install", "-at_install")
class TestFxProfileAccess(TransactionCase):
    """Práva a oddělení společností podle security/ir.access.csv."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Profile = cls.env["investra.fx.profile"]
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Investra test B"})
        cls.profile_a = Profile.create({"name": "Profil A", "company_id": cls.company_a.id})
        cls.profile_b = Profile.create({"name": "Profil B", "company_id": cls.company_b.id})

        def make_user(login, group_xmlid):
            return cls.env["res.users"].create({
                "name": login,
                "login": login,
                "company_id": cls.company_b.id,
                "company_ids": [(6, 0, [cls.company_b.id])],
                "group_ids": [(6, 0, [
                    cls.env.ref("base.group_user").id,
                    cls.env.ref(group_xmlid).id,
                ])],
            })

        cls.reader_b = make_user("fx_reader_b", "account.group_account_readonly")
        cls.manager_b = make_user("fx_manager_b", "account.group_account_manager")

    def _profiles_as(self, user):
        return self.env["investra.fx.profile"].with_user(user).with_company(self.company_b)

    def test_user_sees_only_own_company(self):
        visible = self._profiles_as(self.reader_b).search([])
        self.assertIn(self.profile_b, visible)
        self.assertNotIn(self.profile_a, visible)

    def test_reader_cannot_create(self):
        with self.assertRaises(AccessError):
            self._profiles_as(self.reader_b).create({"name": "Nepovolený"})

    def test_manager_can_create_in_own_company(self):
        profile = self._profiles_as(self.manager_b).create({"name": "Nový B"})
        self.assertEqual(profile.company_id, self.company_b)

    def test_manager_cannot_read_other_company(self):
        with self.assertRaises(AccessError):
            self.profile_a.with_user(self.manager_b).with_company(self.company_b).read(["name"])
