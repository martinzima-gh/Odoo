"""MN-07: odstranění prázdného sloupce investra_entity.founder_id.

Pole founder_id (zakladatel knihy) z MN-05 už v modelu není; sloupec zůstal v databázi. Souhlas Martina 16. 11. 2026
(změna schématu). Před smazáním se ověří, že sloupec nenese žádná data – jinak migrace skončí chybou a nic nesmaže.
Opakovatelné: bez sloupce nedělá nic.
"""


def migrate(cr, version):
    cr.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_name = 'investra_entity' AND column_name = 'founder_id'"
    )
    if not cr.fetchone():
        return
    cr.execute("SELECT COUNT(*) FROM investra_entity WHERE founder_id IS NOT NULL")
    if cr.fetchone()[0]:
        raise RuntimeError("investra_entity.founder_id obsahuje data; sloupec se nemaže (MN-07).")
    cr.execute("ALTER TABLE investra_entity DROP COLUMN IF EXISTS founder_id")
