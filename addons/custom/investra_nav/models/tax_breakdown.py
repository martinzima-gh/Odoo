"""Rozpad daně ocenění po daňových pravidlech (ZJ-07, oddíl 9.2 C4 a 9.1 E).

Krátká tabulka z detailu řádku daně (`rules`, zapisuje `valuation._book_tax`): pravidlo | základ | sazba | požadovaná | zaúčtovaná |
pohyb; nulové řádky skryté; u výchozího pravidla rozbalení (výsledek od začátku účetního období, výjimky, neuznatelné náklady, krok,
opravy základu) a u pravidla se zápočtem zápočet a propadlý zápočet. Jen zobrazení: nic nepočítá ani neúčtuje.
"""
import json
from decimal import Decimal

from markupsafe import Markup, escape

from odoo import api, fields, models


def _fmt(value):
    number = Decimal(str(value or 0))
    return f"{number:,.2f}".replace(",", " ").replace(".", ",")


def _pct(value):
    number = Decimal(str(value or 0)) * 100
    return f"{number.normalize():f}".replace(".", ",") + " %"


class InvestraValuationTaxBreakdown(models.Model):
    _inherit = "investra.valuation"

    tax_breakdown_html = fields.Html(compute="_compute_tax_breakdown_html", sanitize=False, string="Rozpad daně",
                                     help="Daň po daňových pravidlech fondu z detailu řádku daně (ZJ-07).")

    @api.depends("fee_line_ids.detail")
    def _compute_tax_breakdown_html(self):
        for valuation in self:
            line = valuation.fee_line_ids.filtered(lambda l: l.rule_id.kind == "tax")[:1]
            detail = json.loads(line.detail or "{}") if line else {}
            valuation.tax_breakdown_html = valuation._tax_breakdown(detail) if detail.get("rules") else False

    def _used_exceptions(self, exceptions):
        """Výjimky s nenulovým pohybem na účtu od začátku účetního období (jen zobrazení; detail řádku daně pohyb neukládá)."""
        if not exceptions:
            return []
        year_start = self.fund_id._fiscal_year_start(self.date)
        used = []
        for exception in exceptions:
            account = self.env["account.account"].sudo().search(
                [("code", "=", exception.get("account")), ("company_ids", "in", self.company_id.id)], limit=1)
            if account and self._sum(("account_id", "=", account.id), ("date", ">=", year_start)):
                used.append(exception)
        return used

    def _tax_breakdown(self, detail):
        _ = self.env._
        head = (_("Pravidlo"), _("Základ"), _("Sazba"), _("Požadovaná"), _("Zaúčtovaná"), _("Pohyb"))
        body = []
        for row in detail["rules"]:
            values = [Decimal(row.get(key) or 0) for key in ("base", "required", "booked", "move")]
            if not any(values) and not row.get("default"):
                continue
            body.append(Markup("<tr><td>%s</td><td class='text-end'>%s</td><td class='text-end'>%s</td><td class='text-end'>%s</td>"
                               "<td class='text-end'>%s</td><td class='text-end'>%s</td></tr>") % (
                row.get("name"), _fmt(row.get("base")), _pct(row.get("rate")), _fmt(row.get("required")),
                _fmt(row.get("booked")), _fmt(row.get("move"))))
            notes = []
            if row.get("default"):
                # ZJ-25 1.4: jedna věta jako výpočet základu (výsledek − výjimky + neuznatelné = základ · krok).
                notes.append(_(
                    "výsledek od zač. období %(result)s − výjimky %(excluded)s + neuznatelné %(nondeductible)s = základ %(base)s · po kroku %(step)s",
                    result=_fmt(row.get("result")), excluded=_fmt(row.get("excluded")), nondeductible=_fmt(row.get("nondeductible")),
                    base=_fmt(row.get("base")), step=detail.get("base_step") or "–"))
            if Decimal(row.get("base_correction") or 0):
                notes.append(_("oprava základu %s", _fmt(row.get("base_correction"))))
            if Decimal(row.get("carried") or 0):
                notes.append(_("převzaté opravy daně %s", _fmt(row.get("carried"))))
            if Decimal(row.get("credit") or 0):
                notes.append(_("zápočet %(credit)s, použito %(used)s, propadá %(lost)s", credit=_fmt(row.get("credit")),
                               used=_fmt(row.get("credit_used")), lost=_fmt(row.get("credit_lost"))))
            if notes:
                body.append(Markup("<tr><td colspan='6' class='text-muted small ps-4'>%s</td></tr>") % escape("; ".join(notes)))
        if not body:
            return False
        exceptions = self._used_exceptions(detail.get("exceptions") or [])
        extra = Markup("")
        if exceptions:
            items = Markup("").join(
                Markup("<li>%s %s → %s%s%s</li>") % (
                    e.get("account"), e.get("name"), e.get("rule_name"),
                    escape(_(", podíl %s", _pct(e.get("share")))) if Decimal(e.get("share") or 1) != 1 else "",
                    escape(_(", neuznatelné %s %% z výnosu", e.get("nondeductible_pct"))) if Decimal(e.get("nondeductible_pct") or 0) else "")
                for e in exceptions)
            # Jen výjimky s pohybem na účtu od začátku účetního období; ostatní jsou k dispozici ve formuláři fondu.
            extra = Markup("<details class='small'><summary>%s</summary><ul>%s</ul></details>") % (
                _("▸ Použité výjimky (%s)", len(exceptions)), items)
        return Markup(
            "<table class='table table-sm'><thead><tr><th>%s</th><th class='text-end'>%s</th><th class='text-end'>%s</th>"
            "<th class='text-end'>%s</th><th class='text-end'>%s</th><th class='text-end'>%s</th></tr></thead><tbody>%s</tbody>"
            "</table>%s") % (*head, Markup("").join(body), extra)
