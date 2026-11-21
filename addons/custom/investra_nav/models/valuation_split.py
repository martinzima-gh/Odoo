"""ZJ-25: rozpad změny tříd po účtech (jen zobrazení a kontrola).

Nic se trvale neukládá: řádky rozpadu jsou v paměti (`_class_split`) a obrazovka je dostane jako dočasné záznamy
(TransientModel). Zveřejněné ocenění je zamčené, rozpad jde proto kdykoli spočítat znovu z hlavní knihy.
Odvození je v `docs/ukoly/podklady/davka-ZJ-24-27/plan-ZJ-25-technicky.md`, oddíl A.
"""
from collections import defaultdict
from decimal import Decimal

from odoo import fields, models
from odoo.exceptions import UserError

from .. import engine
from .valuation import d

TOLERANCE = Decimal("0.01")
MODES = ("balance", "result")
GROUP_SELECTION = [
    ("asset", "Aktiva"), ("liability", "Závazky"), ("off_balance", "Podrozvaha"),
    ("capital", "Kapitálové pohyby (nejsou výsledek)"), ("prior", "Dodatečné zápisy do minulých období"),
    ("income", "Výnosy"), ("expense", "Náklady"), ("equity", "Vlastní kapitál a OCI"),
    ("transfer", "Převody mezi společnou částí a třídou"), ("rounding", "Zaokrouhlení podílu"),
]


def account_group(account_type):
    """Skupina účtu v režimu Rozvaha (asset, liability, off_balance) nebo Podle výsledovky (income, expense, equity)."""
    for prefix in ("asset", "liability", "off_balance", "income", "expense", "equity"):
        if (account_type or "").startswith(prefix):
            return prefix
    return None


class InvestraValuationClassAccount(models.TransientModel):
    """Řádek rozpadu změny třídy po účtech; dočasný, nic se neukládá natrvalo."""

    _name = "investra.valuation.class.account"
    _description = "Rozpad třídy po účtech"
    _order = "mode, sequence, id"

    class_line_id = fields.Many2one("investra.valuation.class", required=True, ondelete="cascade", string="Třída ocenění")
    valuation_id = fields.Many2one(related="class_line_id.valuation_id", string="Ocenění")
    mode = fields.Selection([("balance", "Rozvaha"), ("result", "Podle výsledovky")], required=True, string="Pohled")
    sequence = fields.Integer(string="Pořadí")
    group = fields.Selection(GROUP_SELECTION, string="Skupina")
    account_id = fields.Many2one("account.account", string="Účet")
    name = fields.Char(string="Název")
    common = fields.Float(digits=(20, 2), string="Společné – fond")
    share = fields.Float(digits=(20, 2), string="Podíl třídy")
    specific = fields.Float(digits=(20, 2), string="Specifické – třída")
    impact = fields.Float(digits=(20, 2), string="Vliv na FK třídy")

    def action_open_lines(self):
        """Položky deníku účtu za období: řádky bez třídy a řádky této třídy."""
        self.ensure_one()
        if not self.account_id:
            raise UserError(self.env._("Řádek nemá účet."))
        valuation = self.valuation_id
        domain = valuation._line_domain(
            ("account_id", "=", self.account_id.id), ("date", ">", valuation._period_start()),
            "|", ("investra_class_id", "=", False), ("investra_class_id", "=", self.class_line_id.class_id.id))
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Položky deníku – %s", self.account_id.display_name),
            "res_model": "account.move.line",
            "views": [(self.env.ref("investra_nav.view_move_line_class_split_list").id, "list")],
            "domain": domain,
            "context": {"group_by": "investra_instrument_id"},
        }

    def action_open_documents(self):
        """Doklady, ze kterých vzniká řádek Převody mezi společnou částí a třídou."""
        self.ensure_one()
        if self.group != "transfer":
            raise UserError(self.env._("Doklady má jen řádek Převody mezi společnou částí a třídou."))
        line = self.class_line_id
        Transfer = self.env["investra.valuation.class.transfer"]
        Transfer.search([("create_uid", "=", self.env.uid), ("class_line_id", "=", line.id)]).unlink()
        records = Transfer.create([{**row, "class_line_id": line.id} for row in line.valuation_id._class_split_transfers(line)])
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Převody – třída %s", line.class_id.code),
            "res_model": "investra.valuation.class.transfer",
            "views": [(self.env.ref("investra_nav.view_valuation_class_transfer_list").id, "list")],
            "domain": [("id", "in", records.ids)],
        }


