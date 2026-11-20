"""Výpočet úplat a rozdělení mezi třídy, bez závislosti na Odoo.

Parametry přicházejí jako slovníky, výsledky se vrací s rozpisem kroků, aby šlo každé číslo vysvětlit.
Pravidla jsou skládaná z bloků: období a verze sazby, základ, částka, výkonnost, rozdělení mezi třídy.
Přehled pokrytých variant je v docs/poplatky-varianty.md.
"""
from datetime import date, timedelta
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal, getcontext

getcontext().prec = 50
ZERO = Decimal(0)
CENT = Decimal("0.01")


def dec(value):
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))


def money(value):
    return dec(value).quantize(CENT, rounding=ROUND_HALF_UP)


def _months_between(start, end):
    return (end.year - start.year) * 12 + end.month - start.month


def _days_30_360(start, end, basis):
    """Dny v konvenci 30/360: evropská 30E/360, nebo americká 30/360 (bond basis)."""
    d1, d2 = start.day, end.day
    if basis == "thirty360_eu":
        d1, d2 = min(d1, 30), min(d2, 30)
    else:
        if d1 == 31:
            d1 = 30
        if d2 == 31 and d1 == 30:
            d2 = 30
    return (end.year - start.year) * 360 + (end.month - start.month) * 30 + d2 - d1


def year_fraction(start, end, basis="act365"):
    """Část roku za období (start, end]: den start se nezapočítává, den end ano."""
    days = (end - start).days
    if basis == "act365":
        return Decimal(days) / 365
    if basis == "act360":
        return Decimal(days) / 360
    if basis == "act_act":
        total = ZERO
        cursor = start
        while cursor < end:
            # Dny (cursor, boundary] leží v jednom kalendářním roce boundary.year.
            year = cursor.year + 1 if cursor == date(cursor.year, 12, 31) else cursor.year
            boundary = min(end, date(year, 12, 31))
            length = (date(year, 12, 31) - date(year - 1, 12, 31)).days
            total += Decimal((boundary - cursor).days) / length
            cursor = boundary
        return total
    if basis == "months":
        return Decimal(_months_between(start, end)) / 12
    if basis in ("thirty360_eu", "thirty360_us"):
        return Decimal(_days_30_360(start, end, basis)) / 360
    raise ValueError(f"Neznámá konvence dnů: {basis}")


def split_by_versions(start, end, versions):
    """Rozdělí období podle verzí sazby. Verze platí od valid_from včetně.

    Období bez platné verze je chyba: sazba se nesmí tiše domýšlet.
    """
    ordered = sorted(versions, key=lambda v: v["valid_from"])
    segments = []
    cursor = start
    while cursor < end:
        first_day = cursor + timedelta(days=1)
        valid = [v for v in ordered if v["valid_from"] <= first_day]
        if not valid:
            raise ValueError(f"Pro den {first_day} není platná sazba.")
        current = valid[-1]
        following = [v for v in ordered if v["valid_from"] > first_day]
        seg_end = end
        if following:
            seg_end = min(end, following[0]["valid_from"] - timedelta(days=1))
        segments.append((cursor, seg_end, current))
        cursor = seg_end
    return segments


def _variable_rate_amount(version, base):
    """Roční částka závislá na základu, před poměrem za období."""
    tiers = version.get("tiers")
    if tiers:
        # Klouzavá pásma: každá sazba platí jen na svou část základu.
        amount = ZERO
        ordered = sorted(tiers, key=lambda t: dec(t["from"]))
        for index, tier in enumerate(ordered):
            low = dec(tier["from"])
            high = dec(ordered[index + 1]["from"]) if index + 1 < len(ordered) else None
            portion = (min(base, high) if high is not None else base) - low
            if portion > 0:
                amount += portion * dec(tier["rate"])
        return amount
    threshold = dec(version.get("threshold"))
    return max(base - threshold, ZERO) * dec(version.get("rate"))


def _step_amount(version, base):
    """Stupňová částka: pevná cena a příplatek za každé započaté pásmo nad prvním."""
    size = dec(version.get("step_size"))
    if not size or base <= size:
        return ZERO
    steps = ((base - size) / size).to_integral_value(rounding=ROUND_CEILING)
    return steps * dec(version.get("step_amount"))


