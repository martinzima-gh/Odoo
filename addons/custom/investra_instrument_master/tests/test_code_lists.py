from datetime import date

from psycopg2 import IntegrityError

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestCodeLists(TransactionCase):
    def esa(self, code):
        return self.env["investra.esa.code"].search([("code", "=", code)])

    def test_esa_codes_and_issuer_types(self):
        self.assertEqual(self.env["investra.esa.code"].search_count([]), 80)
        by_code = {}
        for rec in self.env["investra.esa.code"].search([]):
            by_code[rec.aggregate_sector_id.code] = by_code.get(rec.aggregate_sector_id.code, 0) + 1
        self.assertEqual(by_code, {"VLI": 8, "BANK": 18, "FIN": 42, "NFP": 6, "OST": 6})

    def test_esa_mapping_examples(self):
        for code, residency, agg in (("1311000", "r", "VLI"), ("2002212", "nr", "BANK"), ("1230100", "r", "FIN")):
            rec = self.esa(code)
            self.assertEqual((rec.residency, rec.aggregate_sector_id.code), (residency, agg), code)
        self.assertEqual(self.esa("2002212").esa2010_sector_id.code, "2002200")
        self.assertFalse(self.esa("1443000").esa2010_sector_id)
        self.assertTrue(self.esa("2009031").any_country)

    def test_residency_warning(self):
        rec = self.esa("1311000")
        self.assertFalse(rec.residency_warning)
        rec.residency = "nr"
        self.assertTrue(rec.residency_warning)
        rec.residency = "r"
        self.assertFalse(rec.residency_warning)

    def test_ba0088_seed(self):
        model = self.env["investra.ba0088.code"]
        self.assertEqual(model.search_count([]), 84)
        selectable = model.search([("selectable", "=", True)])
        self.assertEqual(len(selectable), 52)
        self.assertFalse(selectable.filtered(lambda r: not r.asset_family or not r.group_id))
        self.assertEqual(model.search_count([("leverage_rule", "=", "must_true")]), 1)
        self.assertEqual(model.search([("leverage_rule", "=", "must_true")]).code, "63")
        self.assertEqual(model.search([("leverage_rule", "=", "must_false")]).code, "191")
        self.assertEqual(model.search([("requires_justification", "=", True)]).code, "7")
        self.assertEqual(model.search([("code", "=", "6111")]).parent_code, "611")

    def test_ba0088_selectable_needs_family(self):
        with self.assertRaises(ValidationError):
            self.env["investra.ba0088.code"].create({"code": "ZZ1", "name": "Test", "selectable": True})

    def test_eu_membership(self):
        eu = self.env["investra.country.group.membership"].search([("group", "=", "eu")])
        self.assertEqual(len(eu), 27)
        self.assertEqual(set(eu.mapped("valid_from")), {date(2020, 2, 1)})
        self.assertIn(self.env.ref("base.cz"), eu.country_id)

    def test_membership_overlap_rejected(self):
        cz = self.env.ref("base.cz")
        model = self.env["investra.country.group.membership"]
        with self.assertRaises(ValidationError):
            model.create({"country_id": cz.id, "group": "eu", "valid_from": "2021-01-01"})
        # jiná skupina téže země a navazující období jsou v pořádku
        model.create({"country_id": cz.id, "group": "eea", "valid_from": "2021-01-01"})
        old = model.search([("country_id", "=", cz.id), ("group", "=", "eu")])
        old.valid_to = "2025-12-31"
        model.create({"country_id": cz.id, "group": "eu", "valid_from": "2026-01-01"})
        with self.assertRaises(ValidationError):
            model.create({"country_id": cz.id, "group": "eu", "valid_from": "2025-06-01", "valid_to": "2026-02-01"})

    def test_measurement_categories_and_reasons(self):
        cats = self.env["investra.measurement.category"].search([])
        self.assertEqual(set(cats.mapped("code")), {"AC", "FVOCI_D", "FVOCI_E", "FVTPL"})
        self.assertEqual(cats.filtered(lambda c: c.code == "AC").ifrs9_category, "amortised")
        reasons = self.env["investra.classification.reason"].search([])
        self.assertEqual(len(reasons), 6)
        self.assertEqual(reasons.filtered("requires_note").code, "OTHER")

    def test_code_unique_and_immutable(self):
        group = self.env["investra.ba0088.group"].search([("code", "=", "GOV_BONDS")])
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.cr.savepoint():
            self.env["investra.ba0088.group"].create({"code": "GOV_BONDS", "name": "Duplicita"})
        user = self.env["res.users"].create({
            "name": "Správce", "login": "codelist_manager_t",
            "group_ids": [(6, 0, [self.env.ref("investra_instrument_master.group_codelist_manager").id])]})
        with self.assertRaises(UserError):
            group.with_user(user).write({"code": "X"})
        group.with_user(user).write({"name": "Státní dluhopisy ČR"})
        self.assertTrue(group.locally_modified)
        group.sudo().write({"code": "GOV_BONDS"})

    def test_valid_to_before_from(self):
        with self.assertRaises(ValidationError):
            self.env["investra.ba0088.group"].create({
                "code": "T1", "name": "T", "valid_from": "2026-01-01", "valid_to": "2025-01-01"})

    def test_tracking_of_name_and_issuer_type(self):
        rec = self.esa("1210000")
        fin = self.env.ref("investra_instrument_master.esa_aggregate_fin")
        self.env.cr.flush()  # Změna ve stejné transakci jako založení se nezaznamenává.
        rec.write({"name": "Centrální banka ČR"})
        self.env.cr.flush()
        rec.write({"aggregate_sector_id": fin.id})
        self.env.cr.flush()
        messages = self.env["mail.message"].search([
            ("model", "=", "investra.esa.code"), ("res_id", "=", rec.id), ("message_type", "=", "tracking")])
        self.assertEqual(len(messages), 2)