class InvestraValuationClassTransfer(models.TransientModel):
    """Doklad, který přispívá k řádku Převody (rozdíl mezi pohledem Rozvaha a Podle výsledovky)."""

    _name = "investra.valuation.class.transfer"
    _description = "Doklad převodu mezi společnou částí a třídou"
    _order = "date, id"

    class_line_id = fields.Many2one("investra.valuation.class", required=True, ondelete="cascade", string="Třída ocenění")
    move_id = fields.Many2one("account.move", string="Doklad")
    date = fields.Date(string="Datum")
    source_name = fields.Char(string="Zdroj")
    common = fields.Float(digits=(20, 2), string="Společné – fond")
    specific = fields.Float(digits=(20, 2), string="Specifické – třída")

    def action_open_move(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "account.move", "res_id": self.move_id.id, "views": [(False, "form")]}


class InvestraValuation(models.Model):
    _inherit = "investra.valuation"

    # --- vstupy -------------------------------------------------------------------------------------

    def _split_inputs(self, context=None, bridges=None):
        """Po třídách: poměr, předběžný kapitál, kapitál bez podílu, FK (t−1), specifická změna a společná změna ocenění.

        Při výpočtu přijde `context` z `_finish` (Decimal); bez něj (staré ocenění, balíček) se vezme uložený řádek třídy.
        """
        result = {}
        for line in self.class_line_ids:
            row = (context or {}).get(line.class_id)
            ratio = row["ratio"] if row else d(line.ratio)
            pre = row["pre_capital"] if row else d(line.pre_capital)
            fixed = row.get("fixed", Decimal(0)) if row else (pre if not ratio else Decimal(0))
            opening = row["opening_capital"] if row else d(line.opening_capital)
            shared = bridges[line.class_id]["shared_result"] if bridges else d(line.shared_result)
            result[line] = {"ratio": ratio, "pre": pre, "fixed": fixed, "opening": opening, "delta": d(line.delta),
                            "shared_result": shared}
        return result

    def _split_ledger(self, start):
        """Změna účtů za období po účtech a třídách (jeden dotaz) a součet rozvahových účtů k začátku období (druhý dotaz)."""
        Line = self.env["account.move.line"].sudo()
        common, by_class, all_classed = defaultdict(Decimal), defaultdict(lambda: defaultdict(Decimal)), defaultdict(Decimal)
        accounts = {}
        for account, fund_class, balance in Line._read_group(
                self._line_domain(("date", ">", start)), groupby=["account_id", "investra_class_id"], aggregates=["balance:sum"]):
            amount = engine.money(d(balance))
            accounts[account.id] = account
            if fund_class:
                by_class[fund_class][account] += amount
                all_classed[account] += amount
            else:
                common[account] += amount
        opening_balance = Decimal(0)
        for _account, balance in Line._read_group(
                self._line_domain(("date", "<=", start), "|", ("account_id.account_type", "=like", "asset%"),
                                  ("account_id.account_type", "=like", "liability%")),
                groupby=["account_id"], aggregates=["balance:sum"]):
            opening_balance += engine.money(d(balance))
        return common, by_class, all_classed, opening_balance

    # --- rozpad -------------------------------------------------------------------------------------

    def _class_split(self, context=None, bridges=None):
        """Rozpad změny tříd po účtech: {řádek třídy: {"balance": [řádky], "result": [řádky]}} (jen v paměti).

        Společná změna fondu S = Σ změn aktiv a závazků bez třídy − změna podrozvahy s třídou − kapitálové pohyby + dodatečné zápisy
        do minulých období. Podíl třídy = poměr × společná část řádku; zaokrouhlení doplní rozdíl proti Změně společné.
        """
        self.ensure_one()
        start = self._period_start()
        inputs = self._split_inputs(context, bridges)
        common, by_class, all_classed, opening_balance = self._split_ledger(start)
        movements = sum((v["pre"] - v["opening"] for v in inputs.values()), Decimal(0))
        prior = opening_balance - sum((v["opening"] for v in inputs.values()), Decimal(0))
        excluded = self.env["investra.account.role"].sudo().accounts_for(self.company_id, "class_capital")
        result = {}
        for line, values in inputs.items():
            own = by_class.get(line.class_id, {})
            balance_rows, result_rows = [], []
            for account in sorted(set(common) | set(all_classed), key=lambda a: a.code):
                group = account_group(account.account_type)
                if group in ("asset", "liability"):
                    balance_rows.append({"group": group, "account": account, "common": common.get(account, Decimal(0)),
                                         "specific": own.get(account, Decimal(0))})
                elif group == "off_balance":
                    # Změna podrozvahy s třídou se od společné části odečítá (nejde do FK), specifická je třídy.
                    balance_rows.append({"group": group, "account": account, "common": -all_classed.get(account, Decimal(0)),
                                         "specific": own.get(account, Decimal(0))})
                elif group in ("income", "expense", "equity") and account.account_type != "equity_unaffected" \
                        and account not in excluded:
                    result_rows.append({"group": group, "account": account, "common": -common.get(account, Decimal(0)),
                                        "specific": -own.get(account, Decimal(0))})
            tail = [{"group": "capital", "common": -movements, "specific": Decimal(0)},
                    {"group": "prior", "common": prior, "specific": Decimal(0)}]
            off_rows = [r for r in balance_rows if r["group"] == "off_balance"]
            balance_rows = self._split_finish(balance_rows + tail, values)
            # Pohled Podle výsledovky: stejná podrozvaha, kapitálové pohyby a dodatečné zápisy; rozdíl proti rozvaze
            # (úplata, přesuny, daňový efekt) dorovná řádek Převody, aby součty obou pohledů byly shodné.
            result_rows = result_rows + off_rows + tail
            transfer = {"group": "transfer", "account": None,
                        "common": sum((r["common"] for r in balance_rows if r["group"] != "rounding"), Decimal(0))
                        - sum((r["common"] for r in result_rows), Decimal(0)),
                        "specific": sum((r["specific"] for r in balance_rows if r["group"] != "rounding"), Decimal(0))
                        - sum((r["specific"] for r in result_rows), Decimal(0))}
            result_rows = self._split_finish(result_rows + [transfer], values)
            result[line] = {"balance": balance_rows, "result": result_rows}
        return result

    def _split_finish(self, rows, values):
        """Podíl a vliv na FK třídy, řádek zaokrouhlení; prázdné řádky se vynechají."""
        ratio = values["ratio"]
        rows = [dict(r, share=engine.money(ratio * r["common"])) for r in rows]
        rows = [r for r in rows if r["common"] or r["share"] or r["specific"]]
        rounding = values["shared_result"] - sum((r["share"] for r in rows), Decimal(0))
        if rounding:
            rows.append({"group": "rounding", "account": None, "common": Decimal(0), "share": rounding, "specific": Decimal(0)})
        for sequence, row in enumerate(rows, start=1):
            row["sequence"] = sequence
            row["impact"] = row["share"] + row["specific"]
        return rows

    def _split_commands(self, line, mode, split=None):
        """Hodnoty dočasných záznamů `investra.valuation.class.account` pro třídu a pohled."""
        split = split or self._class_split()
        labels = dict(GROUP_SELECTION)
        values = []
        for row in split[line][mode]:
            account = row.get("account")
            values.append({
                "class_line_id": line.id, "mode": mode, "sequence": row["sequence"], "group": row["group"],
                "account_id": account.id if account else False,
                "name": account.name if account else labels[row["group"]],
                **{key: float(engine.money(row[key])) for key in ("common", "share", "specific", "impact")},
            })
        return values

    def _class_split_transfers(self, line):
        """Doklady období, které přispívají k řádku Převody: (hodnota v pohledu Rozvaha) − (hodnota Podle výsledovky).

        Kapitálové pohyby a dodatečné zápisy jsou v obou pohledech stejné, v rozdílu odpadnou. Součet dokladů = řádek Převody.
        """
        self.ensure_one()
        start = self._period_start()
        excluded = self.env["investra.account.role"].sudo().accounts_for(self.company_id, "class_capital")
        Line = self.env["account.move.line"].sudo()
        # Rozvahové a výsledkové řádky přispívají do rozdílu shodně (+ částka); podrozvaha je v obou pohledech stejná a odpadne.
        per_move = defaultdict(lambda: [Decimal(0), Decimal(0)])
        for move, account, fund_class, balance in Line._read_group(
                self._line_domain(("date", ">", start)), groupby=["move_id", "account_id", "investra_class_id"],
                aggregates=["balance:sum"]):
            group = account_group(account.account_type)
            counted = group in ("asset", "liability") or (
                group in ("income", "expense", "equity") and account.account_type != "equity_unaffected" and account not in excluded)
            if not counted:
                continue
            amount = engine.money(d(balance))
            if not fund_class:
                per_move[move][0] += amount
            elif fund_class == line.class_id:
                per_move[move][1] += amount
        moves = self.env["account.move"].sudo().browse([m.id for m in per_move])
        sources = {m.id: m.investra_event_id.source_name or m.investra_event_id.name or m.name for m in moves}
        rows = []
        for move, (common, specific) in per_move.items():
            if common or specific:
                rows.append({"move_id": move.id, "date": move.date, "source_name": sources.get(move.id) or move.name,
                             "common": float(common), "specific": float(specific)})
        return rows

    # --- kontrola -----------------------------------------------------------------------------------

    def _run_split_check(self, context, bridges):
        """Kód `class_split`: rozpad po účtech sedí na přemostění tříd (rozdíl nad 0,01 zastaví ocenění)."""
        split = self._class_split(context, bridges)
        inputs = self._split_inputs(context, bridges)
        wrong, expected_total, actual_total = [], Decimal(0), Decimal(0)
        for line, modes in split.items():
            rows = modes["balance"]
            values = inputs[line]
            expected = values["shared_result"] + values["delta"]
            impact = sum((r["impact"] for r in rows), Decimal(0))
            specific = sum((r["specific"] for r in rows), Decimal(0))
            expected_total += expected
            actual_total += impact
            if abs(impact - expected) > TOLERANCE or abs(specific - values["delta"]) > TOLERANCE:
                wrong.append((line, expected, impact))
        # Společná změna fondu z rozpadu = neutrální částka − předběžný kapitál tříd s podílem (oddíl A plánu).
        shared_from_rows = Decimal(0)
        if split:
            first = next(iter(split.values()))["balance"]
            shared_from_rows = sum((r["common"] for r in first), Decimal(0))
        shared_expected = d(self.neutral_capital) - sum((v["pre"] - v["fixed"] for v in inputs.values()), Decimal(0))
        common_wrong = abs(shared_from_rows - shared_expected) > TOLERANCE
        self._check("class_split", "Rozpad tříd po účtech = přemostění", not wrong and not common_wrong,
                    "; ".join(f"{line.class_id.code}: {impact} ≠ {expected}" for line, expected, impact in wrong)
                    or (f"společná změna {shared_from_rows} ≠ {shared_expected}" if common_wrong else ""),
                    expected=expected_total, actual=actual_total, difference=actual_total - expected_total,
                    items=[{"record": line, "name": line.class_id.code,
                            "values": f"očekáváno {expected}, rozpad {impact}, rozdíl {impact - expected}"}
                           for line, expected, impact in wrong])


