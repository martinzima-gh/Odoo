# Dávka ZJ-07 až ZJ-19 – 5 relací, levnější modely, málo klikání (19. 11. 2026)

## Příprava (jednou)
1. Zkopíruj do `~/odoo-dev/docs/ukoly/podklady/`: `zadani-davka-ZJ-07-az-19.md` a celou složku `davka-ZJ-07-19/` (tyto běhy).
2. Klikání: na druhém počítači spusť Claude Code v režimu **auto** (nebo „Accept edits“) a do `~/odoo-dev/.claude/settings.local.json`
   dej povolení níže – agent pak neptá na testy, git, psql ani restart. Copilot: v agent mode zapni automatické schvalování terminálu
   (Settings › chat.tools.autoApprove / „Always allow“ u prvního příkazu).
```json
{ "permissions": { "allow": [
  "Bash(git:*)", "Bash(tools/run_tests.sh:*)", "Bash(./tools/run_tests.sh:*)", "Bash(psql:*)", "Bash(pg_dump:*)",
  "Bash(createdb:*)", "Bash(dropdb:*)", "Bash(sudo systemctl restart investra-web)", "Bash(python3:*)", "Bash(grep:*)",
  "Bash(sed:*)", "Bash(ls:*)", "Bash(cat:*)", "Edit", "Write" ] } }
```
   (Uprav podle toho, jak u vás běží Odoo – např. `Bash(./odoo-bin:*)`, `Bash(docker compose:*)`.)

## Relace (každá = jedna zpráva; když dojde kontext, agent napíše předávku a ty jen napíšeš „pokračuj“)

| Relace | Model | Prompt (vlož) | Obsah |
|---|---|---|---|
| 1 | **Opus 5.5, high** | „Přečti CLAUDE.md a proveď postupně docs/ukoly/podklady/davka-ZJ-07-19/beh-0-sonnet-slouceni-a-zadani.md a beh-1-opus-tridy.md (prompty v blocích ```), bez zastávky mezi nimi.“ | sloučení + REVOKE + zadání, třída portfolia, třída bez podílu |
| 2 | Sonnet 5.5, high | „Přečti CLAUDE.md a proveď postupně beh-2…, beh-3…, beh-4… ze složky docs/ukoly/podklady/davka-ZJ-07-19/, bez zastávky mezi nimi.“ | účetní období, poplatky, cena odúčtování, dividendy, ex-kupón, daňové modely a účty |
| 3 | **Opus 5.5, high** | „Přečti CLAUDE.md a proveď docs/ukoly/podklady/davka-ZJ-07-19/beh-5-opus-fvoci-a-vypocet-dane.md.“ | FVOCI, výpočet daně, migrace |
| 4 | Copilot (agent mode) | obsah bloku z `beh-6-copilot-formulare-a-manual.md` | formuláře, nabídky, manuál, SQL |
| 5 | Sonnet 5.5, high | „Přečti CLAUDE.md a proveď docs/ukoly/podklady/davka-ZJ-07-19/beh-7-sonnet-prevzeti-a-zaver.md.“ | převzetí Copilota, XLS, testy all, nasazení, závěr |

Opus jen v relacích 1 a 3 (jádro výpočtů); Sonnet a Copilot zbytek. Zastávky jen podle podmínek v bězích (změna snímku 35/39,
nejde to v kódu, data k migraci, pozice FVOCI) – jinak běží bez dotazů. Když Sonnet v relaci 2 dvakrát neprojde stejný test,
skončí s popisem: ten bod dej Opusu („Přečti CLAUDE.md a předávku; dokonči bod X z beh-…“).
Kontrola u mě (volitelná, levná): zprávu po relaci 1 a 3 mi vlož sem – zkontroluji diff dřív, než na tom stavějí další relace.

Pořadí je závazné: relace 2 potřebuje třídy z relace 1, relace 3 účty a modely z relace 2, Copilot pole ze všech, relace 5 vše.
Pole, která se RUŠÍ (`investra.instrument.class_id`), odstraní logický běh i z pohledů – Copilot jen přidává.
