# Odoo 20: technické ověření pro ocenění a účtování

Stav 2026-11-07. Ověřeno na `odoo:20.0-20261102`: čtení kódu modulu `account` a sondy v databázi `investra_test`
s osnovou `l10n_cz` a smyšlenými doklady. Závěry platí pro Community a toto sestavení; po upgradu se musí znovu ověřit
automatickými testy modulů.

## Zjištění

| # | Zjištění | Jak ověřeno | Dopad | Řešení v modulech |
|---|---|---|---|---|
| 1 | Zaúčtování do uzamčeného období nehlásí chybu. `_post` tiše změní datum na první otevřený den (doklad z 15. 10. skončil 7. 11.) | Sonda, `account_move.py` | Ocenění by mohlo skončit v jiném období, než bylo schváleno | `investra_posting` zaúčtování zastaví a datum po zaúčtování kontroluje |
| 2 | Storno `_reverse_moves` bez parametrů nese dnešní datum | Sonda | Storno ocenění musí nést datum ocenění | Služba předává datum a kontroluje výsledek |
| 3 | `restrictive_audit_trail` brání smazání, ale ne návratu do návrhu | Sonda | Samotný auditní režim nestačí | Hash na denících a zákaz návratu pro doklady z událostí |
| 4 | Hash vzniká při zaúčtování, je trvalý a na deníku s doklady nejde vypnout | Sonda | Nevratné nastavení; zapnout jen záměrně | Fondové deníky mají hash od založení |
| 5 | Po zaúčtování lze měnit popis, referenci a analytiku; hash chrání jen datum, deník, společnost a na řádku popis, částky, účet, partnera | Sonda, `_get_integrity_hash_fields` | Vlastní pole (třída, nástroj, typ pohybu) by šla po zaúčtování přepsat, a tím změnit NAV tříd | Vlastní ochrana zápisu a zařazení polí do hashe |
| 6 | Uživatel se základní účetní skupinou zaúčtuje interní doklad a vrátí ho do návrhu | Sonda | Standardní práva čtyři oči nezajistí | Zámek návrhů na serveru, zaúčtování jen přes službu |
| 7 | Návrhy dokladů lze volně měnit a mazat | Kód | Schválený sumář by přestal platit | Zámek a snímek s kontrolním součtem |
| 8 | Načtení české osnovy přepíše měnu společnosti na CZK; nastavení EUR po načtení bez dokladů projde | Sonda | Fond v EUR by tiše vznikl v CZK | Založení knihy měnu po načtení vynutí a zkontroluje |
| 9 | Chybí-li kurz před datem, Odoo vezme první pozdější kurz bez upozornění | Sonda | Použití budoucího kurzu v ocenění | `investra_rates` vyžaduje kurz k datu a hlídá stáří |
| 10 | Kurzy bez společnosti se základem CZK fungují i pro společnost v EUR; kurz společnosti má přednost | Sonda, přepočet 1 234 567,89 EUR bez odchylky | Jedna sada ČNB pro všechny knihy, ECB jako kurzy společnosti | `investra_rates` |
| 11 | Účty dvou společností jsou oddělené, účet cizí společnosti na dokladu Odoo odmítne | Sonda | Model samostatných společností je použitelný | Testy oddělení knih |
| 12 | Hard lock nejde posunout zpět | Sonda | Uzamčení období je trvalé, proto až po stanovisku depozitáře | Uzamčení je poslední krok ocenění |
| 13 | Česká osnova zapíná účtování storna (záporné částky na stejné straně) | Sonda | Obraty se po stornu nenafouknou | Testy kontrolují storno se zápornými částkami |
| 14 | Založení společnosti s osnovou trvá přibližně 2 sekundy; první načtení šablony může spustit instalaci a potvrdit transakci | Sonda | Desítky knih nejsou problém; hromadné založení nesmí počítat s vrácením transakce | Založení knihy jde po jedné |

## Co z toho plyne pro návrh

- Serverová pravidla patří do `investra_posting`, ne do jednotlivých modulů. Doklady z událostí mění jen služba.
- Klíč k obejití ochrany je objekt v paměti procesu, stejně jako `BYPASS_LOCK_CHECK` v jádru Odoo, takže ho nejde poslat přes API ani přes kontext z prohlížeče.
- `investra_posting` závisí na `investra_fund`, protože třída je pole na účetním řádku. Oproti tabulce modulů v architektuře je to změna pořadí.

## Neověřeno

Chování v UI, výkon při velkých objemech, vzájemná slučitelnost s Enterprise a chování po upgradu Odoo.
