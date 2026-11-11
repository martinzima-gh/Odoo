"""Parametry úpisů a odkupů: stávající třídy převezmou hodnoty svého fondu (fond má výchozí 6 míst, dolů,
rozdíl ve fondu, poplatky 0 %, příjemce obhospodařovatel). Mění jen nové sloupce, jiná data ne."""


def migrate(cr, version):
    cr.execute("""
        UPDATE investra_fund_class c
           SET unit_digits = COALESCE(c.unit_digits, f.unit_digits),
               unit_rounding = COALESCE(c.unit_rounding, f.unit_rounding),
               rounding_owner = COALESCE(c.rounding_owner, f.rounding_owner),
               entry_fee_rate = COALESCE(c.entry_fee_rate, f.entry_fee_rate),
               exit_fee_rate = COALESCE(c.exit_fee_rate, f.exit_fee_rate),
               fee_recipient = COALESCE(c.fee_recipient, f.fee_recipient)
          FROM investra_fund f
         WHERE f.id = c.fund_id
    """)
