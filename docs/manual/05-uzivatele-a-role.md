# 5. Uživatelé a role

*Ověřeno v kódu, v prohlížeči neověřeno.*

Uživatel se zakládá v běžné správě uživatelů Odoo. Vlastní moduly role k novému fondu ani účetní knize automaticky nepřidávají; správce je přidělí každému uživateli podle jeho práce.

## Založení uživatele

Odoo standardně: **Nastavení › Uživatelé a společnosti › Uživatelé › Nový**. Založte interního uživatele, vyplňte jméno a přihlašovací údaje a v části **Přístupová práva** přidělte skupiny níže. Přesný název a umístění těchto položek nebylo ověřeno v prohlížeči.

Uživatel musí mít účetní společnost fondu mezi **Povolenými společnostmi**. Před prací ji také zaškrtněte v přepínači společností vpravo nahoře. Samotná role nepřidá přístup ke společnosti; záznamy jsou omezené podle společností povolených uživateli.

## Skupiny a role

Vlastní názvy jsou přesně podle `res.groups` v kódu. Odoo vestavěné skupiny uvádím technickým ID, protože jejich zobrazovaný překlad vlastní moduly nedefinují.

| Název nebo ID skupiny | Co dovoluje a co ne |
|---|---|
| `account.group_account_readonly` | Vestavěná skupina Odoo poskytuje čtení řady účetních a fondových záznamů; sama o sobě nedává zápisová práva z příslušných ACL. Další skupina může oprávnění rozšířit. |
| `account.group_account_manager` | Vestavěná účetní skupina má v některých vlastních modelech plná práva, například ke knihám, fondům, třídám a rolím účtů; nenahrazuje oprávnění schvalovatele v pracovním postupu. |
| `Investra: příprava ocenění` | Přidává přístupová práva pro přípravu a změnu mnoha pracovních záznamů, například nástrojů, cen, obchodů, zařazení a ocenění; sama nepovoluje kroky vyhrazené schvalovateli. |
| `Investra: schvalování ocenění` | Povoluje schvalovací kroky, správu schvalovací matice, platnosti kurzů a založení ručních kurzů podle matice; nezahrnuje automaticky skupinu přípravy. |
| `Investra: správce číselníků` | Umožňuje spravovat číselníky klasifikace, kódy a účetní profily; přístupová práva běžně dovolují vytvořit a změnit, nikoli odstranit záznam. Nenahrazuje schvalování ocenění. |
| `base.group_system` | Vestavěná systémová skupina Odoo; vlastní ACL ji používá pro průvodce založením nové účetní knihy. Není běžnou rolí účetního. |

Skupiny `Investra: příprava ocenění`, `Investra: schvalování ocenění` a `Investra: správce číselníků` každá automaticky zahrne také `account.group_account_readonly` (nastavení `implied_ids`). Schvalovatel však není technicky členem skupiny přípravy. V matici má vyšší roli a kód ho proto uzná i tam, kde je požadována nižší role přípravy. Role nejsou přiřazené ke konkrétnímu fondu; rozsah společností se řídí samostatně.

## Minimální obsazení rolí pro první ocenění

Odkaz: [kapitola 4, minimální nastavení pro první ocenění](./04-oceneni-a-matice.md#4-minimální-nastavení-pro-první-ocenění).

- Připravovatel má skupinu **Investra: příprava ocenění**; schvalovatel má **Investra: schvalování ocenění**.
- Výchozí matice pro schválení ocenění požaduje přípravu a následný schvalovací krok. Pro výchozí režim čtyř očí musí jít o dva různé uživatele; jeden uživatel se zapnutými oběma skupinami se nemůže schválit sám.
- Oba uživatelé musí mít povolenou společnost účetní knihy fondu. Před prací ji musí také vybrat v přepínači společností.
- Skupinu **Investra: správce číselníků** přidělte jen osobě, která má číselníky opravdu spravovat. Není potřeba pro běžnou přípravu ani schvalování ocenění.

## Co nelze obejít běžnými právy

- Matici smí měnit jen schvalovatel; jinak kód vrátí „Schvalovací matici mění jen skupina schvalování ocenění.“
- Činnost podle matice vyžaduje minimálně určenou roli a případně výslovně povoleného uživatele.
- U schvalování čtyřma očima „Zadavatel nemůže schválit vlastní ocenění.“ Předchozí schvalovatel nemůže potvrdit další krok téhož záznamu.
- Přístup k cizí společnosti ani nezaškrtnutá společnost v přepínači se rolí nepřekoná.

Samotný účetní správce proto nemůže obejít pravidla pracovního postupu; přístup k jednotlivým záznamům dále omezují ACL, pravidla společností a kontroly modelů.
