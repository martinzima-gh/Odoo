"""Příjemce poplatku jedním výběrem (rozhodnutí 2026-11-13).

U pohybů (i zaúčtovaných) se příjemce „Třída“ převede podle dosavadního zaškrtávátka fee_to_capital:
zaškrtnuto = class_capital (Třída – kapitál), jinak class_income (Třída – výnos). Zaúčtování se nemění,
mění se jen způsob zápisu stejného údaje. Běží před načtením polí; sloupec fee_to_capital pak Odoo 20 při upgradu odstraní. Opakovatelné.
"""


def migrate(cr, version):
    cr.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_name = 'investra_class_movement' AND column_name = 'fee_to_capital'"
    )
    capital = "COALESCE(fee_to_capital, FALSE)" if cr.fetchone() else "FALSE"
    cr.execute(f"""
        UPDATE investra_class_movement
           SET fee_recipient = CASE WHEN {capital} THEN 'class_capital' ELSE 'class_income' END
         WHERE fee_recipient = 'class'
    """)
