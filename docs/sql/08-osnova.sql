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
