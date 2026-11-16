import importlib.util
from datetime import date

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path, mute_logger

from odoo.addons.investra_counterparty.models.counterparty import lei_is_valid
from odoo.addons.investra_instruments.tests.test_instrument import InstrumentCase
from odoo.addons.investra_instruments.tests.common import with_ids


@tagged("post_install", "-at_install")
class TestCounterparty(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Banka"})
        cls.sectors = cls.env["investra.esa.sector"].search([], limit=2)
        cls.cz, cls.de = cls.env.ref("base.cz"), cls.env.ref("base.de")

    def profile(self, sector=None, country=None, partner=None, **vals):
        return self.env["investra.counterparty.profile"].create({
            "partner_id": (partner or self.partner).id, "country_id": (country or self.cz).id,
            "sector_id": (sector or self.sectors[0]).id, **vals,
        })

    def test_all_esa_sectors_are_loaded(self):
        self.assertEqual(self.env["investra.esa.sector"].search_count([]), 33)

    def test_single_profile_at_any_date(self):
        """Údaje nemají platnost od data (MN-09): k libovolnému datu i bez data vrací jediný záznam."""
        profile = self.profile()
        for day in (date(1990, 1, 1), date(2026, 6, 30), date(2099, 12, 31), None):
            self.assertEqual(self.partner._counterparty_profile(day), profile)
        self.assertFalse(self.env["res.partner"].create({"name": "Bez údajů"})._counterparty_profile(date(2026, 1, 1)))

    def test_second_profile_is_refused(self):
        self.profile()
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.profile(self.sectors[1], self.de)

    def test_change_is_tracked(self):
        """Přepsaný sektor a LEI zůstávají v historii záznamu (stará a nová hodnota)."""
        profile = self.profile()
        self.env.cr.flush()  # Změna ve stejné transakci jako založení se nezaznamenává.
        profile.write({"sector_id": self.sectors[1].id, "lei": "5493001KJTIIGC8Y1R12"})
        self.env.cr.flush()
        body = "".join(self.env["mail.message"].search([
            ("model", "=", profile._name), ("res_id", "=", profile.id), ("message_type", "=", "tracking")]).mapped("body"))
        for text in (self.sectors[0].code, self.sectors[1].code, "5493001KJTIIGC8Y1R12"):
            self.assertIn(text, body)

    def test_lei_checksum(self):
        self.assertTrue(lei_is_valid("5493001KJTIIGC8Y1R12"))
        self.assertFalse(lei_is_valid("5493001KJTIIGC8Y1R13"))
        self.assertFalse(lei_is_valid("KRATKY"))

    def test_invalid_lei_is_refused(self):
        with self.assertRaises(ValidationError):
            self.profile(lei="5493001KJTIIGC8Y1R13")

    def test_instrument_issuer_profile(self):
        profile = self.profile(lei="5493001KJTIIGC8Y1R12")
        instrument = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": "Dluhopis", "currency_id": self.env.ref("base.CZK").id,
            "type_id": self.env.ref("investra_instruments.type_bond").id, "issuer_id": self.partner.id,
        }))
        self.assertEqual(instrument._issuer_profile(date(2026, 2, 1)), profile)
        self.assertEqual(instrument._issuer_profile(date(1990, 1, 1)), profile)

    def test_instrument_without_issuer_has_empty_profile(self):
        instrument = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": "Dluhopis", "currency_id": self.env.ref("base.CZK").id,
            "type_id": self.env.ref("investra_instruments.type_bond").id,
        }))
        self.assertFalse(instrument._issuer_profile(date(2026, 2, 1)))


