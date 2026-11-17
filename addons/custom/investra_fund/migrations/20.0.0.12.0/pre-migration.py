"""ZJ-03 (rozhodnutí 2026-11-17 „Poplatky fondu a tříd“): vstupní a výstupní poplatek jen na třídě.

Sazby třídy jsou nově povinné (výchozí 0): prázdné hodnoty se před aktualizací schématu doplní nulou.
Výchozí sazby a příjemci fondu zanikají; výpočet úpisu a odkupu četl už jen třídu, takže se nic nepřepočítává.
Sloupce fondu Odoo při upgradu odstraní.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    for column in ("entry_fee_rate", "exit_fee_rate"):
        cr.execute(f"UPDATE investra_fund_class SET {column} = 0 WHERE {column} IS NULL")
        if cr.rowcount:
            _logger.info("ZJ-03: %s tříd mělo prázdné %s, doplněna 0.", cr.rowcount, column)
