# Návrh: storno a oprava obchodu, pojistka kurzu vypořádání

Stav: **schváleno a provedeno** 2026-11-12 (deník „Storno a oprava obchodu, pojistka kurzu“). Zóna: červená (účtování, pozice, NAV), provádí Claude.

## Proč

- Zaúčtovaný obchod nejde změnit ani stornovat (`investra.trade.write`: „Zaúčtovaný obchod nejde změnit“).
  Chybu v obchodu dnes nejde v UI opravit; ruční storno dokladu nestačí, protože pozice se počítá z obchodů.
- Podnět: obchod 5348 (CZK) dostal kurz vypořádání 10 070 místo 1 (zadána cena); doklad vypořádání
  MISC/2026/11/0003 nese 99,5 mld. Kč. Testovací data, uživatel je obnovovat nechce.

## 1. Storno vypořádání (obchod zpět do stavu Sjednáno, nevypořádáno)

- Pro chybu jen ve vypořádání (datum, kurz vypořádání). Tlačítko u vypořádaného obchodu s odloženým vypořádáním.
- Událost vypořádání se stornuje k jejímu datu (`_reverse_events`), `settlement_event_id` se vyprázdní
  (původní událost zůstává dohledatelná přes storno), stav zpět na `unsettled`; datum a kurz vypořádání jdou opravit
  a znovu Vypořádat.
- Rozvaha ke dni vypořádání: událost vypořádání je zároveň zaúčtování obchodu → stejný krok vrací obchod do `unsettled`
  a vyprázdní i `event_id`.

## 2. Storno a oprava obchodu (stejně jako u splátek, deník 2026-11-12 „Zámek a storno splátky“)

- Okno s důvodem: **Stornovat** / **Opravit** (storno a nový obchod v návrhu s odkazem na opravovaný, pole `replaced_id`).
- Storno všech událostí obchodu (obchod i vypořádání) k jejich datům, nový stav **Stornováno** (`reversed`), důvod.
- Stornovaný obchod se **nepočítá do pozic** (`_recognised`, `_holdings`, `_check_sale`, nabídka držených nástrojů).
  Návrhy obchodů se do pozic počítají dál (otevřený bod „Návrhy obchodů v pozicích“ tím nemění).
- Zámek ocenění: storno nejde, když obchod spadá do zamčeného ocenění (`_check_valuation_lock`, jako u splátek);
  pozdější ocenění v návrhu se přepočte.
- Schvalovací matice: nový úkon `trade_reverse` (Storno a oprava obchodu), výchozí nastavení jako `repayment_reverse`.
- Stav, události a důvod zapisuje jen storno (rozšířit `SYSTEM_TRADE_FIELDS`).

## 3. Pojistka kurzu

- Nástroj v měně fondu: Kurz i Kurz vypořádání ve formuláři skryté, na serveru vynucené 1 (omezení).
- Cizí měna: upozornění ve formuláři, když se kurz vypořádání liší od kurzu obchodu o víc než 10 %; neblokuje.
- Náhled Očekávané zaúčtování i u nevypořádaného obchodu (doklad vypořádání před stiskem Vypořádat).

## Ověření

Testy: storno vypořádání a nové vypořádání (předvaha shodná s obchodem bez chyby); storno a oprava obchodu
(pozice, ocenění, `positions_ledger`); storno v zamčeném období odmítnuto; matice; CZK kurz vynucený; upozornění
cizí měny. Celá sada na čisté DB `investra_ci_*`. Migrace: nový stav a pole; stávající obchody beze změny
(ověřit předvahu na kopii `investra_test`). Nástroj 5348 pak opravit stornem vypořádání v UI.

## Otázky k rozhodnutí

1. Storno vypořádání jako samostatný krok (doporučeno), nebo jen storno celého obchodu?
2. Storno v zamčeném ocenění: odmítnout jako u splátek (doporučeno), nebo připustit s výjimkou zámku?
3. Matice: storno obchodu se stejným nastavením druhé osoby jako storno splátky (doporučeno)?
4. Kurz cizí měny: hranice upozornění 10 % (doporučeno), nebo jiná?
