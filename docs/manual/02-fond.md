# 2. Fond

*Ověřeno v kódu, v prohlížeči neověřeno.*

Fond je záznam navázaný na účetní knihu (kap. 1). Kniha může mít **jen jeden fond** („Kniha může mít jen jeden fond.“)
a musí být druhu Fond, Podfond nebo SICAV („Fond musí stát na knize fondu, podfondu nebo SICAV.“).
Předpoklad: nová společnost je zaškrtnutá v přepínači firem, jinak fond nevytvoříte ani neuvidíte.

## Založení

**Investra › Nastavení › Fondy › Fondy › Nový.** Vyplňte hlavičku a parametry, uložte. Třídy a kalendář přidáte na záložkách (kap. 3, 4).
Při uložení vznikne automaticky portfolio **Hlavní** (obchodní model Řízení na reálnou hodnotu; posouzení je potřeba doplnit, kap. 6)
a profil FX přecenění fondu.

## Hlavička

| Pole | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Účetní kniha** | ano | – | kniha fondu z kap. 1 (nabízí se jen druh Fond, Podfond a SICAV); po výběru se doplní funkční měna |
| **Funkční měna** | jen čtení | z knihy | v ní se vede účetnictví a NAV |
| **Obhospodařovatel** | ne | prázdné | kniha druhu Investiční společnost („Obhospodařovatel musí být kniha druhu Investiční společnost.“); její schvalovací matice platí pro fond, prázdné = výchozí matice |

## Základní parametry

| Pole | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Frekvence ocenění** | ano | Měsíčně | Denně, Týdně, Měsíčně, Čtvrtletně, Ročně; určuje termíny ocenění |
| **Výchozí desetinná místa kurzu** | ano | 4 | nová třída je převezme; na třídě 0 až 18 |
| **Výchozí zaokrouhlení kurzu** | ano | Dolů | Dolů, Matematicky, Nahoru; nová třída je převezme |
| **Zaúčtování obchodu** | ano | Trade date accounting | alternativa Settlement date accounting (IFRS 9 odst. 3.1.2); **po prvním obchodu fondu nejde změnit** („Po prvním obchodu fondu nejde způsob zaúčtování změnit.“) |

## Úpisy a odkupy – výchozí hodnoty tříd

Hodnoty se **zkopírují do nové třídy při jejím založení**; pozdější změna ve fondu už stávající třídy nemění.

| Pole | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Výchozí desetinná místa kusů** | ano | 6 | na třídě 0 až 6 (kusy se ukládají nejvýš na 6 míst) |
| **Výchozí zaokrouhlení kusů** | ano | Dolů | Dolů, Matematicky, Nahoru |
| **Výchozí: rozdíl ze zaokrouhlení kusů** | ano | Zůstává ve fondu | Zůstává ve fondu = kapitál třídy; Vrací se investorovi = závazek, výplatu zadává IS |
| **Výchozí vstupní poplatek (%)** | ne | 0 | sazba z hrubé platby úpisu; 0 až 100 |
| **Výchozí příjemce vstupního poplatku** | ano | Obhospodařovatel | viz níže |
| **Výchozí výstupní poplatek (%)** | ne | 0 | sazba z hrubé částky odkupu (kusy × cena); 0 až 100 |
| **Výchozí příjemce výstupního poplatku** | ano | Obhospodařovatel | viz níže |

**Příjemce poplatku:**

| Volba | Účetní dopad |
|---|---|
| Obhospodařovatel, Distributor | závazek fondu, poplatek se platí ven |
| Fond | výnos celého fondu, dělí se mezi třídy poměrem |
| Třída – výnos | celý poplatek jen třídě pohybu, jako výnos |
| Třída – kapitál | celý poplatek jen třídě pohybu, jako kapitál třídy |

Volbu řiďte statutem. Kapitál je vždy kapitál třídy, poměrem se dělí jen výnosy a náklady (proto Fond do kapitálu nejde).
Sazbu i příjemce lze na třídě přepsat (kap. 3).

## Úročení nástrojů

| Pole | Povinné | Výchozí | Význam |
|---|---|---|---|
| **Úročení nástrojů v naběhlé hodnotě** | ano | Efektivní úroková míra | druhá volba Lineárně |
| **Zdůvodnění lineárního úročení** | při Lineárně | – | zobrazí se jen u Lineárně; bez něj „Lineární úročení fondu musí mít zdůvodnění.“ |
| **Tolerance ruční hodnoty derivátu (% nominálu)** | ne | výchozí z modulu derivátů | ocenění upozorní, když se ruční hodnota FX derivátu liší od spočtené o víc než toto procento nominálu otevřených noh |

## Záložky

- **Třídy:** kap. 3.
- **Zpřísnění matice:** řádky schvalovací matice zpřísňující pravidla jen pro tento fond (činnost, platnost od, role, druhá osoba, počet osob). Řádky zakládají a mění jen schvalovatelé ocenění (kap. 4).
- **Kalendář ocenění:** řádky **Datum ocenění** (povinné, ve fondu jedinečné: „Datum ocenění je v kalendáři už uvedené.“) a **Plánované zveřejnění** (kap. 4).
- **Obchodní modely:** portfolia fondu (kap. 6).
- Pod formulářem je **historie** (chatter).

## Datum vzniku

Pole **Datum vzniku** (začátek prvního oceňovacího období) je ve formuláři fondu u Frekvence ocenění. Povinné není, ale
bez něj první ocenění skončí chybou „Fond nemá datum vzniku.“, takže ho vyplňte před prvním oceněním.
Po prvním ocenění fondu, které není stornované, je pole jen pro čtení a změna skončí chybou „Datum vzniku fondu … nejde změnit,
protože fond má ocenění, které není stornované.“ Po stornu všech ocenění jde změnit znovu.

## Co nejde po zaúčtování nebo prvním pohybu změnit

- **Zaúčtování obchodu** po prvním obchodu fondu.
- Kniha fondu: rámec ani společnost po zaúčtovaném dokladu (kap. 1).
- Stávající třídy se při změně výchozích hodnot ve fondu nemění.
- Fond s třídami nejde smazat (vazba tříd na fond je chráněná).

## Další krok

Přidejte třídy, kap. 3.
