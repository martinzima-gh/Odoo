"""Identifikátory nástrojů pro testy (rozhodnutí 2026-11-13 „Sdílené nástroje a pravidlo knihy“).

Typ s povinným ISIN dostane fiktivní jedinečný ISIN (sdílený nástroj); jiný typ fond a číslo smlouvy (nástroj fondu).
Hodnoty zadané testem mají přednost.
"""

import itertools

_counter = itertools.count(1)


def with_ids(env, vals, fund=None):
    vals = dict(vals)
    kind = env["investra.instrument.type"].browse(vals.get("type_id"))
    number = next(_counter)
    if "isin" in vals or (kind.isin_required and not vals.get("fund_id")):
        vals.setdefault("isin", f"TS{number:010d}")
    else:
        if fund is not None:
            vals.setdefault("fund_id", fund.id)
        vals.setdefault("identifier_kind", "contract")
        vals.setdefault("identifier", f"TEST-{number}")
    return vals


def manager_book(env, currency):
    """Kniha investiční společnosti: v testovací DB s daty už může existovat (jen jedna je přípustná)."""
    found = env["investra.entity"].sudo().search([("entity_type", "=", "manager")])
    return found or env["investra.entity"].create_book("Investiční společnost", "manager", "cas501", currency, "cz")
