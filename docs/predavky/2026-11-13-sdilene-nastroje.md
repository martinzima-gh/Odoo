# Předávka 2026-11-13: sdílené nástroje a pravidlo knihy

**Cíl:** nástroj s ISIN je sdílený a mění ho jen kniha investiční společnosti, nástroj bez ISIN patří fondu;
jedinečný ISIN + měna, kód podle typu, změny nástroje se ukážou v příštím ocenění.

**Stav:** větev `feature/nav-prototyp`, kód v c069146 (pushnuto), dokumentace v následujícím commitu.
`investra_instruments` 0.14.0 (migrace), `investra_nav` 0.24.0. Claude Doc rev 332, `docs/architektura.md` je jeho export.

**Hotovo:**
- Plán `docs/navrh-sdilene-nastroje.md` (varianta B, odpovědi uživatele), deník rozhodnutí, otevřené body, Claude Doc.
- `instrument.py`: `company_id`, `code` (prefix typu + řada `investra.instrument`), `identifier_kind`/`identifier`,
  typ `isin_required`/`code_prefix`, jedinečné indexy, record guard, zámek měny, historie změn (podtyp
  `mt_instrument_change`), toky s knihou a historií, převzetí sdílených nástrojů založením knihy investiční společnosti.
- Pravidla záznamů pro nástroje a toky; formulář a seznam nástrojů; kontrola `instrument_changes` (upozornění).
- Migrace 0.14.0: pre zastaví upgrade při duplicitě, chybějícím ISIN, sdíleném bez ISIN nebo fondovém s ISIN.
- Testy: pomocníci `with_ids`, `manager_book` v `investra_instruments/tests/common.py`; nové `test_shared_instrument.py`.
  Čistá DB: celá sada 543 testů (2 chyby opraveny, pak 407 testů dotčených modulů 0 chyb). DB `investra_ci_*` smazány.
- `investra_test` se zálohou `zalohy/investra_test-2026-11-13-pred-sdilene-nastroje.dump`: ISIN 45, 46, 466, 467, 5710
  přes ORM (starý kód), vklad 1561 → fond 2931, upgrade, kniha „Investiční společnost (test)“ převzala 7 sdílených
  nástrojů, vklad má číslo smlouvy. Doklady, řádky, MD/D, obchody, ocenění, FK, toky, ceny a zařazení shodné.
  Testy na generálkové kopii: jen známá selhání (5× „cannot approve“, 3× `TestApprovalMatrix`). Web 8071 znovu spuštěn.
- `tools/nav_demo`: sdílené nástroje se hledají podle ISIN + měny, vklad má fond a číslo smlouvy.

**Zbývá – první krok:** uživatel vyzkouší v UI 8071 nástroj (kód, ISIN, identifikátor, fond) a kontrolu „Údaje
nástrojů v portfoliu…“; pak navrhnout další otevřený bod (doporučeno „Oddělení uživatelů podle fondů“).

**Pozor:**
- `tools/vzhled_fiktivni_data.py` (relace vzhledu) zakládá nástroje bez ISIN a fondu; po upgradu by selhal.
- Souběžná relace zvedla `investra_entity` na 0.7.1 (53cba5b); `investra_test` má 0.7.0, `run_tests.sh` bude chtít upgrade.

**Otevřené otázky:** žádné.

**Přečíst:**
1. `CLAUDE.md`
2. tato předávka
3. `docs/navrh-sdilene-nastroje.md`
4. `addons/custom/investra_instruments/models/instrument.py` (třída `InvestraInstrument` po `_check_identifier`)
