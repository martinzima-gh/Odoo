"""Příjemce vstupního a výstupního poplatku (rozhodnutí 2026-11-13).

Dřívější společný příjemce fee_recipient se zkopíruje do nových sloupců entry_fee_recipient a exit_fee_recipient
u fondů i tříd. Zaškrtávátka „do kapitálu“ zůstanou prázdná (Odoo je doplní jako nepravda). Jiná data se nemění,
starý sloupec zůstává pro historii. Opakovatelné: kopíruje jen do prázdných hodnot.
"""


def migrate(cr, version):
    for table in ("investra_fund", "investra_fund_class"):
        cr.execute("SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = 'fee_recipient'", (table,))
        if not cr.fetchone():
            continue
        for column in ("entry_fee_recipient", "exit_fee_recipient"):
            cr.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} varchar")
            cr.execute(f"UPDATE {table} SET {column} = fee_recipient WHERE {column} IS NULL")
