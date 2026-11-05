# Bezpečnostní a architektonický audit Odoo 20

**Datum:** 5. 11. 2026
**Rozsah:** read-only kontrola Odoo 20, Docker Compose, PostgreSQL, volumes, portů, `.env`, `addons_path`, oddělení addonů a rizika vůči výukovému Odoo 19.
**Závěr:** nebyla zjištěna aktivní zneužitelná zranitelnost ani kritický problém. Následující doporučení jsou hardening a provozní předvídatelnost, nikoli nálezy zneužitelné chyby.

## OK

- **Odoo 19 a 20 jsou oddělené.** Compose projekty, databáze (`odoo_cz` a `investra_dev`), sítě a pojmenované databázové/Odoo volumes se liší. Při kontrole nebyla zjištěna kolize prostředků.
- **Porty jsou omezené na localhost.** Odoo 20 je publikováno na `127.0.0.1:8070`, Odoo 19 na `127.0.0.1:8069`. PostgreSQL Odoo 20 nemá publikovaný host port; PostgreSQL výukové instance je dostupný jen přes `127.0.0.1:5432`.
- **Secrets jsou přiměřeně chráněny.** `.env` existuje, má oprávnění `0600`, není sledován Gitem a je ignorován pravidly v `.gitignore`. `.env.example` obsahuje prázdné hodnoty, nikoli skutečná hesla.
- **Addony jsou oddělené.** Odoo 20 připojuje a načítá `addons/custom`; Odoo 19 načítá Odoo Mates z `addons/third_party/odoomates`. Odoo 20 nepřipojuje Odoo Mates.
- **Zdroj third-party modulu je evidován.** `addons/third_party/README.md` uvádí zdroj, větev a konkrétní commit Odoo Mates.

## Doporučení

1. **Odoo master password před povolením správy databází.** Odoo 20 používá `--no-database-list`, a proto je správa databází aktuálně vypnutá; nenastavené `admin_passwd` tedy není v současné konfiguraci aktivní zranitelnost. Proměnná `INVESTRA_ADMIN_PASSWORD` je uvedena v `.env.example`, ale není zapojena do Compose ani konfigurace Odoo. Před případným odstraněním `--no-database-list` nakonfigurujte master password bezpečným způsobem, nebo nepoužívanou zavádějící proměnnou odstraňte.
2. **Explicitní název Compose projektu pro Odoo 19.** `docker-compose.yml` nemá kořenové `name`; název projektu se nyní odvozuje od adresáře. Výslovný název sníží riziko jiné sady sítí/volumes při spuštění Compose z jiného umístění.
3. **Objasnit dodatečné připojení `/mnt/extra-addons`.** Runtime kontrola Odoo 20 ukazuje anonymní volume na `/mnt/extra-addons` vedle bind mountu `./addons/custom:/mnt/extra-addons/custom`. Toto volume není sdílené s Odoo 19 a nebylo zjištěno, že by způsobovalo bezpečnostní problém. Pokud není potřeba, lze při budoucí schválené úpravě konfiguraci zjednodušit nebo mount výslovně zdokumentovat.

## Problém

- Nebyl zjištěn žádný aktuální zneužitelný bezpečnostní nebo architektonický problém.

## Kritický problém

- Nebyl zjištěn.

## Omezení auditu

Audit byl read-only a vztahoval se ke konfiguraci a běžícímu prostředí v okamžiku kontroly. Nešlo o penetrační test, audit zdrojového kódu všech Odoo modulů ani kontrolu bezpečnosti hostitele/macOS či veřejně přístupných systémů. Doporučení nebyla v rámci auditu aplikována.

## Stav doporučení (5. 11. 2026)

1. **Master password:** `INVESTRA_ADMIN_PASSWORD` je v `.env.example` popsaná jako místo pro heslo uživatele admin, Compose ji nepoužívá. Správa databází zůstává vypnutá (`--no-database-list`); před jejím zapnutím se nastaví master password.
2. **Název Compose projektu:** `docker-compose.yml` má `name: odoo-dev` (stejný název, jaký projekt už měl, takže beze změny běžící instance). Konfigurace ověřena `docker compose config --quiet`.
3. **Anonymní svazek `/mnt/extra-addons`:** pochází z oficiálního obrazu Odoo (VOLUME v obrazu), je prázdný a zdokumentovaný v `CLAUDE.md`. Bez dalších úprav.
