"""AG-019: Testy onchange dopočtů při ručním zadání úpisu a odkupu.

Pokrývá:
- Vzorový úpis z platby 1 000 000,00 CZK, sazba 1 %, cena 1 036,6444, 6 míst dolů.
- Odkup podle kusů.
- Odkup podle částky (simulováno ručním zadáním amount_class + kusy).
- První úpis bez zveřejněného ocenění (cena nepředvyplněna, price_reason = 'První úpis třídy').
- Třída v cizí měně – fx_rate předvyplněn z vyhlášeného kurzu.
- Zdroj IS – nic se nedopočítává onchange (blok source != 'manual').
- Ruční úprava poplatku zůstane, dokud se nezmění vstup (amount_class).
- Předvyplněný pohyb projde action_book bez chyby.
- Třída bez sazby s ručním poplatkem a příjemcem.

Testy jsou psány jako odoo.tests.Form (viz zadání AG-019, bod D). Odoo a Docker spouští Claude.
"""

from datetime import date
from decimal import Decimal, ROUND_DOWN

from odoo.tests import tagged, Form

from .common import NavCase


PRICE = 1036.6444  # Vzorová cena ze zadání
GROSS = 1_000_000.00
FEE_RATE = 1  # %


def _quantize6(value, rounding=ROUND_DOWN):
    return Decimal(str(value)).quantize(Decimal("0.000001"), rounding=rounding)


