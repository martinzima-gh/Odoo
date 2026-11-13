"""Úpis a odkup třídy (rozhodnutí „Úpisy a odkupy (bod 8 UX)“ a „Úpisy a odkupy – účty a vzorce“, 2026-11-11).

Vše posílá a určuje IS: kusy, cenu, hrubou částku, poplatek a rozdíl ze zaokrouhlení kusů. Odoo nic nedopočítává,
jen kontroluje a účtuje. Částky z IS jsou v měně kurzu třídy; doklad je ve funkční měně.

Úpis:  hrubá částka (přijatá platba) = kusy × cena + poplatek + rozdíl + zbytek
Odkup: hrubá částka = kusy × cena + zbytek; výplata = hrubá částka − poplatek − rozdíl

Kusy × cena se zaokrouhlí na haléře matematicky. Zbytek (nesoulad dat z IS) do 0,01 jde na výnos nebo náklad
ze zaokrouhlení, větší zastaví zaúčtování. Rozdíl ze zaokrouhlení kusů zůstává ve fondu (kapitál třídy), nebo
se vrací investorovi (závazek, výplatu zadává IS). Poplatek se platí ven (závazek vůči příjemci).

Pohyb bez ceny (pořízený před evidencí ceny, nebo z testů) se účtuje jako dřív: kapitál = hrubá částka − poplatek − rozdíl.
"""

from decimal import ROUND_DOWN, ROUND_HALF_UP, ROUND_UP, Decimal

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from odoo.addons.investra_fund.models.fund import FEE_RECIPIENT, ROUNDING_OWNER

PREPARER = "investra_entity.group_valuation_preparer"
UNIT_ROUNDING = {"down": ROUND_DOWN, "half_up": ROUND_HALF_UP, "up": ROUND_UP}
CENT = Decimal("0.01")
RESIDUAL_LIMIT = Decimal("0.01")


def d(value):
    return Decimal(str(value or 0))


def money(value):
    return d(value).quantize(CENT, rounding=ROUND_HALF_UP)


class InvestraFund(models.Model):
    _inherit = "investra.fund"

    def _fx_at(self, currency, day):
        """Funkční měna za jednotku měny, jen z vyhlášeného kurzu k datu."""
        self.ensure_one()
        if currency == self.currency_id:
            return Decimal(1)
        Rate = self.env["investra.rate"].sudo()
        source = self.entity_id.rate_source
        return Rate.get_rate(source, currency, day) / Rate.get_rate(source, self.currency_id, day)


