#!/usr/bin/env bash
# Snímek ocenění po povýšení modulů na DOČASNÉ kopii pracovní databáze (pracovní investra se nemění).
#
# Postup: kopie investra → investra_ci_snap_<čas> (pg_dump | psql, bez filestore), povýšení zadaných modulů (-u),
# přepočet ocenění ve stavu Návrh/Spočteno ze seznamu (action_compute jako admin), snímek docs/sql/28-snimek-oceneni.sql,
# porovnání se souborem bez sloupce write_date, smazání kopie. Pracovní databáze se jen čte (pg_dump).
#
# Použití:
#   tools/snimek_na_kopii.sh investra_instruments,investra_nav docs/predavky/snimek-35-39-pred-davkou.txt [35]
#   (3. parametr = id ocenění k přepočtu, čárkou; výchozí 35; ocenění v jiném stavu se nepřepočítávají)
#   KEEP_DB=1 … kopii nesmaže (k ladění; pak smazat ručně).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODULES="${1:?moduly k povýšení}"
BEFORE="${2:?soubor se snímkem před}"
RECOMPUTE="${3:-35}"
[[ "$MODULES" =~ ^[a-z0-9_]+(,[a-z0-9_]+)*$ ]] || { echo "Neplatné moduly: $MODULES" >&2; exit 2; }
[[ "$RECOMPUTE" =~ ^[0-9]+(,[0-9]+)*$ ]] || { echo "Neplatná id ocenění: $RECOMPUTE" >&2; exit 2; }
DB="investra_ci_snap_$(date +%Y%m%d_%H%M%S)"
COMPOSE=(docker compose -f "$ROOT/docker-compose.investra.yml")
ADDONS="--addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/custom"
LOG_DIR="$ROOT/.test-logs"; mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/$(date +%Y%m%d-%H%M%S)-snimek-na-kopii.log"
AFTER="$LOG_DIR/$(date +%Y%m%d-%H%M%S)-snimek-po.txt"

cleanup() {
  if [[ "${KEEP_DB:-}" == "1" ]]; then echo "KEEP_DB=1 – kopie $DB zůstala."; return; fi
  if "${COMPOSE[@]}" run --rm --no-deps -T --entrypoint sh odoo -c \
      'odoo db --db_host "$HOST" --db_user "$USER" --db_password "$PASSWORD" drop "$1"' sh "$DB" >>"$LOG" 2>&1; then
    echo "Dočasná kopie $DB smazána."
  else
    echo "POZOR: kopii $DB se nepodařilo smazat (viz $LOG)." >&2
  fi
}
trap cleanup EXIT

echo "Kopie investra → $DB"
"${COMPOSE[@]}" exec -T db createdb -U odoo "$DB"
"${COMPOSE[@]}" exec -T db sh -c 'pg_dump -U odoo investra | psql -q -v ON_ERROR_STOP=1 -U odoo "$1" >/dev/null' sh "$DB"

echo "Povýšení: $MODULES"
"${COMPOSE[@]}" run --rm --no-deps -T odoo odoo "$ADDONS" -d "$DB" --db-filter="^${DB}\$" -u "$MODULES" \
  --stop-after-init --no-http --max-cron-threads=0 >>"$LOG" 2>&1
if grep -qE '^[0-9-]+ [0-9:,]+ [0-9]+ (ERROR|CRITICAL) ' "$LOG"; then
  echo "POZOR: chyby při povýšení (viz $LOG):"; grep -E ' (ERROR|CRITICAL) ' "$LOG" | head -20
fi

echo "Přepočet ocenění: $RECOMPUTE"
"${COMPOSE[@]}" run --rm --no-deps -T odoo odoo shell "$ADDONS" -d "$DB" --db-filter="^${DB}\$" --no-http \
  --max-cron-threads=0 >>"$LOG" 2>&1 <<PY
admin = env.ref("base.user_admin")
for valuation in env["investra.valuation"].with_user(admin).browse([$RECOMPUTE]):
    if valuation.state in ("draft", "computed"):
        valuation.action_compute()
        print("PREPOCET", valuation.id, valuation.state)
    else:
        print("BEZ PREPOCTU", valuation.id, valuation.state)
env.cr.commit()
PY
grep -E "PREPOCET|BEZ PREPOCTU|Traceback|Error" "$LOG" | tail -10 || true

"${COMPOSE[@]}" exec -T db psql -U odoo -d "$DB" -v ON_ERROR_STOP=1 < "$ROOT/docs/sql/28-snimek-oceneni.sql" > "$AFTER"
# write_date se po přepočtu mění vždy; porovnává se bez něj. Počet zahozených návrhů dokladů (stav discarded) také roste.
strip() { sed -E 's/\| [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9:.]+ *$//' "$1" | grep -v ' discarded '; }
if diff <(strip "$BEFORE") <(strip "$AFTER") >/dev/null; then
  echo "SNÍMEK SHODNÝ (bez write_date a zahozených návrhů): $AFTER"
else
  echo "SNÍMEK SE LIŠÍ: $AFTER"; diff <(strip "$BEFORE") <(strip "$AFTER") || true
  exit 1
fi