def _segment_amount(version, seg_start, seg_end, base, basis, classes_count):
    fraction = year_fraction(seg_start, seg_end, basis)
    variable = _variable_rate_amount(version, base) * fraction
    # Pevné částky jsou měsíční; „každý započatý měsíc“ počítá kalendářní měsíce období.
    months = Decimal(_months_between(seg_start, seg_end))
    if version.get("fixed_mode", "pro_rata") == "pro_rata":
        months = year_fraction(seg_start, seg_end, basis) * 12
    fixed = dec(version.get("fixed_monthly")) + _step_amount(version, base)
    extra = max(classes_count - int(version.get("included_classes") or classes_count), 0)
    fixed += extra * dec(version.get("extra_class_monthly"))
    total = variable + fixed * months
    if version.get("min_annual") not in (None, False, 0):
        total = max(total, dec(version["min_annual"]) * fraction)
    if version.get("max_annual") not in (None, False, 0):
        total = min(total, dec(version["max_annual"]) * fraction)
    return total, {
        "from": seg_start.isoformat(),
        "to": seg_end.isoformat(),
        "fraction": str(fraction),
        "variable": str(variable),
        "fixed": str(fixed * months),
        "amount": str(total),
    }


def periodic_fee(rule, start, end, base, classes_count=1, max_steps=100):
    """Časově rozlišená úplata za období.

    rule: basis, base_mode (before|after) a versions. U základu „po úplatě“ se výsledek
    opakuje do ustálení, protože úplata snižuje vlastní základ.
    """
    base = dec(base)
    basis = rule.get("basis", "act365")
    segments = split_by_versions(start, end, rule["versions"])

    def compute(current_base):
        rows = [_segment_amount(v, s, e, current_base, basis, classes_count) for s, e, v in segments]
        return sum((r[0] for r in rows), ZERO), [r[1] for r in rows]

    amount, rows = compute(base)
    steps = 1
    if rule.get("base_mode", "before") == "after":
        for steps in range(2, max_steps + 1):
            updated, rows = compute(base - amount)
            if abs(updated - amount) < Decimal("0.000001"):
                amount = updated
                break
            amount = updated
        else:
            raise ValueError("Výpočet úplaty se neustálil.")
    # „exact“ = částka před zaokrouhlením; ocenění na ní ustaluje společný dopočet úplat „po všech úplatách“ (ZJ-06 bod 7).
    return {"amount": money(amount), "exact": amount, "steps": steps, "segments": rows}


def average_fee(rule, start, end, points, current, booked=ZERO, shift=ZERO, classes_count=1):
    """Úplata z průměru (ZJ-14): nárok za období (start, end] z prostého průměru bodů a dnešního bodu minus naúčtované.

    points: dřívější body (kapitály), current: dnešní bod, shift: oprava základu přičtená k průměru (ZJ-12 B.7).
    Pevné části, minimum, maximum a příplatky se uplatní jednou za volání (u tříd tedy za každou třídu).
    """
    points = [dec(p) for p in points]
    average = (sum(points, ZERO) + dec(current)) / (len(points) + 1) + dec(shift)
    result = periodic_fee(rule, start, end, average, classes_count=classes_count)
    booked = dec(booked)
    return {"average": average, "entitlement": result["amount"], "booked": booked, **result,
            "move": result["amount"] - booked, "exact_move": result["exact"] - booked}


def growth_factor(start, end, spec):
    """Kolikrát má vzrůst srovnávací hodnota za období (start, end]."""
    kind = spec.get("hurdle_kind", "none")
    if kind == "none" or end <= start:
        return Decimal(1)
    fraction = year_fraction(start, end, spec.get("basis", "act365"))
    if kind == "fixed":
        rate = dec(spec.get("hurdle_rate"))
        factor = (1 + rate) ** fraction if spec.get("compounding") else 1 + rate * fraction
    elif kind == "index":
        margin = dec(spec.get("hurdle_margin")) * fraction
        factor = dec(spec["index_end"]) / dec(spec["index_start"]) + margin
    else:
        raise ValueError(f"Neznámý druh překážky: {kind}")
    # Záporný etalon: odměna se počítá jen z kladné výkonnosti.
    return max(factor, Decimal(1)) if spec.get("hurdle_floor_zero") else factor


