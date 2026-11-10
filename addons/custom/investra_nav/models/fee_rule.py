from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

EXPENSE_ROLES = [
    ("expense_management", "Úplata za obhospodařování"),
    ("expense_administration", "Úplata za administraci"),
    ("expense_depositary", "Úplata depozitáři"),
    ("expense_performance", "Výkonnostní odměna"),
    ("expense_other", "Ostatní náklady"),
]


class InvestraFeeRule(models.Model):
    """Skladba úplaty: druh, základ, kdo platí, kdo přijímá. Sazby jsou ve verzích s platností od data."""

    _name = "investra.fee.rule"
    _description = "Pravidlo úplaty"
    _order = "fund_id, sequence, id"

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    name = fields.Char(required=True, string="Název")
    sequence = fields.Integer(default=10, help="Pořadí výpočtu podle statutu.", string="Pořadí")
    active = fields.Boolean(default=True, string="Aktivní")
    statute_ref = fields.Char(string="Článek statutu")
    kind = fields.Selection(
        [
            ("periodic", "Časově rozlišená úplata"),
            ("performance", "Výkonnostní odměna"),
            ("tax", "Očekávaná daň"),
            ("external", "Výpočet mimo Odoo s doložením"),
        ],
        required=True,
        default="periodic",
        string="Druh",
    )
    basis = fields.Selection(
        [
            ("act365", "ACT/365"),
            ("act360", "ACT/360"),
            ("act_act", "ACT/ACT (ISDA)"),
            ("thirty360_eu", "30E/360"),
            ("thirty360_us", "30/360 US"),
            ("months", "Celé měsíce / 12"),
        ],
        required=True,
        default="act365",
        string="Konvence dnů",
    )
    base_source = fields.Selection(
        [
            ("fk", "Fondový kapitál"),
            ("average_fk", "Průměrný FK od začátku roku"),
            ("class_fk", "Kapitál třídy"),
            ("assets", "Aktiva"),
            ("none", "Bez základu"),
        ],
        required=True,
        default="fk",
        string="Základ",
    )
    base_mode = fields.Selection([("before", "Před úplatou"), ("after", "Po úplatě")], required=True, default="before", string="Základ před/po úplatě")
    class_ids = fields.Many2many("investra.fund.class", string="Platí třídy", help="Prázdné znamená společný náklad.")
    expense_role = fields.Selection(EXPENSE_ROLES, default="expense_other", required=True, string="Nákladová role")
    recipient_share = fields.Float(digits=(6, 4), default=0, string="Podíl příjemcům z tříd")
    recipient_class_ids = fields.Many2many(
        "investra.fund.class", "investra_fee_rule_recipient_rel", "rule_id", "class_id", string="Přijímající třídy",
        help="Přijímající třídy se dělí podle kapitálu; přesun jde přes vnitřní zúčtování.",
    )
    cover_class_id = fields.Many2one(
        "investra.fund.class", string="Třída krytí",
        help="Při nedosažení cíle výkonnostního pravidla kryje rozdíl tato třída, nejvýše do svého kapitálu.",
    )
    crystallisation = fields.Selection(
        [("none", "Nekrystalizuje"), ("month", "Měsíčně"), ("quarter", "Čtvrtletně"), ("year", "Ročně")],
        required=True,
        default="year",
        string="Krystalizace",
    )
    version_ids = fields.One2many("investra.fee.version", "rule_id", string="Verze")

    @api.constrains("recipient_share")
    def _check_share(self):
        for rule in self:
            if not 0 <= rule.recipient_share <= 1:
                raise ValidationError(self.env._("Podíl příjemců musí být 0 až 1."))

    def _engine_rule(self, start, end):
        self.ensure_one()
        versions = [v._engine_values() for v in self.version_ids]
        if not versions:
            raise UserError(self.env._("Pravidlo %s nemá žádnou sazbu.", self.name))
        return {"basis": self.basis, "base_mode": self.base_mode, "versions": versions}

    def _version_at(self, day):
        self.ensure_one()
        valid = self.version_ids.filtered(lambda v: v.valid_from <= day).sorted("valid_from")
        if not valid:
            raise UserError(self.env._("Pravidlo %(rule)s nemá sazbu k %(day)s.", rule=self.name, day=day))
        return valid[-1]


