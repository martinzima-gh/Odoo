#!/usr/bin/env bash
# Přečte nastavení Investra Services z investra_dev (jen SELECT) do tools/demo_data/services_config.json:
# účty (kód, název, typ, párování, aktivní), daně a fiskální pozice (aktivní), deníky (kód, název, výchozí účet)
# a datum otevření účetnictví. Doklady, partneři, bankovní účty ani DIČ se nečtou.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/tools/demo_data/services_config.json"
docker compose -f "$ROOT/docker-compose.investra.yml" exec -T db psql -q -U odoo -d investra_dev -tA -v ON_ERROR_STOP=1 <<'SQL' | python3 -m json.tool --indent 1 > "$OUT"
BEGIN TRANSACTION READ ONLY;
WITH c AS (SELECT id FROM res_company WHERE chart_template = 'cz' ORDER BY id LIMIT 1),
xid AS (SELECT model, res_id, regexp_replace(name, '^[0-9]+_', '') AS tmpl FROM ir_model_data
        WHERE module = 'account' AND model IN ('account.account', 'account.tax', 'account.fiscal.position', 'account.journal'))
SELECT json_build_object(
  'opening_date', (SELECT account_opening_date FROM res_company WHERE id = (SELECT id FROM c)),
  'accounts', (SELECT json_agg(json_build_object(
      'code', a.code_store ->> (SELECT id::text FROM c), 'template', x.tmpl,
      'name', coalesce(a.name ->> 'cs_CZ', a.name ->> 'en_US'), 'account_type', a.account_type,
      'reconcile', a.reconcile, 'active', a.active) ORDER BY a.code_store ->> (SELECT id::text FROM c))
    FROM account_account a LEFT JOIN xid x ON x.model = 'account.account' AND x.res_id = a.id
    WHERE a.code_store ? (SELECT id::text FROM c)),
  'taxes', (SELECT json_agg(json_build_object('template', x.tmpl, 'name', coalesce(t.name ->> 'cs_CZ', t.name ->> 'en_US'),
      'active', t.active) ORDER BY t.id)
    FROM account_tax t LEFT JOIN xid x ON x.model = 'account.tax' AND x.res_id = t.id WHERE t.company_id = (SELECT id FROM c)),
  'fiscal_positions', (SELECT json_agg(json_build_object('template', x.tmpl, 'name', coalesce(f.name ->> 'cs_CZ', f.name ->> 'en_US'),
      'active', f.active) ORDER BY f.id)
    FROM account_fiscal_position f LEFT JOIN xid x ON x.model = 'account.fiscal.position' AND x.res_id = f.id
    WHERE f.company_id = (SELECT id FROM c)),
  'journals', (SELECT json_agg(json_build_object('template', x.tmpl, 'type', j.type, 'code', j.code,
      'name', coalesce(j.name ->> 'cs_CZ', j.name ->> 'en_US'), 'active', j.active,
      'default_account', a.code_store ->> (SELECT id::text FROM c)) ORDER BY j.id)
    FROM account_journal j LEFT JOIN xid x ON x.model = 'account.journal' AND x.res_id = j.id
    LEFT JOIN account_account a ON a.id = j.default_account_id WHERE j.company_id = (SELECT id FROM c))
);
ROLLBACK;
SQL
echo "Uloženo: $OUT"
