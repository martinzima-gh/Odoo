-- Úrok v RH a realizovaný výsledek (rozhodnutí 2026-11-12 „Úrok v RH a realizovaný výsledek“).
-- Jen čtení. Kniha: dosaďte id společnosti (ukázka: 3363 = Ukázkový fond Delta, smyšlený).

-- 1. Řádky portfolia ocenění: naběhlý úrok v hodnotě, pořizovací cena průměrem a realizovaný výsledek.
select v.date as datum, v.version as verze, v.state, p.name as pozice, c.ifrs9_category as kategorie, p.quantity as kusy,
       p.price as cena, p.accrued_interest_currency as nabehly_urok_v_mene, p.cost_currency as porizovaci_v_mene,
       p.fair_value_currency as hodnota_v_mene, p.fair_value as hodnota, p.realised as realizovany_vysledek
  from investra_valuation_portfolio p
  join investra_valuation v on v.id = p.valuation_id
  left join investra_portfolio_classification c on c.id = p.classification_id
 where p.company_id = 3363
 order by v.date desc, v.version desc, p.name;

-- 2. Výsledek z nástrojů po druzích pohybu a rolích (úrok, přecenění, realizace, kurz), zaúčtované doklady.
select r.code as role, l.investra_movement_type as druh_pohybu, i.name as nastroj, sum(l.balance) as zustatek
  from account_move_line l
  join investra_role_account m on m.company_id = l.company_id and m.account_id = l.account_id
  join investra_account_role r on r.id = m.role_id
  left join investra_instrument i on i.id = l.investra_instrument_id
 where l.company_id = 3363 and l.parent_state = 'posted'
   and r.code in ('income_interest', 'gain_fair_value', 'loss_fair_value', 'gain_realised', 'loss_realised', 'gain_fx', 'loss_fx')
 group by r.code, l.investra_movement_type, i.name
 order by r.code, i.name;

-- 3. Obchody s dluhopisy a naběhlým úrokem zaplaceným (nákup) nebo přijatým (prodej).
select t.trade_date, i.name as nastroj, t.quantity as kusy, t.price as cena, t.accrued_interest as nabehly_urok,
       t.quantity * t.price + sign(t.quantity) * coalesce(t.accrued_interest, 0) as platba_v_mene, t.state
  from investra_trade t
  join investra_instrument i on i.id = t.instrument_id
 where t.company_id = 3363 and coalesce(t.accrued_interest, 0) <> 0
 order by t.trade_date;