class InvestraFeeVersion(models.Model):
    """Parametry platné od data. Změna sazby je nová verze, období se při výpočtu rozdělí."""

    _name = "investra.fee.version"
    _description = "Verze úplaty"
    _order = "rule_id, valid_from"

    rule_id = fields.Many2one("investra.fee.rule", required=True, ondelete="cascade", index=True, string="Pravidlo")
    company_id = fields.Many2one(related="rule_id.company_id", store=True, index=True)
    valid_from = fields.Date(required=True, string="Platí od")
    decision_ref = fields.Char(string="Rozhodnutí nebo změna statutu")
    rate = fields.Float(digits=(10, 8), string="Sazba p. a.")
    threshold = fields.Float(digits=(20, 2), string="Práh základu")
    fixed_monthly = fields.Float(digits=(20, 2), string="Pevná částka měsíčně")
    fixed_mode = fields.Selection([("pro_rata", "Poměrně"), ("started_month", "Za každý započatý měsíc")], default="pro_rata", required=True, string="Výpočet za období")
    step_size = fields.Float(digits=(20, 2), string="Velikost pásma")
    step_amount = fields.Float(digits=(20, 2), string="Příplatek za pásmo")
    included_classes = fields.Integer(string="Tříd v ceně")
    extra_class_monthly = fields.Float(digits=(20, 2), string="Příplatek za třídu")
    min_annual = fields.Float(digits=(20, 2), string="Minimum ročně")
    max_annual = fields.Float(digits=(20, 2), string="Maximum ročně")
    tier_ids = fields.One2many("investra.fee.tier", "version_id", string="Klouzavá pásma")
    perf_measure = fields.Selection([("capital", "Kapitál třídy"), ("unit", "Hodnota na kus")], default="capital", required=True, string="Měřítko výkonnosti")
    perf_use_hwm = fields.Boolean(default=True, string="High-water mark")
    initial_reference = fields.Float(digits=(20, 8), string="Počáteční srovnávací hodnota")
    hurdle_kind = fields.Selection([("none", "Bez překážky"), ("fixed", "Pevná sazba"), ("index", "Index nebo benchmark")], default="none", required=True, string="Překážka (hurdle)")
    hurdle_rate = fields.Float(digits=(10, 8), string="Sazba překážky")
    hurdle_margin = fields.Float(digits=(10, 8), string="Marže nad index")
    hurdle_type = fields.Selection([("hard", "Tvrdá"), ("soft", "Měkká s doháněním")], default="hard", required=True, string="Typ překážky")
    catch_up = fields.Float(digits=(6, 4), default=1, string="Dohánění (catch-up)")
    hurdle_floor_zero = fields.Boolean(string="Záporný etalon počítat jako nulu")
    benchmark_id = fields.Many2one("investra.benchmark", ondelete="restrict", string="Benchmark")
    require_positive_return = fields.Boolean(string="Jen při kladném výnosu")
    probability = fields.Float(digits=(6, 4), default=1, string="Váha pravděpodobnosti dohadu")
    cap_rate = fields.Float(digits=(10, 8), string="Strop z hodnoty")

    _uniq = models.Constraint("unique(rule_id, valid_from)", "Verze s tímto datem už existuje.")

    def _check_unused(self):
        """Verze použitá v ocenění mimo návrh zůstává beze změny; změna sazby je nová verze."""
        Fee = self.env["investra.valuation.fee"].sudo()
        for version in self:
            fees = Fee.search([
                ("rule_id", "=", version.rule_id.id),
                ("valuation_id.state", "not in", ("draft", "computed", "returned")),
            ])
            if fees and version.valid_from <= max(fees.valuation_id.mapped("date")):
                raise UserError(self.env._("Použitou verzi sazby nejde měnit, založte novou s platností od data."))

    def write(self, vals):
        self._check_unused()
        return super().write(vals)

    def unlink(self):
        self._check_unused()
        return super().unlink()

    def _engine_values(self):
        self.ensure_one()
        return {
            "valid_from": self.valid_from,
            "rate": self.rate,
            "threshold": self.threshold,
            "fixed_monthly": self.fixed_monthly,
            "fixed_mode": self.fixed_mode,
            "step_size": self.step_size,
            "step_amount": self.step_amount,
            "included_classes": self.included_classes,
            "extra_class_monthly": self.extra_class_monthly,
            "min_annual": self.min_annual,
            "max_annual": self.max_annual,
            "tiers": [{"from": t.amount_from, "rate": t.rate} for t in self.tier_ids],
        }


class InvestraFeeTier(models.Model):
    _name = "investra.fee.tier"
    _description = "Klouzavé pásmo"
    _order = "amount_from"

    version_id = fields.Many2one("investra.fee.version", required=True, ondelete="cascade", string="Verze pravidla")
    company_id = fields.Many2one(related="version_id.company_id", store=True, index=True)
    amount_from = fields.Float(digits=(20, 2), required=True, string="Od částky")
    rate = fields.Float(digits=(10, 8), required=True, string="Sazba")


class InvestraBenchmark(models.Model):
    _name = "investra.benchmark"
    _description = "Benchmark"

    name = fields.Char(required=True, string="Název")
    value_ids = fields.One2many("investra.benchmark.value", "benchmark_id", string="Hodnoty")

    def _value_at(self, day):
        self.ensure_one()
        record = self.value_ids.filtered(lambda v: v.date <= day).sorted("date")
        if not record:
            raise UserError(self.env._("Benchmark %(name)s nemá hodnotu k %(day)s.", name=self.name, day=day))
        return record[-1].value


class InvestraBenchmarkValue(models.Model):
    _name = "investra.benchmark.value"
    _description = "Hodnota benchmarku"
    _order = "date desc"

    benchmark_id = fields.Many2one("investra.benchmark", required=True, ondelete="cascade", string="Benchmark")
    date = fields.Date(required=True, string="Datum")
    value = fields.Float(digits=(20, 8), required=True, string="Hodnota")
    source = fields.Char(string="Zdroj")
