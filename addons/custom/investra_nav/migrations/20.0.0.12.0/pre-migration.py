"""Mimořádná splátka jedním druhem (rozhodnutí 2026-11-12 „Mimořádná splátka nástroje“, úprava formuláře).

Druhy „Mimořádná – poměrné snížení“ a „Předčasné ukončení“ se slučují do druhu „Mimořádná“; předčasné ukončení
nese zaškrtávátko Uzavírá pozici. Doklady se nemění.
"""


def migrate(cr, version):
    cr.execute("ALTER TABLE investra_instrument_repayment ADD COLUMN IF NOT EXISTS closes_position boolean")
    cr.execute("""
        UPDATE investra_instrument_repayment
           SET closes_position = (kind = 'early_termination'), kind = 'extraordinary'
         WHERE kind IN ('prorata', 'early_termination')
    """)
