#!/usr/bin/env python3
"""Vygeneruje seed číselníků ESA (D_S_RNBD_4) a BA0088 z katalogů v docs/cnb/.

Použití: python3 tools/codelist_seed.py
Zapíše data/esa_code.xml a data/ba0088.xml addonu investra_instrument_master. Žádné kódy mimo katalog.
Mapování (typ emitenta, Z_ESA2010, rodina a skupina BA0088) je z oddílu 4 plánu evidence nástrojů.
"""
import csv
import sys
from pathlib import Path
from xml.sax.saxutils import quoteattr

ROOT = Path(__file__).resolve().parent.parent
CNB = ROOT / "docs" / "cnb"
DATA = ROOT / "addons" / "custom" / "investra_instrument_master" / "data"
ESA_SECTOR_XML = ROOT / "addons" / "custom" / "investra_counterparty" / "data" / "esa_sector.xml"
ESA_METHOD = "FOFI20261201 / D_S_RNBD_4"
BA_METHOD = "BA0088 v023.000"


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def esc(value):
    return quoteattr(value)[1:-1]


# ---------- ESA ----------
VLI = {"1311000", "1312000", "1313000", "1314000", "2003110", "2003120", "2003130", "2003140"}
OST = {"1443000", "1500000", "2004430", "2005000", "2009031", "2009035"}
ANY_COUNTRY = {"2009031", "2009035"}
NO_ESA2010 = {"1443000", "2004430"}


def aggregate(code):
    if code in VLI:
        return "VLI"
    if code in OST:
        return "OST"
    if code.startswith("110") or code.startswith("2001"):
        return "NFP"
    if code == "1210000" or code.startswith("122") or code == "2002100" or code.startswith("20022"):
        return "BANK"
    if code[:3] in {"123", "124", "125", "126", "127", "128", "129"} or code[:5] in {
            f"2002{d}" for d in "3456789"}:
        return "FIN"
    raise SystemExit(f"ESA kód {code} nelze zařadit k typu emitenta")


def esa2010(code, known):
    if code in NO_ESA2010:
        return None
    if code in VLI:
        target = code
    elif code in {"2009031", "2009035"}:
        target = "2009030"
    elif code.startswith("1"):
        target = code[:3] + "0000"
    else:
        target = code[:5] + "00"
    if target not in known:
        raise SystemExit(f"ESA kód {code}: sektor Z_ESA2010 {target} neexistuje")
    return target


def build_esa():
    known = {line.split('"code">')[1].split("<")[0] for line in ESA_SECTOR_XML.read_text().splitlines() if '"code">' in line}
    rows = [r for r in read_csv(CNB / "ciselniky-FOFI20261201.csv") if r["domena"] == "D_S_RNBD_4"]
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           f"<!-- Číselník {ESA_METHOD}; generuje tools/codelist_seed.py, ručně neupravovat -->",
           '<odoo noupdate="1">']
    counts = {}
    for r in rows:
        code, name = r["kod"], r["hodnota"].strip()
        agg = aggregate(code)
        counts[agg] = counts.get(agg, 0) + 1
        sector = esa2010(code, known)
        fields = [
            f'<field name="code">{code}</field>',
            f'<field name="name">{esc(name)}</field>',
            f'<field name="aggregate_sector_id" ref="esa_aggregate_{agg.lower()}"/>',
            f'<field name="residency">{"r" if code[0] == "1" else "nr"}</field>',
        ]
        if sector:
            fields.append(f'<field name="esa2010_sector_id" ref="investra_counterparty.esa_{sector}"/>')
        if code in ANY_COUNTRY:
            fields.append('<field name="any_country" eval="True"/>')
        fields.append(f'<field name="source_methodology">{ESA_METHOD}</field>')
        out.append(f'    <record id="esa_code_{code}" model="investra.esa.code">{"".join(fields)}</record>')
    out.append("</odoo>")
    (DATA / "esa_code.xml").write_text("\n".join(out) + "\n", encoding="utf-8")
    return len(rows), counts


