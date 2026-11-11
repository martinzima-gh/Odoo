def migrate(cr, version):
    """Splátky dostanou obchodní model (plán docs/navrh-klasifikace-ifrs9.md).

    Řádky listu portfolio hotových ocenění jsou historický snímek, proto se nedoplňují (pole zůstanou prázdná).

    Portfolio splátky = portfolio obchodů téhož fondu a nástroje (migrace investra_instruments 20.0.0.4.0
    dává všechny obchody jedné dvojice fond + nástroj do jednoho portfolia). Částky se nemění.
    """
    cr.execute("""
        UPDATE investra_instrument_repayment r SET portfolio_id = t.portfolio_id
          FROM (SELECT DISTINCT ON (fund_id, instrument_id) fund_id, instrument_id, portfolio_id
                  FROM investra_trade ORDER BY fund_id, instrument_id, id) t
         WHERE r.fund_id = t.fund_id AND r.instrument_id = t.instrument_id AND r.portfolio_id IS NULL
    """)
    cr.execute("SELECT count(*) FROM investra_instrument_repayment WHERE portfolio_id IS NULL")
    if not cr.fetchone()[0]:
        cr.execute("ALTER TABLE investra_instrument_repayment ALTER COLUMN portfolio_id SET NOT NULL")
