import base64
from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import NavCase


@tagged("post_install", "-at_install")
class TestAttachmentLock(NavCase):
    """Přílohy ocenění po odeslání ke schválení nejdou změnit ani smazat (rozhodnutí 2026-11-10)."""

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}])
        self.subscribe(self.cls(self.fund, "A"), "2027-01-01", 1000, 10)
        self.common_result(self.fund, "r1", "2027-01-15", 100)
        self.day = date(2027, 1, 31)

    def with_external(self):
        valuation = self.valuation(self.fund, self.day)
        self.manual_fee(valuation, 5, document=base64.b64encode(b"vypocet").decode(), document_name="vypocet.xlsx")
        return valuation

    def test_uploaded_document_becomes_valuation_attachment(self):
        valuation = self.with_external()
        attachment = valuation.external_fee_ids.attachment_id
        self.assertEqual((attachment.name, attachment.res_model, attachment.res_id),
                         ("vypocet.xlsx", "investra.valuation", valuation.id))
        valuation.action_compute()
        self.assertEqual(valuation.state, "computed")

    def test_external_attachment_editable_before_submit_locked_after(self):
        valuation = self.with_external()
        attachment = valuation.external_fee_ids.attachment_id
        attachment.with_user(self.preparer).write({"name": "oprava.xlsx"})
        valuation.action_compute()
        valuation.action_submit()
        with self.assertRaises(UserError):
            attachment.with_user(self.preparer).write({"raw": b"jiny"})
        with self.assertRaises(UserError):
            attachment.with_user(self.preparer).unlink()
        with self.assertRaises(UserError):
            valuation.external_fee_ids.with_user(self.preparer).write({"amount": 6})
        with self.assertRaises(UserError):
            valuation.external_fee_ids.with_user(self.preparer).unlink()

    def test_package_cannot_be_replaced_and_rebuild_makes_new_file(self):
        valuation = self.with_external()
        self.run_to_posted(valuation)
        package = valuation.with_user(self.preparer).action_build_package()
        self.assertEqual(valuation.package_checksum, package.checksum)
        self.assertTrue(valuation.package_ok)
        for user in (self.preparer, self.approver):
            with self.assertRaises(UserError):
                package.with_user(user).write({"raw": b"cizi", "name": "cizi.docx"})
            with self.assertRaises(UserError):
                package.with_user(user).unlink()
        again = valuation.with_user(self.preparer).action_build_package()
        self.assertNotEqual(again, package)
        self.assertTrue(package.exists())
        self.assertEqual(valuation.package_id, again)

    def test_changed_package_is_reported(self):
        valuation = self.run_to_posted(self.with_external())
        package = valuation.with_user(self.preparer).action_build_package()
        package.sudo().write({"raw": b"cizi"})
        valuation.invalidate_recordset(["package_ok"])
        self.assertFalse(valuation.package_ok)

    def test_new_attachment_on_closed_valuation_can_be_added(self):
        valuation = self.run_to_posted(self.with_external())
        note = self.env["ir.attachment"].with_user(self.preparer).create({
            "name": "poznamka.txt", "raw": b"x",
            "res_model": "investra.valuation", "res_id": valuation.id,
        })
        self.assertTrue(note.exists())

    def test_external_class_and_account_must_belong_to_valuation_fund(self):
        """Ručně doložená úplata nesmí použít třídu ani účet jiného fondu (uživatel 2026-11-13, ZJ-03)."""
        valuation = self.valuation(self.fund, self.day)
        own_company = self.fund.company_id
        own_account = self.expense_account(self.fund).id
        # make_fund přepne testovací prostředí do firmy nového fondu; zápis do ocenění pak běží s oběma firmami.
        other = self.make_fund(classes=[{"code": "B"}])
        valuation = valuation.with_context(allowed_company_ids=[own_company.id, other.company_id.id])
        for vals in ({"class_id": self.cls(other, "B").id, "account_id": own_account},
                     {"account_id": self.expense_account(other).id}):
            with self.assertRaises(ValidationError):
                valuation.write({"external_fee_ids": [(0, 0, dict(vals, amount=5, note="x"))]})
        valuation.write({"external_fee_ids": [(0, 0, {
            "class_id": self.cls(self.fund, "A").id, "amount": 5, "note": "x", "account_id": own_account})]})
        self.assertEqual(len(valuation.external_fee_ids), 1)
