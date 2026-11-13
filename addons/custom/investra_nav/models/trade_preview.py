"""Náhled zaúčtování obchodu a upozornění na kalendář dluhopisu (rozhodnutí 2026-11-12 „Náhled zaúčtování obchodu“).

Jen výpočet pro formulář obchodu v návrhu: nic se neúčtuje ani neukládá. Tabulka dokladů, skutečné doklady se storny
a kostra záložky jsou ve společném modelu `investra.posting.preview` (rozhodnutí 2026-11-13, přesun 1:1).
"""
from decimal import Decimal

from markupsafe import Markup

from odoo import api, fields, models
from odoo.tools import format_date, formatLang

from .. import engine


def d(value):
    return Decimal(str(value or 0))


class InvestraTradePreview(models.Model):
    _name = "investra.trade"
    _inherit = ["investra.trade", "investra.posting.preview"]

    calendar_note = fields.Char(
        compute="_compute_calendar_note", string="Upozornění ke kalendáři",
        help="Dluhopis bez kalendáře toků nebo obchod mimo kupónová období: naběhlý úrok se nepředvyplní.",
    )
    posting_preview = fields.Html(
        compute="_compute_posting_preview", sanitize=False, string="Zaúčtování",
        help="Zaúčtované doklady obchodu a vypořádání; u návrhu a nevypořádaného obchodu náhled dokladů, které vzniknou, "
             "a u prodeje v návrhu odhad výsledku, který zaúčtuje ocenění.",
    )

    @api.depends("state", "instrument_id", "trade_date")
    def _compute_calendar_note(self):
        for trade in self:
            trade.calendar_note = trade._calendar_note()

    def _calendar_note(self):
        self.ensure_one()
        instrument = self.instrument_id
        if self.state != "draft" or instrument.type_id.kind != "bond" or not self.trade_date:
            return False
        flows = instrument._origin.cashflow_ids
        if not flows:
            return self.env._(
                "Dluhopis %s nemá kalendář toků: naběhlý úrok se nepředvyplnil a ocenění ho u pozice nepočítá. "
                "Doplňte kalendář u nástroje, nebo úrok zadejte ručně.", instrument.name,
            )
        periods = instrument._origin._coupon_periods()
        if not periods:
            return False  # Bezkupónový dluhopis (jen jistina): úrok 0 je správně.
        if not any(start < self.trade_date < end for start, end, _amount in periods):
            return self.env._(
                "Datum sjednání je mimo kupónová období dluhopisu (%(start)s – %(end)s) nebo v den kupónu: "
                "naběhlý úrok vyšel 0. Zkontrolujte Začátek úročení a kalendář nástroje.",
                start=format_date(self.env, periods[0][0]), end=format_date(self.env, periods[-1][1]),
            )
        return False

    @api.depends("state", "fund_id", "portfolio_id", "instrument_id", "trade_date", "settlement_date", "side",
                 "units", "quantity", "price", "accrued_interest", "fx_rate", "settlement_fx_rate", "classification_id",
                 "event_id", "settlement_event_id", "event_id.state", "settlement_event_id.state", "reversal_reason")
    def _compute_posting_preview(self):
        for trade in self:
            trade.posting_preview = trade._posting_preview_html()

    # --- doklady ---------------------------------------------------------------------------------------------

    def _ready_for_preview(self):
        # Nevypořádaný obchod: náhled dokladu vypořádání před tlačítkem Vypořádat (přání uživatele 2026-11-12).
        return (self.state in ("draft", "unsettled") and self.fund_id and self.portfolio_id and self.instrument_id
                and self.trade_date and self.quantity and self.classification_id)

    def _preview_documents(self):
        """[(nadpis, datum, [(účet, MD, D, částka v měně)])] z téže funkce, kterou účtuje Zaúčtovat a Vypořádat."""
        self.ensure_one()
        captions = {"book": self.env._("Při zaúčtování"), "settle": self.env._("Při vypořádání")}
        documents = []
        for step, _key, _name, day, lines, _event_type in self._planned_postings():
            if self.state == "unsettled" and step != "settle":
                continue  # Doklad obchodu už je zaúčtovaný.
            documents.append((captions[step], day, self._preview_rows(lines)))
        return documents

    def _preview_currency(self):
        currency = self.instrument_id.currency_id
        return currency if currency != self.company_id.currency_id else self.env["res.currency"]

    def _preview_intro(self):
        if self.state == "draft":
            return self.env._("Jen náhled: nic se neúčtuje. Doklady vzniknou tlačítky Zaúčtovat a Vypořádat.")
        return self.env._("Náhled: doklad vypořádání vznikne tlačítkem Vypořádat. Zkontrolujte datum a kurz vypořádání.")

    def _booked_intro(self):
        return self.env._("Zaúčtované doklady obchodu.")

    def _booked_caption(self, event):
        # Přání uživatele 2026-11-12: u zaúčtovaného obchodu vidět obě nohy; po stornu i stornované události.
        captions = {"trade": self.env._("Obchod"), "trade_settlement": self.env._("Vypořádání")}
        return captions.get(event.event_type, event.name)

    def _preview_extra_html(self, money):
        # Výsledek prodeje jen u návrhu; u nevypořádaného obchodu ho už počítá ocenění ze zaúčtovaného obchodu.
        result = self._expected_result() if self.state == "draft" else None
        parts = []
        if self.quantity < 0 and self.classification_id.valuation_method == "amortised":
            parts.append(Markup('<p class="text-muted">%s</p>') % self.env._(
                "Pozice v naběhlé hodnotě: výsledek prodeje dopočítá ocenění."))
        if result:
            parts.append(self._result_html(result))
        return Markup().join(parts)

    # --- očekávaný výsledek prodeje ------------------------------------------------------------------------

    def _expected_result(self):
        """Příspěvek prodeje k výsledku nejbližšího ocenění k datu zařazení obchodu, stejným výpočtem jako ocenění.

        Ocenění se spočte dvakrát (s obchodem a bez něj); rozdíl je realizace tohoto prodeje. Platí, když před
        oceněním nepřibude jiný prodej nebo splátka. Výsledek: slovník částek ve funkční měně, nebo None.
        """
        self.ensure_one()
        if self.quantity >= 0 or self.classification_id.valuation_method == "amortised":
            return None
        day = self._recognition_date()
        if not day:
            return None
        fund = self.fund_id
        instrument, portfolio = self.instrument_id._origin, self.portfolio_id._origin
        Valuation = self.env["investra.valuation"].sudo()
        probe = Valuation.new({"fund_id": fund.id, "date": day})
        previous = probe._find_previous()
        account = self.env["investra.account.role"].account_for(self.company_id, self.classification_id.role_id.code)
        foreign = instrument.currency_id != fund.currency_id
        exclude_id = self._origin.id or 0

        def run(trade):
            valuation = probe.with_context(investra_trade_preview={"exclude_id": exclude_id, "trade": trade})
            cost_ccy, cost, realised_fx = valuation._cost_walk(instrument, portfolio, previous)
            realised_ccy, rated = valuation._realised_ccy(instrument, portfolio, previous, account, foreign)
            return d(cost_ccy), d(cost), d(realised_fx), d(realised_ccy), d(rated)

        with_trade, without = run(self), run(None)
        fx = d(self._booked_fx())
        proceeds_ccy = -d(self.quantity) * d(self.price)
        proceeds = engine.money(proceeds_ccy * fx)
        realised = engine.money(with_trade[4] - without[4]) if foreign else engine.money(with_trade[3] - without[3])
        realised_fx = engine.money(with_trade[2] - without[2]) if foreign else Decimal(0)
        cost_sold = engine.money(without[1] - with_trade[1])
        return {
            "previous": previous,
            "proceeds": proceeds,
            "carrying": proceeds - realised,
            "realised": realised,
            "realised_fx": realised_fx,
            "total": realised + realised_fx,
            "interest": engine.money(d(self.accrued_interest) * fx),
            "cost_sold": cost_sold,
            "against_cost": proceeds - cost_sold,
            "foreign": foreign,
        }

    # --- HTML ------------------------------------------------------------------------------------------------

    def _result_html(self, result):
        currency = self.company_id.currency_id.name
        previous = result["previous"]
        basis = (self.env._("k ocenění %s", format_date(self.env, previous.date)) if previous
                 else self.env._("z pořizovací ceny (fond zatím nemá ocenění)"))
        rows = [
            (self.env._("Výnos z prodeje bez úroku"), result["proceeds"], False),
            (self.env._("Účetní hodnota prodávaných kusů (%s)", basis), result["carrying"], False),
            (self.env._("Realizovaný výsledek ceny"), result["realised"], True),
        ]
        if result["foreign"]:
            rows.append((self.env._("Realizovaný kurzový rozdíl (proti pořizovací ceně)"), result["realised_fx"], True))
        rows.append((self.env._("Očekávaný výsledek celkem (+ zisk, − ztráta)"), result["total"], True))
        amount = lambda value: formatLang(self.env, float(value), digits=2)
        body = Markup()
        for label, value, strong in rows:
            cell = Markup("<strong>%s</strong>") % amount(value) if strong else amount(value)
            body += Markup("<tr><td>%s</td><td class='text-end'>%s</td></tr>") % (label, cell)
        info = self.env._(
            "Pro informaci: pořizovací cena prodaných kusů %(cost)s %(cur)s, výsledek proti pořizovací ceně %(gain)s %(cur)s.",
            cost=amount(result["cost_sold"]), gain=amount(result["against_cost"]), cur=currency,
        )
        note = self.env._(
            "Odhad: výsledek zaúčtuje ocenění; platí při ocenění k datu obchodu, když předtím nepřibude jiný prodej "
            "nebo splátka. Přijatý naběhlý úrok %(interest)s %(cur)s není součástí realizace, úrokový výnos do data "
            "prodeje dopočítá ocenění.", interest=amount(result["interest"]), cur=currency,
        )
        alert = Markup()
        if result["total"] < 0 and result["carrying"] and abs(result["total"]) > abs(result["carrying"]) / 10:
            alert = Markup('<div class="alert alert-warning" role="alert">%s</div>') % self.env._(
                "Ztráta přesahuje 10 % účetní hodnoty prodávaných kusů. Zkontrolujte cenu a kusy.")
        return Markup(
            "<h5>%s (%s)</h5>%s<table class='table table-sm o_investra_preview'><tbody>%s</tbody></table>"
            "<p>%s</p><p class='text-muted'>%s</p>"
        ) % (self.env._("Očekávaný výsledek prodeje"), currency, alert, body, info, note)
