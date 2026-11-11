from odoo import SUPERUSER_ID, api

DEBT_KINDS = {"bond", "loan", "deposit", "repo"}
NOTE = "Migrace z klasifikace nástroje (rozhodnutí 2026-11-11)"


def _column_exists(cr, table, column):
    cr.execute("SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s", (table, column))
    return bool(cr.fetchone())


def migrate(cr, version):
    """Klasifikace se přesouvá z nástroje do zařazení v obchodním modelu fondu (plán docs/navrh-klasifikace-ifrs9.md).

    Zůstatky ani částky se nemění; doplňuje se portfolio u obchodů a zařazení u zaúčtovaných řádků.
    Staré sloupce nástroje Odoo nemaže, proto je jde přečíst i po aktualizaci.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    Portfolio = env["investra.fund.portfolio"]
    Classification = env["investra.portfolio.classification"]

    portfolios = {}

    def portfolio(fund, model):
        key = (fund.id, model)
        if key not in portfolios:
            found = Portfolio.search([("fund_id", "=", fund.id), ("business_model", "=", model)], limit=1)
            if not found:
                name = {"fair_value": "Hlavní", "hold_to_collect": "Držet pro inkaso", "hold_collect_sell": "Inkaso i prodej"}[model]
                found = Portfolio.create({"fund_id": fund.id, "name": name, "business_model": model, "assessment": NOTE})
            portfolios[key] = found
        return portfolios[key]

    for fund in env["investra.fund"].search([]):
        portfolio(fund, "fair_value")

    if not _column_exists(cr, "investra_instrument", "ifrs9_category"):
        return
    cr.execute("""
        SELECT t.fund_id, t.instrument_id, min(t.trade_date), i.ifrs9_category, i.valuation_method, i.role_id
          FROM investra_trade t JOIN investra_instrument i ON i.id = t.instrument_id
         GROUP BY t.fund_id, t.instrument_id, i.ifrs9_category, i.valuation_method, i.role_id
    """)
    for fund_id, instrument_id, first_day, category, method, role_id in cr.fetchall():
        fund = env["investra.fund"].browse(fund_id)
        instrument = env["investra.instrument"].browse(instrument_id)
        debt = instrument.type_id.kind in DEBT_KINDS
        # Model „Ostatní“ byl 2026-11-11 rozdělen; stávající portfolia jsou Řízení na reálnou hodnotu (migrace 20.0.0.5.0).
        model = "fair_value"
        if category == "amortised":
            model = "hold_to_collect"
        elif category == "fvoci" and debt:
            model = "hold_collect_sell"
        target = portfolio(fund, model)
        classification = Classification.search([("portfolio_id", "=", target.id), ("instrument_id", "=", instrument.id)], limit=1)
        if not classification:
            sppi = "pass" if debt and category in ("amortised", "fvoci") else "na"
            designation = "fvoci_equity" if category == "fvoci" and not debt else "none"
            # Kategorie se od verze 20.0.0.5.0 počítá; vstupy se volí tak, aby vyšla stejná jako na nástroji.
            classification = Classification.create({
                "portfolio_id": target.id, "instrument_id": instrument.id, "valid_from": first_day,
                "valuation_method": method, "role_id": role_id, "sppi": sppi, "designation": designation,
                "sppi_note": "Převzato migrací z dřívější klasifikace nástroje; potvrdit posouzení SPPI." if sppi != "na" else False,
                "designation_note": "Převzato migrací z dřívější klasifikace nástroje; potvrdit." if designation != "none" else False,
                "note": NOTE,
            })
            if classification.ifrs9_category != category:
                raise RuntimeError(f"Migrace: zařazení {classification.id} by změnilo kategorii {category} -> {classification.ifrs9_category}")
        cr.execute(
            "UPDATE investra_trade SET portfolio_id = %s WHERE fund_id = %s AND instrument_id = %s AND portfolio_id IS NULL",
            (target.id, fund.id, instrument.id),
        )
        cr.execute("""
            UPDATE account_move_line SET investra_classification_id = %s
             WHERE company_id = %s AND investra_instrument_id = %s AND investra_classification_id IS NULL
        """, (classification.id, fund.company_id.id, instrument.id))
    cr.execute("SELECT count(*) FROM investra_trade WHERE portfolio_id IS NULL")
    if not cr.fetchone()[0]:
        cr.execute("ALTER TABLE investra_trade ALTER COLUMN portfolio_id SET NOT NULL")
