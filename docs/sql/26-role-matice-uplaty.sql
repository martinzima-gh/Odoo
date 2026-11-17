-- Role a činnosti, uživatelé, řádky matice, ručně doložené úplaty v ocenění (ZJ-01 až ZJ-03).
-- Jen čtení, spouštět po jednom. Ověřeno na dočasné databázi ze skriptu tools/demo_data/run_seed.sh (smyšlená data).
SET default_transaction_read_only = on;

-- 1. Role: úroveň přístupu, příznak ručního účtování, počet činností a uživatelů
SELECT r.name AS role, r.access_level AS uroven, r.manual_posting AS rucni_uctovani, r.active AS aktivni,
       (SELECT count(*) FROM investra_role_line l WHERE l.role_id = r.id) AS cinnosti,
       (SELECT count(*) FROM investra_role_user_rel u WHERE u.role_id = r.id) AS uzivatele
FROM investra_role r
ORDER BY r.name;

-- 2. Činnosti rolí: co role smí provádět a co schvalovat
SELECT r.name AS role, l.activity AS cinnost, l.perform AS provadi, l.approve AS schvaluje
FROM investra_role_line l
JOIN investra_role r ON r.id = l.role_id
ORDER BY r.name, l.activity;

-- 3. Uživatelé a jejich role
SELECT p.name AS uzivatel, u.login, r.name AS role, u.active AS aktivni
FROM investra_role_user_rel rel
JOIN investra_role r ON r.id = rel.role_id
JOIN res_users u ON u.id = rel.user_id
JOIN res_partner p ON p.id = u.partner_id
ORDER BY u.login, r.name;

-- 4. Řádky schvalovací matice (bez fondů a jmenovitých uživatelů): činnost, platnost, druhá osoba
SELECT m.activity AS cinnost, m.valid_from AS plati_od, m.second_person AS druha_osoba,
       m.builtin AS vychozi_radek, m.note AS poznamka
FROM investra_approval_matrix m
ORDER BY m.activity, m.valid_from DESC;

-- 5. Ručně doložené úplaty v oceněních (bez pravidla úplaty): fond, datum, částka, popis
SELECT c.name AS fond, v.date AS datum_oceneni, v.version AS verze, v.state AS stav, f.detail AS popis, f.amount AS castka
FROM investra_valuation_fee f
JOIN investra_valuation v ON v.id = f.valuation_id
JOIN res_company c ON c.id = f.company_id
WHERE f.rule_id IS NULL
ORDER BY c.name, v.date DESC, v.version DESC, f.id;
