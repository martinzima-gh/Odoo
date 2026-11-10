import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from decimal import Decimal

import requests

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

CNB_URL = (
    "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/"
    "kurzy-devizoveho-trhu/denni_kurz.txt?date={date}"
)
CNB_MONTHLY_URL = (
    "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-ostatnich-men/"
    "kurzy-ostatnich-men/kurzy.txt?rok={year}&mesic={month}"
)
ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
# Měsíční kurz ČNB (kurzy ostatních měn) platí do dalšího měsíčního vyhlášení.
MONTHLY_MAX_AGE_DAYS = 35
APPROVER = "investra_entity.group_valuation_approver"
ECB_NS = "{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}"


def parse_cnb(text):
    """Vrátí (datum vyhlášení, {kód: (množství, kurz)}) z denního souboru ČNB."""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) < 3:
        raise ValueError("Soubor ČNB nemá očekávaný obsah.")
    published = datetime.strptime(lines[0].split(" ")[0], "%d.%m.%Y").date()
    rates = {}
    for line in lines[2:]:
        parts = line.split("|")
        if len(parts) != 5:
            raise ValueError(f"Neočekávaný řádek ČNB: {line}")
        rates[parts[3]] = (Decimal(parts[2]), Decimal(parts[4].replace(",", ".")))
    return published, rates


def parse_ecb(text):
    """Vrátí (datum, {kód: (1, jednotek měny za 1 EUR)}) z denního souboru ECB."""
    root = ET.fromstring(text)
    day = root.find(f".//{ECB_NS}Cube[@time]")
    if day is None:
        raise ValueError("Soubor ECB nemá očekávaný obsah.")
    published = date.fromisoformat(day.get("time"))
    return published, {c.get("currency"): (Decimal(1), Decimal(c.get("rate"))) for c in day}


