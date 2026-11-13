from datetime import date

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

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

    def profile(self, day, sector=None, country=None, **vals):
        return self.env["investra.counterparty.profile"].create({
            "partner_id": self.partner.id, "valid_from": day, "country_id": (country or self.cz).id,
            "sector_id": (sector or self.sectors[0]).id, **vals,
        })

    def test_all_esa_sectors_are_loaded(self):
        self.assertEqual(self.env["investra.esa.sector"].search_count([]), 33)

    def test_profile_valid_at_date(self):
        old = self.profile("2026-01-01")
        new = self.profile("2026-07-01", self.sectors[1], self.de)
        self.assertEqual(self.partner._counterparty_profile(date(2026, 6, 30)), old)
        self.assertEqual(self.partner._counterparty_profile(date(2026, 7, 1)), new)

    def test_no_profile_before_first_date(self):
        self.profile("2026-01-01")
        self.assertFalse(self.partner._counterparty_profile(date(2025, 12, 31)))

    def test_duplicate_date_is_refused(self):
        self.profile("2026-01-01")
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.profile("2026-01-01")

    def test_lei_checksum(self):
        self.assertTrue(lei_is_valid("5493001KJTIIGC8Y1R12"))
        self.assertFalse(lei_is_valid("5493001KJTIIGC8Y1R13"))
        self.assertFalse(lei_is_valid("KRATKY"))

    def test_invalid_lei_is_refused(self):
        with self.assertRaises(ValidationError):
            self.profile("2026-01-01", lei="5493001KJTIIGC8Y1R13")

    def test_instrument_issuer_profile(self):
        profile = self.profile("2026-01-01", lei="5493001KJTIIGC8Y1R12")
        instrument = self.env["investra.instrument"].create(with_ids(self.env, {
            "name": "Dluhopis", "currency_id": self.env.ref("base.CZK").id,
            "type_id": self.env.ref("investra_instruments.type_bond").id, "issuer_id": self.partner.id,
        }))
        self.assertEqual(instrument._issuer_profile(date(2026, 2, 1)), profile)

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
            "partner_id": partner.id, "valid_from": "2000-01-01", "country_id": self.env.ref("base.cz").id,
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
