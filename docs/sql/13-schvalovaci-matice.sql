-- Schvalovací matice obhospodařovatele (rozhodnutí 2026-11-11). Jen čtení, spouštět po jednom.
-- Ověřeno na databázi investra_test se smyšlenými daty; v investra_dev tyto tabulky zatím nejsou.
SET default_transaction_read_only = on;

-- 1. Řádky matice: činnost, komu patří (výchozí / obhospodařovatel / zpřísnění fondu), platnost a počet osob
SELECT m.activity AS cinnost,
       COALESCE(fc.name, mc.name, 'výchozí') AS plati_pro,
       CASE WHEN m.fund_id IS NOT NULL THEN 'zpřísnění fondu' WHEN m.manager_id IS NOT NULL THEN 'obhospodařovatel' ELSE 'výchozí' END AS uroven,
       m.valid_from AS plati_od, m.performer_role AS provadi, m.second_person AS druha_osoba,
       1 + (SELECT count(*) FROM investra_approval_matrix_step s WHERE s.matrix_id = m.id) AS pocet_osob,
       m.builtin AS vychozi_radek, m.note AS poznamka
FROM investra_approval_matrix m
LEFT JOIN investra_entity me ON me.id = m.manager_id
LEFT JOIN res_company mc ON mc.id = me.company_id
LEFT JOIN investra_fund f ON f.id = m.fund_id
LEFT JOIN res_company fc ON fc.id = f.company_id
ORDER BY m.activity, uroven, m.valid_from DESC;

-- 2. Schvalovatelé v řádcích matice (kroky)
SELECT m.activity AS cinnost, m.valid_from AS plati_od, s.sequence AS poradi, s.name AS krok, s.role AS nejnizsi_role
FROM investra_approval_matrix_step s
JOIN investra_approval_matrix m ON m.id = s.matrix_id
ORDER BY m.activity, m.valid_from DESC, s.sequence;

-- 3. Úkony bez druhé osoby (nejnovější nahoře); výchozí řádek = chování před maticí, kontrola ocenění ho neukazuje
SELECT l.create_date AS kdy, l.activity AS cinnost, l.record_name AS zaznam, p.name AS provedl,
       c.name AS kniha, m.builtin AS podle_vychoziho_radku
FROM investra_approval_log l
JOIN res_users u ON u.id = l.user_id
JOIN res_partner p ON p.id = u.partner_id
LEFT JOIN res_company c ON c.id = l.company_id
LEFT JOIN investra_approval_matrix m ON m.id = l.matrix_id
ORDER BY l.id DESC
LIMIT 100;

-- 4. Žádosti ke schválení (čtyři oči u jednorázových úkonů) a stav potvrzení
SELECT r.id, r.create_date AS pozadano, r.activity AS cinnost, r.record_name AS zaznam, r.state AS stav,
       (SELECT count(*) FROM investra_approval_request_line l WHERE l.request_id = r.id AND l.user_id IS NOT NULL) AS potvrzeno,
       (SELECT count(*) FROM investra_approval_request_line l WHERE l.request_id = r.id) AS potreba
FROM investra_approval_request r
ORDER BY r.id DESC;

-- 5. Fondy a jejich obhospodařovatel (prázdný = výchozí matice)
SELECT fc.name AS fond, mc.name AS obhospodarovatel
FROM investra_fund f
JOIN res_company fc ON fc.id = f.company_id
LEFT JOIN investra_entity me ON me.id = f.manager_id
LEFT JOIN res_company mc ON mc.id = me.company_id
ORDER BY fc.name;
