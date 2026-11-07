from odoo import SUPERUSER_ID, api

OLD_TYPES = {"derivative": "derivative_otc"}


def migrate(cr, version):
    """Převede dosavadní výběr typu na číselník a zachová hodnoty, podle kterých už se účtovalo."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    role = env.ref("investra_entity.role_instrument")
    cr.execute("SELECT id, instrument_type, ifrs9_category FROM investra_instrument WHERE type_id IS NULL")
    for instrument_id, old_type, category in cr.fetchall():
        kind = env.ref(f"investra_instruments.type_{OLD_TYPES.get(old_type, old_type)}")
        env["investra.instrument"].browse(instrument_id).write({
            "type_id": kind.id, "ifrs9_category": category, "valuation_method": "price", "role_id": role.id,
        })
