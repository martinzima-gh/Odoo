from odoo import models

from odoo.addons.account.models.chart_template import template

ROLE_ACCOUNTS = {
    "bank": "ifa_221100",
    "cash_in_transit": "ifa_261000",
    # Splátky nástrojů účtují na inkasa na cestě, výpis je vynuluje (rozhodnutí 2026-11-12 „Splátky jistiny nástrojů“).
    "cash_in_transit_receipt": "ifa_119100",
    "unidentified_payment": "ifa_229000",
    "instrument": "ifa_251000",
    "instrument_debt": "ifa_252000",
    "deposit": "ifa_253000",
    "repo": "ifa_254000",
    "repo_client": "ifa_212000",
    "loan_given": "ifa_255000",
    # Účet ifa_256000 (dříve „Účasti“) nese účasti v reálné hodnotě do výsledku (413100), aby se zůstatky při rozdělení
    # role nepřesouvaly; ostatní účasti mají účet ifa_411000 (413200). Převodová tabulka v docs/osnova-fondu.md.
    "participation": "ifa_411000",
    "participation_fv": "ifa_256000",
    "derivative": "ifa_257000",
    "other_holding": "ifa_258000",
    "unsettled_receivable": "ifa_378100",
    "unsettled_fair_value": "ifa_378200",
    "unsettled_payable": "ifa_379100",
    "receivable_other": "ifa_315000",
    "internal_clearing": "ifa_395000",
    "subscription_payable": "ifa_325100",
    "redemption_payable": "ifa_325200",
    "fee_payable": "ifa_325300",
    "performance_payable": "ifa_325400",
    # Interní identifikátory ifa_* jsou původní pracovní čísla; skutečné kódy (syntetické účty podle vnitřního standardu
    # rámce 501, docs/osnova-501-syntetika.md) jsou v CSV šablony (rozhodnutí 2026-11-12 „Osnova fondů – syntetické účty“).
    "subscription_fee_payable": "ifa_325500",
    "investor_rounding_payable": "ifa_325600",
    "accrual": "ifa_389000",
    "tax_payable": "ifa_341000",
    "class_capital": "ifa_413000",
    # Poplatky ve prospěch fondu nebo třídy (rozhodnutí 2026-11-13): pracovní účty, číslo určí uživatel.
    "entry_fee_capital": "ifa_564100",
    "exit_fee_capital": "ifa_564200",
    "retained_result": "ifa_428000",
    # FVOCI (ZJ-18, dávka ZJ-07 až ZJ-19, oddíl 8 G1): oceňovací rozdíly a odložená daň z nich v ostatních kapitálových fondech
    # (564), číslo pracovní k potvrzení metodikem.
    "revaluation_reserve": "ifa_564300",
    "revaluation_reserve_tax": "ifa_564400",
    "gain_fair_value": "ifa_611000",
    "gain_fx": "ifa_663000",
    "income_interest": "ifa_662000",
    "income_dividend": "ifa_665000",
    "income_other": "ifa_668000",
    "rounding_gain": "ifa_668100",
    "entry_fee_income": "ifa_767200",
    "exit_fee_income": "ifa_767300",
    "loss_fair_value": "ifa_511000",
    # Realizovaný výsledek v RH: analytika pod 615/715 (rozhodnutí 2026-11-12 „Úrok v RH a realizovaný výsledek“).
    "gain_realised": "ifa_611100",
    "loss_realised": "ifa_511100",
    "loss_fx": "ifa_563000",
    "expense_management": "ifa_518100",
    "expense_administration": "ifa_518200",
    "expense_depositary": "ifa_518300",
    "expense_performance": "ifa_518400",
    "expense_other": "ifa_548000",
    "expense_bank_fee": "ifa_612000",
    "rounding_loss": "ifa_548100",
    "expense_tax": "ifa_591000",
    # FX spot, forward a swap (DE-03; čísla účtů schválil Martin 2026-11-16). Reálná hodnota forwardu a swapu ve skupině 31,
    # kurzový rozdíl spotu na uspořádacím účtu 358, podrozvaha ve skupinách 94 a 95, vyrovnávací účet 992.
    "derivative_liability": "ifa_313100",
    "derivative_swap": "ifa_313200",
    "derivative_swap_liability": "ifa_313300",
    "fx_spot_asset": "ifa_358100",
    "fx_spot_liability": "ifa_358200",
    "gain_derivative": "ifa_719100",
    "loss_derivative": "ifa_619100",
    "gain_derivative_swap": "ifa_719200",
    "loss_derivative_swap": "ifa_619200",
    "gain_fx_spot": "ifa_716100",
    "loss_fx_spot": "ifa_616100",
    "offbalance_forward_receivable": "ifa_953100",
    "offbalance_forward_payable": "ifa_954100",
    "offbalance_swap_receivable": "ifa_953200",
    "offbalance_swap_payable": "ifa_954200",
    "offbalance_spot_receivable": "ifa_943000",
    "offbalance_spot_payable": "ifa_944000",
    "offbalance_clearing": "ifa_992000",
}