def performance_fee(spec, start, end, gross, units=None, flows=(), accrued=ZERO):
    """Požadovaný zůstatek výkonnostní odměny a doplatek proti už zaúčtovanému.

    measure:
      capital: porovnání kapitálu třídy, vstupy a výstupy upravují srovnávací hodnotu
      unit: porovnání hodnoty na kus, odměna se násobí počtem kusů
    gross je hodnota před touto odměnou. reference je výchozí hodnota období a hwm nejvyšší
    dosažená hodnota, nad kterou se odměna počítá; obojí v jednotkách podle measure.
    """
    measure = spec.get("measure", "capital")
    gross = dec(gross)
    reference = dec(spec.get("reference"))
    rate = dec(spec.get("rate"))
    factor = growth_factor(start, end, spec)
    adjusted_flows = ZERO
    plain_flows = ZERO
    multiplier = Decimal(1)
    if measure == "unit":
        multiplier = dec(units)
        value = gross / multiplier
    else:
        value = gross
        for flow_date, amount in flows:
            plain_flows += dec(amount)
            adjusted_flows += dec(amount) * growth_factor(flow_date, end, spec)
    target = reference * factor + adjusted_flows
    profit_base = reference + plain_flows
    excess = value - target
    if spec.get("hwm") not in (None, False):
        # Srovnávací hodnota nesmí být nižší než HWM upravený o toky.
        excess = min(excess, value - (dec(spec["hwm"]) + plain_flows))
    if spec.get("require_positive_return") and value <= profit_base:
        excess = min(excess, ZERO)
    positive = max(excess, ZERO)
    if spec.get("hurdle_type", "hard") == "soft" and positive:
        # Měkká překážka s doháněním: po dosažení cíle se doplácí až do sazby z celého zisku.
        catch_up = dec(spec.get("catch_up") or 1)
        required_unit = min(catch_up * positive, rate * max(value - profit_base, ZERO))
    else:
        required_unit = rate * positive
    required = required_unit * multiplier
    if spec.get("average_base") not in (None, False):
        # Odměna ze zhodnocení nad benchmark násobená průměrným NAV místo počtu kusů.
        required = rate * (positive / reference) * dec(spec["average_base"])
    required *= dec(spec.get("probability") or 1)
    if spec.get("cap_rate") not in (None, False):
        required = min(required, dec(spec["cap_rate"]) * dec(spec.get("cap_base") or gross))
    if spec.get("net_floor") not in (None, False):
        required = min(required, max(gross - dec(spec["net_floor"]), ZERO))
    # Přesná částka pro společný dopočet (solve_fees ustaluje bez zaokrouhlení, zaokrouhluje se až zaúčtování).
    exact = required
    required = money(required)
    return {
        "required": required,
        "exact": exact,
        "move": required - money(accrued),
        "shortfall": money(max(-excess, ZERO) * multiplier),
        "target": str(target),
        "excess": str(excess),
        "factor": str(factor),
    }


# --- Společný dopočet úplat, výkonnostní odměny a daně (ZJ-12 B.1–B.5) ------------------------------------------------

STAGE_FEE, STAGE_PERFORMANCE, STAGE_TAX = 2, 3, 4


def _recipient_weights(item):
    weights = {code: dec(w) for code, w in (item.get("recipients") or {}).items()}
    total = sum(weights.values(), ZERO)
    return {code: w / total for code, w in weights.items()} if total else {}


def fee_effects(item, amount, ratios, transfers=None):
    """Změna hodnoty tříd a fondu, kterou způsobí položka s částkou `amount` (náklad kladný).

    Plátce třída: třída nese celou částku. Plátce fond (None): dělí se poměrem tříd. Podíl `share` jde přijímajícím
    třídám podle vah `recipients` (vnitřní zúčtování, FK nemění). Daň (`transfers`) přidá přesun daňového efektu tříd.
    Vrací (změna FK, {třída: změna}).
    """
    amount = dec(amount)
    payer = item.get("payer")
    share = dec(item.get("share")) if item.get("recipients") else ZERO
    effects = {}
    for code, rho in ratios.items():
        effects[code] = -(amount if payer == code else (rho * amount if payer is None else ZERO))
    for code, weight in _recipient_weights(item).items():
        effects[code] += amount * share * weight
    for code, move in (transfers or {}).items():
        effects[code] += move
    return -amount * (1 - share), effects


