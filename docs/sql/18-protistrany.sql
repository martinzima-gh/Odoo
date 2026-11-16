-- Protistrany: sektory ESA 2010, údaje protistran (jeden záznam na kontakt, MN-09) a vazby na nástroje.
-- Jen čtení, spouštět po jednom. Ověřeno na databázi investra (16. 11. 2026, po MN-09).

-- 1. Číselník sektorů ESA 2010
SELECT code AS kod, name AS nazev
FROM investra_esa_sector
ORDER BY code;

-- 2. Údaje protistran: partner, země, sektor ESA a LEI (změny jsou v historii záznamu, mail_tracking_value)
SELECT p.name AS protistrana, c.name AS zeme, s.code AS sektor_esa,
       s.name AS nazev_sektoru, cp.lei, cp.write_date AS zmeneno
FROM investra_counterparty_profile cp
JOIN res_partner p ON p.id = cp.partner_id
JOIN res_country c ON c.id = cp.country_id
JOIN investra_esa_sector s ON s.id = cp.sector_id
ORDER BY p.name
LIMIT 100;

-- 3. Protistrana a emitent přiřazení k investičnímu nástroji
SELECT i.name AS nastroj, t.name AS typ_nastroje,
       cp.name AS protistrana, issuer.name AS emitent
FROM investra_instrument i
JOIN investra_instrument_type t ON t.id = i.type_id
LEFT JOIN res_partner cp ON cp.id = i.counterparty_id
LEFT JOIN res_partner issuer ON issuer.id = i.issuer_id
WHERE i.counterparty_id IS NOT NULL OR i.issuer_id IS NOT NULL
ORDER BY i.name
LIMIT 100;

-- 4. Klasifikace portfolia a sektor protistrany (jediný záznam údajů, bez data)
SELECT f.name AS fond, p.name AS portfolio, i.name AS nastroj,
       pc.valid_from AS klasifikace_od, cp.name AS protistrana,
       s.code AS sektor_esa, r.code AS role_uctu
FROM investra_portfolio_classification pc
JOIN investra_fund_portfolio p ON p.id = pc.portfolio_id
JOIN investra_fund f ON f.id = pc.fund_id
JOIN investra_instrument i ON i.id = pc.instrument_id
LEFT JOIN res_partner cp ON cp.id = i.counterparty_id
LEFT JOIN investra_counterparty_profile profile ON profile.partner_id = i.counterparty_id
LEFT JOIN investra_esa_sector s ON s.id = profile.sector_id
LEFT JOIN investra_account_role r ON r.id = pc.role_id
ORDER BY f.name, p.name, i.name, pc.valid_from DESC
LIMIT 100;
