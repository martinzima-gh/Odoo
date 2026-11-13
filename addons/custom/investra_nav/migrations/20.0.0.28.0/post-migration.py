"""Profil přecenění pro stávající fondy (rozhodnutí 2026-11-13, varianta A).

Ocenění přeceňuje účty profilů přecenění knihy; nový fond profil dostane při založení. Stávajícím fondům, jejichž kniha
profil nemá, se založí s bankami a závazkem z úplat. Doklady ani dřívější ocenění se nemění. Opakovatelné.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["investra.fund"].with_context(active_test=False).search([])._ensure_fx_profile()
