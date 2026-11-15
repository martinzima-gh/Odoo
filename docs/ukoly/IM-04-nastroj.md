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

**Změněné soubory** (vše v `addons/custom/investra_instrument_master/`): `__init__.py`, `__manifest__.py` (verze 20.0.0.3.0, závislost
`investra_instruments`), `models/__init__.py`, `models/instrument.py` (nový: nástroj, typ, mapa CFI), `models/masterdata_change.py`,
`wizard/__init__.py`, `wizard/masterdata_change.py`, `views/instrument_views.xml`, `data/instrument_type.xml`,
`security/ir.access.csv`, `tests/__init__.py`, `tests/test_instrument.py`. `investra_instruments` se nezměnil.

**Testy** (dočasná DB `investra_ci_master`, postup z oddílu 2 plánu; instalace `investra_instrument_master,investra_nav`, pak `l10n_cz`):
`-u investra_instrument_master,investra_instruments,investra_nav --test-enable --test-tags /investra_instrument_master,/investra_instruments,/investra_nav`
→ 441 testů, 0 selhání, 0 chyb (z toho 45 v `investra_instrument_master`, nových 16 v `test_instrument.py`; zbytek je beze změny).
Řádek „null value in column reason“ v logu je očekávaná chyba z testu, který ověřuje povinný důvod. DB i filestore po testech smazány.

**Neověřeno:** vzhled formuláře v prohlížeči (jen načtení pohledů při instalaci a kontrola polí ve zděděném pohledu); instalace do
`investra_test` a `investra_vzhled` se podle IM-00 neprovádí.

**Odchylky:**
- Model `investra.cfi.ba0088.map` v IM-01 nevznikl (byl mimo rozsah), proto ho zakládá tento úkol (bez seed dat, práva podle oddílu 5).
- `classification_gap` hlásí zatím jen chybějící BA0088, emitenta a splatnost; část o SPPI doplní IM-05.
- `cfi_code` je Char bez `size=6`: ORM by delší hodnotu ořízl a kontrola 7 znaků by neprošla.
- Splatnost se při potvrzení nevyžaduje u nástroje s příznakem „Bez splatnosti“ (`perpetual`).
- Skupina „Emitent“ (aktuální ESA) a „Test SPPI“ z oddílu 6 plánu nejsou v rozsahu IM-04 a nepřidávají se; filtr „Kategorie 7“ také ne.
- Přidáno mimo zadání: nabídka Historie změn klasifikace (jen čtení) a související pole `ba0088_requires_justification`, `ba0088_leverage_rule`.
- Formulář: přidána hlavička s tlačítky a stavem a `readonly` po potvrzení u ISIN a emitenta; podmínka viditelnosti bloku Úročení rozšířena o rodinu debt.

**Návrh vzhledu (jen návrh):** stavový pruh v hlavičce nebyl v původním formuláři; zvážit, zda ho Copilot ve vzhledové úpravě nahradí štítkem.

## Převzetí

- 15. 11. 2026 (IM-12): kód nainstalován do `investra_test` (`investra_instrument_master` 20.0.0.6.0 installed; `investra_instruments` 20.0.0.15.0). `investra_vzhled` zatím ne, viz Výsledek IM-12. Ověřeno jen stavem modulů, logem a SELECTem, ne průchodem v UI.
