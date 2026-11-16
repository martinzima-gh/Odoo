-- FX deriváty (modul investra_derivative, úkol DE-05): smlouvy, nohy, reálná hodnota v oceněních, podrozvaha, kontrola FK.
-- Jen čtení (účet dbeaver_ro). Ověřeno 16. 11. 2026 na dočasné databázi s ukázkovým swapem fondu A (tools/demo_data/seed.py).
-- Částky jsou ve funkční měně fondu, pokud není uvedeno jinak. Podrozvaha = účty typu off_balance (do FK nevstupují).

-- 1. Smlouvy: fond, druh, protistrana, stav, sjednání a počet noh
SELECT f.name AS fond, d.contract_ref AS smlouva, d.kind AS druh, p.name AS protistrana, d.state AS stav,
       d.trade_date AS sjednano, count(l.id) AS nohy,
       count(l.id) FILTER (WHERE l.state = 'settled') AS vyporadane_nohy
FROM investra_derivative d
JOIN investra_fund f ON f.id = d.fund_id
JOIN res_partner p ON p.id = d.partner_id
LEFT JOIN investra_derivative_leg l ON l.derivative_id = d.id
GROUP BY f.id, f.name, d.id, d.contract_ref, d.kind, p.name, d.state, d.trade_date
ORDER BY f.id, d.trade_date, d.id;

-- 2. Nohy: měny a částky, sjednaný kurz, B0 (forwardové body ve funkční měně), stav a doklady
SELECT d.contract_ref AS smlouva, l.sequence AS poradi, l.settlement_date AS vyporadani, l.state AS stav,
       bc.name AS kupovana_mena, l.buy_amount AS kupovano, sc.name AS prodavana_mena, l.sell_amount AS prodavano,
       l.rate AS sjednany_kurz, l.b0, l.settlement_event_id AS doklad_vyporadani, l.offbalance_event_id AS doklad_podrozvahy
FROM investra_derivative_leg l
JOIN investra_derivative d ON d.id = l.derivative_id
JOIN res_currency bc ON bc.id = l.buy_currency_id
JOIN res_currency sc ON sc.id = l.sell_currency_id
ORDER BY d.trade_date, d.id, l.settlement_date, l.id;

-- 3. Reálná hodnota po oceněních: spočtená, ruční, použitá, zaúčtováno před oceněním a změna do výsledku
SELECT f.name AS fond, v.date AS ocenění, v.state AS stav_oceneni, d.contract_ref AS smlouva,
       x.computed_value AS spoctena, x.manual_value AS rucni, x.manual_source AS zdroj_rucni, x.difference AS rozdil,
       x.used_value AS pouzita_rh, x.booked_before AS zauctovano_pred, x.change AS zmena_do_vysledku, x.problem
FROM investra_valuation_derivative x
JOIN investra_valuation v ON v.id = x.valuation_id
JOIN investra_fund f ON f.id = v.fund_id
JOIN investra_derivative d ON d.id = x.derivative_id
WHERE v.state <> 'reversed'
ORDER BY f.id, v.date, d.id;

-- 4. Ruční hodnoty (potvrzení banky): datum, částka a měna, zdroj, důvod a příloha
SELECT d.contract_ref AS smlouva, r.date AS datum, r.amount AS castka, c.name AS mena, r.source AS zdroj,
       r.reason AS duvod, r.document_name AS priloha
FROM investra_derivative_value r
JOIN investra_derivative d ON d.id = r.derivative_id
JOIN res_currency c ON c.id = r.currency_id
ORDER BY d.id, r.date;

-- 5. Zůstatky podrozvahy a účtů derivátů podle knihy a účtu (zaúčtované řádky; role z mapování rolí na účty knihy)
SELECT c.name AS kniha, a.code_store ->> c.id::text AS ucet, string_agg(DISTINCT r.code, ', ') AS role, a.account_type AS typ,
       round(sum(l.debit), 2) AS md, round(sum(l.credit), 2) AS d, round(sum(l.balance), 2) AS zustatek
FROM account_move_line l
JOIN account_account a ON a.id = l.account_id
JOIN res_company c ON c.id = l.company_id
JOIN investra_role_account m ON m.company_id = l.company_id AND m.account_id = a.id
JOIN investra_account_role r ON r.id = m.role_id
WHERE l.parent_state = 'posted' AND l.company_id IN (SELECT company_id FROM investra_derivative)
  AND (r.code LIKE 'offbalance%' OR r.code LIKE '%derivative%')
GROUP BY c.id, c.name, a.id, a.account_type
ORDER BY c.id, 2;

-- 6. Kontrola MD = D: každý zaúčtovaný doklad fondu se smlouvami musí být vyrovnaný (čekáme 0 řádků)
SELECT m.id, m.name AS doklad, m.date, round(sum(l.debit) - sum(l.credit), 2) AS rozdil
FROM account_move m
JOIN account_move_line l ON l.move_id = m.id
WHERE m.state = 'posted' AND m.company_id IN (SELECT company_id FROM investra_derivative)
GROUP BY m.id, m.name, m.date
HAVING round(sum(l.debit) - sum(l.credit), 2) <> 0;

-- 7. Podrozvaha otevřených noh: součet zůstatku podrozvahových účtů vždy 0 (MD = D) a nulový po vypořádání všech noh
SELECT c.name AS kniha, round(sum(l.balance), 2) AS soucet_podrozvahy,
       count(DISTINCT lg.id) FILTER (WHERE lg.state = 'open') AS otevrene_nohy
FROM account_move_line l
JOIN account_account a ON a.id = l.account_id AND a.account_type = 'off_balance'
JOIN res_company c ON c.id = l.company_id
LEFT JOIN investra_derivative_leg lg ON lg.company_id = l.company_id
WHERE l.parent_state = 'posted' AND l.company_id IN (SELECT company_id FROM investra_derivative)
GROUP BY c.id, c.name
ORDER BY c.id;

-- 8. FK = aktiva − závazky u všech fondů: ocenění ke svému datu proti rozvaze (rozdíl 0; podrozvaha do FK nevstupuje).
--    Poslední ocenění v každém stavu; u rozpracovaných ocenění jsou v rozvaze už návrhy dokladů.
WITH val AS (
    SELECT DISTINCT ON (v.fund_id, v.date) v.fund_id, v.company_id, v.date, v.state, v.fund_capital
    FROM investra_valuation v WHERE v.state <> 'reversed'
    ORDER BY v.fund_id, v.date, v.version DESC
)
SELECT f.name AS fond, val.date AS datum, val.state AS stav, val.fund_capital AS fk_oceneni,
       round(sum(l.balance) FILTER (WHERE a.account_type LIKE 'asset%')
             + sum(l.balance) FILTER (WHERE a.account_type LIKE 'liability%'), 2) AS aktiva_minus_zavazky,
       round(val.fund_capital - (sum(l.balance) FILTER (WHERE a.account_type LIKE 'asset%')
             + sum(l.balance) FILTER (WHERE a.account_type LIKE 'liability%')), 2) AS rozdil
FROM val
JOIN investra_fund f ON f.id = val.fund_id
JOIN account_move_line l ON l.company_id = val.company_id AND l.parent_state IN ('posted', 'draft') AND l.date <= val.date
JOIN account_account a ON a.id = l.account_id
WHERE val.date = (SELECT max(date) FROM val v2 WHERE v2.fund_id = val.fund_id)
GROUP BY f.id, f.name, val.date, val.state, val.fund_capital
ORDER BY f.id;
