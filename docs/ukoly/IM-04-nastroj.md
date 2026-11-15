# IM-04 Nástroj: BA0088, CFI, atributy a potvrzení klasifikace

| Položka | Hodnota |
|---|---|
| Model | Sonnet 5.5 |
| Zóna | oranžová |
| Plán | oddíly 2, 3.4 (bez řádku SPPI), 5, 6 (Nástroj), 7 |
| Číst | `addons/custom/investra_instruments/views/instrument_views.xml` (řádky 1–110), třídu `InvestraInstrument` v `models/instrument.py` (řádky 115–330), `docs/vzhled/navrh-detail-nastroje.html` |

**Cíl:** nástroj nese druh ČNB, CFI a doplňkové atributy; schvalovatel klasifikaci potvrdí; pozdější změna jde jen
s důvodem a zapíše se do historie.

**Rozsah souborů:** v novém addonu `models/instrument.py`, `models/masterdata_change.py`, `wizard/masterdata_change.py`
a pohled, `views/instrument_views.xml`, `data/instrument_type.xml` (jen `ba0088_required`), `tests/test_instrument.py`,
manifest, práva. Modul `investra_instruments` se nemění.

**Mimo rozsah:** SPPI (IM-05), `active`, povinnost BA0088 při uložení, změny obchodu a NAV.

**Kritéria přijetí:**
- CFI: `ABCDEF` projde, `abcdef` se uloží velkými písmeny; 5 a 7 znaků a číslice se odmítnou.
- BA0088 211 → rodina equity; 141 → debt a ve formuláři splatnost, nominál, kupón.
- Kód s `leverage_rule` a s `requires_justification` se chová podle oddílu 7 (test na pomocném kódu založeném v testu).
- Potvrzení bez BA0088 u typu s `ba0088_required` nebo bez emitenta u kódu s `requires_issuer` se odmítne.
- Po potvrzení přímý zápis BA0088, CFI, ISIN nebo emitenta skončí chybou; průvodce změnu provede a založí řádek historie.
- Neplatná kontrolní číslice ISIN jen upozorní.
- Testy `investra_instruments` a `investra_nav` projdou beze změny.

**Commit:** `Nástroj: BA0088, CFI a potvrzení klasifikace`

## Výsledek

## Převzetí
