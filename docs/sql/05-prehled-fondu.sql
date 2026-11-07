-- Přehled fondů (modul investra_dashboard). Jen čtení.
-- Ověřeno na databázi investra_test se smyšlenými daty; v investra_dev tyto tabulky zatím nejsou.

-- 1. Poslední ocenění každého fondu mimo stornovaná
SELECT DISTINCT ON (f.id) f.name AS fond, v.date AS datum, v.version AS verze, v.state AS stav, v.fund_capital AS fk
FROM investra_fund f
LEFT JOIN investra_valuation v ON v.fund_id = f.id AND v.state <> 'reversed'
ORDER BY f.id, v.date DESC, v.version DESC;

-- 2. Plánovaná ocenění bez zveřejnění
SELECT f.name AS fond, c.date AS datum, c.published_on AS planovane_zverejneni
FROM investra_valuation_calendar c
JOIN investra_fund f ON f.id = c.fund_id
WHERE NOT EXISTS (
    SELECT 1 FROM investra_valuation v
    WHERE v.fund_id = c.fund_id AND v.date = c.date AND v.state = 'published'
)
ORDER BY c.date;

-- 3. Otevřené termíny ČNB
SELECT f.name AS fond, d.report AS vykaz, d.period_end AS obdobi_do, d.due_date AS termin
FROM investra_regulatory_deadline d
JOIN investra_fund f ON f.id = d.fund_id
WHERE d.state = 'open'
ORDER BY d.due_date;

-- 4. Nevypořádané obchody
SELECT f.name AS fond, i.name AS nastroj, t.trade_date AS sjednano, t.settlement_date AS vyporadani, t.quantity AS kusy
FROM investra_trade t
JOIN investra_fund f ON f.id = t.fund_id
JOIN investra_instrument i ON i.id = t.instrument_id
WHERE t.state = 'unsettled'
ORDER BY t.settlement_date;
