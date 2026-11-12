"""Splátka má jistinu a úrok (rozhodnutí 2026-11-12 „Splátky jistiny nástrojů“).

Dosavadní splátky měly jen celkovou částku; celá se převede na jistinu, úrok 0, takže částka (nově součet) se nemění.
Zaúčtované doklady se nemění (staré splátky dál nesou MD banka; nové účtují na inkasa na cestě).
"""


def migrate(cr, version):
    cr.execute("ALTER TABLE investra_instrument_repayment ADD COLUMN IF NOT EXISTS principal_amount numeric")
    cr.execute("ALTER TABLE investra_instrument_repayment ADD COLUMN IF NOT EXISTS interest_amount numeric")
    cr.execute("""
        UPDATE investra_instrument_repayment
           SET principal_amount = amount, interest_amount = 0
         WHERE principal_amount IS NULL
    """)
