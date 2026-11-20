# ZADÁNÍ PRO AGENTA – dávka ZJ-07 až ZJ-19 (třídy, poplatky, účetní období, cena odúčtování, dividendy, FVOCI, daně)

Verze 19. 11. 2026 (jediný soubor; nahrazuje prompt v3/v4, technický plán, postup, doplněk v4, podklad manuálu a zadání daní v2/v3).
Připravil Claude (Opus) čtením `ukol/ZJ-13-14` @ `e1a23bc`; návrhy kódu NEBYLY spuštěny. Schválil Martin 19. 11. 2026.
**Model: Claude Opus 5.5, úsilí high, jeden běh** (červená zóna: výpočet NAV, daně, migrace).
Cesty v kódu relativně k `addons/custom/`, odkazy `soubor:řádek` platí pro `e1a23bc`.

## 0. Prompt (vlož agentovi; tento soubor ulož do ~/odoo-dev/docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md)

```
Přečti CLAUDE.md a docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md (celé zadání v jednom souboru; oddíl „Přednosti“ řeší rozpory).
Z repozitáře čti jen docs/ukoly/ZJ-07, ZJ-08, ZJ-09 a místa kódu, která zadání uvádí (soubor:řádek k e1a23bc), a body OVĚŘ;
nic dalšího neprocházej celé. Vše je schválené (Martin, 19. 11. 2026) včetně odchylek C0.1–C0.8 – NEposílej ke schválení.
Návrhy kódu jsou nespuštěné: převezmi je, uprav podle skutečného kódu a otestuj; chybný návrh oprav a zapiš jako odchylku do Výsledku.

KROK 0 – sloučení (Martin zkontroloval v prohlížeči ZJ-13/14 i AG-019–022): v ukol/ZJ-13-14 tools/run_tests.sh all; povýšení investra
po AG-020–022, pokud ještě neproběhlo (záloha, upgrade investra_instruments, investra_instrument_master, investra_nav, investra_derivative,
restart investra-web, snímek ocenění 35 a 39); sloučení do main (merge commit „Sloučení ZJ-13, ZJ-14, AG-019 až AG-022“), push.
Databáze: REVOKE CREATE ON SCHEMA public FROM PUBLIC (schválil Martin) – zapiš do tools/db/dbeaver_ro_grants.sql, spusť, ověř, že
dbeaver_ro tabulku nezaloží a Odoo funguje; do deníku. Pak větev ukol/ZJ-07-dane-a-tridy z main. Do main nic.

KROK 1 – zadání podle docs/ukoly/_sablona.md; Technický plán = odkaz na oddíl tohoto souboru + odchylky (NEpřepisuj ho celý):
ZJ-09 (oddíl 2; body 2b, 2c „později“), ZJ-08 (oddíl 3; bod 4 ruční krystalizace „později“), ZJ-17-ucetni-obdobi.md (4),
ZJ-16-poplatek-obchodu.md (5), ZJ-15-cena-vyskladneni.md (6), ZJ-19-dividendy-a-ex-kupon.md (7), ZJ-18-fvoci-do-oci.md (8; uzavírá
otevřený bod „Účtování FVOCI“), ZJ-07 (9 + Právní rámec z oddílu 1). Deník: D1–D14, odchylky C0 a oddíl 12. Commit (vč. tohoto souboru).

KROK 2 – programuj v pořadí oddílů 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9, commit po každém oddílu (uvnitř po bodech). Po každém oddílu testy
dotčených modulů a snímek ocenění 35 a 39 (docs/sql/28-snimek-oceneni.sql) – musí zůstat stejný. Zastav se a napiš mi JEN když:
něco ze zadání v kódu nejde; výsledky existujících ocenění (35, 39, referenční scénáře) by se bez nového nastavení změnily; SELECT najde
nástroje s vyplněnou třídou (A5) nebo data, která migrace neumí převést; naběhlá hodnota nejde napojit na kapitalizovaný poplatek (E4);
v databázi investra je pozice FVOCI (před oddílem 8 napiš kolik a jaké – jejich výsledek se změní).
Když ti dochází kontext: dokonči rozdělaný bod, commitni, napiš předávku do docs/predavky/ a skonči zprávou, kde pokračovat.

ZÁVĚR: run_tests.sh all, migrace zkouškou na kopii, povýšení investra se zálohou, snímek 35 a 39 před a po. Výsledek do ZJ-07, 08, 09,
15, 16, 17, 18, 19; manuál (kapitola 10 + obchody, fond, portfolio/FVOCI, dividendy, daň), otevřené body (poradce: prostý zápočet,
podfond SICAV, uznatelnost ECL; metodik: daň z realizace akcií FVOCI ve výsledku vs. kapitálu, řádky ČNB pro OCI a odloženou daň;
dceřiný podíl C0.8), předávka do docs/predavky/. Push. Na konci mi napiš krátce: co šlo ven, odchylky od zadání, referenční příklady
daní (každé číslo proti oddílu 9), výsledky testů a seznam ke kontrole v prohlížeči (portfolio třídy, třída bez podílu na společných
položkách a upozornění na úplatu, konec účetního období na fondu, poplatek obchodu v cizí měně, prodej s cenou odúčtování, dividenda
česká i zahraniční se zápočtem, dluhopis v ex-kupónové lhůtě, pozice FVOCI a sloupec OCI, záložka Daň fondu, Daňová pravidla,
odložená daň z OCI, rozpad daně v ocenění, XLS list Daň).
```

## Přednosti (rozpory mezi oddíly řeší tento seznam)
1. Pořadí: oddíly 2 → 9 (A → D → F → E → B → H → G → C). Pořadí „A → B → C“ a „Pořadí commitů“ v oddílech níže neplatí.
2. Všude „od 1. 1.“ znamená **od začátku účetního období fondu** (D6, oddíl 4) – výpočty, popisky („Pohyb od začátku období“), testy.
3. Rozvahový účet ve výjimce daně smí mít i splatné pravidlo (D10) – mění C0.5 a kontrolu v C1 („rozvahový jen s Odloženou“).
4. Pohledávka za zahraniční daní k vrácení: účet z oddílu 7 (H1), ne 341200 z C5.
5. „Zdanění při realizaci“ (C10) je jen přes účty a výjimky (oddíl 8, G3); poziční přechodný rozdíl se nedělá. FVTPL se zdaní hned (D7).
6. Pokyny v původním zadání daní „pošli plán ke schválení“ a jeho „ZÁVĚR“ neplatí; řídí prompt v oddílu 0.
7. Při rozporu kódu: nejdřív text oddílů 3–8 (novější), pak postup s kódem, pak technický plán.
8. Odkazy v textu na „zadání v2/v3“ = oddíly 1 a 9.1; „plán“ / „plán C5“ = 2.1, 6.1, 9.2; „postup“ = 2.2, 6.2, 9.3; „doplněk“ = oddíly 2.3, 3–8; „podklad manuálu“ = oddíl 10.


# 1. Rozhodnutí Martina a právní rámec

ROZHODNUTÍ MARTINA (zapiš do deníku):
D1. DA-01 se slučuje do ZJ-07 (v docs/plan-dalsiho-vyvoje.md „nahrazeno ZJ-07“).
D2. Výjimku jde nastavit na jakýkoli výsledkový účet, i na účty úplat a odměny. Přednost má výjimka na účtu; volba „Základ: po kroku“
    u daně (ZJ-12) platí pro účty úplat a odměny bez výjimky. Ve Schématu výpočtu informace „Úplata X má daňovou výjimku na účtu“.
    Změna nastavení se projeví dalším výpočtem (daň se počítá od 1. 1., rozdíl se doúčtuje).
D3. Daňová ztráta minulých let se nepočítá; uživatel ji zadá opravou základu (ZJ-12). Odložená daň se počítá jen tehdy, když fond
    použije daňové pravidlo se způsobem „Odložená“ (např. přecenění FVOCI do kapitálu); jinak ji uživatel účtuje ručně.
D4. Daňová pravidla jsou SDÍLENÁ pro všechny fondy (Nastavení › Daně › Daňová pravidla); fond, který potřebuje zvláštní, zadá nové.
    Každé pravidlo má vlastní sazbu (verze s platností od data), vlastní účet daně (výsledovka nebo vlastní kapitál) a vlastní rozvahový účet.
D5. Přiřazení účtů k pravidlům je na úrovni FONDU (každý fond má vlastní knihu a účty): výchozí pravidlo fondu pro všechny výsledkové účty
    + tabulka výjimek (účet → daňové pravidlo). Rozvahové účty dani nepodléhají, pokud nejsou ve výjimkách.

PRÁVNÍ RÁMEC (rešerše 19. 11. 2026, ZDP 586/1992 Sb. ve znění k 1. 8. 2026, zakonyprolidi.cz; [Z] ověřeno v zákoně, [N] neověřeno):
- Sazba 21 % (§ 21/1), základní investiční fond 5 % (§ 21/2); ZIF podle § 17b/1: a) kótovaný fond bez 10% podílu právnické osoby,
  b) každý podílový fond, c) fond/podfond investující podle statutu víc než 90 % do vyjmenovaných finančních aktiv (bez nemovitostí),
  d) srovnatelný fond EU/EHP. [Z] Část roku jako ZIF (§ 20a, § 21/6) – mimo rozsah, ručně.
- Samostatný základ (§ 20b): podíly na zisku ze zahraničí, 15 % (§ 21/4); zvláštní sazba pro ZIF v textu není [Z], praxe: 15 % i u ZIF, do samostatného základu jen zahraniční dividendy (ověřeno s daňovým poradcem);
  mimo obecný základ (§ 23/4/b), ztráta obecného základu se nezapočte [N].
- Osvobozeno: dividendy a převod podílu v dceřiné společnosti (§ 19/1/ze, zi, odst. 9; 10 % a 12 měsíců); změna RH takového podílu mimo
  základ (§ 23/4/k). [Z] Podílový fond jako mateřská společnost [N].
- Přecenění na RH do výsledku je zdanitelné průběžně (§ 23/9) [Z]; přecenění do vlastního kapitálu až při realizaci (§ 23/19) [Z]
  → odložená daň typicky jen u přecenění do kapitálu (FVOCI) a nemovitostí [N].
- Příjmy zdaněné srážkou (české dividendy 15 %, § 36/2) mimo základ (§ 23/4/a), srážka konečná. [Z]
- Neuznatelné (§ 25/1): penále a pokuty (f), výdaje na příjmy, které nejsou předmětem daně (i), daň z příjmů (s), reprezentace (t),
  náklady na držbu podílu v dceřiné společnosti (zk); úplata za obhospodařování a výkonnostní odměna zvláštní pravidlo nemají. [Z]
- Odložená daň (vyhl. 501/2002, § 78): závazková metoda, sazba období vyrovnání, závazek vždy, pohledávka s ohledem na opatrnost. [Z]
- Otázky pro daňového poradce (do ZJ-07 a docs/otevrene-body.md): zápočet zahraniční daně (rozhodnuto: započitatelnou část určí uživatel při zaúčtování dividendy, poradce potvrdí prostý zápočet do výše české daně); [osvobození
  § 19 u podílového fondu a SICAV – rozhodnuto: běžná výjimka nabízena u všech fondů, bez nápovědy]; krácení nákladů na osvobozené příjmy (které náklady a jakou metodou: poměr výnosů, hrubé nebo čisté
  výnosy, započíst nerealizované zisky?); přecenění nemovitostí; test 90 % a 10 % a ztráta statusu ZIF v roce;
  podfondy. Odpovědi musí jít NASTAVIT (pravidla, sazby, výjimky) bez změny kódu.

D6. ÚČETNÍ OBDOBÍ: všude, kde výše stojí „od 1. 1.“, platí „od začátku účetního období fondu“ (hospodářský rok podle knihy,
    `fund._fiscal_year_start(datum)`, ZJ-17). Týká se základu splatné daně, zaúčtované daně, zápočtu (681400), neuznatelných % z výnosu,
    sloupce výjimek „Pohyb od začátku období“ a konce roku (odhad k poslednímu dni období, doměrky 681200). Roční úplaty a období výkonnostní
    odměny se řídí také účetním obdobím.
D7. FVTPL: přecenění do výsledku se zdaňuje hned (§ 23/9) – žádná výjimka ani odložená daň; testem ověř, že přecenění FVTPL je v základu.
D8. FVOCI (ZJ-18 v této dávce): úrok efektivní mírou a ECL do výsledku (ECL ručním dokladem), zbylé přecenění do OCI (role
    `revaluation_reserve`); akcie FVOCI bez recyklace – při prodeji převod rezervy na „Realizované přecenění FVOCI“ (kapitál), dluh s recyklací.
D9. ODLOŽENÁ DAŇ Z OCI: sdílené pravidlo „Odložená – přecenění do kapitálu“ ve dvou variantách sazby jako výchozí data šablony:
    „Odložená FVOCI 21 %“ a „Odložená FVOCI 5 %“ (způsob Odložená, účet daně = `revaluation_reserve_tax` (kapitál), rozvahový 348000,
    bez pohledávky). Výjimka fondu: hlavní účet `revaluation_reserve` → toto pravidlo; základ = zůstatek účtu k datu (kumulativní,
    nenuluje se), účet „Opravná položka ECL v OCI“ se nepočítá.
D10. REALIZACE AKCIÍ FVOCI: výjimka fondu na účtu „Realizované přecenění FVOCI“ s VÝCHOZÍM (splatným) pravidlem fondu. Nové obecné
    pravidlo: rozvahový účet ve výjimce se splatným pravidlem přispívá do základu svým POHYBEM od začátku období se znaménkem výnosu
    (kredit = +); dosud byly rozvahové účty jen u Odložené. Daň se účtuje na 681000 (výsledek); otevřený bod pro metodika (IAS 12.61A).
D11. „Přidat běžné výjimky“: když má fond zařazení FVOCI, přidá i výjimky D9 a D10 (pravidlo D9 podle sazby výchozího pravidla fondu:
    5 % → Odložená FVOCI 5 %, jinak 21 %). Bez FVOCI se nic nepřidá.
D12. ECL v manuálu: náklad ECL („Opravné položky ECL“) doporučit jako výjimku „Mimo základ“ – tlačítko ji NEpřidává (rozhodne poradce).
D13. TŘÍDA BEZ PODÍLU (ZJ-08): nenese daň ze sdílených položek (poměr 0); daň ze zisku převedeného jako odměna na M nesou ostatní třídy.
D14. DIVIDENDY (ZJ-19): zaúčtují se záznamem dividendy – hrubá na 714100/714200/714300 podle druhu, sražená daň u české na 681100,
    u zahraniční započitatelná část (do smluvní sazby) na 681400, přeplatek na pohledávku k vrácení nebo náklad. Výpočet daně tak
    dostane účty správně bez ručních dokladů; ruční doklady dál fungují.

# 2. ZJ-09 jádro – třída portfolia (část A)

## 2.1 Plán
Rozhodnutí 17. 11. 2026 („Třída portfolia“) platí: `investra.fund.portfolio.class_id` – prázdné = **sdílené portfolio** všech tříd
(výsledek se dělí poměrem), vyplněné = portfolio jen této třídy. Stejný nástroj může být ve sdíleném i v portfoliu třídy (dvě pozice,
dvě průměrky – pozice se vedou po dvojici nástroj + portfolio už dnes, `investra.trade._holdings`, `_cost_walk`).

A1. Pole Třída na portfoliu (doména třídy fondu), zámek po prvním obchodu, splátce, derivátu nebo zařazení s doklady (`_has_trades` a obdoby).
    Formulář portfolia (Nastavení › Fondy › Portfolia, AG-020): Třída pod Fondem s nápovědou „prázdné = sdílené všemi třídami“.
A2. Obchod třídu nevybírá; třída = `portfolio_id.class_id`. Řádky dokladů nesou `investra_class_id` = třída portfolia na VŠECH řádcích
    (rozvaha i výsledek): nákup, prodej, vypořádání, storno a oprava obchodu, ocenění pozic (přecenění, realizace, kurz), naběhlý úrok,
    splátky nástrojů, deriváty (forward, swap, spot, obě nohy, podrozvaha). Peníze (banka bez třídy) proti třídě přes `internal_clearing`
    s třídou – stejný vzor jako `_transfer_lines` u úplat. OVĚŘ: kde se řádky skládají (investra_instruments trade posting, valuation
    `_compute_portfolio`, `_compute_unsettled*`, investra_nav instrument_accrual, investra_derivative posting) a zda `_delta` třídy
    pak sedí (rozvahové řádky s třídou + vnitřní zúčtování).
