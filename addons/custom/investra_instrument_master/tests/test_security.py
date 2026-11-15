from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCodelistSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        users = cls.env["res.users"]
        cls.reader = users.create({"name": "Čtenář", "login": "cl_reader",
                                   "group_ids": [(6, 0, [cls.env.ref("account.group_account_readonly").id])]})
        cls.manager = users.create({"name": "Správce", "login": "cl_manager", "group_ids": [
            (6, 0, [cls.env.ref("investra_instrument_master.group_codelist_manager").id])]})
        cls.group = cls.env["investra.ba0088.group"]

    def test_reader_cannot_write(self):
        rec = self.env["investra.ba0088.group"].search([], limit=1)
        self.assertTrue(rec.with_user(self.reader).read(["name"]))
        with self.assertRaises(AccessError):
            rec.with_user(self.reader).write({"name": "X"})
        with self.assertRaises(AccessError):
            self.group.with_user(self.reader).create({"code": "RD", "name": "X"})

    def test_manager_creates_and_edits_but_nobody_deletes(self):
        rec = self.group.with_user(self.manager).create({"code": "MG1", "name": "Nový"})
        rec.write({"name": "Upravený"})
        with self.assertRaises(AccessError):
            rec.unlink()

    def test_reader_and_manager_cannot_delete_other_codelists(self):
        for model in ("investra.esa.code", "investra.ba0088.code", "investra.country.group.membership",
                      "investra.measurement.category", "investra.classification.reason"):
            rec = self.env[model].search([], limit=1)
            for user in (self.reader, self.manager):
                with self.assertRaises(AccessError, msg=model):
                    rec.with_user(user).unlink()

    def test_measurement_category_created_only_by_module(self):
        with self.assertRaises(Exception):
            self.env["investra.measurement.category"].with_user(self.manager).create({
                "code": "NEW", "name": "Nová", "ifrs9_category": "fvtpl"})
