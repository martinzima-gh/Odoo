from odoo.fields import Command
from odoo.tests import tagged

from .common import NavCase


class TrackingMixin:
    """Pomocné funkce: změnu oddělit od vytvoření a číst jen zprávy vzniklé po bodu `mark`."""

    def flush_tracking(self):
        self.env.flush_all()
        if hasattr(self.env.cr, "precommit"):
            self.env.cr.precommit.run()

    def mark(self, record):
        self.flush_tracking()
        return set(record.message_ids.ids)

    def new_bodies(self, record, mark):
        self.flush_tracking()
        return [m.body or "" for m in record.message_ids.filtered(lambda m: m.id not in mark)]

    def new_text(self, record, mark):
        return "\n".join(self.new_bodies(record, mark))


@tagged("post_install", "-at_install")
class TestTrackingFees(TrackingMixin, NavCase):
    """ZJ-10 fáze 2: pravidlo úplaty, verze, pásma, benchmark (chatter pravidla a benchmarku)."""

    def setUp(self):
        super().setUp()
        self.fund = self.make_fund(classes=[{"code": "A"}, {"code": "B"}])
        self.rule = self.env["investra.fee.rule"].create({
            "fund_id": self.fund.id, "name": "Úplata", "kind": "periodic", "base_source": "fk",
            "version_ids": [(0, 0, {"valid_from": "2020-01-01", "rate": 0.01})],
        })
        self.version = self.rule.version_ids

    def test_rule_header_selection(self):
        mark = self.mark(self.rule)
        self.rule.write({"base_mode": "after"})
        text = self.new_text(self.rule, mark)
        self.assertIn("Před úplatami", text)
        self.assertIn("Po všech úplatách", text)
        self.assertIn("(Základ před/po úplatách)", text)

    def test_rule_many2many(self):
        mark = self.mark(self.rule)
        self.rule.write({"class_ids": [Command.set(self.cls(self.fund, "A").ids)]})
        self.assertIn("(Platí třídy)", self.new_text(self.rule, mark))

    def test_rule_more_fields_one_message(self):
        mark = self.mark(self.rule)
        self.rule.write({"base_mode": "after", "expense_role": "expense_management"})
        bodies = self.new_bodies(self.rule, mark)
        self.assertEqual(len(bodies), 1)
        self.assertIn("(Základ před/po úplatách)", bodies[0])
        self.assertIn("(Nákladová role)", bodies[0])

    def test_version_and_tier_go_to_rule_chatter(self):
        mark = self.mark(self.rule)
        self.version.write({"rate": 0.02})
        text = self.new_text(self.rule, mark)
        self.assertIn("Verze platná od 2020-01-01 – Sazba p. a.: 0.01 → 0.02", text)
        self.assertFalse(self.version.message_ids if hasattr(self.version, "message_ids") else False)

        mark = self.mark(self.rule)
        tier = self.env["investra.fee.tier"].create({"version_id": self.version.id, "amount_from": 1000, "rate": 0.01})
        text = self.new_text(self.rule, mark)
        self.assertIn("Přidáno", text)
        self.assertIn("Pásmo (verze od 2020-01-01)", text)
        self.assertIn("Od částky: 1000", text)

        mark = self.mark(self.rule)
        tier.write({"rate": 0.02})
        self.assertIn("Pásmo (verze od 2020-01-01) – Sazba: 0.01 → 0.02", self.new_text(self.rule, mark))

        mark = self.mark(self.rule)
        tier.unlink()
        text = self.new_text(self.rule, mark)
        self.assertIn("Odebráno", text)
        self.assertIn("Pásmo (verze od 2020-01-01)", text)

    def test_new_version_and_removal(self):
        mark = self.mark(self.rule)
        version = self.env["investra.fee.version"].create({"rule_id": self.rule.id, "valid_from": "2021-01-01", "rate": 0.03})
        text = self.new_text(self.rule, mark)
        self.assertIn("Přidáno: Verze platná od 2021-01-01", text)
        self.assertIn("Sazba p. a.: 0.03", text)
        mark = self.mark(self.rule)
        version.unlink()
        self.assertIn("Odebráno: Verze platná od 2021-01-01", self.new_text(self.rule, mark))

    def test_tracking_disable_silences_everything(self):
        mark = self.mark(self.rule)
        quiet = self.env["investra.fee.rule"].with_context(tracking_disable=True)
        self.rule.with_context(tracking_disable=True).write({"base_mode": "after"})
        self.version.with_context(tracking_disable=True).write({"rate": 0.05})
        self.env["investra.fee.tier"].with_context(tracking_disable=True).create(
            {"version_id": self.version.id, "amount_from": 1, "rate": 0.01})
        quiet.create({"fund_id": self.fund.id, "name": "Tichá", "kind": "periodic"})
        self.assertEqual(self.new_bodies(self.rule, mark), [])

    def test_benchmark(self):
        bench = self.env["investra.benchmark"].create({"name": "Index A"})
        mark = self.mark(bench)
        bench.write({"name": "Index B"})
        text = self.new_text(bench, mark)
        self.assertIn("Index A", text)
        self.assertIn("Index B", text)
        self.assertIn("(Název)", text)

        mark = self.mark(bench)
        value = self.env["investra.benchmark.value"].create({"benchmark_id": bench.id, "date": "2026-01-01", "value": 100})
        text = self.new_text(bench, mark)
        self.assertIn("Přidáno: Hodnota benchmarku", text)
        mark = self.mark(bench)
        value.write({"value": 101})
        self.assertIn("Hodnota benchmarku – Hodnota: 100 → 101", self.new_text(bench, mark))
        mark = self.mark(bench)
        value.unlink()
        self.assertIn("Odebráno: Hodnota benchmarku", self.new_text(bench, mark))

    def test_single_chatter_in_forms(self):
        for xmlid, model in (("investra_nav.view_fee_rule_form", "investra.fee.rule"),
                             ("investra_nav.view_benchmark_form", "investra.benchmark")):
            arch = self.env[model].get_view(view_id=self.env.ref(xmlid).id)["arch"]
            self.assertEqual(arch.count("<chatter"), 1, xmlid)