A3. Kurzové přecenění (`investra_fx_revaluation`) po třídách: zůstatky s třídou přeceňovat po třídách, aby se třída neztratila.
A4. Náhled zaúčtování ukazuje třídu na řádcích.
A5. Zrušit `investra.instrument.class_id` (SELECT v `investra`: kolik nástrojů ho má vyplněné; když nějaké, zastav se a napiš).
A6. Přemostění tříd: výsledek portfolia třídy jde do specifické změny třídy („Ostatní specifické“, rozpad podle rolí zůstává otevřený bod).
A7. Testy: stejný nástroj ve sdíleném a v portfoliu třídy B (dvě průměrky, výsledek B jen v ΔT B); forward v portfoliu třídy B (zajištění
    jen B); storno obchodu v portfoliu třídy; úrok a splátka v portfoliu třídy; kurzové přecenění; ČNB výkazy a přehled portfolia beze změny
    (součet přes portfolia); referenční scénáře bez portfolií tříd beze změny (snímek ocenění 35 a 39).
A8. Manuál: portfolio = obchodní model IFRS 9 a zároveň „kapsa“ třídy; sdílené portfolio; třída se dvěma obchodními modely má dvě portfolia.

## 2.2 Postup a kód
### A1. Pole a zámek
`investra_instruments/models/portfolio.py` (model `investra.fund.portfolio`, ř. ~181):
```python
class_id = fields.Many2one(
    "investra.fund.class", ondelete="restrict", tracking=True, string="Třída",
    domain="[('fund_id', '=', fund_id)]",
    help="Prázdné = sdílené portfolio všech tříd (výsledek se dělí poměrem tříd). Vyplněné = portfolio jen této třídy.",
)

@api.constrains("class_id", "fund_id")
def _check_class(self):
    for portfolio in self:
        if portfolio.class_id and portfolio.class_id.fund_id != portfolio.fund_id:
            raise ValidationError(self.env._("Třída portfolia musí patřit fondu portfolia."))

def write(self, vals):
    if "class_id" in vals:
        for portfolio in self.filtered(lambda p: p.class_id.id != vals["class_id"]):
            if portfolio._has_postings():  # obchod, splátka, derivát nebo řádek dokladu se zařazením portfolia
                raise UserError(self.env._("Portfolio %s už má doklady; třídu nejde změnit.", portfolio.name))
    return super().write(vals)
```
`_has_postings`: nejjednodušší je `account.move.line` search_count s `investra_classification_id.portfolio_id = portfolio`
(pokrývá obchody, ocenění, splátky i deriváty se zařazením).

### A2. Třída na řádcích – JEDNO místo: `_create_event`
Místo úprav v každém zdroji doplnit třídu centrálně. `investra_instruments` dědí `investra.accounting.event` (zná model zařazení):
```python
MONEY_ROLES = {"bank", "cash_in_transit", "cash_in_transit_receipt", "unidentified_payment"}

class InvestraAccountingEvent(models.Model):
    _inherit = "investra.accounting.event"

    @api.model
    def _create_event(self, company, key, name, date, event_type, lines, journal=None, source=None):
        return super()._create_event(company, key, name, date, event_type, self._portfolio_class_lines(lines),
                                     journal=journal, source=source)

    @api.model
    def _portfolio_class_lines(self, lines):
        """ZJ-09: třída z portfolia zařazení. (1) Řádek se zařazením dostane třídu jeho portfolia. (2) Má-li doklad
        jedinou třídu portfolia, dostanou ji i ostatní řádky bez třídy kromě peněžních (poplatek, úrok, kurz pozice).
        (3) Peníze zůstávají sdílené: součet řádků s doplněnou třídou se vyrovná vnitřním zúčtováním třída ↔ fond.
        Řádky s třídou zadanou volajícím (úplaty, přesuny mezi třídami) se nemění. Sdílené portfolio = beze změny."""
        Classification = self.env["investra.portfolio.classification"].sudo()
        lines = [dict(line) for line in lines]
        assigned = []
        for line in lines:
            if line.get("class_id"):
                continue
            cid = (line.get("extra") or {}).get("investra_classification_id")
            fund_class = Classification.browse(cid).portfolio_id.class_id if cid else False
            if fund_class:
                line["class_id"] = fund_class.id
                assigned.append(line)
        classes = {line["class_id"] for line in assigned}
        if len(classes) == 1:
            only = next(iter(classes))
            for line in lines:
                if not line.get("class_id") and line["role"] not in MONEY_ROLES:
                    line["class_id"] = only
                    assigned.append(line)
        totals = {}
        for line in assigned:
            totals[line["class_id"]] = totals.get(line["class_id"], Decimal(0)) + Decimal(str(line["amount"]))
        for class_id, total in totals.items():
            if total:
                lines += [
                    {"role": "internal_clearing", "amount": -total, "class_id": class_id, "movement_type": "class_transfer"},
                    {"role": "internal_clearing", "amount": total, "class_id": False, "movement_type": "class_transfer"},
                ]
        return lines
```
Ověření logiky (`valuation._delta` = rozvahové řádky s třídou; hodnota třídy = ρ × neutrální + Δ):
nákup 100 do portfolia B: nástroj +100 (B), banka −100, clearing B −100, clearing fond +100 → Δ_B = 0, neutrální 0 ✓;
přecenění +10: nástroj +10 (B), výnos −10 (B) → součet B = 0, bez clearingu, Δ_B = +10 ✓.
OVĚŘ: (a) otisk dokladu (`_fingerprint`) se mění jen u portfolií tříd – existující doklady sdílených portfolií stejné ✓;
(b) `investra_derivative/models/posting.py:64` `_line_extra` nemá zařazení → přidat `investra_classification_id`
(`_ensure_classification`, ř. 92); (c) splátka `instrument_accrual.py:743`: poplatek (`expense_bank_fee`) extra nemá – pravidlo (2)
ho pokryje (jediná třída v dokladu); (d) `valuation._compute_portfolio` (ř. 481–621) je JEDEN doklad za všechny pozice:
každý řádek pozice (úrok, přecenění, realizace, kurz) musí mít `extra` se zařazením – zkontroluj ř. 560–600, kde chybí, doplň;
(e) `valuation._compute_unsettled` (ř. 780) a `_compute_unsettled_fair_value` (ř. 805): skupinovat i podle `investra_class_id`
a třídu dát explicitně na oba řádky; (f) `investra_fx_revaluation/models/fx_profile.py:61` `_foreign_balances`: přidat
`investra_class_id` do groupby a vracet ho; `valuation._fx_revaluation_lines` (ř. 743) dá třídu na oba řádky.
Obchod: `investra_instruments/models/instrument.py:979` `_event_lines` už extra se zařazením má ✓ (A2 nic dalšího).

### A3–A5
- Formulář portfolia (`investra_instrument_master/views/portfolio_views.xml`): Třída pod Fond, nápověda o sdíleném.
- Obchod: žádné pole třídy; ve formuláři pod Portfolio drobný text „Třída: B“ / „Sdílené portfolio“ (related `portfolio_id.class_id`).
- Zrušit `investra.instrument.class_id` (`instrument.py:168`, kontrola ř. 286–291, pohled `instrument_views.xml:87`); před tím
  `SELECT count(*) FROM investra_instrument WHERE class_id IS NOT NULL;` v `investra` – nenulové → zastav se.
- Náhled zaúčtování: sloupec Třída (pohled `investra.posting.preview`, řádky už `class_id` po A2 mají).

### A7 testy (nový `investra_nav/tests/test_portfolio_class.py`)
Fond se dvěma třídami 50/50; portfolio „Hlavní“ (sdílené) a „B“ (třída B). Stejný dluhopis v obou. Ověřit: po nákupu do B se kapitál tříd
nezmění; po přecenění jde zisk z B jen do B, zisk ze sdíleného 50/50; dvě průměrky (`_cost_walk` po portfoliu); forward v portfoliu B
mění jen B; storno nákupu v B vrátí clearing; splátka s poplatkem v B – poplatek nese B; kurzové přecenění zůstatku v cizí měně v B;
ČNB výkaz a přehled portfolia stejné jako bez třídy; zámek třídy portfolia po prvním dokladu.


## 2.3 Doplnění (deriváty, nevypořádané, kurzové přecenění)

A2(d) `valuation._compute_portfolio` (ř. 481–621): **beze změny** – každý řádek pozice už má `extra` se zařazením (ř. 557).
A2(b) deriváty `investra_derivative/models/posting.py:64` – zařazení jen u portfolia třídy, aby se otisk dokladů sdílených portfolií nezměnil:
```python
def _line_extra(self):
    self.ensure_one()
    extra = {"investra_instrument_id": self.instrument_id.id}
    if self.portfolio_id.class_id:  # ZJ-09: třídu doplní _portfolio_class_lines ze zařazení
        classification = self.env["investra.portfolio.classification"]._valid(
            self.portfolio_id, self.instrument_id, self.trade_date)
        if classification:
            extra["investra_classification_id"] = classification.id
    return extra
```
OVĚŘ: `_ensure_classification` (ř. 92) proběhne před prvním `_line_extra` (sjednání); ocenění derivátu volá `_line_extra` také.

A2(e) nevypořádané obchody `valuation._compute_unsettled` (ř. 780): pohledávka/závazek z nevypořádaného obchodu dostane v dokladu obchodu
třídu pravidlem (2) (jediná třída v dokladu); kurzové přecenění proto po třídách:
```python
groups = Line._read_group(
    self._line_domain(("account_id", "=", account.id)),
    groupby=["currency_id", "investra_class_id"], aggregates=["amount_currency:sum", "balance:sum"],
)
for currency, fund_class, amount, balance in groups:
    if currency == self.fund_id.currency_id:
        continue
    difference = engine.money(d(amount) * self._fx(currency)) - engine.money(balance)
    if difference:
        cls = {"class_id": fund_class.id} if fund_class else {}   # bez třídy klíč nepřidávat → otisk beze změny
        lines.append({"role": role, "amount": difference, "movement_type": "fx_revaluation",
                      "currency_id": currency.id, "amount_currency": "0", **cls})
        lines.append({"role": "gain_fx" if difference > 0 else "loss_fx", "amount": -difference,
                      "movement_type": "fx_revaluation", **cls})
```
`_compute_unsettled_fair_value` (ř. 805): beze změny – řádky mají `extra` se zařazením.

A2(f) `investra_fx_revaluation/models/fx_profile.py:49` – modul nezná třídu (závisí jen na `account`), proto obecný parametr:
```python
def _foreign_balances(self, company, accounts, date, domain=None, by_partner=None, extra_groupby=()):
    ...
    groups = self.env["account.move.line"]._read_group(
        [*domain, ("account_id", "in", accounts.ids), ("currency_id", "!=", base.id)],
        groupby=["account_id", "currency_id", "partner_id", *extra_groupby],
        aggregates=["amount_currency:sum", "balance:sum"],
    )
    merged = {}
    for account, currency, partner, *rest in groups:
        *keys, amount, balance = rest
        key = (account, currency, partner if by_partner is None or by_partner(account) else None, *keys)
        total = merged.setdefault(key, [0.0, 0.0])
        total[0] += amount
        total[1] += balance
    return [(account, currency, partner or None, amount, balance, *keys)
            for (account, currency, partner, *keys), (amount, balance) in merged.items()]
```
`valuation._fx_revaluation_lines` (ř. 757): `extra_groupby=("investra_class_id",)`, smyčka `for account, currency, partner, amount, balance,
fund_class in balances:` a `**({"class_id": fund_class.id} if fund_class else {})` na oba řádky. Samostatný běh přecenění (`fx_profile.py:150`)
volá beze změny (knihy bez fondů). Banky jsou peníze → třídu nikdy nemají, jejich přecenění zůstává sdílené.


# 3. ZJ-08 body 1–3 – třída bez podílu na společných položkách (část D)

Zadání `docs/ukoly/ZJ-08-…md` je rozhodnuté (17. 11.) a nenaprogramované. Teď body 1–3; **bod 4 ruční krystalizace zůstává na později**.
Dnes `valuation._class_context` ř. 408–412: poměr = předběžný kapitál třídy / součet všech → manažerská třída by od dalšího ocenění
dostávala podíl na zisku i ztrátě portfolia.

D1. Pole na třídě (`investra_fund/models/fund.py`, `investra.fund.class`):
```python
shares_common = fields.Boolean(default=True, required=True, tracking=True, string="Podílí se na společných položkách",
    help="Vypnuto: třída nemá podíl na sdíleném výsledku (portfolio, společné náklady, daň). Její kapitál = předchozí kapitál + "
         "pohyby třídy (úpisy, odkupy) + položky jen této třídy (např. přijatá výkonnostní odměna). Typicky manažerská třída.")
```
Zámek v `investra_nav` (override `write` třídy): změna jen do prvního zaúčtovaného ocenění fondu („Změna by přepsala historii; založte novou
třídu.“). Kontrola: fond musí mít aspoň jednu třídu se zapnutým polem; třída s vypnutým polem nesmí být na řádku alokačního schématu
(`investra_allocation`, constrains na `investra.allocation.line`).

D2. Výpočet (`investra_nav/models/valuation.py`) – jeden pomocník, všechna místa přes něj:
```python
def _class_context(self):
    ...  # beze změny až po ř. 407
    common = {c: row for c, row in result.items() if c.shares_common}
    total = sum(row["pre_capital"] for row in common.values())
    if not total:
        raise UserError(self.env._("Předběžný kapitál tříd, které se podílejí na společných položkách, je nulový."))
    for fund_class, row in result.items():
        row["ratio"] = row["pre_capital"] / total if fund_class in common else Decimal(0)
        row["fixed"] = Decimal(0) if fund_class in common else row["pre_capital"]
    return result

def _shared_neutral(self, context, deltas, net_assets=None):
    """Společná část k rozdělení poměrem: FK − specifické položky − kapitál tříd bez podílu na společném."""
    net = self._net_assets() if net_assets is None else net_assets
    return net - sum(deltas.values()) - sum(row.get("fixed", Decimal(0)) for row in context.values())
```
Hodnota třídy všude `ratio × shared + delta + fixed`:
- `_class_value` ř. 853–855: `neutral = self._shared_neutral(context, deltas)`; `return ratio * neutral + deltas[c] + context[c].get("fixed", 0)`.
- `_finish` ř. 1771–1773: totéž (`raw = {c: row["ratio"] * neutral + deltas[c] + row.get("fixed", 0) …}`); kontrola ΣFKT = FK zůstává.
- Přemostění ř. 1849: `shared_raw = engine.money(row["ratio"] * neutral) - (row["pre_capital"] - row.get("fixed", 0))` → u třídy bez podílu 0.
- `_apply_scheme` ř. 1736–1739: `neutral = self._shared_neutral(...)`, `pre_total` jen ze tříd s podílem, `capitals`/`transfers` jen pro ně.
- Úplaty, opravy a daň dělené poměrem (ř. 973–1007, 1541, 1595, `_effect_detail`): beze změny – poměr 0 → nic.
OVĚŘ: `_class_value` volají i `_recipient_parts` (váhy příjemců) a dopočet úplat; projdi `grep -n '"ratio"\]' valuation.py`, žádné místo
nesmí počítat `ratio * neutral` bez `fixed`. Referenční scénáře (všechny třídy s podílem) musí vyjít beze změny (fixed = 0).

D3. Přijetí odměny: existuje (pravidlo výkonnostní odměny → Přijímající třídy, Podíl příjemcům z tříd; jediná přijímající třída dostane
vše i s nulovou hodnotou, ř. 895–905). Přesun jde přes vnitřní zúčtování s třídou → je v Δ třídy → zůstane jí. Odkup ručně (stávající).
D4. Zobrazení: karta třídy a přemostění – u třídy bez podílu „Změna společná“ 0 a v nápovědě důvod; XLS stejně.
D5. Testy `investra_nav/tests/test_class_no_common.py` (příklad 4 + 1 podle zadání ZJ-08 bod 5 bez krystalizace): zisk i ztráta portfolia
nemění třídu M; přijatá odměna zvýší jen M; symbolický úpis M; odkup M; ruční úplata na M jako jediná ztráta; kombinace se schématem
pořadí nároků (M není na řádcích); kontrola nulového předběžného kapitálu.


## D6. Kontrola úplat na třídě bez podílu (k části D)
Pravidlo úplaty (`investra.fee.rule`), jehož třídy (`class_ids`) nebo celé fondové pravidlo zahrnují třídu s vypnutým „Podílí se na
společných položkách“: ve formuláři pravidla žluté upozornění „Třída M se nepodílí na společných položkách; úplata z ní je obvykle omyl.“
(computed warning, ne chyba) a kontrola ocenění (`check_ids`, stav upozornění) se stejným textem. Výjimka: ruční úplata na M (ztráta M).
Daň: třída M nenese žádnou daň ze sdílených položek (poměr 0) – daň ze zisku převedeného na M nesou A a B (Martin 19. 11.); do manuálu.


# 4. ZJ-17 – účetní (hospodářský) rok fondu (část F)

Dnes natvrdo kalendářní rok: `valuation.py:952` `_year_start` (31. 12. předchozího roku), `valuation.py:1220` daň `date(year, 1, 1)`,
`fee_rule.py:280`, `fee_scheme.py:114` (náhled), `investra_cnb/models/cnb_map.py:48` (výkaz ČNB „od počátku roku“).
Zdaňovací období = účetní období (hospodářský rok smí) → daň i roční úplaty musí jít od začátku účetního období.

