"""SPPI je vlastnost nástroje (úkol IM-05, rozhodnutí uživatele 15. 11. 2026): snímek zařazení před upgradem.

Snímek drží hodnoty SPPI a kategorie IFRS 9 všech zařazení, aby post-migrace mohla hodnoty přenést na nástroj
a ověřit, že se kategorie žádného zařazení nezměnila. Post-migrace snímek smaže.
"""

SNAPSHOT = "investra_im05_sppi_snapshot"


def migrate(cr, version):
    cr.execute(f"DROP TABLE IF EXISTS {SNAPSHOT}")
    cr.execute(f"""
        CREATE TABLE {SNAPSHOT} AS
        SELECT id, instrument_id, instrument_nature, sppi, sppi_note, sppi_version, valid_from,
               coalesce(write_uid, create_uid) AS user_id, mandatory_category, computed_category, ifrs9_category
          FROM investra_portfolio_classification
    """)
