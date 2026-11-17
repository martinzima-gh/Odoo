"""ZJ-01 (rozhodnutí 2026-11-17): schvalovací matice pro celou aplikaci, role místo nejnižší role.

Před aktualizací schématu (nová unikátnost řádku matice podle činnosti a „Platí od“):
- řádky obhospodařovatele → globální, kolize data → ponechán novější id (ohlásí se); řádek fondu převod zastaví,
- text role v řádcích žádostí (`role`) místo kódu.
Skupiny Investry uživatelům zůstávají; nově se odvozují z rolí, až je správce přiřadí (ZJ-02, ZJ-04).
"""

from odoo.addons.investra_fund.zj01_migration import merge_matrix_rows, role_codes_to_text


def migrate(cr, version):
    merge_matrix_rows(cr)
    role_codes_to_text(cr, "investra_approval_request_line", "role")