F1. Zdroj pravdy = standardní nastavení Odoo knihy: `res.company.fiscalyear_last_day/month` a záznamy `account.fiscal.year` (první
prodloužené či zkrácené období). Funkce (OVĚŘ název v Odoo 20: `company.compute_fiscalyear_dates(day)` → `date_from`, `date_to`):
```python
# investra_fund/models/fund.py, investra.fund
def _fiscal_year_start(self, day):
    """První den účetního období, do kterého patří `day` (podle knihy fondu)."""
    self.ensure_one()
    return self.company_id.compute_fiscalyear_dates(day)["date_from"]
```
F2. Náhrady: `valuation._year_start()` → `self.fund_id._fiscal_year_start(self.date) - timedelta(days=1)`; ř. 1220 →
`self.fund_id._fiscal_year_start(self.date)`; `fee_rule.py:280` → `last.fund_id._fiscal_year_start(last.date)`; `fee_scheme.py:114` →
rok podle knihy fondu (start, start + 1 rok); `cnb_map.py:48` → OVĚŘ v `docs/cnb` – výkaz zisku je „od počátku účetního období“ →
`company.compute_fiscalyear_dates(day)["date_from"]`. `engine.year_fraction` (dny v kalendářních letech) beze změny.
Rozhodnuto (Martin): roční úplaty i období výkonnostní odměny (high-water mark, krystalizace „ročně“) se řídí účetním obdobím – žádná
volba na pravidle. OVĚŘ v `fee_rule.py`/`valuation.py` všechna místa, kde se období odměny odvozuje od kalendářního roku (`grep -n
"year" investra_nav/models/*.py`), a převeď je na `_fiscal_year_start`.
F3. Texty: „od 1. 1.“ → „od začátku účetního období“ (pohledy, nápovědy, chyba ř. 1073, sloupec výjimek daně „Pohyb od začátku období“,
manuál). `grep -rn "1\. 1\." addons/custom docs/manual`.
F4. UI: formulář fondu, záložka Obecné: „Konec účetního období“ (related `company_id.fiscalyear_last_day/month`, jen pro čtení, s odkazem
na nastavení účetnictví); změna po prvním zaúčtovaném ocenění jen přes `account.fiscal.year` (účetní), v manuálu.
F5. Testy `test_fiscal_year.py`: kniha s rokem 1. 7.–30. 6.; ocenění 31. 8. bere výsledek a úplaty od 1. 7.; daň se k 1. 7. „nuluje“
(splatná od začátku období); přechod 30. 6. → 31. 7.; kalendářní fondy beze změny (referenční scénáře).


# 5. ZJ-16 – poplatek obchodu (část E)

Dnes `instrument.py:1043` „v prototypu bez poplatků“. Splátka jistiny poplatek má (`instrument_accrual.py:354`, náklad `expense_bank_fee`).

E1. Pole obchodu (`investra.trade`, `investra_instruments/models/instrument.py:623`):
```python
fee_amount = fields.Float(digits=(20, 2), default=0, string="Poplatek", help="Poplatek obchodníka/burzy, kladně.")
fee_currency_id = fields.Many2one("res.currency", string="Měna poplatku", help="Prázdné = měna nástroje.")
fee_fx_rate = fields.Float(digits=(16, 6), string="Kurz poplatku",
    help="Funkční měna za jednotku měny poplatku. Měna nástroje → kurz obchodu; funkční měna → 1.")
fee_treatment = fields.Selection([("expense", "Náklad"), ("capitalise", "Součást pořizovací ceny")],
    compute="_compute_fee_treatment", string="Účtování poplatku")
```
Výchozí kurz poplatku: stejná logika jako výchozí kurz obchodu (AG-021, R3); poplatek a jeho měna/kurz do `BOOKED_TRADE_FIELDS`.
Kontrola: poplatek ≥ 0; měna poplatku ≠ funkční a ≠ měna nástroje → kurz povinný.

E2. Účtování (IFRS 9.5.1.1, 9.B5.4.8; IFRS 13.25):
| Obchod | Zařazení | Poplatek |
|---|---|---|
| nákup | FVTPL | náklad hned |
| nákup | naběhlá hodnota, FVOCI | součást pořizovací ceny (řádek role nástroje) |
| prodej | všechny | náklad (prodejní náklady nesnižují reálnou hodnotu; realizace = výnos − účetní hodnota) |
`_compute_fee_treatment`: `capitalise` jen nákup a kategorie zařazení `amortised`/`fvoci`, jinak `expense`.
Náklad: nový analytický účet šablony **„Poplatky za obchody s investičními nástroji“** jako další účet role `expense_bank_fee` (stejný
přístup jako C0.1; číslo podle `docs/osnova-501-syntetika.md`, řádek ČNB „Náklady na poplatky a provize“ – OVĚŘ), řádek s
`extra.account_id`.

E3. `_event_lines` (`instrument.py:979`) – doplnit na konec, před protiúčet:
```python
fee_lines, fee_pay = self._fee_lines(role, fx)  # fee_pay = [(částka ve funkční měně, měna, částka v měně)]
lines += fee_lines
for amount_fee, currency, amount_fee_ccy in fee_pay:
    lines.append({"role": counter_role, "amount": -amount_fee, "movement_type": "transaction",
                  **({"currency_id": currency.id, "amount_currency": -amount_fee_ccy} if currency != self.company_id.currency_id else {})})

def _fee_lines(self, role, fx):
    if not self.fee_amount:
        return [], []
    currency = self.fee_currency_id or self.instrument_id.currency_id
    rate = self.fee_fx_rate or (fx if currency == self.instrument_id.currency_id else 1.0)
    amount = self.company_id.currency_id.round(self.fee_amount * rate)
    extra = {"investra_instrument_id": self.instrument_id.id, "investra_classification_id": self._classification().id}
    if self.fee_treatment == "capitalise":
        ccy = self.instrument_id.currency_id
        foreign = ccy != self.company_id.currency_id
        line = {"role": role, "amount": amount, "movement_type": "transaction", "extra": extra,
                "name": self.env._("Poplatek %s", self.instrument_id.name),
                **({"currency_id": ccy.id, "amount_currency": amount / fx} if foreign else {})}  # křížově přes kurz obchodu
    else:
        account = self.env["account.account"].search([("code", "=", FEE_ACCOUNT_CODE), ("company_ids", "in", self.company_id.ids)], limit=1)
        line = {"role": "expense_bank_fee", "amount": amount, "movement_type": "fee", "extra": {**extra, "account_id": account.id},
                "name": self.env._("Poplatek %s", self.instrument_id.name)}
    return [line], [(amount, currency, self.fee_amount)]
```
Volání: `_event_lines` se volá pro krok „book“ i „settle“ (`_planned_postings` ř. 1024–1036). Poplatek patří **jen do kroku sjednání**
(odložené vypořádání: protiúčet poplatku = role nevypořádaných, ve kroku vypořádání druhá dvojice nevypořádané ↔ banka v měně poplatku).
Přidej parametr `with_fee=True` a v kroku „settle“ při trade-date účtování předej jen přesun nevypořádané → banka. Při settlement-date
účtování (jediný krok „settle“) poplatek v něm.
Peníze (banka/nevypořádané) zůstávají sdílené; náklad poplatku dostane třídu pravidlem (2) z A2 → portfolio třídy B nese i poplatek.

E4. Průměrka a cena odúčtování: `_position_events` (po B1 na `investra.trade`) – u nákupu s `capitalise` přičíst poplatek v měně
nástroje (`amount / fx` jako výše) k částce; u `expense` ne. Náhled obchodu (kontext `investra_trade_preview`) stejně.
OVĚŘ `instrument._accrued_value` (naběhlá hodnota): musí vycházet z pořizovací ceny včetně poplatku (efektivní úroková míra z
nákladů), jinak další ocenění poplatek odepíše do úroků. Když vychází jen z ceny obchodu, uprav ji tak, aby brala pořizovací cenu
z `_position_events`; když to nejde čistě, zastav se.
E5. Formulář obchodu (AG-021): skupina „Poplatek“ (částka, měna, kurz – kurz jen u cizí měny poplatku), pod ní text „Účtování: náklad
/ součást pořizovací ceny“; náhled zaúčtování ukáže řádky poplatku; seznam obchodů sloupec Poplatek (volitelný). XLS a SQL ukázky
(`docs/sql`) – sloupec poplatku.
E6. Testy `test_trade_fee.py`: nákup FVTPL USD akcie s poplatkem v CZK (náklad, banka CZK); nákup dluhopisu naběhlou hodnotou s poplatkem
v EUR (kapitalizace, průměrka +poplatek, další ocenění poplatek neodepíše); prodej s poplatkem (náklad, realizace beze změny);
odložené vypořádání (poplatek v kroku sjednání proti nevypořádaným, vypořádání v bance); storno; portfolio třídy B (poplatek nese B);
obchod bez poplatku – otisk dokladu beze změny (existující doklady).


# 6. ZJ-15 – cena odúčtování na prodeji (část B)

## 6.1 Plán
Dnes: realizovaný výsledek počítá ocenění (`_realised_ccy`) jako výnos prodeje − poměrná účetní hodnota průměrem; pořizovací cena
zbývajících kusů průměrem v `_cost_walk`. Prodej sám pořizovací cenu nenese.

B1. Prodej (`investra.trade`, side = sell) dostane pole jen pro prodej:
    - **Průměrná cena k datu sjednání** (počítané, jen pro čtení): pořizovací cena za kus průměrem po dvojici nástroj + portfolio
      (stejná funkce jako `_cost_walk`, vytáhnout do sdílené metody), v měně nástroje;
    - **Cena odúčtování za kus** (uložené, předvyplněné průměrnou; uživatel smí přepsat);
    - **Důvod úpravy ceny odúčtování** (povinný, jen když se cena liší od průměrné o víc než zaokrouhlení);
    - kontrola: cena odúčtování × kusy ≤ pořizovací cena celé pozice k datu (nelze odúčtovat víc, než pozice má); záporná nejde.
    Změna se zapíše do chatteru (tracking). Zámek jako ostatní pole obchodu po zaúčtování.
B2. Ocenění: u prodeje s ručně upravenou cenou se pořizovací cena prodaných kusů bere z ní (ve `_cost_walk` místo průměrného podílu),
    zbytek pozice nese zbytek pořizovací ceny. Realizovaný výsledek proti účetní hodnotě (`_realised_ccy`) se mění stejně: poměrná část
    přecenění se rozpouští podle podílu pořizovací ceny (OVĚŘ a zvol nejjednodušší konzistentní variantu; součet realizace + přecenění
    za pozici se nesmí změnit – u reálné hodnoty do výsledku cena odúčtování mění jen rozdělení, ne celkový výsledek ani daň).
B3. Bez ruční úpravy (cena = průměrná) musí být výsledky ocenění 35 a 39 beze změny.
B4. Testy: prodej s výchozí cenou = dnešní výsledek; ruční cena → jiná realizace i přecenění, stejný součet; cena nad pozici → chyba;
    důvod povinný; storno prodeje; prodej v portfoliu třídy (realizace nese třídu).
B5. Formulář prodeje (AG-021): pod Kusy a Cenou řádek „Odúčtování: průměrná X, použitá Y“ a důvod jen při odchylce. Manuál: kapitola obchodů.

## 6.2 Postup a kód
### B1. Společná průměrka
Přesunout `valuation._position_events` (ř. 626) do `investra.trade` (investra_nav dědí trade; splátky jsou v investra_nav):
`Trade._position_events(fund, instrument, portfolio, start, end)` – stejné tělo, `self.fund_id` → `fund`; ocenění volá ji.
Událost dostane 6. prvek `cost` = pořizovací cena prodaných kusů v měně nástroje zadaná ručně, jinak `None`:
```python
events = [(t._recognition_date(), d(t.quantity), d(t.quantity) * d(t.price), d(t._booked_fx()), False,
           (-d(t.quantity) * d(t.derecognition_price)) if t.quantity < 0 and t.derecognition_manual else None)
          for t in trades]
```
(u splátek a náhledu `None`). Průměrka k datu:
```python
def _average_cost(self, fund, instrument, portfolio, day, exclude=None):
    """Pořizovací cena za kus průměrem po nástroji a portfoliu k datu (měna nástroje), bez obchodu `exclude`."""
    units = cost = Decimal(0)
    for _day, quantity, amount, _fx, closes, manual in self._position_events(fund, instrument, portfolio, None, day):
        ...  # stejná smyčka jako _cost_walk, jen v měně nástroje; vrací (units, cost)
```

### B2. Pole na prodeji (investra_nav, `_inherit = "investra.trade"`)
```python
average_cost_price = fields.Float(digits=(20, 8), compute="_compute_average_cost", string="Průměrná cena k datu sjednání")
derecognition_price = fields.Float(digits=(20, 8), tracking=True, string="Cena odúčtování za kus",
    help="Pořizovací cena prodaných kusů za kus; výchozí průměrná cena pozice (nástroj a portfolio). Mění jen rozdělení "
         "výsledku na realizovaný a přecenění, ne celkový výsledek.")
derecognition_manual = fields.Boolean(compute="_compute_derecognition_manual", store=True, string="Upraveno ručně")
derecognition_reason = fields.Text(tracking=True, string="Důvod úpravy ceny odúčtování")
```
- onchange (side, instrument, portfolio, trade_date) → `derecognition_price = average_cost_price` (jen prodej, jen návrh);
- `derecognition_manual = abs(price − average) > 10^-8` (uloženo, aby ocenění nepočítalo průměrku znovu při čtení);
- kontroly při Zaúčtovat (`action_book` / `_check_booking` – v oranžové zóně jen nová kontrola, účtování obchodu beze změny):
  ruční → důvod povinný; cena ≥ 0; `−quantity × price ≤ cost pozice k datu` (z `_average_cost`).
  Prodej bez ručního zásahu (cena = průměrná) = dnešní chování (event `cost=None`).

### B3. Ocenění (`valuation._cost_walk` ř. 654, `_realised_ccy` ř. 674)
Ve smyčce u prodeje s `manual`:
```python
if manual is not None and cost_ccy:
    share_cost = min(manual / cost_ccy, Decimal(1))          # podíl pořizovací ceny, který odchází
    share_units = Decimal(1) if closes else min(-quantity / units, Decimal(1))
else:
    share_cost = share_units = (Decimal(1) if closes else min(-quantity / units, Decimal(1)))
# _cost_walk: realised_fx += share_cost × (cost_ccy × fx − cost); units *= (1 − share_units); cost_ccy, cost *= (1 − share_cost)
# _realised_ccy: part = −amount − carrying × share_cost; carrying *= (1 − share_cost); units *= (1 − share_units)
```
Celkový výsledek pozice se nemění (přecenění = hodnota − zbývající účetní hodnota). OVĚŘ na testu: součet realizace + přecenění + kurz
je stejný pro průměrnou i ruční cenu.

### B4. Testy (`investra_nav/tests/test_derecognition.py`)
nákup 10 ks à 100 a 10 ks à 120, prodej 5 ks à 130: průměrná 110 → realizace 5 × (130 − účetní hodnota/ks); ruční 100 + důvod →
vyšší realizace, nižší přecenění, stejný součet; ruční bez důvodu → chyba; 25 × 110 > pozice → chyba; storno prodeje;
prodej v portfoliu třídy B (realizace s třídou B). Snímek ocenění 35 a 39 beze změny.


# 7. ZJ-19 – dividendy a ex-kupón dluhopisů (část H)

Dnes: dividendy jen ručním dokladem (role `income_dividend`, účet 714000; žádný model ani pohledávka); ex-kupónové datum nikde
(`grep -i "ex_coupon|exkup"` nic). Kupón nabíhá lineárně do dne výplaty (`instrument_accrual.py:212` `_earned_coupon_unit`), naběhlý úrok
obchodu musí být kladný (`instrument.py:~889`), kupón přijímá splátka (`instrument.repayment.interest_amount`, řádky ř. 750–775).
Společný princip (Martin 19. 11.): **výnos patří tomu, kdo drží k večeru dne před ex-datem** (`Trade._holdings(fund, ex_date − 1 den)`).

