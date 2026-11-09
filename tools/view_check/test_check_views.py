"""Testy kontroly pohledů: chybu, kterou Odoo 20 hlásí při aktualizaci modulu, musí zachytit i skript."""

import tempfile
import unittest
from pathlib import Path

import check_views

GOOD = """<odoo><record id="v" model="ir.ui.view"><field name="model">x.y</field><field name="arch" type="xml">
<search><field name="name"/><filter name="f" string="F" domain="[]"/>
<group><filter name="g" string="G" context="{'group_by': 'name'}"/></group></search>
</field></record></odoo>"""


class TestCheckViews(unittest.TestCase):
    def check(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "views.xml"
            path.write_text(text, encoding="utf-8")
            return check_views.check_file(path)

    def test_valid_search_view(self):
        self.assertEqual(self.check(GOOD), [])

    def test_group_attributes_rejected_like_odoo20(self):
        errors = self.check(GOOD.replace("<group>", '<group expand="0" string="Seskupit podle">'))
        self.assertEqual(len(errors), 1)
        self.assertIn("expand", errors[0])

    def test_inherited_view_skipped(self):
        bad = GOOD.replace('<field name="model">', '<field name="inherit_id" ref="a.b"/><field name="model">')
        self.assertEqual(self.check(bad.replace("<group>", '<group expand="0">')), [])

    def test_repository_views_valid(self):
        errors = []
        for path in sorted(check_views.ROOT.glob("addons/custom/*/views/*.xml")):
            errors.extend(check_views.check_file(path))
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