class InvestraClassMovement(models.Model):
    """Úpis nebo odkup ze závěrky IS. Do napojení IS se pořizuje ručně a v testech."""

    _name = "investra.class.movement"
    _inherit = ["investra.record.guard", "mail.thread", "investra.posting.preview"]
    _description = "Pohyb kapitálu třídy"
    _order = "date, id"
    _book_fields = ("class_id",)
    _system_fields = frozenset({"event_id", "state", "valuation_id", "reversal_reason"})

    class_id = fields.Many2one("investra.fund.class", required=True, ondelete="restrict", index=True, tracking=True, string="Třída")
    fund_id = fields.Many2one(related="class_id.fund_id", store=True, index=True)
    company_id = fields.Many2one(related="class_id.company_id", store=True, index=True)
    date = fields.Date(required=True, tracking=True, string="Datum")
    movement_type = fields.Selection([("subscription", "Úpis"), ("redemption", "Odkup")], required=True, tracking=True, string="Typ")
    state = fields.Selection(
        [("draft", "Nezaúčtováno"), ("posted", "Zaúčtováno"), ("reversed", "Stornováno")],
        default="draft", required=True, readonly=True, tracking=True, string="Stav",
    )

    # A. Zdroj
    source = fields.Selection([("is", "IS"), ("manual", "Ruční zadání")], required=True, default="manual", tracking=True, string="Zdroj")
    external_ref = fields.Char(tracking=True, string="Identifikátor z IS", help="Dávka a řádek z IS; ve fondu jedinečný.")
    manual_reason = fields.Text(tracking=True, string="Důvod ručního zadání")

    # B. Cena a částky (v měně kurzu, není-li uvedeno jinak)
    currency_id = fields.Many2one(related="class_id.currency_id", string="Měna kurzu")
    units = fields.Float(digits=(20, 6), required=True, tracking=True, string="Kusy")
    price = fields.Float(digits=(24, 10), tracking=True, string="Cena za kus", help="Cena za kus v měně kurzu, kterou určil IS.")
    valuation_id = fields.Many2one(
        "investra.valuation", readonly=True, ondelete="restrict", string="Ocenění s cenou",
        help="Poslední zveřejněné ocenění fondu k datu pohybu; jeho kurz třídy je očekávaná cena.",
    )
    price_reason = fields.Text(tracking=True, string="Důvod odlišné ceny")
    amount_class = fields.Float(
        digits=(20, 2), tracking=True, string="Hrubá částka v měně kurzu",
        help="Úpis: přijatá platba. Odkup: kusy × cena před poplatkem a rozdílem.",
    )
    fx_rate = fields.Float(digits=(16, 6), tracking=True, string="Kurz", help="Funkční měna za jednotku měny kurzu; bez zadání platí vyhlášený kurz k datu.")
    amount = fields.Float(digits=(20, 2), tracking=True, string="Hrubá částka ve funkční měně")
    rounding_amount_class = fields.Float(digits=(20, 2), tracking=True, string="Rozdíl ze zaokrouhlení kusů")
    rounding_owner = fields.Selection(ROUNDING_OWNER, tracking=True, string="Rozdíl patří", help="Bez zadání platí hodnota třídy.")

    # C. Poplatek
    fee_amount_class = fields.Float(digits=(20, 2), tracking=True, string="Poplatek")
    fee_recipient = fields.Selection(FEE_RECIPIENT, tracking=True, string="Příjemce poplatku", help="Bez zadání platí hodnota třídy.")
    fee_partner_id = fields.Many2one("res.partner", tracking=True, string="Příjemce (partner)")
    fee_expected_class = fields.Float(compute="_compute_amounts", digits=(20, 2), string="Poplatek podle sazby")

    # Výsledné částky
    value_class = fields.Float(compute="_compute_amounts", digits=(20, 2), string="Kusy × cena")
    residual_class = fields.Float(compute="_compute_amounts", digits=(20, 2), string="Zbytek (zaokrouhlení)")
    payout_class = fields.Float(compute="_compute_amounts", digits=(20, 2), string="Výplata investorovi")
    capital_amount = fields.Float(
        compute="_compute_capital", store=True, digits=(20, 2), string="Změna kapitálu třídy",
        help="Kladně; úpis kapitál zvyšuje, odkup snižuje. Ve funkční měně.",
    )
    capital_amount_class = fields.Float(compute="_compute_capital", store=True, digits=(20, 2), string="Změna kapitálu v měně kurzu")

    # D. Storno a oprava
    event_id = fields.Many2one("investra.accounting.event", readonly=True, string="Účetní událost")
    replaced_id = fields.Many2one("investra.class.movement", readonly=True, ondelete="restrict", tracking=True, string="Opravuje pohyb")
    reversal_reason = fields.Text(readonly=True, tracking=True, string="Důvod storna")

    _external_ref_uniq = models.Constraint(
        "unique(fund_id, external_ref)", "Identifikátor z IS už ve fondu existuje.",
    )

    @api.depends("class_id", "date", "movement_type")
    def _compute_display_name(self):
        types = dict(self._fields["movement_type"]._description_selection(self.env))
        for movement in self:
            parts = [types.get(movement.movement_type, ""), movement.class_id.display_name or "", str(movement.date or "")]
            movement.display_name = " ".join(p for p in parts if p)

    # --- částky ---------------------------------------------------------------------------------

    def _owner(self):
        return self.rounding_owner or self.class_id.rounding_owner or "fund"

    def _fx(self):
        return d(self.fx_rate) if self.currency_id != self.fund_id.currency_id else Decimal(1)

    def _to_functional(self, value):
        if self.currency_id == self.fund_id.currency_id:
            return money(value)
        return money(d(value) * self._fx())

    def _gross_class(self):
        if self.amount_class:
            return money(self.amount_class)
        if self.currency_id == self.fund_id.currency_id or not self.fx_rate:
            return money(self.amount)
        return money(d(self.amount) / d(self.fx_rate))

    def _value_class(self):
        """Kusy × cena na haléře; bez ceny dopočet z hrubé částky (pohyby před evidencí ceny)."""
        if self.price:
            return money(d(self.units) * d(self.price))
        gross, fee, rounding = self._gross_class(), money(self.fee_amount_class), money(self.rounding_amount_class)
        return gross - fee - rounding if self.movement_type == "subscription" else gross

    def _residual_class(self):
        gross, value = self._gross_class(), self._value_class()
        if self.movement_type == "subscription":
            return gross - value - money(self.fee_amount_class) - money(self.rounding_amount_class)
        return gross - value

    def _fee_rate(self):
        rate = self.class_id.entry_fee_rate if self.movement_type == "subscription" else self.class_id.exit_fee_rate
        return d(rate) / 100

    @api.depends("units", "price", "amount_class", "amount", "fx_rate", "fee_amount_class", "rounding_amount_class", "movement_type", "class_id")
    def _compute_amounts(self):
        for movement in self:
            if not movement.class_id or not movement.movement_type:
                movement.update({"value_class": 0, "residual_class": 0, "payout_class": 0, "fee_expected_class": 0})
                continue
            gross = movement._gross_class()
            movement.value_class = float(movement._value_class())
            movement.residual_class = float(movement._residual_class())
            movement.payout_class = float(gross - money(movement.fee_amount_class) - money(movement.rounding_amount_class)) \
                if movement.movement_type == "redemption" else 0.0
            movement.fee_expected_class = float(money(gross * movement._fee_rate()))

    @api.depends("units", "price", "amount_class", "amount", "fx_rate", "fee_amount_class", "rounding_amount_class",
                 "rounding_owner", "movement_type", "class_id")
    def _compute_capital(self):
        """Změna kapitálu třídy: kusy × cena, upravená o rozdíl, který zůstává ve fondu."""
        for movement in self:
            if not movement.class_id or not movement.movement_type:
                movement.capital_amount = movement.capital_amount_class = 0
                continue
            sign = 1 if movement.movement_type == "subscription" else -1
            kept = money(movement.rounding_amount_class) if movement._owner() == "fund" else Decimal(0)
            movement.capital_amount = float(movement._capital_functional())
            movement.capital_amount_class = float(movement._value_class() + sign * kept)

    def _capital_functional(self):
        """Úpis: kusy × cena + rozdíl, který zůstává ve fondu; odkup: kusy × cena − tento rozdíl."""
        lines = self._lines_functional()
        sign = 1 if self.movement_type == "subscription" else -1
        kept = lines["rounding"] if self._owner() == "fund" else Decimal(0)
        return lines["value"] + sign * kept

    def _lines_functional(self):
        """Částky dokladu ve funkční měně; zbytek dorovná doklad i o zaokrouhlení přepočtu měny."""
        gross = money(self.amount)
        fee = self._to_functional(self.fee_amount_class)
        rounding = self._to_functional(self.rounding_amount_class)
        if self.price:
            value = self._to_functional(self._value_class())
        else:
            value = gross - fee - rounding if self.movement_type == "subscription" else gross
        if self.movement_type == "subscription":
            residual = gross - value - fee - rounding
        else:
            residual = gross - value
        return {"gross": gross, "fee": fee, "rounding": rounding, "value": value, "residual": residual}

    # --- založení a změny ----------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and any(set(vals) & self._system_fields for vals in vals_list):
            raise UserError(self.env._("Stav, vazbu na účetní událost a ocenění nastavuje jen zaúčtování."))
        for vals in vals_list:
            fund_class = self.env["investra.fund.class"].browse(vals["class_id"])
            vals.setdefault("rounding_owner", fund_class.rounding_owner)
            if vals.get("fee_amount_class"):
                vals.setdefault("fee_recipient", fund_class.fee_recipient)
            if vals.get("amount_class"):
                rate = vals.get("fx_rate") or float(fund_class.fund_id._fx_at(fund_class.currency_id, fields.Date.to_date(vals["date"])))
                vals.update({"fx_rate": rate, "amount": fund_class.fund_id.currency_id.round(vals["amount_class"] * rate)})
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su and (set(vals) & self._system_fields or self.filtered(lambda m: m.state != "draft")):
            raise UserError(self.env._("Zaúčtovaný pohyb nejde změnit; opravte ho stornem a novým pohybem."))
        if "amount_class" in vals or "fx_rate" in vals or "date" in vals:
            for movement in self:
                amount_class = vals.get("amount_class", movement.amount_class)
                if amount_class:
                    day = fields.Date.to_date(vals.get("date", movement.date))
                    rate = vals.get("fx_rate") or float(movement.fund_id._fx_at(movement.currency_id, day))
                    super(InvestraClassMovement, movement).write({
                        "fx_rate": rate, "amount": movement.fund_id.currency_id.round(amount_class * rate),
                    })
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda m: m.state != "draft" or m.event_id):
            raise UserError(self.env._("Zaúčtovaný pohyb nejde smazat; opravte ho stornem."))
        return super().unlink()

    @api.constrains("amount", "units", "fee_amount_class")
    def _check_positive(self):
        for movement in self:
            if movement.amount <= 0 or movement.units <= 0:
                raise ValidationError(self.env._("Částka i kusy musí být kladné."))
            if movement.fee_amount_class < 0 or movement.price < 0:
                raise ValidationError(self.env._("Poplatek ani cena nesmí být záporné."))

    @api.constrains("source", "manual_reason", "external_ref")
    def _check_source(self):
        for movement in self:
            if movement.source == "manual" and not (movement.manual_reason or "").strip():
                raise ValidationError(self.env._("Ruční zadání úpisu nebo odkupu vyžaduje důvod."))
            if movement.source == "is" and not movement.external_ref:
                raise ValidationError(self.env._("Pohyb z IS musí mít identifikátor z IS."))

    @api.onchange("class_id", "movement_type", "amount_class", "amount")
    def _onchange_fee(self):
        """Ruční zadání: poplatek se předvyplní ze sazby třídy, uživatel ho může upravit."""
        for movement in self:
            if movement.source == "manual" and movement.class_id and movement.movement_type and not movement.fee_amount_class:
                movement.fee_amount_class = float(money(movement._gross_class() * movement._fee_rate()))
            if movement.class_id:
                movement.rounding_owner = movement.rounding_owner or movement.class_id.rounding_owner
                movement.fee_recipient = movement.fee_recipient or movement.class_id.fee_recipient

    @property
    def signed_amount(self):
        """Změna kapitálu třídy se znaménkem (ve funkční měně)."""
        return self.capital_amount if self.movement_type == "subscription" else -self.capital_amount

    @property
    def signed_units(self):
        return self.units if self.movement_type == "subscription" else -self.units

    # --- kontroly před zaúčtováním ---------------------------------------------------------------

    def _published_valuation(self):
        """Poslední zveřejněné ocenění fondu k datu pohybu (poslední známý kurz, rozhodnutí 2026-11-04)."""
        self.ensure_one()
        return self.env["investra.valuation"].sudo().search([
            ("fund_id", "=", self.fund_id.id), ("state", "=", "published"), ("date", "<=", self.date),
        ], order="date desc, version desc", limit=1)

    def _check_booking(self):
        """Kontroly B: kusy, cena a součet částek. Pohyb bez ceny se kontroluje jen ze součtu."""
        for movement in self:
            valuation = movement._booking_valuation()
            if valuation is not None:
                movement.sudo().valuation_id = valuation

    def _booking_valuation(self):
        """Kontroly z `_check_booking` bez zápisu (volá je i náhled zaúčtování, rozhodnutí 2026-11-13).

        Přesun 1:1; zápis vazby na ocenění zůstává v `_check_booking`. Vrací ocenění s cenou, u pohybu bez ceny None.
        """
        self.ensure_one()
        for movement in self:
            name = movement.display_name
            residual = movement._residual_class()
            if abs(residual) > RESIDUAL_LIMIT:
                raise UserError(self.env._(
                    "%(name)s: částky nesedí, zbytek %(residual)s je větší než 0,01. Zkontrolujte data z IS.",
                    name=name, residual=residual,
                ))
            if movement.fee_amount_class and not movement.fee_recipient:
                raise UserError(self.env._("%s: poplatek musí mít příjemce.", name))
            if not movement.price:
                return None
            fund_class = movement.class_id
            digits = Decimal(1).scaleb(-fund_class.unit_digits)
            units = d(movement.units)
            if units != units.quantize(digits, rounding=ROUND_HALF_UP):
                raise UserError(self.env._(
                    "%(name)s: kusy mají víc než %(digits)s desetinných míst třídy.", name=name, digits=fund_class.unit_digits,
                ))
            if movement.movement_type == "subscription":
                net = movement._gross_class() - money(movement.fee_amount_class)
                expected = (net / d(movement.price)).quantize(digits, rounding=UNIT_ROUNDING[fund_class.unit_rounding])
                if units != expected:
                    raise UserError(self.env._(
                        "%(name)s: kusy %(units)s neodpovídají zaokrouhlení třídy (%(expected)s).",
                        name=name, units=units, expected=expected,
                    ))
            valuation = movement._published_valuation()
            line = valuation.class_line_ids.filtered(lambda l: l.class_id == fund_class)[:1]
            published = d(line.price) if line else None
            if (published is None or published != d(movement.price)) and not (movement.price_reason or "").strip():
                raise UserError(self.env._(
                    "%(name)s: cena %(price)s se liší od zveřejněného kurzu třídy (%(published)s). Uveďte důvod odlišné ceny.",
                    name=name, price=movement.price, published=published if published is not None else self.env._("žádné zveřejněné ocenění"),
                ))
            return valuation

    # --- zaúčtování ---------------------------------------------------------------------------------

    def _require_preparer(self):
        if not self.env.su and not self.env.user.has_group(PREPARER):
            raise AccessError(self.env._("Úpisy a odkupy účtuje jen skupina přípravy ocenění."))
        if not self.env.su and self.sudo().company_id - self.env.companies:
            raise AccessError(self.env._("Pohyb patří jiné společnosti."))

    def action_book(self):
        """Tlačítko Zaúčtovat (i hromadně ze seznamu). Ruční zadání jde přes schvalovací matici."""
        self._require_preparer()
        Matrix = self.env["investra.approval.matrix"]
        requests = self.env["investra.approval.request"]
        for movement in self.sorted(lambda m: (m.date, m.id)):
            if movement.state != "draft":
                raise UserError(self.env._("%s už je zaúčtovaný.", movement.display_name))
            if not movement.price:
                raise UserError(self.env._("%s: chybí cena za kus.", movement.display_name))
            movement._check_booking()
            if movement.source == "manual":
                request = Matrix._gate(
                    "subscription_manual", movement, "action_book", movement.sudo().fund_id,
                    summary=self.env._("Zaúčtování: %s", movement.display_name),
                )
                if request:
                    requests |= request
                    continue
            # Doklad vzniká jako služba (stejně jako u obchodů); oprávnění a matice jsou ověřené výše.
            movement.sudo()._book()
        return requests[:1]._action_open() if requests else True

    def _book_lines(self):
        """Řádky dokladu; bez poplatku a rozdílu stejné jako dřív (banka / kapitál třídy)."""
        self.ensure_one()
        kind = self.movement_type
        sign = 1 if kind == "subscription" else -1
        lines = self._lines_functional()
        investor = self._owner() == "investor"
        capital = self._capital_functional()
        bank = lines["gross"] if kind == "subscription" else lines["gross"] - lines["fee"] - lines["rounding"]
        result = [
            {"role": "bank", "amount": sign * bank, "movement_type": kind, **self._bank_currency()},
            {"role": "class_capital", "amount": -sign * capital, "class_id": self.class_id.id, "movement_type": kind},
        ]
        if lines["fee"]:
            result.append({"role": "subscription_fee_payable", "amount": -lines["fee"], "movement_type": kind,
                           "partner_id": self.fee_partner_id.id or None})
        if investor and lines["rounding"]:
            result.append({"role": "investor_rounding_payable", "amount": -lines["rounding"], "movement_type": kind})
        # Úpis: zbytek je platba navíc (výnos) nebo chybějící (náklad); odkup: fond vyplácí víc (náklad) nebo méně (výnos).
        residual = lines["residual"] if kind == "subscription" else -lines["residual"]
        if residual:
            result.append({"role": "rounding_gain" if residual > 0 else "rounding_loss", "amount": -residual,
                           "movement_type": kind})
        return result

    def _bank_currency(self):
        """Bankovní řádek v měně kurzu, pokud je úpis nebo odkup zadaný v ní."""
        self.ensure_one()
        if self.amount_class and self.currency_id != self.fund_id.currency_id:
            gross = money(self.amount_class)
            if self.movement_type == "subscription":
                return {"currency_id": self.currency_id.id, "amount_currency": gross}
            payout = gross - money(self.fee_amount_class) - money(self.rounding_amount_class)
            return {"currency_id": self.currency_id.id, "amount_currency": -payout}
        return {}

    def _book(self):
        for movement in self:
            if movement.state != "draft":
                raise UserError(self.env._("%s už je zaúčtovaný.", movement.display_name))
            movement._check_booking()
            event = self.env["investra.accounting.event"]._create_event(
                movement.company_id, f"movement:{movement.id}", f"{movement.movement_type} {movement.class_id.code}",
                movement.date, "class_movement", movement._book_lines(), source=movement,
            )
            event._lock_events()
            event._post_events()
            movement.sudo().write({"event_id": event.id, "state": "posted"})

    # --- náhled zaúčtování (rozhodnutí 2026-11-13) ----------------------------------------------

    @api.depends("state", "class_id", "movement_type", "date", "units", "price", "price_reason", "amount_class", "amount",
                 "fx_rate", "fee_amount_class", "fee_recipient", "fee_partner_id", "rounding_amount_class", "rounding_owner",
                 "event_id", "event_id.state")
    def _compute_posting_preview(self):
        for movement in self:
            movement.posting_preview = movement._posting_preview_html()

    def _ready_for_preview(self):
        return (self.state == "draft" and self.class_id and self.movement_type and self.date and self.units
                and (self.amount_class or self.amount))

    def _preview_documents(self):
        """Doklad, který vznikne tlačítkem Zaúčtovat; stejné kontroly a řádky jako `action_book` a `_book`."""
        self.ensure_one()
        if not self.price:
            raise UserError(self.env._("%s: chybí cena za kus.", self.display_name))
        self._booking_valuation()
        return [(self.env._("Při zaúčtování"), self.date, self._preview_rows(self._book_lines()))]

    def _preview_currency(self):
        currency = self.currency_id
        return currency if currency and currency != self.fund_id.currency_id else self.env["res.currency"]

    def _booked_intro(self):
        return self.env._("Zaúčtované doklady pohybu.")

    def _booked_caption(self, event):
        return {"subscription": self.env._("Úpis"), "redemption": self.env._("Odkup")}.get(self.movement_type, event.name)

    # --- storno a oprava -----------------------------------------------------------------------

    def action_reverse(self, reason):
        """Storno zaúčtovaného pohybu k jeho datu. Jde jen do ocenění, které ještě není schválené (zámek ocenění)."""
        self.ensure_one()
        self._require_preparer()
        if self.state != "posted":
            raise UserError(self.env._("Stornovat lze jen zaúčtovaný pohyb."))
        if not (reason or "").strip():
            raise UserError(self.env._("Uveďte důvod storna."))
        request = self.env["investra.approval.matrix"]._gate(
            "subscription_manual", self, "action_reverse", self.sudo().fund_id, {"reason": reason},
            summary=self.env._("Storno: %s", reason),
        )
        if request:
            return request
        self._do_reverse(reason)
        return self

    def action_correct(self, reason):
        """Oprava = storno a nový pohyb v návrhu s odkazem na opravovaný (rozhodnutí 2026-11-11, bod D)."""
        self.ensure_one()
        self._require_preparer()
        if self.state != "posted":
            raise UserError(self.env._("Opravit lze jen zaúčtovaný pohyb."))
        if not (reason or "").strip():
            raise UserError(self.env._("Uveďte důvod opravy."))
        request = self.env["investra.approval.matrix"]._gate(
            "subscription_manual", self, "action_correct", self.sudo().fund_id, {"reason": reason},
            summary=self.env._("Oprava: %s", reason),
        )
        if request:
            return request
        self._do_reverse(reason)
        return self.copy({
            "source": "manual", "external_ref": False, "replaced_id": self.id,
            "manual_reason": self.env._("Oprava pohybu %(name)s: %(reason)s", name=self.display_name, reason=reason),
        })

    def _do_reverse(self, reason):
        movement = self.sudo()
        movement._check_valuation_lock(movement.company_id, movement.date, self.env._("Storno úpisu nebo odkupu"))
        movement.event_id._reverse_events()
        movement.write({"state": "reversed", "reversal_reason": reason})

    def copy_data(self, default=None):
        # Stav, událost a ocenění nastavuje jen zaúčtování; kopie začíná v návrhu.
        vals_list = super().copy_data(default)
        for vals in vals_list:
            for name in self._system_fields:
                vals.pop(name, None)
        return vals_list


