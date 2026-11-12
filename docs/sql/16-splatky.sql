-- Splátky nástrojů: stav, účetní událost, storno a oprava (rozhodnutí 2026-11-12 „Zámek a storno splátky“).
-- Jen čtení. Kniha: dosaďte id společnosti (ukázka: 244 = Ukázkový fond, smyšlený).

-- 1. Splátky se stavem, událostí a storno dokladem; oprava ukazuje na opravovanou splátku.
select r.id, r.date, i.name as nastroj, r.kind as druh, r.closes_position as uzavira_pozici, r.principal_amount as jistina, r.interest_amount as urok,
       r.fee_amount as poplatek, r.amount as vyplata, r.fx_rate, r.state,
       e.name as udalost, e.state as stav_udalosti, mv.name as doklad, rv.name as storno_doklad,
       r.replaced_id as opravuje, r.reversal_reason as duvod_storna
  from investra_instrument_repayment r
  join investra_instrument i on i.id = r.instrument_id
  left join investra_accounting_event e on e.id = r.event_id
  left join account_move mv on mv.id = e.move_id
  left join account_move rv on rv.id = e.reversal_move_id
 where r.company_id = 244
 order by r.date, r.id;

-- 2. Kontrola: stav splátky odpovídá stavu události (má vrátit 0 řádků).
select r.id, r.state, e.state as stav_udalosti
  from investra_instrument_repayment r
  left join investra_accounting_event e on e.id = r.event_id
 where (r.state = 'draft' and r.event_id is not null)
    or (r.state = 'posted' and coalesce(e.state, '') <> 'posted')
    or (r.state = 'reversed' and coalesce(e.state, '') <> 'reversed');

-- 3. Zbývající jistina pozic (rozhodnutí 2026-11-12 „Splátky jistiny nástrojů“): jistina z obchodů
--    (kusy × jistina na jednotku z kalendáře, jinak pole Jistina na jednotku, jinak 1) minus zaúčtované splátky.
with ppu as (
    select i.id instrument_id,
           coalesce(nullif((select sum(c.amount) from investra_instrument_cashflow c
                             where c.instrument_id = i.id and c.flow_type = 'principal'), 0), nullif(i.principal, 0), 1) ppu
      from investra_instrument i
), pos as (
    select t.fund_id, t.instrument_id, t.portfolio_id, sum(t.quantity) * max(p.ppu) principal
      from investra_trade t join ppu p on p.instrument_id = t.instrument_id
     group by 1, 2, 3
), paid as (
    select fund_id, instrument_id, portfolio_id, sum(principal_amount) repaid
      from investra_instrument_repayment where state = 'posted' group by 1, 2, 3
)
select f.id fund_id, i.name nastroj, fp.name model, round(pos.principal, 2) jistina,
       round(coalesce(paid.repaid, 0), 2) splaceno, round(pos.principal - coalesce(paid.repaid, 0), 2) zbyva
  from pos
  join investra_fund f on f.id = pos.fund_id
  join investra_instrument i on i.id = pos.instrument_id
  join investra_fund_portfolio fp on fp.id = pos.portfolio_id
  left join paid on paid.fund_id = pos.fund_id and paid.instrument_id = pos.instrument_id
                 and paid.portfolio_id = pos.portfolio_id
 where f.company_id = 244
 order by 2, 3;

-- 4. Inkasa na cestě (role cash_in_transit_receipt) nespárovaná s výpisem: má být jen to, co ještě nepřišlo na účet.
select m.name doklad, l.date, l.name, l.balance, l.amount_residual zbyva_sparovat
  from account_move_line l
  join account_move m on m.id = l.move_id
  join investra_role_account ra on ra.account_id = l.account_id and ra.company_id = l.company_id
  join investra_account_role r on r.id = ra.role_id and r.code = 'cash_in_transit_receipt'
 where l.company_id = 244 and l.parent_state = 'posted' and not l.reconciled
 order by l.date, m.name;
