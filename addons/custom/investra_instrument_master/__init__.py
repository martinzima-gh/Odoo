from . import models


def post_init_hook(env):
    """Při instalaci do databáze s existujícími profily označí nejnovější verzi každé protistrany."""
    profiles = env["investra.counterparty.profile"].sudo().search([])
    profiles._refresh_latest(profiles.partner_id.ids)
