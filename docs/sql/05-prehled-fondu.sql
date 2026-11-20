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
SELECT f.name AS fond, i.name AS nastroj, t.trade_date AS sjednano, t.settlement_date AS vyporadani,
       t.side AS smer, t.quantity AS kusy, t.price AS cena, t.fee_amount AS poplatek,
       fc.name AS mena_poplatku, t.fee_fx_rate AS kurz_poplatku,
       t.derecognition_price AS cena_vyskladneni,
       t.derecognition_manual AS upraveno_rucne, t.derecognition_reason AS duvod_upravy
FROM investra_trade t
JOIN investra_fund f ON f.id = t.fund_id
JOIN investra_instrument i ON i.id = t.instrument_id
LEFT JOIN res_currency fc ON fc.id = t.fee_currency_id
WHERE t.state = 'unsettled'
ORDER BY t.settlement_date;

-- 5. Dividendy: nárok k ex-datu, srážka, zápočet, přeplatek a výplata
SELECT f.name AS fond, i.name AS nastroj, p.name AS portfolio, d.ex_date AS ex_datum,
       d.pay_date AS datum_vyplaty, d.kind AS druh, d.units AS kusy_s_narokem,
       d.per_share AS dividenda_na_kus, d.gross_amount AS hruba_dividenda,
       d.withholding_rate AS srazena_sazba, d.withheld_amount AS srazena_dan,
       d.treaty_rate AS smluvni_sazba, d.creditable_amount AS zapocitatelna_dan,
       d.withheld_amount - d.creditable_amount AS preplatek, d.excess_treatment AS postup_preplatku,
       cur.name AS mena, d.fx_rate AS kurz_k_ex_datu,
       d.pay_fx_rate AS kurz_k_vyplate, d.state AS stav
FROM investra_dividend d
JOIN investra_fund f ON f.id = d.fund_id
JOIN investra_instrument i ON i.id = d.instrument_id
JOIN investra_fund_portfolio p ON p.id = d.portfolio_id
JOIN res_currency cur ON cur.id = d.currency_id
ORDER BY d.ex_date DESC, d.id DESC;
