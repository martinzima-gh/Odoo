-- Převody mezi bankami, platby na cestě a bankovní poplatky (rozhodnutí 2026-11-12 „Role s více účty“).
-- Jen čtení. Kniha: dosaďte id společnosti (ukázka: 244 = Ukázkový fond, smyšlený).

-- 1. Účty rolí bank, peněz na cestě a bankovních poplatků: hlavní účet a další účty.
select r.code as role, a.code_store->>ra.company_id::text as hlavni_ucet,
       (select string_agg(x.code_store->>ra.company_id::text, ', ' order by x.code_store->>ra.company_id::text)
          from investra_role_account_extra_rel e join account_account x on x.id = e.account_id
         where e.mapping_id = ra.id) as dalsi_ucty
  from investra_role_account ra
  join investra_account_role r on r.id = ra.role_id
  join account_account a on a.id = ra.account_id
 where ra.company_id = 244 and r.code in ('bank', 'cash_in_transit', 'unidentified_payment', 'expense_bank_fee')
 order by 1;

-- 2. Modely párování: Internal Transfers má vést na 119000, Bank Fees na 612000.
select d.name as model, a.code_store->>m.company_id::text as ucet, a.active
  from account_reconcile_model m
  join ir_model_data d on d.model = 'account.reconcile.model' and d.res_id = m.id
  join account_reconcile_model_line l on l.model_id = m.id
  join account_account a on a.id = l.account_id
 where m.company_id = 244
 order by 1;

-- 3. Zůstatky bank a peněz na cestě (zaúčtované doklady); po převodu má být 119000 nulový.
select a.code_store->>l.company_id::text as ucet, a.name->>'en_US' as nazev,
       round(sum(l.debit), 2) as md, round(sum(l.credit), 2) as dal, round(sum(l.balance), 2) as zustatek,
       count(*) filter (where l.reconciled) as sparovano, count(*) as polozek
  from account_move_line l
  join account_move m on m.id = l.move_id
  join account_account a on a.id = l.account_id
 where l.company_id = 244 and m.state = 'posted'
   and (a.code_store->>l.company_id::text like '1311%' or a.code_store->>l.company_id::text like '119%')
 group by 1, 2
 order by 1;

-- 4. Doklady s účtem peněz na cestě: deník, stav, protiúčty.
select m.name as doklad, m.date, j.code as denik, m.state,
       string_agg((a.code_store->>l.company_id::text) || ' ' || round(l.balance, 2), '; ' order by l.id) as radky
  from account_move m
  join account_journal j on j.id = m.journal_id
  join account_move_line l on l.move_id = m.id
  join account_account a on a.id = l.account_id
 where m.company_id = 244
   and m.id in (select l2.move_id from account_move_line l2 join account_account a2 on a2.id = l2.account_id
                 where l2.company_id = 244 and a2.code_store->>'244' like '119%')
 group by m.id, m.name, m.date, j.code, m.state
 order by m.date, m.id;
