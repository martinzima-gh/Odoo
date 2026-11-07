-- Ocenění fondů a účtování (modul investra_nav). Jen čtení.
-- Ověřeno na databázi investra_test se smyšlenými daty; v investra_dev tyto tabulky zatím nejsou.

-- 1. Přehled ocenění: stav, verze a fondový kapitál
SELECT c.name AS fond, v.date AS datum, v.version AS verze, v.state AS stav, v.fund_capital AS fk
FROM investra_valuation v
JOIN investra_fund f ON f.id = v.fund_id
JOIN res_company c ON c.id = f.company_id
ORDER BY c.name, v.date, v.version;

-- 2. Výsledek tříd: kapitál, kusy, kurz a specifická změna
SELECT v.date AS datum, k.code AS trida, l.pre_capital AS predbezny_kapital, l.ratio AS pomer,
       l.delta AS specificka_zmena, l.capital AS kapital, l.units AS kusy, l.price AS kurz
FROM investra_valuation_class l
JOIN investra_valuation v ON v.id = l.valuation_id
JOIN investra_fund_class k ON k.id = l.class_id
ORDER BY v.date, k.code;

-- 3. Kontrola: součet tříd se rovná FK
SELECT v.id, v.date AS datum, v.fund_capital AS fk, SUM(l.capital) AS soucet_trid,
       v.fund_capital - SUM(l.capital) AS rozdil
FROM investra_valuation v
JOIN investra_valuation_class l ON l.valuation_id = v.id
GROUP BY v.id, v.date, v.fund_capital
ORDER BY v.date;

-- 4. Doklady ocenění a jejich stav: návrh, zamčený návrh, zaúčtováno, stornováno
SELECT e.date AS datum, e.name AS udalost, e.state AS stav_udalosti, m.state AS stav_dokladu,
       m.name AS cislo_dokladu, m.inalterable_hash IS NOT NULL AS ma_hash
FROM investra_accounting_event e
LEFT JOIN account_move m ON m.id = e.move_id
ORDER BY e.date, e.id;

-- 5. Řádky s třídou: co tvoří specifickou změnu (ΔT)
SELECT l.date AS datum, a.code_store->>c.id::text AS ucet, k.code AS trida, l.balance AS castka,
       l.investra_movement_type AS typ_pohybu, l.parent_state AS stav
FROM account_move_line l
JOIN account_account a ON a.id = l.account_id
JOIN res_company c ON c.id = l.company_id
JOIN investra_fund_class k ON k.id = l.investra_class_id
ORDER BY l.date, l.id;

-- 6. Rozpis úplat po pravidlech
SELECT v.date AS datum, r.name AS pravidlo, k.code AS trida, f.amount AS castka
FROM investra_valuation_fee f
JOIN investra_valuation v ON v.id = f.valuation_id
JOIN investra_fee_rule r ON r.id = f.rule_id
LEFT JOIN investra_fund_class k ON k.id = f.class_id
ORDER BY v.date, r.sequence;

-- 7. Portfolio k datu: měna, pořízení, reálná hodnota a kurz
SELECT v.date AS datum, p.kind AS druh, p.name AS nazev, cur.name AS mena, p.quantity AS kusy,
       p.cost AS porizeni, p.fair_value_currency AS rh_v_mene, p.fx_rate AS kurz, p.fair_value AS rh_ve_mene_fondu
FROM investra_valuation_portfolio p
JOIN investra_valuation v ON v.id = p.valuation_id
JOIN res_currency cur ON cur.id = p.currency_id
ORDER BY v.date, p.kind, p.name;

-- 8. Vyhlášené kurzy se zdrojem a datem stažení
SELECT r.date AS datum, r.source AS zdroj, cur.name AS mena, r.quantity AS mnozstvi, r.rate AS kurz, r.fetched_at AS stazeno
FROM investra_rate r
JOIN res_currency cur ON cur.id = r.currency_id
ORDER BY r.date DESC, cur.name;
