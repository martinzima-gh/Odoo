from odoo import models

from odoo.addons.account.models.chart_template import template

ROLE_ACCOUNTS = {
    "bank": "ifa_221100",
    "cash_in_transit": "ifa_261000",
    "instrument": "ifa_251000",
    "instrument_debt": "ifa_252000",
    "deposit": "ifa_253000",
    "repo": "ifa_254000",
    "loan_given": "ifa_255000",
    "participation": "ifa_256000",
    "derivative": "ifa_257000",
    "other_holding": "ifa_258000",
    "receivable_other": "ifa_315000",
    "internal_clearing": "ifa_395000",
    "subscription_payable": "ifa_325100",
    "redemption_payable": "ifa_325200",
    "fee_payable": "ifa_325300",
    "performance_payable": "ifa_325400",
    "accrual": "ifa_389000",
    "tax_payable": "ifa_341000",
    "class_capital": "ifa_413000",
    "retained_result": "ifa_428000",
    "gain_fair_value": "ifa_611000",
    "gain_fx": "ifa_663000",
    "income_interest": "ifa_662000",
    "income_dividend": "ifa_665000",
    "income_other": "ifa_668000",
    "loss_fair_value": "ifa_511000",
    "loss_fx": "ifa_563000",
    "expense_management": "ifa_518100",
    "expense_administration": "ifa_518200",
    "expense_depositary": "ifa_518300",
    "expense_performance": "ifa_518400",
    "expense_other": "ifa_548000",
    "expense_tax": "ifa_591000",
}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("investra_fund")
    def _get_investra_fund_template_data(self):
        return {"name": "Investra fond (pracovní návrh)", "country": "cz", "code_digits": "6"}

    @template("investra_fund", "res.company")
    def _get_investra_fund_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.cz",
                "bank_account_code_prefix": "2211",
                "cash_account_code_prefix": "2111",
                "transfer_account_code_prefix": "2611",
                "income_currency_exchange_account_id": "ifa_663000",
                "expense_currency_exchange_account_id": "ifa_563000",
                "account_journal_suspense_account_id": "ifa_261000",
                "receivable_account_id": "ifa_311000",
                "payable_account_id": "ifa_321000",
                "income_account_id": "ifa_668000",
                "expense_account_id": "ifa_548000",
            },
        }
