-- Pracovní databáze investra: kontrola ukázkových dat (úkol IM-13). Jen čtení.
-- Ověřeno na databázi investra 15. 11. 2026 po tools/demo_data/run_seed.sh.

-- 1. Knihy: společnost, druh, rámec, funkční měna, osnova
SELECT c.id, c.name AS kniha, e.entity_type AS druh, e.framework AS ramec, cur.name AS funkcni_mena,
       c.chart_template AS osnova
FROM res_company c
JOIN investra_entity e ON e.company_id = c.id
JOIN res_currency cur ON cur.id = c.currency_id
ORDER BY c.id;

-- 2. Ocenění podle fondu a stavu (čekáme 14 / 12 / 6 / 4 / 1, poslední u A a B rozpracované)
SELECT f.name AS fond, count(*) AS oceneni,
       count(*) FILTER (WHERE v.state = 'published') AS zverejnena,
       string_agg(DISTINCT v.state, ', ') AS stavy, max(v.date) AS posledni
FROM investra_valuation v
JOIN investra_fund f ON f.id = v.fund_id
WHERE v.state <> 'reversed'
GROUP BY f.id, f.name
ORDER BY f.id;

-- 3. Obchody podle fondu a směru
SELECT f.name AS fond, t.side AS smer, t.state AS stav, count(*) AS obchody
FROM investra_trade t
JOIN investra_fund f ON f.id = t.fund_id
GROUP BY f.id, f.name, t.side, t.state
ORDER BY f.id, t.side, t.state;

-- 4. Zařazení nástrojů podle kategorie IFRS 9 (platná zařazení)
SELECT f.name AS fond, pc.ifrs9_category AS kategorie, count(*) AS zarazeni
FROM investra_portfolio_classification pc
JOIN investra_fund f ON f.id = pc.fund_id
WHERE pc.valid_to IS NULL
GROUP BY f.id, f.name, pc.ifrs9_category
ORDER BY f.id, pc.ifrs9_category;

-- 5. Stejný nástroj ve více fondech v různých kategoriích (dluhopis fondů B a D)
SELECT i.name AS nastroj, string_agg(f.name || ': ' || pc.ifrs9_category, ' | ' ORDER BY f.id) AS fondy
FROM investra_portfolio_classification pc
JOIN investra_fund f ON f.id = pc.fund_id
JOIN investra_instrument i ON i.id = pc.instrument_id
WHERE pc.valid_to IS NULL
GROUP BY i.id, i.name
HAVING count(DISTINCT pc.ifrs9_category) > 1;

-- 6. Rozvaha každé knihy ze zaúčtovaných řádků: aktiva − závazky = vlastní kapitál + neuzavřený výsledek
SELECT c.name AS kniha,
       round(sum(l.balance) FILTER (WHERE a.account_type LIKE 'asset%'), 2) AS aktiva,
       round(-sum(l.balance) FILTER (WHERE a.account_type LIKE 'liability%'), 2) AS zavazky,
       round(-sum(l.balance) FILTER (WHERE a.account_type LIKE 'equity%'), 2) AS vlastni_kapital,
       round(-sum(l.balance) FILTER (WHERE a.account_type LIKE 'income%' OR a.account_type LIKE 'expense%'), 2) AS vysledek,
       round(sum(l.balance), 2) AS rozdil_md_d
FROM account_move_line l
JOIN account_account a ON a.id = l.account_id
JOIN res_company c ON c.id = l.company_id
WHERE l.parent_state = 'posted'
GROUP BY c.id, c.name
ORDER BY c.id;

-- 7. FK posledního zveřejněného ocenění proti rozvaze k jeho datu
WITH last AS (
    SELECT DISTINCT ON (v.fund_id) v.fund_id, v.company_id, v.date, v.fund_capital
    FROM investra_valuation v WHERE v.state = 'published'
    ORDER BY v.fund_id, v.date DESC, v.version DESC
)
SELECT f.name AS fond, last.date AS datum, last.fund_capital AS fk_oceneni,
       round(sum(l.balance) FILTER (WHERE a.account_type LIKE 'asset%')
             + sum(l.balance) FILTER (WHERE a.account_type LIKE 'liability%'), 2) AS aktiva_minus_zavazky
FROM last
JOIN investra_fund f ON f.id = last.fund_id
JOIN account_move_line l ON l.company_id = last.company_id AND l.parent_state = 'posted' AND l.date <= last.date
JOIN account_account a ON a.id = l.account_id
GROUP BY f.id, f.name, last.date, last.fund_capital
ORDER BY f.id;

-- 8. Investra Services: doklady podle deníku a stavu úhrady faktur
SELECT j.code AS denik, m.move_type AS druh, m.state AS stav, m.payment_state AS uhrada, count(*) AS doklady
FROM account_move m
JOIN account_journal j ON j.id = m.journal_id
JOIN res_company c ON c.id = m.company_id
WHERE c.name = 'Investra Services s.r.o.'
GROUP BY j.code, m.move_type, m.state, m.payment_state
ORDER BY j.code, m.move_type;
