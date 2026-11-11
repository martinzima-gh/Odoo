-- Ceny nástrojů: sdílené tržní ceny a ceny fondu (rozhodnutí 2026-11-11). Jen čtení, spouštět po jednom.
-- Název nástroje je obyčejný text, název fondu je název společnosti (JSON není).
SET default_transaction_read_only = on;

-- 1. Ceny s rozsahem, měnou, knihou a stavem
SELECT p.date AS datum, i.name AS nastroj, p.scope AS rozsah, c.name AS kniha,
       p.price AS cena, cur.name AS mena, p.source AS zdroj, p.deviation_reason AS duvod_odchylky, p.state AS stav
FROM investra_instrument_price p
JOIN investra_instrument i ON i.id = p.instrument_id
JOIN res_company c ON c.id = p.company_id
JOIN res_currency cur ON cur.id = p.currency_id
ORDER BY p.date DESC, i.name, p.scope DESC
LIMIT 100;

-- 2. Kontrola: měna ceny se liší od měny nástroje (má být prázdné)
SELECT p.id, i.name AS nastroj, p.currency_id, i.currency_id
FROM investra_instrument_price p
JOIN investra_instrument i ON i.id = p.instrument_id
WHERE p.currency_id <> i.currency_id;

-- 3. Ceny fondu ke dni, ke kterému existuje sdílená cena (odchylky a jejich důvod)
SELECT f.date AS datum, i.name AS nastroj, c.name AS fond, f.price AS cena_fondu, s.price AS sdilena_cena, f.deviation_reason
FROM investra_instrument_price f
JOIN investra_instrument_price s ON s.instrument_id = f.instrument_id AND s.date = f.date AND s.fund_id IS NULL
JOIN investra_instrument i ON i.id = f.instrument_id
JOIN res_company c ON c.id = f.company_id
WHERE f.fund_id IS NOT NULL;

-- 4. Kde byla cena použita: řádky portfolia ocenění s odkazem na cenu a stářím ceny
SELECT v.date AS datum_oceneni, c.name AS fond, l.name AS nastroj, l.price AS cena, l.price_date AS datum_ceny,
       v.date - l.price_date AS stari_dni, p.scope AS rozsah, v.state AS stav_oceneni
FROM investra_valuation_portfolio l
JOIN investra_valuation v ON v.id = l.valuation_id
JOIN res_company c ON c.id = v.company_id
LEFT JOIN investra_instrument_price p ON p.id = l.price_id
WHERE l.instrument_id IS NOT NULL
ORDER BY v.date DESC, c.name, l.name
LIMIT 100;
