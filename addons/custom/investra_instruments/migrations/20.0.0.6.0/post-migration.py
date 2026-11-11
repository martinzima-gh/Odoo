from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Zdroj, fond a druh starých událostí obchodů podle klíče (plán docs/navrh-ucetni-udalosti.md, bod 7).

    Klíč `trade:<id>` je obchod nebo vypořádání při zachycení k datu vypořádání (druh zůstává Obchod),
    `trade-settle:<id>` je vypořádání dříve zachyceného obchodu (druh Vypořádání obchodu). Doklady se nemění.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    Trade = env["investra.trade"]
    for prefix, event_type in (("trade:", "trade"), ("trade-settle:", "trade_settlement")):
        events = env["investra.accounting.event"].search([("key", "=like", f"{prefix}%"), ("res_model", "=", False)])
        for event in events:
            trade = Trade.browse(int(event.key[len(prefix):].split("#")[0])).exists()
            values = {"event_type": event_type}
            if trade:
                values.update(res_model=Trade._name, res_id=trade.id, fund_id=trade.fund_id.id)
            event.write(values)
