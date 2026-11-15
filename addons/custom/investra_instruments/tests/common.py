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


def assess_sppi(instrument, vals, day):
    """Zadání SPPI z volání testu zapíše na nástroj (od IM-05 je SPPI vlastnost nástroje, zařazení ho přebírá).

    Klíče `sppi`, `sppi_note`, `sppi_version` z `vals` odebere; posouzení je ke dni zařazení, takže znění IFRS 9 vychází
    stejně jako dřív podle dne platnosti zařazení. Nástroj se zapíše jen při jiné hodnotě (po obchodu je zamčený).
    """
    if not {"sppi", "sppi_note", "sppi_version"} & set(vals):
        return vals
    wanted = {"sppi_status": vals.pop("sppi", instrument.sppi_status), "sppi_note": vals.pop("sppi_note", False)}
    if "sppi_version" in vals:
        wanted["sppi_version"] = vals.pop("sppi_version")
    if any((instrument[name] or False) != (value or False) for name, value in wanted.items()):
        instrument.write({**wanted, "sppi_assessed_on": day})
    return vals
