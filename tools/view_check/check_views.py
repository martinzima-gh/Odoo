"""Kontrola pohledů Odoo 20 podle schémat RelaxNG bez Dockeru a databáze.

Odoo při aktualizaci modulu ověřuje pohledy list, search, calendar, graph, pivot a activity
podle schémat v odoo/addons/base/rng (zde kopie z obrazu odoo:20.0-20261102, licence LGPL-3).
Skript projde soubory XML (výchozí: addons/custom/*/views/*.xml), vybere záznamy ir.ui.view
s vlastním arch (bez inherit_id) a ověří je přes xmllint. Formuláře Odoo kontroluje jinak,
skript je nepokrývá; nenahrazuje testy Odoo, jen zachytí chyby struktury dřív.

Použití z kořene repozitáře: python3 tools/view_check/check_views.py [soubor.xml ...]
Návratový kód 0 = vše v pořádku, 1 = chyba.
"""

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RNG_DIR = Path(__file__).resolve().parent / "rng"
VIEW_TYPES = {"list", "search", "calendar", "graph", "pivot", "activity"}
XMLLINT = "/usr/bin/xmllint"


def view_archs(path):
    """Vrátí (id záznamu, kořen arch) pro každý samostatný pohled v souboru."""
    for record in ET.parse(path).getroot().iter("record"):
        if record.get("model") != "ir.ui.view":
            continue
        fields = {f.get("name"): f for f in record.findall("field")}
        if "inherit_id" in fields or "arch" not in fields:
            continue
        children = list(fields["arch"])
        if len(children) == 1 and children[0].tag in VIEW_TYPES:
            yield record.get("id"), children[0]


def check_file(path):
    errors = []
    try:
        archs = list(view_archs(path))
    except ET.ParseError as exc:
        return [f"{path}: neplatné XML: {exc}"]
    for rec_id, arch in archs:
        schema = RNG_DIR / f"{arch.tag}_view.rng"
        result = subprocess.run(
            [XMLLINT, "--noout", "--relaxng", str(schema), "-"],
            input=ET.tostring(arch, encoding="utf-8"), capture_output=True, check=False,
        )
        if result.returncode != 0:
            detail = " ".join(
                line for line in result.stderr.decode("utf-8", "replace").splitlines()
                if "fails to validate" not in line
            )
            errors.append(f"{path}: pohled {rec_id} ({arch.tag}): {detail}")
    return errors


def main(argv):
    paths = [Path(a) for a in argv] or sorted(ROOT.glob("addons/custom/*/views/*.xml"))
    errors = []
    for path in paths:
        errors.extend(check_file(path))
    for error in errors:
        print(error)
    print(f"Zkontrolováno souborů: {len(paths)}, chyb: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
