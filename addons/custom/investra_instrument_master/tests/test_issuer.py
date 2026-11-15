from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestIssuerProfile(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.profiles = cls.env["investra.counterparty.profile"]
        cls.partner = cls.env["res.partner"].create({"name": "Emitent"})
        cls.approver = cls.env["res.users"].create({
            "name": "Schvalovatel", "login": "issuer_approver",
            "group_ids": [(6, 0, [cls.env.ref("investra_entity.group_valuation_approver").id])]})
        cls.preparer = cls.env["res.users"].create({
            "name": "Příprava", "login": "issuer_preparer",
            "group_ids": [(6, 0, [cls.env.ref("investra_entity.group_valuation_preparer").id])]})

    def esa(self, code):
        return self.env["investra.esa.code"].search([("code", "=", code)])

    def profile(self, country, esa, day="2026-01-01", partner=None, **vals):
        return self.profiles.create({
            "partner_id": (partner or self.partner).id, "valid_from": day,
            "country_id": self.env.ref(f"base.{country}").id, "esa_code_id": self.esa(esa).id, **vals})

    def test_derived_values(self):
        for country, esa, resident, region, issuer_type in (
                ("cz", "1311000", "r", "cz", "VLI"), ("de", "2002212", "nr", "eu", "BANK"),
                ("us", "2001002", "nr", "non_eu", "NFP")):
            partner = self.env["res.partner"].create({"name": f"P {esa}"})
            profile = self.profile(country, esa, partner=partner)
            self.assertEqual(
                (profile.resident_status, profile.eu_status, profile.issuer_type_id.code),
                (resident, region, issuer_type), esa)
            self.assertIn(esa, profile.derivation_note)

    def test_sector_is_filled_from_esa_code(self):
        profile = self.profile("de", "2002212")
        self.assertEqual(profile.sector_id.code, "2002200")
        profile.write({"esa_code_id": self.esa("2001002").id, "country_id": self.env.ref("base.us").id})
        self.assertEqual(profile.sector_id, self.esa("2001002").esa2010_sector_id)

    def test_explicit_sector_is_kept(self):
        sector = self.env["investra.esa.sector"].search([("code", "=", "2002500")])
        profile = self.profile("de", "2002212", sector_id=sector.id)
        self.assertEqual(profile.sector_id, sector)

    def test_esa_without_sector_needs_manual_sector(self):
        with self.assertRaises(ValidationError):
            self.profile("de", "1443000")

    def test_esa_country_check(self):
        with self.assertRaisesRegex(ValidationError, "pro nerezidenty"):
            self.profile("cz", "2002212")
        with self.assertRaisesRegex(ValidationError, "pro rezidenty"):
            self.profile("de", "1311000")

    def test_any_country_code_skips_check(self):
        self.profile("de", "2009031")

    def test_region_follows_membership_at_date(self):
        profile = self.profile("de", "2002212")
        self.assertEqual(profile._eu_status_at(date(2026, 1, 1)), "eu")
        self.assertEqual(profile._eu_status_at(date(2019, 1, 1)), "non_eu")
        membership = self.env["investra.country.group.membership"].search(
            [("country_id", "=", self.env.ref("base.de").id), ("group", "=", "eu")])
        membership.write({"valid_to": "2020-12-31"})
        self.assertEqual(profile._eu_status_at(date(2026, 1, 1)), "non_eu")
        self.assertEqual(profile.eu_status, "non_eu")  # změna členství přepočítá uložený region
        self.assertEqual(profile.resident_status, "nr")  # ESA se tím nemění

    def test_eea_and_unknown_region(self):
        no = self.env.ref("base.no")
        self.env["investra.country.group.membership"].create(
            {"country_id": no.id, "group": "eea", "valid_from": "2000-01-01"})
        self.assertEqual(self.profile("no", "2002212")._eu_status_at(date(2026, 1, 1)), "eea")
        old = self.profiles.create({
            "partner_id": self.partner.id, "valid_from": "2000-01-01", "country_id": no.id,
            "sector_id": self.esa("2002212").esa2010_sector_id.id})
        self.assertFalse(old.derivation_note)

    def test_review_only_by_approver(self):
        profile = self.profile("de", "2002212")
        with self.assertRaises(UserError):
            profile.with_user(self.preparer).action_review()
        profile.with_user(self.approver).action_review()
        self.assertEqual(
            (profile.review_state, profile.reviewed_by, profile.reviewed_on),
            ("reviewed", self.approver, fields_today(self.env)))

    def test_reviewed_version_is_locked(self):
        profile = self.profile("de", "2002212")
        profile.with_user(self.approver).action_review()
        with self.assertRaisesRegex(UserError, "Potvrzenou verzi nejde změnit"):
            profile.with_user(self.preparer).write({"lei": "5493001KJTIIGC8Y1R12"})
        with self.assertRaises(UserError):
            profile.with_user(self.preparer).unlink()

    def test_review_needs_esa_code(self):
        old = self.profiles.create({
            "partner_id": self.partner.id, "valid_from": "2000-01-01", "country_id": self.env.ref("base.cz").id,
            "sector_id": self.esa("1311000").esa2010_sector_id.id})
        with self.assertRaises(UserError):
            old.with_user(self.approver).action_review()

    def test_second_version_needs_reason(self):
        first = self.profile("de", "2002212")
        with self.assertRaisesRegex(ValidationError, "důvod změny"):
            self.profile("de", "2002212", day="2026-07-01")
        second = self.profile("de", "2002212", day="2026-07-01", change_reason="Změna ESA po kontrole")
        self.assertTrue(second.is_latest)
        self.assertFalse(first.is_latest)

    def test_is_latest_follows_changes(self):
        first = self.profile("de", "2002212")
        second = self.profile("de", "2002212", day="2026-07-01", change_reason="Nová verze")
        second.unlink()
        self.assertTrue(first.is_latest)
        second = self.profile("de", "2002212", day="2026-07-01", change_reason="Nová verze")
        first.write({"valid_from": "2026-12-01", "change_reason": "Přesun"})
        self.assertTrue(first.is_latest)
        self.assertFalse(second.is_latest)

    def test_lei_unique_across_partners(self):
        lei = "5493001KJTIIGC8Y1R12"
        self.profile("de", "2002212", lei=lei)
        other = self.env["res.partner"].create({"name": "Jiný"})
        with self.assertRaisesRegex(ValidationError, "už má protistrana"):
            self.profile("de", "2002212", partner=other, lei=lei)
        # Nová verze téže protistrany může LEI zachovat.
        self.profile("de", "2002212", day="2026-07-01", lei=lei, change_reason="Nová verze")


def fields_today(env):
    from odoo import fields
    return fields.Date.context_today(env["res.users"])
