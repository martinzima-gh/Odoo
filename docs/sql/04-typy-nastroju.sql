-- Typy nástrojů a návrhy z číselníku (modul investra_instruments). Jen čtení.
-- Ověřeno na databázi investra_test se smyšlenými daty; v investra_dev tyto tabulky zatím nejsou.

-- 1. Číselník typů: co typ navrhuje
SELECT t.code AS kod, t.name AS typ, t."group" AS skupina, t.ifrs9_category AS ifrs9,
       t.valuation_method AS oceneni, r.code AS role_uctu, t.cnb_sheet AS list_cnb
FROM investra_instrument_type t
JOIN investra_account_role r ON r.id = t.role_id
ORDER BY t."group", t.code;

-- 2. Nástroje, které se liší od návrhu svého typu
SELECT i.name AS nastroj, t.code AS typ, i.ifrs9_category, t.ifrs9_category AS navrh_ifrs9,
       ri.code AS role_uctu, rt.code AS navrh_role, i.valuation_method, t.valuation_method AS navrh_oceneni
FROM investra_instrument i
JOIN investra_instrument_type t ON t.id = i.type_id
JOIN investra_account_role ri ON ri.id = i.role_id
JOIN investra_account_role rt ON rt.id = t.role_id
WHERE i.ifrs9_category <> t.ifrs9_category OR i.role_id <> t.role_id OR i.valuation_method <> t.valuation_method
ORDER BY i.name;

-- 3. Metoda úročení fondů
SELECT f.name AS fond, f.accrual_method AS urocani, f.accrual_note AS zduvodneni
FROM investra_fund f
ORDER BY f.name;

-- 4. Historie změn nástrojů: Odoo 20 ukládá změnu přímo v textu zprávy
SELECT m.date AS kdy, p.name AS kdo, i.name AS nastroj, m.body AS zmena
FROM mail_message m
JOIN investra_instrument i ON i.id = m.res_id
LEFT JOIN res_partner p ON p.id = m.author_id
WHERE m.model = 'investra.instrument' AND m.message_type = 'tracking'
ORDER BY m.date DESC;