def fee_expense(item, amount):
    """Náklad mimo fond (do výsledku a daně); podíl přijímajícím třídám je vnitřní přesun."""
    share = dec(item.get("share")) if item.get("recipients") else ZERO
    return dec(amount) * (1 - share)


def _included(item, other, step):
    """Patří položka `other` do stavu po kroku `step` pro základ položky `item`? Odměna ani daň nikdy po sobě samé."""
    if other["stage"] > step:
        return False
    return not (other is item and item["stage"] >= STAGE_PERFORMANCE)


def _tax(spec, items, amounts, ratios):
    """Očekávaná daň (doplatek) a přesun daňového efektu specifických položek tříd (ZJ-12 B.4 a B.5).

    spec: rate, step (1–3: které náklady snižují základ), result (výsledek od začátku účetního období po kroku 1 už se zpět přičtenými
    náklady dřívějších ocenění, které podle kroku základ nesnižují), booked (zaúčtovaná daň od začátku účetního období), specific
    ({třída: specifické náklady od začátku účetního období před tímto oceněním, které základ snižují}), previous_effect ({třída: e × spec_c
    minulého ocenění v roce}), previous_effect_total (e × Σ spec minulého ocenění).
    Daňový efekt od začátku účetního období: E_c = e × spec_c, e = efektivní sazba specifických položek. Přesun je přírůstkový:
    přesun_c = ΔE_c − ρ_c × ΔΣE, Δ proti minulému ocenění, ρ dnešní. Dřívější přesuny se dnešním poměrem nepřepočítávají
    (stejně jako se dnes nepřepočítává daň rozdělená v minulých oceněních); součet přesunů je nula.
    """
    rate, step = dec(spec["rate"]), int(spec["step"])
    deductible = ZERO
    specific = {code: dec((spec.get("specific") or {}).get(code)) for code in ratios}
    for item in items:
        if item["stage"] == STAGE_TAX or item["stage"] > step:
            continue
        expense = fee_expense(item, amounts[item["key"]])
        deductible += expense
        if item.get("payer") is not None:
            specific[item["payer"]] += expense
    # Oprava základu daně (ZJ-12 B.7, ZJ-07 bod 2): kladná = připočitatelná, záporná = odčitatelná položka.
    base = dec(spec["result"]) - deductible + dec(spec.get("base_correction"))
    required = rate * max(base, ZERO)
    total_specific = sum(specific.values(), ZERO)
    effective = ZERO
    if total_specific:
        effective = (rate * max(base + total_specific, ZERO) - required) / total_specific
    previous = spec.get("previous_effect") or {}
    effect = {code: effective * specific[code] for code in ratios}
    effect_total = effective * total_specific
    change_total = effect_total - dec(spec.get("previous_effect_total"))
    transfers = {
        code: effect[code] - dec(previous.get(code)) - ratios[code] * change_total
        for code in ratios
    }
    return {
        "amount": required - dec(spec.get("booked")),
        "base": base, "required": required, "specific": specific, "effective_rate": effective,
        "effect": effect, "effect_total": effect_total, "transfers": transfers,
    }


