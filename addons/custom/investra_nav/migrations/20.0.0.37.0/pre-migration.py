"""ZJ-12 krok 2 (rozhodnutí 2026-11-18 „Základ úplat, odměny a daně“): `base_mode` a `perf_base` → `base_step`.

Odoo 20 při upgradu smaže sloupce zrušených polí (rozhodnutí 2026-11-17 „Zrušená pole a sloupce databáze“), proto
se hodnoty převedou před načtením modelu do nového sloupce `base_step`. Odoo pak sloupec najde a výchozí výpočet
(`_compute_base_step`) nad existujícími záznamy nespustí.

Převod (zadání ZJ-12, část D.1), výsledky stávajících pravidel se nemění:
- pravidla daně → 3 (dnešní chování: úplaty i odměna snižují základ),
- výkonnostní odměna podle `perf_base`: before_fees → 1, after_fees → 2, after_tax → 4,
- časově rozlišená úplata ze základu FK nebo kapitál třídy podle `base_mode`: before → 1, after → 2,
- aktiva, bez základu a průměrný FK → 1 (dnes počítají vždy „před“).
Neznámá hodnota migraci zastaví, aby se pravidlo tiše nepřevedlo jinak.
"""

import logging

_logger = logging.getLogger(__name__)

PERF = {"before_fees": "1", "after_fees": "2", "after_tax": "4"}
PERIODIC = {"before": "1", "after": "2"}


def base_step_for(kind, base_source, base_mode, perf_base):
    """Krok základu ze starého nastavení; None = neznámá hodnota (migrace se zastaví). Testuje `test_fee_base_step`."""
    if kind == "tax":
        return "3"
    if kind == "performance":
        return PERF.get(perf_base)
    if base_source in ("fk", "class_fk"):
        return PERIODIC.get(base_mode)
    return "1"


def _columns(cr):
    cr.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'investra_fee_rule' "
        "AND column_name IN ('base_mode', 'perf_base', 'base_step')"
    )
    return {row[0] for row in cr.fetchall()}


def migrate(cr, version):
    columns = _columns(cr)
    if "base_step" in columns:
        _logger.info("ZJ-12: sloupec base_step už existuje, převod přeskočen.")
        return
    if not {"base_mode", "perf_base"} <= columns:
        raise RuntimeError("ZJ-12: chybí sloupce base_mode nebo perf_base, převod na base_step nejde provést.")
    cr.execute("SELECT id, kind, base_source, base_mode, perf_base FROM investra_fee_rule ORDER BY id")
    rows = cr.fetchall()
    values, unknown = {}, []
    for rule_id, kind, base_source, base_mode, perf_base in rows:
        step = base_step_for(kind, base_source, base_mode, perf_base)
        if step is None:
            unknown.append((rule_id, kind, base_source, base_mode, perf_base))
        values[rule_id] = step
    if unknown:
        raise RuntimeError("ZJ-12: neznámé nastavení základu u pravidel %s" % unknown)
    cr.execute("ALTER TABLE investra_fee_rule ADD COLUMN base_step varchar")
    for step in sorted(set(values.values())):
        ids = [rule_id for rule_id, value in values.items() if value == step]
        cr.execute("UPDATE investra_fee_rule SET base_step = %s WHERE id = ANY(%s)", [step, ids])
        _logger.info("ZJ-12: base_step = %s u pravidel %s.", step, ids)
    _logger.info("ZJ-12: převedeno %s pravidel na base_step.", len(values))