class InvestraRate(models.Model):
    """Evidence kurzů: vyhlášené kurzy a ruční výjimky s důvodem; záznam se po uložení nemění.

    Kurzy Odoo (res.currency.rate) se zapisují jen odsud (rozhodnutí 2026-11-10 „Ochrana kurzů“).
    Ruční přepis vyhlášeného kurzu i ruční kurz měny, kterou zdroj nevyhlásil, zakládá jen skupina
    schvalování ocenění s důvodem. Oprava přepisu je nový přepis; platí poslední.
    """

    _name = "investra.rate"
    _description = "Kurz"
    _order = "date desc, source, currency_id, id desc"

    source = fields.Selection([("cnb", "ČNB"), ("ecb", "ECB")], required=True, readonly=True)
    date = fields.Date(required=True, readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", required=True, readonly=True, ondelete="restrict")
    quantity = fields.Float(required=True, default=1, readonly=True, digits=(12, 0))
    rate = fields.Float(required=True, readonly=True, digits=(16, 6), help="Základní měna zdroje za množství.")
    fetched_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    document_hash = fields.Char(readonly=True, help="SHA-256 staženého souboru.")
    origin = fields.Selection(
        [("published", "Vyhlášený"), ("override", "Ruční přepis"), ("manual", "Ruční kurz")],
        required=True, default="published", readonly=True, string="Druh",
    )
    periodicity = fields.Selection(
        [("daily", "Denní"), ("monthly", "Měsíční")], required=True, default="daily", readonly=True,
        string="Vyhlašování", help="Měsíční kurzy ČNB (kurzy ostatních měn) platí do dalšího měsíčního vyhlášení.",
    )
    reason = fields.Text(readonly=True, string="Důvod")
    overridden_id = fields.Many2one("investra.rate", readonly=True, ondelete="restrict", string="Přepisuje kurz")

    # Jeden vyhlášený a jeden ruční kurz zdroje k datu pro měnu; přepisů může být víc, každý přepisuje předchozí.
    _source_date_currency_uniq = models.Constraint(
        "UNIQUE NULLS NOT DISTINCT (source, date, currency_id, origin, overridden_id)",
        "Kurz zdroje k datu pro měnu už existuje.",
    )

    def write(self, vals):
        raise UserError(self.env._("Kurz v evidenci nejde měnit. Opravu zadejte jako ruční přepis s důvodem."))

    def unlink(self):
        raise UserError(self.env._("Kurz v evidenci nejde smazat."))

    @api.model
    def _store(self, source, published, rates, document, periodicity="daily"):
        """Uloží vyhlášené kurzy; kurz 0 (zdroj ho nevyhlašuje) a už uložený kurz přeskočí."""
        digest = hashlib.sha256(document.encode()).hexdigest()
        currencies = self.env["res.currency"].with_context(active_test=False).search([("name", "in", list(rates))])
        by_name = {c.name: c for c in currencies}
        existing = self.search([
            ("source", "=", source), ("date", "=", published), ("origin", "in", ("published", "manual")),
        ]).mapped("currency_id.name")
        values = []
        for code, (quantity, rate) in rates.items():
            if code in by_name and code not in existing and rate and quantity:
                values.append({
                    "source": source,
                    "date": published,
                    "currency_id": by_name[code].id,
                    "quantity": float(quantity),
                    "rate": float(rate),
                    "document_hash": digest,
                    "periodicity": periodicity,
                })
        return self.create(values)

    @api.model
    def fetch_cnb(self, day):
        response = requests.get(CNB_URL.format(date=day.strftime("%d.%m.%Y")), timeout=30)
        response.raise_for_status()
        published, rates = parse_cnb(response.text)
        return self._store("cnb", published, rates, response.text)

    @api.model
    def fetch_cnb_monthly(self, year, month):
        """Kurzy ostatních měn ČNB (vyhlašuje se poslední pracovní den měsíce)."""
        response = requests.get(CNB_MONTHLY_URL.format(year=year, month=month), timeout=30)
        response.raise_for_status()
        published, rates = parse_cnb(response.text)
        return self._store("cnb", published, rates, response.text, periodicity="monthly")

    @api.model
    def fetch_ecb(self):
        response = requests.get(ECB_URL, timeout=30)
        response.raise_for_status()
        published, rates = parse_ecb(response.text)
        return self._store("ecb", published, rates, response.text)

    @api.model
    def _cron_fetch(self):
        """Selhání zdroje se zaloguje; chybějící kurz zastaví až ocenění.

        Měsíční kurzy se stahují za minulý i běžný měsíc; už uložené se přeskočí.
        """
        today = fields.Date.context_today(self)
        last_month = today.replace(day=1) - timedelta(days=1)
        fetches = (
            lambda: self.fetch_cnb(today),
            lambda: self.fetch_cnb_monthly(last_month.year, last_month.month),
            lambda: self.fetch_cnb_monthly(today.year, today.month),
            self.fetch_ecb,
        )
        for fetch in fetches:
            try:
                fetch()._publish()
            except (requests.RequestException, ValueError, ET.ParseError):
                _logger.exception("Stažení kurzů selhalo")

    @api.model
    def base_currency(self, source):
        return self.env.ref("base.CZK" if source == "cnb" else "base.EUR")

    @api.model
    def get_rate(self, source, currency, day, max_age_days=5):
        """Kurz platný k datu: poslední vyhlášený do data včetně, nikdy pozdější.

        Vrací počet jednotek základní měny zdroje za 1 jednotku měny.
        """
        if currency == self.base_currency(source):
            return Decimal(1)
        record = self._effective(source, currency, day)
        if not record:
            raise UserError(self.env._("Chybí kurz %(cur)s ke dni %(day)s.", cur=currency.name, day=day))
        if record.periodicity == "monthly":
            max_age_days = max(max_age_days, MONTHLY_MAX_AGE_DAYS)
        if (day - record.date).days > max_age_days:
            raise UserError(self.env._(
                "Kurz %(cur)s z %(rate_day)s je k datu %(day)s příliš starý.",
                cur=currency.name, rate_day=record.date, day=day,
            ))
        return record._base_per_unit()

    @api.model
    def _effective(self, source, currency, day):
        """Kurz platný k datu: poslední datum do dne včetně; k tomu datu poslední ruční přepis, jinak kurz."""
        day = fields.Date.to_date(day)
        latest = self.search(
            [("source", "=", source), ("currency_id", "=", currency.id), ("date", "<=", day)],
            order="date desc", limit=1,
        )
        if not latest:
            return latest
        same_day = self.search([("source", "=", source), ("currency_id", "=", currency.id), ("date", "=", latest.date)])
        overrides = same_day.filtered(lambda r: r.origin == "override")
        return max(overrides, key=lambda r: r.id) if overrides else same_day.filtered(lambda r: r.origin != "override")[:1]

    def _base_per_unit(self):
        """ČNB vyhlašuje CZK za množství měny, ECB jednotky měny za 1 EUR."""
        self.ensure_one()
        rate, quantity = Decimal(str(self.rate)), Decimal(str(self.quantity))
        return rate / quantity if self.source == "cnb" else quantity / rate

    @api.model
    def convert(self, source, amount, from_currency, to_currency, day):
        """Přepočet přes základní měnu zdroje."""
        if from_currency == to_currency:
            return Decimal(str(amount))
        ratio = self.get_rate(source, from_currency, day) / self.get_rate(source, to_currency, day)
        return Decimal(str(amount)) * ratio

    def _publish(self):
        """Promítne kurzy do res.currency.rate.

        Hodnota v Odoo znamená jednotky měny za 1 jednotku základu. ČNB se ukládá jako společné
        kurzy se základem CZK, které fungují i ve společnosti v EUR (ověřeno). ECB se ukládá jen
        do knih se zdrojem ECB se základem EUR, včetně EUR = 1, protože kurz společnosti má přednost
        a společný kurz EUR by jinak míchal základy.

        Do Odoo jde jen kurz, který k datu platí (poslední přepis má přednost). Ruční přepis hodnotu v Odoo
        přepíše; stažený kurz existující odlišnou hodnotu nepřepíše a rozdíl ohlásí. Vrací seznam rozdílů.
        """
        ecb_books = self.env["investra.entity"].sudo().search([("rate_source", "=", "ecb")])
        euro = self.env.ref("base.EUR")
        differences = []
        for record in self:
            if record != self._effective(record.source, record.currency_id, record.date):
                continue
            value = float(1 / record._base_per_unit())
            overwrite = record.origin != "published"
            if record.source == "cnb":
                differences += self._publish_value(record.currency_id, record.date, value, False, overwrite)
                continue
            for company_id in ecb_books.company_id.ids:
                differences += self._publish_value(record.currency_id, record.date, value, company_id, overwrite)
                self._publish_value(euro, record.date, 1.0, company_id)
        for difference in differences:
            _logger.warning("Kurz v Odoo se liší od evidence a nebyl přepsán: %s", difference)
        return differences

    @api.model
    def _publish_value(self, currency, day, value, company_id, overwrite=False):
        Rate = self.env["res.currency.rate"].sudo()
        domain = [("currency_id", "=", currency.id), ("name", "=", day), ("company_id", "=", company_id)]
        existing = Rate.search(domain, limit=1)
        if not existing:
            Rate.create({"currency_id": currency.id, "name": day, "rate": value, "company_id": company_id})
            return []
        if abs(existing.rate - value) <= 1e-12 * max(abs(value), 1):
            return []
        if overwrite:
            existing.write({"rate": value})
            return []
        return [f"{currency.name} {day}: v Odoo {existing.rate}, v evidenci {value}"]

    # --- ruční kurz a přepis -------------------------------------------------------------------

    @api.model
    def _check_change_allowed(self, source, day):
        """Háček pro moduly, které kurz používají (ocenění odmítne přepis po schváleném ocenění)."""
        return True

    @api.model
    def create_manual(self, origin, source, currency, day, quantity, rate, reason):
        """Ruční přepis vyhlášeného kurzu nebo ruční kurz měny, kterou zdroj k datu nevyhlásil."""
        if not self.env.su and not self.env.user.has_group(APPROVER):
            raise AccessError(self.env._("Ruční kurz smí zadat jen uživatel se skupinou schvalování ocenění."))
        if origin not in ("override", "manual"):
            raise UserError(self.env._("Neznámý druh ručního kurzu."))
        if not (reason or "").strip():
            raise UserError(self.env._("Uveďte důvod ručního kurzu."))
        if not rate or rate <= 0 or not quantity or quantity <= 0:
            raise UserError(self.env._("Kurz i množství musí být kladné."))
        day = fields.Date.to_date(day)
        if currency == self.base_currency(source):
            raise UserError(self.env._("Základní měna zdroje má kurz 1."))
        current = self.sudo().search([
            ("source", "=", source), ("currency_id", "=", currency.id), ("date", "=", day),
        ])
        base = current.filtered(lambda r: r.origin != "override")
        if origin == "manual" and base:
            raise UserError(self.env._(
                "Kurz %(cur)s k %(day)s už existuje; použijte ruční přepis.", cur=currency.name, day=day,
            ))
        if origin == "override" and not base:
            raise UserError(self.env._(
                "Kurz %(cur)s k %(day)s neexistuje; použijte ruční kurz.", cur=currency.name, day=day,
            ))
        self._check_change_allowed(source, day)
        overridden = False
        if origin == "override":
            overridden = self.sudo()._effective(source, currency, day)
        record = self.sudo().create({
            "source": source, "date": day, "currency_id": currency.id, "quantity": quantity, "rate": rate,
            "origin": origin, "reason": reason.strip(), "overridden_id": overridden.id if overridden else False,
        })
        record._publish()
        return record.sudo(False)
