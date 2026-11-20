# Návod krok za krokem – dávka ZJ-07 až ZJ-19 na druhém počítači

## Krok 1 – přenést soubory (jednou)
Přenes na druhý počítač (OneDrive / USB / e-mail sobě) z `C:\Users\MZima\Projects\Other\`:
- `zadani-davka-ZJ-07-az-19.md`
- celou složku `davka-ZJ-07-19\` (00-prehled.md, NAVOD-krok-za-krokem.md, beh-0 až beh-7)

Na druhém počítači v terminálu (uprav cestu, odkud kopíruješ):
```bash
mkdir -p ~/odoo-dev/docs/ukoly/podklady
cp ~/Stažené/zadani-davka-ZJ-07-az-19.md ~/odoo-dev/docs/ukoly/podklady/
cp -r ~/Stažené/davka-ZJ-07-19 ~/odoo-dev/docs/ukoly/podklady/
```
Nic necommituj ručně – udělá to agent v relaci 1.

## Krok 2 – méně klikání (jednou)
Ulož do `~/odoo-dev/.claude/settings.local.json` (když soubor existuje, jen doplň položky do "allow"):
```json
{ "permissions": { "allow": [
  "Bash(git:*)", "Bash(tools/run_tests.sh:*)", "Bash(./tools/run_tests.sh:*)", "Bash(psql:*)", "Bash(pg_dump:*)",
  "Bash(createdb:*)", "Bash(dropdb:*)", "Bash(sudo systemctl restart investra-web)", "Bash(python3:*)", "Bash(grep:*)",
  "Bash(sed:*)", "Bash(ls:*)", "Bash(cat:*)", "Edit", "Write" ] } }
```
Spouštěj Claude Code v režimu **auto** (nebo „Accept edits“). Když se přesto na něco zeptá, zvol „Yes, and don't ask again“.

## Krok 3 – relace 1: Opus 5.5, úsilí High
Nová relace v `~/odoo-dev`, model **Opus**, úsilí **High**. Vlož:
```
Přečti CLAUDE.md a proveď postupně docs/ukoly/podklady/davka-ZJ-07-19/beh-0-sonnet-slouceni-a-zadani.md a beh-1-opus-tridy.md (prompty v blocích ```), bez zastávky mezi nimi.
```
Hotovo, když napíše závěrečnou zprávu (commity, odchylky, testy, snímek, pole pro Copilota).
→ Zprávu vlož sem do relace „poradce“ (volitelné, doporučuji): zkontroluji diff, než pokračuješ.

## Krok 4 – relace 2: Sonnet 5.5, úsilí High
Nová relace, model **Sonnet**, úsilí **High**. Vlož:
```
Přečti CLAUDE.md a proveď postupně beh-2-sonnet-obdobi-poplatky-vyskladneni.md, beh-3-sonnet-dividendy-exkupon.md a beh-4-sonnet-dane-ucty-modely.md ze složky docs/ukoly/podklady/davka-ZJ-07-19/, bez zastávky mezi nimi.
```
Když skončí se zprávou „test dvakrát neprošel, převezme Opus“: nová relace Opus a vlož
```
Přečti CLAUDE.md a poslední předávku v docs/predavky/; dokonči bod, na kterém Sonnet skončil, a pak zbytek běhu podle jeho souboru v docs/ukoly/podklady/davka-ZJ-07-19/.
```

## Krok 5 – relace 3: Opus 5.5, úsilí High
Nová relace, model **Opus**, úsilí **High**. Vlož:
```
Přečti CLAUDE.md a proveď docs/ukoly/podklady/davka-ZJ-07-19/beh-5-opus-fvoci-a-vypocet-dane.md.
```
Když se zastaví kvůli pozicím FVOCI v databázi, pošli mi jeho zprávu – rozhodneme spolu.
→ Závěrečnou zprávu (tabulka referenčních čísel) vlož sem – zkontroluji.

## Krok 6 – relace 4: Copilot (VS Code, Copilot Chat, režim Agent)
Otevři `~/odoo-dev` ve VS Code, Copilot Chat → **Agent**, model libovolný (doporučuji Claude Sonnet nebo GPT, co máš v předplatném).
V nastavení zapni automatické schvalování příkazů terminálu (nebo u prvního příkazu „Always allow“).
Vlož celý obsah bloku ``` … ``` ze souboru `docs/ukoly/podklady/davka-ZJ-07-19/beh-6-copilot-formulare-a-manual.md`
(v promptu nahraď `2026-11-xx` dnešním datem). Hotovo, když pushne větev `cp/ZJ-07-19-formulare`.

## Krok 7 – relace 5: Sonnet 5.5, úsilí High
Nová relace Claude Code, model **Sonnet**, úsilí **High**. Vlož:
```
Přečti CLAUDE.md a proveď docs/ukoly/podklady/davka-ZJ-07-19/beh-7-sonnet-prevzeti-a-zaver.md.
```
Výsledek: vše na větvi `ukol/ZJ-07-dane-a-tridy`, povýšená databáze investra, zpráva se seznamem ke kontrole v prohlížeči.

## Krok 8 – kontrola a sloučení
1. Zprávu z relace 5 vlož sem – připravím kontrolu v prohlížeči bod po bodu a pokyn ke sloučení do main.
2. Projdi seznam v prohlížeči (investra-web), pak dej agentovi pokyn ke sloučení.

## Když něco
- Dojde kontext uprostřed relace: agent napíše předávku → nová relace stejného modelu: `Přečti CLAUDE.md a poslední předávku v docs/predavky/; pokračuj.`
- Agent se zastaví s otázkou: odpověz přímo, nebo jeho zprávu pošli sem.
- Snímek ocenění 35/39 se změnil: nepokračuj, pošli zprávu sem.