H1. Dividenda – nový model `investra.dividend` (investra_nav, `mail.thread`, oprávnění jako obchod – `_require_preparer`):
```python
fund_id, instrument_id (akcie/podíly: type_group equity/fund), portfolio_id (nabídka jen portfolií s pozicí k ex-date − 1)
ex_date (Ex-datum, povinné), pay_date (Datum výplaty), currency_id (výchozí měna nástroje)
units = Float(compute z _holdings k ex_date − 1, store, readonly=False)        # „Kusy s nárokem“
per_share = Float(digits=(20, 8), string="Hrubá dividenda na kus")
gross_amount = compute units × per_share (měna dividendy)
kind = Selection([("domestic","Česká"),("foreign","Zahraniční"),("subsidiary","Z dceřiné společnosti")]) – výchozí podle země
       emitenta (CZ → domestic, jinak foreign); subsidiary jen ručně
withholding_rate (sražená sazba %), withheld_amount (compute gross × rate, editovatelné)
treaty_rate (smluvní sazba %, jen foreign; výchozí 15), creditable_amount (compute min(withheld, gross × treaty_rate), editovatelné)
excess_treatment = Selection([("receivable","Pohledávka k vrácení"),("expense","Náklad")], default="receivable")  # přeplatek nad smluvní
fx_rate (k ex-date), pay_fx_rate (k výplatě; prázdné = fx_rate)
state draft / booked / paid / reversed; event_id, pay_event_id; posting_preview (jako obchod)
```
Zaúčtování k ex-date (`_create_event`, extra se zařazením → třída portfolia podle A2):
| Řádek | Česká | Zahraniční | Dceřiná |
|---|---|---|---|
| D výnos (hrubá) | 714100 | 714200 | 714300 (účty z C1, další účty `income_dividend`) |
| MD sražená daň | 681100 (srážková, konečná) | 681400 započitatelná část | dle země jako česká/zahraniční |
| MD přeplatek nad smluvní | – | pohledávka 3xx „Pohledávky – zahraniční daň k vrácení“ nebo náklad (excess_treatment) | – |
| MD pohledávka z dividendy (čistá) | 3xx „Pohledávky z dividend“ | dtto | dtto |
Nové analytiky: „Pohledávky z dividend a kupónů“ a „Pohledávky – zahraniční daň k vrácení“ jako další účty role `receivable_other`
(řádek s `extra.account_id`); účet pohledávek z dividend přidat do profilu kurzového přecenění šablony (`_fx_accounts`), OVĚŘ.
Výplata (tlačítko „Zaplaceno“, pay_date): MD banka (měna dividendy) / D pohledávka; kurzový rozdíl gain/loss_fx. Storno jako obchod.
Daň: účty 714100–714300, 681100, 681400 už ZJ-07 zná (výjimky „Přidat běžné výjimky“ – kontrola, že sedí na nové analytiky).
Ocenění: akcie ex-div klesne, pohledávka to vyrovná – nic dalšího. Formulář pod Portfolio › Dividendy, tlačítko z nástroje.

H2. Ex-kupón dluhopisu:
- Nástroj: `ex_coupon_days = fields.Integer(default=0, string="Ex-kupónová lhůta (dny)", help="Kolik kalendářních dní před výplatou
  kupónu se obchoduje bez kupónu. 0 = bez lhůty.")`; tok kalendáře (`investra.instrument.cashflow`, jen Úrok): `ex_date` (compute
  date − ex_coupon_days, store, readonly=False – přepis u nepravidelných).
- Předvyplnění naběhlého úroku obchodu (`_calendar_accrued_interest` ř. 911): když trade_date ∈ [ex_date, date toku) → naběhlý úrok
  = vydělaný od začátku období − celý kupón (ZÁPORNÝ). Kontrola ř. ~889 „zadává se kladně“ → povolit záporný jen v ex-lhůtě
  (jinak dál chyba); `_signed_accrued_interest` beze změny (znaménko směru × hodnota se znaménkem).
- Nárok na kupón: splátka (výplata kupónu) předvyplní `interest_amount` = kusy k ex_date − 1 × kupón na jednotku (dnes kusy k datu
  výplaty – OVĚŘ `_compute_*` splátky); prodávající v ex-lhůtě kupón dostane i bez pozice → splátka musí jít i na uzavřenou pozici
  (OVĚŘ `_check_repayment`/`allowed_portfolio_ids` ř. 601 – nabízet portfolia s pozicí k ex_date − 1).
- `_fair_value_interest` (ř. 254): vzorec earned + bought − received s naběhlým úrokem se znaménkem vyjde správně sám (kupující
  v ex-lhůtě: zbytek kupónu − zbytek = 0; prodávající: přijatý kupón proti zaplacenému zápornému úroku) – OVĚŘ testem, uzavřená
  pozice (`_closed_positions`) s nevyplaceným kupónem nesmí doúčtovat naběhlý úrok na nulu dřív, než přijde výplata.
- Test `test_ex_coupon.py`: dluhopis kupón 5 % ročně, výplata 30. 6., lhůta 30 dní; nákup 10. 6. → naběhlý úrok záporný, kupón 30. 6.
  nedostane, ocenění 20. 6. a 30. 6. bez skoku; prodej 10. 6. → prodávající kupón dostane, pozice po výplatě 0; nákup před lhůtou beze
  změny; lhůta 0 = dnešní chování (referenční scénáře beze změny).


# 8. ZJ-18 – FVOCI do OCI a daň z OCI (část G)

Martin 19. 11. večer: **FVTPL se zdaňuje hned podle účetnictví** (§ 23/9) → u FVTPL žádné zdanění při realizaci. Zdanění při realizaci
se týká jen přecenění do kapitálu (FVOCI, § 23/19) a FVOCI se dělá **v této dávce**: úrok efektivní mírou do výsledku, ECL do výsledku
(ruční doklad), zbylé přecenění do OCI. Původní poziční návrh C10 (přechodný rozdíl pozic) se ruší – stačí účty a výjimky ze ZJ-07.
Dnes: FVOCI se přeceňuje do výsledku jako FVTPL, nevypořádaný obchod FVOCI ocenění zastaví (`valuation.py:817`), otevřený bod
„Účtování FVOCI“ (`docs/otevrene-body.md:43`).

G1. Role a účty (nové role v kódu `investra_entity/data/account_role.xml`, účty v šabloně + migrace; čísla podle osnovy 501, OVĚŘ):
- `revaluation_reserve` „Oceňovací rozdíly FVOCI“ (equity), hlavní účet = jen cílový zůstatek přecenění; další účet „Opravná položka ECL
  v OCI“ (ruční doklady ECL dluhu FVOCI, výpočet ho nebere jako zaúčtované přecenění).
- `revaluation_reserve_tax` „Odložená daň k oceňovacím rozdílům“ (equity) – účet daně pravidla „Odložená“ pro FVOCI.
- další účet `retained_result` „Realizované přecenění FVOCI“ (equity) – převod rezervy akcií FVOCI při prodeji (bez recyklace).
- ECL náklad: další účet `expense_other` „Opravné položky ECL“ (ruční doklad MD náklad / D „Opravná položka ECL v OCI“).
Mapování ČNB: rezerva a její odložená daň na řádek oceňovacích rozdílů vlastního kapitálu (OVĚŘ v docs/cnb).

G2. Výpočet v `valuation._compute_portfolio` (ř. 481–621) pro zařazení `fvoci` – jeden princip „cílová rezerva“:
```
base_t      = naběhlá hodnota k datu (dluh, instrument._accrued_value jako u amortised)  |  pořizovací cena průměrem (akcie, _cost_walk, vč. poplatku E)
cíl_rezervy = hodnota RH − base_t        (pozice bez kusů → 0)
pohyb_OCI   = cíl_rezervy − zůstatek hlavního účtu revaluation_reserve pozice (extra se zařazením, jako účet nástroje)
řádek nástroje = hodnota − účetní hodnota (jako dnes, bez naběhlého úroku zvlášť)
zbytek      = řádek nástroje − pohyb_OCI
  dluh:  zbytek → výsledek: realizace = výnos prodeje − podíl naběhlé hodnoty prodaných kusů (gain/loss_realised), zbytek income_interest
  akcie: zbytek → „Realizované přecenění FVOCI“ (kapitál), ve výsledku nic; dividendy do výsledku jako dnes
kurz:  dluh je peněžní položka – kurz z naběhlé hodnoty do výsledku (gain/loss_fx), kurz z rezervy do OCI; akcie – celý kurz do OCI
```
Kontrola příkladů (ručně): akcie nákup 100 + poplatek 1 (kapitalizace E) → cena 101; RH 130 → OCI 29; prodej 140 → OCI −29, „Realizované
přecenění“ +39, výsledek 0. Dluh: nákup 980, naběhlá 985, RH 990 → úrok 5, OCI 5; prodej 995 při naběhlé 987 → úrok 2, realizace 8,
OCI −5 (recyklace je ve zbytku). Nevypořádaný obchod FVOCI (`valuation.py:817`): změna RH místo výjimky na `revaluation_reserve`.
Třídy: rezerva je kapitál → `_delta` ji nepočítá, řádek nástroje (aktivum) ano → výsledek portfolia třídy B zůstane B (A2 beze změny).
Řádek listu portfolio: nový sloupec „Oceňovací rozdíl (OCI)“; přemostění tříd a XLS: OCI je součást „Ostatní/společná“ změny (FK se
mění), v manuálu vysvětlit.

G3. Daň (rozšíření ZJ-07, bez pozičního výpočtu):
- Odložená daň z OCI: pravidlo „Odložená“ (sazba fondu, účet daně = `revaluation_reserve_tax`, rozvahový 348000), výjimka fondu na
  hlavním účtu `revaluation_reserve` → požadovaný stav = sazba × zůstatek (kumulativní, ke konci roku se nenuluje).
- Splatná daň při realizaci: dluh – recyklace jde do výsledku, zdaní se sama; akcie – výjimka na účtu „Realizované přecenění FVOCI“
  s výchozím (splatným) pravidlem: **rozvahový účet ve výjimce se splatným pravidlem = jeho pohyb od začátku období se znaménkem výnosu**
  (rozšíření D5/C0.5: rozvahové účty ve výjimkách i se splatným pravidlem, ne jen s Odloženou).
- Splatná daň z realizace akcií FVOCI se účtuje na 681000 (výsledek); IAS 12.61A by ji mohl chtít v kapitálu → otevřený bod pro metodika.
- ECL: náklad ECL je daňově neuznatelný, pokud zvláštní zákon neříká jinak → v manuálu doporučit výjimku „Mimo základ“ (poradce).
- Tlačítko „Přidat běžné výjimky“ přidá u fondu s pozicí FVOCI i obě výjimky FVOCI (odložená z rezervy, splatná z realizace akcií).

G4. Testy `test_fvoci.py`: příklady z G2 (akcie i dluh, CZK i USD); nevypořádaný obchod FVOCI; portfolio třídy B; ruční ECL nezmění cílovou
rezervu; daň: odložená 5 % z rezervy 29 → 1,45 (kapitál), po prodeji 0 a splatná +39 × 5 % = 1,95; dluh – recyklovaný zisk ve splatné dani;
fond bez FVOCI pozic – výsledky beze změny (35, 39, referenční scénáře).


# 9. ZJ-07 – daňová pravidla a daň fondu (část C)

