"""Stav splátky (rozhodnutí 2026-11-12 „Zámek a storno splátky“).

Nový sloupec state dostane u všech splátek výchozí Návrh; splátka s účetní událostí je zaúčtovaná.
Storno splátky dosud neexistovalo, stornovaná splátka proto být nemůže. Mění jen nový sloupec.
"""


def migrate(cr, version):
    cr.execute("UPDATE investra_instrument_repayment SET state = 'posted' WHERE event_id IS NOT NULL AND state = 'draft'")
