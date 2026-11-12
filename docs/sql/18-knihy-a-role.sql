-- Účetní knihy, role účtů a bankovní deníky.
-- Jen čtení, spouštět po jednom. Ověřeno na databázi investra_test.
-- Bez modelu record_guard.

-- 1. Knihy, společnost, funkční měna a případná nadřazená kniha
SELECT e.name AS kniha, c.id AS company_id, e.entity_type AS druh,
       e.framework AS ramec, e.rate_source AS zdroj_kurzu,
       cur.name AS funkcni_mena, parent.name AS nadrizena_kniha
FROM investra_entity e
JOIN res_company c ON c.id = e.company_id
JOIN res_currency cur ON cur.id = c.currency_id
LEFT JOIN investra_entity parent ON parent.id = e.parent_id
ORDER BY e.name;

-- 2. Role účtů a hlavní přiřazený účet v knize
SELECT c.name AS kniha, r.code AS role, r.name AS nazev_role,
       a.code_store ->> ra.company_id::text AS hlavni_ucet,
       COALESCE(a.name ->> 'cs_CZ', a.name ->> 'en_US') AS nazev_uctu
FROM investra_role_account ra
JOIN investra_account_role r ON r.id = ra.role_id
JOIN res_company c ON c.id = ra.company_id
JOIN account_account a ON a.id = ra.account_id
ORDER BY c.name, r.code;

-- 3. Další účty přiřazené k roli (vedle hlavního účtu)
SELECT c.name AS kniha, r.code AS role,
       a.code_store ->> ra.company_id::text AS dalsi_ucet,
       COALESCE(a.name ->> 'cs_CZ', a.name ->> 'en_US') AS nazev_uctu
FROM investra_role_account_extra_rel extra
JOIN investra_role_account ra ON ra.id = extra.mapping_id
JOIN investra_account_role r ON r.id = ra.role_id
JOIN res_company c ON c.id = ra.company_id
JOIN account_account a ON a.id = extra.account_id
ORDER BY c.name, r.code, dalsi_ucet;

-- 4. Bankovní deníky a informace, zda je jejich výchozí účet dalším účtem role bank
SELECT c.name AS kniha, j.code AS kod_deniku,
       COALESCE(j.name ->> 'cs_CZ', j.name ->> 'en_US') AS denik,
       a.code_store ->> j.company_id::text AS vychozi_ucet,
       EXISTS (
           SELECT 1
           FROM investra_role_account ra
           JOIN investra_account_role r ON r.id = ra.role_id
           JOIN investra_role_account_extra_rel extra ON extra.mapping_id = ra.id
           WHERE ra.company_id = j.company_id
             AND r.code = 'bank'
             AND extra.account_id = j.default_account_id
       ) AS ucet_je_dalsim_u_role_bank
FROM account_journal j
JOIN res_company c ON c.id = j.company_id
LEFT JOIN account_account a ON a.id = j.default_account_id
WHERE j.type = 'bank'
ORDER BY c.name, j.code;
