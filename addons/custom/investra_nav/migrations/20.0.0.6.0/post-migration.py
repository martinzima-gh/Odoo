import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def _exists(cr, table, column=None):
    if column:
        cr.execute("SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s", (table, column))
    else:
        cr.execute("SELECT 1 FROM information_schema.tables WHERE table_name = %s", (table,))
    return bool(cr.fetchone())


def migrate(cr, version):
    """Převod `second_person_required` a kroků schválení fondu do schvalovací matice (rozhodnutí 2026-11-11,
    docs/navrh-schvalovaci-matice.md, Dopad).

    Výchozí matice (investra_fund, data) = dnešní chování: druhá osoba ano. Fond s vlastními kroky dostane
    řádek zpřísnění se stejnými kroky. Fond s vypnutou druhou osobou převést nejde (fond smí matici jen
    zpřísnit): zapíše se do logu a dál platí výchozí matice, tedy druhá osoba. Doklady a ocenění se nemění;
    sloupec `second_person_required` i tabulka kroků zůstávají v databázi jen pro historii, dokud je Odoo
    neodstraní spolu se zrušeným modelem.
    """
    env = api.Environment(cr, SUPERUSER_ID, {}, su=True)
    steps = {}
    if _exists(cr, "investra_fund_approval_step"):
        cr.execute("SELECT fund_id, name FROM investra_fund_approval_step ORDER BY fund_id, sequence, id")
        for fund_id, name in cr.fetchall():
            steps.setdefault(fund_id, []).append(name)
    Matrix = env["investra.approval.matrix"]
    for fund_id, names in steps.items():
        Matrix.create({
            "activity": "valuation_approve",
            "fund_id": fund_id,
            "valid_from": "2000-01-01",
            "performer_role": "preparer",
            "second_person": "steps" if len(names) > 1 else "yes",
            "step_ids": [(0, 0, {"sequence": i, "name": name, "role": "approver"}) for i, name in enumerate(names)],
            "note": "Převedeno z kroků schválení fondu",
        })
    if _exists(cr, "investra_fund", "second_person_required"):
        cr.execute("SELECT id, name FROM investra_fund WHERE second_person_required IS NOT TRUE ORDER BY id")
        for fund_id, name in cr.fetchall():
            if fund_id not in steps:
                _logger.warning(
                    "Fond %s (%s) měl vypnutou druhou osobu; matice ji fondu zmírnit nedovolí, platí výchozí matice. "
                    "Pro schvalování bez druhé osoby založte řádek výchozí matice nebo obhospodařovatele.", fund_id, name,
                )
