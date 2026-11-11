from odoo import SUPERUSER_ID, api

SOURCES = (
    ("movement:", "investra.class.movement", "class_movement"),
    ("repayment:", "investra.instrument.repayment", "repayment"),
    ("valuation:", "investra.valuation", "valuation"),
)


def migrate(cr, version):
    """Zdroj, fond a druh starých událostí úpisů a odkupů, splátek a ocenění podle klíče
    (plán docs/navrh-ucetni-udalosti.md, bod 7). Splátky měly druh Obchod, nově Splátka. Doklady se nemění.

    Klíč ocenění je `valuation:<id>:<běh>:<druh>`, u zrušeného návrhu s příponou `#discarded<id>`.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    for prefix, model, event_type in SOURCES:
        Source = env[model]
        events = env["investra.accounting.event"].search([("key", "=like", f"{prefix}%"), ("res_model", "=", False)])
        for event in events:
            source = Source.browse(int(event.key[len(prefix):].split(":")[0].split("#")[0])).exists()
            values = {"event_type": event_type}
            if source:
                values.update(res_model=model, res_id=source.id, fund_id=source.fund_id.id)
            event.write(values)
