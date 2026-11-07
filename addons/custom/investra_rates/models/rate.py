import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from decimal import Decimal

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

CNB_URL = (
    "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/"
    "kurzy-devizoveho-trhu/denni_kurz.txt?date={date}"
)
ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
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
    """Kurz tak, jak ho zdroj vyhlásil; záznam se po uložení nemění."""

    _name = "investra.rate"
    _description = "Vyhlášený kurz"
    _order = "date desc, source, currency_id"

    source = fields.Selection([("cnb", "ČNB"), ("ecb", "ECB")], required=True, readonly=True)
    date = fields.Date(required=True, readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", required=True, readonly=True, ondelete="restrict")
    quantity = fields.Float(required=True, default=1, readonly=True, digits=(12, 0))
    rate = fields.Float(required=True, readonly=True, digits=(16, 6), help="Základní měna zdroje za množství.")
    fetched_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    document_hash = fields.Char(readonly=True, help="SHA-256 staženého souboru.")

    _source_date_currency_uniq = models.Constraint(
        "unique(source, date, currency_id)", "Kurz zdroje k datu pro měnu už existuje."
    )

    def write(self, vals):
        raise UserError(self.env._("Vyhlášený kurz nejde měnit."))

    def unlink(self):
        raise UserError(self.env._("Vyhlášený kurz nejde smazat."))

    @api.model
    def _store(self, source, published, rates, document):
        digest = hashlib.sha256(document.encode()).hexdigest()
        currencies = self.env["res.currency"].with_context(active_test=False).search([("name", "in", list(rates))])
        by_name = {c.name: c for c in currencies}
        existing = self.search([("source", "=", source), ("date", "=", published)]).mapped("currency_id.name")
        values = []
        for code, (quantity, rate) in rates.items():
            if code in by_name and code not in existing:
                values.append({
                    "source": source,
                    "date": published,
                    "currency_id": by_name[code].id,
                    "quantity": float(quantity),
                    "rate": float(rate),
                    "document_hash": digest,
                })
        return self.create(values)

    @api.model
    def fetch_cnb(self, day):
        response = requests.get(CNB_URL.format(date=day.strftime("%d.%m.%Y")), timeout=30)
        response.raise_for_status()
        published, rates = parse_cnb(response.text)
        return self._store("cnb", published, rates, response.text)

    @api.model
    def fetch_ecb(self):
        response = requests.get(ECB_URL, timeout=30)
        response.raise_for_status()
        published, rates = parse_ecb(response.text)
        return self._store("ecb", published, rates, response.text)

    @api.model
    def _cron_fetch(self):
        """Selhání zdroje se zaloguje; chybějící kurz zastaví až ocenění."""
        for fetch in (lambda: self.fetch_cnb(fields.Date.context_today(self)), self.fetch_ecb):
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
        record = self.search(
            [("source", "=", source), ("currency_id", "=", currency.id), ("date", "<=", day)],
            order="date desc",
            limit=1,
        )
        if not record:
            raise UserError(self.env._("Chybí kurz %(cur)s ke dni %(day)s.", cur=currency.name, day=day))
        if (day - record.date).days > max_age_days:
            raise UserError(self.env._(
                "Kurz %(cur)s z %(rate_day)s je k datu %(day)s příliš starý.",
                cur=currency.name, rate_day=record.date, day=day,
            ))
        return record._base_per_unit()

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
        """
        ecb_books = self.env["investra.entity"].sudo().search([("rate_source", "=", "ecb")])
        euro = self.env.ref("base.EUR")
        for record in self:
            value = float(1 / record._base_per_unit())
            if record.source == "cnb":
                self._publish_value(record.currency_id, record.date, value, False)
                continue
            for company_id in ecb_books.company_id.ids:
                self._publish_value(record.currency_id, record.date, value, company_id)
                self._publish_value(euro, record.date, 1.0, company_id)

    @api.model
    def _publish_value(self, currency, day, value, company_id):
        Rate = self.env["res.currency.rate"].sudo()
        domain = [("currency_id", "=", currency.id), ("name", "=", day), ("company_id", "=", company_id)]
        if not Rate.search_count(domain, limit=1):
            Rate.create({"currency_id": currency.id, "name": day, "rate": value, "company_id": company_id})