@tagged("post_install", "-at_install")
class TestMovementOnchange(NavCase):
    """Onchange dopočty při ručním zadání (AG-019, bod D)."""

    def setUp(self):
        super().setUp()
        # Třída A: sazba 1 %, příjemce Obhospodařovatel, 6 míst dolů
        # Třída B: sazba 0 % (bez sazby, poplatek zadán ručně)
        # Třída E: v EUR (cizí měna)
        self.fund = self.make_fund(classes=[
            {"code": "A", "entry_fee_rate": FEE_RATE, "exit_fee_rate": FEE_RATE},
            {"code": "B", "entry_fee_rate": 0.0, "exit_fee_rate": 0.0},
        ])
        self.cls_a = self.cls(self.fund, "A")
        self.cls_b = self.cls(self.fund, "B")
        self.Movement = self.env["investra.class.movement"]
        # Zveřejněné ocenění: kurz třídy A = PRICE
        self._publish_valuation_with_price(self.fund, self.cls_a, PRICE, "2027-01-10")

    def _publish_valuation_with_price(self, fund, fund_class, price, day):
        """Vytvoří zveřejněné ocenění s kurzem třídy; minimální stub pro test."""
        from odoo.addons.investra_nav.models.valuation import InvestraValuation  # noqa: F401
        valuation = self.env["investra.valuation"].with_user(self.preparer).create({
            "fund_id": fund.id, "date": day, "version": 1,
        })
        # Naplnit class_line ručně přes sudo (ocenění je ve stavu draft, cena jen pro onchange test)
        valuation.sudo().write({
            "class_line_ids": [(0, 0, {
                "class_id": fund_class.id,
                "price": price,
                "units": 0,
                "subscription_amount": 0,
                "redemption_amount": 0,
                "capital": 0,
            })],
            "state": "published",
        })
        return valuation

    # --- Vzorový úpis (bod B ze zadání) -------------------------------------------------------

    def test_subscription_from_payment(self):
        """Vzorový úpis: platba 1 000 000, sazba 1 %, cena 1 036,6444, kusy dolů na 6 míst.

        Očekávané výsledky (přepočítané dle vzorce):
          poplatek = 1 000 000 × 0,01 = 10 000,00
          čistá platba = 990 000,00
          kusy = (990 000 / 1 036,6444) zaokrouhleno dolů na 6 míst
          rounding = čistá - kusy × cena (na haléře)
        """
        fee_expected = round(GROSS * FEE_RATE / 100, 2)  # 10 000,00
        net = Decimal(str(GROSS)) - Decimal(str(fee_expected))
        price_d = Decimal(str(PRICE))
        units_d = (net / price_d).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
        rounding_d = net - (units_d * price_d).quantize(Decimal("0.01"), rounding=__import__("decimal").ROUND_HALF_UP)

        with Form(self.Movement) as f:
            f.class_id = self.cls_a
            f.movement_type = "subscription"
            f.date = date(2027, 1, 15)
            f.manual_reason = "Test vzorový úpis"
            f.amount_class = GROSS
            # cena by se měla předvyplnit z ocenění – ale ocenění je k 2027-01-10, takže k 2027-01-15 je platné
            # proto ručně nastavíme cenu (onchange ceny spustí dopočet)
            f.price = PRICE

            # Zkontrolujeme po onchange
            self.assertAlmostEqual(f.fee_amount_class, fee_expected, places=2,
                                   msg="Poplatek se liší od 1 % z platby")
            self.assertAlmostEqual(f.units, float(units_d), places=6,
                                   msg="Kusy nesedí (zaokrouhlení dolů)")
            self.assertAlmostEqual(f.rounding_amount_class, float(rounding_d), places=2,
                                   msg="Rozdíl ze zaokrouhlení nesedí")

        # Pohyb projde action_book (kontrola součtu)
        movement = self.Movement.search([], order="id desc", limit=1)
        movement.price_reason = "Počáteční cena"  # nutné, jinak _booking_valuation vyžaduje důvod
        movement.with_user(self.preparer).action_book()
        self.assertEqual(movement.state, "posted")

    # --- Odkup podle kusů -----------------------------------------------------------------------

    def test_redemption_by_units(self):
        """Odkup: zadáme kusy, formulář dopočte hrubou částku, poplatek a výplatu."""
        units = 100.0
        price = 1_050.0
        gross_expected = round(units * price, 2)
        fee_expected = round(gross_expected * FEE_RATE / 100, 2)

        with Form(self.Movement) as f:
            f.class_id = self.cls_a
            f.movement_type = "redemption"
            f.date = date(2027, 1, 15)
            f.manual_reason = "Test odkup"
            f.price = price
            f.units = units

            self.assertAlmostEqual(f.amount_class, gross_expected, places=2,
                                   msg="Hrubá částka odkupu nesedí")
            self.assertAlmostEqual(f.fee_amount_class, fee_expected, places=2,
                                   msg="Poplatek odkupu nesedí")

    # --- Odkup podle částky (simulace) ----------------------------------------------------------

    def test_redemption_by_amount_manual(self):
        """Odkup: uživatel zadá amount_class ručně + kusy (simulace tlačítka 'odkup podle částky').

        Zadání: kusy se dopočítají, hrubá = kusy × cena, rozdíl = zadaná částka - hrubá.
        V aktuální implementaci se onchange redemption_by_units spustí při změně kusů;
        simulujeme tak, že kusy ručně vypočteme a vložíme.
        """
        price = 1_050.0
        required_amount = 100_000.0
        # kusy = floor(required_amount / price, 6 míst)
        units_d = (Decimal(str(required_amount)) / Decimal(str(price))).quantize(
            Decimal("0.000001"), rounding=ROUND_DOWN
        )
        gross_d = (units_d * Decimal(str(price))).quantize(Decimal("0.01"), rounding=__import__("decimal").ROUND_HALF_UP)
        fee_expected = float((gross_d * Decimal("0.01")).quantize(Decimal("0.01"), rounding=__import__("decimal").ROUND_HALF_UP))

        with Form(self.Movement) as f:
            f.class_id = self.cls_a
            f.movement_type = "redemption"
            f.date = date(2027, 1, 15)
            f.manual_reason = "Test odkup podle částky"
            f.price = price
            f.units = float(units_d)

            self.assertAlmostEqual(f.amount_class, float(gross_d), places=2)
            self.assertAlmostEqual(f.fee_amount_class, fee_expected, places=2)

    # --- První úpis bez zveřejněného ocenění ---------------------------------------------------

    def test_first_subscription_no_valuation(self):
        """Nový fond bez zveřejněného ocenění: cena se nepředvyplní, price_reason = 'První úpis třídy'."""
        fund_new = self.make_fund(classes=[{"code": "X", "entry_fee_rate": 1.0}])
        cls_x = self.cls(fund_new, "X")

        with Form(self.Movement) as f:
            f.class_id = cls_x
            f.movement_type = "subscription"
            f.date = date(2027, 1, 20)
            f.manual_reason = "První úpis"

            # Žádné zveřejněné ocenění → cena by měla být 0 nebo nepředvyplněna
            self.assertAlmostEqual(f.price, 0.0, places=2,
                                   msg="Cena by neměla být předvyplněna u prvního úpisu")
            # price_reason by měl obsahovat nápovědu
            self.assertIn("První úpis", f.price_reason or "",
                          msg="Nápověda 'První úpis třídy' by měla být předvyplněna")

    # --- Třída v cizí měně – kurz předvyplněn --------------------------------------------------

    def test_foreign_currency_fx_rate_prefilled(self):
        """Třída v EUR: po výběru třídy a data by se měl fx_rate předvyplnit z kurzu ČNB."""
        # Fond s třídou v EUR, kurz ČNB k 2027-01-15
        fund_eur = self.make_fund(classes=[{"code": "E", "entry_fee_rate": 0.0}])
        cls_e = fund_eur.class_ids.filtered(lambda c: c.code == "E")
        cls_e.currency_id = self.eur
        # Zaregistrujeme kurz ČNB (1 EUR = 25 CZK)
        self.rate("2027-01-15", 25, "EUR")

        with Form(self.Movement) as f:
            f.class_id = cls_e
            f.movement_type = "subscription"
            f.date = date(2027, 1, 15)
            f.manual_reason = "Test EUR třída"

            # fx_rate by měl být předvyplněn (> 0)
            self.assertGreater(f.fx_rate, 0.0,
                               msg="Kurz by měl být předvyplněn z vyhlášeného kurzu ČNB")

    # --- Zdroj IS – nic se nedopočítává ---------------------------------------------------------

    def test_is_source_no_computation(self):
        """Zdroj IS: onchange dopočty se nespustí, kusy a amount_class zůstanou z IS."""
        with Form(self.Movement) as f:
            f.class_id = self.cls_a
            f.movement_type = "subscription"
            f.date = date(2027, 1, 15)
            f.source = "is"
            f.external_ref = "D99/1"
            f.price = PRICE
            f.units = 500.0
            f.amount_class = 520_000.0  # zadáno z IS, nekopíruje se z výpočtu

            # units i amount_class musí zůstat tak, jak je zadal uživatel
            self.assertAlmostEqual(f.units, 500.0, places=6)
            self.assertAlmostEqual(f.amount_class, 520_000.0, places=2)

    # --- Ruční úprava poplatku zůstane ---------------------------------------------------------

    def test_manual_fee_survives_until_input_changes(self):
        """Ruční úprava poplatku zůstane, dokud se nezmění amount_class (vstup)."""
        with Form(self.Movement) as f:
            f.class_id = self.cls_a
            f.movement_type = "subscription"
            f.date = date(2027, 1, 15)
            f.manual_reason = "Test ruční poplatek"
            f.amount_class = 100_000.0
            f.price = PRICE
            # Onchange nastaví fee = 1 000,00 (1 %)
            self.assertAlmostEqual(f.fee_amount_class, 1_000.0, places=2)
            # Uživatel ručně upraví poplatek
            f.fee_amount_class = 500.0
            # Poplatek zůstane 500, protože amount_class se nezměnil
            self.assertAlmostEqual(f.fee_amount_class, 500.0, places=2)

    # --- Třída bez sazby, ruční poplatek + příjemce – projde action_book ----------------------

    def test_zero_rate_manual_fee_with_recipient_books(self):
        """Třída bez sazby (0 %): ruční poplatek s příjemcem projde action_book."""
        # Vytvoříme pohyb přímo (bez Form, protože příjemce je podmíněný)
        movement = self.Movement.create({
            "class_id": self.cls_b.id,
            "date": "2027-01-15",
            "movement_type": "subscription",
            "source": "manual",
            "manual_reason": "Test třída bez sazby",
            "amount_class": 100_000.0,
            "units": 100.0,
            "price": 1_000.0,
            "fee_amount_class": 500.0,
            "fee_recipient": "manager",
            "price_reason": "Počáteční cena",
        })
        # Musí projít action_book bez UserError
        movement.with_user(self.preparer).action_book()
        self.assertEqual(movement.state, "posted", "Pohyb se třídou bez sazby a ručním poplatkem musí jít zaúčtovat")

    # --- Výchozí hodnoty -----------------------------------------------------------------------

    def test_default_date_is_today(self):
        """Výchozí hodnota pole Datum je dnešek."""
        from odoo import fields
        defaults = self.Movement.default_get(["date"])
        today = fields.Date.context_today(self.Movement)
        self.assertEqual(defaults.get("date"), today,
                         "Výchozí datum by mělo být dnešek")

    def test_default_class_prefilled_for_single_class_fund(self):
        """Jediná třída fondu: class_id se předvyplní z kontextu default_fund_id."""
        fund_single = self.make_fund(classes=[{"code": "S", "entry_fee_rate": 0.0}])
        cls_s = self.cls(fund_single, "S")
        defaults = self.Movement.with_context(default_fund_id=fund_single.id).default_get(["class_id"])
        self.assertEqual(defaults.get("class_id"), cls_s.id,
                         "Jediná třída fondu by se měla předvyplnit")

    def test_default_class_not_prefilled_for_multi_class_fund(self):
        """Více tříd fondu: class_id se nepředvyplní."""
        defaults = self.Movement.with_context(default_fund_id=self.fund.id).default_get(["class_id"])
        self.assertFalse(defaults.get("class_id"),
                         "U fondu s více třídami se class_id nesmí předvyplnit")
