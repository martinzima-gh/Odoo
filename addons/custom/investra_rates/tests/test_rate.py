from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.investra_rates.models.rate import parse_cnb, parse_ecb

CNB = """06.11.2026 #216
země|měna|množství|kód|kurz
EMU|euro|1|EUR|24,345
Japonsko|jen|100|JPY|15,123
Maďarsko|forint|100|HUF|6,321
"""
ECB = """<?xml version="1.0"?><gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01"
xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref"><Cube><Cube time="2026-11-06">
<Cube currency="USD" rate="1.1"/><Cube currency="CZK" rate="24.3"/></Cube></Cube></gesmes:Envelope>"""


@tagged("post_install", "-at_install")
class TestRate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Rate = cls.env["investra.rate"]
        cls.czk, cls.eur, cls.jpy = (cls.env.ref(f"base.{c}") for c in ("CZK", "EUR", "JPY"))
        (cls.czk | cls.eur | cls.jpy).active = True
        cls.env["res.currency.rate"].search([("name", ">=", "2026-11-01")]).unlink()
        cls.stored = cls.Rate._store("cnb", *parse_cnb(CNB), CNB)

    def test_parse_cnb(self):
        day, rates = parse_cnb(CNB)
        self.assertEqual(day, date(2026, 11, 6))
        self.assertEqual(rates["JPY"], (Decimal(100), Decimal("15.123")))

    def test_parse_ecb(self):
        day, rates = parse_ecb(ECB)
        self.assertEqual(day, date(2026, 11, 6))
        self.assertEqual(rates["CZK"][1], Decimal("24.3"))

    def test_malformed_cnb_is_error(self):
        with self.assertRaises(ValueError):
            parse_cnb("06.11.2026 #216\nhlavička\nrozbitý řádek\n")

    def test_quantity_is_respected(self):
        self.assertEqual(self.Rate.get_rate("cnb", self.jpy, date(2026, 11, 6)), Decimal("0.15123"))

    def test_weekend_uses_last_published(self):
        self.assertEqual(self.Rate.get_rate("cnb", self.eur, date(2026, 11, 8)), Decimal("24.345"))

    def test_never_uses_future_rate(self):
        with self.assertRaises(UserError):
            self.Rate.get_rate("cnb", self.eur, date(2026, 11, 5))

    def test_stale_rate_is_error(self):
        with self.assertRaises(UserError):
            self.Rate.get_rate("cnb", self.eur, date(2026, 11, 20))

    def test_rate_is_immutable(self):
        record = self.stored.filtered(lambda r: r.currency_id == self.eur)
        with self.assertRaises(UserError):
            record.rate = 1
        with self.assertRaises(UserError):
            record.unlink()

    def test_second_store_adds_nothing(self):
        self.assertFalse(self.Rate._store("cnb", *parse_cnb(CNB), CNB))

    def test_hash_is_stored(self):
        self.assertEqual(len(self.stored[0].document_hash), 64)

    def test_publish_reaches_czk_and_eur_books(self):
        self.stored._publish()
        Entity = self.env["investra.entity"]
        czk_book = Entity.create_book("CZK", "fund", "cas501", self.czk, "cz").company_id
        eur_book = Entity.create_book("EUR", "fund", "cas501", self.eur, "cz").company_id
        day = date(2026, 11, 6)
        self.assertEqual(self.eur._convert(1000, self.czk, czk_book, day), 24345.0)
        self.assertEqual(self.czk._convert(24345, self.eur, eur_book, day), 1000.0)

    def test_ecb_rate_only_in_ecb_book(self):
        Entity = self.env["investra.entity"]
        ecb_book = Entity.create_book("ECB", "fund", "cas501", self.eur, "cz").company_id
        cnb_book = Entity.create_book("ČNB", "fund", "cas501", self.czk, "cz").company_id
        self.stored._publish()
        day = date(2026, 11, 6)
        ecb = self.Rate._store("ecb", *parse_ecb(ECB), ECB)
        ecb._publish()
        # 1 EUR = 24,30 CZK podle ECB, ale 24,345 CZK podle ČNB
        self.assertAlmostEqual(self.czk._convert(24300, self.eur, ecb_book, day), 1000.0, places=2)
        self.assertEqual(self.eur._convert(1000, self.czk, cnb_book, day), 24345.0)

    def test_ecb_book_mixes_cnb_rate_for_currency_outside_ecb(self):
        """Riziko 4 plánu ochrany kurzů (otevřený bod „Kniha se zdrojem ECB a měna mimo ECB“): POTVRZENO 2026-11-11.

        Charakterizační test: zachycuje akceptované standardní chování Odoo. JPY je ve vzorku jen u ČNB (ve skutečnosti
        např. XDR nebo měsíční kurzy ČNB). Kniha ECB má EUR = 1 jako kurz knihy, pro JPY kurz knihy nemá,
        a Odoo (res.currency._get_rates) proto vezme společný kurz ČNB se základem CZK. 1000 JPY se tak
        přepočte na 151,23 „EUR“, což je částka v CZK. Riziko uživatel akceptoval (deník 2026-11-11 „Riziko 4
        akceptováno, standard Odoo“); test hlídá, že se standardní chování Odoo nezměnilo (např. při upgradu).
        """
        ecb_book = self.env["investra.entity"].create_book("ECB JPY", "fund", "cas501", self.eur, "cz").company_id
        self.stored._publish()
        self.Rate._store("ecb", *parse_ecb(ECB), ECB)._publish()
        day = date(2026, 11, 6)
        mixed_czk = 1000 * 15.123 / 100  # CZK za 1000 JPY podle ČNB
        converted = self.jpy._convert(1000, self.eur, ecb_book, day, round=False)
        self.assertAlmostEqual(converted, mixed_czk, places=6)
        # Kontrola: měna, kterou ECB vyhlašuje, se přepočte správně (1,1 USD = 1 EUR).
        self.assertAlmostEqual(self.env.ref("base.USD")._convert(1100, self.eur, ecb_book, day, round=False), 1000.0, places=6)

    def test_ecb_rate_is_inverse_of_cnb_quotation(self):
        ecb = self.Rate._store("ecb", *parse_ecb(ECB), ECB)
        self.assertEqual(self.Rate.get_rate("ecb", self.czk, date(2026, 11, 6)), 1 / Decimal("24.3"))
        self.assertTrue(ecb)

    def test_failed_download_does_not_stop_cron(self):
        import requests
        with patch("odoo.addons.investra_rates.models.rate.requests.get", side_effect=requests.ConnectionError):
            with self.assertLogs("odoo.addons.investra_rates.models.rate", "ERROR"):
                self.Rate._cron_fetch()

    def test_cron_publishes_downloaded_rates(self):
        document = "27.07.2031 #143\nzemě|měna|množství|kód|kurz\nEMU|euro|1|EUR|24,500\n"
        response = MagicMock(text=document)
        Rates = self.env["res.currency.rate"].sudo()
        with patch("odoo.addons.investra_rates.models.rate.requests.get", return_value=response):
            self.env["investra.rate"]._cron_fetch()
        rate = Rates.search([("currency_id.name", "=", "EUR"), ("name", "=", "2031-07-27"), ("company_id", "=", False)])
        self.assertEqual(len(rate), 1)
        self.assertAlmostEqual(rate.rate, 1 / 24.5, places=8)

    def eur_in_czk(self, day):
        company = self.env["res.company"].create({"name": f"Kurz {day!r}", "currency_id": self.env.ref("base.CZK").id})
        return round(self.env.ref("base.EUR")._convert(1, self.env.ref("base.CZK"), company, day, round=False), 3)

    def publish_eur(self, day, value):
        self.Rate._store("cnb", day, {"EUR": (Decimal(1), Decimal(value))}, f"{day}{value}")._publish()

    def test_rate_applies_on_its_own_day(self):
        self.publish_eur(date(2034, 3, 2), "24.100")
        self.publish_eur(date(2034, 3, 3), "24.300")
        self.assertEqual(self.eur_in_czk(date(2034, 3, 2)), 24.1)
        self.assertEqual(self.eur_in_czk(date(2034, 3, 3)), 24.3)

    def test_weekend_uses_friday_and_string_date_works(self):
        self.publish_eur(date(2034, 3, 3), "24.300")
        self.assertEqual(self.eur_in_czk(date(2034, 3, 5)), 24.3)
        self.assertEqual(self.eur_in_czk("2034-03-05"), 24.3)

    def test_fetch_uses_requested_date(self):
        response = MagicMock(text=CNB)
        with patch("odoo.addons.investra_rates.models.rate.requests.get", return_value=response) as get:
            self.Rate.fetch_cnb(date(2026, 11, 6))
        self.assertIn("date=06.11.2026", get.call_args[0][0])
