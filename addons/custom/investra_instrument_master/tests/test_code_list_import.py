import base64
from datetime import date

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

ESA_HEAD = "domena;nazev_domeny_nebo_hierarchie;kod;hodnota\n"


@tagged("post_install", "-at_install")
class TestCodelistImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = cls.env["res.users"].create({"name": "Správce importu", "login": "imp_manager", "group_ids": [
            (6, 0, [cls.env.ref("investra_instrument_master.group_codelist_manager").id])]})
        cls.reader = cls.env["res.users"].create({"name": "Čtenář importu", "login": "imp_reader", "group_ids": [
            (6, 0, [cls.env.ref("account.group_account_readonly").id])]})
        cls.Esa = cls.env["investra.esa.code"]
        cls.Ba = cls.env["investra.ba0088.code"]

    def wizard(self, text, target="esa", user=None, **vals):
        data = dict(target=target, file=base64.b64encode(text.encode()).decode(), methodology="TEST v1",
                    valid_from=date(2027, 1, 1), domain_code="D_S_RNBD_4" if target == "esa" else "BA0088")
        data.update(vals)
        return self.env["investra.codelist.import.wizard"].with_user(user or self.manager).create(data)

    def esa_file(self, extra="", rename=None):
        """Současný číselník ESA ze seedu (beze změny), případně s přejmenovaným kódem a řádky navíc."""
        rows = []
        for rec in self.Esa.search([]):
            name = rename.get(rec.code, rec.name) if rename else rec.name
            rows.append(f"D_S_RNBD_4;Rezidenti;{rec.code};{name}\n")
        return ESA_HEAD + "".join(rows) + extra

    def lines(self, wiz):
        return {line.code: line for line in wiz.line_ids}

    def test_same_file_changes_nothing(self):
        wiz = self.wizard(self.esa_file())
        wiz.action_preview()
        self.assertEqual({line.state for line in wiz.line_ids}, {"same"})
        wiz.action_apply()
        self.assertEqual(self.Esa.search_count([]), 80)

    def test_new_renamed_and_second_import_idempotent(self):
        sector = self.env["investra.esa.aggregate.sector"].search([("code", "=", "OST")])
        text = self.esa_file(extra="D_S_RNBD_4;Rezidenti;1999900;Nový kód\n", rename={"1311000": "Nový název"})
        wiz = self.wizard(text)
        wiz.action_preview()
        lines = self.lines(wiz)
        self.assertEqual((lines["1999900"].state, lines["1311000"].state), ("new", "renamed"))
        lines["1999900"].aggregate_sector_id = sector
        wiz.action_apply()
        new = self.Esa.search([("code", "=", "1999900")])
        self.assertEqual((new.residency, new.source_methodology, new.valid_from), ("r", "TEST v1", date(2027, 1, 1)))
        self.assertFalse(new.locally_modified)
        renamed = self.Esa.search([("code", "=", "1311000")])
        self.assertEqual(renamed.name, "Nový název")
        self.assertFalse(renamed.locally_modified)
        # druhý import stejného souboru nic nezmění
        again = self.wizard(text)
        again.action_preview()
        self.assertEqual({line.state for line in again.line_ids}, {"same"})

    def test_new_esa_code_needs_issuer_type_and_valid_prefix(self):
        wiz = self.wizard(self.esa_file(extra="D_S_RNBD_4;Rezidenti;2999900;Nový nerezident\n"))
        wiz.action_preview()
        with self.assertRaises(UserError):
            wiz.action_apply()
        self.assertFalse(self.Esa.search([("code", "=", "2999900")]))
        wiz2 = self.wizard(self.esa_file(extra="D_S_RNBD_4;Rezidenti;3999900;Špatný začátek\n"))
        wiz2.action_preview()
        self.lines(wiz2)["3999900"].aggregate_sector_id = self.env["investra.esa.aggregate.sector"].search([], limit=1)
        with self.assertRaises(UserError):
            wiz2.action_apply()

    def test_locally_modified_row_is_conflict_and_stays(self):
        rec = self.Esa.search([("code", "=", "1311000")])
        rec.write({"name": "Ruční název"})
        self.assertTrue(rec.locally_modified)
        wiz = self.wizard(self.esa_file(rename={"1311000": "Název z metodiky"}))
        wiz.action_preview()
        self.assertEqual(self.lines(wiz)["1311000"].state, "conflict")
        wiz.action_apply()
        self.assertEqual(rec.name, "Ruční název")
        self.assertIn("1311000", wiz.result)

    def test_missing_code_gets_valid_to_not_deleted(self):
        text = self.esa_file()
        text = "".join(row for row in text.splitlines(True) if ";1311000;" not in row)
        wiz = self.wizard(text)
        wiz.action_preview()
        self.assertEqual(self.lines(wiz)["1311000"].state, "missing")
        wiz.action_apply()
        rec = self.Esa.search([("code", "=", "1311000")])
        self.assertEqual(rec.valid_to, date(2026, 12, 31))
        self.assertTrue(rec.active)
        self.assertEqual(self.Esa.search_count([]), 80)
        again = self.wizard(text)
        again.action_preview()
        self.assertNotIn("missing", again.line_ids.mapped("state"))

    def test_ba0088_catalog_format_skips_summary_rows_and_sets_parent(self):
        rows = ["ciselnik;verze;platnost_od;typ;kod;nazev\n"]
        for rec in self.Ba.search([]):
            rows.append(f"BA0088;023.000;2024-01-01;polozka;{rec.code};{rec.name}\n")
        rows.append("BA0088;023.000;2024-01-01;souhrnna;S_X;Souhrn\n")
        rows.append("BA0088;023.000;2024-01-01;polozka;1119;Nový druh\n")
        wiz = self.wizard("".join(rows), target="ba0088")
        wiz.action_preview()
        lines = self.lines(wiz)
        self.assertNotIn("S_X", lines)
        self.assertEqual(lines["1119"].state, "new")
        wiz.action_apply()
        new = self.Ba.search([("code", "=", "1119")])
        self.assertEqual((new.parent_code, new.selectable), ("111", False))

    def test_bad_files(self):
        with self.assertRaises(UserError):
            self.wizard("a;b\n1;2\n").action_preview()
        with self.assertRaises(UserError):
            self.wizard(ESA_HEAD + "JINA;x;1;y\n").action_preview()

    def test_regular_user_cannot_run_wizard(self):
        with self.assertRaises(AccessError):
            self.wizard(self.esa_file(), user=self.reader)
