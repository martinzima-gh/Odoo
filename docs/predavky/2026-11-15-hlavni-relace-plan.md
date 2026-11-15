# Předávka 2026-11-15 – hlavní relace (zadání, plán vývoje)

**Cíl:** hlavní relace (Fable) jen analyzuje, píše zadání do `docs/ukoly/` a hotové prompty s určením modelu;
programují Opus, Sonnet a Haiku v samostatných relacích. Uživatel chce jednu verzi aplikace a šetřit kredity.

**Stav:** větev `feature/instrument-master`, poslední commit `5894951` (+ tato předávka), pracovní strom čistý.
Běží 8070 `investra_dev`, 8071 `investra_test`, 8072 `investra_vzhled`; databáze `investra` ještě neexistuje.

**Hotovo:**
- IM-01 až IM-12: evidence nástrojů, SPPI na nástroji, výplata Nepravidelně, variabilní sazba (`investra_nav` 20.0.0.29.0),
  vše nainstalované v `investra_test` i `investra_vzhled`.
- Pravidlo „Jedna verze aplikace“ v `CLAUDE.md` (výjimka: společná instance Copilota a Antigravity nad `~/odoo-review`).
- `docs/plan-dalsiho-vyvoje.md`: etapy ST, DE (FX forward a swap), PF, CN, EC (ECL jako procento), FO, VZ, UX s modely a prompty.

**Zbývá (první krok nahoře):**
1. IM-13 stojí na chybě `create_book` (odložené načtení osnovy přepíše měnu a šablonu osnovy po commitu); podrobnosti
   v `docs/predavky/2026-11-15-im13-pracovni-databaze.md`. Připravit zadání opravy (červená zóna: kniha, měna, osnova)
   a prompt pro Opus; po opravě pokračování IM-13 (Investra Services, databáze `investra`, zastavení starých instancí).
2. Ověřit dopad chyby na stávající data: v `investra_test` má Investra Services šablonu osnovy `investra_fund`.
3. Po IM-13: ST-01 (sloučení do `main`), pak DE-01 (návrh FX derivátů) podle plánu.
4. Chyba nabídky Přehled na 8072: čeká se na text chyby z prohlížeče od uživatele.
5. Doplnit pravidla Copilota a Antigravity o společnou instanci (ST-04); zápis dnešních rozhodnutí do Claude Doc.

**Rozhodnutí:** vše v `docs/rozhodnuti.md` s datem 2026-11-15 (naposledy: jedna pracovní databáze, schvalování jedním
uživatelem v `investra`, Investra Services v pracovní databázi, jedna verze aplikace, plán vývoje, ECL jako procento).

**Otevřené otázky:** IFRS 9 B5.4.5/B5.4.6 a zjednodušení ECL ověřit s auditorem; zóna opravy `create_book` a souhlas
Martina; smazání starých databází až na výslovný pokyn.

**Číst:** `docs/predavky/2026-11-15-im13-pracovni-databaze.md`, `docs/plan-dalsiho-vyvoje.md`,
`docs/ukoly/IM-13-nova-databaze-s-ukazkami.md`, `docs/ukoly/IM-00-prehled.md`.