def solve_fees(classes, items, pinned=None, max_steps=500, rel_tol=Decimal("1e-12")):
    """Společný dopočet úplat, výkonnostní odměny a daně jedné valuace (ZJ-12 B.1): iterace pevného bodu (Jacobi).

    classes: {třída: {"value": hodnota třídy po kroku 1, "ratio": poměr ρ}}; FK po kroku 1 = součet hodnot.
    items: položky v pevném pořadí, každá s
      key        jednoznačný klíč,
      stage      2 úplata, ruční úplata, oprava úplaty; 3 výkonnostní odměna a její oprava; 4 daň a její oprava,
      payer      třída, nebo None = fond (dělí se poměrem),
      share, recipients  podíl přijímajícím třídám a jejich váhy (ocenění je bere z hodnot tříd po kroku 1),
      base       None = základ nezávislý na dopočtu (aktiva, bez základu, pevná částka),
                 {"scope": "fund", "step": s} = FK po kroku s, {"scope": "class", "class": c, "step": s} = hodnota třídy,
      amount     funkce základ → přesná částka (bez zaokrouhlení); u pevné částky konstanta,
      tax        jen pravidlo daně (nejvýš jedno): popis podle _tax (místo base a amount); oprava daně je pevná
                 položka kroku 4 bez `tax` (plátce fond, do základu daně nevstupuje).
    Stav po kroku s obsahuje položky se stage ≤ s; „po kroku 2“ zahrnuje i úplatu samotnou, odměna a daň nikdy samy sebe.
    pinned: {klíč: pevná částka} (opravy, B.7). Tolerance relativní: rel_tol × max(1, největší částka).
    Vrací částky, základy, výsledek daně, počet kroků a zbytek konzistence (B.8); neustálí-li se, ValueError.
    """
    pinned = pinned or {}
    ratios = {code: dec(row["ratio"]) for code, row in classes.items()}
    values = {code: dec(row["value"]) for code, row in classes.items()}
    fund_value = sum(values.values(), ZERO)
    taxes = [item for item in items if item.get("tax")]
    if len(taxes) > 1:
        raise ValueError("Společný dopočet umí jedno pravidlo daně na fond.")

    def evaluate(amounts):
        tax = _tax(taxes[0]["tax"], items, amounts, ratios) if taxes else None
        effects = {}
        for item in items:
            transfers = tax["transfers"] if item.get("tax") else None
            effects[item["key"]] = fee_effects(item, amounts[item["key"]], ratios, transfers)
        bases, result = {}, {}
        for item in items:
            key = item["key"]
            if item.get("tax"):
                result[key] = tax["amount"]
            else:
                base = item.get("base")
                if base is not None:
                    step = int(base["step"])
                    included = [o["key"] for o in items if _included(item, o, step)]
                    if base["scope"] == "class":
                        base = values[base["class"]] + sum((effects[k][1][base["class"]] for k in included), ZERO)
                    else:
                        base = fund_value + sum((effects[k][0] for k in included), ZERO)
                bases[key] = base
                amount = item["amount"]
                result[key] = dec(amount(base) if callable(amount) else amount)
            if key in pinned:
                result[key] = dec(pinned[key])
        return result, bases, tax

    amounts = {item["key"]: ZERO for item in items}
    last = None
    for steps in range(1, max_steps + 1):
        updated, bases, tax = evaluate(amounts)
        scale = max([Decimal(1)] + [abs(v) for v in updated.values()])
        last = max([ZERO] + [abs(updated[k] - amounts[k]) for k in amounts])
        amounts = updated
        if last <= rel_tol * scale:
            break
    else:
        raise ValueError(f"Společný dopočet úplat se neustálil ani po {max_steps} krocích (poslední rozdíl {last}).")
    check, bases, tax = evaluate(amounts)
    scale = max([Decimal(1)] + [abs(v) for v in amounts.values()])
    residual = max([ZERO] + [abs(check[k] - amounts[k]) for k in amounts if k not in pinned])
    return {"amounts": amounts, "bases": bases, "tax": tax, "steps": steps, "residual": residual / scale}


def crystallise_on_redemption(accrued, redeemed_units, units_before):
    """Část dohadu odměny připadající na odkoupené kusy se stává splatnou."""
    return money(dec(accrued) * dec(redeemed_units) / dec(units_before))


def split_amount(amount, weights):
    """Rozdělí částku podle vah tak, aby součet přesně seděl; rozdíl nese největší váha."""
    amount = money(amount)
    total = sum(dec(w) for w in weights.values())
    if not total:
        raise ValueError("Součet vah je nula.")
    parts = {code: money(amount * dec(w) / total) for code, w in weights.items()}
    remainder = amount - sum(parts.values())
    if remainder:
        largest = max(sorted(parts), key=lambda code: dec(weights[code]))
        parts[largest] += remainder
    return parts


