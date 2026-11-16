"""Výpočet reálné hodnoty FX spotu, forwardu a swapu – varianta B (docs/navrh-fx-derivaty.md, oddíl Reálná hodnota).

Čisté funkce bez ORM nad Decimal; zaokrouhluje se až na konci (`money`). Vstupy (kurzy, B0, dny) si volající ukládá,
aby šel výpočet zopakovat a později nahradit výpočtem ze sazeb měn.
"""
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def d(value):
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))


def money(value):
    return d(value).quantize(CENT, rounding=ROUND_HALF_UP)


def leg_value(buy_amount, buy_rate, sell_amount, sell_rate):
    """V(t) = kupovaná částka × kurz kupované měny − prodávaná částka × kurz prodávané měny (ve funkční měně)."""
    return d(buy_amount) * d(buy_rate) - d(sell_amount) * d(sell_rate)


def days_left(day, settlement_date):
    return max((settlement_date - day).days, 0)


def leg_fair_value(value, b0, left, total):
    """RH(t) = V(t) − B0 × zbývající dny / dny celkem; v den vypořádání a po něm RH = V(t).

    `b0` = V(den sjednání), tedy forwardové body ve funkční měně; rozpouštějí se rovnoměrně do vypořádání.
    """
    if total <= 0 or left <= 0:
        return d(value)
    return d(value) - d(b0) * Decimal(left) / Decimal(total)
