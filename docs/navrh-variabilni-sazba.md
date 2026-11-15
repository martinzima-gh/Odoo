# Návrh: variabilní úroková sazba (IM-11, krok 1)

Stav: **návrh ke schválení Martinem**, kód se nemění. Zóna červená (naběhlá hodnota, EIR, kalendář toků).

## Ověření stavu v kódu (15. 11. 2026)
- Body „Stav dnes“ ze zadání platí: jedna sazba `coupon_rate`; `action_generate_schedule` maže a generuje celý kalendář
  a po nestornované splátce odmítne; `_accrued_value` počítá EIR **při každém volání** z ceny obchodu a všech
  současných toků po obchodu (EIR se nikde neukládá). Přepis budoucích toků proto dnes změní naběhlou hodnotu i zpětně.
- `_coupon_periods` / `_earned_coupon_unit` (RH a naběhlý úrok obchodu) dělí kupón lineárně v rámci období;
  změna částky kupónu by zpětně změnila vydělaný úrok za dny téhož období před změnou.
- Lineární úročení umí jen jeden tok (vklad ve splatnosti); prodej v naběhlé hodnotě není podporovaný (beze změny).
- Zámek: `investra.valuation._locking(company, day)` = ocenění Ke schválení až Potvrzeno s datem ≥ day.

## Opora ve standardu – NEOVĚŘENO
EUR-Lex (nařízení (EU) 2023/1803, CS i EN) vrátil 15. 11. 2026 prázdnou odpověď (HTTP 202); omezení jsem neobcházel.
Odkazy jsou z paměti a před krokem 2 je ověří Martin nebo auditor proti znění přijatému EU:
- IFRS 9 odst. B5.4.5: u nástroje s pohyblivou sazbou pravidelné přecenění toků podle tržních sazeb mění efektivní
  úrokovou míru; je-li nástroj zaúčtován v jistině, dopad na účetní hodnotu obvykle není významný.
- IFRS 9 odst. B5.4.6: jiné změny odhadu toků → hrubá účetní hodnota = současná hodnota nových toků při původní EIR,
  rozdíl do výsledku. Odst. 5.4.1: úrokový výnos metodou efektivní úrokové míry.

## Datový model (doporučení)
1. `investra.instrument.rate_type` (fixed / variable, výchozí fixed; po prvním obchodu jen fixed → variable).
2. `investra.instrument.rate.period`: nástroj, platí od, sazba % p.a., poznámka (referenční sazba + marže, jen text),
   zadal, kdy (create_uid/create_date). První řádek = `start_date` a dnešní `coupon_rate`. U variabilní je `coupon_rate`
   počítané = poslední známá sazba (jen ke čtení). Nové období jen s „platí od“ po posledním; opravit/smazat jde jen poslední.
3. Tok `investra.instrument.cashflow`: `estimated` (odhad), `active` a `superseded_on` (od kdy neplatí). Nahrazené toky
   se **nemažou, jen archivují** – výpočet tak umí složit kalendář „jak byl znám před změnou“. Stávající kód čte
   `cashflow_ids` bez archivovaných, takže pevná sazba počítá beze změny.

## Algoritmus
- Generátor: období přes změnu sazby po částech (jistina × sazba_i × část roku úseku); období po poslední známé
  sazbě touto sazbou s příznakem odhad. Pevná sazba = jedno období sazeb → stejné toky jako dnes.
- Průvodce „Zadat novou sazbu“ (platí od, sazba, poznámka) s textem „Co se stane“: založí období sazby; toky Úrok
  s datem > platí od archivuje (superseded_on = platí od) a založí nové; toky s datem ≤ platí od a jistina beze změny;
  zápis do historie nástroje (`_log_cashflow_change`). Obejde zámek „Kalendář po splacení“, protože mění jen budoucí úroky.
- Odmítnutí: (a) existuje zamykající ocenění (`_locking`) ke dni ≥ platí od u společnosti fondu, který nástroj drží
  nebo držel; (b) existuje nestornovaná splátka s datem > platí od (tok už je v návrhu/zaúčtovaný).
