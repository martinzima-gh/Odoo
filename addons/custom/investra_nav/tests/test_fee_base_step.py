"""ZJ-12 krok 2: volba „Základ: po kroku 1–4“ (`base_step`), kontroly na pravidle, nová pole řádku opravy a převod
starého nastavení v pre-migraci (rozhodnutí 2026-11-18 „Základ úplat, odměny a daně“)."""

import importlib.util
from datetime import date
from pathlib import Path

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import NavCase

YEAR_END = date(2027, 12, 31)
MIGRATION = Path(__file__).resolve().parent.parent / "migrations" / "20.0.0.37.0" / "pre-migration.py"


def _migration():
    spec = importlib.util.spec_from_file_location("investra_nav_zj12_pre_migration", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@tagged("post_install", "-at_install")
class TestFeeBaseStep(NavCase):
    def setUp(self):
        super().setUp()
        self.Rule = self.env["investra.fee.rule"]
        self.fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        self.a, self.b = self.cls(self.fund, "A"), self.cls(self.fund, "B")

    def rule(self, kind="periodic", fund=None, **vals):
        version = {"valid_from": "2020-01-01", "rate": 0.01}
        if kind == "performance":
            version.update(rate=0.2, initial_reference=0)
            vals.setdefault("class_ids", [(6, 0, self.a.ids)])
            vals.setdefault("expense_role", "expense_performance")
        return self.Rule.create({
            "fund_id": (fund or self.fund).id, "name": vals.pop("name", kind), "kind": kind,
            "version_ids": [(0, 0, version)], **vals,
        })

    # --- volba základu -----------------------------------------------------------------------------------------

    def test_default_step_by_kind(self):
        # Výchozí podle tabulky ZJ-12: úplata 1, odměna 2, daň 3; aktiva a bez základu jen 1.
        self.assertEqual(self.rule("periodic").base_step, "1")
        self.assertEqual(self.rule("periodic", base_source="assets", name="Aktiva").base_step, "1")
        self.assertEqual(self.rule("performance").base_step, "2")
        self.assertEqual(self.rule("tax").base_step, "3")

    def test_admissible_steps(self):
        allowed = {
            ("periodic", "fk"): "1234", ("periodic", "class_fk"): "1234", ("periodic", "average_fk"): "1234",
            ("periodic", "assets"): "1", ("periodic", "none"): "1",
            ("performance", "fk"): "124", ("tax", "fk"): "123",
        }
        for (kind, source), steps in allowed.items():
            for step in "1234":
                with self.subTest(kind=kind, source=source, step=step), self.cr.savepoint():
                    fund = self.make_fund(classes=[{"code": "A"}])
                    vals = {"base_source": source, "base_step": step}
                    if kind == "performance":
                        vals["class_ids"] = [(6, 0, self.cls(fund, "A").ids)]
                    if step in steps:
                        self.assertEqual(self.rule(kind, fund=fund, **vals).base_step, step)
                    else:
                        with self.assertRaises(ValidationError):
                            self.rule(kind, fund=fund, **vals)

    def test_change_of_kind_or_source_resets_inadmissible_step(self):
        rule = self.rule("periodic", base_step="3")
        rule.write({"kind": "performance", "class_ids": [(6, 0, self.a.ids)]})
        self.assertEqual(rule.base_step, "2")  # 3 odměna nepřipouští → výchozí odměny
        rule.write({"kind": "periodic", "base_step": "4"})
        self.assertEqual(rule.base_step, "4")
        rule.base_source = "assets"
        self.assertEqual(rule.base_step, "1")
        # Přípustná volba se při změně druhu zachová.
        other = self.rule("periodic", base_step="2", name="Druhá")
        other.kind = "tax"
        self.assertEqual(other.base_step, "2")
        # Výslovně zadaná nepřípustná volba spolu se změnou druhu se odmítne.
        with self.assertRaises(ValidationError), self.cr.savepoint():
            other.write({"kind": "performance", "class_ids": [(6, 0, self.b.ids)], "base_step": "3"})

    # --- kontroly na pravidle ------------------------------------------------------------------------------------

    def test_one_active_performance_per_class(self):
        self.rule("performance", name="Odměna A")
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.rule("performance", name="Druhá odměna A", class_ids=[(6, 0, (self.a | self.b).ids)])
        on_b = self.rule("performance", name="Odměna B", class_ids=[(6, 0, self.b.ids)])
        with self.assertRaises(ValidationError), self.cr.savepoint():
            on_b.class_ids = self.a | self.b
        # Neaktivní pravidlo se nepočítá; opětovná aktivace se odmítne.
        spare = self.rule("performance", name="Záložní A", class_ids=[(6, 0, self.b.ids)], active=False)
        spare.class_ids = self.a
        with self.assertRaises(ValidationError), self.cr.savepoint():
            spare.active = True

    def test_one_active_tax_per_fund(self):
        self.rule("tax", name="Daň")
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.rule("tax", name="Druhá daň")
        other_fund = self.make_fund(classes=[{"code": "A"}])
        self.rule("tax", fund=other_fund, name="Daň jiného fondu")
        self.rule("tax", name="Neaktivní daň", active=False)

    def test_rules_without_classes(self):
        # Pravidla bez tříd (úplaty celého fondu, daň) kontrolu odměn na třídu nespouštějí a smějí být vedle odměny.
        whole = self.rule("periodic", name="Obhospodařování")
        self.rule("periodic", name="Administrace")
        tax = self.rule("tax", name="Daň")
        self.rule("performance", name="Odměna A")
        self.assertFalse(whole.class_ids | tax.class_ids)
        # Oprava pravidla bez tříd (daň) nesmí mít třídu; oprava odměny musí mít třídu, která odměnu platí.
        valuation = self.valuation(self.fund, YEAR_END)
        values = {"note": "Daňový poradce", "account_id": False}
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.manual_fee(valuation, -1, corrects_rule_id=tax.id, class_id=self.a.id, **values)
        entry = self.manual_fee(valuation, -1, corrects_rule_id=tax.id, validity="valuation", **values)
        self.assertEqual((entry.class_id.id, entry.validity), (False, "valuation"))

    def test_correction_fields_only_on_correction(self):
        valuation = self.valuation(self.fund, YEAR_END)
        for vals in ({"correction_target": "base"}, {"validity": "valuation"}):
            with self.subTest(vals=vals), self.assertRaises(ValidationError), self.cr.savepoint():
                self.manual_fee(valuation, 100, **vals)
        entry = self.manual_fee(valuation, 100)
        self.assertEqual((entry.correction_target, entry.validity, entry.computed_at_entry, entry.origin_id.id),
                         ("amount", "period", 0.0, False))

    # --- pre-migrace ---------------------------------------------------------------------------------------------

    def test_pre_migration_mapping(self):
        step = _migration().base_step_for
        cases = {
            ("tax", "fk", "before", "after_fees"): "3",
            ("tax", "none", "after", "before_fees"): "3",
            ("performance", "fk", "before", "before_fees"): "1",
            ("performance", "fk", "after", "after_fees"): "2",
            ("performance", "fk", "before", "after_tax"): "4",
            ("periodic", "fk", "before", "after_fees"): "1",
            ("periodic", "class_fk", "after", "after_fees"): "2",
            ("periodic", "average_fk", "after", "after_fees"): "1",
            ("periodic", "assets", "after", "after_fees"): "1",
            ("periodic", "none", "after", "after_fees"): "1",
            ("performance", "fk", "before", "neznámá"): None,
        }
        for args, expected in cases.items():
            with self.subTest(args=args):
                self.assertEqual(step(*args), expected)

    def test_pre_migration_skips_when_column_exists(self):
        # Na nainstalované databázi sloupec base_step už je: migrace nic nemění.
        self.cr.execute("SELECT id, base_step FROM investra_fee_rule ORDER BY id")
        before = self.cr.fetchall()
        _migration().migrate(self.cr, "20.0.0.36.0")
        self.cr.execute("SELECT id, base_step FROM investra_fee_rule ORDER BY id")
        self.assertEqual(self.cr.fetchall(), before)
