"""Referenční model společného dopočtu úplat, výkonnostní odměny a daně (ZJ-12, příloha A).

Věrný přepis `docs/ukoly/ZJ-12/model.ps1` a `testy.ps1` do Pythonu; nezávislý na Odoo i na `engine.py`.
Slouží jako zdroj očekávaných hodnot, dokud čistá funkce dopočtu v `engine.py` neexistuje (krok 3 ZJ-12);
pak se testy přepnou na ni. Je to jen testovací pomůcka, produkční kód ho nevolá.

Zjednodušení: jedno období, měřítko kapitál třídy, bez příjemců úplat. F1 = úplata fondu, F2 = úplata třídy A,
P = odměna třídy A, T = daň. Stavy S0–S3 = kroky 1–4 (S0 před úplatami, S1 po úplatách, S2 po odměně, S3 po dani).
"""

import math

KEYS = ("F1", "F2", "P", "T")


def amounts(f1=0.0, f2=0.0, p=0.0, t=0.0):
    return {"F1": float(f1), "F2": float(f2), "P": float(p), "T": float(t)}


def scenario(name, classes, rc, hwm_a, f1, f2, r, t):
    return {"Name": name, "Classes": classes, "Rc": rc, "HwmA": hwm_a, "f1": f1, "f2": f2, "r": r, "t": t,
            "s1": 0, "s2": 0, "sp": 0, "st": 2, "Pinned": None}


def with_states(sc, s1, s2, sp, st):
    copy = dict(sc)
    copy.update(s1=s1, s2=s2, sp=sp, st=st)
    return copy


def ratio(sc, code):
    total = sum(c["Pre"] for c in sc["Classes"])
    for c in sc["Classes"]:
        if c["Code"] == code:
            return c["Pre"] / total
    raise KeyError(code)


def tax_deductions(x, st):
    """Odpočitatelné náklady podle stavu daně: S0 nic, S1 úplaty, S2 úplaty a odměna."""
    fund = spec_a = 0.0
    if st >= 1:
        fund += x["F1"]
        spec_a += x["F2"]
    if st >= 2:
        spec_a += x["P"]
    return fund, spec_a


def tax_total(sc, x, st):
    fund, spec_a = tax_deductions(x, st)
    return sc["t"] * max(0.0, sc["Rc"] - fund - spec_a)


def tax_split(sc, x, st):
    """Rozdělení daně x["T"] mezi třídy: poměrem + přesun daňového efektu specifických položek."""
    fund, spec = tax_deductions(x, st)
    base = sc["Rc"] - fund - spec
    e = 0.0
    if abs(spec) > 1e-12:
        e = (sc["t"] * max(0.0, base + spec) - sc["t"] * max(0.0, base)) / spec
    split = {}
    for c in sc["Classes"]:
        rho = ratio(sc, c["Code"])
        spec_c = spec if c["Code"] == "A" else 0.0
        split[c["Code"]] = rho * x["T"] - e * (spec_c - rho * spec)
    return split


def class_value(sc, x, code, fees, perf, tax):
    c = next(c for c in sc["Classes"] if c["Code"] == code)
    rho = ratio(sc, code)
    v = c["Pre"] + rho * sc["Rc"]
    if fees:
        v -= rho * x["F1"]
        if code == "A":
            v -= x["F2"]
    if perf and code == "A":
        v -= x["P"]
    if tax:
        v -= tax_split(sc, x, sc["st"])[code]
    return v


def nav(sc, x, fees, perf, tax):
    return sum(class_value(sc, x, c["Code"], fees, perf, tax) for c in sc["Classes"])


def stage_flags(stage):
    """S0 nic, S1 úplaty, S2 úplaty + odměna, S3 úplaty + odměna + daň."""
    return stage >= 1, stage >= 2, stage >= 3


def step(sc, x):
    """Jeden krok dopočtu: každé pravidlo z aktuálních částek."""
    f1 = sc["f1"] * nav(sc, x, *stage_flags(sc["s1"]))
    f2 = sc["f2"] * class_value(sc, x, "A", *stage_flags(sc["s2"]))
    p = 0.0
    if sc["r"] > 0:
        # Odměna nikdy po sobě samé: S0 nic, S1 úplaty, S3 úplaty + daň.
        value = class_value(sc, x, "A", sc["sp"] >= 1, False, sc["sp"] >= 3)
        p = sc["r"] * max(0.0, value - sc["HwmA"])
    result = amounts(f1, f2, p, tax_total(sc, x, sc["st"]))
    # Opravené pravidlo má pevnou výslednou částku (vypočteno bez opravy + oprava).
    for key, value in (sc["Pinned"] or {}).items():
        result[key] = value
    return result


