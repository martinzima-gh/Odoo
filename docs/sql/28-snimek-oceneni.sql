-- Snímek vybraných ocenění před a po povýšení modulu (porovnat výstupy diffem). Jen čtení.
-- Ověřeno na pracovní databázi investra (2026-11-19, ocenění 35 a 39). Čísla ocenění upravit v podmínkách.

-- 1. Ocenění: stav, FK, neutrální FK, změna
SELECT id, fund_id, date, version, state, fund_capital, neutral_capital, write_date
FROM investra_valuation WHERE id IN (35, 39) ORDER BY id;

-- 2. Třídy: kapitál, kusy, kurz, přemostění, naběhlá odměna
SELECT valuation_id, class_id, capital, capital_class, units, price, delta, fee_amount, performance_amount,
       allocation_amount, tax_effect_amount, other_amount, perf_accrued
FROM investra_valuation_class WHERE valuation_id IN (35, 39) ORDER BY valuation_id, class_id;

-- 3. Úplaty: počet a součet podle ocenění
SELECT valuation_id, count(*) AS radku, sum(amount) AS soucet
FROM investra_valuation_fee WHERE valuation_id IN (35, 39) GROUP BY 1 ORDER BY 1;

-- 4. Doklady ocenění podle stavu: počet, součet částek
SELECT res_id AS valuation_id, state, count(*) AS dokladu, sum(amount) AS soucet
FROM investra_accounting_event WHERE res_model = 'investra.valuation' AND res_id IN (35, 39)
GROUP BY 1, 2 ORDER BY 1, 2;

-- 5. Kontroly ocenění: stav podle kódu
SELECT valuation_id, code, status FROM investra_valuation_check WHERE valuation_id IN (35, 39) ORDER BY 1, 2;