## 9.1 Zadání (řešení, jednoduchost, referenční příklady)
```
ŘEŠENÍ
A) Daňové pravidlo – nový sdílený model (Nastavení › Daně › Daňová pravidla; mail.thread, tracking):
   název; druh: „Obecný základ“ / „Samostatný základ“ / „Mimo základ daně“; způsob (jen u základů): „Splatná – výsledek od 1. 1.“ /
   „Odložená – zůstatek k datu“; sazba ve verzích „Platí od“ (řádkový model, tracking do chatteru pravidla); účet daně = role účtu
   (náklad 68x, nebo vlastní kapitál u odložené daně z přecenění do kapitálu); rozvahový účet = role účtu (347x splatná, 348x odložená);
   u odložené „Vykázat i pohledávku“ (výchozí ne – opatrnost); poznámka (paragraf). „Mimo základ daně“ nemá sazbu ani účty.
   ZÁPOČET ZAHRANIČNÍ DANĚ (Martin): u samostatného i obecného základu volitelně „Započíst daň z účtu“ (role „Započitatelná zahraniční
   daň“, nový účet v šabloně, např. 681400). Kolik je započitatelné (podle smlouvy o zamezení dvojího zdanění), určí uživatel už při
   zaúčtování dividendy: započitatelnou část srážky zaúčtuje na tento účet, nezapočitatelný přeplatek jinam (pohledávka k vymáhání
   v zahraničí nebo náklad). Výpočet: daň pravidla = max(0, sazba × základ − zápočet), zápočet = zůstatek účtu od 1. 1., nejvýš daň
   pravidla (zbytek zápočtu propadá, jen informace v rozpadu). Účet zápočtu se nepočítá do základu ani do zaúčtované daně.
   Ověř, jestli má příjem dividendy vlastní formulář; pokud ano, přidej k němu pole „Započitatelná část srážky“ (oranžová zóna),
   jinak stačí ruční doklad – popiš v manuálu.
   Výchozí data (šablona): „Daň 21 %“ a „Daň ZIF 5 %“ (obecný, splatná, 681000/347000), „Samostatný základ 15 %“ (samostatný, splatná; Martin 19. 11.: 15 % pro všechny fondy včetně ZIF podle praxe ověřené s daňovým poradcem, jen zahraniční dividendy;
   vlastní účty 681300/347300), „Mimo základ daně“. Role účtů: každé pravidlo vlastní role; ověř, jak se v projektu zakládají role
   a jejich účty v knihách (Nastavení › Účtování), a aby nové pravidlo uměl uživatel založit i s rolemi bez programátora; když to nejde,
   navrhni nejjednodušší cestu a napiš mi ji.
B) Daň fondu = SOUČÁST NASTAVENÍ FONDU (Martin): celé nastavení daně je na formuláři fondu v záložce „Daň“, jinde se needituje.
   Stávající pravidlo úplaty druhu Očekávaná daň zůstává jen jako technický nosič (jedno na fond, založí se samo při volbě výchozího
   pravidla, v seznamu Pravidla úplat jen pro čtení s odkazem na záložku Daň; ve Schématu výpočtu dál řádek „Daň“ s krokem).
   Záložka Daň: výchozí daňové pravidlo fondu (výběr ze sdílených pravidel, vedle něj jeho aktuální sazba; prázdné = fond daň nepočítá;
   návrh: podílový fond → Daň ZIF 5 %, jinak dotaz) – změna zákona se tak upraví jednou ve sdíleném pravidle pro všechny fondy,
   zvláštní sazba fondu = nové sdílené pravidlo;
   Základ (krok, ZJ-12), tabulka Výjimky: účet knihy fondu → daňové pravidlo (jakýkoli výsledkový účet, rozvahový jen s pravidlem
   „Odložená“), poznámka. Tlačítko „Přidat běžnou výjimku“: České dividendy → Mimo základ, neuznatelné náklady 5 % z výnosu;
   Zahraniční dividendy → Samostatný základ 15 %, neuznatelné náklady 5 % z výnosu;
   Penále a pokuty → Mimo základ; Reprezentace → Mimo základ; Dividendy z dceřiné společnosti → Mimo základ (nabízí se u všech fondů, bez zvláštní nápovědy). Výběr účtu nabízí nejdřív
   účty s pohybem v roce.
   KRÁCENÍ NÁKLADŮ na osvobozené výnosy (§ 25/1/i; např. osvobozené úroky ze státních dluhopisů): řádek výjimky má navíc „Podíl“
   (výchozí 100 %), vždy ručně zadaná konstanta (Martin: automatický poměr se nedělá); podíl jde do pravidla řádku (typicky Mimo
   základ daně), zbytek účtu zůstává ve výchozím pravidle. Podíl se ukáže v rozpadu daně.
   NEUZNATELNÉ NÁKLADY JAKO % Z VÝNOSU (Martin; praxe: 5 % z hrubých dividend, paušál § 25/1/zk): řádek výjimky u VÝNOSOVÉHO účtu má
   pole „Neuznatelné náklady (% z výnosu)“ (výchozí 0, u běžných výjimek dividend 5 %); výpočet přičte toto % z výnosu účtu od 1. 1.
   k základu VÝCHOZÍHO (obecného) pravidla, bez ohledu na pravidlo řádku. Ukáže se v rozpadu daně jako samostatný řádek.
   Sazby se z verzí daně fondu přesunou do pravidel (migrace: 5 % → Daň ZIF 5 %, 21 % → Daň 21 %, jiná sazba →
   nové pravidlo „Daň X %“ se stejnými verzemi). Bez výjimek musí být výsledky ocenění stejné jako dnes.
C) Výpočet (engine.tax_amounts, _tax_item), pro každé daňové pravidlo r použité ve fondu:
   - účty pravidla = výsledkové účty bez výjimky (u výchozího pravidla) + účty výjimek s pravidlem r;
   - nikdy se nepočítají účty daně (role všech daňových pravidel, srážková daň, doměrky minulých let – viz D);
   - splatná: základ_r = výsledek účtů pravidla od 1. 1. (výnosy +, náklady −); u výchozího pravidla navíc přičtení podle kroku (ZJ-12)
     a opravy základu (ZJ-12); daň_r = sazba × max(0, základ_r); zaúčtovaná_r = pohyb na účtu daně pravidla od 1. 1.;
   - odložená: základ_r = zůstatek účtů pravidla k datu; požadovaný stav = sazba × základ_r (záporný jen s „Vykázat i pohledávku“);
     zaúčtovaná_r = zůstatek rozvahového účtu pravidla;
   - pohyb_r = požadovaná − zaúčtovaná, doklad na účty pravidla; jeden doklad daně za ocenění se řádky po pravidlech;
   - účet s podílem < 100 % se rozdělí: podíl × částka do pravidla řádku, zbytek do výchozího pravidla (stejně i u řádků s třídou);
   - samostatné základy si nezapočítávají ztrátu obecného základu;
   - účty „Mimo základ daně“ se nikde nepočítají (náklad základ nesnižuje, výnos ho nezvyšuje);
   - dopočet (ZJ-12 solve_fees) a přesná odměna „po dani“ beze změny principu; daň = součet pravidel.
   - OPRAVY (ZJ-12, Martin): oprava daně i oprava základu daně má pole „Daňové pravidlo“ (výchozí = výchozí pravidlo fondu; nabízí jen
     pravidla použitá ve fondu); oprava základu se přičte k základu toho pravidla, oprava částky je pevná částka daně toho pravidla;
     platnost a převzetí jako v ZJ-12 (do konce roku; u odložené daně do ukončení). V rozpadu daně se oprava ukáže u svého pravidla.
     Existující opravy daně se migrací přiřadí výchozímu pravidlu fondu.
   - DAŇ PO TŘÍDÁCH (daňový efekt, ZJ-12 B.5) zobecnit na každé pravidlo zvlášť: specifické položky třídy = výsledkové řádky s třídou na
     účtech pravidla; efektivní sazba podle pravidla; přírůstkový přesun a dorovnání beze změny, součet přesunů 0. Projdi a v ZJ-07 vypiš,
     odkud všude vznikají výsledkové řádky s třídou (úplaty a odměny tříd, ruční úplaty a opravy, poplatky z úpisů a odkupů ve prospěch
     třídy, kurzové rozdíly a zajištění třídy, portfolio třídy podle ZJ-09, ruční doklady s třídou, další?) a ke každému zdroji test,
     že se jeho daňový efekt přesune správné třídě.
D) Další účty daně (šablona + migrace existujících knih se zálohou): srážková daň (681100) a doměrky a vratky minulých let (681200)
   s vlastními rolemi – výpočet je nepočítá do základu ani do zaúčtované daně (jinak by je „dorovnal“). Mapování na výkazy ČNB jako
   stávající daňové řádky (ověř v docs/cnb).
E) Zobrazení a protokol: v ocenění rozpad daně po pravidlech jako krátká tabulka (pravidlo | základ | sazba | požadovaná | zaúčtovaná |
   pohyb), nulové řádky skryté, u výchozího pravidla rozbalení: výsledek od 1. 1., výjimky, kroky, opravy základu. XLS pro depozitáře:
   list „Daň“ ze snímku detailu. Schéma výpočtu: informace podle D2.
F) Manuál: kapitola Daň z příjmů fondu – výchozí pravidlo a výjimky na příkladech, sdílená pravidla a založení nového, odložená daň
   z přecenění do kapitálu, ztráta opravou základu, zápočet zahraniční daně (při zaúčtování zahraniční dividendy rozdělit srážku:
   započitatelná část do výše smluvní sazby na 681400, přeplatek nad smluvní sazbu na pohledávku k vymáhání v zahraničí; nedobytnou
   pohledávku odepsat na účet s výjimkou podle dohody s poradcem), neuznatelné náklady 5 % z dividend,
   tabulka „kam co účtovat“ (srážková daň, doměrky, zálohy na 347 výpočet neovlivní).
   KONEC ROKU (Martin, varianta A, bez nové funkce): odhad k 31. 12. zůstává zaúčtovaný; rozdíl z daňového přiznání se účtuje ručně
   na „Doměrky a vratky minulých let“ (681200) s datem v novém roce nebo do otevřeného prosince; zálohy na 347; od 1. 1. výpočet
   začíná od nuly. Krok „Uzávěrka daně za rok“ se nedělá (případně později).

JEDNODUCHOST (Martin: funkční, jednoduché, přehledné): běžný fond nastaví jen výchozí pravidlo (předvyplněné) a nic dalšího; výjimky
jen výběrem účtu a pravidla; lidské názvy, nápověda jednou větou, paragrafy jen v poznámce; upozornění jen tam, kde je co dělat.

REFERENČNÍ PŘÍKLAD (ručně; test v Odoo i v tools/nav_reference). Jedna třída, výchozí Daň ZIF 5 %, krok 3, výsledek od 1. 1. 100 000, v něm:
penále 2 000 (Mimo základ), české dividendy 10 000 (Mimo základ), zahraniční dividendy 5 000 (Samostatný základ 15 %),
dividendy z dceřiné spol. 3 000 (Mimo základ).
Daň ZIF: základ = 100 000 + 2 000 − 10 000 − 5 000 − 3 000 = 84 000 → 4 200,00 (681000/347000);
s neuznatelnými náklady 5 % z výnosu u českých i zahraničních dividend: + 5 % × (10 000 + 5 000) = + 750 → základ 84 750 → 4 237,50;
Samostatný 15 %: 5 000 → 750,00 (681300/347300); se započitatelnou zahraniční daní 750 na 681400 → 0,00; se zápočtem 900 → 0,00 (150 propadá). Srážková daň 1 500 na 681100 se nezapočítá.
Ztráta: výsledek −20 000 (základ ZIF −37 000) → ZIF 0, samostatný 750,00.
Rakouská dividenda (kontrola účtování): hrubá 7 000, smlouva 10 %, sraženo 27,5 % (1 925) → uživatel zaúčtuje 700 na 681400
(započitatelná) a 1 225 na pohledávku za zahraničím; samostatný 15 % = 1 050 − zápočet 700 = 350 doplatek (681300/347300);
náklad na daň celkem 1 050 (= 15 %), pohledávka 1 225.
Odložená (pravidlo „Odložená 5 %“, účet daně = vlastní kapitál, rozvahový 348): výjimka na účtu přecenění v kapitálu se zůstatkem
40 000 → požadovaný stav 2 000,00; při zůstatku −10 000 bez „Vykázat i pohledávku“ → 0.
Třídy: dvě třídy 50/50, penále 2 000 jen třídy A (Mimo základ) → daňový efekt 0; zahraniční dividenda 5 000 jen třídy A → samostatná daň
750 celá třídě A (přesun A +375 / B −375).
Krácení: úplata za obhospodařování 40 000 s výjimkou „Mimo základ, podíl 25 %“ → 10 000 mimo základ, 30 000 snižuje základ;
s podílem 10 % → 4 000 mimo základ.
Další testy: bez výjimek = dnešní výsledky; výjimka na účtu úplaty má přednost před krokem (D2); migrace sazeb do pravidel; nové sdílené
pravidlo použité ve dvou fondech; doměrek na 681200 se nedorovná.


REFERENČNÍ PŘÍKLAD – doplnění (ZIF 5 %, jedna třída, CZK; čísla v Kč, daň na 2 desetinná místa):
- akcie FVOCI: nákup 100 + poplatek 1 (kapitalizace, ZJ-16) → pořizovací cena 101; RH 130 → OCI 29; odložená 5 % × 29 = 1,45
  (`revaluation_reserve_tax` MD / 348000 D); splatná beze změny (OCI není ve výsledku);
- prodej v dalším období za 140 → OCI 0, „Realizované přecenění FVOCI“ +39, odložená → 0 (rozpuštění 1,45), splatná + 5 % × 39 = 1,95;
- dluh FVOCI: nákup 980, naběhlá 985, RH 990 → úrok 5 ve výsledku (splatná + 0,25), OCI 5 (odložená 0,25); prodej 995 při naběhlé 987 →
  úrok 2 + realizace 8 ve výsledku (splatná + 0,50), OCI 0, odložená 0;
- FVTPL akcie: nákup 100, RH 130 → +30 ve výsledku, splatná + 1,50 hned, odložená 0;
- hospodářský rok 1. 7.–30. 6.: ocenění k 30. 6. 2027, výsledek 1. 7. 2026–30. 6. 2027 = 120 000 → splatná 6 000,00 (zaúčtovaná
  od 1. 7. 2026 dorovná); ocenění k 31. 7. 2027, výsledek 1.–31. 7. 2027 = 4 000 → splatná 200,00 (NE 6 200 – nové období začíná od nuly,
  zaúčtovaná = pohyb 681000 od 1. 7. 2027); stejný fond s kalendářním rokem by k 31. 7. počítal od 1. 1.
- dividendy (ZIF 5 %): česká hrubá 10 000, srážka 15 % → 714100 10 000, 681100 1 500, pohledávka 8 500; Mimo základ, neuznatelné
  5 % → +500 do základu ZIF (+25,00); rakouská 7 000, sraženo 27,5 %, smluvní 10 % → 714200 7 000, 681400 700, pohledávka k vrácení
  1 225, pohledávka z dividendy 5 075 → samostatný 1 050 − zápočet 700 = 350,00; neuznatelné 5 % → +350 do základu ZIF (+17,50).
TESTY navíc: tytéž příklady v investra_nav (test_tax_rules.py, test_fvoci.py, test_fiscal_year.py) a engine v tools/nav_reference.
```

## 9.2 Technický plán (C0 odchylky, modely, výpočet, migrace, zobrazení, testy C5)
### C0. Odchylky od zadání v2 (k potvrzení)
1. **Účty pravidla jako kód účtu, ne nová role.** Role (`investra.account.role`) jde dnes založit jen datovým souborem (seznam má
   `create="false"`, data `noupdate`), mapování je po knihách. Sdílené pravidlo proto drží **kód účtu** (Char): „Účet daně“, „Rozvahový účet“,
   „Započíst daň z účtu“; v knize fondu se dohledá podle kódu. Nové účty jsou v šabloně „Další účty“ existujících rolí (`EXTRA_ROLE_ACCOUNTS`):
   681xxx a 682000 k `expense_tax`, 347300 a 348000 k `tax_payable` (role se už jmenuje „Odložená a splatná daň“). ČNB sčítá hlavní i další
   účty role, výkazy se nemění. Uživatel pak založí nové pravidlo bez programátora: účet v osnově knihy + přidat ho k roli v Účtech rolí.
   Při výpočtu chybějící účet v knize = stop s jasnou hláškou; účet bez role = stop („přidejte ho k roli Daň z příjmů“).
2. **Nové analytické účty v šabloně** (výjimky jsou po účtech; dnes je jediný účet dividend 714000 a penále ani reprezentace účet nemají):
   714100 Dividendy tuzemské, 714200 Dividendy zahraniční, 714300 Dividendy z dceřiných společností (další účty role `income_dividend`);
   667300 Penále a pokuty, 667400 Reprezentace (další účty `expense_other`); 681100 Srážková daň, 681200 Doměrky a vratky daně minulých let,
   681300 Daň ze samostatného základu, 681400 Započitatelná zahraniční daň, 682000 Odložená daň (další účty `expense_tax`);
   347300 Daň ze samostatného základu – závazek, 348000 Odložená daň (další účty `tax_payable`). Čísla ověř proti `docs/osnova-501-syntetika.md`.
   Migrace `investra_chart_fund` (vzor 20.0.0.9.0: `_ensure_fund_accounts`, `_map_fund_roles` → `_assign_extra_accounts`).
3. **Zbytek účtu s výjimkou se řídí výjimkou, ne krokem (D2).** Účet s výjimkou: podíl jde do pravidla řádku, zbytek do výchozího pravidla
   vždy jako běžná položka (náklad základ snižuje i při kroku 1). Volba kroku platí jen pro účty úplat a odměny bez výjimky.
4. **Odložená daň bez rozdělení po třídách**: dělí se poměrem tříd. Výjimky odložené daně jen na rozvahových účtech (aktiva, závazky, VK).
5. **Výběr účtu ve výjimce**: místo řazení „nejdřív s pohybem“ sloupec **Pohyb od 1. 1.** v tabulce výjimek a doména výsledkové
   účty knihy fondu (rozvahové jen s pravidlem Odložená). Jednodušší, stejný účel.
6. **Návrh výchozího pravidla podle druhu fondu nejde**: `entity_type` rozlišuje jen SICAV, fond, podfond, ne podílový fond.
   Výchozí pravidlo se vybírá ručně; kontrola ocenění upozorní „Fond nemá výchozí daňové pravidlo – daň se nepočítá“.
7. **Oprava v referenčním příkladu**: při ztrátě vychází základ ZIF −36 000 (se 5 % neuznatelných z dividend −35 250), ne −37 000.
8. **Osvobozený podíl v dceřiné společnosti** (§ 19, § 23/4/k): jeho přecenění a prodej jdou na společné účty 715000/715100, výjimka po účtech
   ho neoddělí. V tomto zadání ručně opravou základu; otevřený bod (výnosový účet podle druhu nástroje nebo portfolia).

### C1. Modely (investra_nav)
- `investra.tax.rule` (sdílené, bez company_id; mail.thread, tracking): name, kind (`general` Obecný základ / `separate` Samostatný základ /
  `exempt` Mimo základ daně), method (`current` Splatná – výsledek od 1. 1. / `deferred` Odložená – zůstatek k datu; jen u základů),
  tax_account_code, balance_account_code, credit_account_code (jen splatná), recognise_asset (jen odložená, výchozí ne), note, active,
  version_ids. Kontroly: exempt nemá sazbu ani účty; základy mají oba účty.
- `investra.tax.rule.version` (`investra.line.tracking.mixin`): rule_id, valid_from, rate, decision_ref. Ochrana jako
  `investra.fee.version._check_unused`: verze použitá v ocenění mimo návrh (rozpad daně ji uvádí) se nemění, změna = nová verze.
- `investra.fund.tax.exception` (tracking mixin): fund_id, company_id (related), account_id (check_company), tax_rule_id, share
  (výchozí 1,0; 0 < share ≤ 1), nondeductible_pct (výchozí 0; jen u výnosového účtu), movement_ytd (počítané), note.
  Unikátní (fund, account). Výsledkový účet s libovolným pravidlem; rozvahový jen s method = deferred.
- `investra.fund`: tax_rule_id (výchozí pravidlo; jen kind general), tax_rate_now (počítané), tax_exception_ids, tax_fee_rule_id
  (nosič – pravidlo úplaty kind tax, jedno na fond, založí se samo při volbě výchozího pravidla; při vyprázdnění archivace přes `_check_archive`),
  tax_base_step (related `tax_fee_rule_id.base_step`, readonly=False, volby BASE_STEPS_TAX).
  Kontrola fondu: použitá pravidla (výchozí + z výjimek, bez exempt) nesmí sdílet účet daně, rozvahový účet ani účet zápočtu
  (zaúčtovaná daň pravidla = zůstatek jeho účtu).
- Nosič v Pravidlech úplat jen pro čtení (formulář: text „Daň se nastavuje ve fondu, záložka Daň“ + odkaz); druh „Očekávaná daň“ nejde
  zvolit ručně (kontrola mimo kontext zakládání z fondu). Verze nosiče zůstávají jako historie, výpočet je nečte.
- `investra.valuation.external.tax_rule_id`: u opravy daně (částky i základu) povinné, výchozí výchozí pravidlo fondu, doména pravidla
  použitá ve fondu (bez exempt). `_carried_corrections` u daně filtruje i podle tax_rule_id.
- Data (noupdate): „Daň 21 %“ (general, current, 681000/347000, 21 % od 1. 1. 2024), „Daň ZIF 5 %“ (general, current, 681000/347000,
  5 % od 1. 1. 2024), „Samostatný základ 15 %“ (separate, current, 681300/347300, zápočet 681400, 15 % od 1. 1. 2024), „Mimo základ daně“ (exempt).
  Nabídka Nastavení › Daně › Daňová pravidla. Práva jako u pravidel úplat (čtení účetní, zápis správce).

### C2. Výpočet
Jedna položka daně v `solve_fees` zůstává (nosič, klíč `("tax", nosič.id)`, kontrola „jedno pravidlo daně na fond“ platí);
`engine._tax` počítá uvnitř po pravidlech. Starý plochý `spec` (bez `rules`) = jedno výchozí pravidlo → náhled schématu a stávající testy
enginu beze změny.

`valuation._tax_item` sestaví spec:
- vyloučené účty: všechny účty role `expense_tax` (hlavní i další: 681000–681400, 682000) – do základu ani do zaúčtované daně;
- výsledkové řádky od 1. 1. seskupené podle účtu a třídy (jeden `_read_group`); každý účet: výjimka → podíl `share` do pravidla řádku,
  zbytek do výchozího pravidla; bez výjimky → celý do výchozího; pravidlo exempt se nepočítá nikde;
