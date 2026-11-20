"""Daň ve fondu: výchozí daňové pravidlo, výjimky po účtech a nosič výpočtu (ZJ-07, oddíl 9.3 C2, D4, D5, D10, D11).

Nosič je pravidlo úplaty druhu „Očekávaná daň“ (jedno na fond): drží „Základ: po kroku“ a dosavadní výpočet v ocenění; založí se samo
při zvolení výchozího pravidla fondu. Sazbu a účty bere výpočet daně z daňových pravidel (běh 5 dávky).
"""
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .fee_rule import BASE_STEPS_TAX


class InvestraFundTax(models.Model):
    _inherit = "investra.fund"

    tax_rule_id = fields.Many2one(
        "investra.tax.rule", tracking=True, domain="[('kind', '=', 'general'), ('method', '=', 'current')]",
        string="Výchozí daňové pravidlo",
        help="Platí pro všechny výsledkové účty bez výjimky. Prázdné = fond daň nepočítá.",
    )
    tax_rate_now = fields.Float(related="tax_rule_id.rate_now", string="Aktuální sazba")
    tax_exception_ids = fields.One2many("investra.fund.tax.exception", "fund_id", string="Výjimky")
    tax_fee_rule_id = fields.Many2one("investra.fee.rule", compute="_compute_tax_fee_rule", string="Nosič výpočtu daně")
    tax_base_step = fields.Selection(
        BASE_STEPS_TAX, compute="_compute_tax_base_step", inverse="_inverse_tax_base_step", string="Základ: po kroku",
        help="Které náklady daň ze základu odečítá: po kroku 1 žádné úplaty ani odměna, po kroku 2 úplaty, po kroku 3 úplaty i odměna. "
             "Platí pro účty úplat a odměny bez výjimky na účtu.",
    )

    @api.depends("company_id", "tax_rule_id")
    def _compute_tax_fee_rule(self):
        Rule = self.env["investra.fee.rule"].sudo()
        for fund in self:
            fund.tax_fee_rule_id = Rule.search([("fund_id", "=", fund.id), ("kind", "=", "tax")], limit=1) if fund.id else Rule

    @api.depends("tax_rule_id")
    def _compute_tax_base_step(self):
        Rule = self.env["investra.fee.rule"].sudo()
        for fund in self:
            carrier = Rule.search([("fund_id", "=", fund.id), ("kind", "=", "tax")], limit=1) if fund.id else Rule
            fund.tax_base_step = carrier.base_step or "3"

    def _inverse_tax_base_step(self):
        Rule = self.env["investra.fee.rule"].sudo()
        for fund in self:
            carrier = Rule.search([("fund_id", "=", fund.id), ("kind", "=", "tax")], limit=1)
            if carrier and fund.tax_base_step:
                carrier.base_step = fund.tax_base_step

    # --- nosič ---------------------------------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        funds = super().create(vals_list)
        funds.filtered("tax_rule_id")._sync_tax_carrier()
        return funds

    def write(self, vals):
        result = super().write(vals)
        if "tax_rule_id" in vals:
            self._sync_tax_carrier()
        return result

    def _sync_tax_carrier(self):
        """Nosič výpočtu daně: při zvolení výchozího pravidla se založí (nebo znovu aktivuje), při vyprázdnění se archivuje
        (archivace se zastaví, má-li nosič zaúčtovanou daň – `fee_rule._check_archive`)."""
        Rule = self.env["investra.fee.rule"].sudo().with_context(investra_tax_carrier=True, active_test=False)
        for fund in self:
            carrier = Rule.search([("fund_id", "=", fund.id), ("kind", "=", "tax")], limit=1)
            if fund.tax_rule_id:
                if not carrier:
                    versions = []
                    first = fund.tax_rule_id.version_ids.sorted("valid_from")[:1]
                    if first:
                        # Dosavadní výpočet čte sazbu z nosiče; po přepisu výpočtu (běh 5) se verze nosiče nečtou.
                        versions = [(0, 0, {"valid_from": first.valid_from, "rate": fund.tax_rule_id.rate_now or first.rate})]
                    Rule.create({"name": self.env._("Daň"), "kind": "tax", "fund_id": fund.id, "base_step": "3",
                                 "version_ids": versions})
                elif not carrier.active:
                    carrier.active = True
            elif carrier and carrier.active:
                carrier._check_archive()
                carrier.active = False
        self.invalidate_recordset(["tax_fee_rule_id", "tax_base_step"])

    # --- kontroly -------------------------------------------------------------------------------------------------

    def _tax_rules_used(self):
        """Pravidla použitá ve fondu (výchozí a z výjimek) bez Mimo základ daně."""
        self.ensure_one()
        return (self.tax_rule_id | self.tax_exception_ids.tax_rule_id).filtered(lambda r: r.kind != "exempt")

    @api.constrains("tax_rule_id", "tax_exception_ids")
    def _check_tax_accounts_distinct(self):
        """Zaúčtovaná daň pravidla = zůstatek jeho účtu, proto dvě použitá pravidla nesmí sdílet účet daně, rozvahy ani zápočtu."""
        for fund in self:
            used = fund._tax_rules_used()
            seen = {}
            for rule in used:
                for code in rule._account_codes():
                    if code in seen and seen[code] != rule:
                        raise ValidationError(self.env._(
                            "Pravidla %(a)s a %(b)s sdílejí účet %(code)s. Použitá pravidla fondu musí mít každé vlastní účty daně, "
                            "rozvahy i zápočtu (zaúčtovaná daň pravidla je zůstatek jeho účtu).",
                            a=seen[code].name, b=rule.name, code=code))
                    seen[code] = rule

    @api.constrains("tax_rule_id")
    def _check_tax_rule(self):
        for fund in self:
            rule = fund.tax_rule_id
            if rule and (rule.kind != "general" or rule.method != "current"):
                raise ValidationError(self.env._("Výchozí daňové pravidlo fondu je splatná daň z obecného základu."))

    # --- běžné výjimky (D11) ----------------------------------------------------------------------------------------

    def action_add_common_tax_exceptions(self):
        """Zkopíruje šablonu běžných výjimek (Nastavení › Daně › Šablona výjimek, ZJ-23) do výjimek fondu. Výchozí šablona: české
        dividendy Mimo základ (5 % neuznatelných), zahraniční Samostatný základ 15 % (5 %), dividendy z dceřiných společností a
        penále a reprezentace Mimo základ; řádky „Jen při FVOCI“ (D9/D10/D11) jen u fondu se zařazením FVOCI. Existující výjimku
        nepřepíše, chybějící účet vypíše."""
        self.ensure_one()
        if not self.tax_rule_id:
            raise UserError(self.env._("Nejdřív zvolte výchozí daňové pravidlo fondu."))
        company = self.company_id
        chart = self.env["account.chart.template"].sudo().with_company(company)
        ref = lambda xmlid: self.env.ref(f"investra_nav.{xmlid}")
        has_fvoci = bool(self.env["investra.portfolio.classification"].sudo().search_count(
            [("portfolio_id.fund_id", "=", self.id), ("ifrs9_category", "=", "fvoci")], limit=1))
        common = []
        for line in self.env["investra.tax.exception.template"].sudo().search([]):
            if line.fvoci_only and not has_fvoci:
                continue
            if line.rule_source == "default":
                rule = self.tax_rule_id
            elif line.rule_source == "deferred_fvoci":
                # D9: odložená daň z oceňovacích rozdílů podle sazby výchozího pravidla (5 % → varianta 5 %, jinak 21 %).
                rule = ref("tax_rule_deferred_fvoci_5") if abs(self.tax_rule_id.rate_now - 0.05) < 1e-9 else ref("tax_rule_deferred_fvoci_21")
            else:
                rule = line.tax_rule_id
            common.append(("ifa_" + line.account_code, rule, line.share, line.nondeductible_pct, line.note))
        added, kept, missing = [], [], []
        for ifa, rule, share, pct, note in common:
            account = chart.ref(ifa, raise_if_not_found=False)
            if not account:
                missing.append(ifa.replace("ifa_", ""))
                continue
            if self.tax_exception_ids.filtered(lambda e: e.account_id == account):
                kept.append(account.code)
                continue
            self.env["investra.fund.tax.exception"].create({
                "fund_id": self.id, "account_id": account.id, "tax_rule_id": rule.id, "share": share,
                "nondeductible_pct": pct if account.account_type.startswith(("income", "expense")) else 0.0, "note": note,
            })
            added.append(account.code)
        parts = [self.env._("Přidáno výjimek: %s.", len(added))]
        if kept:
            parts.append(self.env._("Už existují: %s.", ", ".join(kept)))
        if missing:
            parts.append(self.env._("Kniha nemá účty %s (povyšte Investra Chart Fund).", ", ".join(missing)))
        return {
            "type": "ir.actions.client", "tag": "display_notification",
            "params": {"type": "warning" if missing else "success", "sticky": bool(missing), "message": " ".join(parts),
                       "next": {"type": "ir.actions.client", "tag": "soft_reload"}},
        }
