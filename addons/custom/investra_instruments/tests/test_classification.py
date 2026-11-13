from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .test_instrument import InstrumentCase


@tagged("post_install", "-at_install")
class TestClassification(InstrumentCase):
    """Klasifikace podle obchodního modelu fondu (plán docs/navrh-klasifikace-ifrs9.md, rozhodnutí 2026-11-11)."""

    def bond(self):
        return self.env["investra.instrument"].create({
            "name": "Dluhopis", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_bond").id,
        })

    def trade(self, instrument, quantity, day="2026-11-02", portfolio=None, fund=None):
        fund = fund or self.fund
        vals = {"fund_id": fund.id, "instrument_id": instrument.id, "trade_date": day, "quantity": quantity, "price": 100}
        if portfolio:
            vals["portfolio_id"] = portfolio.id
        return self.env["investra.trade"].create(vals)

    def test_new_fund_has_main_portfolio(self):
        self.assertEqual(self.fund.portfolio_ids.mapped("name"), ["Hlavní"])
        self.assertEqual(self.fund.portfolio_ids.business_model, "fair_value")
        self.assertEqual(self.trade(self.instrument, 1).portfolio_id, self.fund.portfolio_ids)

    def test_two_portfolios_need_choice(self):
        self.portfolio(self.fund, "hold_to_collect")
        with self.assertRaises(UserError):
            self.trade(self.instrument, 1)

    def test_trade_without_classification_is_not_booked(self):
        trade = self.trade(self.bond(), 1)
        self.assertFalse(trade.classification_id)
        with self.assertRaises(UserError):
            trade._book()
        self.assertEqual(trade.state, "draft")

    def test_same_instrument_in_two_portfolios(self):
        bond = self.bond()
        main = self.fund.portfolio_ids
        held = self.portfolio(self.fund, "hold_to_collect")
        fair = self.classify(self.fund, bond)
        amortised = self.classify(self.fund, bond, "hold_to_collect")
        first = self.trade(bond, 10, portfolio=main)
        second = self.trade(bond, 4, portfolio=held)
        self.assertEqual((first.classification_id, second.classification_id), (fair, amortised))
        self.assertEqual((first.ifrs9_category, second.ifrs9_category), ("fvtpl", "amortised"))
        # V pozici jen obchody s dokladem (rozhodnutí 2026-11-13 „Návrhy obchodů v pozicích“).
        (first | second)._book()
        Trade = self.env["investra.trade"]
        self.assertEqual(Trade._holdings(self.fund, date(2026, 11, 30)), {(bond, main): 10, (bond, held): 4})
        self.assertEqual(Trade._positions(self.fund, date(2026, 11, 30)), {bond: 14})

    def test_sale_is_limited_to_portfolio(self):
        bond = self.bond()
        main = self.fund.portfolio_ids
        held = self.portfolio(self.fund, "hold_to_collect")
        self.classify(self.fund, bond)
        self.classify(self.fund, bond, "hold_to_collect")
        self.trade(bond, 10, portfolio=main)._book()
        self.trade(bond, 4, portfolio=held)._book()
        with self.assertRaises(UserError):
            self.trade(bond, -5, day="2026-11-10", portfolio=held)._book()
        self.trade(bond, -4, day="2026-11-10", portfolio=held)._book()
        holdings = self.env["investra.trade"]._holdings(self.fund, date(2026, 11, 30))
        self.assertEqual(holdings, {(bond, main): 10})

    def test_two_funds_classify_independently(self):
        other_book = self.env["investra.entity"].sudo().create_book("Fond 2", "fund", "cas501", self.czk, "investra_fund")
        env = self.env(context=dict(self.env.context, allowed_company_ids=[self.company.id, other_book.company_id.id]))
        other = env["investra.fund"].create({"entity_id": other_book.id})
        bond = self.bond()
        first = self.classify(self.fund, bond)
        self.trade(bond, 1)._book()
        second = env["investra.portfolio.classification"].create({
            "portfolio_id": env["investra.fund.portfolio"].create({
                "fund_id": other.id, "name": "Inkaso", "business_model": "hold_to_collect",
            }).id,
            "instrument_id": bond.id, "valid_from": "2000-01-01", "sppi": "pass", "sppi_note": "Pevná sazba",
        })
        self.assertEqual((first.ifrs9_category, second.ifrs9_category), ("fvtpl", "amortised"))

    def test_reserved_instrument_only_in_own_fund(self):
        other_book = self.env["investra.entity"].sudo().create_book("Fond 3", "fund", "cas501", self.czk, "investra_fund")
        env = self.env(su=True)
        other = env["investra.fund"].create({"entity_id": other_book.id})
        holding = self.env["investra.instrument"].create({
            "name": "Podíl", "currency_id": self.czk.id, "type_id": self.env.ref("investra_instruments.type_other_holding").id,
            "fund_id": self.fund.id, "holding_kind": "shares",
        })
        with self.assertRaises(ValidationError):
            env["investra.portfolio.classification"].create({
                "portfolio_id": other.portfolio_ids.id, "instrument_id": holding.id, "valid_from": "2000-01-01",
            })

    def test_portfolio_must_belong_to_fund(self):
        other_book = self.env["investra.entity"].sudo().create_book("Fond 4", "fund", "cas501", self.czk, "investra_fund")
        other = self.env(su=True)["investra.fund"].create({"entity_id": other_book.id})
        with self.assertRaises(ValidationError):
            self.env(su=True)["investra.trade"].create({
                "fund_id": self.fund.id, "portfolio_id": other.portfolio_ids.id, "instrument_id": self.instrument.id,
                "trade_date": "2026-11-02", "quantity": 1, "price": 1,
            })


