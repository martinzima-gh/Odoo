from odoo import api, models
from odoo.exceptions import UserError

# Daně pro identifikovanou osobu: sazba, původ dodavatele, standardní daň l10n_cz (zdroj štítků a skupiny), účet daně k úhradě.
# EU s DIČ: řádky přiznání 5 (základní) a 6 (snížená); ostatní zahraničí: řádky 12 a 13. Štítky se přebírají ze standardních daní.
SPECS = [
    {"rate": 21, "origin": "eu", "label": "z EU", "source": "l10n_cz_21_receipt_service_person_eu", "payable": "343221"},
    {"rate": 12, "origin": "eu", "label": "z EU", "source": "l10n_cz_12_receipt_service_person_eu", "payable": "343212"},
    {"rate": 21, "origin": "non_eu", "label": "ze třetí země", "source": "l10n_cz_21_receipt_service_person_non_eu", "payable": "343221"},
    {"rate": 12, "origin": "non_eu", "label": "ze třetí země", "source": "l10n_cz_12_receipt_service_person_non_eu", "payable": "343212"},
]

# Fiskální pozice. Pořadí rozhoduje: tuzemsko (standardní pozice l10n_cz, sekvence 1) se vyhodnotí dřív,
# jinak by se pozice bez země použila i pro české partnery. Dodavatel z EU bez DIČ spadne do „ostatní zahraničí“
# (řádky 12 a 13). Pozice daň jen přemapuje nebo odebere, prázdný řádek nevyplní.
FPOS = {
    "eu": {"name": "Identifikovaná osoba – EU s DIČ", "sequence": 2, "vat_required": True, "group": "account.europe_vat"},
    "non_eu": {"name": "Identifikovaná osoba – ostatní zahraničí", "sequence": 4, "vat_required": False, "group": None},
}


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def _identified_vat_name(self, spec):
        return f"{spec['rate']} % IO přijatá služba {spec['label']}"

    def _setup_identified_vat_fiscal_positions(self):
        """Zapne standardní tuzemskou pozici a založí pozice pro identifikovanou osobu; vrací {původ: pozice}."""
        self.ensure_one()
        Fpos = self.env["account.fiscal.position"].with_context(active_test=False).with_company(self)
        domestic = self.env.ref(f"account.{self.id}_fiscal_position_domestic_cz", raise_if_not_found=False)
        if not domestic:
            raise UserError(self.env._("Společnost %s nemá tuzemskou fiskální pozici české lokalizace.", self.name))
        if not domestic.active:
            domestic.active = True
        result = {}
        for origin, spec in FPOS.items():
            group = self.env.ref(spec["group"], raise_if_not_found=False) if spec["group"] else self.env["res.country.group"]
            values = {
                "name": spec["name"], "sequence": spec["sequence"], "auto_apply": True, "vat_required": spec["vat_required"],
                "country_group_id": group.id or False, "company_id": self.id, "active": True,
            }
            fpos = Fpos.search([("company_id", "=", self.id), ("name", "=", spec["name"])], limit=1)
            if fpos:
                fpos.write(values)
            else:
                fpos = Fpos.create(values)
            result[origin] = fpos
        return result

    def _setup_identified_vat_taxes(self):
        """Založí nebo srovná daně pro identifikovanou osobu a jejich fiskální pozice; vrací daně.

        Standardní daň l10n_cz pro přijetí služby ze zahraničí rozpisuje daň na vstup (nárok na odpočet) a výstup.
        Identifikovaná osoba (§ 6h ZDPH) odpočet nemá: daň se zaúčtuje do závazku na daň k úhradě a zároveň zvýší náklad,
        který nese řádek dokladu. Částka dluhu dodavateli se nemění. Štítky přiznání (základ a daň) se přebírají
        ze standardní daně; řádek +100 % nese štítek daně stejně jako ve standardu.
        Odpočet v řádcích 43 a 44 přiznání počítá vzorec l10n_cz automaticky z řádků 3 až 13; u identifikované osoby
        musí být nula. Je to účetní návrh, který potvrdí metodik nebo daňový poradce.
        """
        self.ensure_one()
        Tax = self.env["account.tax"].with_context(active_test=False).with_company(self)
        Account = self.env["account.account"].with_company(self)
        fpos = self._setup_identified_vat_fiscal_positions()
        result = Tax
        for spec in SPECS:
            rate = spec["rate"]
            name = self._identified_vat_name(spec)
            source = self.env.ref(f"account.{self.id}_{spec['source']}", raise_if_not_found=False)
            payable = Account.search([("code", "=", spec["payable"])], limit=1)
            if not source or not payable:
                raise UserError(self.env._("Společnost %s nemá českou osnovu s daní a účtem %s.", self.name, spec["payable"]))
            tags = {}
            for doc in ("invoice", "refund"):
                lines = source.repartition_line_ids.filtered(lambda r, d=doc: r.document_type == d)
                tags[doc] = {
                    "base": lines.filtered(lambda r: r.repartition_type == "base").tag_ids,
                    "tax": lines.filtered(lambda r: r.repartition_type == "tax" and r.factor_percent > 0).tag_ids,
                }

            existing = Tax.search([("company_id", "=", self.id), ("name", "=", name)])
            if existing:
                for doc in ("invoice", "refund"):
                    lines = existing.repartition_line_ids.filtered(lambda r, d=doc: r.document_type == d)
                    lines.filtered(lambda r: r.repartition_type == "base").tag_ids = tags[doc]["base"]
                    lines.filtered(lambda r: r.repartition_type == "tax" and r.factor_percent > 0).tag_ids = tags[doc]["tax"]
                existing.fiscal_position_ids = fpos[spec["origin"]]
                result |= existing
                continue

            def lines(doc_tags):
                return [
                    (0, 0, {"repartition_type": "base", "factor_percent": 100, "tag_ids": [(6, 0, doc_tags["base"].ids)]}),
                    # Daň zvyšuje náklad: bez účtu patří řádek účtu základu; štítek daně jako ve standardu.
                    (0, 0, {"repartition_type": "tax", "factor_percent": 100, "use_in_tax_closing": False,
                            "tag_ids": [(6, 0, doc_tags["tax"].ids)]}),
                    (0, 0, {"repartition_type": "tax", "factor_percent": -100, "account_id": payable.id, "use_in_tax_closing": True}),
                ]

            result |= Tax.create({
                "name": name,
                "description": f"{rate} % DPH, identifikovaná osoba",
                "type_tax_use": "purchase",
                "amount_type": "percent",
                "amount": rate,
                "tax_scope": "service",
                "company_id": self.id,
                "country_id": source.country_id.id,
                "tax_group_id": source.tax_group_id.id,
                "fiscal_position_ids": [(6, 0, fpos[spec["origin"]].ids)],
                "invoice_repartition_line_ids": lines(tags["invoice"]),
                "refund_repartition_line_ids": lines(tags["refund"]),
            })
        return result
