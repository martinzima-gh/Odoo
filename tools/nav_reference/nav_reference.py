#!/usr/bin/env python3
"""Referenční výpočet NAV tříd mimo Odoo.

Počítá podle vzorců z části „Ocenění a alokace“ v docs/architektura.md, v přesné desítkové aritmetice.
Vstup a očekávané výsledky jsou ve scénářích JSON, které používají i testy modulu investra_nav.
Není to nezávislá kontrola modulu: autor je stejný. Klíčové příklady musí ověřit člověk.

Použití: nav_reference.py [--write] [adresář se scénáři]
"""
import json
import sys
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal, getcontext
from pathlib import Path

getcontext().prec = 50
CENT = Decimal("0.01")


def dec(value):
    return Decimal(str(value))


def money(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def unit_price(value, units, digits, method):
    rounding = ROUND_DOWN if method == "down" else ROUND_HALF_UP
    return (value / units).quantize(Decimal(1).scaleb(-digits), rounding=rounding)


def split_with_remainder(raw):
    """Zaokrouhlí kapitály tříd; rozdíl haléřů nese třída s největším kapitálem.

    Pravidlo je návrh: zajišťuje, že součet tříd se přesně rovná FK.
    """
    rounded = {code: money(value) for code, value in raw.items()}
    remainder = money(sum(raw.values())) - sum(rounded.values())
    if remainder:
        largest = max(sorted(rounded), key=lambda code: rounded[code])
        rounded[largest] += remainder
    return rounded


def compute(scenario):
    classes = {c["code"]: c for c in scenario["classes"]}
    fkt = {code: dec(c["opening_capital"]) for code, c in classes.items()}
    units = {code: dec(c["opening_units"]) for code, c in classes.items()}
    perf_accrued = {code: Decimal(0) for code in classes}
    tax_accrued = Decimal(0)
    ytd_result = Decimal(0)
    results = []

    for val in scenario["valuations"]:
        subs = {k: dec(v["amount"]) for k, v in val.get("subscriptions", {}).items()}
        reds = {k: dec(v["amount"]) for k, v in val.get("redemptions", {}).items()}
        pfkt = {c: fkt[c] + subs.get(c, 0) - reds.get(c, 0) for c in classes}
        for code, item in val.get("subscriptions", {}).items():
            units[code] += dec(item["units"])
        for code, item in val.get("redemptions", {}).items():
            units[code] -= dec(item["units"])
        pfk = sum(pfkt.values())
        apt = {c: pfkt[c] / pfk for c in classes}

        common = dec(val.get("common_result", 0))
        delta = {c: dec(val.get("specific", {}).get(c, 0)) for c in classes}
        fk = pfk + common + sum(delta.values())
        result = common + sum(delta.values())

        mgmt_fee = Decimal(0)
        if val.get("mgmt_fee"):
            fee = val["mgmt_fee"]
            ratio = dec(fee["rate"]) * dec(fee["days"]) / dec(fee["basis"])
            if fee.get("base", "before") == "after":
                ratio = ratio / (1 + ratio)  # základ je FK po úplatě: přímý vzorec místo opakování
            mgmt_fee = money(fk * ratio)
            fk -= mgmt_fee
            result -= mgmt_fee

        perf_moves = {}
        for code, fee in val.get("perf_fee", {}).items():
            nfk = fk - sum(delta.values())
            gross = apt[code] * nfk + delta[code] + perf_accrued[code]
            excess = gross / units[code] - dec(fee["hwm"])
            required = money(dec(fee["rate"]) * max(excess, Decimal(0)) * units[code])
            move = required - perf_accrued[code]
            perf_moves[code] = move
            perf_accrued[code] = required
            delta[code] -= move
            fk -= move
            result -= move

        ytd_result += result
        tax_move = Decimal(0)
        if val.get("tax"):
            required = money(max(ytd_result, Decimal(0)) * dec(val["tax"]["rate"]))
            tax_move = required - tax_accrued
            tax_accrued = required
            fk -= tax_move

        nfk = fk - sum(delta.values())
        fkt = split_with_remainder({c: apt[c] * nfk + delta[c] for c in classes})
        fx = {k: dec(v) for k, v in val.get("fx", {}).items()}
        prices = {}
        for code, cls in classes.items():
            value = fkt[code]
            if cls.get("currency", scenario["currency"]) != scenario["currency"]:
                value = value / fx[cls["currency"]]
            prices[code] = unit_price(value, units[code], cls["price_digits"], cls.get("rounding", "down"))

        assert sum(fkt.values()) == money(fk), "součet tříd se musí rovnat FK"
        results.append({
            "date": val["date"],
            "fk": str(money(fk)),
            "nfk": str(money(nfk)),
            "mgmt_fee": str(mgmt_fee),
            "tax_move": str(tax_move),
            "perf_moves": {k: str(v) for k, v in sorted(perf_moves.items())},
            "apt": {c: str(apt[c].quantize(Decimal("0.0000000001"))) for c in sorted(classes)},
            "delta": {c: str(money(delta[c])) for c in sorted(classes)},
            "fkt": {c: str(fkt[c]) for c in sorted(classes)},
            "units": {c: str(units[c]) for c in sorted(classes)},
            "price": {c: str(prices[c]) for c in sorted(classes)},
        })
    return results


def main(argv):
    write = "--write" in argv
    paths = [a for a in argv if not a.startswith("--")]
    default = Path(__file__).resolve().parents[2] / "addons/custom/investra_nav/tests/scenarios"
    folder = Path(paths[0]) if paths else default
    failed = 0
    for path in sorted(folder.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        computed = compute(data)
        if write:
            data["expected"] = computed
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        status = "OK" if data.get("expected") == computed else "ROZDÍL"
        failed += status != "OK"
        print(f"{status:7}{path.name}: {data['title']}")
        for row in computed:
            print("        ", row["date"], "FK", row["fk"], "třídy", row["fkt"], "kurzy", row["price"])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
