-- Převodová tabulka ČNB: jen databáze investra_test, v investra_dev modul není.
-- Co ukazuje: která role účtu jde na který řádek výkazu a do kterých součtů.
SELECT m.sheet            AS list,
       m."row"            AS radek,
       m.source           AS zdroj,
       r.code             AS role,
       r.name             AS nazev_role,
       m.ifrs9_category   AS kategorie_ifrs9,
       m.period           AS obdobi,
       m.sign             AS znamenko,
       m.report_sign      AS znamenko_radku,
       m.rollup_rows      AS soucty,
       m.valid_from       AS plati_od
FROM investra_cnb_map m
LEFT JOIN investra_account_role r ON r.id = m.role_id
ORDER BY m.sheet, m."row", m.id;

-- Kolik řádků převodu má každý list.
SELECT sheet AS list, count(*) AS radku
FROM investra_cnb_map
GROUP BY sheet
ORDER BY sheet;
