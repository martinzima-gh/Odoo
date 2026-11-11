"""Úpisy a odkupy, body A–E (rozhodnutí 2026-11-11). Doplní nové sloupce stávajících pohybů; doklady se nemění.

- stav: zaúčtovaný pohyb (má událost) = Zaúčtováno, ostatní Nezaúčtováno;
- zdroj: ruční zadání s důvodem „Zadáno před evidencí zdroje“;
- cena: hrubá částka / kusy v měně kurzu; u třídy v cizí měně bez částky v měně kurzu a bez kurzu zůstane prázdná
  (cenu v měně třídy nejde určit);
- poplatek a rozdíl 0, rozdíl patří podle třídy;
- změna kapitálu = hrubá částka (tak byly pohyby zaúčtované: banka / kapitál třídy).
"""


def migrate(cr, version):
    cr.execute("UPDATE investra_class_movement SET state = 'posted' WHERE event_id IS NOT NULL")
    cr.execute("UPDATE investra_class_movement SET state = 'draft' WHERE event_id IS NULL AND state IS NULL")
    cr.execute("""
        UPDATE investra_class_movement
           SET source = 'manual',
               manual_reason = 'Zadáno před evidencí zdroje (migrace 20.0.0.7.0)'
         WHERE source IS NULL OR (source = 'manual' AND COALESCE(manual_reason, '') = '')
    """)
    cr.execute("""
        UPDATE investra_class_movement m
           SET rounding_owner = COALESCE(m.rounding_owner, c.rounding_owner, 'fund'),
               fee_amount_class = COALESCE(m.fee_amount_class, 0),
               rounding_amount_class = COALESCE(m.rounding_amount_class, 0),
               capital_amount = m.amount,
               capital_amount_class = CASE
                   WHEN COALESCE(m.amount_class, 0) <> 0 THEN m.amount_class
                   WHEN c.currency_id = rc.currency_id THEN m.amount
                   WHEN COALESCE(m.fx_rate, 0) <> 0 THEN round((m.amount / m.fx_rate)::numeric, 2)
                   ELSE 0 END,
               price = CASE
                   WHEN m.price IS NOT NULL AND m.price <> 0 THEN m.price
                   WHEN COALESCE(m.amount_class, 0) <> 0 THEN m.amount_class / m.units
                   WHEN c.currency_id = rc.currency_id THEN m.amount / m.units
                   WHEN COALESCE(m.fx_rate, 0) <> 0 THEN m.amount / m.fx_rate / m.units
                   ELSE NULL END
          FROM investra_fund_class c, res_company rc
         WHERE c.id = m.class_id AND rc.id = m.company_id
    """)