# Účty Odoo pro platby čekající na spárování s výpisem (Outstanding Receipts/Payments). Odoo je zakládá s prefixem
# bankovních účtů (1311), tedy mezi banky; ve fondu jsou to peníze na cestě (119) a patří k roli cash_in_transit
# jako další účty (rozhodnutí 2026-11-12 „Role s více účty“).
OUTSTANDING_ACCOUNTS = {
    "account_journal_payment_debit_account_id": "ifa_119100",
    "account_journal_payment_credit_account_id": "ifa_119200",
}
# Další účty rolí: role → účty šablony, které se k ní přidají jako další účty (hlavní účet je v ROLE_ACCOUNTS).
# Inkasa na cestě (119100) mají od 2026-11-12 vlastní roli cash_in_transit_receipt (hlavní účet).
# Poplatky obchodů s nástroji (ZJ-16) mají vlastní analytický účet 615200 pod rolí Bankovní poplatky: ČNB VYFO20_11 ř. 23
# sčítá hlavní i další účty role, ostatní poplatky (612000) zůstávají odděleně.
# Dividendy a daně (dávka ZJ-07 až ZJ-19, oddíl 9.3 C1 a 7): analytické účty pod existujícími rolemi; ČNB sčítá hlavní i další
# účty role. 341210 a 341220 jsou pohledávky z dividend a ze zahraniční daně k vrácení (ZJ-19), pracovní čísla k potvrzení.
EXTRA_ROLE_ACCOUNTS = {
    "cash_in_transit": ("ifa_119200",),
    "expense_bank_fee": ("ifa_615200",),
    "income_dividend": ("ifa_714100", "ifa_714200", "ifa_714300"),
    "expense_other": ("ifa_667300", "ifa_667400", "ifa_667500"),
    "revaluation_reserve": ("ifa_564500",),
    "retained_result": ("ifa_571100",),
    "expense_tax": ("ifa_681100", "ifa_681200", "ifa_681300", "ifa_681400", "ifa_682000"),
    "tax_payable": ("ifa_347300", "ifa_348000"),
    "receivable_other": ("ifa_341210", "ifa_341220"),
}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("investra_fund")
    def _get_investra_fund_template_data(self):
        return {"name": "Investra fond (osnova podle vyhlášky 501)", "country": "cz", "code_digits": "6"}

    @template("investra_fund", "res.company")
    def _get_investra_fund_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.cz",
                "bank_account_code_prefix": "1311",
                "cash_account_code_prefix": "1111",
                # Převody mezi bankami jdou přes účet peněz na cestě (119), aby je viděla kontrola ocenění i výkaz ČNB.
                "transfer_account_code_prefix": "1191",
                "transfer_account_id": "ifa_261000",
                "income_currency_exchange_account_id": "ifa_663000",
                "expense_currency_exchange_account_id": "ifa_563000",
                # Neidentifikované platby jsou závazek (229); doména formuláře deníku nabízí jen asset_current,
                # hodnotu proto nastavuje šablona (Odoo ji na serveru nekontroluje).
                "account_journal_suspense_account_id": "ifa_229000",
                "receivable_account_id": "ifa_311000",
                "payable_account_id": "ifa_321000",
                "income_account_id": "ifa_668000",
                "expense_account_id": "ifa_548000",
                # Bez nich Odoo založí účty 999xxx, ale třída 9 je podle vyhlášky 501 podrozvaha.
                "default_cash_difference_income_account_id": "ifa_761901",
                "default_cash_difference_expense_account_id": "ifa_661901",
                "account_journal_early_pay_discount_gain_account_id": "ifa_761902",
                "account_journal_early_pay_discount_loss_account_id": "ifa_661902",
            },
        }

    def _create_outstanding_accounts(self, company, bank_prefix, code_digits):
        """Ve fondu jsou účty plateb na cestě účty šablony (119100, 119200); Odoo je jen převezme pod svým xmlid."""
        if company.chart_template != "investra_fund":
            return super()._create_outstanding_accounts(company, bank_prefix, code_digits)
        Data = self.env["ir.model.data"].sudo()
        for field, ifa in OUTSTANDING_ACCOUNTS.items():
            name = f"{company.id}_{field}"
            if not Data.search_count([("module", "=", "account"), ("name", "=", name)]):
                Data.create({
                    "module": "account", "name": name, "model": "account.account",
                    "res_id": self.with_company(company).ref(ifa).id, "noupdate": True,
                })
        return None

    def _get_bank_fees_reco_account(self, company):
        """Model párování Bank Fees: bankovní poplatky na 612 (rozhodnutí 2026-11-12), ne první nákladový účet."""
        if company.chart_template == "investra_fund":
            return self.with_company(company).ref("ifa_612000")
        return super()._get_bank_fees_reco_account(company)
