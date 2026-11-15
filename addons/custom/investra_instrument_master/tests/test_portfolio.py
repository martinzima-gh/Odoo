from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.investra_instruments.tests.common import with_ids
from odoo.addons.investra_instruments.tests.test_instrument import InstrumentCase


@tagged("post_install", "-at_install")
class TestPortfolioCategory(InstrumentCase):
    """Portfolio určuje oceňovací kategorii; zařazení musí podle IFRS 9 vycházet stejně (úkol IM-06)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Portfolio = cls.env["investra.fund.portfolio"]
        cls.Classification = cls.env["investra.portfolio.classification"]

    def category(self, code):
        return self.env.ref(f"investra_instrument_master.measurement_{code.lower()}")

    def reason(self, code):
        return self.env["investra.classification.reason"].search([("code", "=", code)])

    def make_portfolio(self, category, model, **vals):
        return self.Portfolio.create({
            "fund_id": self.fund.id, "name": f"{category} {model}", "measurement_category_id": self.category(category).id,
            "business_model": model, **vals,
        })

    def make(self, kind, **vals):
        return self.env["investra.instrument"].create(with_ids(self.env, {
            "name": f"{kind} {self.id()[-12:]}", "currency_id": self.czk.id,
            "type_id": self.env.ref(f"investra_instruments.type_{kind}").id, **vals,
        }, self.fund))

    def bond(self, sppi="pass"):
        vals = {"coupon_type": "fixed", "sppi_status": sppi}
        if sppi in ("pass", "fail"):
            vals["sppi_note"] = "Test: pevný kupón a jistina" if sppi == "pass" else "Test: páka v úroku"
        return self.make("bond", **vals)

    def place(self, portfolio, instrument, **vals):
        return self.Classification.create({
            "portfolio_id": portfolio.id, "instrument_id": instrument.id, "valid_from": "2026-11-01", **vals,
        })

    # --- kritéria 1–5: kompatibilita -----------------------------------------------------------------------------

    def test_ac_accepts_sppi_bond(self):
        held = self.place(self.make_portfolio("AC", "hold_to_collect"), self.bond())
        self.assertEqual((held.ifrs9_category, held.valuation_method), ("amortised", "amortised"))

    def test_ac_rejects_bond_without_passed_sppi(self):
        portfolio = self.make_portfolio("AC", "hold_to_collect")
        with self.assertRaisesRegex(ValidationError, "nesplněným testem SPPI"):
            self.place(portfolio, self.bond("fail"))
        with self.assertRaisesRegex(ValidationError, "vyžaduje u nástroje splněný test SPPI.*Neposouzeno"):
            self.place(portfolio, self.bond("not_assessed"))

    def test_ac_rejects_derivative_and_fund_units(self):
        portfolio = self.make_portfolio("AC", "hold_to_collect")
        with self.assertRaisesRegex(ValidationError, "vychází podle IFRS 9 jako FVTPL"):
            self.place(portfolio, self.make("derivative_otc"))
        with self.assertRaisesRegex(ValidationError, "vyžaduje u nástroje splněný test SPPI"):
            self.place(portfolio, self.make("fund"))
        with self.assertRaisesRegex(ValidationError, "nesplněným testem SPPI"):
            self.place(portfolio, self.make("fund", sppi_status="fail", sppi_note="Výnos podle výkonnosti fondu"))

    def test_fvoci_debt_accepts_sppi_bond_only(self):
        portfolio = self.make_portfolio("FVOCI_D", "hold_collect_sell")
        self.assertEqual(self.place(portfolio, self.bond()).ifrs9_category, "fvoci")
        with self.assertRaisesRegex(ValidationError, "vychází podle IFRS 9 jako FVOCI_E"):
            self.place(portfolio, self.make("equity"), designation="fvoci_equity", designation_note="Strategická investice")

    def test_fvoci_equity_needs_election_and_no_model(self):
        with self.assertRaisesRegex(ValidationError, "vyžaduje obchodní model Nepoužije se"):
            self.make_portfolio("FVOCI_E", "trading")
        portfolio = self.make_portfolio("FVOCI_E", "na")
        chosen = self.place(portfolio, self.make("equity"), designation="fvoci_equity", designation_note="Strategická investice")
        self.assertEqual(chosen.ifrs9_category, "fvoci")
        self.assertIn("(c) Obchodní model: Nepoužije se", chosen.classification_basis)
        with self.assertRaisesRegex(ValidationError, "jen kapitálový nástroj s volbou podle IFRS 9 5.7.5"):
            self.place(portfolio, self.make("equity"))
        with self.assertRaisesRegex(ValidationError, "jen kapitálový nástroj s volbou podle IFRS 9 5.7.5"):
            self.place(portfolio, self.bond())
        with self.assertRaisesRegex(ValidationError, "vyžaduje obchodní model"):
            portfolio.write({"business_model": "trading"})

    def test_category_requires_model(self):
        with self.assertRaisesRegex(ValidationError, "vyžaduje obchodní model Držet pro inkaso"):
            self.make_portfolio("AC", "fair_value")
        with self.assertRaisesRegex(ValidationError, "vyžaduje obchodní model Držet pro inkaso i prodej"):
            self.make_portfolio("FVOCI_D", "hold_to_collect")
        for model in ("hold_to_collect", "fair_value", "trading"):
            self.make_portfolio("FVTPL", model, name=f"FVTPL {model}")

    def test_category_change_revalidates_classifications(self):
        portfolio = self.Portfolio.create({"fund_id": self.fund.id, "name": "Bez kategorie", "business_model": "hold_to_collect"})
        self.place(portfolio, self.make("derivative_otc"))
        with self.assertRaisesRegex(ValidationError, "vychází podle IFRS 9 jako FVTPL"):
            portfolio.write({"measurement_category_id": self.category("AC").id})
        portfolio.write({"measurement_category_id": self.category("FVTPL").id})
        with self.assertRaisesRegex(ValidationError, "vychází podle IFRS 9 jako FVTPL"):
            portfolio.write({"measurement_category_id": self.category("FVOCI_D").id, "business_model": "hold_collect_sell"})

    def test_instrument_sppi_change_revalidates(self):
        bond = self.bond()
        self.place(self.make_portfolio("FVOCI_D", "hold_collect_sell"), bond)
        with self.assertRaisesRegex(ValidationError, "nesplněným testem SPPI"):
            bond.write({"sppi_status": "fail", "sppi_note": "Páka v úroku"})

    def test_portfolio_without_category_behaves_as_before(self):
        portfolio = self.Portfolio.create({"fund_id": self.fund.id, "name": "Dosavadní", "business_model": "fair_value"})
        self.assertEqual(self.place(portfolio, self.bond("not_assessed")).ifrs9_category, "fvtpl")
        self.assertEqual(portfolio.state, "draft")

    # --- kritérium 6 a 8: schválení a důvod --------------------------------------------------------------------------

    def test_fvtpl_accepts_derivative_and_approval_needs_reason(self):
        portfolio = self.make_portfolio("FVTPL", "trading", code="DER", assessment="Deriváty k obchodování", valid_from="2026-11-01")
        self.assertEqual(self.place(portfolio, self.make("derivative_otc")).ifrs9_category, "fvtpl")
        with self.assertRaisesRegex(UserError, "Před schválením doplňte: Důvod klasifikace"):
            portfolio.with_user(self.approver).action_approve()
        portfolio.classification_reason_id = self.reason("MANDATORY_FVTPL")
        with self.assertRaisesRegex(UserError, "jen schvalovatel"):
            portfolio.with_user(self.preparer).action_approve()
        portfolio.with_user(self.approver).action_approve()
        self.assertEqual((portfolio.state, portfolio.approved_by), ("approved", self.approver))
        self.assertTrue(portfolio.approved_on)
        portfolio.with_user(self.approver).action_close()
        self.assertEqual(portfolio.state, "closed")
        self.assertTrue(portfolio.valid_to)

    def test_state_only_by_buttons(self):
        portfolio = self.make_portfolio("FVTPL", "fair_value")
        with self.assertRaisesRegex(UserError, "mění jen tlačítka"):
            portfolio.with_user(self.preparer).write({"state": "approved"})
        with self.assertRaisesRegex(UserError, "mění jen tlačítka"):
            self.Portfolio.with_user(self.preparer).create({"fund_id": self.fund.id, "name": "Import", "state": "approved"})

    def test_code_unique_in_fund(self):
        self.make_portfolio("FVTPL", "fair_value", code="P1")
        with self.assertRaises(Exception), mute_logger("odoo.sql_db"), self.cr.savepoint():
            self.make_portfolio("FVTPL", "trading", code="P1")
        self.make_portfolio("FVTPL", "trading", name="Bez kódu")
        self.make_portfolio("FVTPL", "hold_to_collect", name="Bez kódu 2")

    def test_reason_help_under_field(self):
        portfolio = self.make_portfolio("FVTPL", "fair_value", classification_reason_id=self.reason("MANDATORY_FVTPL").id)
        self.assertEqual(portfolio.reason_help, self.reason("MANDATORY_FVTPL").help_text)
        self.assertIn("Reálná hodnota do výsledku je povinná", portfolio.reason_help)
        arch = self.Portfolio.get_view(self.env.ref("investra_instruments.view_portfolio_form").id)["arch"]
        for name in ("measurement_category_id", "classification_reason_id", "reason_help", "state", "classification_ids",
                     "business_model", "assessment"):
            self.assertIn(f'name="{name}"', arch)

    # --- kritérium 7: zámek po prvním obchodu --------------------------------------------------------------------------

    def test_locked_after_first_trade(self):
        portfolio = self.make_portfolio("FVTPL", "fair_value", classification_reason_id=self.reason("BUSINESS_MODEL").id)
        self.assertFalse(portfolio.is_locked)
        equity = self.make("equity")
        self.place(portfolio, equity)
        self.env["investra.trade"].create({
            "fund_id": self.fund.id, "portfolio_id": portfolio.id, "instrument_id": equity.id, "trade_date": "2026-11-03",
            "quantity": 1, "price": 100,
        })
        portfolio.invalidate_recordset(["is_locked", "lock_date"])
        self.assertTrue(portfolio.is_locked)
        self.assertEqual(str(portfolio.lock_date), "2026-11-03")
        other_book = self.env["investra.entity"].sudo().create_book("Fond 2", "fund", "cas501", self.czk, "investra_fund")
        other = self.env["investra.fund"].sudo().create({"entity_id": other_book.id})
        as_preparer = portfolio.with_user(self.preparer)
        for vals in (
            {"measurement_category_id": self.category("AC").id}, {"business_model": "trading"},
            {"classification_reason_id": self.reason("OTHER").id}, {"fund_id": other.id},
        ):
            with self.assertRaisesRegex(UserError, "Po prvním obchodu nejde změnit kategorii"):
                as_preparer.write(vals)
        as_preparer.write({"measurement_category_id": self.category("FVTPL").id, "name": "Přejmenované",
                           "strategy_description": "Změna popisu projde"})
        self.assertEqual(portfolio.measurement_category_id, self.category("FVTPL"))