- splatná r: result_r = −Σ balance × podíl; specific_r[c] = Σ balance třídy × podíl (náklad +);
- výchozí pravidlo navíc: zpětné přičtení úplat dřívějších ocenění podle kroku jen u položek, jejichž účet výjimku nemá
  (`_earlier_fee_items` doplní u položky účet: role `expense_role` pravidla v knize, u ruční úplaty `entry.account_id`);
  neuznatelné náklady: + pct × výnos účtu od 1. 1. (−balance) k result_def a pct × balance třídy do specific_def[c]; opravy základu
  s tax_rule_id = r k base_r;
- zápočet r: credit_r = zůstatek účtu zápočtu od 1. 1. (má dáti);
- booked_r = pohyb účtu daně r od 1. 1.;
- odložená r: base_r = −zůstatek účtů výjimek k datu × podíl (celá historie), booked_r = −zůstatek rozvahového účtu r, bez specific;
- `split`: {účet: [(pravidlo, podíl), …]} pro úplaty tohoto ocenění; položky dopočtu nesou `tax_account` (účet nákladové role pravidla).

`engine._tax`: pro úplatu tohoto ocenění: účet bez výjimky → do výchozího pravidla podle kroku (jako dnes); účet s výjimkou → náklad × podíl
do pravidla řádku (exempt ignoruje), zbytek do výchozího vždy. Daň pravidla T_r(b) = max(0, sazba × max(b, 0) − credit_r);
odložená: sazba × b (záporné jen s recognise_asset). required_r = T_r(base_r); effective_r = (T_r(base_r + spec_r) − required_r) / spec_r.
Efekt tříd: E_c = Σ_r effective_r × specific_r[c]; přesuny přírůstkově z E jako dnes – `effect`, `effect_total`, `transfers`,
`transfers_exact` zůstávají v detailu jako součty, proto se přemostění, `_earlier_fee_items` a `_previous_tax_effect` nemění.
Výsledek: amount = Σ_r (required_r − booked_r), `rules` = rozpad po pravidlech.

`_book_tax`: jeden doklad; za každé pravidlo s pohybem dva řádky s `extra: {"account_id": …}` (účet daně, rozvahový účet –
`_create_event` účet z `extra` přebírá, OVĚŘ, že role řádku nic dalšího neřídí) + přesuny tříd jako dnes. Detail řádku: dnešní klíče
(base a result = výchozí pravidlo, required a booked = součty) + `rules`: [{rule, name, kind, method, rate, base, required, booked, move,
credit, credit_used, credit_lost, nondeductible, corrections}]. Pojistka archivace nosiče: součet zaúčtované daně přes účty použitých pravidel.
Oprava částky daně: pevná částka pravidla tax_rule_id; `_book_manual` účtuje na účty toho pravidla.

### C3. Migrace investra_nav
Pre/post: založit sdílená pravidla (data); pro každý fond s pravidlem druhu tax: všechny verze 5 % → Daň ZIF 5 %, všechny 21 % → Daň 21 %,
jinak nové pravidlo „Daň <fond>“ se stejnými verzemi a účty 681000/347000; nastavit fund.tax_rule_id a nosič; existující opravy daně
→ tax_rule_id = výchozí pravidlo. Pojistka jako 20.0.0.9.0 (ocenění Ke schválení / Schváleno zastaví migraci). Zkouška na kopii,
bez výjimek musí být ocenění 35 a 39 shodná (`docs/sql/28-snimek-oceneni.sql`).

### C4. Zobrazení a dokumenty
- Fond, záložka **Daň**: Výchozí daňové pravidlo + aktuální sazba; Základ: po kroku; tabulka Výjimky (Účet, Daňové pravidlo, Podíl,
  Neuznatelné náklady % z výnosu, Pohyb od 1. 1., Poznámka); tlačítko „Přidat běžné výjimky“ (účty podle xmlid šablony
  ifa_714100, 714200, 714300, 667300, 667400; chybějící účet přeskočí a řekne který; existující výjimku nepřepíše):
  tuzemské dividendy → Mimo základ, 5 %; zahraniční → Samostatný základ 15 %, 5 %; dceřiné → Mimo základ; penále → Mimo; reprezentace → Mimo.
- Ocenění: rozpad daně po pravidlech (počítané HTML z detailu řádku daně: pravidlo | základ | sazba | požadovaná | zaúčtovaná | pohyb;
  nulové skryté; u výchozího rozbalení: výsledek od 1. 1., výjimky, neuznatelné, kroky, opravy základu; zápočet a propadlý zápočet).
- XLS: list „Daň“ ze stejného detailu. Schéma výpočtu: „Úplata X má daňovou výjimku na účtu Y“; náhled počítá jen výchozí pravidlo
  (napsat „náhled bez výjimek“).
- Kontroly ocenění: bez výchozího pravidla upozornění; chybějící účet pravidla v knize stop; propadlý zápočet upozornění.
- Manuál (kapitola Daň z příjmů fondu podle zadání v2 F), ZJ-07 (Technický plán + Právní rámec ze zadání v2), deník D1–D5 a odchylky C0,
  otevřené body (poradce; odložená daň po třídách; odložená pohledávka ve výkazu ČNB; dceřiný podíl C0.8), plán: DA-01 „nahrazeno ZJ-07“.

### C5. Testy (referenční příklad v Odoo i `tools/nav_reference`)
Jedna třída, výchozí Daň ZIF 5 %, krok 3, výsledek od 1. 1. 100 000 (penále 2 000 na 667300, tuzemské dividendy 10 000 na 714100,
zahraniční 5 000 na 714200, dceřiné 3 000 na 714300), výjimky běžné:
- bez neuznatelných: ZIF základ 84 000 → 4 200,00 (681000/347000); s 5 % z 714100 a 714200: 84 750 → 4 237,50;
- samostatný 5 000 → 750,00 (681300/347300); zápočet 750 na 681400 → 0,00; zápočet 900 → 0,00 (150 propadá, upozornění);
- srážková daň 1 500 na 681100 základ nemění;
- ztráta: výsledek −20 000 → ZIF základ −36 000 (s 5 %: −35 250) → 0; samostatný 750,00;
- rakouská dividenda: hrubá 7 000 na 714200, 700 na 681400, 1 225 na 341200 → samostatný 1 050 − 700 = 350,00; náklad na daň 1 050;
- odložená 5 % (testovací pravidlo, účet daně = testovací účet VK, rozvahový 348000): výjimka na účtu přecenění ve VK se zůstatkem
  40 000 → 2 000,00; zůstatek −10 000 bez „Vykázat i pohledávku“ → 0;
- třídy 50/50: penále 2 000 jen A → daňový efekt 0; zahraniční dividenda 5 000 jen A → A nese celou samostatnou daň 750, B 0;
  realizovaný zisk z portfolia třídy A (část A) → daňový efekt jen A;
- krácení: úplata za obhospodařování 40 000 s výjimkou „Mimo základ, podíl 25 %“ → 10 000 mimo, 30 000 snižuje základ i při kroku 1;
  podíl 10 % → 4 000 mimo;
- bez výjimek = dnešní výsledky (stávající testy daně beze změny); migrace sazeb; jedno sdílené pravidlo ve dvou fondech;
  doměrek na 681200 se nedorovná; oprava daně a základu s daňovým pravidlem (převzetí do konce roku); chybějící účet → stop;
  dvě pravidla se stejným účtem daně ve fondu → chyba.
Zdroje výsledkových řádků s třídou vypsat v ZJ-07 a ke každému test přesunu efektu: úplaty a odměny tříd, ruční úplaty a opravy s třídou,
poplatky z úpisů a odkupů ve prospěch třídy, portfolio třídy (část A: obchody, přecenění, úroky, deriváty, kurzové přecenění),
ruční doklady s třídou.

## 9.3 Postup a kód
### C1. Účty a role (investra_chart_fund)
`data/template/account.account-investra_fund.csv` – přidat (typ, reconcile False):
```
"ifa_714100","Dividendy tuzemské","714100","income","False"
"ifa_714200","Dividendy zahraniční","714200","income","False"
"ifa_714300","Dividendy z dceřiných společností","714300","income","False"
"ifa_667300","Penále a pokuty","667300","expense","False"
"ifa_667400","Reprezentace","667400","expense","False"
"ifa_681100","Srážková daň","681100","expense","False"
"ifa_681200","Doměrky a vratky daně minulých let","681200","expense","False"
"ifa_681300","Daň ze samostatného základu","681300","expense","False"
"ifa_681400","Započitatelná zahraniční daň","681400","expense","False"
"ifa_682000","Odložená daň","682000","expense","False"
"ifa_347300","Daň ze samostatného základu – závazek","347300","liability_current","False"
"ifa_348000","Odložená daň – závazek a pohledávka","348000","liability_current","False"
```
`models/template_investra_fund.py` → `EXTRA_ROLE_ACCOUNTS`:
```python
EXTRA_ROLE_ACCOUNTS = {
    "cash_in_transit": ("ifa_119200",),
    "income_dividend": ("ifa_714100", "ifa_714200", "ifa_714300"),
    "expense_other": ("ifa_667300", "ifa_667400"),
    "expense_tax": ("ifa_681100", "ifa_681200", "ifa_681300", "ifa_681400", "ifa_682000"),
    "tax_payable": ("ifa_347300", "ifa_348000"),
}
```
Migrace `migrations/20.0.0.13.0/post-migration.py` = kopie 20.0.0.9.0 bez přejmenování (`_ensure_fund_accounts` + `_map_fund_roles`,
které volá `_assign_extra_accounts`). Verze manifestu 20.0.0.13.0. Test: nová kniha i migrovaná mají účty a další účty rolí;
`_accounts_without_role` je nevidí; výkaz ČNB VYFO20_11 ř. 57 sčítá 681xxx (role expense_tax).

### C2. Modely (investra_nav, nový soubor `models/tax_rule.py`)
```python
TAX_KINDS = [("general", "Obecný základ"), ("separate", "Samostatný základ"), ("exempt", "Mimo základ daně")]
TAX_METHODS = [("current", "Splatná – výsledek od 1. 1."), ("deferred", "Odložená – zůstatek k datu")]

class InvestraTaxRule(models.Model):
    _name = "investra.tax.rule"
    _inherit = ["mail.thread"]
    _description = "Daňové pravidlo"
    _order = "kind, name"

    name = fields.Char(required=True, tracking=True, string="Název")
    active = fields.Boolean(default=True, tracking=True)
    kind = fields.Selection(TAX_KINDS, required=True, default="general", tracking=True, string="Druh")
    method = fields.Selection(TAX_METHODS, default="current", tracking=True, string="Způsob")
    tax_account_code = fields.Char(tracking=True, string="Účet daně",
        help="Kód účtu v knize fondu: náklad na daň (681…, 682…), u odložené daně z přecenění do kapitálu účet vlastního kapitálu.")
    balance_account_code = fields.Char(tracking=True, string="Rozvahový účet", help="Kód účtu závazku: 347… splatná, 348… odložená.")
    credit_account_code = fields.Char(tracking=True, string="Započíst daň z účtu",
        help="Zahraniční daň k zápočtu (681400): zůstatek od 1. 1. snižuje daň pravidla nejvýš na nulu.")
    recognise_asset = fields.Boolean(tracking=True, string="Vykázat i pohledávku",
        help="Odložená daň: i záporný stav (pohledávka). Výchozí ne – opatrnost.")
    note = fields.Text(tracking=True, string="Poznámka")
    version_ids = fields.One2many("investra.tax.rule.version", "rule_id", string="Sazby")
    rate_now = fields.Float(compute="_compute_rate_now", digits=(10, 6), string="Aktuální sazba")

    @api.constrains("kind", "method", "tax_account_code", "balance_account_code", "credit_account_code", "recognise_asset")
    def _check_setup(self):
        for rule in self:
            if rule.kind == "exempt":
                if rule.tax_account_code or rule.balance_account_code or rule.credit_account_code or rule.version_ids:
                    raise ValidationError(self.env._("%s: Mimo základ daně nemá sazbu ani účty.", rule.name))
                continue
            if not (rule.method and rule.tax_account_code and rule.balance_account_code):
                raise ValidationError(self.env._("%s: vyplňte způsob, účet daně a rozvahový účet.", rule.name))
            if rule.method == "deferred" and rule.credit_account_code:
                raise ValidationError(self.env._("%s: zápočet je jen u splatné daně.", rule.name))

    def _version_at(self, day): ...          # stejné jako investra.fee.rule._version_at (fee_rule.py:423)

    def _book_accounts(self, company):
        """Účty pravidla v knize podle kódu; chybějící účet nebo účet bez role je chyba (stop výpočtu)."""
        self.ensure_one()
        Account = self.env["account.account"].sudo().with_company(company)
        Role = self.env["investra.account.role"]
        tax_role = Role.accounts_for(company, "expense_tax")
        payable_role = Role.accounts_for(company, "tax_payable")
        result = {}
        for key, field in (("tax", "tax_account_code"), ("balance", "balance_account_code"), ("credit", "credit_account_code")):
            code = self[field]
            if not code:
                continue
            account = Account.search([("code", "=", code), ("company_ids", "in", company.ids)], limit=1)  # OVĚŘ API kódu v Odoo 20
            if not account:
                raise UserError(self.env._("Kniha %(book)s nemá účet %(code)s daňového pravidla %(rule)s. Založte ho v osnově "
                                           "a přidejte k roli v Nastavení › Účtování › Účty rolí.", book=company.name, code=code, rule=self.name))
            expected = payable_role if key == "balance" else tax_role
            if account not in expected and not (key == "tax" and account.account_type.startswith("equity")):
                raise UserError(self.env._("Účet %(code)s pravidla %(rule)s nemá v knize %(book)s roli %(role)s (přidejte ho jako další účet).",
                                           code=code, rule=self.name, book=company.name,
                                           role="Odložená a splatná daň" if key == "balance" else "Daň z příjmů"))
            result[key] = account
        return result

class InvestraTaxRuleVersion(models.Model):
    _name = "investra.tax.rule.version"
    _inherit = ["investra.line.tracking.mixin"]
    _order = "valid_from"
    rule_id = fields.Many2one("investra.tax.rule", required=True, ondelete="cascade", index=True)
    valid_from = fields.Date(required=True, tracking=True, string="Platí od")
    rate = fields.Float(digits=(10, 6), required=True, tracking=True, string="Sazba", help="0,05 = 5 %.")
    decision_ref = fields.Char(tracking=True, string="Předpis")
    # _check_unused: verze, jejíž pravidlo je v rozpadu daně ocenění mimo návrh s datem ≥ valid_from, se nemění ani nemaže
    # (hledat investra.valuation.fee s rule_id.kind = tax a detail LIKE '%"rule": <id>%' – nebo jednodušeji uložit
    # do rozpadu id verze a hledat podle něj).

class InvestraFundTaxException(models.Model):
    _name = "investra.fund.tax.exception"
    _inherit = ["investra.line.tracking.mixin"]
    fund_id = fields.Many2one("investra.fund", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    account_id = fields.Many2one("account.account", required=True, ondelete="restrict", check_company=True, string="Účet")
    tax_rule_id = fields.Many2one("investra.tax.rule", required=True, ondelete="restrict", string="Daňové pravidlo")
    share = fields.Float(digits=(6, 4), default=1.0, string="Podíl", help="Část účtu pro toto pravidlo; zbytek zůstává ve výchozím.")
    nondeductible_pct = fields.Float(digits=(6, 2), default=0.0, string="Neuznatelné náklady (% z výnosu)")
    movement_ytd = fields.Monetary(compute="_compute_movement_ytd", string="Pohyb od 1. 1.", currency_field="currency_id")
    note = fields.Char(string="Poznámka")
    _fund_account_uniq = models.Constraint("unique(fund_id, account_id)", "Účet už má ve fondu výjimku.")
    # _check: 0 < share ≤ 1; nondeductible jen u income účtu, 0–100; rozvahový účet jen s method deferred; výsledkový ne s deferred;
    # účet nesmí patřit roli expense_tax (účty daně se nikdy nepočítají).
```
(Pozn.: v D10 se tato kontrola mění – rozvahový účet smí mít i splatné pravidlo; viz Přednosti 3.)

