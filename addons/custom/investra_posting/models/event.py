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


class InvestraAccountingEvent(models.Model):
    """Událost, ze které vzniká právě jeden doklad. Metody jsou neveřejné, volá je jen kód modulů."""

    _name = "investra.accounting.event"
    _description = "Účetní událost"
    _order = "date desc, id desc"

    name = fields.Char(required=True, readonly=True, string="Název")
    company_id = fields.Many2one("res.company", required=True, readonly=True, index=True, string="Společnost")
    date = fields.Date(required=True, readonly=True, string="Datum")
    event_type = fields.Char(required=True, readonly=True, string="Druh události")
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

    @api.model
    def _fingerprint(self, date, lines):
        payload = [
            sorted((k, str(v)) for k, v in line.items())
            for line in sorted(lines, key=lambda line: json.dumps(line, sort_keys=True, default=str))
        ]
        return hashlib.sha256(json.dumps([str(date), payload]).encode()).hexdigest()

    @api.model
    def _create_event(self, company, key, name, date, event_type, lines, journal=None):
        """Vytvoří návrh dokladu z řádků podle rolí účtů.

        Řádek: role, amount (kladně MD, záporně D), případně class_id, movement_type, name, partner_id,
        amount_currency a currency_id. Stejný klíč se stejným obsahem vrátí původní událost,
        s jiným obsahem je chyba.
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
        service = self.sudo().with_company(company).with_context(investra_service=SERVICE)
        event = service.create({
            "name": name,
            "company_id": company.id,
            "date": date,
            "event_type": event_type,
            "key": key,
            "fingerprint": fingerprint,
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
