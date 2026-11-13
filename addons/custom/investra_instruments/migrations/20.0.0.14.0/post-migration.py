"""Sdílené nástroje a pravidlo knihy (rozhodnutí 2026-11-13): typy, kniha, kód a identifikátor existujících nástrojů.

- Typy z dat modulu (noupdate) dostanou prefix kódu a příznak „Vyžaduje ISIN“.
- Kniha: nástroj fondu = kniha fondu; sdílený = kniha investiční společnosti, jinak prázdná (převezme ji založení knihy).
- Kód: prefix typu + číslo z řady, v pořadí id.
- Nástroj bez ISIN nemá identifikátor: dostane druh „Jiný“ a jako hodnotu svůj nový kód, s poznámkou v historii.
  Skutečný identifikátor (číslo smlouvy, IČO/LEI) doplní účetní; migrace ho nevymýšlí.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

TYPES = {
    "type_equity": ("AKC", True), "type_fund": ("PL", True), "type_bond": ("DLU", True), "type_deposit": ("TV", False),
    "type_repo": ("REPO", False), "type_loan": ("UVR", False), "type_participation": ("UCA", False),
    "type_derivative_listed": ("DER", False), "type_derivative_otc": ("OTC", False), "type_other_holding": ("POD", False),
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid, (prefix, required) in TYPES.items():
        kind = env.ref(f"investra_instruments.{xmlid}", raise_if_not_found=False)
        if kind:
            kind.write({"code_prefix": prefix, "isin_required": required})
    Instrument = env["investra.instrument"].with_context(active_test=False, tracking_disable=True)
    shared_company = Instrument._shared_company()
    Sequence = env["ir.sequence"]
    for instrument in Instrument.search([], order="id"):
        vals = {
            "company_id": instrument.fund_id.company_id.id if instrument.fund_id else shared_company.id,
            "code": f"{instrument.type_id.code_prefix or 'NAS'}-{Sequence.next_by_code('investra.instrument')}",
        }
        if not instrument.isin and not instrument.identifier:
            vals.update(identifier_kind="other", identifier=vals["code"])
        instrument.write(vals)
        if vals.get("identifier"):
            instrument.message_post(body="Migrace 2026-11-13: identifikátor doplněn kódem nástroje; doplňte skutečný "
                                         "(číslo smlouvy, IČO nebo LEI).")
            _logger.warning("Nástroj %s (%s) bez ISIN: identifikátor doplněn kódem, doplnit skutečný.", instrument.id, instrument.name)
