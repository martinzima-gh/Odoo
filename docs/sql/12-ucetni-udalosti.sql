-- Účetní události: fond, zdroj, částka a měna (bod 15, rozhodnutí 2026-11-11). Jen čtení, spouštět po jednom.
-- Ověřeno na databázi investra_test se smyšlenými daty; v investra_dev modul investra_posting zatím není.
-- Název fondu je název společnosti; částka = součet MD dokladu ve funkční měně knihy.
SET default_transaction_read_only = on;

-- 1. Události se zdrojem a částkami
SELECT e.date AS datum, k.name AS kniha, fc.name AS fond, e.event_type AS druh, e.name AS nazev, e.state AS stav,
       e.res_model AS model_zdroje, e.res_id AS id_zdroje, e.amount AS castka, m.name AS mena,
       e.amount_currency AS castka_puvodni, fm.name AS puvodni_mena, mv.name AS doklad
FROM investra_accounting_event e
JOIN res_company k ON k.id = e.company_id
LEFT JOIN investra_fund f ON f.id = e.fund_id
LEFT JOIN res_company fc ON fc.id = f.company_id
LEFT JOIN res_currency m ON m.id = e.currency_id
LEFT JOIN res_currency fm ON fm.id = e.foreign_currency_id
LEFT JOIN account_move mv ON mv.id = e.move_id
ORDER BY e.date DESC, e.id DESC;

-- 2. Souhrn podle druhu a stavu
SELECT e.event_type AS druh, e.state AS stav, count(*) AS pocet, count(e.fund_id) AS s_fondem,
       count(e.res_model) AS se_zdrojem, sum(e.amount) AS castka
FROM investra_accounting_event e
GROUP BY 1, 2
ORDER BY 1, 2;

-- 3. Kontrola: částka události proti součtu MD dokladu (očekávaný výsledek: žádný řádek)
SELECT e.id, e.name, e.amount, s.debit
FROM investra_accounting_event e
JOIN (SELECT move_id, sum(debit) AS debit FROM account_move_line GROUP BY move_id) s ON s.move_id = e.move_id
WHERE e.amount IS DISTINCT FROM s.debit;