Fond (`_inherit = "investra.fund"` v investra_nav, `models/fund_tax.py`):
```python
tax_rule_id = fields.Many2one("investra.tax.rule", tracking=True, domain="[('kind', '=', 'general')]", string="Výchozí daňové pravidlo",
                              help="Platí pro všechny výsledkové účty bez výjimky. Prázdné = fond daň nepočítá.")
tax_rate_now = fields.Float(related="tax_rule_id.rate_now", string="Aktuální sazba")
tax_exception_ids = fields.One2many("investra.fund.tax.exception", "fund_id", string="Výjimky")
tax_fee_rule_id = fields.Many2one("investra.fee.rule", compute="_compute_tax_fee_rule")   # kind tax, active
tax_base_step = fields.Selection(BASE_STEPS_TAX, compute="_compute_tax_base_step", inverse="_inverse_tax_base_step", string="Základ: po kroku")

def write(self, vals):
    result = super().write(vals)
    if "tax_rule_id" in vals:
        self._sync_tax_carrier()   # založí nosič {"name": "Daň", "kind": "tax", "fund_id", "base_step": "3"} s kontextem
                                   # investra_tax_carrier=True; při vyprázdnění nosič archivuje (_check_archive hlídá zaúčtovanou daň)
    return result

def _tax_rules_used(self):
    return (self.tax_rule_id | self.tax_exception_ids.tax_rule_id).filtered(lambda r: r.kind != "exempt")

@api.constrains("tax_rule_id", "tax_exception_ids")
def _check_tax_accounts_distinct(self):  # dvě použitá pravidla se stejným kódem účtu daně, rozvahy nebo zápočtu → chyba

def action_add_common_tax_exceptions(self):
    COMMON = [("ifa_714100", "investra_nav.tax_rule_exempt", 1.0, 5.0), ("ifa_714200", "investra_nav.tax_rule_separate_15", 1.0, 5.0),
              ("ifa_714300", "investra_nav.tax_rule_exempt", 1.0, 0.0), ("ifa_667300", "investra_nav.tax_rule_exempt", 1.0, 0.0),
              ("ifa_667400", "investra_nav.tax_rule_exempt", 1.0, 0.0)]
    # účet: account.chart.template.with_company(company).ref(ifa, raise_if_not_found=False); chybějící vypsat v notifikaci;
    # existující výjimku nepřepsat.
```
Nosič: v `fee_rule.py` `create`/`write` – druh „tax“ jen s kontextem `investra_tax_carrier` (jinak ValidationError „Daň se nastavuje
ve fondu, záložka Daň“); formulář pravidla úplat u tax `readonly="1"` a alert s odkazem. `fee_rule._check_archive` (ř. 264):
pro tax `amount` = součet `_sum(od 1. 1., account in [účty daně všech použitých pravidel])`.
Oprava (`valuation.py:2684` `investra.valuation.external`): `tax_rule_id = fields.Many2one("investra.tax.rule", string="Daňové pravidlo")`;
`_check_correction`: u `rule.kind == "tax"` povinné a v `fund._tax_rules_used()`; formulář opravy: pole viditelné jen u daně,
výchozí `fund.tax_rule_id` (default_get z `default_corrects_rule_id`).

Data `data/tax_rules.xml` (noupdate): `tax_rule_21` (Daň 21 %, general, current, 681000/347000, verze 0,21 od 2024-01-01),
`tax_rule_zif_5` (Daň ZIF 5 %, 0,05 od 2024-01-01), `tax_rule_separate_15` (Samostatný základ 15 %, separate, current,
681300/347300, zápočet 681400, 0,15 od 2024-01-01), `tax_rule_exempt` (Mimo základ daně). Nabídka: `menu_setup_taxes` „Daně“
pod `investra_entity.menu_setup` (sekvence 37) a „Daňová pravidla“. Práva v `security/ir.access.csv` jako `investra.fee.rule`.

### C3. Engine (`investra_nav/engine.py`, nahradit `_tax` ř. 308–348)
```python
def _tax_rule_amount(rule, base):
    """Daň pravidla ze základu: splatná max(0, sazba × max(b, 0) − zápočet); odložená sazba × b (záporná jen s pohledávkou)."""
    rate = dec(rule["rate"])
    if rule.get("method") == "deferred":
        value = rate * base
        return value if rule.get("recognise_asset") else max(value, ZERO)
    return max(rate * max(base, ZERO) - dec(rule.get("credit")), ZERO)


def _tax_rules(spec):
    """Pravidla daně; plochý spec (před ZJ-07, náhled schématu) = jedno výchozí splatné pravidlo."""
    if "rules" in spec:
        return spec["rules"]
    return [{"key": "default", "default": True, "method": "current", "rate": spec["rate"], "result": spec["result"],
             "booked": spec.get("booked"), "specific": spec.get("specific") or {},
             "base_correction": spec.get("base_correction")}]


def _tax(spec, items, amounts, ratios):
    """Očekávaná daň po daňových pravidlech (ZJ-07) a přesun daňového efektu tříd (ZJ-12 B.5).

    spec: step; rules [{key, default, method, rate, result, booked, credit, recognise_asset, specific, base_correction}];
    split {účet: [(klíč pravidla, podíl), …]} – úplaty tohoto ocenění na účtech s výjimkou (klíč mimo rules = Mimo základ);
    previous_effect, previous_effect_total. Úplata na účtu bez výjimky jde do výchozího pravidla podle kroku (jako dosud),
    na účtu s výjimkou podíl do pravidla výjimky a zbytek do výchozího vždy (výjimka má přednost před krokem, D2).
    Efekt tříd E_c = Σ_r e_r × spec_{r,c}; přesuny přírůstkově ze součtů, proto přemostění a historie přesunů beze změny.
    """
    step = int(spec["step"])
    rules = _tax_rules(spec)
    keys = {rule["key"] for rule in rules}
    default = next(rule["key"] for rule in rules if rule.get("default"))
    split = spec.get("split") or {}
    deductible = {key: ZERO for key in keys}
    specific = {rule["key"]: {code: dec((rule.get("specific") or {}).get(code)) for code in ratios} for rule in rules}
    for item in items:
        if item["stage"] == STAGE_TAX:
            continue
        parts = split.get(item.get("tax_account"))
        if parts is None:
            if item["stage"] > step:
                continue
            parts = [(default, Decimal(1))]
        else:
            parts = list(parts) + [(default, 1 - sum((dec(share) for _key, share in parts), ZERO))]
        expense = fee_expense(item, amounts[item["key"]])
        for key, share in parts:
            if key not in keys or not dec(share):
                continue
            deductible[key] += expense * dec(share)
            if item.get("payer") is not None:
                specific[key][item["payer"]] += expense * dec(share)
    detail, effect = {}, {code: ZERO for code in ratios}
    required_total = booked_total = ZERO
    for rule in rules:
        key = rule["key"]
        base = dec(rule["result"]) - deductible[key] + dec(rule.get("base_correction"))
        required = _tax_rule_amount(rule, base)
        total_specific = sum(specific[key].values(), ZERO)
        effective = ZERO
        if total_specific and rule.get("method") != "deferred":
            effective = (_tax_rule_amount(rule, base + total_specific) - required) / total_specific
        for code in ratios:
            effect[code] += effective * specific[key][code]
        gross = dec(rule["rate"]) * max(base, ZERO)
        detail[key] = {"base": base, "required": required, "booked": dec(rule.get("booked")), "specific": specific[key],
                       "effective_rate": effective, "credit": dec(rule.get("credit")),
                       "credit_used": min(dec(rule.get("credit")), gross) if rule.get("method") != "deferred" else ZERO}
        required_total += required
        booked_total += dec(rule.get("booked"))
    effect_total = sum(effect.values(), ZERO)
    previous = spec.get("previous_effect") or {}
    change_total = effect_total - dec(spec.get("previous_effect_total"))
    transfers = {code: effect[code] - dec(previous.get(code)) - ratios[code] * change_total for code in ratios}
    main = detail[default]
    return {
        "amount": required_total - booked_total, "base": main["base"], "required": required_total,
        "specific": {code: sum((specific[k][code] for k in keys), ZERO) for code in ratios},
        "effective_rate": main["effective_rate"], "effect": effect, "effect_total": effect_total,
        "transfers": transfers, "rules": detail,
    }
```
Kontrola zpětné shody: plochý spec → jedno pravidlo, stejné vzorce jako dnes (base, required, effective, transfers) ✓.
`solve_fees` beze změny (jen docstring: položky nesou `tax_account`).

### C4. Ocenění (`investra_nav/models/valuation.py`)
`_apply_fees` (ř. 1461): položkám úplat a odměny doplnit `"tax_account": Role.account_for(company, rule.expense_role).id`,
ruční úplatě `entry.account_id.id`, opravě úplaty účet nákladové role opravovaného pravidla. Položka daně se přidá jen,
když `_tax_item` nevrátí None (fond bez výchozího pravidla → kontrola-upozornění `tax_no_rule`).

`_earlier_fee_items` (ř. 961): do položky přidat `"account"` (stejně jako výše; řádek pravidla `line.rule_id.expense_role`,
ruční `line.external_id.account_id`, oprava `line.external_id.corrects_rule_id.expense_role`; daň None).

`_tax_item` (ř. 1210) – nové tělo:
```python
def _tax_item(self, rule):
    fund, company = self.fund_id, self.company_id
    default_rule = fund.tax_rule_id
    if not default_rule:
        return None
    step = int(rule.base_step)
    year_start = date_type(self.date.year, 1, 1)          # D6: fund._fiscal_year_start(self.date)
    Role = self.env["investra.account.role"]
    tax_accounts = Role.accounts_for(company, "expense_tax")
    exceptions = {e.account_id: e for e in fund.tax_exception_ids}
    used = fund._tax_rules_used()
    accounts = {r: r._book_accounts(company) for r in used}
    versions = {r: r._version_at(self.date) for r in used}
    current = used.filtered(lambda r: r.method == "current")
    rows = {r: {"result": Decimal(0), "specific": {c.id: Decimal(0) for c in fund.class_ids},
                "nondeductible": Decimal(0)} for r in used}

    def add(tax_rule, balance, fund_class, share=Decimal(1)):
        if tax_rule in rows and tax_rule in current:
            rows[tax_rule]["result"] -= balance * share
            if fund_class:
                rows[tax_rule]["specific"][fund_class.id] += balance * share

    pnl = [("date", ">=", year_start), ("account_id", "not in", tax_accounts.ids),
           "|", ("account_id.account_type", "=like", "income%"), ("account_id.account_type", "=like", "expense%")]
    groups = self.env["account.move.line"].sudo()._read_group(
        self._line_domain(*pnl), groupby=["account_id", "investra_class_id"], aggregates=["balance:sum"])
    for account, fund_class, balance in groups:
        balance = d(balance)
        exception = exceptions.get(account)
        if not exception:
            add(default_rule, balance, fund_class)
            continue
        share = d(exception.share)
        add(exception.tax_rule_id, balance, fund_class, share)
        add(default_rule, balance, fund_class, 1 - share)
        if exception.nondeductible_pct:
            pct = d(exception.nondeductible_pct) / 100
            add(default_rule, balance * pct, fund_class)          # výnos (záporný zůstatek) → + pct × výnos k základu
            rows[default_rule]["nondeductible"] -= balance * pct
    for item in self._earlier_fee_items(self._year_start()):
        if item["stage"] == engine.STAGE_TAX or item["stage"] <= step or item.get("account") in exceptions:
            continue
        rows[default_rule]["result"] += item["expense"]
        if item["payer"] in rows[default_rule]["specific"]:
            rows[default_rule]["specific"][item["payer"]] -= item["expense"]
    specs = []
    for r in used:
        acc, version = accounts[r], versions[r]
        spec = {"key": r.id, "default": r == default_rule, "method": r.method, "rate": d(version.rate),
                "recognise_asset": r.recognise_asset, "version": version.id}
        if r.method == "current":
            spec.update(result=rows[r]["result"], specific=rows[r]["specific"],
                        booked=self._sum(("date", ">=", year_start), ("account_id", "=", acc["tax"].id)),
                        credit=self._sum(("date", ">=", year_start), ("account_id", "=", acc["credit"].id)) if "credit" in acc else Decimal(0))
        else:
            mine = [e for e in exceptions.values() if e.tax_rule_id == r]
            spec.update(result=sum((-self._sum(("account_id", "=", e.account_id.id)) * d(e.share) for e in mine), Decimal(0)),
                        booked=-self._sum(("account_id", "=", acc["balance"].id)), specific={})
        spec["nondeductible"] = rows[r]["nondeductible"]
        specs.append(spec)
    split = {e.account_id.id: [(e.tax_rule_id.id if e.tax_rule_id.kind != "exempt" else "exempt", d(e.share))]
             for e in exceptions.values() if e.account_id.account_type.startswith(("income", "expense"))}
    previous, previous_total = self._previous_tax_effect(rule)
    transfers_booked, transfers_exact = self._tax_transfer_history(rule)
    return {"stage": engine.STAGE_TAX, "payer": None, "tax_rules": {r.id: r for r in used}, "tax_accounts": accounts, "tax": {
        "step": step, "rules": specs, "split": split, "previous_effect": previous, "previous_effect_total": previous_total,
        "transfers_booked": transfers_booked, "transfers_exact": transfers_exact,
    }}
```
Pozor: u fondu BEZ výjimek musí být součet `rows[default]["result"]` roven dnešnímu `-self._sum(*pnl)` a `specific` dnešnímu
(dnes zaokrouhlení `_sum` na haléře a specific po třídách `quantize(CENT)`) – výsledky po kvantizaci porovnat testem na ocenění 35 a 39.
Dnešní `pnl` vylučuje jen hlavní účet `expense_tax`; nově všechny účty role – u existujících knih je jediný, výsledek stejný ✓.
(Dále platí D10: rozvahový účet ve výjimce se splatným pravidlem přispívá pohybem od začátku období – kód výše to ještě nezná, doplň.)

`_apply_base_correction` (ř. 1330), větev daně:
```python
if item["kind"] == "tax":
    for spec in item["tax"]["rules"]:
        spec["base_correction"] = sum((engine.money(d(e.amount)) for e in entries if e.tax_rule_id.id == spec["key"]), Decimal(0))
```
`_book_tax` (ř. 1685): pohyb a řádky po pravidlech:
```python
rules, accounts = item["tax_rules"], item["tax_accounts"]
source = (computed or tax)["rules"]
carried_entries = item.get("carried_entries") or self.env["investra.valuation.external"]
lines, rows, move_total, required_total = [], [], Decimal(0), Decimal(0)
for key, row in source.items():
    r = rules[key]
    carried = sum((engine.money(d(e.amount)) for e in carried_entries if e.tax_rule_id.id == key), Decimal(0))
    required = engine.money(row["required"])
    move = required - engine.money(row["booked"]) + carried
    move_total += move
    required_total += required
    lines += [{"role": "expense_tax", "amount": move, "movement_type": "fee", "extra": {"account_id": accounts[r]["tax"].id}},
              {"role": "tax_payable", "amount": -move, "movement_type": "fee", "extra": {"account_id": accounts[r]["balance"].id}}]
    rows.append({"rule": key, "name": r.name, "kind": r.kind, "method": r.method, "rate": str(spec_rate[key]),
                 "base": str(engine.money(row["base"])), "required": str(required), "booked": str(row["booked"]),
                 "move": str(move), "credit": str(row["credit"]), "credit_used": str(engine.money(row["credit_used"])),
                 "credit_lost": str(engine.money(row["credit"] - row["credit_used"])), "carried": str(carried)})
# dál jako dnes: transfers (beze změny), _fee_record(rule, move_total, None, {…dnešní klíče…, "required": required_total,
# "booked": součet booked, "rules": rows, "nondeductible": …}), _add_event(f"tax:{rule.id}", …, lines + transfer lines)
```
(`spec_rate` = {spec["key"]: spec["rate"]} z `item["tax"]["rules"]`; nondeductible a exceptions do detailu pro rozpad.)
`_book_manual` (ř. 1660) pro opravu daně: `accounts = entry.tax_rule_id._book_accounts(self.company_id)` a řádky s `extra` účty jako výše.
`_check_negative_corrections` beze změny (vrací součet).

### C5. Migrace investra_nav (`migrations/20.0.0.39.0/post-migration.py`)
```python
def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # pojistka jako investra_chart_fund 20.0.0.9.0: ocenění Ke schválení / Schváleno → UserError
    standard = {0.21: env.ref("investra_nav.tax_rule_21"), 0.05: env.ref("investra_nav.tax_rule_zif_5")}
    for carrier in env["investra.fee.rule"].with_context(active_test=False).search([("kind", "=", "tax")]):
        rates = {round(v.rate, 6) for v in carrier.version_ids}
        if len(rates) == 1 and next(iter(rates)) in standard:
            tax_rule = standard[next(iter(rates))]
        else:
            tax_rule = env["investra.tax.rule"].create({
                "name": f"Daň {carrier.fund_id.name}", "kind": "general", "method": "current",
                "tax_account_code": "681000", "balance_account_code": "347000",
                "version_ids": [(0, 0, {"valid_from": v.valid_from, "rate": v.rate, "decision_ref": v.decision_ref})
                                for v in carrier.version_ids]})
        if carrier.active:
            carrier.fund_id.with_context(investra_tax_carrier=True).tax_rule_id = tax_rule
        env["investra.valuation.external"].search([("corrects_rule_id", "=", carrier.id)]).write({"tax_rule_id": tax_rule.id})
```
OVĚŘ: kódy 681000/347000 ve všech knihách (SELECT), verze `tax_rule_21`/`zif_5` od 2024-01-01 pokrývají nejstarší ocenění s daní.

