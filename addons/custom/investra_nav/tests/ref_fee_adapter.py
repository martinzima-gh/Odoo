"""Převod scénářů referenčního modelu (ref_fee_model) na vstup engine.solve_fees (ZJ-12 krok 3).

Stavy modelu S0–S3 odpovídají krokům 1–4. Testovací pomůcka bez Odoo; produkční kód ji nevolá.
"""

from decimal import Decimal

try:
    from .. import engine
except ImportError:  # spuštění mimo Odoo: python3 -m ... z adresáře modulu
    import engine  # noqa: F401


def D(value):
    return Decimal(str(value))


def solve(sc, pinned=None, corrections=None):
    """Vstup pro solve_fees ze scénáře modelu; vrací částky pod klíči F1, F2, P, T a výsledek dopočtu."""
    classes = sc["Classes"]
    total = sum(D(c["Pre"]) for c in classes)
    rc = D(sc["Rc"])
    state = {c["Code"]: {"value": D(c["Pre"]) + D(c["Pre"]) / total * rc, "ratio": D(c["Pre"]) / total} for c in classes}
    f1, f2, r, t, hwm = D(sc["f1"]), D(sc["f2"]), D(sc["r"]), D(sc["t"]), D(sc["HwmA"])
    perf_step = {0: 1, 1: 2, 3: 4}[sc["sp"]]
    items = [
        {"key": "F1", "stage": 2, "payer": None, "base": {"scope": "fund", "step": sc["s1"] + 1},
         "amount": lambda base: f1 * base},
        {"key": "F2", "stage": 2, "payer": "A", "base": {"scope": "class", "class": "A", "step": sc["s2"] + 1},
         "amount": lambda base: f2 * base},
        {"key": "P", "stage": 3, "payer": "A", "base": {"scope": "class", "class": "A", "step": perf_step},
         "amount": lambda base: r * max(base - hwm, Decimal(0)) if r > 0 else Decimal(0)},
        {"key": "T", "stage": 4, "payer": None, "tax": {"rate": t, "step": sc["st"] + 1, "result": rc, "booked": 0}},
    ]
    for key, amount in (corrections or {}).items():
        # Oprava jako samostatná pevná položka plátce opraveného pravidla (jako ruční oprava v ocenění).
        source = next(i for i in items if i["key"] == key)
        if key == "T":
            continue
        items.append({"key": f"corr:{key}", "stage": source["stage"], "payer": source["payer"], "base": None,
                      "amount": D(amount)})
    result = engine.solve_fees(state, items, pinned=pinned)
    return result


def class_value(sc, result, code):
    """Hodnota třídy po všech krocích (pro kontrolu daňového efektu)."""
    classes = sc["Classes"]
    total = sum(D(c["Pre"]) for c in classes)
    pre = next(D(c["Pre"]) for c in classes if c["Code"] == code)
    rho = pre / total
    value = pre + rho * D(sc["Rc"])
    x = result["amounts"]
    value -= rho * x["F1"]
    if code == "A":
        value -= x["F2"] + x["P"]
    value -= rho * x["T"]
    value += result["tax"]["transfers"][code]
    for key, amount in x.items():
        if key.startswith("corr:"):
            value -= rho * amount if key == "corr:F1" else (amount if code == "A" else 0)
    return value