class InvestraClassMovementReverseWizard(models.TransientModel):
    """Okno pro důvod storna nebo opravy; volá pohyb, samo nic neúčtuje."""

    _name = "investra.class.movement.reverse.wizard"
    _description = "Storno nebo oprava úpisu a odkupu"

    movement_id = fields.Many2one("investra.class.movement", required=True, ondelete="cascade", string="Pohyb")
    mode = fields.Selection([("reverse", "Stornovat"), ("correct", "Opravit (storno a nový pohyb)")], required=True, default="correct", string="Krok")
    effect = fields.Text(compute="_compute_effect", string="Co se stane")
    reason = fields.Text(required=True, string="Důvod")

    @api.depends("mode")
    def _compute_effect(self):
        for wizard in self:
            wizard.effect = self.env._(
                "Doklad pohybu se stornuje k datu pohybu a pohyb dostane stav Stornováno; do ocenění už nevstoupí."
            ) + ("" if wizard.mode == "reverse" else self.env._(
                " Vznikne nový pohyb v návrhu (ruční zadání) s odkazem na opravovaný; po úpravě ho zaúčtujte."
            ))

    def action_confirm(self):
        self.ensure_one()
        method = self.movement_id.action_reverse if self.mode == "reverse" else self.movement_id.action_correct
        result = method(self.reason)
        if result._name == "investra.approval.request":
            return result._action_open()
        return {"type": "ir.actions.act_window", "res_model": result._name, "res_id": result.id,
                "view_mode": "form", "target": "current"}