def waterfall(total_change, capitals, tiers, residual=None, residual_pro_rata=ZERO, loss_order=()):
    """Rozdělí změnu hodnoty mezi třídy podle pořadí nároků.

    tiers: seznam úrovní {třída: cílová částka}, vyplácí se postupně; nestačí-li, poměrem cílů.
    residual: pevné podíly zbytku; residual_pro_rata: část zbytku dělená podle kapitálů.
    loss_order: třídy, které nesou ztrátu přednostně do výše svého kapitálu; zbytek poměrem kapitálů.
    Vrací změnu za každou třídu, součet se přesně rovná total_change.
    """
    total_change = money(total_change)
    result = {code: ZERO for code in capitals}
    if total_change >= 0:
        remaining = total_change
        for tier in tiers:
            wanted = sum(dec(v) for v in tier.values())
            if not wanted or remaining <= 0:
                continue
            paid = min(remaining, wanted)
            for code, part in split_amount(paid, tier).items():
                result[code] += part
            remaining -= paid
        if remaining > 0:
            pro_rata = money(remaining * dec(residual_pro_rata))
            if pro_rata:
                for code, part in split_amount(pro_rata, capitals).items():
                    result[code] += part
            rest = remaining - pro_rata
            if rest:
                if not residual:
                    raise ValueError("Zbytek nemá určené příjemce.")
                for code, part in split_amount(rest, residual).items():
                    result[code] += part
        return result
    loss = -total_change
    pool = {code: dec(value) for code, value in capitals.items()}
    for code in loss_order:
        taken = min(loss, max(pool[code], ZERO))
        result[code] -= taken
        pool[code] -= taken
        loss -= taken
    if loss > 0:
        weights = {code: value for code, value in pool.items() if value > 0}
        for code, part in split_amount(loss, weights).items():
            result[code] -= part
    return result


def act_act_icma(start, end, period_start, period_end, frequency):
    """ACT/ACT ICMA: část kupónu za skutečné dny v kupónovém období krát počet kupónů ročně."""
    return Decimal((end - start).days) / (Decimal((period_end - period_start).days) * frequency)


def _present_value(rate, flows, start, basis):
    return sum(dec(amount) / (1 + rate) ** year_fraction(start, day, basis) for day, amount in flows)


def effective_rate(flows, basis="act365"):
    """Efektivní úroková míra: sazba, při níž je současná hodnota peněžních toků nulová.

    flows: seznam (datum, částka), první tok je pořízení se záporným znaménkem. Řeší se půlením intervalu.
    """
    flows = sorted(flows, key=lambda flow: flow[0])
    start = flows[0][0]
    low, high = Decimal("-0.99"), Decimal(10)
    if _present_value(low, flows, start, basis) * _present_value(high, flows, start, basis) > 0:
        raise ValueError("Peněžní toky nemají efektivní úrokovou míru v rozsahu výpočtu.")
    for _step in range(200):
        middle = (low + high) / 2
        value = _present_value(middle, flows, start, basis)
        if abs(value) < Decimal("0.0000001"):
            return middle
        if value * _present_value(low, flows, start, basis) > 0:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def amortised_cost(flows, day, rate=None, basis="act365"):
    """Naběhlá hodnota k datu: současná hodnota budoucích toků při efektivní úrokové míře."""
    rate = effective_rate(flows, basis) if rate is None else dec(rate)
    remaining = [(d, a) for d, a in flows if d > day]
    return money(sum(dec(a) / (1 + rate) ** year_fraction(day, d, basis) for d, a in remaining))


def amortised_cost_segments(cost, segments, day, basis="act365"):
    """Naběhlá hodnota s prospektivním přepočtem efektivní míry při změně toků (variabilní sazba, IM-11 varianta a).

    segments: [(od, toky)] vzestupně; první úsek začíná pořízením, další dnem změny sazby. Toky úseku jsou kalendář
    platný od jeho začátku. Úsek k: EIR_k z (od_k, −hodnota k od_k) a toků po od_k; hodnota ke konci úseku je současná
    hodnota toků úseku při EIR_k. Ke dnům před od_k se hodnota nemění a v od_k nevzniká skok.
    """
    used = [segment for index, segment in enumerate(segments) if index == 0 or segment[0] < day]
    value = dec(cost)
    for index, (start, flows) in enumerate(used):
        future = [(d, a) for d, a in flows if d > start]
        if not future:
            return money(ZERO)
        end = used[index + 1][0] if index + 1 < len(used) else day
        value = amortised_cost([(start, -value), *future], end, basis=basis)
    return value


def linear_accrual(purchase, redemption, start, end, day, basis="act365"):
    """Lineární rozpuštění rozdílu mezi pořizovací a splatnou částkou."""
    share = year_fraction(start, min(day, end), basis) / year_fraction(start, end, basis)
    return money(dec(purchase) + (dec(redemption) - dec(purchase)) * share)
