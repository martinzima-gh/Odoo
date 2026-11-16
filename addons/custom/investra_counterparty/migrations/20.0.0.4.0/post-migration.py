"""Údaje protistrany bez historie (MN-09, rozhodnutí 2026-11-16): jeden záznam na kontakt.

Má-li kontakt víc záznamů, zůstává nejnovější (největší „Platí od“, pak nejvyšší id); hodnoty starších se zapíšou jako
poznámka do historie ponechaného záznamu a starší se odstraní přes ORM. Omezení unique(partner_id) Odoo při upgradu
odloží, dokud duplicity existují, a přidá ho na konci upgradu (po této migraci). Sloupce valid_from a is_latest odstraní
Odoo na konci upgradu spolu s definicemi zrušených polí."""

import logging

from markupsafe import Markup, escape

from odoo import SUPERUSER_ID, api
from odoo.tools import sql

_logger = logging.getLogger(__name__)

TABLE = "investra_counterparty_profile"


def _describe(cr, ids):
    """Popis hodnot záznamů přímo z tabulky: pole modulu emitentů (kód ESA, stav kontroly, důvod změny) v té chvíli
    nemusí být v registru načtená, sloupce ale v tabulce jsou."""
    columns = {name: sql.column_exists(cr, TABLE, name)
               for name in ("valid_from", "esa_code_id", "review_state", "change_reason")}
    cr.execute(f"""
        SELECT p.id, {"p.valid_from::text" if columns["valid_from"] else "NULL"}, c.code, s.code || ' ' || s.name, p.lei,
               {"e.code" if columns["esa_code_id"] else "NULL"},
               {"p.review_state" if columns["review_state"] else "NULL"},
               {"p.change_reason" if columns["change_reason"] else "NULL"}
          FROM {TABLE} p
          LEFT JOIN res_country c ON c.id = p.country_id
          LEFT JOIN investra_esa_sector s ON s.id = p.sector_id
          {"LEFT JOIN investra_esa_code e ON e.id = p.esa_code_id" if columns["esa_code_id"] else ""}
         WHERE p.id = ANY(%s)""", [list(ids)])
    return {
        row[0]: (
            f"Platí od: {row[1] or '–'}; Země: {row[2] or '–'}; Sektor ESA 2010: {row[3] or '–'}; LEI: {row[4] or '–'}; "
            f"Kód sektoru ESA: {row[5] or '–'}; Stav kontroly: {row[6] or '–'}; Důvod změny: {row[7] or '–'}"
        )
        for row in cr.fetchall()
    }


def merge_duplicates(env):
    """Sloučí víc záznamů téhož kontaktu do nejnovějšího. Vrací počet odstraněných záznamů."""
    cr = env.cr
    has_date = sql.column_exists(cr, TABLE, "valid_from")
    order = "valid_from DESC NULLS LAST, id DESC" if has_date else "id DESC"
    cr.execute(f"SELECT partner_id, array_agg(id ORDER BY {order}) FROM {TABLE} GROUP BY partner_id HAVING count(*) > 1")
    groups = cr.fetchall()
    Profile = env["investra.counterparty.profile"].sudo()
    removed = 0
    for partner_id, ids in groups:
        keep, older = Profile.browse(ids[0]), Profile.browse(ids[1:])
        texts = _describe(cr, ids)
        items = Markup("").join(Markup("<li>%s</li>") % texts[profile_id] for profile_id in ids[1:])
        keep.message_post(
            body=Markup("<p>%s</p><ul>%s</ul>") % (
                escape("Sloučení údajů protistrany (MN-09): ponechán nejnovější záznam "
                       f"({texts[keep.id]}); hodnoty starších záznamů:"), items),
            subtype_xmlid="mail.mt_note",
        )
        _logger.warning("MN-09: kontakt %s – ponechán záznam %s, odstraněny %s", partner_id, keep.id, older.ids)
        removed += len(older)
        older.unlink()
    return removed


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    removed = merge_duplicates(env)
    _logger.info("MN-09: odstraněno %s starších záznamů údajů protistrany", removed)
