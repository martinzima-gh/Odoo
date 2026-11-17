# 5. Uživatelé a role

*Ověřeno v kódu a SELECTem na čisté databázi z ukázkového skriptu; v prohlížeči neověřeno. Přepsáno po ZJ-01 a ZJ-02 (17. 11. 2026).*

Přístup k Investře se neřídí skupinami Odoo nastavovanými ručně, ale **rolemi**. Roli zakládá uživatel s úrovní **Správa**, přidělí jí činnosti
a uživatele; skupiny Odoo se uživateli **odvodí z jeho rolí** a při změně role se přepočtou. Role se nepřidělují ke konkrétnímu fondu;
rozsah knih se řídí samostatně (povolené společnosti uživatele).

## Role

**Investra › Nastavení › Uživatelé a role › Role** (nabídku vidí jen úroveň Správa a správce systému Odoo).

| Pole role | Význam |
|---|---|
| **Název** | jedinečný („Role s tímto názvem už existuje.“) |
| **Úroveň přístupu** | **Čtení** (jen čte), **Zpracování** (zpracovává ocenění, obchody a pohyby), **Správa** (navíc zakládá a mění role a schvalovací matici) |
| **Účtuje ručně v hlavní knize** | člen smí zadávat ruční doklady v hlavní knize Odoo mimo náhled zaúčtování a schvalovací matici (skupina Odoo „Účetnictví“); zapněte jen rolím, které to smějí |
| **Činnosti** | tabulka: činnost z matice (kap. 4), příznak **Provádí** a příznak **Schvaluje**; aspoň jeden z nich („Činnost v roli musí mít aspoň příznak Provádí nebo Schvaluje.“), činnost nejvýš jednou |
| **Uživatelé** | kdo roli má; uživatel může mít rolí víc, platí nejvyšší úroveň a součet příznaků |
| **Poznámka**, **Aktivní** | neaktivní role se nezapočítává |

**Provádí** = smí činnost provést (například připravit ocenění nebo zadat ruční úpis). **Schvaluje** = smí potvrdit krok druhé osoby podle
schvalovací matice. Matice (kap. 4) říká, kolik lidí je potřeba; role říká, kdo to smí být.

Skupiny, které se z rolí odvozují (jiné skupiny uživatele, např. správa systému nebo účetnictví Odoo, zůstávají beze změny):

| Z role | Skupina |
|---|---|
| úroveň Čtení a vyšší | Investra: čtení |
| úroveň Zpracování a vyšší | Investra: příprava ocenění |
| úroveň Správa | Investra: správa |
| příznak Schvaluje u některé činnosti | Investra: schvalování ocenění |
| příznak Účtuje ručně | Účetnictví (Odoo, `account.group_account_user`) |

Příznak ručního účtování se odebere jen tehdy, když ho nedává jiná role uživatele a uživatel není správce systému ani správce účetnictví Odoo;
ti si skupinu ponechají, mají-li ji přidělenou. Skupinu **Investra: správce číselníků** role nepřidělují; dává se ručně jen osobě, která číselníky spravuje.

## Založení uživatele a přidělení rolí

Odoo standardně: **Nastavení › Uživatelé a společnosti › Uživatelé › Nový**. Založte interního uživatele, vyplňte jméno a přihlašovací údaje.
Role Investry přidělíte na záložce **Role Investry** ve formuláři uživatele, nebo v roli v poli **Uživatelé**. Uživatele upravuje jen ten, kdo má i přístup
do Nastavení (správce systému); úroveň Správa sama formulář uživatele neotevře. Přidělit role smí jen úroveň Správa nebo správce systému
(„Role zakládá a mění jen uživatel s úrovní přístupu Správa.“).

Uživatel musí mít účetní společnost knihy mezi **Povolenými společnostmi** a před prací ji zaškrtnout v přepínači společností vpravo nahoře.
Samotná role přístup ke společnosti nepřidá.

## Ukázkové role a uživatelé

Skript `tools/demo_data/run_seed.sh` zakládá v ukázkové databázi čtyři role a čtyři uživatele s přístupem ke všem knihám.
**Hesla se v manuálu neuvádějí.** Ukázkoví uživatelé mají heslo ze skriptu (proměnná prostředí, ne z repozitáře); uživatel `admin` má po založení
**výchozí heslo Odoo, které si hned změňte**.

| Role | Úroveň | Provádí / Schvaluje (10 činností matice) | Ručně účtuje | Uživatel |
|---|---|---|---|---|
| Admin | Správa | provádí i schvaluje všech 10 | ano | `admin` |
| Schvalovatel | Zpracování | provádí i schvaluje všech 10 | ano | `schvalovatel` |
| Účetní | Zpracování | jen provádí všech 10 | ano | `ucetni` |
| Náhled | Čtení | žádné činnosti | ne | `view` |

Skupiny Investry po založení (ověřeno SELECTem, `docs/sql/26-role-matice-uplaty.sql`): `admin` čtení, příprava, schvalování, správa a správce číselníků;
`schvalovatel` čtení, příprava a schvalování; `ucetni` čtení a příprava; `view` jen čtení.

## Minimální obsazení pro první ocenění

Odkaz: [kapitola 4, minimální nastavení pro první ocenění](./04-oceneni-a-matice.md#5-minimální-nastavení-pro-první-ocenění).

- Role pro připravovatele má u činnosti Schválení ocenění příznak **Provádí**; role pro schvalovatele **Schvaluje**.
- Výchozí matice u schválení ocenění vyžaduje druhou osobu: musí jít o **dva různé uživatele**. Jeden uživatel se sám neschválí
  („Zadavatel nemůže schválit vlastní ocenění.“; předchozí schvalovatel nepotvrdí další krok téhož záznamu).
- V ukázkové databázi je pro všech deset činností řádek matice „jeden člověk“ (kap. 4), takže ocenění připraví i schválí jeden uživatel; čtyři oči si zapnete novým řádkem matice.

## Co nelze obejít běžnými právy

- Matici a role mění jen úroveň Správa (nebo správce systému).
- Činnost podle matice vyžaduje roli s příznakem Provádí; krok druhé osoby roli s příznakem Schvaluje (u kroku s vyplněnou rolí právě tu roli).
- Přístup k cizí společnosti ani nezaškrtnutá společnost v přepínači se rolí nepřekoná.
- Uživatel s úrovní Čtení nic nezapíše.