@tagged("post_install", "-at_install")
class TestRepoRole(InstrumentCase):
    """Reverzní repo podle sektoru protistrany: banka skupina 13, ostatní skupina 21 (rozhodnutí 2026-11-11)."""

    def repo(self, sector_code):
        partner = self.env["res.partner"].create({"name": f"Protistrana {sector_code}"})
        self.env["investra.counterparty.profile"].create({
            "partner_id": partner.id, "country_id": self.env.ref("base.cz").id,
            "sector_id": self.env["investra.esa.sector"].search([("code", "=", sector_code)]).id,
        })
        instrument = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"Repo {sector_code}", "currency_id": self.czk.id, "counterparty_id": partner.id,
            "type_id": self.env.ref("investra_instruments.type_repo").id,
        }, self.fund))
        return self.classify(self.fund, instrument, "hold_to_collect")

    def test_bank_counterparty_keeps_repo(self):
        self.assertEqual(self.repo("1220000").role_id, self.env.ref("investra_entity.role_repo"))

    def test_non_bank_counterparty_is_repo_client(self):
        classification = self.repo("1100000")
        self.assertEqual(classification.role_id, self.env.ref("investra_entity.role_repo_client"))
        self.assertFalse(classification.deviates_from_proposal)


@tagged("post_install", "-at_install")
class TestEntityIdentification(TransactionCase):
    """LEI a sektor knihy z údajů protistrany kontaktu společnosti (MN-05)."""

    def test_lei_and_sector_from_profile(self):
        czk = self.env.ref("base.CZK")
        entity = self.env["investra.entity"].create_book("Fond LEI", "fund", "cas501", czk, "cz")
        self.assertFalse(entity.lei)
        self.assertFalse(entity.esa_sector_id)
        action = entity.action_open_counterparty_profiles()
        self.assertEqual((action["view_mode"], action["res_id"]), ("form", False))  # zatím bez údajů: nový záznam
        sector = self.env["investra.esa.sector"].search([], limit=1)
        partner = entity.company_id.partner_id
        profile = self.env["investra.counterparty.profile"].create({
            "partner_id": partner.id, "country_id": self.env.ref("base.cz").id,
            "sector_id": sector.id, "lei": "5493001KJTIIGC8Y1R12",
        })
        entity.invalidate_recordset()
        self.assertEqual(entity.lei, "5493001KJTIIGC8Y1R12")
        self.assertEqual(entity.esa_sector_id, sector)
        action = entity.action_open_counterparty_profiles()
        self.assertEqual(action["res_id"], profile.id)  # jediný záznam
        self.assertEqual(action["context"]["default_partner_id"], partner.id)
        self.assertEqual(action["context"]["default_country_id"], self.env.ref("base.cz").id)


@tagged("post_install", "-at_install")
class TestMergeMigration(TransactionCase):
    """Migrace MN-09: víc záznamů téhož kontaktu se sloučí do nejnovějšího, hodnoty starších jdou do historie."""

    def test_merge_duplicates(self):
        path = file_path("investra_counterparty/migrations/20.0.0.4.0/post-migration.py")
        spec = importlib.util.spec_from_file_location("mn09_post_migration", path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        # Stav před migrací: bez omezení unique(partner_id) (DDL se na konci testu vrátí s transakcí).
        self.env.cr.execute("ALTER TABLE investra_counterparty_profile DROP CONSTRAINT investra_counterparty_profile_partner_uniq")
        Profile = self.env["investra.counterparty.profile"]
        sectors = self.env["investra.esa.sector"].search([], limit=2)
        partner, other = self.env["res.partner"].create([{"name": "Dvakrát"}, {"name": "Jednou"}])
        vals = {"partner_id": partner.id, "country_id": self.env.ref("base.cz").id}
        old = Profile.create({**vals, "sector_id": sectors[0].id, "lei": "5493001KJTIIGC8Y1R12"})
        new = Profile.create({**vals, "sector_id": sectors[1].id})
        single = Profile.create({**vals, "partner_id": other.id, "sector_id": sectors[0].id})
        self.assertEqual(migration.merge_duplicates(self.env), 1)
        self.assertFalse(old.exists())
        self.assertEqual(Profile.search([("partner_id", "in", (partner | other).ids)]), new | single)
        note = new.message_ids.filtered(lambda m: "MN-09" in (m.body or ""))
        self.assertEqual(len(note), 1)
        self.assertIn("5493001KJTIIGC8Y1R12", note.body)
        self.assertFalse(single.message_ids.filtered(lambda m: "MN-09" in (m.body or "")))
