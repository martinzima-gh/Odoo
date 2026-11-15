"""Testy kontroly šablon OWL: chyba ST-03 (čtení členu bez this.) se musí zachytit."""

import tempfile
import unittest
from pathlib import Path

import check_templates

BAD = '<templates><t t-name="a.B"><span t-if="!items.length"/><li t-foreach="items" t-as="item" t-key="item.k"/></t></templates>'
GOOD = '<templates><t t-name="a.B"><span t-if="!this.items.length"/><li t-foreach="this.items" t-as="item" t-key="item.k" t-out="item.x"/></t></templates>'


class TestCheckTemplates(unittest.TestCase):
    def check(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.xml"
            path.write_text(text, encoding="utf-8")
            return check_templates.check_file(path)

    def test_missing_this_found(self):
        self.assertEqual(len(self.check(BAD)), 2)

    def test_this_and_loop_variable_ok(self):
        self.assertEqual(self.check(GOOD), [])

    def test_repository_templates_valid(self):
        errors = []
        for path in sorted(check_templates.ROOT.glob("addons/custom/*/static/src/**/*.xml")):
            errors.extend(check_templates.check_file(path))
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
