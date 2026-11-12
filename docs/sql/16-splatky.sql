-- Splátky nástrojů: stav, účetní událost, storno a oprava (rozhodnutí 2026-11-12 „Zámek a storno splátky“).
-- Jen čtení. Kniha: dosaďte id společnosti (ukázka: 244 = Ukázkový fond, smyšlený).

-- 1. Splátky se stavem, událostí a storno dokladem; oprava ukazuje na opravovanou splátku.
select r.id, r.date, i.name as nastroj, r.amount, r.fx_rate, r.state,
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
