from odoo import api, models
from odoo.exceptions import UserError

# Daně pro identifikovanou osobu: sazba, původ dodavatele, standardní daň l10n_cz (zdroj štítků a skupiny), účet daně k úhradě.
# EU: řádky přiznání 5 a 6, třetí země: řádky 12 a 13 (štítky převzaty ze standardních daní).
SPECS = [
    {"rate": 21, "origin": "eu", "label": "z EU", "source": "l10n_cz_21_receipt_service_person_eu", "payable": "343221"},
    {"rate": 12, "origin": "eu", "label": "z EU", "source": "l10n_cz_12_receipt_service_person_eu", "payable": "343212"},
    {"rate": 21, "origin": "non_eu", "label": "ze třetí země", "source": "l10n_cz_21_receipt_service_person_non_eu", "payable": "343221"},
    {"rate": 12, "origin": "non_eu", "label": "ze třetí země", "source": "l10n_cz_12_receipt_service_person_non_eu", "payable": "343212"},
]


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def _identified_vat_name(self, spec):
        return f"{spec['rate']} % IO přijatá služba {spec['label']}"

    def _setup_identified_vat_taxes(self):
        """Založí daně pro identifikovanou osobu, pokud ještě nejsou; vrací je.

        Standardní daň l10n_cz pro přijetí služby z EU rozpisuje daň na vstup (nárok na odpočet) a výstup.
        Identifikovaná osoba (§ 6h ZDPH) odpočet nemá: daň se zaúčtuje do závazku na daň k úhradě a zároveň zvýší náklad,
        který nese řádek dokladu. Částka dluhu dodavateli se nemění. Štítky přiznání se zatím přebírají jen u základu.
        Je to účetní návrh, který potvrdí metodik nebo daňový poradce.
        """
        self.ensure_one()
        Tax = self.env["account.tax"].with_context(active_test=False).with_company(self)
        Account = self.env["account.account"].with_company(self)
        created = Tax
        for spec in SPECS:
            rate = spec["rate"]
            name = self._identified_vat_name(spec)
            existing = Tax.search([("company_id", "=", self.id), ("name", "=", name)])
            if existing:
                created |= existing
                continue
            source = self.env.ref(f"account.{self.id}_{spec['source']}", raise_if_not_found=False)
            payable = Account.search([("code", "=", spec["payable"])], limit=1)
            if not source or not payable:
                raise UserError(self.env._("Společnost %s nemá českou osnovu s daní a účtem %s.", self.name, spec["payable"]))
            base_tags = source.invoice_repartition_line_ids.filtered(lambda r: r.repartition_type == "base").tag_ids
            refund_tags = source.refund_repartition_line_ids.filtered(lambda r: r.repartition_type == "base").tag_ids

            def lines(base_tag_ids):
                return [
                    (0, 0, {"repartition_type": "base", "factor_percent": 100, "tag_ids": [(6, 0, base_tag_ids.ids)]}),
                    # Daň zvyšuje náklad: bez účtu patří řádek účtu základu.
                    (0, 0, {"repartition_type": "tax", "factor_percent": 100, "use_in_tax_closing": False}),
                    (0, 0, {"repartition_type": "tax", "factor_percent": -100, "account_id": payable.id, "use_in_tax_closing": True}),
                ]

            created |= Tax.create({
                "name": name,
                "description": f"{rate} % DPH, identifikovaná osoba",
                "type_tax_use": "purchase",
                "amount_type": "percent",
                "amount": rate,
                "tax_scope": "service",
                "company_id": self.id,
                "country_id": source.country_id.id,
                "tax_group_id": source.tax_group_id.id,
                "invoice_repartition_line_ids": lines(base_tags),
                "refund_repartition_line_ids": lines(refund_tags),
            })
        return created
