"""Očekávané datum dalšího ocenění z frekvence fondu (MN-14, rozhodnutí 2026-11-16).

Čistá funkce bez databáze. Pravidla dnů jsou návrh; konkrétní dny ocenění ze statutu řeší pozdější úkol:
- měsíčně / čtvrtletně / ročně: poslední den následujícího kalendářního období (měsíce, čtvrtletí, roku);
- týdně: nejbližší další pátek;
- denně: nejbližší další pracovní den (pondělí až pátek; státní svátky se zatím neberou).
"""

from calendar import monthrange
from datetime import date, timedelta

FRIDAY = 4
# Počet měsíců v kalendářním období.
PERIOD_MONTHS = {"monthly": 1, "quarterly": 3, "yearly": 12}


def next_valuation_date(last, frequency):
    """Datum dalšího ocenění po `last` (poslední zaúčtované ocenění, u prvního datum vzniku fondu).

    Vždy je přísně po `last`. Neznámá frekvence nebo chybějící `last` vrací False.
    """
    if not last:
        return False
    if frequency == "daily":
        day = last + timedelta(days=1)
        while day.weekday() > FRIDAY:
            day += timedelta(days=1)
        return day
    if frequency == "weekly":
        return last + timedelta(days=(FRIDAY - last.weekday()) % 7 or 7)
    months = PERIOD_MONTHS.get(frequency)
    if not months:
        return False
    # Číslo měsíce od nuly; začátek období obsahujícího `last`, o jedno období dál, poslední den toho období.
    index = last.year * 12 + last.month - 1
    start = index - index % months if months != 12 else last.year * 12
    end = start + 2 * months - 1
    year, month = divmod(end, 12)
    return date(year, month + 1, monthrange(year, month + 1)[1])
