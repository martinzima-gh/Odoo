def migrate(cr, version):
    """Uloží dosavadní kategorie zařazení; post-migrace je po přepočtu porovná (dodatek plánu 2026-11-11)."""
    cr.execute("SELECT to_regclass('investra_portfolio_classification')")
    if not cr.fetchone()[0]:
        return
    cr.execute("DROP TABLE IF EXISTS investra_mig_ifrs9_snapshot")
    cr.execute("CREATE TABLE investra_mig_ifrs9_snapshot AS SELECT id, ifrs9_category FROM investra_portfolio_classification")
