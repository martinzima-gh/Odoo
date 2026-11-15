-- Evidence nástrojů, emitentů a portfolií (addon investra_instrument_master). Jen čtení, spouštět po jednom.
-- Ověřeno na dočasné databázi s nainstalovaným addonem (číselníky ze seedu, bez obchodních dat);
-- investra_test a investra_dev addon zatím nemají, dotazy tam spadnou na chybějící tabulky a sloupce.
-- Názvy emitentů jsou názvy partnerů, názvy fondů názvy společností.
SET default_transaction_read_only = on;

-- 1. Emitenti (aktuální verze údajů) s kódem ESA, typem emitenta, rezidentstvím a regionem
SELECT p.name AS emitent, v.valid_from AS plati_od, co.code AS zeme, e.code AS esa_kod, e.name AS esa_nazev,
       a.name AS typ_emitenta, v.resident_status AS rezidentstvi, v.eu_status AS region,
       v.review_state AS stav_kontroly, v.source AS zdroj
FROM investra_counterparty_profile v
JOIN res_partner p ON p.id = v.partner_id
JOIN res_country co ON co.id = v.country_id
LEFT JOIN investra_esa_code e ON e.id = v.esa_code_id
LEFT JOIN investra_esa_aggregate_sector a ON a.id = v.issuer_type_id
WHERE v.is_latest
ORDER BY p.name;

-- 2. Emitenti bez kódu ESA (starší profily; kód se doplní novou verzí s důvodem změny)
SELECT p.name AS emitent, v.valid_from AS plati_od, co.code AS zeme
FROM investra_counterparty_profile v
JOIN res_partner p ON p.id = v.partner_id
JOIN res_country co ON co.id = v.country_id
WHERE v.is_latest AND v.esa_code_id IS NULL
ORDER BY p.name;

-- 3. Nástroje bez druhu cenného papíru BA0088 (jen typy, u kterých je druh povinný)
SELECT c.name AS kniha, i.name AS nastroj, i.isin, t.name AS typ, i.review_state AS stav_potvrzeni
FROM investra_instrument i
JOIN investra_instrument_type t ON t.id = i.type_id
LEFT JOIN res_company c ON c.id = i.company_id
WHERE i.ba0088_id IS NULL AND t.ba0088_required
ORDER BY c.name, i.name;

-- 4. Nástroje s druhem BA0088, CFI a stavem potvrzení (nepotvrzené první)
SELECT i.name AS nastroj, i.isin, b.code AS ba0088, b.name AS druh, i.cfi_code AS cfi, i.leverage_flag AS paka,
       i.maturity_date AS splatnost, e.name AS emitent, i.review_state AS stav_potvrzeni
FROM investra_instrument i
JOIN investra_ba0088_code b ON b.id = i.ba0088_id
LEFT JOIN res_partner e ON e.id = i.issuer_id
ORDER BY (i.review_state = 'reviewed'), i.name;

-- 5. Portfolia s kategorií ocenění, obchodním modelem, důvodem a stavem schválení
SELECT c.name AS fond, p.code AS kod, p.name AS portfolio, m.code AS kategorie, p.business_model AS obchodni_model,
       r.code AS duvod, p.state AS stav, p.valid_from AS plati_od, p.valid_to AS plati_do,
       p.approved_on AS schvaleno, p.next_review_date AS pristi_revize
FROM investra_fund_portfolio p
JOIN investra_fund f ON f.id = p.fund_id
JOIN res_company c ON c.id = f.company_id
LEFT JOIN investra_measurement_category m ON m.id = p.measurement_category_id
LEFT JOIN investra_classification_reason r ON r.id = p.classification_reason_id
ORDER BY c.name, p.sequence, p.id;

-- 6. Portfolia bez kategorie nebo neschválená (než se do nich budou zařazovat nástroje)
SELECT c.name AS fond, p.name AS portfolio, p.state AS stav,
       (p.measurement_category_id IS NULL) AS chybi_kategorie, (p.classification_reason_id IS NULL) AS chybi_duvod
FROM investra_fund_portfolio p
JOIN investra_fund f ON f.id = p.fund_id
JOIN res_company c ON c.id = f.company_id
WHERE p.state <> 'approved' OR p.measurement_category_id IS NULL
ORDER BY c.name, p.name;

-- 7. Zařazení nástrojů bez účetního profilu k dnešku (stejná logika jako výběr profilu: pravidlo společnosti,
--    portfolio shodné nebo prázdné, druh BA0088 shodný, shodná skupina, nebo obojí prázdné)
SELECT c.name AS fond, p.name AS portfolio, i.name AS nastroj, b.code AS ba0088, z.valid_from AS plati_od
FROM investra_portfolio_classification z
JOIN investra_fund_portfolio p ON p.id = z.portfolio_id
JOIN investra_fund f ON f.id = p.fund_id
JOIN res_company c ON c.id = f.company_id
JOIN investra_instrument i ON i.id = z.instrument_id
LEFT JOIN investra_ba0088_code b ON b.id = i.ba0088_id
WHERE z.valid_from <= CURRENT_DATE AND (z.valid_to IS NULL OR z.valid_to >= CURRENT_DATE)
  AND NOT EXISTS (
    SELECT 1 FROM investra_accounting_profile_assignment a
    WHERE a.company_id = f.company_id
      AND a.valid_from <= CURRENT_DATE AND (a.valid_to IS NULL OR a.valid_to >= CURRENT_DATE)
      AND (a.portfolio_id IS NULL OR a.portfolio_id = p.id)
      AND ((a.ba0088_id IS NULL AND a.ba0088_group_id IS NULL)
           OR a.ba0088_id = i.ba0088_id
           OR a.ba0088_group_id = b.group_id))
ORDER BY c.name, p.name, i.name;

-- 8. Pravidla přiřazení účetních profilů (pořadí výběru: priorita, pak konkrétnost)
SELECT c.name AS spolecnost, p.name AS portfolio, b.code AS ba0088, g.name AS skupina_ba0088,
       ap.code AS ucetni_profil, a.priority AS priorita, a.valid_from AS plati_od, a.valid_to AS plati_do
FROM investra_accounting_profile_assignment a
JOIN res_company c ON c.id = a.company_id
JOIN investra_accounting_profile ap ON ap.id = a.accounting_profile_id
LEFT JOIN investra_fund_portfolio p ON p.id = a.portfolio_id
LEFT JOIN investra_ba0088_code b ON b.id = a.ba0088_id
LEFT JOIN investra_ba0088_group g ON g.id = a.ba0088_group_id
ORDER BY c.name, a.priority, a.valid_from;

-- 9. Číselníky: počty záznamů a ručně změněné záznamy (kontrola po importu nové metodiky)
SELECT 'BA0088' AS ciselnik, count(*) AS zaznamu, count(*) FILTER (WHERE locally_modified) AS rucne_zmeneno FROM investra_ba0088_code
UNION ALL SELECT 'ESA', count(*), count(*) FILTER (WHERE locally_modified) FROM investra_esa_code
UNION ALL SELECT 'Kategorie ocenění', count(*), count(*) FILTER (WHERE locally_modified) FROM investra_measurement_category
UNION ALL SELECT 'Důvody klasifikace', count(*), count(*) FILTER (WHERE locally_modified) FROM investra_classification_reason;
