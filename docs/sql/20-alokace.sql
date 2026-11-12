-- Alokační schémata, jejich řádky a součet podílů zbytku.
-- Jen čtení, spouštět po jednom. Ověřeno na databázi investra_test.

-- 1. Schémata alokace podle fondu, data účinnosti a metody
SELECT f.name AS fond, s.valid_from AS plati_od, s.method AS metoda,
       s.statute_ref AS odkaz_na_statut,
       s.residual_pro_rata AS podil_zbytku_podle_kapitalu
FROM investra_allocation_scheme s
JOIN investra_fund f ON f.id = s.fund_id
ORDER BY f.name, s.valid_from DESC;

-- 2. Řádky schématu: třída, pořadí nároku, cílový výnos a podíly
SELECT f.name AS fond, s.valid_from AS plati_od, s.method AS metoda,
       cl.code AS kod_tridy, cl.name AS trida, l.rank AS poradi_naroku,
       l.target_rate AS cilovy_vynos_pa, l.residual_share AS podil_na_zbytku,
       l.loss_rank AS poradi_ve_ztrate
FROM investra_allocation_line l
JOIN investra_allocation_scheme s ON s.id = l.scheme_id
JOIN investra_fund f ON f.id = s.fund_id
JOIN investra_fund_class cl ON cl.id = l.class_id
ORDER BY f.name, s.valid_from DESC, l.rank, cl.code;

-- 3. Součet podílů na zbytku v každém schématu; dotaz pouze zobrazuje součet
SELECT f.name AS fond, s.valid_from AS plati_od, s.method AS metoda,
       COALESCE(sum(l.residual_share), 0) AS soucet_podilu_na_zbytku,
       s.residual_pro_rata AS podil_zbytku_podle_kapitalu,
       COALESCE(sum(l.residual_share), 0) + COALESCE(s.residual_pro_rata, 0)
           AS soucet_vcetne_podilu_podle_kapitalu
FROM investra_allocation_scheme s
JOIN investra_fund f ON f.id = s.fund_id
LEFT JOIN investra_allocation_line l ON l.scheme_id = s.id
GROUP BY f.name, s.valid_from, s.method, s.residual_pro_rata
ORDER BY f.name, s.valid_from DESC;
