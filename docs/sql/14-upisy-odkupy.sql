-- Úpisy a odkupy, body A–E (rozhodnutí 2026-11-11). Jen čtení, spouštět po jednom.
-- Ověřeno na databázi investra_test se smyšlenými daty; v investra_dev modul NAV zatím není.
SET default_transaction_read_only = on;

-- 1. Pohyby: zdroj, stav, kusy, cena, hrubá částka, poplatek, rozdíl a změna kapitálu třídy
SELECT rc.name AS fond, c.code AS trida, m.date AS datum, m.movement_type AS typ, m.state AS stav,
       m.source AS zdroj, m.external_ref AS identifikator_is, m.units AS kusy, m.price AS cena,
       COALESCE(NULLIF(m.amount_class, 0), m.amount) AS hruba_castka, m.fee_amount_class AS poplatek,
       m.fee_recipient AS prijemce_poplatku, m.rounding_amount_class AS rozdil, m.rounding_owner AS rozdil_patri,
       m.capital_amount AS zmena_kapitalu, m.replaced_id AS opravuje_pohyb
FROM investra_class_movement m
JOIN investra_fund_class c ON c.id = m.class_id
JOIN res_company rc ON rc.id = m.company_id
ORDER BY rc.name, m.date, m.id;

-- 2. Řádky dokladů pohybů podle rolí účtů (u pohybu bez poplatku jen banka a kapitál třídy)
SELECT m.id AS pohyb, m.movement_type AS typ, r.code AS role, a.code_store->>(m.company_id::text) AS ucet,
       l.balance AS castka, l.investra_movement_type AS typ_pohybu
FROM investra_class_movement m
JOIN investra_accounting_event e ON e.id = m.event_id
JOIN account_move_line l ON l.move_id = e.move_id
JOIN account_account a ON a.id = l.account_id
LEFT JOIN investra_role_account ra ON ra.account_id = l.account_id AND ra.company_id = m.company_id
LEFT JOIN investra_account_role r ON r.id = ra.role_id
ORDER BY m.id, l.id;

-- 3. Parametry tříd pro úpisy a odkupy (převzaté z fondu, třída je smí přepsat)
SELECT rc.name AS fond, c.code AS trida, c.unit_digits AS mista_kusu, c.unit_rounding AS zaokrouhleni_kusu,
       c.rounding_owner AS rozdil_patri, c.entry_fee_rate AS vstupni_pct, c.exit_fee_rate AS vystupni_pct,
       c.fee_recipient AS prijemce_poplatku
FROM investra_fund_class c
JOIN investra_fund f ON f.id = c.fund_id
JOIN res_company rc ON rc.id = f.company_id
ORDER BY rc.name, c.sequence, c.code;

-- 4. Kontrola: každá kniha fondu má nové role účtů (výsledek má být prázdný)
SELECT rc.name AS kniha, r.code AS chybejici_role
FROM res_company rc
CROSS JOIN investra_account_role r
WHERE rc.chart_template = 'investra_fund'
  AND r.code IN ('subscription_fee_payable', 'investor_rounding_payable', 'rounding_gain', 'rounding_loss')
  AND NOT EXISTS (SELECT 1 FROM investra_role_account ra WHERE ra.company_id = rc.id AND ra.role_id = r.id);
