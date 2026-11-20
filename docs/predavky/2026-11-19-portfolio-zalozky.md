# Předávka 2026-11-19: Portfolio – srozumitelné záložky (AG-020 až AG-022)

## Cíl
Sjednotit názvy (Portfolio × Obchodní model), přeuspořádat nabídku Portfolio a zpřehlednit formuláře obchodu, ceny, splátky,
derivátů, portfolia a zařazení. Zaúčtování a kontroly se nemění (oranžová zóna).

## Stav
- Větev `ukol/ZJ-13-14`, poslední commit `ce4f8e4` (pushnuto, `~/odoo-review` synchronizovaný).
- Testy Odoo `investra_instruments+`: 838 testů, 0 selhání; `check_views.py` bez chyb.

## Hotové
- Zadání AG-020 (portfolia, zařazení, nabídka), AG-021 (obchody, ceny), AG-022 (splátky, deriváty), provedl Copilot, převzal Claude.
- Čísla změněna oproti plánu (AG-012 až AG-014 byla obsazená); rozhodnutí 2026-11-19 v `docs/rozhodnuti.md`.
- Upřesnění rozsahu: onchange kategorie → model v `investra_instrument_master`; „Prodat vše“ a hromadné Schválit jako úzké metody;
  úprava testu swapu po automatických nohách.
- Opravy při převzetí: kurz cizí měny předvyplňuje `investra_nav` (`float()`, chybějící kurz nezastaví), datum vypořádání jen přes
  onchange, vzdálená noha swapu přes onchange `leg_ids`.

## Zbývá
1. Povýšení pracovní databáze `investra` je HOTOVÉ (2026-11-19, se zálohou `zalohy/investra-2026-11-19-pred-AG-020-022.dump`;
   verze instruments 20.0.0.15.0, instrument_master 20.0.0.8.1, nav 20.0.0.38.0, derivative 20.0.0.3.0; bez chyb v logu, instance 8071 běží).
   ZBÝVÁ ruční zkouška v UI na 8071 (Martin, příště; prohlížeč Claude neovládá): nabídka Portfolio (Obchody, Splátky nástrojů,
   Deriváty, Ceny, Zařazení nástrojů; Portfolia v Nastavení › Fondy), nový nákup/prodej (předvyplnění kurzu cizí měny, datum
   vypořádání, „Prodat vše“, náhled zaúčtování), cena, mimořádná splátka (náhled), swap (obě nohy, vzdálená noha). Nálezy zapsat
   a opravit.
2. Zapsat rozhodnutí 2026-11-19 do Claude Doc (tabulka Přijatá rozhodnutí) – čeká na souhlas.
3. Do `main` jen na výzvu Martina (před tím `tools/run_tests.sh all`).

## Rozhodnutí
R1 názvy Portfolio; R2 pořadí nabídky, Portfolia v Nastavení › Fondy; R3 předvyplnění kurzu; R4 datum vypořádání = sjednání.
Příloha u ceny: zatím jen chatter (soubory jdou do filestore, ne do DB).

## Otevřené otázky
- Datum vypořádání se v novém formuláři přepíše jen při první změně data sjednání (poté se bere jako ruční).
- Výchozí nohy derivátu v `default_get` se použijí i při `create` bez `leg_ids` (testy neovlivnilo).

## Číst
CLAUDE.md; docs/ukoly/AG-020-portfolia-zarazeni-nabidka.md; docs/ukoly/AG-021-obchody-a-ceny.md;
docs/ukoly/AG-022-splatky-a-derivaty.md; docs/ukoly/CP-2026-11-19-AG020-022.md
