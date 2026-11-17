"""ZJ-03 (rozhodnutí 2026-11-17 „Ručně doložené úplaty zjednodušeny“): druh pravidla „Výpočet mimo Odoo“ zaniká.

Ručně doložené úplaty a pravidla druhu `external` se smažou přes ORM (Martin 17. 11. 2026: v `investra` jsou jen
ukázková data). Před smazáním se vypíše počet. Ocenění, ke kterým ruční úplaty patřily, se vrátí k přepočtu
(zahodí se jejich nezaúčtované doklady). Zaúčtovaná ocenění migrace nemění: má-li pravidlo `external` rozpis
v ocenění, které není otevřené, migrace skončí chybou a nic nesmaže.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)
OPEN_STATES = ("draft", "computed")


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {"active_test": False})
    cr.execute("SELECT id FROM investra_fee_rule WHERE kind = 'external'")
    rule_ids = [row[0] for row in cr.fetchall()]
    cr.execute("SELECT id FROM investra_valuation_external")
    entry_ids = [row[0] for row in cr.fetchall()]
    _logger.info("ZJ-03: mažu %s ručně doložených úplat a %s pravidel druhu external.", len(entry_ids), len(rule_ids))
    if not rule_ids and not entry_ids:
        return
    entries = env["investra.valuation.external"].browse(entry_ids)
    cr.execute(
        "SELECT DISTINCT valuation_id FROM investra_valuation_fee WHERE rule_id = ANY(%s)", [rule_ids or [0]]
    )
    Valuation = env["investra.valuation"]
    valuations = entries.valuation_id | Valuation.browse([row[0] for row in cr.fetchall()])
    closed = valuations.filtered(lambda v: v.state not in OPEN_STATES)
    if closed:
        raise RuntimeError(
            "ZJ-03: ruční úplaty nebo pravidla external jsou v ocenění, které není otevřené: %s"
            % ", ".join(closed.mapped("display_name"))
        )
    for valuation in valuations.filtered(lambda v: v.state == "computed"):
        valuation._clear()
        valuation.state = "draft"
        _logger.info("ZJ-03: ocenění %s vráceno k přepočtu.", valuation.display_name)
    entries.unlink()
    env["investra.fee.rule"].browse(rule_ids).unlink()
