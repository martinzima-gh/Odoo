"""Převod schvalovací matice na matici pro celou aplikaci (ZJ-01, rozhodnutí 2026-11-17).

Volá se z pre-migrace `investra_fund` 20.0.0.10.0 a `investra_nav` 20.0.0.32.0; samostatně kvůli testům.
Pracuje jen SQL nad sloupci, které po odstranění polí v databázi zůstávají (Odoo sloupce nemaže).
"""

import logging

_logger = logging.getLogger(__name__)

# Názvy rolí před ZJ-01; do textových sloupců se ukládají místo kódů.
OLD_ROLE_LABELS = {"preparer": "Příprava ocenění", "approver": "Schvalování ocenění"}
MATRIX_REFERENCES = ("investra_approval_log", "investra_approval_request", "investra_valuation_approval")


def _column_exists(cr, table, column):
    cr.execute("SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s", (table, column))
    return bool(cr.fetchone())


def _table_exists(cr, table):
    cr.execute("SELECT to_regclass(%s)", (table,))
    return bool(cr.fetchone()[0])


def merge_matrix_rows(cr):
    """Řádky obhospodařovatele převede na globální. Vrátí seznam hlášení (i do logu).

    - Řádek zpřísnění fondu nesmí existovat: převod zastaví (rozhodnutí patří Martinovi).
    - Více řádků se stejnou činností a „Platí od“ (obhospodařovatelé navzájem nebo s globálním řádkem): zůstane
      řádek s nejvyšším id, odkazy z úkonů, žádostí a schválení ocenění se na něj převedou, ostatní se smažou
      i se svými kroky a ohlásí.
    """
    messages = []
    if not _table_exists(cr, "investra_approval_matrix"):
        return messages
    if _column_exists(cr, "investra_approval_matrix", "fund_id"):
        cr.execute("SELECT id, activity, fund_id FROM investra_approval_matrix WHERE fund_id IS NOT NULL ORDER BY id")
        fund_rows = cr.fetchall()
        if fund_rows:
            raise RuntimeError(
                f"Schvalovací matice má {len(fund_rows)} řádků zpřísnění fondu (id {[r[0] for r in fund_rows]}); "
                "ZJ-01 je nepřevádí. Před povýšením je vyřeš s Martinem."
            )
    if not _column_exists(cr, "investra_approval_matrix", "manager_id"):
        return messages
    cr.execute("""
        SELECT activity, valid_from, array_agg(id ORDER BY id)
          FROM investra_approval_matrix
         GROUP BY activity, valid_from
        HAVING count(*) > 1
         ORDER BY activity, valid_from
    """)
    for activity, day, ids in cr.fetchall():
        keep, drop = ids[-1], tuple(ids[:-1])
        for table in MATRIX_REFERENCES:
            if _table_exists(cr, table):
                cr.execute(f"UPDATE {table} SET matrix_id = %s WHERE matrix_id IN %s", (keep, drop))  # noqa: S608
        cr.execute("DELETE FROM investra_approval_matrix_step WHERE matrix_id IN %s", (drop,))
        cr.execute("DELETE FROM ir_model_data WHERE model = 'investra.approval.matrix' AND res_id IN %s", (drop,))
        cr.execute("DELETE FROM investra_approval_matrix WHERE id IN %s", (drop,))
        messages.append(
            f"Matice {activity} od {day}: více řádků ({list(ids)}), ponechán novější id {keep}, smazány {list(drop)}."
        )
    cr.execute("""
        UPDATE investra_approval_matrix SET manager_id = NULL
         WHERE manager_id IS NOT NULL
     RETURNING id, activity, valid_from
    """)
    converted = cr.fetchall()
    if converted:
        messages.append(
            f"Řádky obhospodařovatele převedeny na globální: {len(converted)} "
            f"({', '.join(f'{a} od {d} (id {i})' for i, a, d in sorted(converted))})."
        )
    for message in messages:
        _logger.warning("ZJ-01: %s", message)
    return messages


def role_codes_to_text(cr, table, column):
    """Kód role před ZJ-01 (preparer / approver) v textovém sloupci nahradí jejím názvem. Vrátí počet řádků."""
    if not _column_exists(cr, table, column):
        return 0
    count = 0
    for code, label in OLD_ROLE_LABELS.items():
        cr.execute(f"UPDATE {table} SET {column} = %s WHERE {column} = %s", (label, code))  # noqa: S608
        count += cr.rowcount
    if count:
        _logger.info("ZJ-01: %s.%s – %s kódů role převedeno na text.", table, column, count)
    return count
