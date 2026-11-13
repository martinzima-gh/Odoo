"""Sdílené nástroje a pravidlo knihy (rozhodnutí 2026-11-13): kontrola dat před jedinečností ISIN + měna.

Migrace data neopravuje: duplicitu, chybějící ISIN, sdílený nástroj bez ISIN nebo fondový nástroj s ISIN vypíše
a upgrade zastaví. Opravit je třeba v Odoo (ORM) a upgrade spustit znovu. ISIN se sjednotí (velká písmena, bez mezer).
"""

ISIN_TYPES = ("type_equity", "type_fund", "type_bond")
NORMALIZED = "NULLIF(upper(regexp_replace(i.isin, '\\s', '', 'g')), '')"


def migrate(cr, version):
    problems = []
    cr.execute(f"""
        SELECT {NORMALIZED}, i.currency_id, string_agg(i.id::text || ' ' || i.name, ', ' ORDER BY i.id)
          FROM investra_instrument i
         WHERE {NORMALIZED} IS NOT NULL
         GROUP BY 1, 2 HAVING count(*) > 1
    """)
    problems += [f"Duplicitní ISIN {isin} (měna id {currency}): {names}" for isin, currency, names in cr.fetchall()]
    cr.execute(f"""
        SELECT i.id, i.name FROM investra_instrument i
          JOIN ir_model_data d ON d.model = 'investra.instrument.type' AND d.res_id = i.type_id
         WHERE d.module = 'investra_instruments' AND d.name IN %s AND {NORMALIZED} IS NULL
    """, (ISIN_TYPES,))
    problems += [f"Chybí ISIN (typ ho vyžaduje): {iid} {name}" for iid, name in cr.fetchall()]
    cr.execute(f"SELECT i.id, i.name FROM investra_instrument i WHERE {NORMALIZED} IS NULL AND i.fund_id IS NULL")
    problems += [f"Nástroj bez ISIN nemá fond: {iid} {name}" for iid, name in cr.fetchall()]
    cr.execute(f"SELECT i.id, i.name FROM investra_instrument i WHERE {NORMALIZED} IS NOT NULL AND i.fund_id IS NOT NULL")
    problems += [f"Nástroj s ISIN má fond (sdílený nesmí): {iid} {name}" for iid, name in cr.fetchall()]
    if problems:
        raise Exception(
            "investra_instruments 20.0.0.14.0: před upgradem opravte nástroje (rozhodnutí 2026-11-13 "
            "„Sdílené nástroje a pravidlo knihy“):\n- " + "\n- ".join(problems)
        )
    cr.execute(f"UPDATE investra_instrument i SET isin = {NORMALIZED} WHERE i.isin IS NOT NULL")