# ---------- BA0088 ----------
# kód -> (rodina, skupina); None = jen z katalogu, bez rodiny
FAMILY = {}
for codes, fam, grp in [
    ("111 112 141", "debt", "GOV_BONDS"),
    ("12 13 142 149 15 41 42 17 199", "debt", "OTHER_BONDS"),
    ("191 63", "certificate", "CERTIFICATES"),
    ("211 212 219", "equity", "EQUITIES"),
    ("217 218 225 226", "fund", "FUND_SECURITIES"),
    ("23 24 27 29", "equity", "OTHER_EQUITY_SECURITIES"),
    ("8", "direct_equity", "OTHER_EQUITY_SECURITIES"),
    ("311 312", "bill", "BILLS_COUPONS"),
    ("36 37", "coupon", "BILLS_COUPONS"),
    ("6111 6112 6119 612", "derivative", "FORWARDS_FUTURES"),
    ("6131 6132 6133 6134 6135 6136 6139", "derivative", "SWAPS"),
    ("6191 6192 6199 6211 6212 6221 6222 623 629 69", "derivative", "OPTIONS_AND_OTHER_DERIVATIVES"),
    ("7", "other", "OTHER_INSTRUMENTS"),
]:
    for c in codes.split():
        FAMILY[c] = (fam, grp)

GROUPS = [
    ("GOV_BONDS", "Státní dluhopisy"),
    ("OTHER_BONDS", "Ostatní dluhopisy"),
    ("CERTIFICATES", "Investiční certifikáty"),
    ("EQUITIES", "Akcie"),
    ("FUND_SECURITIES", "Cenné papíry fondů"),
    ("OTHER_EQUITY_SECURITIES", "Ostatní majetkové cenné papíry"),
    ("BILLS_COUPONS", "Směnky a kupóny"),
    ("FORWARDS_FUTURES", "Forwardy a futures"),
    ("SWAPS", "Swapy"),
    ("OPTIONS_AND_OTHER_DERIVATIVES", "Opce a ostatní deriváty"),
    ("OTHER_INSTRUMENTS", "Ostatní nástroje"),
]
LEVERAGE = {"63": "must_true", "191": "must_false"}


def build_ba0088():
    rows = [r for r in read_csv(CNB / "ciselnik-BA0088-v023.csv") if r["typ"] == "polozka"]
    codes = {r["kod"] for r in rows}
    missing = set(FAMILY) - codes
    if missing:
        raise SystemExit(f"Kódy mimo katalog BA0088: {sorted(missing)}")
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           f"<!-- Číselník {BA_METHOD}; generuje tools/codelist_seed.py, ručně neupravovat -->",
           '<odoo noupdate="1">']
    selectable = 0
    for r in rows:
        code, name = r["kod"], " ".join(r["nazev"].split())
        parents = [c for c in codes if c != code and code.startswith(c)]
        fields = [
            f'<field name="code">{code}</field>',
            f'<field name="name">{esc(name)}</field>',
            f'<field name="valid_from">{r["platnost_od"]}</field>',
            f'<field name="source_methodology">{BA_METHOD}</field>',
        ]
        if parents:
            fields.append(f'<field name="parent_code">{max(parents, key=len)}</field>')
        if code in FAMILY:
            fam, grp = FAMILY[code]
            selectable += 1
            fields += ['<field name="selectable" eval="True"/>', f'<field name="asset_family">{fam}</field>',
                       f'<field name="group_id" ref="ba0088_group_{grp.lower()}"/>']
            if fam != "derivative":
                fields.append('<field name="requires_issuer" eval="True"/>')
            if fam in ("debt", "bill"):
                fields.append('<field name="requires_maturity" eval="True"/>')
            if code == "7":
                fields.append('<field name="requires_justification" eval="True"/>')
            if code in LEVERAGE:
                fields.append(f'<field name="leverage_rule">{LEVERAGE[code]}</field>')
        out.append(f'    <record id="ba0088_{code}" model="investra.ba0088.code">{"".join(fields)}</record>')
    out.append("</odoo>")
    (DATA / "ba0088.xml").write_text("\n".join(out) + "\n", encoding="utf-8")

    grp = ['<?xml version="1.0" encoding="utf-8"?>', "<odoo noupdate=\"1\">"]
    for code, name in GROUPS:
        grp.append(f'    <record id="ba0088_group_{code.lower()}" model="investra.ba0088.group">'
                   f'<field name="code">{code}</field><field name="name">{name}</field></record>')
    grp.append("</odoo>")
    (DATA / "ba0088_group.xml").write_text("\n".join(grp) + "\n", encoding="utf-8")
    return len(rows), selectable


if __name__ == "__main__":
    DATA.mkdir(parents=True, exist_ok=True)
    print("ESA kódů, podle typu emitenta:", build_esa())
    print("BA0088 položek, z toho nabízených:", build_ba0088())
    sys.exit(0)
