# Předávka 2026-11-13 – srozumitelná hláška knihy

**Cíl:** místo obecné chyby více společností („multi-company issue“) při založení nebo změně nástroje či ceny
říct, kterou knihu zaškrtnout v přepínači, nebo že ji uživatel nemá mezi povolenými společnostmi.

**Stav:** větev `feature/nav-prototyp`, commit s touto předávkou.

**Hotové:**
- `check_book_active()` v `investra_instruments/models/instrument.py`; volá se v `create`/`write` nástroje a ceny.
  Pravidla záznamů beze změny, jde jen o dřívější a čitelnější kontrolu (AccessError s textem).
- Test `test_book_not_active_gives_clear_message` (obě varianty hlášky a zápis).
- Testy na čisté DB (HEAD + změna, bez rozpracovaných souborů souběžné relace): investra_nav, investra_instruments,
  investra_counterparty 377 testů, 0 chyb. DB `investra_ci_knihy` smazána.
- `investra_test`: Administrator dostal povolenou společnost „Investiční společnost (test)“ (id 8149) přes ORM.

**Zbývá:** běžící Odoo na 8070 má starý Python kód; nová hláška se projeví po restartu služby (jen se souhlasem).
Verze modulu se nezvedala (bez změny dat a schématu).

**Pozor:** v `~/odoo-dev` jsou necommitnuté změny souběžné relace (fond, rozvrh fondu, NAV, ČNB, migrace);
`run_tests.sh -u` nad `investra_test` by je povýšil, proto testy jen na čisté DB z worktree.

**Číst:** `investra_instruments/models/instrument.py` (`check_book_active`), `tests/test_shared_instrument.py`.
