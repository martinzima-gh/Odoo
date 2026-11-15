# IM-03 Emitent: detailní ESA a odvozené údaje

| Položka | Hodnota |
|---|---|
| Model | Sonnet 5.5 |
| Zóna | oranžová |
| Plán | oddíly 2, 3.3, 5, 6 (Emitenti a protistrany), 7 |
| Číst | `addons/custom/investra_counterparty/models/counterparty.py`, `views/counterparty_views.xml`, `tests/test_counterparty.py` |

**Cíl:** profil protistrany nese detailní ESA kód; R/NR, typ emitenta a region se odvodí; schvalovatel verzi potvrdí.

**Rozsah souborů:** v novém addonu `models/issuer.py`, `views/issuer_views.xml`, `tests/test_issuer.py`, manifest.
Modul `investra_counterparty` se nemění (pohledy rozšířit přes `inherit_id`, nabídku přejmenovat záznamem v novém addonu
jen pokud to jde bez zásahu do cizího souboru; jinak nechat název a napsat to do Výsledku).

**Mimo rozsah:** změna `required` u stávajících polí, `BANK_SECTORS`, síťové ověřování LEI.

**Kritéria přijetí:**
- CZ + 1311000 → R, CZ, VLI; DE + 2002212 → NR, EU, BANK; US + 2001002 → NR, mimo EU, NFP.
- CZ + kód začínající 2 a DE + kód začínající 1 skončí chybou podle oddílu 7.
- `sector_id` se doplní z ESA kódu; testy `investra_counterparty` projdou beze změny (repo s bankou zůstává `repo`).
- Region se mění s členstvím země k datu (`_eu_status_at`), ne s ESA.
- Potvrzenou verzi nejde změnit; nová verze vyžaduje důvod změny; stejný LEI u jiné protistrany se odmítne.

**Commit:** `Emitent: detailní ESA, odvozené údaje a kontrola`

## Výsledek

## Převzetí
