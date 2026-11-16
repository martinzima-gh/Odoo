from odoo import models


class AccountAccount(models.Model):
    _inherit = "account.account"

    def _compute_display_name(self):
        """MN-10: číslo účtu před názvem i při jiné aktivní společnosti.

        Odchylka od jádra: kód účtu je v Odoo 20 závislý na společnosti, a když aktivní společnost
        účet nemá, jádro ukáže jen název. Tady se v takovém případě vezme kód v účtu vlastní společnosti.
        Formát `kód název`, bez názvu společnosti. Podmínku skupiny account.group_account_readonly
        neměníme (zůstává z jádra)."""
        super()._compute_display_name()
        if not self.env.user.has_group("account.group_account_readonly"):
            return
        formatted = self.env.context.get("formatted_display_name")
        for account in self:
            if account.code:
                continue
            code = ""
            for company in account.company_ids:
                code = account.with_company(company).code
                if code:
                    break
            if not code:
                continue
            if formatted:
                # jádro dává při prázdném kódu "" + " " + name_path
                account.display_name = f"{code}{account.display_name}"
            else:
                account.display_name = f"{code} {account.name}"
