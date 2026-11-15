"""SPPI je vlastnost nástroje (úkol IM-05, rozhodnutí uživatele 15. 11. 2026): přenos ze zařazení na nástroj.

- Nástroj, jehož zařazení s vyhodnoceným testem (Splněn / Nesplněn) mají jednu shodnou hodnotu (výsledek, odůvodnění,
  znění), ji dostane; posouzeno dne = nejstarší „Platí od“ takového zařazení, posoudil = kdo zařazení naposledy změnil.
- Nástroj s rozdílnými hodnotami ve více zařazeních se nepřepisuje: zůstane „Neposouzeno“, vypíše se do logu a jeho
  zařazení si ponechají dosavadní hodnoty, dokud účetní SPPI na nástroji neposoudí.
- „Nehodnotí se“ v zařazení: u nástroje, jehož povaha se SPPI nehodnotí (akcie, deriváty, účasti), se přenese jako
  „Nehodnotí se“; u dluhového nástroje a podílového listu nástroj zůstane „Neposouzeno“ (zařazení se nemění, obojí
  se v zařazení chová jako „Nehodnotí se“).
- Zařazení ostatních nástrojů se přepočtou z nástroje. Změní-li se kategorie IFRS 9 kteréhokoli zařazení, upgrade se
  zastaví. Počty zařazení podle hodnoty SPPI před a po se vypíší do logu.
"""

import logging
from collections import Counter, defaultdict

from odoo import SUPERUSER_ID, api

from odoo.addons.investra_instruments.models.portfolio import NATURE_BY_KIND, SPPI_NATURES

_logger = logging.getLogger(__name__)
SNAPSHOT = "investra_im05_sppi_snapshot"
RECOMPUTED = ("sppi", "sppi_note", "sppi_version", "mandatory_category", "computed_category", "ifrs9_category",
              "classification_basis")


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute(f"SELECT id, instrument_id, sppi, sppi_note, sppi_version, valid_from, user_id, ifrs9_category FROM {SNAPSHOT}")
    rows = cr.dictfetchall()
    before = Counter(row["sppi"] for row in rows)
    by_instrument = defaultdict(list)
    for row in rows:
        by_instrument[row["instrument_id"]].append(row)

    Instrument = env["investra.instrument"].with_context(active_test=False)
    conflicts, transferred = [], 0
    for instrument_id, items in sorted(by_instrument.items()):
        instrument = Instrument.browse(instrument_id)
        assessed = [row for row in items if row["sppi"] in ("pass", "fail")]
        values = {(row["sppi"], row["sppi_note"] or False, row["sppi_version"] or False) for row in assessed}
        if len(values) > 1:
            conflicts.append(instrument)
            _logger.warning(
                "IM-05: nástroj %s (%s) má ve zařazeních rozdílné SPPI, nepřepisuje se: %s", instrument.id, instrument.name,
                "; ".join(f"zařazení {row['id']}: {row['sppi']} / {row['sppi_version']} / {row['sppi_note']}" for row in assessed),
            )
            continue
        if values:
            status, note, version = values.pop()
            first = min(assessed, key=lambda row: (row["valid_from"], row["id"]))
            vals = {"sppi_status": status, "sppi_note": note, "sppi_version": version,
                    "sppi_assessed_on": first["valid_from"], "sppi_assessed_by": first["user_id"] or SUPERUSER_ID}
            source = first["id"]
        elif NATURE_BY_KIND.get(instrument.type_id.kind, "equity") not in SPPI_NATURES:
            vals = {"sppi_status": "na", "sppi_assessed_on": min(row["valid_from"] for row in items),
                    "sppi_assessed_by": items[0]["user_id"] or SUPERUSER_ID}
            source = items[0]["id"]
        else:
            continue
        instrument.write(vals)
        instrument.message_post(body=f"Migrace IM-05 (2026-11-15): test SPPI převzat ze zařazení {source}.")
        transferred += 1

    Classification = env["investra.portfolio.classification"].with_context(active_test=False)
    skip = set(conflicts and Instrument.browse([i.id for i in conflicts]).classification_ids.ids)
    records = Classification.browse([row["id"] for row in rows if row["id"] not in skip]).exists()
    for name in RECOMPUTED:
        env.add_to_compute(Classification._fields[name], records)
    env.flush_all()

    cr.execute(f"""
        SELECT s.id, s.ifrs9_category, c.ifrs9_category FROM {SNAPSHOT} s
          JOIN investra_portfolio_classification c ON c.id = s.id
         WHERE s.ifrs9_category IS DISTINCT FROM c.ifrs9_category
            OR s.computed_category IS DISTINCT FROM c.computed_category
            OR s.mandatory_category IS DISTINCT FROM c.mandatory_category
    """)
    changed = cr.fetchall()
    if changed:
        raise Exception(
            "investra_instruments 20.0.0.15.0: přenos SPPI na nástroj by změnil kategorii IFRS 9 zařazení "
            "(id, před, po): " + ", ".join(map(str, changed))
        )
    cr.execute("SELECT sppi, count(*) FROM investra_portfolio_classification GROUP BY sppi")
    after = Counter(dict(cr.fetchall()))
    _logger.info(
        "IM-05: SPPI přeneseno na %s nástrojů; nástroje s rozdílným SPPI: %s; zařazení podle SPPI před %s, po %s.",
        transferred, ", ".join(f"{i.id} {i.name}" for i in conflicts) or "žádné", dict(before), dict(after),
    )
    if before != after:
        _logger.warning("IM-05: počty zařazení podle SPPI se po přenosu liší (zařazení přebírají hodnotu nástroje).")
    cr.execute(f"DROP TABLE {SNAPSHOT}")
