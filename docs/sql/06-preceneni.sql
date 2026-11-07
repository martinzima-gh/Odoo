-- Přecenění cizích měn (modul investra_fx_revaluation). Jen čtení.
-- Ověřeno na databázi investra_test; v investra_dev zatím bez dat.

-- 1. Profily přecenění: zdroj kurzu, stáří a protiúčty
SELECT p.name AS profil, p.rate_source AS zdroj_kurzu, p.max_rate_age_days AS stari_dny,
       g.name->>'cs_CZ' AS ucet_zisku, l.name->>'cs_CZ' AS ucet_ztraty
FROM investra_fx_profile p
LEFT JOIN account_account g ON g.id = p.gain_account_id
LEFT JOIN account_account l ON l.id = p.loss_account_id
ORDER BY p.name;

-- 2. Přecenění a stav návrhu dokladu
SELECT r.date AS datum, p.name AS profil, m.state AS stav_dokladu, m.name AS doklad
FROM investra_fx_run r
JOIN investra_fx_profile p ON p.id = r.profile_id
LEFT JOIN account_move m ON m.id = r.move_id
ORDER BY r.date DESC;

-- 3. Rozpis přecenění po účtu, měně a partnerovi
SELECT r.date AS datum, c.name AS mena, l.amount_currency AS zustatek_v_mene, l.rate AS kurz,
       l.balance AS ucetni_zustatek, l.target AS potrebny_zustatek, l.difference AS rozdil
FROM investra_fx_run_line l
JOIN investra_fx_run r ON r.id = l.run_id
JOIN res_currency c ON c.id = l.foreign_currency_id
ORDER BY r.date DESC, c.name;

-- 4. Kurzy ČNB k vybranému období, se zdrojem a otiskem souboru
SELECT r.date AS datum, c.name AS mena, r.quantity AS mnozstvi, r.rate AS kurz, left(r.document_hash, 12) AS otisk
FROM investra_rate r
JOIN res_currency c ON c.id = r.currency_id
WHERE c.name IN ('EUR', 'USD') AND r.date >= DATE '2026-11-01'
ORDER BY r.date DESC, c.name;
