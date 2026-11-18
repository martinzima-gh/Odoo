from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAllocationTracking(TransactionCase):
    """ZJ-10 fáze 2: změny alokačního schématu a jeho řádků v chatteru schématu."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        czk = cls.env.ref("base.CZK")
        czk.active = True
        book = cls.env["investra.entity"].create_book("Fond Alokace", "fund", "cas501", czk, "cz")
        cls.fund = cls.env["investra.fund"].create({"entity_id": book.id})
        cls.klass = cls.env["investra.fund.class"].create(
            {"fund_id": cls.fund.id, "code": "A", "name": "Třída A", "currency_id": czk.id})
        cls.scheme = cls.env["investra.allocation.scheme"].create({"fund_id": cls.fund.id, "valid_from": "2026-01-01"})

    def flush_tracking(self):
        self.env.flush_all()
        self.env.cr.precommit.run()

    def mark(self):
        self.flush_tracking()
        return set(self.scheme.message_ids.ids)

    def text(self, mark):
        self.flush_tracking()
        return "\n".join(m.body or "" for m in self.scheme.message_ids.filtered(lambda m: m.id not in mark))

    def test_scheme_method(self):
        mark = self.mark()
        self.scheme.write({"method": "waterfall"})
        text = self.text(mark)
        self.assertIn("Alokační poměr", text)
        self.assertIn("Pořadí nároků", text)
        self.assertIn("(Metoda rozdělení)", text)

    def test_line_add_change_remove(self):
        mark = self.mark()
        line = self.env["investra.allocation.line"].create(
            {"scheme_id": self.scheme.id, "class_id": self.klass.id, "target_rate": 0.04})
        text = self.text(mark)
        self.assertIn("Přidáno: Nárok třídy", text)
        self.assertIn("Cílový výnos p. a.: 0.04", text)

        mark = self.mark()
        line.write({"target_rate": 0.05})
        self.assertIn("Nárok třídy", self.text(mark))
        mark = self.mark()
        line.write({"target_rate": 0.06})
        self.assertIn("Cílový výnos p. a.: 0.05 → 0.06", self.text(mark))

        mark = self.mark()
        line.unlink()
        self.assertIn("Odebráno: Nárok třídy", self.text(mark))

    def test_tracking_disable(self):
        mark = self.mark()
        self.scheme.with_context(tracking_disable=True).write({"method": "waterfall"})
        self.env["investra.allocation.line"].with_context(tracking_disable=True).create(
            {"scheme_id": self.scheme.id, "class_id": self.klass.id})
        self.assertEqual(self.text(mark), "")

    def test_single_chatter_in_form(self):
        arch = self.env["investra.allocation.scheme"].get_view(view_id=self.env.ref("investra_allocation.view_scheme_form").id)["arch"]
        self.assertEqual(arch.count("<chatter"), 1)
