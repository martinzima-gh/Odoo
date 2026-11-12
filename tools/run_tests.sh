#!/usr/bin/env bash
# Spustí testy Odoo vlastních modulů nad testovací databází investra_test.
# Celý log uloží do .test-logs/ (mimo git), na obrazovku vypíše jen souhrn a chyby,
# aby se při zeleném běhu nečetly tisíce řádků.
#
# Použití:
#   tools/run_tests.sh investra_nav                 # jeden modul
#   tools/run_tests.sh investra_nav,investra_rates  # více modulů
#   TEST_TAGS=/investra_nav:TestValuation tools/run_tests.sh investra_nav   # jen vybraná třída
#   MAX_LINES=400 tools/run_tests.sh investra_nav   # delší výpis chyb (výchozí 200)
#
# Databáze je pevně investra_test; proti investra_dev se skript spustit nedá.
# Upgrade modulu (-u) mění schéma testovací databáze, ne vývojové.

set -euo pipefail

DB="investra_test"
MODULES="${1:-}"
if [[ -z "$MODULES" || ! "$MODULES" =~ ^[a-z0-9_]+(,[a-z0-9_]+)*$ ]]; then
  echo "Použití: tools/run_tests.sh modul[,modul...]" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/.test-logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/$(date +%Y%m%d-%H%M%S)-${MODULES//,/+}.log"
MAX_LINES="${MAX_LINES:-200}"

if [[ -z "${TEST_TAGS:-}" ]]; then
  TEST_TAGS="$(echo "$MODULES" | sed 's/^/\//; s/,/,\//g')"
fi

# Pojistka proti nechtěné migraci: -u aktualizuje i moduly, které na testovaném závisejí.
# Když se verze v kódu liší od verze v databázi, spustila by se migrace – bez ALLOW_UPGRADE=1 se skončí.
COMPOSE=(docker compose -f "$ROOT/docker-compose.investra.yml")
DB_VERSIONS="$("${COMPOSE[@]}" exec -T db psql -U odoo -d "$DB" -tAc \
  "SELECT name || ' ' || coalesce(latest_version, '') FROM ir_module_module WHERE name LIKE 'investra%' AND state = 'installed'")" || {
  echo "Nelze přečíst verze modulů z $DB (běží služba db?)." >&2; exit 2; }
PENDING=""
while read -r NAME DBVER; do
  [[ -z "$NAME" ]] && continue
  MANIFEST="$ROOT/addons/custom/$NAME/__manifest__.py"
  [[ -f "$MANIFEST" ]] || continue
  CODEVER="$(sed -nE "s/.*[\"']version[\"'] *: *[\"']([^\"']+)[\"'].*/\1/p" "$MANIFEST" | head -1)"
  [[ "$CODEVER" != "$DBVER" ]] && PENDING+="  $NAME: databáze $DBVER, kód $CODEVER"$'\n'
done <<<"$DB_VERSIONS"
if [[ -n "$PENDING" ]]; then
  echo "Verze modulů v $DB se liší od kódu – běh by spustil upgrade a migraci:"
  printf '%s' "$PENDING"
  if [[ "${ALLOW_UPGRADE:-}" != "1" ]]; then
    echo "Zastaveno. Upgrade testovací databáze je změna dat: po dohodě a se zálohou spusť s ALLOW_UPGRADE=1." >&2
    exit 3
  fi
  echo "ALLOW_UPGRADE=1 – pokračuji včetně upgradu."
fi

echo "Testy: $MODULES | tagy: $TEST_TAGS | databáze: $DB"
START=$(date +%s)
set +e
"${COMPOSE[@]}" run --rm --no-deps -T odoo odoo \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/custom \
  -d "$DB" --db-filter="^${DB}\$" -u "$MODULES" --test-enable --test-tags "$TEST_TAGS" \
  --stop-after-init --no-http --max-cron-threads=0 >"$LOG" 2>&1
RC=$?
set -e
echo "Doba: $(( $(date +%s) - START )) s | návratový kód: $RC | log: $LOG"

# Souhrn Odoo: „N failed, M error(s) of K tests when loading database …“
SUMMARY="$(grep -E 'odoo\.tests\.result: .* of [0-9]+ tests' "$LOG" | tail -1 | sed -E 's/.*odoo\.tests\.result: //')"
if [[ -n "$SUMMARY" ]]; then
  echo "Výsledek: $SUMMARY"
else
  echo "Výsledek: souhrn testů v logu chybí (testy možná neproběhly, viz chyby níže)"
fi

TOTAL="$(echo "$SUMMARY" | sed -nE 's/.* of ([0-9]+) tests.*/\1/p')"
if [[ "$TOTAL" == "0" ]]; then
  echo "POZOR: 0 testů není úspěch – zkontroluj název modulu a tagy."
fi
echo "Varování v logu: $(grep -cE '^[0-9-]+ [0-9:,]+ [0-9]+ WARNING ' "$LOG" || true)"

# Chyby: řádky ERROR/CRITICAL a jejich pokračování (traceback bez časové značky).
ERRORS="$(awk '
  /^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9:,]+ [0-9]+ / { inerr = ($4 == "ERROR" || $4 == "CRITICAL") }
  inerr { print }
' "$LOG")"
if [[ -n "$ERRORS" ]]; then
  N="$(echo "$ERRORS" | wc -l | tr -d ' ')"
  echo "--- Chyby (${N} řádků, zobrazeno nejvýš ${MAX_LINES}) ---"
  echo "$ERRORS" | head -n "$MAX_LINES"
  [[ "$N" -gt "$MAX_LINES" ]] && echo "… zbytek v logu"
  grep -q "COMPANY_OFFSET\|MissingError" "$LOG" && \
    echo "Tip: MissingError při přípravě testů – zkontroluj res_company_id_seq (docs/prototyp-nav.md, Spuštění testů)."
fi

# Úspěch jen při nulovém kódu, souhrnu s nenulovým počtem testů a bez chyb.
if [[ $RC -eq 0 && -n "$SUMMARY" && "$TOTAL" != "0" && "$SUMMARY" =~ ^0\ failed,\ 0\ error && -z "$ERRORS" ]]; then
  echo "OK"
  exit 0
fi
echo "NEÚSPĚCH"
exit 1
