"""ZJ-22: dividenda cenného papíru. Existující řádky dividend se zařadí pod událost podle nástroje a ex-data.

Událost (`investra.dividend.event`) se založí z prvního řádku skupiny (nástroj, ex-datum): datum výplaty, dividenda na kus, druh
a sazby. Stornované řádky patří vlastní události, aby nebránily nové (jedna aktivní událost na nástroj a ex-datum).
Řádky se nemění jinak než odkazem na událost (bez sledování změn).
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {"tracking_disable": True})
    Line, Event = env["investra.dividend"], env["investra.dividend.event"]
    groups = {}
    for line in Line.search([("dividend_event_id", "=", False)], order="id"):
        key = (line.instrument_id.id, line.ex_date, line.state == "reversed")
        groups[key] = groups.get(key, Line) | line
    for (instrument_id, ex_date, _reversed), group in sorted(groups.items(), key=lambda item: item[0][2]):
        first = group[0]
        Event.create({
            "instrument_id": instrument_id, "ex_date": ex_date, "pay_date": first.pay_date, "per_share": first.per_share,
            "kind": first.kind, "withholding_rate": first.withholding_rate, "treaty_rate": first.treaty_rate,
            "line_ids": [(6, 0, group.ids)],
        })