def distance(a, b):
    return max(abs(a[k] - b[k]) for k in KEYS)


def solve(sc, start, max_steps=500, rel_tol=1e-12):
    """Iterace pevného bodu s relativní tolerancí (1e-12 × max(1, největší částka))."""
    x = start
    last = math.inf
    for i in range(1, max_steps + 1):
        nxt = step(sc, x)
        scale = max([1.0] + [abs(nxt[k]) for k in KEYS])
        last = distance(nxt, x)
        if last < rel_tol * scale:
            return {"X": nxt, "Steps": i, "Converged": True, "Last": last}
        x = nxt
    return {"X": x, "Steps": max_steps, "Converged": False, "Last": last}


def solve_with_corrections(sc, corrections):
    """Dva průchody: bez oprav (= „Vypočteno“), pak s pevnými částkami opravených pravidel."""
    plain = dict(sc, Pinned=None)
    base = solve(plain, amounts())
    pinned = dict(sc, Pinned={k: base["X"][k] + v for k, v in corrections.items()})
    solved = solve(pinned, amounts())
    return {"Base": base["X"], "X": solved["X"], "Converged": base["Converged"] and solved["Converged"],
            "Scenario": pinned}


def today(sc):
    """Dnešní pevné pořadí pro kombinace, které jde dnes nastavit; úplaty S1 přes Cramerovo pravidlo."""
    rho_a = ratio(sc, "A")
    n0 = sum(c["Pre"] for c in sc["Classes"]) + sc["Rc"]
    a0 = next(c for c in sc["Classes"] if c["Code"] == "A")["Pre"] + rho_a * sc["Rc"]
    k1, k2 = float(sc["s1"] == 1), float(sc["s2"] == 1)
    m11, m12 = 1 + sc["f1"] * k1, sc["f1"] * k1
    m21, m22 = sc["f2"] * k2 * rho_a, 1 + sc["f2"] * k2
    b1, b2 = sc["f1"] * n0, sc["f2"] * a0
    det = m11 * m22 - m12 * m21
    f1 = (b1 * m22 - m12 * b2) / det
    f2 = (m11 * b2 - m21 * b1) / det
    p = 0.0
    if sc["r"] > 0:
        value = a0
        if sc["sp"] == 1:
            value -= rho_a * f1 + f2
        p = sc["r"] * max(0.0, value - sc["HwmA"])
    return amounts(f1, f2, p, sc["t"] * max(0.0, sc["Rc"] - f1 - f2 - p))


# --- Testovací sada (přepis testy.ps1; počty kontrol musí sedět s A.1) ---------------------------------------------

TWO = [{"Code": "A", "Pre": 1000000.0}, {"Code": "B", "Pre": 1000000.0}]
ONE = [{"Code": "A", "Pre": 1000000.0}]


def base_scenarios():
    return [
        scenario("Z1 dvě třídy, zisk", TWO, 100000.0, 1000000.0, 0.01, 0.002, 0.2, 0.05),
        scenario("Z2 dvě třídy, ztráta", TWO, -50000.0, 1000000.0, 0.01, 0.002, 0.2, 0.05),
        scenario("Z3 kolem HWM a nuly daně", TWO, 2000.0, 1000000.0, 0.01, 0.002, 0.2, 0.05),
        scenario("Z4 jedna třída, zisk", ONE, 100000.0, 1000000.0, 0.01, 0.002, 0.2, 0.05),
        scenario("Z5 zátěž (vysoké sazby)", TWO, 300000.0, 1000000.0, 0.05, 0.05, 0.5, 0.3),
    ]


class Report:
    def __init__(self):
        self.passed = 0
        self.failures = []

    def close(self, name, actual, expected, tol=0.005):
        if abs(actual - expected) > tol:
            self.failures.append(f"{name}: očekáváno {expected}, vyšlo {actual}")
        else:
            self.passed += 1

    def true(self, name, ok, detail=""):
        if ok:
            self.passed += 1
        else:
            self.failures.append(f"{name} {detail}")


def gross(sc):
    return sum(c["Pre"] for c in sc["Classes"]) + sc["Rc"]


