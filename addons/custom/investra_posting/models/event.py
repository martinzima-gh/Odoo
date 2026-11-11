import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import UserError

# Klíč služby: objekt v paměti procesu, přes API ani kontext z prohlížeče ho nejde předat.
SERVICE = object()

MOVEMENT_TYPES = [
    ("transaction", "Transakce"),
    ("price_revaluation", "Přecenění cenou"),
    ("fx_revaluation", "Přecenění kurzem"),
    ("accrued_interest", "Naběhlý úrok"),
    ("subscription", "Úpis"),
    ("redemption", "Odkup"),
    ("dividend", "Dividenda"),
    ("fee", "Úplata"),
    ("class_transfer", "Přesun mezi třídami"),
    ("other", "Ostatní změna"),
]


EVENT_TYPES = [
    ("trade", "Obchod"),
    ("trade_settlement", "Vypořádání obchodu"),
    ("class_movement", "Úpis/odkup"),
    ("repayment", "Splátka"),
    ("valuation", "Ocenění"),
    ("fx", "Konverze měn"),
    ("other", "Ostatní"),
]


class InvestraAccountingEvent(models.Model):
    """Událost, ze které vzniká právě jeden doklad. Metody jsou neveřejné, volá je jen kód modulů."""

    _name = "investra.accounting.event"
    _description = "Účetní událost"
    _order = "date desc, id desc"

    name = fields.Char(required=True, readonly=True, string="Název")
    company_id = fields.Many2one("res.company", required=True, readonly=True, index=True, string="Společnost")
    date = fields.Date(required=True, readonly=True, string="Datum")
    event_type = fields.Selection(EVENT_TYPES, required=True, readonly=True, string="Druh události")
    fund_id = fields.Many2one("investra.fund", readonly=True, index=True, ondelete="restrict", string="Fond")
    res_model = fields.Char(readonly=True, string="Model zdroje")
    res_id = fields.Many2oneReference(model_field="res_model", readonly=True, string="Id zdroje")
    source_name = fields.Char(compute="_compute_source_name", string="Zdroj")
    currency_id = fields.Many2one(related="company_id.currency_id", store=True, string="Měna")
    amount = fields.Monetary(readonly=True, currency_field="currency_id", string="Částka",
                             help="Součet MD dokladu ve funkční měně knihy.")
    foreign_currency_id = fields.Many2one("res.currency", readonly=True, string="Původní měna")
    amount_currency = fields.Monetary(readonly=True, currency_field="foreign_currency_id", string="Částka v původní měně",
                                      help="Jen když mají všechny řádky s cizí měnou jednu měnu.")
    move_line_ids = fields.One2many(related="move_id.line_ids", string="Řádky dokladu")
    key = fields.Char(required=True, readonly=True, help="Klíč proti dvojímu zaúčtování.", string="Klíč")
    fingerprint = fields.Char(required=True, readonly=True, string="Otisk")
    move_id = fields.Many2one("account.move", readonly=True, ondelete="restrict", string="Doklad")
    reversal_move_id = fields.Many2one("account.move", readonly=True, ondelete="restrict", string="Storno doklad")
    state = fields.Selection(
        [
            ("draft", "Návrh"),
            ("locked", "Zamčený návrh"),
            ("posted", "Zaúčtováno"),
            ("reversed", "Stornováno"),
            ("discarded", "Zrušený návrh"),
        ],
        default="draft",
        required=True,
        readonly=True,
        string="Stav",
    )

    _company_key_uniq = models.Constraint("unique(company_id, key)", "Událost s tímto klíčem už existuje.")

    @api.depends("res_model", "res_id")
    def _compute_source_name(self):
        for event in self:
            source = event._source()
            event.source_name = source.sudo().display_name if source else False

    def _source(self):
        """Zdrojový záznam události, nebo None (zdroj neznámý nebo smazaný)."""
        self.ensure_one()
        if not self.res_model or not self.res_id or self.res_model not in self.env:
            return None
        return self.env[self.res_model].browse(self.res_id).exists() or None

    def action_open_source(self):
        self.ensure_one()
        source = self._source()
        if not source:
            raise UserError(self.env._("Událost %s nemá dostupný zdroj.", self.name))
        return {"type": "ir.actions.act_window", "res_model": source._name, "res_id": source.id, "views": [(False, "form")]}

    def action_open_move(self):
        self.ensure_one()
        if not self.move_id:
            raise UserError(self.env._("Událost %s nemá doklad.", self.name))
        return {"type": "ir.actions.act_window", "res_model": "account.move", "res_id": self.move_id.id, "views": [(False, "form")]}

    @api.model
    def _amounts(self, company, lines):
        """Částka ve funkční měně (součet MD) a částka v původní měně, je-li cizí měna jen jedna.

        V původní měně se bere větší ze součtu kladných a absolutní hodnoty součtu záporných částek
        (u odkupu má měnu jen řádek banky na straně D).
        """
        amount = sum(
            company.currency_id.round(float(line["amount"])) for line in lines
            if company.currency_id.round(float(line["amount"])) > 0
        )
        foreign = {line["currency_id"] for line in lines if line.get("currency_id") and line["currency_id"] != company.currency_id.id}
        if len(foreign) != 1:
            return amount, False, False
        currency_id = foreign.pop()
        values = [float(line["amount_currency"]) for line in lines if line.get("currency_id") == currency_id]
        foreign_amount = max(sum(v for v in values if v > 0), -sum(v for v in values if v < 0))
        if not foreign_amount:
            return amount, False, False
        return amount, currency_id, foreign_amount

    @api.model
    def _fingerprint(self, date, lines):
        payload = [
            sorted((k, str(v)) for k, v in line.items())
            for line in sorted(lines, key=lambda line: json.dumps(line, sort_keys=True, default=str))
        ]
        return hashlib.sha256(json.dumps([str(date), payload]).encode()).hexdigest()

    @api.model
    def _create_event(self, company, key, name, date, event_type, lines, journal=None, source=None):
        """Vytvoří návrh dokladu z řádků podle rolí účtů.

        Řádek: role, amount (kladně MD, záporně D), případně class_id, movement_type, name, partner_id,
        amount_currency a currency_id. Stejný klíč se stejným obsahem vrátí původní událost,
        s jiným obsahem je chyba. Zdroj (source) je záznam, ze kterého událost vzniká; má-li fond, převezme se.
        Zdroj ani druh nejsou součástí otisku.
        """
        fingerprint = self._fingerprint(date, lines)
        existing = self.sudo().search([("company_id", "=", company.id), ("key", "=", key)], limit=1)
        if existing:
            if existing.fingerprint != fingerprint:
                raise UserError(self.env._("Událost %s už existuje s jiným obsahem.", key))
            return existing
        role = self.env["investra.account.role"]
        journal = journal or self.env["account.journal"].sudo().search(
            [("company_id", "=", company.id), ("type", "=", "general")], limit=1
        )
        if not journal:
            raise UserError(self.env._("Kniha %s nemá deník ostatních operací.", company.name))
        commands = []
        for line in lines:
            amount = company.currency_id.round(float(line["amount"]))
            values = {
                "account_id": role.account_for(company, line["role"]).id,
                "name": line.get("name") or name,
                "balance": amount,
                "investra_class_id": line.get("class_id"),
                "investra_part": line.get("part", "investment"),
                "investra_movement_type": line.get("movement_type", "other"),
                "partner_id": line.get("partner_id"),
            }
            if line.get("currency_id"):
                values.update(currency_id=line["currency_id"], amount_currency=float(line["amount_currency"]))
            values.update(line.get("extra", {}))
            commands.append((0, 0, values))
        amount, foreign_currency_id, amount_currency = self._amounts(company, lines)
        source_values = {}
        if source:
            source.ensure_one()
            source_values = {"res_model": source._name, "res_id": source.id}
            if "fund_id" in source._fields:
                source_values["fund_id"] = source.sudo().fund_id.id
        service = self.sudo().with_company(company).with_context(investra_service=SERVICE)
        event = service.create({
            "name": name,
            "company_id": company.id,
            "date": date,
            "event_type": event_type,
            "key": key,
            "fingerprint": fingerprint,
            "amount": amount,
            "foreign_currency_id": foreign_currency_id,
            "amount_currency": amount_currency,
            **source_values,
        })
        move = service.env["account.move"].create({
            "journal_id": journal.id,
            "date": date,
            "ref": name,
            "move_type": "entry",
            "line_ids": commands,
            "investra_event_id": event.id,
        })
        event.move_id = move
        return event.with_env(self.env)

    def _service(self):
        return self.sudo().with_context(investra_service=SERVICE)

    def _lock_events(self):
        for event in self._service():
            if event.state != "draft":
                raise UserError(self.env._("Událost %s není návrh.", event.name))
            event.state = "locked"
            event.move_id.investra_locked = True

    def _post_events(self):
        for event in self._service():
            if event.state != "locked":
                raise UserError(self.env._("Zaúčtovat lze jen zamčený návrh: %s.", event.name))
            move = event.move_id.with_company(event.company_id)
            move.investra_locked = False
            move._post(soft=False)
            if move.state != "posted" or move.date != event.date:
                raise UserError(self.env._("Doklad %s se nezaúčtoval k datu události.", event.name))
            event.state = "posted"

    def _reverse_events(self):
        """Storno se stejným datem jako původní doklad; v uzamčeném období skončí chybou."""
        for event in self._service():
            if event.state != "posted":
                raise UserError(self.env._("Stornovat lze jen zaúčtovanou událost: %s.", event.name))
            original = event.move_id.with_company(event.company_id)
            reversal = original._reverse_moves(
                [{"date": event.date, "ref": f"Storno: {event.name}", "investra_event_id": event.id}],
                cancel=True,
            )
            if reversal.date != event.date:
                raise UserError(self.env._("Storno %s by změnilo datum.", event.name))
            event.write({"reversal_move_id": reversal.id, "state": "reversed"})

    def _discard_events(self):
        """Zruší návrhy nové verze ocenění bez storen: doklad nebyl nikdy zaúčtován."""
        for event in self._service():
            if event.state not in ("draft", "locked"):
                raise UserError(self.env._("Zrušit lze jen návrh: %s.", event.name))
            move = event.move_id
            event.write({"move_id": False, "state": "discarded", "key": f"{event.key}#discarded{event.id}"})
            move.investra_locked = False
            move.unlink()
