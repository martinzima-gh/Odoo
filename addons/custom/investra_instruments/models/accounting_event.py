"""ZJ-09 A2: třída portfolia na řádcích dokladů – jedno místo pro obchody, splátky, ocenění i deriváty.

Plán: docs/ukoly/podklady/zadani-davka-ZJ-07-az-19.md, oddíl 2.2 (A2) a 2.3. Sdílené portfolio (bez třídy) doklady nemění,
otisk existujících dokladů zůstává stejný.
"""
from decimal import Decimal

from odoo import api, models

# Peníze zůstávají sdílené (banka bez třídy; bankovní účet třídy je ZJ-09 bod 2b, později).
MONEY_ROLES = {"bank", "cash_in_transit", "cash_in_transit_receipt", "unidentified_payment"}


class InvestraAccountingEvent(models.Model):
    _inherit = "investra.accounting.event"

    @api.model
    def _create_event(self, company, key, name, date, event_type, lines, journal=None, source=None):
        return super()._create_event(company, key, name, date, event_type,
                                     self._portfolio_class_lines(company, lines, source), journal=journal, source=source)

    @api.model
    def _portfolio_class_lines(self, company, lines, source=None):
        """Doplní třídu portfolia na řádky dokladu a vyrovná ji vnitřním zúčtováním.

        (1) Řádek se zařazením (extra.investra_classification_id) dostane třídu jeho portfolia.
        (2) Zdroj s portfoliem třídy (obchod, splátka, derivát): třídu dostanou i ostatní řádky bez zařazení kromě peněz
            (poplatek, protiúčet nevypořádaného obchodu, podrozvaha). Odchylka od plánu A2: plán bral „jedinou třídu
            v dokladu“; v dokladu ocenění (všechny pozice v jednom dokladu) by tak dostaly třídu i řádky bez zařazení ze
            sdíleného portfolia (např. přecenění derivátu sdíleného portfolia). Zdroj ocenění portfolio nemá, platí jen (1).
        (3) Peníze zůstávají sdílené: součet řádků s doplněnou třídou se vyrovná vnitřním zúčtováním třída ↔ fond.
        Řádky, kde volající třídu uvedl (klíč class_id, i prázdný – úplaty, přesuny mezi třídami), se nemění.
        Bez portfolia třídy vrací řádky beze změny (otisk stejný jako dřív).
        """
        Classification = self.env["investra.portfolio.classification"].sudo()
        source_class = False
        if source is not None and "portfolio_id" in source._fields:
            source_class = source.sudo().portfolio_id.class_id
        result, assigned = [], []
        for line in lines:
            if "class_id" in line or line.get("role") in MONEY_ROLES:
                result.append(line)
                continue
            cid = (line.get("extra") or {}).get("investra_classification_id")
            fund_class = Classification.browse(cid).portfolio_id.class_id if cid else source_class
            if not fund_class:
                result.append(line)
                continue
            line = {**line, "class_id": fund_class.id}
            result.append(line)
            assigned.append(line)
        if not assigned:
            return list(lines)
        round_ = company.currency_id.round
        totals = {}
        for line in assigned:
            totals[line["class_id"]] = totals.get(line["class_id"], Decimal(0)) + Decimal(str(round_(float(line["amount"]))))
        for class_id, total in totals.items():
            if total:
                result += [
                    {"role": "internal_clearing", "amount": str(-total), "class_id": class_id, "movement_type": "class_transfer"},
                    {"role": "internal_clearing", "amount": str(total), "class_id": False, "movement_type": "class_transfer"},
                ]
        return result
