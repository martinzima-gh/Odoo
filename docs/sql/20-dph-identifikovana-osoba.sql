-- Daně a fiskální pozice vytvářené modulem identifikované osoby.
-- Jen čtení, spouštět po jednom. Ověřeno na databázi investra_dev.
-- Modul nepřidává pole do res.company; přidává metody, které zakládají daně a fiskální pozice.

-- 1. Společnosti s daněmi a fiskálními pozicemi identifikované osoby
SELECT c.id AS company_id, c.name AS spolecnost, c.chart_template AS osnova,
       count(DISTINCT t.id) AS pocet_dani,
       count(DISTINCT fp.id) AS pocet_fiskalnich_pozic
FROM res_company c
LEFT JOIN account_tax t
       ON t.company_id = c.id
      AND COALESCE(t.description ->> 'cs_CZ', t.description ->> 'en_US')
          LIKE '%DPH, identifikovaná osoba%'
LEFT JOIN account_fiscal_position fp
       ON fp.company_id = c.id
      AND COALESCE(fp.name ->> 'cs_CZ', fp.name ->> 'en_US')
          LIKE 'Identifikovaná osoba%'
GROUP BY c.id, c.name, c.chart_template
HAVING count(DISTINCT t.id) > 0 OR count(DISTINCT fp.id) > 0
ORDER BY c.name;

-- 2. Daně identifikované osoby: sazba, použití, skupina daně a fiskální pozice
SELECT c.name AS spolecnost,
       COALESCE(t.description ->> 'cs_CZ', t.description ->> 'en_US') AS popis,
       COALESCE(t.name ->> 'cs_CZ', t.name ->> 'en_US') AS dan,
       t.amount AS sazba, t.type_tax_use AS pouziti, t.tax_scope AS rozsah,
       COALESCE(g.name ->> 'cs_CZ', g.name ->> 'en_US') AS skupina_dane,
       COALESCE(fp.name ->> 'cs_CZ', fp.name ->> 'en_US') AS fiskalni_pozice,
       fp.auto_apply AS automaticky_vyber, fp.vat_required AS pozadovat_dic
FROM account_tax t
JOIN res_company c ON c.id = t.company_id
LEFT JOIN account_tax_group g ON g.id = t.tax_group_id
LEFT JOIN account_fiscal_position_account_tax_rel rel ON rel.account_tax_id = t.id
LEFT JOIN account_fiscal_position fp ON fp.id = rel.account_fiscal_position_id
WHERE COALESCE(t.description ->> 'cs_CZ', t.description ->> 'en_US')
      LIKE '%DPH, identifikovaná osoba%'
ORDER BY c.name, t.amount, t.description, fp.sequence;

-- 3. Štítky přiznání na rozpisových řádcích daně pro faktury a dobropisy
SELECT c.name AS spolecnost,
       COALESCE(t.description ->> 'cs_CZ', t.description ->> 'en_US') AS dan,
       line.document_type AS typ_dokladu,
       line.repartition_type AS druh_radku,
       line.factor_percent AS podil_procent,
       a.code_store ->> line.company_id::text AS ucet,
       string_agg(
           DISTINCT COALESCE(tag.name ->> 'cs_CZ', tag.name ->> 'en_US'),
           ', ' ORDER BY COALESCE(tag.name ->> 'cs_CZ', tag.name ->> 'en_US')
       ) FILTER (WHERE tag.id IS NOT NULL) AS stitky_priznani
FROM account_tax_repartition_line line
JOIN account_tax t ON t.id = line.tax_id
JOIN res_company c ON c.id = t.company_id
LEFT JOIN account_account a ON a.id = line.account_id
LEFT JOIN account_account_tag_account_tax_repartition_line_rel tag_rel
       ON tag_rel.account_tax_repartition_line_id = line.id
LEFT JOIN account_account_tag tag ON tag.id = tag_rel.account_account_tag_id
WHERE COALESCE(t.description ->> 'cs_CZ', t.description ->> 'en_US')
      LIKE '%DPH, identifikovaná osoba%'
GROUP BY c.name, t.description, line.document_type, line.repartition_type,
         line.factor_percent, a.code_store, line.company_id
ORDER BY c.name, t.description, line.document_type, line.repartition_type;