class InvestraValuationClass(models.Model):
    _inherit = "investra.valuation.class"

    movement_ids = fields.Many2many("investra.class.movement", compute="_compute_split_records", string="Úpisy a odkupy období")
    fee_line_ids = fields.Many2many("investra.valuation.fee", compute="_compute_split_records", string="Úplaty třídy")

    def _compute_split_records(self):
        Movement = self.env["investra.class.movement"].sudo()
        for line in self:
            valuation = line.valuation_id
            line.movement_ids = Movement.search([
                ("class_id", "=", line.class_id.id), ("date", ">", valuation._period_start()), ("date", "<=", valuation.date),
                ("state", "!=", "reversed")], order="date, id")
            line.fee_line_ids = valuation.fee_line_ids.filtered(lambda fee: fee.class_id == line.class_id)

    def action_open_split(self):
        """Dočasné řádky rozpadu třídy po účtech (pohled z kontextu `split_mode`: balance | result) a jejich seznam."""
        self.ensure_one()
        mode = self.env.context.get("split_mode", "balance")
        if mode not in MODES:
            raise UserError(self.env._("Neznámý pohled rozpadu."))
        Account = self.env["investra.valuation.class.account"]
        Account.search([("create_uid", "=", self.env.uid), ("class_line_id", "=", self.id)]).unlink()
        valuation = self.valuation_id
        split = valuation._class_split()
        rows = Account.create(valuation._split_commands(self, mode, split))
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Rozpad po účtech – %s", self.class_id.code),
            "res_model": "investra.valuation.class.account",
            "views": [(self.env.ref("investra_nav.view_valuation_class_account_list").id, "list")],
            "domain": [("id", "in", rows.ids)],
            "context": {"group_by": "group"},
        }


