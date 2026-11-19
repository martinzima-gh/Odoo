-- Kontrola dat před ZJ-12 krok 2 (základ úplat ve čtyřech krocích). Jen čtení, spouštět po jednom.
-- Ověřeno na pracovní databázi investra (2026-11-18). Platí pro stav před migrací (sloupce base_mode, perf_base).

-- 1. Přehled pravidel podle druhu a nastavení základu
SELECT kind, base_source, base_mode, perf_base, active, count(*) AS pocet
FROM investra_fee_rule GROUP BY 1,2,3,4,5 ORDER BY 1,2,3,4,5;

-- 2. Odměny sdílející třídu (aktivní) – očekává se 0 řádků
SELECT r.fund_id, rel.investra_fund_class_id AS trida, count(*) AS pocet, array_agg(r.id ORDER BY r.id) AS pravidla
FROM investra_fee_rule r
JOIN investra_fee_rule_investra_fund_class_rel rel ON rel.investra_fee_rule_id = r.id
WHERE r.kind = 'performance' AND r.active GROUP BY 1,2 HAVING count(*) > 1;

-- 3. Odměny bez tříd (porušují rozhodnutí 2026-11-17) – očekává se 0 řádků
SELECT r.id, r.name, r.fund_id FROM investra_fee_rule r
WHERE r.kind = 'performance' AND NOT EXISTS (
  SELECT 1 FROM investra_fee_rule_investra_fund_class_rel x WHERE x.investra_fee_rule_id = r.id);

-- 4. Fondy s více pravidly daně (aktivními) – očekává se 0 řádků
SELECT fund_id, count(*) AS pocet, array_agg(id) AS pravidla
FROM investra_fee_rule WHERE kind = 'tax' AND active GROUP BY 1 HAVING count(*) > 1;

-- 5. Průměrný FK s třídami nebo příjemci – očekává se 0 řádků
SELECT r.id, r.fund_id, r.active,
  (SELECT count(*) FROM investra_fee_rule_investra_fund_class_rel x WHERE x.investra_fee_rule_id = r.id) AS tridy,
  (SELECT count(*) FROM investra_fee_rule_recipient_rel y WHERE y.rule_id = r.id) AS prijemci
FROM investra_fee_rule r WHERE r.base_source = 'average_fk';

-- 6. Pravidla, jejichž výsledek se po převodu změní (odměna před úplatami nebo po dani; úplata po úplatách)
SELECT id, fund_id, kind, base_source, base_mode, perf_base FROM investra_fee_rule
WHERE (kind = 'performance' AND perf_base <> 'after_fees') OR (kind = 'periodic' AND base_mode = 'after');
