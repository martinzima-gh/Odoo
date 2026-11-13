"""Sdílené nástroje a pravidlo knihy (rozhodnutí 2026-11-13).

Nástroj s ISIN je sdílený a vede ho kniha investiční společnosti; nástroj bez ISIN patří jednomu fondu.
ISIN + měna jsou jedinečné, kód nástroje přiděluje systém, změny údajů a toků jdou do historie nástroje.
"""

import re

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import manager_book
from .test_instrument import InstrumentCase


@tagged("post_install", "-at_install")
class TestInstrumentIdentifiers(InstrumentCase):
    def bond(self, **vals):
        return self.env["investra.instrument"].create({
            "name": "Dluhopis", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_bond").id, **vals,
        })

    def deposit(self, **vals):
        return self.env["investra.instrument"].create({
            "name": "Vklad", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_deposit").id, **vals,
        })

    def test_isin_required_by_type(self):
        with self.assertRaises(ValidationError):
            self.bond()

    def test_isin_normalized_and_code_by_type(self):
        bond = self.bond(isin=" cz 0001 234567 ")
        self.assertEqual(bond.isin, "CZ0001234567")
        self.assertTrue(bond.code.startswith("DLU-"))
        self.assertFalse(bond.fund_id)

    def test_isin_and_currency_unique(self):
        self.bond(isin="CZ0001234567")
        self.bond(isin="CZ0001234567", currency_id=self.eur.id)  # jiná měna je jiný nástroj
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.bond(isin="cz0001234567")

    def test_isin_instrument_is_shared(self):
        with self.assertRaises(ValidationError):
            self.bond(isin="CZ0001234567", fund_id=self.fund.id)

    def test_without_isin_needs_fund_and_identifier(self):
        with self.assertRaises(ValidationError):
            self.deposit(identifier_kind="contract", identifier="TV-1")
        with self.assertRaises(ValidationError):
            self.deposit(fund_id=self.fund.id)
        deposit = self.deposit(fund_id=self.fund.id, identifier_kind="contract", identifier=" TV-1 ")
        self.assertEqual((deposit.identifier, deposit.company_id), ("TV-1", self.company))
        self.assertTrue(deposit.code.startswith("TV-"))

    def test_identifier_unique_in_fund(self):
        self.deposit(fund_id=self.fund.id, identifier_kind="contract", identifier="TV-1")
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.deposit(fund_id=self.fund.id, identifier_kind="contract", identifier="TV-1")

    def test_code_cannot_be_changed(self):
        deposit = self.deposit(fund_id=self.fund.id, identifier_kind="contract", identifier="TV-1")
        with self.assertRaises(UserError):
            deposit.with_user(self.preparer).write({"code": "TV-X"})

    def test_instrument_cannot_move_between_books(self):
        deposit = self.deposit(fund_id=self.fund.id, identifier_kind="contract", identifier="TV-1")
        with self.assertRaises(UserError):
            deposit.with_user(self.preparer).write({"fund_id": False})

    def test_currency_locked_after_first_trade(self):
        instrument = self.instrument
        instrument.write({"currency_id": self.czk.id})  # bez obchodu jde měnu změnit
        self.env["investra.trade"].create({
            "fund_id": self.fund.id, "instrument_id": instrument.id, "trade_date": "2030-01-05", "quantity": 1, "price": 10,
        })
        with self.assertRaises(UserError):
            instrument.with_user(self.preparer).write({"currency_id": self.eur.id})

    def test_shared_instrument_needs_manager_book(self):
        """Před knihou investiční společnosti sdílený nástroj běžný uživatel nezaloží; skripty ano, bez knihy."""
        if self.env["investra.entity"].search_count([("entity_type", "=", "manager")]):
            self.skipTest("Databáze už má knihu investiční společnosti.")
        with self.assertRaises(UserError):
            self.env["investra.instrument"].with_user(self.preparer).create({
                "name": "Akcie", "isin": "XS0001234567", "currency_id": self.eur.id,
                "type_id": self.env.ref("investra_instruments.type_equity").id,
            })
        self.assertFalse(self.instrument.company_id)


