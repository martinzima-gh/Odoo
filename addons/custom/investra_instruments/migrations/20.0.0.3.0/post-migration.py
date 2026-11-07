from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Dosavadní zaúčtované obchody šly přímo proti bance, jsou tedy vypořádané."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["investra.trade"].search([("event_id", "!=", False)]).write({"state": "settled"})
