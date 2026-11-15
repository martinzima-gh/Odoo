import csv
import io
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

STATES = [
    ("new", "Nový"), ("renamed", "Změněný název"), ("same", "Beze změny"),
    ("missing", "Chybí v nové verzi"), ("conflict", "Konflikt"),
]
DEFAULT_DOMAIN = {"esa": "D_S_RNBD_4", "ba0088": "BA0088"}


class InvestraCodelistImportWizard(models.TransientModel):
    _name = "investra.codelist.import.wizard"
    _description = "Import číselníku"

    target = fields.Selection([("ba0088", "Druhy CP (BA0088)"), ("esa", "Sektory ESA (D_S_RNBD_4)")],
                              "Cílový číselník", required=True, default="ba0088")
    file = fields.Binary("Soubor CSV")
    filename = fields.Char("Název souboru")
    domain_code = fields.Char("Doména", help="Jen pro soubor ve formátu domena;nazev_domeny_nebo_hierarchie;kod;hodnota.")
    methodology = fields.Char("Metodika", required=True, help="Např. FOFI20261201 / D_S_RNBD_4 v004.000")
    valid_from = fields.Date("Platí od", required=True, default=fields.Date.context_today)
    state = fields.Selection([("upload", "Soubor"), ("preview", "Náhled"), ("done", "Hotovo")], default="upload")
    line_ids = fields.One2many("investra.codelist.import.line", "wizard_id", "Řádky")
    result = fields.Text("Výsledek", readonly=True)

    @api.onchange("target")
    def _onchange_target(self):
        self.domain_code = DEFAULT_DOMAIN[self.target]

    def _check_manager(self):
        if not self.env.su and not self.env.user.has_group("investra_instrument_master.group_codelist_manager"):
            raise UserError(self.env._("Číselníky smí importovat jen správce číselníků."))

    def _model(self):
        return self.env["investra.ba0088.code" if self.target == "ba0088" else "investra.esa.code"]

    def _parse(self):
        """Vrátí {kód: název}. Formát domény ČNB (domena;…;kod;hodnota) nebo katalog BA0088 (…;typ;kod;nazev)."""
        if not self.file:
            raise UserError(self.env._("Nahrajte soubor CSV."))
        try:
            text = self.file.content.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise UserError(self.env._("Soubor musí být v kódování UTF-8."))
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
        fields_ = set(reader.fieldnames or [])
        rows = {}
        if {"domena", "kod", "hodnota"} <= fields_:
            domain = (self.domain_code or DEFAULT_DOMAIN[self.target]).strip()
            seen = False
            for row in reader:
                if row["domena"] != domain:
                    continue
                seen = True
                code, name = (row["kod"] or "").strip(), (row["hodnota"] or "").strip()
                if not code or code.startswith("S_") or name == "(souhrnná položka)":
                    continue
                rows[code] = name
            if not seen:
                raise UserError(self.env._("V souboru není doména %s.", domain))
        elif {"kod", "nazev", "typ"} <= fields_:
            for row in reader:
                if (row["typ"] or "").strip() != "polozka":
                    continue
                rows[row["kod"].strip()] = (row["nazev"] or "").strip()
        else:
            raise UserError(self.env._("Neznámý formát souboru: očekává se domena;nazev_domeny_nebo_hierarchie;kod;hodnota."))
        rows = {code: name for code, name in rows.items() if code and name}
        if not rows:
            raise UserError(self.env._("V souboru nejsou žádné položky."))
        return rows

    def _reopen(self):
        return {"type": "ir.actions.act_window", "res_model": self._name, "res_id": self.id,
                "view_mode": "form", "target": "new"}

    def action_preview(self):
        self.ensure_one()
        self._check_manager()
        rows = self._parse()
        existing = {rec.code: rec for rec in self._model().with_context(active_test=False).search([])}
        lines = []
        for code, name in sorted(rows.items()):
            rec = existing.get(code)
            if not rec:
                state = "new"
            elif rec.name == name:
                state = "same"
            elif rec.locally_modified:
                state = "conflict"
            else:
                state = "renamed"
            lines.append({"code": code, "name": name, "current_name": rec.name if rec else False, "state": state,
                          "res_id": rec.id if rec else 0, "apply": state in ("new", "renamed")})
        for code, rec in sorted(existing.items()):
            if code not in rows:
                # Kód, který už má platnost ukončenou, se znovu nenavrhuje (druhý import nic nemění).
                state = "same" if rec.valid_to else "missing"
                lines.append({"code": code, "name": False, "current_name": rec.name, "state": state,
                              "res_id": rec.id, "apply": state == "missing"})
        self.line_ids.unlink()
        self.write({"line_ids": [(0, 0, vals) for vals in lines], "state": "preview"})
        return self._reopen()

    def action_back(self):
        self.ensure_one()
        self.write({"state": "upload"})
        return self._reopen()

    def action_apply(self):
        self.ensure_one()
        self._check_manager()
        if self.state != "preview":
            raise UserError(self.env._("Nejdřív zobrazte náhled."))
        selected = self.line_ids.filtered(lambda l: l.apply and l.state in ("new", "renamed", "missing"))
        if self.target == "esa":
            incomplete = selected.filtered(lambda l: l.state == "new" and not l.aggregate_sector_id)
            if incomplete:
                raise UserError(self.env._(
                    "U nových kódů ESA doplňte typ emitenta: %s.", ", ".join(incomplete.mapped("code"))))
            unknown = selected.filtered(lambda l: l.state == "new" and l.code[:1] not in ("1", "2"))
            if unknown:
                raise UserError(self.env._(
                    "Kód ESA musí začínat 1 (rezident) nebo 2 (nerezident): %s.", ", ".join(unknown.mapped("code"))))
        model = self._model().with_context(investra_codelist_import=True, active_test=False)
        all_codes = set(self.line_ids.filtered(lambda l: l.state != "missing").mapped("code")) | set(
            model.search([]).mapped("code"))
        end = self.valid_from - timedelta(days=1)
        counts = {"new": 0, "renamed": 0, "missing": 0}
        for line in selected:
            if line.state == "new":
                vals = {"code": line.code, "name": line.name, "valid_from": self.valid_from,
                        "source_methodology": self.methodology}
                if self.target == "esa":
                    vals.update(residency="r" if line.code[:1] == "1" else "nr",
                                aggregate_sector_id=line.aggregate_sector_id.id)
                else:
                    parents = [c for c in all_codes if c != line.code and line.code.startswith(c)]
                    vals["parent_code"] = max(parents, key=len) if parents else False
                model.create(vals)
            elif line.state == "renamed":
                model.browse(line.res_id).write({"name": line.name, "source_methodology": self.methodology})
            else:
                model.browse(line.res_id).write({"valid_to": end})
            counts[line.state] += 1
        conflicts = self.line_ids.filtered(lambda l: l.state == "conflict")
        text = self.env._(
            "Nových: %(new)s, změněných názvů: %(renamed)s, kódů s ukončenou platností (od %(end)s): %(missing)s. "
            "Nic se nemazalo.", new=counts["new"], renamed=counts["renamed"], missing=counts["missing"], end=end)
        if conflicts:
            text += "\n" + self.env._("Konflikty (ručně upravené, nepřepsáno): %s.", ", ".join(conflicts.mapped("code")))
        self.write({"state": "done", "result": text})
        return self._reopen()


class InvestraCodelistImportLine(models.TransientModel):
    _name = "investra.codelist.import.line"
    _description = "Řádek importu číselníku"
    _order = "state_order, code"

    wizard_id = fields.Many2one("investra.codelist.import.wizard", required=True, ondelete="cascade")
    code = fields.Char("Kód", readonly=True)
    name = fields.Char("Nový název", readonly=True)
    current_name = fields.Char("Současný název", readonly=True)
    state = fields.Selection(STATES, "Stav", readonly=True)
    state_order = fields.Integer(compute="_compute_state_order", store=True)
    res_id = fields.Integer(readonly=True)
    apply = fields.Boolean("Zapsat")
    aggregate_sector_id = fields.Many2one("investra.esa.aggregate.sector", "Typ emitenta")

    @api.depends("state")
    def _compute_state_order(self):
        order = {"conflict": 0, "new": 1, "renamed": 2, "missing": 3, "same": 4}
        for line in self:
            line.state_order = order.get(line.state, 9)
