"""Vypuštění kalendáře ocenění (MN-14, rozhodnutí 2026-11-16).

Model `investra.valuation.calendar` zaniká; Odoo při povýšení odstraní jeho záznam v `ir.model`. Tabulku tu
pro jistotu odstraníme dřív, ale jen když je prázdná (v investra byla 16. 11. 2026 prázdná). Plná tabulka
zastaví povýšení, aby se plánovaná data nepřišla beze stopy.
"""


def migrate(cr, version):
    cr.execute("SELECT to_regclass('investra_valuation_calendar')")
    if not cr.fetchone()[0]:
        return
    cr.execute("SELECT COUNT(*) FROM investra_valuation_calendar")
    rows = cr.fetchone()[0]
    if rows:
        raise RuntimeError(f"Kalendář ocenění obsahuje {rows} řádků; před povýšením je vyřeš s Martinem.")
    cr.execute("DROP TABLE investra_valuation_calendar")
