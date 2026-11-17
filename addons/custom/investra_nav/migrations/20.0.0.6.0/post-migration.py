import logging

_logger = logging.getLogger(__name__)


def _exists(cr, table, column=None):
    if column:
        cr.execute("SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s", (table, column))
    else:
        cr.execute("SELECT 1 FROM information_schema.tables WHERE table_name = %s", (table,))
    return bool(cr.fetchone())


def migrate(cr, version):
    """Původně převod `second_person_required` a kroků schválení fondu do schvalovací matice (rozhodnutí
    2026-11-11). Od ZJ-01 (rozhodnutí 2026-11-17) matice řádky fondu nezná, takže převod jen ohlásí fondy
    s vlastními kroky. Doklady a ocenění se nemění.
    """
    # ZJ-01 (rozhodnutí 2026-11-17): matice už nemá řádky fondu ani nejnižší role, proto se kroky fondu nepřevádějí;
    # jen se ohlásí. Všechny databáze projektu jsou za touto verzí, převod proběhl v době, kdy matice fondy znala.
    if _exists(cr, "investra_fund_approval_step"):
        cr.execute("SELECT DISTINCT fund_id FROM investra_fund_approval_step ORDER BY fund_id")
        for (fund_id,) in cr.fetchall():
            _logger.warning(
                "Fond %s měl vlastní kroky schválení; matice je od ZJ-01 společná pro celou aplikaci, "
                "kroky se nepřevádějí. Pravidlo nastavte řádkem schvalovací matice.", fund_id,
            )
