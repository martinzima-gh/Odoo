from datetime import date

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

from odoo.addons.investra_counterparty.models.counterparty import lei_is_valid


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
        instrument = self.env["investra.instrument"].create({
            "name": "Dluhopis", "currency_id": self.env.ref("base.CZK").id,
            "type_id": self.env.ref("investra_instruments.type_bond").id, "issuer_id": self.partner.id,
        })
        self.assertEqual(instrument._issuer_profile(date(2026, 2, 1)), profile)

    def test_instrument_without_issuer_has_empty_profile(self):
        instrument = self.env["investra.instrument"].create({
            "name": "Dluhopis", "currency_id": self.env.ref("base.CZK").id,
            "type_id": self.env.ref("investra_instruments.type_bond").id,
        })
        self.assertFalse(instrument._issuer_profile(date(2026, 2, 1)))
