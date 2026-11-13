from odoo import fields, models, tools


class InvestraValuationPriceHistory(models.Model):
    """Historie zveřejněných kurzů tříd jako čísla – zdroj pro grafy (rozhodnutí 2026-11-13).

    Jen pro čtení, nad řádky tříd zveřejněných ocenění. Kurz se ve výpočtu ukládá jako text (přesná hodnota
    po zaokrouhlení Decimal), tady je převedený na číslo jen pro zobrazení a grafy; pro výpočty se nepoužívá.
    Jen stav „Zveřejněno a uzamčeno“: zveřejněné ocenění se nestornuje, takže na datum připadá nejvýš jedna verze.
    Nic se nedopočítává: chybí-li zveřejněné ocenění, chybí i bod v grafu.
    """

    _name = "investra.valuation.price.history"
    _description = "Historie zveřejněných kurzů tříd"
    _auto = False
    _order = "date desc, fund_id, class_id"
    _rec_name = "class_id"
    # Před čtením pohledu Odoo zapíše rozpracované změny těchto polí (jinak by čerstvě zveřejněné ocenění chybělo).
    _depends = {
        "investra.valuation": ["date", "fund_id", "state"],
        "investra.valuation.class": ["valuation_id", "class_id", "company_id", "price"],
        "investra.fund.class": ["currency_id"],
    }

    date = fields.Date(readonly=True, string="Datum ocenění")
    fund_id = fields.Many2one("investra.fund", readonly=True, string="Fond")
    class_id = fields.Many2one("investra.fund.class", readonly=True, string="Třída")
    company_id = fields.Many2one("res.company", readonly=True, string="Kniha")
    currency_id = fields.Many2one("res.currency", readonly=True, string="Měna kurzu")
    valuation_id = fields.Many2one("investra.valuation", readonly=True, string="Ocenění")
    # Průměr: v grafu se seskupuje podle data a třídy, na skupinu připadá jeden kurz. Součet kurzů nedává smysl.
    price = fields.Float(readonly=True, digits=(20, 8), aggregator="avg", string="Kurz")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # Přímý převod textu na číslo bez filtru: nečíselný kurz má skončit chybou, ne tiše zmizet z grafu.
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT line.id AS id,
                       valuation.date AS date,
                       valuation.fund_id AS fund_id,
                       line.class_id AS class_id,
                       line.company_id AS company_id,
                       fund_class.currency_id AS currency_id,
                       valuation.id AS valuation_id,
                       line.price::numeric AS price
                  FROM investra_valuation_class line
                  JOIN investra_valuation valuation ON valuation.id = line.valuation_id
                  JOIN investra_fund_class fund_class ON fund_class.id = line.class_id
                 WHERE valuation.state = 'published'
            )
        """)