@tagged("post_install", "-at_install")
class TestClassificationRules(InstrumentCase):
    """Jen kombinace přípustné podle IFRS 9 (dodatek plánu 2026-11-11; body 1–5 ověřil uživatel vůči IFRS přijatým EU)."""

    def make(self, code, **vals):
        return self.env["investra.instrument"].create({
            "name": f"{code} {self.id()[-12:]}", "currency_id": self.czk.id,
            "type_id": self.env.ref(f"investra_instruments.type_{code}").id, **vals,
        })

    def test_debt_with_sppi_follows_business_model(self):
        """Mezera 1: dluh se splněným SPPI je povinně v naběhlé hodnotě / FVOCI, kategorie se nezadává."""
        held = self.classify(self.fund, self.make("bond"), "hold_to_collect")
        self.assertEqual((held.mandatory_category, held.ifrs9_category), ("amortised", "amortised"))
        self.assertEqual(self.classify(self.fund, self.make("bond"), "hold_collect_sell").ifrs9_category, "fvoci")
        self.assertEqual(self.classify(self.fund, self.make("bond"), "hold_to_collect", sppi="fail").ifrs9_category, "fvtpl")
        self.assertEqual(self.classify(self.fund, self.make("bond"), "fair_value").ifrs9_category, "fvtpl")
        with self.assertRaises(UserError):
            self.classify(self.fund, self.make("bond"), "hold_to_collect", ifrs9_category="fvtpl")
        with self.assertRaises(UserError):
            held.with_user(self.preparer).write({"ifrs9_category": "fvtpl"})
        with self.assertRaises(ValidationError):  # v modelu Držet pro inkaso musí být SPPI vyhodnocené
            self.classify(self.fund, self.make("bond"), "hold_to_collect", sppi="na")
        with self.assertRaises(ValidationError):  # vyhodnocené SPPI potřebuje odůvodnění
            self.classify(self.fund, self.make("bond"), "hold_to_collect", sppi_note=False)

    def test_fund_units_are_puttable_without_election(self):
        """Mezera 2: podílový list není kapitálový nástroj pro volbu 5.7.5."""
        units = self.classify(self.fund, self.make("fund"))
        self.assertEqual((units.instrument_nature, units.ifrs9_category), ("puttable", "fvtpl"))
        with self.assertRaises(ValidationError):
            self.classify(self.fund, self.make("fund"), designation="fvoci_equity", designation_note="Strategická")
        with self.assertRaises(ValidationError):  # jiná povaha než podle druhu jen s posouzením
            self.classify(self.fund, self.make("fund"), instrument_nature="equity")
        assessed = self.classify(
            self.fund, self.make("fund"), instrument_nature="equity", nature_note="Uzavřený fond, IAS 32.11 bez 16A–16D",
            designation="fvoci_equity", designation_note="Strategická investice",
        )
        self.assertEqual(assessed.ifrs9_category, "fvoci")

    def test_no_election_when_held_for_trading(self):
        """Mezera 3: volba 5.7.5 není u nástroje drženého k obchodování."""
        with self.assertRaises(ValidationError):
            self.classify(self.fund, self.make("equity"), "trading", designation="fvoci_equity", designation_note="Strategická")
        chosen = self.classify(self.fund, self.make("equity"), designation="fvoci_equity", designation_note="Strategická investice")
        self.assertEqual((chosen.mandatory_category, chosen.ifrs9_category), ("fvtpl", "fvoci"))

    def test_fvo_only_when_it_changes_category(self):
        """Mezera 4: určení 4.1.5 jen u nástroje, který by byl v naběhlé hodnotě nebo FVOCI."""
        designated = self.classify(self.fund, self.make("bond"), "hold_to_collect", designation="fvo", designation_note="Účetní nesoulad se závazkem")
        self.assertEqual((designated.mandatory_category, designated.ifrs9_category), ("amortised", "fvtpl"))
        with self.assertRaises(ValidationError):
            self.classify(self.fund, self.make("bond"), "hold_to_collect", sppi="fail", designation="fvo", designation_note="x")
        with self.assertRaises(ValidationError):
            self.classify(self.fund, self.make("bond"), designation="fvo", designation_note="x")
        with self.assertRaises(ValidationError):
            self.classify(self.fund, self.make("equity"), designation="fvo", designation_note="x")
        with self.assertRaises(ValidationError):  # určení bez odůvodnění
            self.classify(self.fund, self.make("bond"), "hold_to_collect", designation="fvo")

    def test_sppi_only_for_debt_and_units(self):
        with self.assertRaises(ValidationError):
            self.classify(self.fund, self.make("equity"), sppi="pass", sppi_note="x")
        with self.assertRaises(ValidationError):
            self.classify(self.fund, self.make("derivative_otc"), sppi="fail", sppi_note="x")

    def test_participation_only_fvtpl(self):
        """Mezera 6: účast fondu je ve FVTPL (IFRS 10.31, IAS 28.18), volba FVOCI není."""
        participation = self.classify(self.fund, self.make("participation"))
        self.assertEqual(participation.ifrs9_category, "fvtpl")
        self.assertIn("IFRS 10.31", participation.classification_basis)
        with self.assertRaises(ValidationError):
            self.classify(self.fund, self.make("participation"), designation="fvoci_equity", designation_note="x")

    def test_sppi_version_follows_period(self):
        """Pro období od 1. 1. 2026 se SPPI posuzuje podle IFRS 9 ve znění nařízení (EU) 2025/1047."""
        current = self.classify(self.fund, self.make("bond"), "hold_to_collect", day="2027-03-01")
        self.assertEqual(current.sppi_version, "eu_2025_1047")
        with self.assertRaises(ValidationError):
            self.classify(self.fund, self.make("bond"), "hold_to_collect", day="2027-03-01", sppi_version="pre_2025_1047")
        older = self.classify(self.fund, self.make("bond"), "hold_to_collect", day="2025-06-30")
        self.assertEqual(older.sppi_version, "pre_2025_1047")

    def test_basis_documents_each_step(self):
        """Zdůvodnění (f) doloží povahu, SPPI, model, povinnou klasifikaci, určení a výsledek."""
        record = self.classify(self.fund, self.make("bond"), "hold_to_collect", day="2027-03-01", sppi_note="Pevná sazba 4 %")
        basis = record.classification_basis
        for part in ("(a) Povaha: Dluhový nástroj", "(b) Test SPPI: Splněn", "IFRS 9 ve znění nařízení (EU) 2025/1047",
                     "Pevná sazba 4 %", "(c) Obchodní model: Držet pro inkaso", "(d) Povinná klasifikace: Naběhlá hodnota – IFRS 9 4.1.2",
                     "(e) Určení / volba: žádné", "(f) Kategorie IFRS 9: Naběhlá hodnota"):
            self.assertIn(part, basis)

    def test_manual_override_needs_reason_and_is_documented(self):
        """Ruční přepsání kategorie (rozhodnutí uživatele 2026-11-11): jen se zdůvodněním, označené jako odchylka."""
        bond = self.make("bond")
        with self.assertRaises(ValidationError):
            self.classify(self.fund, bond, category_override="fvoci")
        with self.assertRaises(ValidationError):  # shodná s vypočtenou nemá smysl
            self.classify(self.fund, bond, category_override="fvtpl", override_note="x")
        record = self.classify(self.fund, bond, category_override="fvoci", override_note="Metodik: strategická držba do splatnosti")
        self.assertEqual((record.computed_category, record.ifrs9_category), ("fvtpl", "fvoci"))
        self.assertIn("RUČNÍ PŘEPSÁNÍ", record.classification_basis)
        self.assertIn("vypočtená: Reálná hodnota do výsledku", record.classification_basis)
        self.assertIn("Metodik: strategická držba do splatnosti", record.classification_basis)
        deposit = self.make("deposit")
        amortised = self.classify(self.fund, deposit, category_override="amortised", override_note="Krátký vklad u banky")
        self.assertEqual(amortised.valuation_method, "amortised")
        self.trade_in(bond)
        with self.assertRaises(UserError):
            record.with_user(self.preparer).write({"category_override": False})

    def trade_in(self, instrument):
        return self.env["investra.trade"].create({
            "fund_id": self.fund.id, "instrument_id": instrument.id, "trade_date": "2026-11-02", "quantity": 1, "price": 1,
        })