- EIR (`_accrued_value`, varianta a): pro každý obchod se dny změn c1 < c2 … (po datu obchodu, ≤ den výpočtu) dělí na
  úseky. Úsek 0: EIR0 z (datum obchodu, −pořizovací částka) a toků platných před c1; AC(c1) = engine.amortised_cost
  s EIR0. Úsek k: EIRk z (ck, −AC(ck)) a toků platných od ck. Výsledek: k žádnému dni < ck se hodnota nezmění,
  v ck nevzniká skok. Engine dostane `amortised_cost_segments(cost, start, versions, day, basis)`; mimořádné splátky
  dál přes koeficient množství (EIR se jimi nemění).
- Lineární úročení (jen jeden tok): po změně lineárně z AC(ck) na novou splatnou částku za (ck, splatnost].
- RH: `_earned_coupon_unit` u variabilní sazby počítá vydělaný úrok po úsecích sazby (jistina × sazba × část roku),
  ne podílem z celého kupónu; naběhlý úrok obchodu (`_accrued_coupon_unit`) tím také. Pevná sazba beze změny.
- Prodej: beze změny (naběhlá hodnota dál odmítne, RH po úsecích funguje i pro prodej).
- Ocenění a doklady se zpětně nemění; nová sazba se projeví od nejbližšího ocenění.

## Varianty k EIR
| | a) prospektivní EIR (B5.4.5) – **doporučeno** | b) původní EIR, rozdíl do výsledku (B5.4.6) |
|---|---|---|
| ke dni změny | bez výsledkového rozdílu | jednorázový zisk/ztráta |
| u pohyblivé sazby | odpovídá podstatě nástroje | nepřiléhavé, výkyvy výsledku |
| data | archivované toky | stačí nové toky + vlastní doúčtování |

Varianta c) „dnešní kód“ (přepsat toky bez segmentů) mění minulé dny – nepřípustná.

## Číselný příklad (spočteno funkcemi engine.py, act365)
Nákup 1 000 000 kusů za 0,98 dne 1. 1. 2027, splatnost 1. 1. 2028, pololetně, 4 %; od 1. 7. 2027 nová sazba 5 %.
Kupón 1. 7. 2027 = 19 835,62 (beze změny); kupón 1. 1. 2028: 20 164,38 → 25 205,48.
- EIR0 = 6,184614 %; AC 1. 4. 2027 = 994 608,63; AC 1. 7. 2027 (po kupónu) = 989 765,37.
- a) EIR1 = 7,228004 %; AC 1. 4. beze změny; AC 1. 10. 2027 = 1 007 329,58; rozdíl ke dni změny 0.
- b) AC 1. 7. při EIR0 = 994 656,26 → do výsledku 4 890,89; AC 1. 10. = 1 009 815,35.
- dnešní kód: EIR 6,704151 % a AC 1. 4. by se zpětně změnilo na 995 806,35.

## Migrace
Bez přepočtu dat: `rate_type = fixed` všem; pre-init nebo post-init založí jedno období sazby (start_date, coupon_rate)
u nástrojů s kalendářem; `estimated = False`, `active = True`. Ověřit na čisté DB i na kopii `investra_test`.

## Testy (krok 2)
1. Pevná sazba: všechny stávající referenční scénáře beze změny očekávaných hodnot (testy všech `investra_*`).
2. Generátor variabilní: toky po částech přes změnu uprostřed období; odhad = poslední sazba; příznak `estimated`.
3. Příklad výše: AC 1. 4. = 994 608,63 před i po změně; AC 1. 7. = 989 765,37; AC 1. 10. = 1 007 329,58.
4. Dvě změny po sobě a obchod mezi nimi (úsek začíná obchodem); mimořádná splátka po změně (koeficient).
5. Lineární vklad ve splatnosti se změnou sazby; RH dluhopis: vydělaný úrok před změnou se nezmění, naběhlý úrok obchodu.
6. Odmítnutí: zamčené ocenění ≥ platí od; splátka po platí od; platí od ≤ posledního období; historie nástroje.

## K rozhodnutí: 1. Varianta EIR a) / b). 2. Archivace nahrazených toků (doporučeno) vs. přegenerování starých toků z období sazeb
(nefunguje u ručních toků „Nepravidelně“). 3. Platí od kdykoli (po úsecích), nebo jen k začátku kupónového období.
