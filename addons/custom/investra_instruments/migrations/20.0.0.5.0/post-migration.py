from odoo import SUPERUSER_ID, api

NATURE_BY_KIND = {
    "bond": "debt", "loan": "debt", "deposit": "debt", "repo": "debt",
    "equity": "equity", "other_holding": "equity", "fund": "puttable",
    "derivative": "derivative", "participation": "participation",
}
SPPI_NOTE = "Převzato migrací z dřívější klasifikace nástroje; potvrdit posouzení SPPI."


def migrate(cr, version):
    """Klasifikace s oddělenými kroky (a)–(f) podle dodatku plánu docs/navrh-klasifikace-ifrs9.md.

    Model „Ostatní“ -> Řízení na reálnou hodnotu; povaha nástroje z druhu typu; u vyhodnoceného SPPI poznámka a znění.
    Kategorie se přepočítá a porovná s uloženou; při rozdílu se aktualizace zastaví (nic se tiše nemění).
    """
    cr.execute("UPDATE investra_fund_portfolio SET business_model = 'fair_value' WHERE business_model = 'other'")
    cr.execute("SELECT to_regclass('investra_mig_ifrs9_snapshot')")
    if not cr.fetchone()[0]:
        return
    for kind, nature in NATURE_BY_KIND.items():
        cr.execute("""
            UPDATE investra_portfolio_classification c SET instrument_nature = %s
              FROM investra_instrument i JOIN investra_instrument_type t ON t.id = i.type_id
             WHERE c.instrument_id = i.id AND t.kind = %s AND c.instrument_nature IS NULL
        """, (nature, kind))
    cr.execute("UPDATE investra_portfolio_classification SET sppi_note = %s WHERE sppi <> 'na' AND sppi_note IS NULL", (SPPI_NOTE,))
    cr.execute("""
        UPDATE investra_portfolio_classification SET designation_note = 'Převzato migrací z dřívější klasifikace nástroje; potvrdit.'
         WHERE designation <> 'none' AND designation_note IS NULL
    """)
    env = api.Environment(cr, SUPERUSER_ID, {})
    Classification = env["investra.portfolio.classification"]
    records = Classification.with_context(active_test=False).search([])
    records.invalidate_model()
    for record in records.filtered(lambda r: r.sppi != "na" and not r.sppi_version):
        cr.execute(
            "UPDATE investra_portfolio_classification SET sppi_version = %s WHERE id = %s",
            (Classification._default_sppi_version(record.portfolio_id, record.valid_from), record.id),
        )
    records.invalidate_model()
    for name in ("mandatory_category", "computed_category", "ifrs9_category", "classification_basis"):
        env.add_to_compute(Classification._fields[name], records)
    records.flush_recordset()
    cr.execute("""
        SELECT c.id, s.ifrs9_category, c.ifrs9_category FROM investra_portfolio_classification c
          JOIN investra_mig_ifrs9_snapshot s ON s.id = c.id WHERE s.ifrs9_category IS DISTINCT FROM c.ifrs9_category
    """)
    changed = cr.fetchall()
    if changed:
        raise RuntimeError(f"Migrace by změnila kategorii IFRS 9 u zařazení {changed}; aktualizace zastavena.")
    records._check_classification()
    cr.execute("DROP TABLE investra_mig_ifrs9_snapshot")
    cr.execute("SELECT count(*) FROM investra_portfolio_classification WHERE instrument_nature IS NULL")
    if not cr.fetchone()[0]:
        cr.execute("ALTER TABLE investra_portfolio_classification ALTER COLUMN instrument_nature SET NOT NULL")
