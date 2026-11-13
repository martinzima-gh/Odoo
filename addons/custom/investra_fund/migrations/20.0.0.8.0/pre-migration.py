"""Příjemce poplatku jedním výběrem (rozhodnutí 2026-11-13).

U fondů i tříd se příjemce „Třída“ převede podle dosavadního zaškrtávátka „do kapitálu“:
zaškrtnuto = class_capital (Třída – kapitál), jinak class_income (Třída – výnos). Ostatní příjemci se nemění.
Běží před načtením polí; sloupce entry/exit_fee_capital pak Odoo 20 při upgradu odstraní.
Opakovatelné: mění jen hodnotu „class“.
"""


def migrate(cr, version):
    for table in ("investra_fund", "investra_fund_class"):
        for kind in ("entry", "exit"):
            cr.execute(
                "SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s",
                (table, f"{kind}_fee_capital"),
            )
            capital = "COALESCE({0}_fee_capital, FALSE)".format(kind) if cr.fetchone() else "FALSE"
            cr.execute(f"""
                UPDATE {table}
                   SET {kind}_fee_recipient = CASE WHEN {capital} THEN 'class_capital' ELSE 'class_income' END
                 WHERE {kind}_fee_recipient = 'class'
            """)
