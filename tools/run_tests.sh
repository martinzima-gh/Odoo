#!/usr/bin/env bash
# Spustí testy Odoo vlastních modulů na nové dočasné databázi investra_ci_<čas>.
# Databáze se založí, moduly se do ní nainstalují (s l10n_cz a account_peppol jako pracovní databáze, bez demo dat), proběhnou testy
# a databáze se i s filestore smaže. Pracovní databáze investra ani jiné databáze se nepoužívají.
# Celý log uloží do .test-logs/ (mimo git), na obrazovku vypíše jen souhrn a chyby.
#
# Použití:
#   tools/run_tests.sh investra_nav                 # jeden modul (instalace včetně závislostí)
#   tools/run_tests.sh investra_nav,investra_rates  # více modulů
#   tools/run_tests.sh all                          # všechny investra_* kromě investra_env_banner
#   TEST_TAGS=/investra_nav:TestValuation tools/run_tests.sh investra_nav   # jen vybraná třída
#   MAX_LINES=400 tools/run_tests.sh investra_nav   # delší výpis chyb (výchozí 200)
#   KEEP_DB=1 tools/run_tests.sh investra_nav       # databázi po testu nesmazat (k ladění; pak smazat ručně)
#
# Migrace se tu netestují (databáze je čistá); zkouška migrace patří na dočasnou kopii ze zálohy.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODULES="${1:-}"
if [[ "$MODULES" == "all" ]]; then
  MODULES="$(cd "$ROOT/addons/custom" && ls -d investra_*/ | tr -d / | grep -vx investra_env_banner | paste -sd, -)"
fi
if [[ -z "$MODULES" || ! "$MODULES" =~ ^[a-z0-9_]+(,[a-z0-9_]+)*$ ]]; then
  echo "Použití: tools/run_tests.sh modul[,modul...] | all" >&2
  exit 2
fi

DB="investra_ci_$(date +%Y%m%d_%H%M%S)"
[[ "$DB" =~ ^investra_ci_[0-9_]+$ ]] || { echo "Neplatný název dočasné databáze: $DB" >&2; exit 2; }

LOG_DIR="$ROOT/.test-logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/$(date +%Y%m%d-%H%M%S)-${MODULES//,/+}.log"
[[ ${#LOG} -gt 200 ]] && LOG="$LOG_DIR/$(date +%Y%m%d-%H%M%S)-sada.log"
MAX_LINES="${MAX_LINES:-200}"

if [[ -z "${TEST_TAGS:-}" ]]; then
  TEST_TAGS="$(echo "$MODULES" | sed 's/^/\//; s/,/,\//g')"
fi

COMPOSE=(docker compose -f "$ROOT/docker-compose.investra.yml")
ODOO=("${COMPOSE[@]}" run --rm --no-deps -T odoo odoo)
ADDONS="--addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/custom"

cleanup() {
  if [[ "${KEEP_DB:-}" == "1" ]]; then
    echo "KEEP_DB=1 – databáze $DB zůstala; po ladění ji smaž (i s filestore) příkazem odoo db drop."
    return
  fi
  # Smaže jen tuto dočasnou databázi i s filestore (odoo db drop). Připojení se bere z proměnných kontejneru,
  # heslo se nepředává na příkazové řádce hostitele ani nezapisuje do logu.
  if "${COMPOSE[@]}" run --rm --no-deps -T --entrypoint sh odoo -c \
      'odoo db --db_host "$HOST" --db_user "$USER" --db_password "$PASSWORD" drop "$1"' sh "$DB" >>"$LOG" 2>&1; then
    echo "Dočasná databáze $DB smazána."
  else
    echo "POZOR: dočasnou databázi $DB se nepodařilo smazat (viz log)." >&2
  fi
}

echo "Testy: $MODULES | tagy: $TEST_TAGS | dočasná databáze: $DB"
START=$(date +%s)
trap cleanup EXIT
set +e
"${ODOO[@]}" "$ADDONS" -d "$DB" --db-filter="^${DB}\$" -i "l10n_cz,account_peppol,$MODULES" --without-demo=all \
  --test-enable --test-tags "$TEST_TAGS" --stop-after-init --no-http --max-cron-threads=0 >"$LOG" 2>&1
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
fi

# Úspěch jen při nulovém kódu, souhrnu s nenulovým počtem testů a bez chyb.
if [[ $RC -eq 0 && -n "$SUMMARY" && "$TOTAL" != "0" && "$SUMMARY" =~ ^0\ failed,\ 0\ error && -z "$ERRORS" ]]; then
  echo "OK"
  exit 0
fi
echo "NEÚSPĚCH"
exit 1