### C6. Pohledy
- Fond: nová `<page string="Daň" name="tax">` za „Schéma výpočtu“ (dědění `investra_fund.view_fund_form` v nav_views.xml):
  group (tax_rule_id, tax_rate_now widget percentage, tax_base_step), tlačítko `action_add_common_tax_exceptions`,
  `tax_exception_ids` editable bottom (account_id s doménou `[('company_ids', 'in', company_id), ('account_type', '=like', 'income%')…]`,
  tax_rule_id, share widget percentage, nondeductible_pct, movement_ytd, note).
- Ocenění, záložka Úplaty: pod tabulkou `tax_breakdown_html` (compute z detailu řádku daně – `rules`, nulové řádky skryté).
- XLS `models/package.py` (vzor listu „Úplaty“ ř. 274): list „Daň“ = řádky `rules` + výjimky + neuznatelné + zápočet.
- `fee_scheme.py:205` náhled: `version = fund.tax_rule_id._version_at(den)`; poznámka „náhled bez výjimek“; info D2 pro pravidla úplat,
  jejichž účet nákladové role má výjimku.

### C7. Testy (`investra_nav/tests/test_tax_rules.py`, engine v `tools/nav_reference/test_engine.py`)
Engine (čisté funkce, rychlé): plochý spec = dnešní výsledky; referenční příklad z plánu C5 přes spec s pravidly
(ZIF 4 200,00 / 4 237,50; samostatný 750,00; zápočet 750 → 0, 900 → 0 a credit_lost 150; ztráta −36 000; Rakousko 350,00;
odložená 2 000,00 / 0; třídy 750 celé A; krácení 25 % a 10 %). Odoo: stejný příklad přes doklady (ruční doklady na účty 667300,
714100–714300, 681100, 681400), migrace (nosič s 5 % → Daň ZIF 5 %), dva fondy se sdíleným pravidlem, doměrek 681200,
opravy s tax_rule_id (převzetí do konce roku), stop při chybějícím účtu, chyba stejného účtu dvou pravidel, upozornění bez pravidla.


# 10. Manuál – podklad kapitoly 10 Rozdělení výsledku mezi třídy

Kapitoly k doplnění: obchody (poplatek, cena odúčtování), fond (účetní období), portfolio (třída portfolia, FVOCI: rezerva, ruční ECL), dividendy a ex-kupón, daň (pravidla, výjimky, odložená z OCI, realizace akcií FVOCI, ECL jako Mimo základ).

Připravil Claude 19. 11. 2026. Názvy polí podle `e1a23bc` + nové z ZJ-08 (Podílí se na společných položkách) a ZJ-09 (Třída portfolia).
Agent: ověř popisky a cesty v menu podle skutečného UI, čísla přepočítej testem (kde se liší, oprav text, ne test).

### Jak systém dělí
- **Pravidlo:** každá položka je buď **sdílená** (bez třídy), nebo **specifická** právě pro jednu třídu.
- **Sdílené položky** se dělí alokačním poměrem. Ten se počítá z předběžného kapitálu tříd, které se podílejí na společných položkách.
- **Specifické položky** jdou celé jedné třídě.
- **Kapitál třídy** = poměr × sdílená část + specifické položky třídy (+ u třídy bez podílu její předchozí kapitál).

| Typicky sdílené | Typicky specifické |
|---|---|
| sdílené portfolio, bankovní úroky, kurzové rozdíly peněz | úplata počítaná na třídu, výkonnostní odměna třídy |
| audit, depozitář a administrace účtované na celý fond | přesun odměny do přijímající třídy, přesun podle pořadí nároků |
| daň ze sdíleného výsledku | portfolio třídy (vč. měnového zajištění), dividenda třídy, úpisy a odkupy |

### Alokační schéma – k čemu je a kdy ho nastavit
(Nastavení › Fondy › Alokační schémata; kód `investra_allocation`, výpočet `valuation._apply_scheme`)

**Bez schématu systém funguje vždy:** při každém ocenění sám spočítá alokační poměr. Poměr třídy = předběžný kapitál třídy / součet
předběžných kapitálů tříd (předběžný = kapitál z minulého ocenění + úpisy − odkupy k datu ocenění). Tímto poměrem se dělí sdílené
položky. Schéma proto běžný fond nepotřebuje.

| Nastavení | Co se stane | Pro koho |
|---|---|---|
| žádné schéma | sdílený výsledek poměrem kapitálů | většina fondů (varianty 1–4, 6–8) |
| schéma s metodou **Alokační poměr** | výsledek úplně stejný jako bez schématu; jen záznam (článek statutu, platnost od) | kdo chce mít ve fondu doložený článek statutu |
| schéma s metodou **Pořadí nároků** | sdílený výsledek se rozdělí podle nároků tříd; rozdíl proti poměru se zaúčtuje jako **přesun mezi třídami** přes vnitřní zúčtování (v přemostění „Přesun podle pořadí nároků“) | fondy s prioritními a výkonnostními (podřízenými) třídami – varianta 5 |

**Jak počítá Pořadí nároků (za období od minulého ocenění):**
1. Změna sdílené části = hodnota sdílené části teď − součet předběžných kapitálů tříd.
2. **Zisk:** nejdřív se plní cíle tříd podle **Pořadí nároku** (1, pak 2 …). Cíl = předběžný kapitál × **Cílový výnos p. a.** × část roku
   od minulého ocenění (dny/365). Když zisk na úroveň nestačí, dělí se mezi třídy téže úrovně poměrem jejich cílů. Co zbude:
   **Část zbytku podle kapitálů** (0–1) se dělí poměrem kapitálů všech tříd, zbytek pevnými **Podíly na zbytku** tříd.
3. **Ztráta:** nesou ji nejdřív třídy podle **Pořadí ve ztrátě** (1 první), každá nejvýš do výše svého kapitálu; zbytek poměrem kapitálů.
4. Rozdíl „podle schématu − podle poměru“ se zaúčtuje jako přesun mezi třídami. **Fondový kapitál se nemění**, mění se jen jeho rozdělení.

**Příklady (P = prioritní, V = výkonnostní; P 80 mil., V 20 mil.; období 1 rok):**
- *Základ* – P: pořadí 1, cíl 6 %; V: podíl na zbytku 1,0, pořadí ve ztrátě 1.
  Zisk 10 mil.: P 4,8 (cíl), V 5,2 (zbytek). Poměr by dal 8,0 / 2,0 → přesun 3,2 mil. z P do V.
  Zisk 3 mil.: cíl P 4,8 nestačí → P 3,0, V 0 (přesun 0,6 z V do P proti poměru 2,4 / 0,6).
  Ztráta 5 mil.: V −5, P 0. Ztráta 30 mil.: V −20 (celý kapitál), zbytek 10 nese P → P −10.
- *Zbytek napůl podle kapitálů* (Část zbytku podle kapitálů 0,5): zisk 10 mil. → P cíl 4,8; zbytek 5,2: polovina 2,6 poměrem
  kapitálů (P 2,08, V 0,52), polovina 2,6 podle podílů na zbytku (V 2,6) → P 6,88, V 3,12.
- *Dvě prioritní třídy* (P1 50 mil. pořadí 1 cíl 5 %, P2 30 mil. pořadí 2 cíl 7 %, V 20 mil. zbytek): zisk 3 mil. → P1 2,5 (celý cíl),
  P2 0,5 (z cíle 2,1), V 0.
- *Měsíční ocenění:* cíl za měsíc = kapitál × 6 % × 31/365. **Nedosažený cíl se do dalšího období nepřenáší** (schéma nemá
  „dohánění“); když ho statut vyžaduje, řeší se ručně nebo třídou krytí (varianta 7) – ověř se statutem.

**Na co pozor:** schéma platí od data (změna = nové schéma s novým datem, staré zůstává pro historii); na řádcích musí být jen třídy
fondu; třída bez podílu na společných položkách (varianta 6) na řádku být nesmí – v pořadí nároků se počítá jen mezi ostatními
třídami; schéma s metodou Alokační poměr řádky nepotřebuje.

### Třída bez podílu na společných položkách (volba na třídě, ZJ-08)
(Třída › **Podílí se na společných položkách**, výchozí zapnuto; měnit jde jen do prvního zaúčtovaného ocenění fondu.)

**Co dělá:** vypnutá třída se vyřadí z alokačního poměru. Nedostává podíl na sdíleném zisku ani ztrátě, nenese sdílené náklady ani
daň ze sdíleného výsledku. Její kapitál = kapitál z minulého ocenění + její úpisy a odkupy + položky jen této třídy (typicky přijatá
výkonnostní odměna, ruční úplata). Ostatní třídy si dělí sdílený výsledek poměrem spočteným jen mezi sebou.
Typické použití: **manažerská třída**, která jen přijímá výkonnostní odměnu (varianta 6). Schéma k tomu není potřeba – je to volba na třídě.

**Rozdíl proti schématu:** schéma rozděluje *sdílený výsledek* podle nároků; volba na třídě určuje, *kdo se na sdíleném výsledku vůbec
podílí*. Jdou kombinovat: pořadí nároků se pak počítá jen mezi třídami s podílem a třída bez podílu nesmí být na řádku schématu.

**Příklad:** A 60 mil., B 40 mil., M 2 mil. (bez podílu), zisk portfolia 10 mil.
- Bez volby (M by se podílela): poměr 60/40/2 z 102 → M by dostala 0,196 mil. zisku – to je chyba, kterou volba řeší.
- S volbou: poměr jen A/B = 60/40 → A +6, B +4, M 0; kapitál M zůstává 2 mil. Ztráta 10 mil.: A −6, B −4, M 0.
- Výkonnostní odměna 2 mil. z A a B převedená do M: M 4 mil.; daň ze zisku nesou A a B (M nemá podíl na sdílených položkách).
- Upozornění: když pravidlo úplaty (např. za obhospodařování) zahrnuje třídu M, formulář pravidla i kontrola ocenění ukážou
  žluté upozornění – úplata z M bývá omyl; záměrnou ztrátu M zadejte ruční úplatou.

### Varianta 1 – jedna třída (výchozí)
Fond má jednu třídu, alokační schéma není potřeba, poměr je 100 %.

### Varianta 2 – více tříd, stejné portfolio, jiné úplaty (retailová a institucionální)
- Třídy R a I; bez alokačního schématu (metoda „Alokační poměr“ je výchozí).
- Úplata za obhospodařování: dvě pravidla (R 2 %, I 1 %) s vyplněnou třídou, nebo jedno pravidlo s více třídami (každá třída počítá svou úplatu).
- Příklad: R 60 mil., I 40 mil., zisk portfolia 10 mil. Poměr je 60/40, takže R dostane +6,0 mil. a I +4,0 mil.
- Úplatu pak nese každá třída sama, z vlastního kapitálu.

### Varianta 3 – měnová třída (EUR) se zajištěním a bez něj
- Třída E má měnu zveřejnění kurzu EUR. NAV i kapitál třídy zůstávají ve funkční měně, kurz se přepočte do EUR.
- **Bez zajištění:** nic dalšího nenastavuj.
- **Se zajištěním:**
  - Založ portfolio „Zajištění E“ s třídou E.
  - Forward sjednávej do tohoto portfolia. Přecenění i vypořádání forwardu pak jde jen třídě E.
  - Peníze na bance zůstávají sdílené; vyrovná je vnitřní zúčtování.

### Varianta 4 – růstová a dividendová třída
- Pole Rozdělování výnosu: Růstová / Dividendová.
- Výplata dividendy je specifická položka dividendové třídy. Portfolio zůstává sdílené.

### Varianta 5 – prioritní a výkonnostní investiční akcie (FKI, pořadí nároků)
- Alokační schéma, metoda **Pořadí nároků**, Platí od 1. 1., Článek statutu.

| Třída | Pořadí nároku | Cílový výnos p. a. | Podíl na zbytku | Pořadí ve ztrátě |
|---|---|---|---|---|
| P (prioritní) | 1 | 6 % | 0 | 0 |
| V (výkonnostní) | – | 0 | 1,0 | 1 |

- **Zisk:** P 80 mil., V 20 mil., zisk za rok 10 mil.
  - P dostane cíl 80 × 6 % = 4,8 mil. a V zbytek 5,2 mil.
  - Rozdíl proti poměru (8,0/2,0) se zaúčtuje jako „Přesun podle pořadí nároků“.
- **Ztráta 5 mil.:** V ji nese první, do výše svého kapitálu, takže V −5 mil. a P 0.
- **Obměny:**
  - Část zbytku podle kapitálů (např. 0,5): polovina zbytku se dělí poměrem kapitálů, druhá polovina pevnými podíly.
  - Více pořadí: druhá prioritní třída s pořadím 2.

### Varianta 6 – manažerská třída (jen přijímá výkonnostní odměnu)
- **Nastavení:**
  - Třída M: vypni **Podílí se na společných položkách**. Úpis může být symbolický, nebo žádný.
  - Pravidlo výkonnostní odměny na třídách A a B (20 % nad high-water mark).
  - Na pravidle nastav Přijímající třídy = M a Podíl příjemcům z tříd = 100 % (nebo např. 50 %; zbytek je náklad vůči obhospodařovateli).
- **Rok 1:**
  - A 60, B 40, M 0 a zisk 10, takže A +6 a B +4.
  - Odměna A 1,2 a B 0,8 jde jako přesun do M, takže M = 2,0.
- **Rok 2:**
  - Zisk 10 % se dělí jen mezi A (64,8) a B (43,2), tedy +6,48 a +4,32. M zůstane 2,0.
- Ztrátu M nese jen ručně doloženou úplatou. Odkup M se zadává ručně.
- Třída M nesmí být na řádku alokačního schématu.

### Varianta 7 – třída krytí výkonnostní odměny
Na pravidle výkonnostní odměny se vyplní Třída krytí. Když třída nedosáhne cíle, kryje rozdíl třída krytí, nejvýš do výše svého kapitálu. Jde o jednodušší náhradu pořadí nároků, kde se dorovnává jen cíl odměny.

### Varianta 8 – třída s vlastním portfoliem (samostatná strategie, „side pocket“)
- Portfolio s třídou X: všechny obchody, přecenění, úroky a poplatky obchodů v něm nese jen X.
- Sdílené portfolio dělí výsledek poměrem dál.
- Průměrná pořizovací cena se vede po nástroji a portfoliu, takže stejný nástroj má ve sdíleném portfoliu a v portfoliu X dvě průměrky.

### Na co pozor
- Poměr tříd se počítá z předběžného kapitálu, tedy po úpisech a odkupech k datu ocenění.
- Schéma platí od data. Změna se zakládá novým schématem, ne přepsáním starého.
- Kontrola ΣFKT = FK musí vždy sedět. Rozdíl ze zaokrouhlení nese třída s největším přesunem.

# 11. Testy a povýšení

- Po oddílech: 2 → testy investra_instruments+, investra_nav+, investra_derivative+, investra_fx_revaluation+; 3, 4 → investra_fund+, investra_nav+,
  investra_allocation+, investra_cnb+; 5, 6, 7 → investra_instruments+, investra_nav+; 8 → investra_entity+, investra_chart_fund+, investra_nav+,
  investra_cnb+; 9 po částech (účty a migrace chart_fund; pravidla, fond, nosič, migrace nav; výpočet a třídy; zobrazení a XLS; manuál)
  → investra_nav+, investra_cnb+.
- Vždy: referenční scénáře a snímek ocenění 35 a 39 beze změny; fond bez nového nastavení (bez třídy portfolia, bez třídy bez podílu,
  kalendářní rok, bez poplatků, bez ruční ceny odúčtování, bez dividend, bez FVOCI, bez výjimek daně) = dnešní výsledky.
- Na konci `tools/run_tests.sh all`, migrace zkouškou na kopii, povýšení `investra` se zálohou, snímek 35 a 39 před a po.
  Verze modulů zvednout podle dotčených (entity, fund, allocation, chart_fund, instruments, nav, derivative, fx_revaluation, cnb).

# 12. Rozhodnutí do deníku (19. 11. 2026, Martin)
- Položka je sdílená, nebo specifická právě pro jednu třídu.
- Třída bez podílu na společných položkách = volba na třídě (ZJ-08 body 1–3); ruční krystalizace později.
- Poplatek obchodu v libovolné měně; nákup FVTPL a každý prodej = náklad, nákup AC/FVOCI = součást pořizovací ceny.
- Účetní období fondu podle knihy (hospodářský rok); roční úplaty, období výkonnostní odměny i daň od začátku účetního období.
- FVTPL se zdaňuje hned podle účetnictví; zdanění při realizaci jen u přecenění do kapitálu (FVOCI).
- FVOCI v této dávce: úrok efektivní mírou a ECL do výsledku (ECL ručně), zbylé přecenění do OCI; akcie bez recyklace (převod do
  „Realizované přecenění FVOCI“), dluh s recyklací.
- Třída bez podílu nenese daň ze sdílených položek; upozornění na úplatu z takové třídy (D6).
- Dividendy jako záznam s ex-datem, srážkou a zápočtem; výnos patří držiteli k ex-datu − 1 den; ex-kupónová lhůta dluhopisů (H).
- Celá dávka jedním během agenta.