class AccountMoveLineSplit(models.Model):
    """Pomocná pole řádku deníku pro seznam „Položky deníku“ z rozpadu tříd (nic se neukládá)."""

    _inherit = "account.move.line"

    investra_class_label = fields.Char(compute="_compute_investra_split_labels", string="Třída")
    investra_source_name = fields.Char(compute="_compute_investra_split_labels", string="Zdroj")

    def _compute_investra_split_labels(self):
        # Zdroj dávkově: událost se bere z dokladu (investra_event_id), názvy zdrojů jedním průchodem.
        events = {}
        for move in self.move_id:
            events[move.id] = move.sudo().investra_event_id
        for line in self:
            event = events.get(line.move_id.id)
            line.investra_class_label = line.investra_class_id.code or self.env._("Společné")
            line.investra_source_name = (event.source_name or event.name) if event else False

    def action_open_source(self):
        """Otevře zdroj dokladu (obchod, úpis, splátku, ocenění …), jinak doklad."""
        self.ensure_one()
        event = self.move_id.sudo().investra_event_id
        if event and event._source():
            return event.action_open_source()
        return {"type": "ir.actions.act_window", "res_model": "account.move", "res_id": self.move_id.id, "views": [(False, "form")]}


class InvestraValuationPortfolioChange(models.Model):
    """ZJ-25 1.5: změna ceny a z toho kurz u řádku portfolia proti minulému ocenění (jen zobrazení, nic se neukládá)."""

    _inherit = "investra.valuation.portfolio"

    prev_line_id = fields.Many2one("investra.valuation.portfolio", compute="_compute_price_change", string="Řádek minulého ocenění")
    price_change = fields.Float(compute="_compute_price_change", digits=(20, 2), string="Změna ceny",
                                help="Kusy × (jednotková hodnota × kurz − minulá jednotková hodnota × minulý kurz); jednotková hodnota = "
                                     "reálná hodnota v měně / kusy. Bez minulého řádku nebo bez kusů 0.")
    fx_change = fields.Float(compute="_compute_price_change", digits=(20, 2), string="z toho kurz",
                             help="Kusy × minulá jednotková hodnota × (kurz − minulý kurz): část změny ceny z pohybu kurzu.")

    def _compute_price_change(self):
        Line = self.sudo()
        previous = {}
        for valuation in self.valuation_id:
            if valuation.previous_id:
                for line in Line.search([("valuation_id", "=", valuation.previous_id.id)]):
                    previous[(valuation.id, line.instrument_id.id, line.portfolio_id.id, line.classification_id.id)] = line
        for line in self:
            prev = previous.get((line.valuation_id.id, line.instrument_id.id, line.portfolio_id.id, line.classification_id.id))
            line.prev_line_id = prev if line.instrument_id else False
            line.price_change = line.fx_change = 0.0
            if not (prev and line.instrument_id and line.quantity and prev.quantity):
                continue
            unit_now = d(line.fair_value_currency) / d(line.quantity)
            unit_before = d(prev.fair_value_currency) / d(prev.quantity)
            quantity = d(line.quantity)
            line.price_change = float(engine.money(quantity * (unit_now * d(line.fx_rate) - unit_before * d(prev.fx_rate))))
            line.fx_change = float(engine.money(quantity * unit_before * (d(line.fx_rate) - d(prev.fx_rate))))
