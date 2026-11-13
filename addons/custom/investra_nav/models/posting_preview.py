"""Společný náhled zaúčtování (rozhodnutí 2026-11-13 „Náhled zaúčtování u splátek, úpisů a odkupů“, varianta A).

Záložka Zaúčtování: před zaúčtováním náhled dokladů ze stejné funkce, která účtuje, po zaúčtování skutečné doklady
včetně storen dohledané podle zdroje. Obchod, splátka nástroje i úpis/odkup dědí tento model a dodávají jen své doklady.
Kód tabulky a dohledání dokladů je přesunutý 1:1 z náhledu obchodu (`trade_preview.py`).
"""
from decimal import Decimal

from markupsafe import Markup

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import format_date, formatLang


def d(value):
    return Decimal(str(value or 0))


class InvestraPostingPreview(models.AbstractModel):
    _name = "investra.posting.preview"
    _description = "Náhled zaúčtování"

    posting_preview = fields.Html(
        compute="_compute_posting_preview", sanitize=False, string="Zaúčtování",
        help="Zaúčtované doklady včetně storen; u návrhu náhled dokladů, které vzniknou.",
    )

    def _compute_posting_preview(self):
        # Modely, které náhled dědí, přepisují tuto metodu jen kvůli @api.depends.
        for record in self:
            record.posting_preview = record._posting_preview_html()

    # --- co dodává konkrétní model ----------------------------------------------------------------------

    def _ready_for_preview(self):
        """Má záznam vyplněno vše, co náhled potřebuje?"""
        return False

    def _preview_documents(self):
        """[(nadpis, datum, [(účet, MD, D, částka v měně)])] z téže funkce, kterou účtuje zaúčtování."""
        return []

    def _preview_intro(self):
        return self.env._("Jen náhled: nic se neúčtuje. Doklad vznikne tlačítkem Zaúčtovat.")

    def _preview_extra_html(self, money):
        """Doplněk pod náhledem dokladů (u obchodu očekávaný výsledek prodeje)."""
        return Markup()

    def _preview_currency(self):
        """Cizí měna dokladu (sloupec V měně), nebo prázdná měna."""
        return self.env["res.currency"]

    def _booked_intro(self):
        return self.env._("Zaúčtované doklady.")

    def _booked_caption(self, event):
        return event.name

    # --- společné ---------------------------------------------------------------------------------------

    def _preview_rows(self, lines):
        """Řádky pro náhled z řádků pro `_create_event`; účet podle role stejně jako při vzniku dokladu."""
        Role = self.env["investra.account.role"]
        rows = []
        for line in lines:
            account = Role.account_for(self.company_id, line["role"])
            amount = d(line["amount"])
            label = line.get("name") or ""
            rows.append((account.display_name + (f" ({label})" if label else ""),
                         amount if amount > 0 else Decimal(0), -amount if amount < 0 else Decimal(0),
                         line.get("amount_currency")))
        return rows

    def _booked_documents(self):
        """Skutečně zaúčtované doklady záznamu ve stejném tvaru jako náhled, včetně stornovaných událostí."""
        self.ensure_one()
        documents = []
        events = self.env["investra.accounting.event"]
        if self._origin.id:
            events = events.sudo().search([
                ("res_model", "=", self._name), ("res_id", "=", self._origin.id), ("move_id", "!=", False),
            ], order="date, id")
        for event in events:
            caption = self._booked_caption(event)
            move = event.move_id
            if not move:
                continue
            # Odchylka od náhledu obchodu (2026-11-13): částka v měně jen u řádku v cizí měně. Řádek ve funkční měně
            # má v Odoo amount_currency = zůstatek v CZK a sloupec „V měně EUR“ by ho ukázal jako eura.
            rows = [(line.account_id.display_name + (f" ({line.name})" if line.name and line.name != event.name else ""),
                     d(line.debit), d(line.credit),
                     line.amount_currency if line.currency_id != line.company_currency_id else None)
                    for line in move.line_ids]
            label = f"{caption} {move.name}"
            if event.state == "reversed":
                label += " " + self.env._("(stornováno dokladem %s)", event.reversal_move_id.name)
            documents.append((label, move.date, rows))
        return documents

    def _documents_html(self, documents, money):
        foreign = self._preview_currency()
        head = Markup("<th>%s</th><th class='text-end'>%s</th><th class='text-end'>%s</th>") % (
            self.env._("Účet"), self.env._("MD"), self.env._("D"))
        if foreign:
            head += Markup("<th class='text-end'>%s</th>") % self.env._("V měně %s", foreign.name)
        parts = []
        for caption, day, rows in documents:
            parts.append(Markup("<h5>%s – %s</h5>") % (caption, format_date(self.env, day) if day else "?"))
            body = Markup()
            for account, debit, credit, amount_currency in rows:
                cells = Markup("<td>%s</td><td class='text-end'>%s</td><td class='text-end'>%s</td>") % (
                    account, money(debit), money(credit))
                if foreign:
                    cells += Markup("<td class='text-end'>%s</td>") % money(d(amount_currency))
                body += Markup("<tr>%s</tr>") % cells
            parts.append(Markup('<table class="table table-sm o_investra_preview"><thead><tr>%s</tr></thead>'
                                '<tbody>%s</tbody></table>') % (head, body))
        return Markup().join(parts)

    def _posting_preview_html(self):
        self.ensure_one()
        money = lambda value: formatLang(self.env, float(value), digits=2) if value else ""
        parts = []
        booked = self._booked_documents()
        if booked:
            parts.append(Markup('<p class="text-muted">%s</p>') % self._booked_intro())
            parts.append(self._documents_html(booked, money))
        if not self._ready_for_preview():
            return Markup().join(parts) if parts else False
        try:
            documents = self._preview_documents()
            extra = self._preview_extra_html(money)
        except UserError as error:
            parts.append(Markup('<div class="alert alert-warning" role="alert">%s</div>') % error.args[0])
            return Markup().join(parts)
        parts.append(Markup('<p class="text-muted">%s</p>') % self._preview_intro())
        parts.append(self._documents_html(documents, money))
        if extra:
            parts.append(extra)
        return Markup().join(parts)
