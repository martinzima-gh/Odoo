-- Realizované a nerealizované kurzové rozdíly po nástrojích a knihách.
-- Jen čtení, spouštět po jednom. Kniha: dosaďte id společnosti (ukázka: 244).
-- Kurzové účty zahrnují hlavní i další účty přiřazené k roli.

-- 1. Kurzové rozdíly po nástrojích a včetně řádků bez nástroje
-- Výnos má záporný balance, proto -SUM(balance) zobrazuje zisk jako kladný.
WITH role_accounts AS (
    SELECT ra.company_id, ra.role_id, ra.account_id
    FROM investra_role_account ra
    UNION
    SELECT ra.company_id, ra.role_id, extra.account_id
    FROM investra_role_account ra
    JOIN investra_role_account_extra_rel extra ON extra.mapping_id = ra.id
)
SELECT c.name AS kniha,
       COALESCE(i.name, '(bez nástroje)') AS nastroj,
       cur.name AS mena_nastroje,
       COALESCE(-SUM(l.balance) FILTER (
           WHERE l.investra_movement_type = 'fx_realised'
       ), 0) AS realizovany_kurzovy_rozdil,
       COALESCE(-SUM(l.balance) FILTER (
           WHERE l.investra_movement_type = 'fx_revaluation'
       ), 0) AS nerealizovany_kurzovy_rozdil,
       COALESCE(-SUM(l.balance), 0) AS kurzovy_rozdil_celkem
FROM account_move_line l
JOIN role_accounts ra
  ON ra.company_id = l.company_id
 AND ra.account_id = l.account_id
JOIN investra_account_role r ON r.id = ra.role_id
JOIN res_company c ON c.id = l.company_id
LEFT JOIN investra_instrument i ON i.id = l.investra_instrument_id
LEFT JOIN res_currency cur ON cur.id = i.currency_id
WHERE l.company_id = 244
  AND l.parent_state = 'posted'
  AND r.code IN ('gain_fx', 'loss_fx')
  AND l.investra_movement_type IN ('fx_realised', 'fx_revaluation')
GROUP BY c.name, i.id, i.name, cur.name
ORDER BY nastroj;

-- 2. Stejné částky po měsících podle data účetního řádku pro jednu knihu
-- Dosaďte id společnosti; ukázková kniha je 244.
WITH role_accounts AS (
    SELECT ra.company_id, ra.role_id, ra.account_id
    FROM investra_role_account ra
    UNION
    SELECT ra.company_id, ra.role_id, extra.account_id
    FROM investra_role_account ra
    JOIN investra_role_account_extra_rel extra ON extra.mapping_id = ra.id
)
SELECT c.name AS kniha,
       date_trunc('month', l.date)::date AS mesic,
       COALESCE(i.name, '(bez nástroje)') AS nastroj,
       cur.name AS mena_nastroje,
       COALESCE(-SUM(l.balance) FILTER (
           WHERE l.investra_movement_type = 'fx_realised'
       ), 0) AS realizovany_kurzovy_rozdil,
       COALESCE(-SUM(l.balance) FILTER (
           WHERE l.investra_movement_type = 'fx_revaluation'
       ), 0) AS nerealizovany_kurzovy_rozdil,
       COALESCE(-SUM(l.balance), 0) AS kurzovy_rozdil_celkem
FROM account_move_line l
JOIN role_accounts ra
  ON ra.company_id = l.company_id
 AND ra.account_id = l.account_id
JOIN investra_account_role r ON r.id = ra.role_id
JOIN res_company c ON c.id = l.company_id
LEFT JOIN investra_instrument i ON i.id = l.investra_instrument_id
LEFT JOIN res_currency cur ON cur.id = i.currency_id
WHERE l.company_id = 244
  AND l.parent_state = 'posted'
  AND r.code IN ('gain_fx', 'loss_fx')
  AND l.investra_movement_type IN ('fx_realised', 'fx_revaluation')
GROUP BY c.name, date_trunc('month', l.date), i.id, i.name, cur.name
ORDER BY mesic, nastroj;

-- 3. Kontrola: kurzové řádky obou druhů proti celému zůstatku účtů rolí
-- Rozdíl tvoří zůstatek řádků jiných druhů pohybu na těchto účtech.
WITH role_accounts AS (
    SELECT ra.company_id, ra.role_id, ra.account_id
    FROM investra_role_account ra
    UNION
    SELECT ra.company_id, ra.role_id, extra.account_id
    FROM investra_role_account ra
    JOIN investra_role_account_extra_rel extra ON extra.mapping_id = ra.id
)
SELECT c.id AS company_id, c.name AS kniha, r.code AS role,
       COALESCE(SUM(l.balance) FILTER (
           WHERE l.parent_state = 'posted'
             AND l.investra_movement_type IN ('fx_realised', 'fx_revaluation')
       ), 0) AS zustatek_dvou_druhu_kurzovych_radku,
       COALESCE(SUM(l.balance) FILTER (
           WHERE l.parent_state = 'posted'
       ), 0) AS celkovy_zustatek_role,
       COALESCE(SUM(l.balance) FILTER (
           WHERE l.parent_state = 'posted'
       ), 0)
       - COALESCE(SUM(l.balance) FILTER (
           WHERE l.parent_state = 'posted'
             AND l.investra_movement_type IN ('fx_realised', 'fx_revaluation')
       ), 0) AS rozdil_jine_druhy_pohybu
FROM role_accounts ra
JOIN res_company c ON c.id = ra.company_id
JOIN investra_account_role r ON r.id = ra.role_id
LEFT JOIN account_move_line l
  ON l.company_id = ra.company_id
 AND l.account_id = ra.account_id
WHERE c.id IN (244, 410)
  AND r.code IN ('gain_fx', 'loss_fx')
GROUP BY c.id, c.name, r.code
ORDER BY c.id, r.code;
