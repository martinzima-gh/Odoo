-- Ukázkové dotazy nad Odoo: jen čtení, spouštět po jednom.
-- V Odoo je název účtu a kód uložený jako JSON, proto ->> a klíč (cs_CZ, id společnosti).
SET default_transaction_read_only = on;

-- 1. Společnosti a jejich měna
SELECT c.id, c.name, cur.name AS mena, c.chart_template
FROM res_company c
JOIN res_currency cur ON cur.id = c.currency_id;

-- 2. Účtová osnova: kód, název a typ účtu
SELECT a.code_store ->> '1' AS ucet,
       COALESCE(a.name ->> 'cs_CZ', a.name ->> 'en_US') AS nazev,
       a.account_type AS typ,
       a.reconcile AS paruje_se
FROM account_account a
ORDER BY ucet
LIMIT 50;

-- 3. Počet účtů podle účtové třídy
SELECT left(a.code_store ->> '1', 1) AS trida, count(*) AS pocet
FROM account_account a
GROUP BY 1
ORDER BY 1;

-- 4. Deníky a výchozí účet
SELECT j.code AS denik, j.type AS typ, a.code_store ->> '1' AS vychozi_ucet
FROM account_journal j
LEFT JOIN account_account a ON a.id = j.default_account_id
ORDER BY j.type, j.code;

-- 5. Účetní doklady podle stavu (draft = návrh, posted = zaúčtováno)
SELECT state AS stav, move_type AS druh, count(*) AS pocet
FROM account_move
GROUP BY 1, 2
ORDER BY 1, 2;

-- 6. Řádky dokladů: účet, MD a Dal
SELECT m.name AS doklad, m.date AS datum, m.state AS stav,
       a.code_store ->> '1' AS ucet,
       l.debit AS md, l.credit AS dal
FROM account_move_line l
JOIN account_move m ON m.id = l.move_id
JOIN account_account a ON a.id = l.account_id
ORDER BY m.date DESC, m.id, l.id
LIMIT 50;

-- 7. Předvaha: jen zaúčtované doklady
SELECT a.code_store ->> '1' AS ucet,
       COALESCE(a.name ->> 'cs_CZ', a.name ->> 'en_US') AS nazev,
       sum(l.debit) AS md, sum(l.credit) AS dal, sum(l.balance) AS zustatek
FROM account_move_line l
JOIN account_account a ON a.id = l.account_id
WHERE l.parent_state = 'posted'
GROUP BY 1, 2
ORDER BY 1;

-- 8. Daně a sazby
SELECT type_tax_use AS pouziti,
       COALESCE(name ->> 'cs_CZ', name ->> 'en_US') AS dan,
       amount AS sazba
FROM account_tax
ORDER BY 1, 3 DESC;

-- 9. Kontrola: účty 451 až 461 mají dnes typ vlastní kapitál
SELECT a.code_store ->> '1' AS ucet, a.account_type AS typ
FROM account_account a
WHERE a.code_store ->> '1' BETWEEN '451000' AND '461999'
ORDER BY 1;
