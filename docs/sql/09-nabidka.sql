-- Ukázkový dotaz nad Odoo: jen čtení.
-- Strom nabídek Investry (a přecenění v Účetnictví): XML id, název, nadřazená nabídka, pořadí.
-- Název nabídky je JSON podle jazyka; vlastní moduly ho ukládají pod klíčem en_US.
SET default_transaction_read_only = on;

SELECT d.module || '.' || d.name           AS xml_id,
       m.name ->> 'en_US'                  AS nabidka,
       p.name ->> 'en_US'                  AS nadrazena,
       m.sequence                          AS poradi,
       a.name ->> 'en_US'                  AS akce
FROM ir_ui_menu m
JOIN ir_model_data d ON d.model = 'ir.ui.menu' AND d.res_id = m.id
LEFT JOIN ir_ui_menu p ON p.id = m.parent_id
LEFT JOIN ir_act_window a
       ON m.action LIKE 'ir.actions.act_window,%'
      AND a.id = split_part(m.action, ',', 2)::int
WHERE d.module LIKE 'investra%'
ORDER BY p.name ->> 'en_US' NULLS FIRST, m.sequence;
