-- Osnova v investra_dev: jen čtení. Kód účtu je uložený podle společnosti, 1 = Investra Services.

-- Kolik účtů má každý typ; typ určuje zařazení v Odoo, ne číslo účtu.
SELECT account_type AS typ, count(*) AS uctu
FROM account_account
GROUP BY account_type
ORDER BY uctu DESC;

-- Účty z revize: typ a párování.
SELECT code_store->>'1'                       AS ucet,
       coalesce(name->>'cs_CZ', name->>'en_US') AS nazev,
       account_type                           AS typ,
       reconcile                              AS parovani
FROM account_account
WHERE left(code_store->>'1', 2) IN ('23', '24', '45', '46', '70', '71')
ORDER BY 1;

-- Zúčtovací účty bez párování: u těchto nejdou sledovat otevřené položky.
SELECT code_store->>'1' AS ucet, coalesce(name->>'cs_CZ', name->>'en_US') AS nazev
FROM account_account
WHERE left(code_store->>'1', 1) = '3' AND NOT reconcile
ORDER BY 1;

-- Výchozí účty deníků.
SELECT j.code AS denik, j.type AS druh, a.code_store->>'1' AS vychozi_ucet
FROM account_journal j
LEFT JOIN account_account a ON a.id = j.default_account_id
ORDER BY j.id;

-- Archivované účty (active = false); od 2026-11-08 uzávěrkové 701000, 702000, 710000.
SELECT code_store->>'1' AS ucet, name->>'cs_CZ' AS nazev, account_type AS typ
FROM account_account
WHERE active IS FALSE
ORDER BY 1;

-- Účty s párováním mimo pohledávky a závazky; od 2026-11-08 doplněno 324, 325, 335, 342, 378, 379, 388, 389.
SELECT code_store->>'1' AS ucet, name->>'cs_CZ' AS nazev, account_type AS typ
FROM account_account
WHERE active AND reconcile AND account_type NOT IN ('asset_receivable', 'liability_payable')
ORDER BY 1;

-- Typy účtů po opravě (bod 3, 2026-11-08): úvěry, dluhopisy, výpomoci a rezervy.
SELECT code_store->>'1' AS ucet, name->>'cs_CZ' AS nazev, account_type AS typ
FROM account_account
WHERE code_store->>'1' IN ('231000', '232000', '241000', '249000', '451000', '452000', '453000', '459000', '461000')
ORDER BY 1;

-- Po bodu 6 (2026-11-08): FA má výchozí účet 602000, PŘIJATÁ FAKTURA 518000 (výpis výše).

-- Po bodu 7 (2026-11-08): opravené názvy 347, 358, 563 a archivovaný 593 (viz výpis archivovaných účtů výše).

-- Po bodu 8 (2026-11-08): všech 32 daní a 4 fiskální pozice je archivováno.
SELECT type_tax_use AS pouziti, active, count(*) AS pocet
FROM account_tax
GROUP BY 1, 2
ORDER BY 1, 2;

-- Aktivní daně po instalaci modulu investra_vat_identified (21 % a 12 % IO přijatá služba z EU) a jejich rozpis.
SELECT t.name->>'cs_CZ' AS dan, r.document_type AS doklad, r.repartition_type AS druh, r.factor_percent AS procent,
       a.code_store->>'1' AS ucet
FROM account_tax t
JOIN account_tax_repartition_line r ON r.tax_id = t.id
LEFT JOIN account_account a ON a.id = r.account_id
WHERE t.active
ORDER BY t.id, r.document_type, r.id;

-- Účty s výchozí daní (46 účtů), uplatní se po opětovném zapnutí daní.
SELECT a.code_store->>'1' AS ucet, t.name->>'cs_CZ' AS vychozi_dan, t.active
FROM account_account_tax_default_rel r
JOIN account_account a ON a.id = r.account_id
JOIN account_tax t ON t.id = r.tax_id
ORDER BY 1;
