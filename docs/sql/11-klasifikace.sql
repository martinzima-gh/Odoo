-- Klasifikace IFRS 9 podle obchodního modelu fondu (rozhodnutí 2026-11-11). Jen čtení, spouštět po jednom.
-- Ověřeno na databázi investra_test se smyšlenými daty; v investra_dev tyto tabulky zatím nejsou.
-- Název fondu je název společnosti; název nástroje je obyčejný text.
SET default_transaction_read_only = on;

-- 1. Obchodní modely (portfolia) fondů
SELECT c.name AS fond, p.name AS portfolio, p.business_model AS obchodni_model, p.active AS aktivni
FROM investra_fund_portfolio p
JOIN investra_fund f ON f.id = p.fund_id
JOIN res_company c ON c.id = f.company_id
ORDER BY c.name, p.sequence, p.id;

-- 2. Zařazení nástrojů: (a) povaha, (b) SPPI, (c) model, (d) povinná klasifikace, (e) určení, (f) kategorie a ocenění
SELECT c.name AS fond, p.name AS portfolio, p.business_model AS model, i.name AS nastroj, z.valid_from AS plati_od,
       z.valid_to AS plati_do, z.instrument_nature AS povaha, z.sppi, z.sppi_version AS zneni_sppi,
       z.mandatory_category AS povinna, z.designation AS urceni, z.ifrs9_category AS kategorie,
       z.valuation_method AS oceneni, r.code AS role_uctu
FROM investra_portfolio_classification z
JOIN investra_fund_portfolio p ON p.id = z.portfolio_id
JOIN investra_fund f ON f.id = p.fund_id
JOIN res_company c ON c.id = f.company_id
JOIN investra_instrument i ON i.id = z.instrument_id
JOIN investra_account_role r ON r.id = z.role_id
ORDER BY c.name, p.name, i.name, z.valid_from;

-- 3. Pozice po obchodních modelech k datu (kusy z obchodů podle data sjednání)
SELECT c.name AS fond, p.name AS portfolio, i.name AS nastroj, sum(t.quantity) AS kusy
FROM investra_trade t
JOIN investra_fund_portfolio p ON p.id = t.portfolio_id
JOIN investra_fund f ON f.id = t.fund_id
JOIN res_company c ON c.id = f.company_id
JOIN investra_instrument i ON i.id = t.instrument_id
WHERE t.trade_date <= DATE '2027-12-31'
GROUP BY c.name, p.name, i.name
HAVING sum(t.quantity) <> 0
ORDER BY c.name, p.name, i.name;

-- 4. Zůstatek zaúčtovaných řádků po nástroji a kategorii zařazení (vazba na výkazy ČNB)
SELECT c.name AS fond, i.name AS nastroj, z.ifrs9_category AS kategorie, a.code_store ->> l.company_id::text AS ucet,
       round(sum(l.balance)::numeric, 2) AS zustatek
FROM account_move_line l
JOIN investra_portfolio_classification z ON z.id = l.investra_classification_id
JOIN investra_instrument i ON i.id = l.investra_instrument_id
JOIN res_company c ON c.id = l.company_id
JOIN account_account a ON a.id = l.account_id
WHERE l.parent_state = 'posted'
GROUP BY c.name, i.name, z.ifrs9_category, a.code_store ->> l.company_id::text
ORDER BY c.name, i.name, 4;

-- 5. Kontrola: zaúčtovaný řádek s nástrojem bez zařazení (má být prázdné)
SELECT l.id, l.date AS datum, i.name AS nastroj, l.balance AS castka
FROM account_move_line l
JOIN investra_instrument i ON i.id = l.investra_instrument_id
WHERE l.parent_state = 'posted' AND l.investra_classification_id IS NULL;

-- 6. Kontrola: obchod, k jehož datu sjednání chybí zařazení (má být prázdné u zaúčtovaných)
SELECT t.id, t.trade_date AS sjednano, i.name AS nastroj, p.name AS portfolio, t.state AS stav
FROM investra_trade t
JOIN investra_instrument i ON i.id = t.instrument_id
JOIN investra_fund_portfolio p ON p.id = t.portfolio_id
WHERE NOT EXISTS (
    SELECT 1 FROM investra_portfolio_classification z
    WHERE z.portfolio_id = t.portfolio_id AND z.instrument_id = t.instrument_id
      AND z.valid_from <= t.trade_date AND (z.valid_to IS NULL OR z.valid_to >= t.trade_date)
);

-- 7. Zdůvodnění klasifikace (audit): kroky (a)–(f) s odkazy na odstavce a poznámkami účetní
SELECT i.name AS nastroj, p.name AS portfolio, z.classification_basis AS zduvodneni
FROM investra_portfolio_classification z
JOIN investra_fund_portfolio p ON p.id = z.portfolio_id
JOIN investra_instrument i ON i.id = z.instrument_id
ORDER BY i.name, p.name;

-- 8. Kontrola: role zařazení se liší od role typu nástroje (má být prázdné; výjimkou je účast v RH,
--    kde návrh dává roli participation_fv místo participation)
SELECT c.name AS fond, i.name AS nastroj, t.name AS typ, rt.code AS role_typu, rz.code AS role_zarazeni, z.valid_from AS plati_od
FROM investra_portfolio_classification z
JOIN investra_instrument i ON i.id = z.instrument_id
JOIN investra_instrument_type t ON t.id = i.type_id
JOIN investra_account_role rt ON rt.id = t.role_id
JOIN investra_account_role rz ON rz.id = z.role_id
JOIN res_company c ON c.id = z.company_id
WHERE z.role_id <> t.role_id
ORDER BY c.name, i.name;
