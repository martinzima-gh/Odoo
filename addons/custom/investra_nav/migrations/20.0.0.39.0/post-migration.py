"""Dávka ZJ-07 až ZJ-19: dividendy a ex-kupón (ZJ-19) a daňová pravidla (ZJ-07, oddíl 9.3 C5).

1. Do profilů přecenění stávajících fondů přidá účty pohledávek z dividend (341210) a ze zahraniční daně k vrácení (341220), pokud
   je kniha má (účty doplňuje migrace investra_chart_fund 20.0.0.13.0, která běží dřív). Nový fond je dostane při založení profilu.
2. Sazby nosičů daně (pravidlo úplaty druhu Očekávaná daň) → sdílená daňová pravidla: všechny verze 5 % → „Daň ZIF 5 %“, všechny
   21 % → „Daň 21 %“, jinak nové pravidlo „Daň <fond>“ se stejnými verzemi a účty 681000/347000. Totéž nové pravidlo i tehdy,
   když fond má ocenění s daní před začátkem platnosti standardního pravidla (1. 1. 2024). Aktivní nosič nastaví fondu výchozí
   pravidlo; opravy daně nosiče bez pravidla dostanou výchozí pravidlo fondu. Nosič bez verze sazby se přeskočí (fond zůstane bez
   výchozího pravidla, ocenění na to upozorní). Verze nosiče zůstávají jako historie, výpočet je nečte.
Doklady ani dřívější ocenění se nemění; bez výjimek počítá výpočet daně stejně jako dosud. Opakovatelné (fond s výchozím pravidlem
se přeskočí). Pojistka jako investra_chart_fund 20.0.0.9.0: ocenění Ke schválení nebo Schváleno migraci zastaví.
"""
import logging

from odoo import SUPERUSER_ID, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

DIVIDEND_RECEIVABLE_CODES = ("341210", "341220")


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _dividend_receivables(env)
    _tax_rules(env)


def _dividend_receivables(env):
    Mapping = env["investra.role.account"]
    for profile in env["investra.fx.profile"].with_context(active_test=False).search([("fund_id", "!=", False)]):
        mapping = Mapping.search([("company_id", "=", profile.company_id.id), ("role_id.code", "=", "receivable_other")], limit=1)
        accounts = mapping.extra_account_ids.filtered(lambda a: a.code in DIVIDEND_RECEIVABLE_CODES) - profile.account_ids
        if accounts:
            profile.with_context(tracking_disable=True).account_ids = [(4, account.id) for account in accounts]


def _tax_rules(env):
    busy = env["investra.valuation"].search([("state", "in", ("submitted", "approved"))]).ids
    if busy:
        raise UserError(
            "Migraci nejde spustit: ocenění ve stavu Ke schválení nebo Schváleno (id %s); "
            "ocenění nejdřív vraťte nebo zaúčtujte." % ", ".join(map(str, busy))
        )
    standard = {0.21: env.ref("investra_nav.tax_rule_21"), 0.05: env.ref("investra_nav.tax_rule_zif_5")}
    Carrier = env["investra.fee.rule"].with_context(active_test=False, investra_tax_carrier=True, tracking_disable=True)
    for carrier in Carrier.search([("kind", "=", "tax")], order="id"):
        fund = carrier.fund_id.with_context(investra_tax_carrier=True, tracking_disable=True)
        if fund.tax_rule_id:
            continue
        versions = carrier.version_ids.sorted("valid_from")
        if not versions:
            _logger.warning("ZJ-07: nosič daně %s fondu %s nemá sazbu, fond zůstává bez výchozího pravidla.", carrier.id, fund.name)
            continue
        rates = {round(version.rate, 6) for version in versions}
        tax_rule = standard.get(next(iter(rates))) if len(rates) == 1 else None
        if tax_rule:
            start = tax_rule.version_ids.sorted("valid_from")[:1].valid_from
            earlier = env["investra.valuation.fee"].search_count([
                ("rule_id", "=", carrier.id), ("valuation_id.date", "<", start)], limit=1)
            if earlier:
                tax_rule = None
        if not tax_rule:
            tax_rule = env["investra.tax.rule"].with_context(tracking_disable=True).create({
                "name": f"Daň {fund.name}", "kind": "general", "method": "current",
                "tax_account_code": "681000", "balance_account_code": "347000",
                "note": "Založeno migrací ZJ-07 ze sazeb dosavadního pravidla Očekávaná daň.",
                "version_ids": [(0, 0, {"valid_from": v.valid_from, "rate": v.rate, "decision_ref": v.decision_ref or False})
                                for v in versions],
            })
        if not carrier.active:
            _logger.info("ZJ-07: nosič daně %s fondu %s je archivovaný, výchozí pravidlo se nenastaví.", carrier.id, fund.name)
            continue
        fund.tax_rule_id = tax_rule
        corrections = env["investra.valuation.external"].search(
            [("corrects_rule_id", "=", carrier.id), ("tax_rule_id", "=", False)])
        if corrections:
            corrections.write({"tax_rule_id": tax_rule.id})
        _logger.info("ZJ-07: fond %s → výchozí daňové pravidlo %s (oprav daně %s).", fund.name, tax_rule.name, len(corrections))
