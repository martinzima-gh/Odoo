# Návrh: detail účetních událostí

Stav 11. 11. 2026, připravil Claude podle bodu 15 podkladu UX z 10. 11. 2026. Odpovědi uživatele na otázky 1–3
jsou níže (11. 11. 2026). **Provedení čeká na pokyn uživatele.**
Červená zóna: `investra_posting` (účtování), migrace.

**Bod 15 podkladu UX:** u účetní události vidět fond, částku, měnu a zdroj s proklikem.

## Jak to funguje dnes

- Model `investra.accounting.event` (`investra_posting/models/event.py`) má pole kniha, datum, druh (volný text), klíč,
  otisk, stav, doklad a storno doklad. Fond, částku, měnu ani odkaz na zdroj nemá.
- Události mají jen seznam bez formuláře; uživatelé je smějí jen číst (`account.group_account_readonly`, `r`).
- Na formuláři dokladu (`account.move`) není vidět pole `investra_event_id`.
- Události vznikají ze čtyř zdrojů; každý má fond a vazbu zpět na událost:

| Zdroj | Klíč | Druh dnes | Vazba zpět |
|---|---|---|---|
| Obchod, vypořádání obchodu (`investra.trade`) | `trade:` / `trade-settle:` | `trade` | `event_id`, `settlement_event_id` |
| Úpis a odkup (`investra.class.movement`) | `movement:` | `class_movement` | `event_id` |
| Splátka nástroje (`investra.instrument.repayment`) | `repayment:` | `trade` (nepřesné) | `event_id` |
| Ocenění (`investra.valuation`, 8 druhů dokladů) | `valuation:…` | `valuation` | `event_ids` |

## Návrh řešení

1. **Nová pole události** (jen pro čtení, plní je výhradně `_create_event`):
   - `fund_id` – fond; nepovinný (budoucí události Investra Services fond mít nebudou).
   - `res_model`, `res_id` – zdroj (Many2oneReference); dá se podle něj filtrovat a seskupovat.
   - `amount` – součet MD dokladu ve funkční měně knihy; `currency_id` = měna knihy.
   - `amount_currency`, `foreign_currency_id` – částka v původní měně (nástroje nebo třídy), jen když mají všechny
     řádky s měnou jednu cizí měnu.
   - Částky se ukládají při vzniku události (ne výpočtem z dokladu): zrušený návrh doklad nemá a seznam musí jít řadit a sčítat.
2. **Druh události** jako výběr s českými názvy: Obchod (`trade`), Vypořádání obchodu (`trade_settlement`),
   Úpis/odkup (`class_movement`), Splátka (`repayment`), Ocenění (`valuation`).
3. **`_create_event(…, source=None)`** – fond se převezme ze zdroje; upravit 4 místa volání (obchod, vypořádání,
   úpis/odkup, splátka, ocenění). Otisk ani klíč se nemění, ochrana proti dvojímu zaúčtování zůstává.
4. **Formulář události:** stav v hlavičce; tlačítka Zdroj a Doklad; fond, kniha, datum, druh, částka, měna;
   záložka Řádky dokladu (účet, třída, typ pohybu, MD, D, částka v měně); záložka Technické (klíč, otisk).
5. **Seznam:** sloupce fond, zdroj, částka, měna; filtry a seskupení podle fondu a druhu zdroje.
6. **Doklad:** na formulář `account.move` odkaz „Účetní událost Investra“ (řetězec doklad → událost → zdroj).
7. **Migrace existujících událostí** (ORM, každý modul své zdroje přes vazby zpět):
   `investra_instruments` obchody a vypořádání, `investra_nav` úpisy a odkupy, splátky a ocenění.
   Částky z dokladu; zrušené návrhy bez dokladu mají částku prázdnou. U splátek a vypořádání se opraví druh
   (`trade` → `repayment`, `trade_settlement`).

## Dopad na data a účetnictví

Žádný účetní dopad: doklady, řádky, klíče, otisky ani stavy se nemění. Přibývají jen popisné údaje události
a mění se popisné pole druhu u starých splátek a vypořádání. Aktualizace modulů: nejdřív `investra_test`,
v `investra_dev` se souhlasem uživatele (před ní záloha).

## Testy (nad `investra_test`)

- Každý zdroj vyplní fond, zdroj, druh a částku.
- Cizí měna u obchodu a u úpisu v jiné měně třídy; smíšené měny nechají částku v měně prázdnou.
- Stejný klíč se stejným obsahem vrátí stejnou událost.
- Zrušený návrh má prázdnou částku.
- Migrace doplní staré události včetně druhu u splátek a vypořádání.
- U zaúčtovaných událostí částka = součet MD dokladu.
- Zápis do nových polí uživatelem skončí chybou.

## Odpovědi uživatele (11. 11. 2026)

1. Zobrazit i původní měnu (nástroje nebo třídy): **ano**.
2. Druh jako výběr s českými názvy a oprava druhu u starých splátek migrací: **ano**.
3. Staré události doplnit migrací: **ano**.
