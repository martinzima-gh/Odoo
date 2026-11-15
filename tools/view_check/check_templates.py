"""Kontrola šablon OWL (static/src/**/*.xml): čtení členu komponenty bez `this.`.

Odoo 20 v šablonách komponent vyžaduje `this.` (příklad: ST-03, `items` místo `this.items`).
Heuristika: první identifikátor ve výrazech t-if, t-elif, t-foreach, t-out, t-esc, t-att-* musí být
`this`, proměnná smyčky (t-as), proměnná z t-set, `props`/`env` nejsou povoleny bez `this.`,
nebo literál/klíčové slovo JS. Vlastní kontrola nenahrazuje zkoušku v prohlížeči.

Použití z kořene repozitáře: python3 tools/view_check/check_templates.py [soubor.xml ...]
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPR_ATTRS = ("t-if", "t-elif", "t-foreach", "t-out", "t-esc", "t-key")
ALLOWED = {"this", "true", "false", "null", "undefined", "not", "and", "or", "new", "typeof", "Math", "Object", "Array", "JSON"}
STRING = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
IDENT = re.compile(r"(?<![\w.$])([A-Za-z_$][\w$]*)")


def is_expr_attr(name):
    return name in EXPR_ATTRS or name.startswith("t-att-") or name == "t-att"


def check_file(path):
    errors = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{path}: neplatné XML: {exc}"]

    def walk(node, scope):
        scope = set(scope)
        if node.get("t-as"):
            scope.add(node.get("t-as"))
            scope.update({node.get("t-as") + s for s in ("_index", "_first", "_last", "_value")})
        if node.get("t-set"):
            scope.add(node.get("t-set"))
        for name, value in node.attrib.items():
            if not is_expr_attr(name) or name == "t-on-click":
                continue
            text = STRING.sub("''", value)
            # tělo šipkové funkce nekontrolujeme (parametry), jen první identifikátor mimo ni
            if "=>" in text:
                continue
            for match in IDENT.finditer(text):
                ident = match.group(1)
                if ident not in ALLOWED and ident not in scope:
                    errors.append(f"{path}: {name}=\"{value}\": „{ident}“ bez this. (člen komponenty?)")
        for child in node:
            walk(child, scope)

    walk(root, set())
    return errors


def main(argv):
    paths = [Path(a) for a in argv] or sorted(ROOT.glob("addons/custom/*/static/src/**/*.xml"))
    errors = []
    for path in paths:
        errors.extend(check_file(path))
    for error in errors:
        print(error)
    print(f"Zkontrolováno šablon: {len(paths)}, chyb: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