def run_all():
    """Spustí celou sadu a vrátí počty jako výstup A.1 plus seznam selhání a tabulku uzavřených případů."""
    rep = Report()
    scenarios = base_scenarios()
    combos = today_checked = max_steps = 0
    max_residual = 0.0
    for base in scenarios:
        for s1 in range(4):
            for s2 in range(4):
                for sp in (0, 1, 3):
                    for st in range(3):
                        sc = with_states(base, s1, s2, sp, st)
                        label = f"{sc['Name']} [F1 S{s1}, F2 S{s2}, P S{sp}, daň S{st}]"
                        combos += 1
                        low = solve(sc, amounts())
                        high = solve(sc, amounts(300000, 300000, 300000, 300000))
                        rep.true(f"{label} konverguje z nuly", low["Converged"], f"poslední rozdíl kroků {low['Last']}")
                        rep.true(f"{label} konverguje ze shora", high["Converged"], f"poslední rozdíl kroků {high['Last']}")
                        max_steps = max(max_steps, low["Steps"], high["Steps"])
                        x = low["X"]
                        rep.true(f"{label} jediné řešení", distance(x, high["X"]) < 1e-6, f"rozdíl {distance(x, high['X'])}")
                        scale = max([1.0] + [x[k] for k in KEYS])
                        residual = distance(step(sc, x), x)
                        max_residual = max(max_residual, residual / scale)
                        rep.true(f"{label} konzistence", residual < 1e-10 * scale, f"zbytek {residual}")
                        rep.close(f"{label} NAV", nav(sc, x, True, True, True),
                                  gross(sc) - x["F1"] - x["F2"] - x["P"] - x["T"], 1e-6)
                        rep.close(f"{label} součet daně tříd", sum(tax_split(sc, x, st).values()), x["T"], 1e-6)
                        rep.true(f"{label} částky nezáporné", all(x[k] >= -1e-9 for k in KEYS))
                        if s1 <= 1 and s2 <= 1 and sp <= 1 and st == 2:
                            rep.true(f"{label} shoda s dnešním pořadím", distance(x, today(sc)) < 1e-6,
                                     f"rozdíl {distance(x, today(sc))}")
                            today_checked += 1

    closed = {}

    def add_closed(name, actual, expected):
        rep.close(name, actual, expected)
        closed[name] = (round(actual, 4), round(expected, 4))

    def solved(sc):
        return solve(sc, amounts())["X"]

    # C1 obě úplaty po kroku 2; C2 obhospodařování po kroku 1, administrace po kroku 2
    x = solved(with_states(scenario("C1", ONE, 0.0, 0.0, 0.01, 0.001, 0, 0), 1, 1, 0, 2))
    add_closed("C1 obě úplaty S1: obhospodařování", x["F1"], 9891.20)
    add_closed("C1 obě úplaty S1: administrace", x["F2"], 989.12)
    x = solved(with_states(scenario("C2", ONE, 0.0, 0.0, 0.01, 0.001, 0, 0), 0, 1, 0, 2))
    add_closed("C2 S0 + S1: obhospodařování", x["F1"], 10000.00)
    add_closed("C2 S0 + S1: administrace", x["F2"], 989.01)
    # C3 odměna po kroku 4, daň po kroku 3: P = r (V − H − t R) / (1 − r t)
    sc = with_states(scenario("C3", [{"Code": "A", "Pre": 1000.0}], 100.0, 1000.0, 0, 0, 0.2, 0.05), 0, 0, 3, 2)
    x = solved(sc)
    add_closed("C3 odměna po dani: odměna", x["P"], 0.2 * (100 - 0.05 * 100) / (1 - 0.2 * 0.05))
    add_closed("C3 odměna po dani: daň", x["T"], 0.05 * (100 - 0.2 * 95 / 0.99))
    # C4 úplata po kroku 4, daň po kroku 2: S = f (N − t R) / (1 + f (1 − t))
    x = solved(with_states(scenario("C4", ONE, 100000.0, 0.0, 0.01, 0, 0, 0.05), 3, 0, 0, 1))
    s = 0.01 * (1100000 - 0.05 * 100000) / (1 + 0.01 * 0.95)
    add_closed("C4 úplata po dani: úplata", x["F1"], s)
    add_closed("C4 úplata po dani: daň", x["T"], 0.05 * (100000 - s))
    # C5 daňový efekt odměny třídy
    sc = with_states(scenario("C5", TWO, 100000.0, 1000000.0, 0, 0, 0.2, 0.05), 0, 0, 0, 2)
    x = solved(sc)
    add_closed("C5 daňový efekt: odměna A", x["P"], 10000)
    add_closed("C5 daňový efekt: daň fondu", x["T"], 4500)
    add_closed("C5 daňový efekt: kapitál A", class_value(sc, x, "A", True, True, True), 1038000)
    add_closed("C5 daňový efekt: kapitál B", class_value(sc, x, "B", True, True, True), 1047500)
    # C6 ztráta
    sc = with_states(scenario("C6", TWO, -50000.0, 1000000.0, 0.01, 0.002, 0.2, 0.05), 0, 0, 0, 2)
    x = solved(sc)
    add_closed("C6 ztráta: daň", x["T"], 0)
    add_closed("C6 ztráta: daň třídy A", tax_split(sc, x, 2)["A"], 0)
    # C7 přechod přes nulu
    sc = with_states(scenario("C7", TWO, 5000.0, 1000000.0, 0, 0.01, 0, 0.05), 0, 0, 0, 1)
    x = solved(sc)
    split = tax_split(sc, x, 1)
    add_closed("C7 přechod přes nulu: úplata A", x["F2"], 10025)
    add_closed("C7 přechod přes nulu: daň fondu", x["T"], 0)
    add_closed("C7 přechod přes nulu: daň třídy A", split["A"], -125)
    add_closed("C7 přechod přes nulu: daň třídy B", split["B"], 125)
    # C8 oprava úplaty po kroku 2 o −100 (test_correction_lowers_cost_before_after_fees)
    sc = with_states(scenario("C8", ONE, 0.0, 0.0, 0.01, 0, 0, 0), 1, 0, 0, 2)
    res = solve_with_corrections(sc, {"F1": -100.0})
    add_closed("C8 oprava úplaty S1: vypočteno bez opravy", res["Base"]["F1"], 0.01 * 1000000 / 1.01)
    add_closed("C8 oprava úplaty S1: výsledek", res["X"]["F1"], 0.01 * 1000000 / 1.01 - 100)
    add_closed("C8 oprava úplaty S1: FK", nav(res["Scenario"], res["X"], True, True, True),
               1000000 - (0.01 * 1000000 / 1.01 - 100))

    # Oprava každého pravidla zvlášť ve všech kombinacích scénářů Z1 a Z4.
    corr_checks = 0
    for base in (scenarios[0], scenarios[3]):
        for s1 in range(4):
            for s2 in range(4):
                for sp in (0, 1, 3):
                    for st in range(3):
                        sc = with_states(base, s1, s2, sp, st)
                        for corr in ({"F1": -100.0}, {"F2": -50.0}, {"P": -30.0}, {"T": -20.0}):
                            key = next(iter(corr))
                            label = f"{sc['Name']} [F1 S{s1}, F2 S{s2}, P S{sp}, daň S{st}] oprava {key}"
                            res = solve_with_corrections(sc, corr)
                            rep.true(f"{label} konverguje", res["Converged"])
                            rep.close(f"{label} výsledek = vypočteno + oprava", res["X"][key], res["Base"][key] + corr[key], 1e-6)
                            nxt = step(res["Scenario"], res["X"])
                            scale = max([1.0] + [abs(res["X"][k]) for k in KEYS])
                            for k in KEYS:
                                if k != key:
                                    rep.true(f"{label} konzistence {k}", abs(nxt[k] - res["X"][k]) < 1e-10 * scale)
                            rep.close(f"{label} NAV", nav(res["Scenario"], res["X"], True, True, True),
                                      gross(sc) - sum(res["X"][k] for k in KEYS), 1e-6)
                            corr_checks += 1

    return {"corrections": corr_checks, "combinations": combos, "today_checked": today_checked, "max_steps": max_steps,
            "max_residual": max_residual, "passed": rep.passed, "failures": rep.failures, "closed": closed}


if __name__ == "__main__":
    result = run_all()
    print(f"Oprav s pevnou částkou ověřeno: {result['corrections']}")
    print(f"Kombinací: {result['combinations']}, ze shody s dnešním pořadím ověřeno: {result['today_checked']}")
    print(f"Nejvíc kroků dopočtu: {result['max_steps']}")
    print(f"Největší relativní zbytek po dopočtu: {result['max_residual']}")
    print(f"Kontrol prošlo: {result['passed']}, selhalo: {len(result['failures'])}")
    for name, (model, formula) in result["closed"].items():
        print(f"  {name}: {model} ({formula})")
    for failure in result["failures"][:40]:
        print("SELHÁNÍ:", failure)