@tagged("post_install", "-at_install")
class TestSharedInstrumentBook(InstrumentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager_company = manager_book(cls.env, cls.czk).company_id
        cls.other_book = cls.env["investra.entity"].create_book("Fond B", "fund", "cas501", cls.czk, "investra_fund")
        cls.other_fund = cls.env["investra.fund"].create({"entity_id": cls.other_book.id})
        cls.admin_user = cls.env["res.users"].create({
            "name": "inst_admin", "login": "inst_admin", "company_id": cls.manager_company.id,
            "company_ids": [(6, 0, [cls.manager_company.id, cls.company.id])],
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id, cls.env.ref("investra_entity.group_valuation_preparer").id])],
        })

    def as_admin(self, record):
        return record.with_user(self.admin_user).with_context(allowed_company_ids=[self.manager_company.id, self.company.id])

    def test_manager_book_adopts_shared_instruments(self):
        self.assertEqual(self.instrument.company_id, self.manager_company)

    def test_only_manager_book_changes_shared_instrument(self):
        with self.assertRaises(AccessError):
            self.instrument.with_user(self.preparer).write({"name": "Přejmenováno"})
        with self.assertRaises(AccessError):
            self.env["investra.instrument.cashflow"].with_user(self.preparer).create({
                "instrument_id": self.instrument.id, "date": "2031-01-01", "amount": 1,
            })
        self.as_admin(self.instrument).write({"name": "Přejmenováno"})
        self.assertEqual(self.instrument.name, "Přejmenováno")
        # Sdílený nástroj vidí každý fond.
        self.assertEqual(self.instrument.with_user(self.preparer).read(["name"])[0]["name"], "Přejmenováno")

    def test_book_not_active_gives_clear_message(self):
        """Hláška řekne, kterou knihu zaškrtnout, nebo že ji uživatel nemá povolenou (místo chyby více společností)."""
        vals = {"name": "Akcie", "isin": "XS0009876543", "currency_id": self.eur.id,
                "type_id": self.env.ref("investra_instruments.type_equity").id}
        Instrument = self.env["investra.instrument"]
        # Kniha je povolená, ale není zaškrtnutá v přepínači.
        with self.assertRaisesRegex(AccessError, "Zaškrtněte ji v přepínači"):
            Instrument.with_user(self.admin_user).with_context(allowed_company_ids=[self.company.id]).create(vals)
        # Kniha není mezi povolenými společnostmi.
        with self.assertRaisesRegex(AccessError, "nemáte mezi povolenými"):
            Instrument.with_user(self.preparer).create(vals)
        with self.assertRaisesRegex(AccessError, re.escape(self.manager_company.name)):
            self.instrument.with_user(self.preparer).write({"name": "Přejmenováno"})
        self.assertTrue(self.as_admin(Instrument).create(vals).company_id == self.manager_company)

    def test_instrument_of_other_fund_is_hidden(self):
        foreign = self.env["investra.instrument"].create({
            "name": "Úvěr B", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_loan").id,
            "fund_id": self.other_fund.id, "identifier_kind": "contract", "identifier": "U-1",
        })
        self.assertEqual(foreign.company_id, self.other_book.company_id)
        Instrument = self.env["investra.instrument"].with_user(self.preparer)
        self.assertFalse(Instrument.search([("id", "=", foreign.id)]))
        with self.assertRaises(AccessError):
            foreign.with_user(self.preparer).read(["name"])

    def test_changes_logged_in_history(self):
        bond = self.env["investra.instrument"].create({
            "name": "Dluhopis", "isin": "CZ0001234567", "currency_id": self.czk.id,
            "type_id": self.env.ref("investra_instruments.type_bond").id, "coupon_rate": 3,
        })
        subtype = self.env.ref("investra_instruments.mt_instrument_change")
        bond = self.as_admin(bond)
        bond.write({"coupon_rate": 4, "name": "Dluhopis 2"})
        flow = self.as_admin(self.env["investra.instrument.cashflow"]).create({
            "instrument_id": bond.id, "date": "2031-01-01", "amount": 100, "flow_type": "principal",
        })
        flow.write({"amount": 101})
        flow.unlink()
        bodies = bond.sudo().message_ids.filtered(lambda m: m.subtype_id == subtype).mapped("body")
        text = " ".join(str(b) for b in bodies)
        for expected in ("Sazba %: 3.0 → 4.0", "Tok přidán: 2031-01-01", "Tok změněn", "→ 2031-01-01 Jistina 101", "Tok smazán"):
            self.assertIn(expected, text)
        self.assertEqual(len(bodies), 4)  # změna názvu se nezapisuje, NAV neovlivní
