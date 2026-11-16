# Předávka: MN-14 nasazeno, zadány MN-15 až MN-19 a revize Copilota

**Cíl:** navázat po MN-14; rozdělit další práci tak, aby co nejvíc šlo na Copilota (čtení, dokumentace, pohledy).
**Stav:** větev `ukol/MN-manual`; MN-14 nasazeno do `investra` (záloha `zalohy/investra-2026-11-16-pred-MN14.dump`).

**Hotové:** nasazení MN-14 (viz sekce Výsledek v MN-14); zadání `CP-MN14-revize`, MN-15 až MN-19 v `docs/ukoly/`; plán doplněn.
**Zbývá:**
1. Martin ověří v prohlížeči Přehled fondů a fond bez záložky Kalendář; nález 9 (příklady kap. 4).
2. Synchronizovat `~/odoo-review` na `ukol/MN-manual` (Copilot nesmí začít s necommitovanými změnami) a dát Copilotovi `CP-MN14-revize`, pak MN-15, MN-16, MN-17.
3. MN-18: nejdřív Claude navrhne varianty Martinovi. MN-19 po MN-15/16, Sonnet.
**Převzetí práce Copilota:** `docs/ukoly/CP-*` a změny z `~/odoo-review`, revize diffu, zóna přes `git diff --stat`; commit s autorem „Copilot“.
**Číst:** CLAUDE.md, `docs/plan-dalsiho-vyvoje.md` (oddíl Manuál a pročištění), příslušné zadání.
