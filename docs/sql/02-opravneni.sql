-- Ukázky k účtu dbeaver_ro: jen čtení, spouštět po jednom.

-- 1. Kdo jsem a do jaké databáze jsem připojený
SELECT current_user AS uzivatel, current_database() AS databaze;

-- 2. Je relace jen pro čtení? Očekávaná hodnota: on
SHOW default_transaction_read_only;

-- 3. Vlastnosti účtu
SELECT rolname AS ucet, rolsuper AS superuzivatel, rolcreatedb AS smi_zakladat_db
FROM pg_roles
WHERE rolname = current_user;

-- 4. Uživatelé Odoo bez citlivých sloupců
SELECT id, login, active
FROM res_users
ORDER BY id;

-- 5. Největší tabulky s daty
SELECT relname AS tabulka, n_live_tup AS priblizny_pocet_radku
FROM pg_stat_user_tables
WHERE schemaname = 'public' AND n_live_tup > 0
ORDER BY n_live_tup DESC
LIMIT 20;
