"""Variabilní sazba (úkol IM-11, rozhodnutí 2026-11-15): bez přepočtu dat.

Všechny stávající nástroje mají pevnou sazbu a všechny toky platí (nejsou odhad ani nahrazené). Odoo nové sloupce
s výchozí hodnotou vyplní samo; skript to pojistí jen u prázdných hodnot a ověří, že výpočty pevné sazby nic nemění:
žádný nástroj není variabilní, žádný tok není archivovaný ani odhad, žádné období sazby neexistuje.

Odchylka od návrhu (oddíl Migrace): období sazby se nezakládá u nástrojů s pevnou sazbou, ale až při přechodu na
variabilní sazbu; u pevné sazby by zastarávalo při každé změně pole Sazba %.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("UPDATE investra_instrument SET rate_type = 'fixed' WHERE rate_type IS NULL")
    filled_type = cr.rowcount
    cr.execute("UPDATE investra_instrument_cashflow SET active = TRUE WHERE active IS NULL")
    filled_active = cr.rowcount
    cr.execute("""
        SELECT (SELECT count(*) FROM investra_instrument),
               (SELECT count(*) FROM investra_instrument WHERE rate_type <> 'fixed'),
               (SELECT count(*) FROM investra_instrument_cashflow),
               (SELECT count(*) FROM investra_instrument_cashflow
                 WHERE NOT active OR estimated OR superseded_on IS NOT NULL OR introduced_on IS NOT NULL),
               (SELECT count(*) FROM investra_instrument_rate_period)
    """)
    instruments, variable, flows, changed, periods = cr.fetchone()
    if variable or changed or periods:
        raise Exception(
            "investra_nav 20.0.0.29.0: po upgradu má být vše s pevnou sazbou a toky beze změny "
            f"(variabilní {variable}, změněné toky {changed}, období sazeb {periods})."
        )
    _logger.info(
        "IM-11: nástrojů %s (vše pevná sazba, doplněno %s), toků %s (vše platné, doplněno %s), období sazeb 0.",
        instruments, filled_type, flows, filled_active,
    )
