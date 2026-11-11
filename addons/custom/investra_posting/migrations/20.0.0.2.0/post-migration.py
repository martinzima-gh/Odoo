from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Částky starých událostí z jejich dokladu (plán docs/navrh-ucetni-udalosti.md, bod 7).

    Funkční měna = součet MD. Původní měna jen tehdy, mají-li řádky v cizí měně jednu měnu; částka je větší ze součtu
    kladných a absolutní hodnoty součtu záporných částek (stejně jako `_amounts` u nových událostí).
    Zrušené návrhy doklad nemají, částka zůstane prázdná. Doklady se nemění.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    events = env["investra.accounting.event"].search([("move_id", "!=", False)])
    for event in events:
        lines = event.move_id.line_ids
        values = {"amount": sum(lines.mapped("debit"))}
        foreign = lines.filtered(lambda line: line.currency_id != event.company_id.currency_id)
        if len(foreign.currency_id) == 1:
            amounts = foreign.mapped("amount_currency")
            foreign_amount = max(sum(a for a in amounts if a > 0), -sum(a for a in amounts if a < 0))
            if foreign_amount:
                values.update(foreign_currency_id=foreign.currency_id.id, amount_currency=foreign_amount)
        event.write(values)
