#!/usr/bin/env bash
# Založí databázi s moduly a naplní ji ukázkovými daty (fondy A–E, investiční společnost, Investra Services).
#
# Použití (z ~/odoo-dev):
#   tools/demo_data/run_seed.sh investra              # pracovní databáze
#   tools/demo_data/run_seed.sh investra_ci_demo      # dočasná zkouška (po ní smazat: odoo db drop)
#
# Když databáze neexistuje, založí ji: všechny investra_* kromě investra_env_banner, l10n_cz, account_peppol
# (bez něj první načtení osnovy přenačte registr uprostřed skriptu), čeština, bez demo dat Odoo.
# Existující databázi nezakládá znovu; oba skripty dat nad naplněnou databází skončí hláškou a nic nezmění.
set -euo pipefail

DB="${1:-}"
if [[ ! "$DB" =~ ^(investra|investra_ci_[a-z0-9_]+)$ ]]; then
  echo "Použití: tools/demo_data/run_seed.sh investra | investra_ci_<název>" >&2
  exit 2
fi
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
COMPOSE=(docker compose -f "$ROOT/docker-compose.investra.yml")
ODOO=("${COMPOSE[@]}" run --rm --no-deps -T odoo odoo)
ADDONS="--addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/custom"
LOG_DIR="$ROOT/.test-logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/$(date +%Y%m%d-%H%M%S)-seed-$DB.log"

EXISTS="$("${COMPOSE[@]}" exec -T db psql -U odoo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$DB'")"
if [[ "$EXISTS" != "1" ]]; then
  MODULES="$(cd "$ROOT/addons/custom" && ls -d investra_*/ | tr -d / | grep -vx investra_env_banner | paste -sd, -)"
  echo "Zakládám $DB: l10n_cz,account_peppol,$MODULES (log $LOG)"
  "${ODOO[@]}" "$ADDONS" -d "$DB" --db-filter="^${DB}\$" -i "l10n_cz,account_peppol,$MODULES" --without-demo=all \
    --load-language=cs_CZ --stop-after-init --no-http --max-cron-threads=0 >>"$LOG" 2>&1 || {
      echo "Založení $DB selhalo, viz $LOG" >&2; exit 1; }
else
  echo "Databáze $DB existuje, zakládání přeskočeno."
fi

SHELL_ARGS=(shell "$ADDONS" -d "$DB" --db-filter="^${DB}\$" --no-http --max-cron-threads=0)
echo "Fondy a investiční společnost (seed.py) …"
"${ODOO[@]}" "${SHELL_ARGS[@]}" <"$ROOT/tools/demo_data/seed.py" 2>>"$LOG" | tee -a "$LOG" | grep -E "^(FOND|  KONTROLY|HOTOVO)|nic se nezměnilo|Chyba|zastaveno" || true
echo "Investra Services (seed_services.py) …"
{ printf 'CONFIG_JSON = %s\n' "$(python3 -c 'import sys; print(repr(open(sys.argv[1]).read()))' "$ROOT/tools/demo_data/services_config.json")"
  cat "$ROOT/tools/demo_data/seed_services.py"; } \
  | "${ODOO[@]}" "${SHELL_ARGS[@]}" 2>>"$LOG" | tee -a "$LOG" | grep -E "^(SERVICES|  |HOTOVO)|nic se nezměnilo|zastaveno" || true
echo "Log: $LOG"
