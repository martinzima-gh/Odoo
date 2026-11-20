from datetime import date

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

BASE_STEPS = [
    ("1", "Po kroku 1"),
    ("2", "Po kroku 2"),
    ("3", "Po kroku 3"),
    ("4", "Po kroku 4"),
]

# ZJ-12 krok 5: popisky voleb základu podle druhu pravidla (stejná hodnota base_step, jiný popis a jen přípustné volby).
BASE_STEPS_FEE = [
    ("1", "Po kroku 1 – před úplatami tohoto ocenění"),
    ("2", "Po kroku 2 – včetně úplat tohoto ocenění"),
    ("3", "Po kroku 3 – po výkonnostní odměně"),
    ("4", "Po kroku 4 – výsledný FK (po úplatách, odměně a dani)"),
]
BASE_STEPS_PERFORMANCE = [
    ("1", "Po kroku 1 – před úplatami a daní od začátku období odměny"),
    ("2", "Po kroku 2 – po úplatách, před daní od začátku období odměny"),
    ("4", "Po kroku 4 – zveřejněná hodnota po úplatách a dani"),
]
BASE_STEPS_TAX = [
    ("1", "Po kroku 1 – základ nesnižují úplaty ani odměna"),
    ("2", "Po kroku 2 – základ snižují úplaty"),
    ("3", "Po kroku 3 – základ snižují úplaty i odměna"),
]

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
    _inherit = ["mail.thread"]
    _description = "Pravidlo úplaty"
    # Pořadí výpočtu je pevné podle druhu (ZJ-06 bod 7); pole Pořadí zrušeno.
    _order = "fund_id, id"

    fund_id = fields.Many2one("investra.fund", required=True, ondelete="restrict", index=True, tracking=True, string="Fond")
    company_id = fields.Many2one(related="fund_id.company_id", store=True, index=True)
    name = fields.Char(required=True, tracking=True, string="Název")
    active = fields.Boolean(default=True, tracking=True, string="Aktivní")
    # ZJ-06 bod 6: jedno pole místo „Článek statutu“ (Char) a „Poznámka“ (Text, pole note zrušeno; ve všech pravidlech bylo prázdné).
    statute_ref = fields.Text(
        tracking=True, string="Statut a poznámka",
        help="Článek statutu, ze kterého úplata vychází, a případná poznámka. Jen informace; do výpočtu nevstupuje.",
    )
    kind = fields.Selection(
        [
            ("periodic", "Časově rozlišená úplata"),
            ("performance", "Výkonnostní odměna"),
            ("tax", "Očekávaná daň"),
            # „Výpočet mimo Odoo s doložením“ zrušilo ZJ-03; ručně doložené úplaty se zadávají v ocenění bez pravidla.
        ],
        required=True,
        default="periodic",
        tracking=True, string="Druh",
        help="Časově rozlišená úplata se počítá ze základu za období, výkonnostní odměna z výnosu třídy nad překážkou, "
             "očekávaná daň z výsledku od začátku roku.",
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
        tracking=True, string="Konvence dnů",
        help="Jak se z počtu dnů období počítá část roku. U očekávané daně se nepoužívá.",
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
        tracking=True, string="Základ",
        help="Z čeho se úplata počítá: fondový kapitál, jeho průměr od začátku roku, kapitál třídy, aktiva, nebo bez základu "
             "(jen pevná částka). Průměrný FK bez tříd je úplata celého fondu z průměru FK; s vyplněnými Platí třídy se počítá "
             "za každou třídu z průměru jejího kapitálu od 1. 1., od prvního úpisu třídy nebo od zařazení do pravidla "
             "(pevné částky, minimum a maximum za každou třídu). U očekávané daně se nepoužívá.",
    )
    # ZJ-12 (rozhodnutí 2026-11-18 „Základ úplat, odměny a daně“): jedna volba „Základ: po kroku 1–4“ nahrazuje
    # base_mode a perf_base. Kroky: 1 FK před úplatami a daní, 2 časově rozlišené a ruční úplaty a opravy,
    # 3 výkonnostní odměna, 4 daň. Přípustné volby podle druhu hlídá _check_base_step; výchozí podle druhu
    # doplní výpočet (_compute_base_step), uživatel ji může přepsat.
    base_step = fields.Selection(
        BASE_STEPS, compute="_compute_base_step", store=True, readonly=False, precompute=True, required=True,
        tracking=True, string="Základ: po kroku",
        help="Stav NAV k datu ocenění, ze kterého se pravidlo počítá. 1 = FK před úplatami a daní, 2 = po časově "
             "rozlišených a ručních úplatách a opravách (včetně této úplaty), 3 = navíc po výkonnostní odměně, "
             "4 = navíc po dani (výsledný FK). Výkonnostní odměna: 1, 2 nebo 4 (výchozí 2), nikdy po sobě samé. "
             "Očekávaná daň: které náklady snižují základ – 1 žádné, 2 úplaty, 3 úplaty i odměna (výchozí). "
             "Úplata ze základu Aktiva nebo Bez základu volbu nemá.",
    )
    # Pohledy na base_step podle druhu (ZJ-12 krok 5): formulář i tabulka schématu ukazují jen přípustné volby a popisky
    # svého druhu. Hodnotu drží base_step (sledování změn, kontrola přípustnosti); pohled ji při uložení zapíše zpět.
    base_step_fee = fields.Selection(
        BASE_STEPS_FEE, compute="_compute_base_step_views", inverse="_inverse_base_step_views", string="Základ úplaty",
        help="Z jakého stavu NAV k datu ocenění se úplata počítá. Před úplatami tohoto ocenění (1) je výchozí; po kroku 2 se "
             "základ snižuje i o tuto úplatu, po kroku 4 se úplata počítá z výsledného (zveřejněného) FK a s daní se dopočte společně.",
    )
    base_step_performance = fields.Selection(
        BASE_STEPS_PERFORMANCE, compute="_compute_base_step_views", inverse="_inverse_base_step_views", string="Základ odměny",
        help="Hodnota třídy, ze které se odměna počítá. Před úplatami a daní (1): k hodnotě třídy se přičtou úplaty i daň, které třída "
             "nesla od začátku období odměny. Po kroku 2 (výchozí): přičte se jen daň. Po kroku 4: zveřejněná hodnota po úplatách a dani.",
    )
    base_step_tax = fields.Selection(
        BASE_STEPS_TAX, compute="_compute_base_step_views", inverse="_inverse_base_step_views", string="Základ daně",
        help="Které náklady snižují základ očekávané daně: žádné (1), úplaty (2), úplaty i výkonnostní odměna (3, výchozí).",
    )
    class_ids = fields.Many2many("investra.fund.class", tracking=True, string="Platí třídy",
        help="Třídy téhož fondu, které úplatu nesou. Prázdné znamená společný náklad celého fondu (dělí se poměrem kapitálu). "
             "U průměrného FK se úplata počítá za každou třídu z průměru jejího kapitálu; třídu přidanou v průběhu roku "
             "počítá od ocenění, kdy v pravidle poprvé je. Třída nesmí být zároveň přijímající.")
    expense_role = fields.Selection(EXPENSE_ROLES, default="expense_other", required=True, tracking=True, string="Nákladová role",
        help="Nákladový účet, na který se úplata zaúčtuje (podle role účtu v Nastavení → Účtování).")
    recipient_share = fields.Float(digits=(6, 4), default=0, tracking=True, string="Podíl příjemcům z tříd",
        help="Část úplaty (0 až 1), která se přesune přijímajícím třídám. Zbytek je náklad fondu.")
    recipient_class_ids = fields.Many2many(
        "investra.fund.class", "investra_fee_rule_recipient_rel", "rule_id", "class_id", tracking=True, string="Přijímající třídy",
        help="Třídy téhož fondu, které dostanou podíl z úplaty. Dělí se podle kapitálu, přesun jde přes vnitřní zúčtování. "
             "Třída nesmí být zároveň platící.",
    )
    cover_class_id = fields.Many2one(
        "investra.fund.class", tracking=True, string="Třída krytí",
        help="Jen výkonnostní odměna. Třída téhož fondu, která při nedosažení cíle kryje rozdíl, nejvýše do svého kapitálu. "
             "Nesmí být platící; smí být přijímající.",
    )
    crystallisation = fields.Selection(
        [
            ("none", "Nekrystalizuje"),
            # ZJ-06 bod 10b: krystalizace k datu každého ocenění (nová volba, kalendářní volby beze změny).
            ("valuation", "Při každém ocenění"),
            ("month", "Měsíčně"),
            ("quarter", "Čtvrtletně"),
            ("year", "Ročně"),
        ],
        required=True,
        default="year",
        tracking=True, string="Krystalizace",
        help="Jen výkonnostní odměna. Při krystalizaci se naběhlá odměna stane splatnou, srovnávací hodnota a high-water mark "
             "se posunou a naběhlá částka se vynuluje.",
    )
    version_ids = fields.One2many("investra.fee.version", "rule_id", string="Verze")
    overlap_warning = fields.Text(compute="_compute_overlap_warning", string="Upozornění na souběh")
    class_base_warning = fields.Text(compute="_compute_class_base_warning", string="Upozornění na nastavení")
    no_common_class_warning = fields.Text(
        compute="_compute_no_common_class_warning", string="Upozornění na třídu bez podílu",
        help="ZJ-08 D6: úplata z třídy, která se nepodílí na společných položkách, je obvykle omyl (ruční úplata ne).")

    @api.model
    def _base_steps(self, kind, base_source):
        """Přípustné volby základu podle druhu (ZJ-12, tabulka „Kroky výpočtu a volba základu“) a výchozí volba."""
        if kind == "performance":
            return ("1", "2", "4"), "2"
        if kind == "tax":
            return ("1", "2", "3"), "3"
        if base_source in ("assets", "none"):
            # Úplaty jsou závazky a aktiva nemění; volba je skrytá a ukládá 1.
            return ("1",), "1"
        return ("1", "2", "3", "4"), "1"

    @api.depends("kind", "base_source")
    def _compute_base_step(self):
        """Nepřípustná nebo prázdná volba se po změně druhu či zdroje základu nahradí výchozí volbou druhu."""
        for rule in self:
            allowed, default = self._base_steps(rule.kind, rule.base_source)
            if rule.base_step not in allowed:
                rule.base_step = default

    @api.depends("kind", "base_step")
    def _compute_base_step_views(self):
        for rule in self:
            rule.base_step_fee = rule.base_step if rule.kind == "periodic" else False
            rule.base_step_performance = rule.base_step if rule.kind == "performance" else False
            rule.base_step_tax = rule.base_step if rule.kind == "tax" else False

    def _inverse_base_step_views(self):
        for rule in self:
            value = {"periodic": rule.base_step_fee, "performance": rule.base_step_performance,
                     "tax": rule.base_step_tax}.get(rule.kind)
            if value and value != rule.base_step:
                rule.base_step = value

    @api.onchange("base_step_fee", "base_step_performance", "base_step_tax")
    def _onchange_base_step_warning(self):
        """Změna základu průměrného FK, odměny a daně se projeví i za dosavadní část roku nebo období odměny (ZJ-12 C.2)."""
        rule = self
        value = {"periodic": rule.base_step_fee, "performance": rule.base_step_performance,
                 "tax": rule.base_step_tax}.get(rule.kind)
        if not rule._origin.id or not value or value == rule._origin.base_step:
            return None
        if rule.kind == "periodic" and rule.base_source != "average_fk":
            return None
        return {"warning": {
            "title": self.env._("Změna základu"),
            "message": self.env._(
                "Změna se projeví i za dosavadní část roku nebo období odměny; rozdíl se doúčtuje v dalším ocenění."),
        }}

    @api.constrains("kind", "base_source", "base_step")
    def _check_base_step(self):
        labels = dict(self._fields["kind"]._description_selection(self.env))
        for rule in self:
            allowed, _default = self._base_steps(rule.kind, rule.base_source)
            if rule.base_step not in allowed:
                raise ValidationError(self.env._(
                    "Pravidlo %(rule)s (%(kind)s): základ po kroku %(step)s není přípustný; zvolte %(allowed)s.",
                    rule=rule.name, kind=labels.get(rule.kind, rule.kind), step=rule.base_step,
                    allowed=", ".join(allowed),
                ))

    @api.constrains("fund_id", "kind", "class_ids", "active")
    def _check_single_performance_and_tax(self):
        """Nejvýš jedna aktivní výkonnostní odměna na třídu a nejvýš jedno aktivní pravidlo daně na fond (ZJ-12 A.2).

        Dělení odměny mezi více příjemců jde přes podíl příjemcům, ne přes druhé pravidlo. Pravidlo bez tříd
        (úplata celého fondu, daň) se do kontroly odměn nepočítá; daň se posuzuje za fond bez ohledu na třídy.
        """
        for rule in self.filtered("active"):
            if rule.kind == "performance" and rule.class_ids:
                others = self.search([
                    ("id", "!=", rule.id), ("fund_id", "=", rule.fund_id.id), ("kind", "=", "performance"),
                    ("class_ids", "in", rule.class_ids.ids),
                ])
                if others:
                    shared = rule.class_ids & others.class_ids
                    raise ValidationError(self.env._(
                        "Třída %(classes)s už má výkonnostní odměnu %(others)s. Třída smí mít nejvýš jednu aktivní "
                        "výkonnostní odměnu; dělení mezi příjemce zadejte podílem příjemcům.",
                        classes=", ".join(shared.mapped("code")), others=", ".join(others.mapped("name")),
                    ))
            if rule.kind == "tax":
                others = self.search([
                    ("id", "!=", rule.id), ("fund_id", "=", rule.fund_id.id), ("kind", "=", "tax"),
                ])
                if others:
                    raise ValidationError(self.env._(
                        "Fond %(fund)s už má pravidlo daně %(others)s. Fond smí mít nejvýš jedno aktivní pravidlo daně.",
                        fund=rule.fund_id.name, others=", ".join(others.mapped("name")),
                    ))

    def write(self, vals):
        if "active" in vals and not vals["active"]:
            self._check_archive()
        return super().write(vals)

    def _check_archive(self):
        """Pojistka archivace (ZJ-12 krok 4, rozhodnutí 2026-11-18): archivované pravidlo se v dalším ocenění nepočítá,
        naběhlou odměnu ani zaúčtovanou daň by proto už nerozpustilo. Archivace se zastaví, má-li pravidlo odměny nebo daně
        z posledního zaúčtovaného ocenění nenulovou naběhlou odměnu (třídy pravidla) nebo daň zaúčtovanou od 1. 1."""
        Valuation = self.env["investra.valuation"].sudo()
        for rule in self.filtered(lambda r: r.active and r.kind in ("performance", "tax")):
            last = Valuation.search([
                ("fund_id", "=", rule.fund_id.id), ("state", "in", ("posted", "sent", "confirmed", "published")),
            ], order="date desc, version desc", limit=1)
            if not last:
                continue
            if rule.kind == "performance":
                lines = last.class_line_ids.filtered(lambda line: line.class_id in rule.class_ids)
                amount, what = sum(lines.mapped("perf_accrued")), self.env._("naběhlou odměnu")
            else:
                account = self.env["investra.account.role"].sudo().account_for(rule.company_id, "expense_tax")
                amount = float(last._sum(("date", ">=", date(last.date.year, 1, 1)), ("account_id", "=", account.id)))
                what = self.env._("zaúčtovanou daň od 1. 1.")
            if round(amount, 2):
                raise UserError(self.env._(
                    "Pravidlo %(rule)s má z posledního ocenění %(valuation)s %(what)s %(amount)s. Archivované pravidlo by ji "
                    "už nerozpustilo. Nejdřív nastavte verzi sazby 0 %% od data dalšího ocenění, ocenění zaúčtujte a pravidlo "
                    "archivujte potom. Omylem založené pravidlo bez částky archivovat jde.",
                    rule=rule.name, valuation=last.display_name, what=what, amount=f"{amount:.2f}"))

    @api.depends("kind", "base_source", "class_ids", "recipient_share", "recipient_class_ids")
    def _compute_class_base_warning(self):
        """Upozornění na pole, která výpočet v dané kombinaci nepoužije (rozhodnutí 2026-11-19); uložení nezastaví."""
        _ = self.env._
        for rule in self:
            messages = []
            if rule.kind == "periodic" and rule.base_source == "class_fk" and not rule.class_ids:
                messages.append(_("Základ je Kapitál třídy, ale pole Třídy je prázdné: úplata se počítá z FK celého fondu. "
                                  "Vyplňte třídy, nebo zvolte základ FK."))
            if rule.kind != "tax" and rule.recipient_share and not rule.recipient_class_ids:
                messages.append(_("Podíl příjemcům je vyplněný, ale nejsou zvolené přijímající třídy: celá úplata je náklad fondu."))
            if rule.kind != "tax" and rule.recipient_class_ids and not rule.recipient_share:
                messages.append(_("Přijímající třídy jsou zvolené, ale podíl příjemcům je 0: nic se jim nepřesune."))
            rule.class_base_warning = "\n".join(messages) or False

    def _no_common_classes(self):
        """Třídy bez podílu na společných položkách, ze kterých by pravidlo platilo (ZJ-08 D6); daň třídy nemá."""
        self.ensure_one()
        if self.kind == "tax":
            return self.env["investra.fund.class"]
        payers = self.class_ids or self.fund_id.class_ids
        return payers.filtered(lambda c: not c.shares_common)

    @api.depends("kind", "fund_id", "class_ids", "class_ids.shares_common", "fund_id.class_ids.shares_common")
    def _compute_no_common_class_warning(self):
        for rule in self:
            classes = rule._no_common_classes()
            rule.no_common_class_warning = "\n".join(
                self.env._("Třída %s se nepodílí na společných položkách; úplata z ní je obvykle omyl.", c.code)
                for c in classes) or False

    @api.depends("fund_id", "class_ids", "expense_role", "kind", "active")
    def _compute_overlap_warning(self):
        for rule in self:
            fund = rule.fund_id
            if not fund or rule.kind == "tax":
                rule.overlap_warning = False
                continue
            # Neuložené pravidlo (formulář) se počítá místo své uložené verze.
            others = self.search([("fund_id", "=", fund.id), ("id", "!=", rule._origin.id)])
            rules = [(r, r.class_ids) for r in others] + ([(rule, rule.class_ids)] if rule.active else [])
            messages = self._overlaps(rules, only=rule)
            rule.overlap_warning = "\n".join(messages) or False

    @api.model
    def _overlaps(self, rules, only=None):
        """Souběh úplat jedné nákladové role (rozhodnutí 2026-11-17 „Poplatky fondu a tříd“): jen upozornění.

        rules = [(pravidlo, třídy)] aktivních pravidel jednoho fondu; daň se neposuzuje. `only` omezí zprávy
        na ty, kterých se pravidlo účastní.
        """
        labels = dict(EXPENSE_ROLES)
        by_role = {}
        for rule, classes in rules:
            if rule.kind != "tax":
                by_role.setdefault(rule.expense_role, []).append((rule, classes))
        messages = []
        for role, items in by_role.items():
            fund_wide = [r for r, c in items if not c]
            on_classes = [(r, c) for r, c in items if c]
            if fund_wide and on_classes and (only is None or only in fund_wide or only in [r for r, _c in on_classes]):
                messages.append(self.env._(
                    "%(role)s: pravidlo celého fondu (%(fund)s) i pravidlo tříd (%(classes)s).",
                    role=labels.get(role, role), fund=", ".join(r.name for r in fund_wide),
                    classes=", ".join(r.name for r, _c in on_classes),
                ))
            per_class = {}
            for rule, classes in on_classes:
                for fund_class in classes:
                    per_class.setdefault(fund_class, []).append(rule)
            for fund_class, class_rules in per_class.items():
                if len(class_rules) > 1 and (only is None or only in class_rules):
                    messages.append(self.env._(
                        "%(role)s: třída %(cls)s má více pravidel (%(rules)s).",
                        role=labels.get(role, role), cls=fund_class.code, rules=", ".join(r.name for r in class_rules),
                    ))
        return messages

    @api.onchange("fund_id")
    def _onchange_fund_id_classes(self):
        """Po změně fondu se třídy z jiného fondu vymažou (bod 9 ZJ-06)."""
        for rule in self:
            for name in ("class_ids", "recipient_class_ids"):
                rule[name] = rule[name].filtered(lambda c: c.fund_id == rule.fund_id)
            if rule.cover_class_id.fund_id != rule.fund_id:
                rule.cover_class_id = False

    @api.onchange("kind")
    def _onchange_kind_tax(self):
        """Daň třídy ani příjemce nemá (rozhodnutí 2026-11-19): při změně druhu na daň se pole vyprázdní."""
        for rule in self:
            if rule.kind == "tax":
                rule.class_ids = rule.recipient_class_ids = False
                rule.recipient_share = 0

    @api.onchange("fund_id", "kind")
    def _onchange_single_class(self):
        """Výkonnostní odměna fondu s jedinou třídou: třída se předvyplní (rozhodnutí 2026-11-17)."""
        for rule in self:
            if rule.kind == "performance" and not rule.class_ids and len(rule.fund_id.class_ids) == 1:
                rule.class_ids = rule.fund_id.class_ids

    @api.constrains("fund_id", "kind", "class_ids", "recipient_class_ids", "cover_class_id", "recipient_share")
    def _check_classes(self):
        """Třídy musí být z fondu pravidla; třída nesmí být platící i přijímající a třída krytí nesmí být platící.

        Výkonnostní odměna musí mít aspoň jednu třídu: počítá se za každou třídu zvlášť, bez třídy by se tiše
        nespočítala (rozhodnutí 2026-11-17).
        """
        for rule in self:
            if rule.kind == "performance" and not rule.class_ids:
                raise ValidationError(self.env._(
                    "Výkonnostní odměna %s musí mít aspoň jednu třídu v poli Platí třídy.", rule.name))
            # Rozhodnutí 2026-11-19: daň výpočet počítá za celý fond a mezi třídy dělí sám (poměr + daňový efekt).
            if rule.kind == "tax" and (rule.class_ids or rule.recipient_class_ids or rule.recipient_share):
                raise ValidationError(self.env._(
                    "%s: daň je náklad celého fondu; třídy ani příjemce nemá.", rule.name))
            classes = rule.class_ids | rule.recipient_class_ids | rule.cover_class_id
            foreign = classes.filtered(lambda c: c.fund_id != rule.fund_id)
            if foreign:
                raise ValidationError(self.env._(
                    "Pravidlo %(rule)s: třída %(classes)s nepatří do fondu %(fund)s.",
                    rule=rule.name, classes=", ".join(foreign.mapped("code")), fund=rule.fund_id.name,
                ))
            both = rule.class_ids & rule.recipient_class_ids
            if both:
                raise ValidationError(self.env._(
                    "Pravidlo %(rule)s: třída %(classes)s nemůže být zároveň platící a přijímající.",
                    rule=rule.name, classes=", ".join(both.mapped("code")),
                ))
            if rule.cover_class_id and rule.cover_class_id in rule.class_ids:
                raise ValidationError(self.env._(
                    "Pravidlo %(rule)s: třída krytí %(cls)s nemůže být platící.",
                    rule=rule.name, cls=rule.cover_class_id.code,
                ))

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
        # ZJ-12 krok 2: engine počítá vždy ze základu, který mu předá ocenění; volbu kroku řeší ocenění.
        return {"basis": self.basis, "versions": versions}

    def _version_at(self, day):
        self.ensure_one()
        valid = self.version_ids.filtered(lambda v: v.valid_from <= day).sorted("valid_from")
        if not valid:
            raise UserError(self.env._("Pravidlo %(rule)s nemá sazbu k %(day)s.", rule=self.name, day=day))
        return valid[-1]


class InvestraFeeVersion(models.Model):
    """Parametry platné od data. Změna sazby je nová verze, období se při výpočtu rozdělí."""

    _name = "investra.fee.version"
    _inherit = ["investra.line.tracking.mixin"]
    _description = "Verze úplaty"
    _order = "rule_id, valid_from"

    # ZJ-10 fáze 2: verze nemá vlastní chatter (ve vnořeném formuláři se nevykreslí), změny jdou do chatteru pravidla.
    _line_tracking_parent = "rule_id"

    rule_id = fields.Many2one("investra.fee.rule", required=True, ondelete="cascade", index=True, string="Pravidlo")
    company_id = fields.Many2one(related="rule_id.company_id", store=True, index=True)
    valid_from = fields.Date(required=True, tracking=True, string="Platí od", help="První den platnosti. Verze platí do dne před začátkem další verze; změna sazby je nová verze s pozdějším datem.")
    decision_ref = fields.Char(tracking=True, string="Rozhodnutí nebo změna statutu", help="Odkaz na rozhodnutí nebo změnu statutu, ze které sazba vychází.")
    rate = fields.Float(digits=(10, 8), tracking=True, string="Sazba p. a.", help="Roční sazba (0,01 = 1 %). U výkonnostní odměny podíl z přebytku nad překážkou, u očekávané daně sazba daně.")
    threshold = fields.Float(digits=(20, 2), tracking=True, string="Práh základu", help="Sazba se použije jen na část základu nad prahem.")
    fixed_monthly = fields.Float(digits=(20, 2), tracking=True, string="Pevná částka měsíčně", help="Pevná částka za měsíc, přičítá se k částce ze sazby.")
    fixed_mode = fields.Selection([("pro_rata", "Poměrně"), ("started_month", "Za každý započatý měsíc")], default="pro_rata", required=True, tracking=True, string="Výpočet za období", help="Poměrně: pevná částka se krátí podle délky období. Za každý započatý měsíc: platí celá za každý kalendářní měsíc období.")
    step_size = fields.Float(digits=(20, 2), tracking=True, string="Velikost pásma", help="Velikost pásma základu. Příplatek za pásmo se přičítá za každé další započaté pásmo nad prvním.")
    step_amount = fields.Float(digits=(20, 2), tracking=True, string="Příplatek za pásmo", help="Měsíční příplatek za každé další započaté pásmo základu nad prvním.")
    included_classes = fields.Integer(tracking=True, string="Tříd v ceně", help="Počet tříd zahrnutých v ceně; za každou další se přičítá příplatek za třídu. Prázdné: všechny třídy jsou v ceně.")
    extra_class_monthly = fields.Float(digits=(20, 2), tracking=True, string="Příplatek za třídu", help="Měsíční příplatek za každou třídu nad počet tříd v ceně.")
    min_annual = fields.Float(digits=(20, 2), tracking=True, string="Minimum ročně", help="Nejnižší roční částka úplaty; za období se krátí poměrně. Prázdné: bez minima.")
    max_annual = fields.Float(digits=(20, 2), tracking=True, string="Maximum ročně", help="Nejvyšší roční částka úplaty; za období se krátí poměrně. Prázdné: bez maxima.")
    tier_ids = fields.One2many("investra.fee.tier", "version_id", string="Klouzavá pásma", help="Každá sazba platí jen na část základu v daném pásmu (od částky do další částky). Pásma nahrazují sazbu a práh.")
    perf_measure = fields.Selection([("capital", "Kapitál třídy"), ("unit", "Hodnota na kus")], default="capital", required=True, tracking=True, string="Měřítko výkonnosti", help="Kapitál třídy: výkonnost z kapitálu třídy očištěná o úpisy a odkupy. Hodnota na kus: z hodnoty podílu.")
    perf_use_hwm = fields.Boolean(default=True, tracking=True, string="High-water mark", help="Odměna jen z přírůstku nad dosavadním maximem srovnávací hodnoty (po poslední krystalizaci).")
    initial_reference = fields.Float(digits=(20, 8), tracking=True, string="Počáteční srovnávací hodnota", help="Srovnávací hodnota pro první období, než proběhne krystalizace.")
    hurdle_kind = fields.Selection([("none", "Bez překážky"), ("fixed", "Pevná sazba"), ("index", "Index nebo benchmark")], default="none", required=True, tracking=True, string="Překážka (hurdle)", help="Minimální výnos, který se musí dosáhnout, než vznikne odměna: pevná sazba, nebo vývoj indexu či benchmarku.")
    hurdle_rate = fields.Float(digits=(10, 8), tracking=True, string="Sazba překážky", help="Roční sazba pevné překážky (0,05 = 5 %).")
    hurdle_margin = fields.Float(digits=(10, 8), tracking=True, string="Marže nad index", help="Roční marže přičtená k vývoji indexu nebo benchmarku.")
    hurdle_type = fields.Selection([("hard", "Tvrdá"), ("soft", "Měkká s doháněním")], default="hard", required=True, tracking=True, string="Typ překážky", help="Tvrdá: odměna jen z přebytku nad překážkou. Měkká s doháněním: po dosažení cíle se odměna doplácí až do sazby z celého zisku.")
    catch_up = fields.Float(digits=(6, 4), default=1, tracking=True, string="Dohánění (catch-up)", help="Podíl přebytku, který se u měkké překážky doplácí (1 = 100 %).")
    hurdle_floor_zero = fields.Boolean(tracking=True, string="Záporný etalon počítat jako nulu", help="Pokles indexu se nepromítne do cíle: srovnávací cíl není nižší než výchozí hodnota období.")
    benchmark_id = fields.Many2one("investra.benchmark", ondelete="restrict", tracking=True, string="Benchmark", help="Benchmark pro překážku typu index; musí mít hodnoty k začátku i konci období.")
    require_positive_return = fields.Boolean(tracking=True, string="Jen při kladném výnosu", help="Odměna jen když je hodnota nad výchozí hodnotou období (výnos je kladný).")
    probability = fields.Float(digits=(6, 4), default=1, tracking=True, string="Váha pravděpodobnosti dohadu", help="Naběhlá odměna se vynásobí touto váhou (1 = 100 %). Pro dohad, který se nepovažuje za jistý.")
    cap_rate = fields.Float(digits=(10, 8), tracking=True, string="Strop z hodnoty", help="Odměna nejvýše tento podíl z hodnoty třídy (0,02 = 2 %). Prázdné: bez stropu.")

    _uniq = models.Constraint("unique(rule_id, valid_from)", "Verze s tímto datem už existuje.")

    # ZJ-06 bod 8: verze platí od svého data do dne před další verzí; „Platí do“ se neukládá ani nezobrazuje.
    validity_state = fields.Selection(
        [("ended", "Ukončená"), ("current", "Platná"), ("future", "Budoucí")],
        compute="_compute_validity_state", string="Stav verze",
    )

    @api.depends("valid_from", "rule_id.version_ids.valid_from")
    @api.depends_context("uid")
    def _compute_validity_state(self):
        today = fields.Date.context_today(self)
        for version in self:
            starts = [v.valid_from for v in version.rule_id.version_ids if v.valid_from]
            later = [day for day in starts if version.valid_from and day > version.valid_from]
            if not version.valid_from:
                version.validity_state = False
            elif version.valid_from > today:
                version.validity_state = "future"
            elif later and min(later) <= today:
                version.validity_state = "ended"
            else:
                version.validity_state = "current"

    def _line_tracking_desc(self):
        return self.env._("Verze platná od %s", self.valid_from or "–")

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
    _inherit = ["investra.line.tracking.mixin"]
    _description = "Klouzavé pásmo"
    _order = "amount_from"

    # Pásmo → verze → pravidlo: zpráva jde do chatteru pravidla úplaty (rozhodnutí 2026-11-18).
    _line_tracking_parent = "version_id.rule_id"

    version_id = fields.Many2one("investra.fee.version", required=True, ondelete="cascade", string="Verze pravidla")
    company_id = fields.Many2one(related="version_id.company_id", store=True, index=True)
    amount_from = fields.Float(digits=(20, 2), required=True, tracking=True, string="Od částky")
    rate = fields.Float(digits=(10, 8), required=True, tracking=True, string="Sazba")

    def _line_tracking_desc(self):
        return self.env._("Pásmo (verze od %(day)s)", day=self.version_id.valid_from or "–")


class InvestraBenchmark(models.Model):
    _name = "investra.benchmark"
    _inherit = ["mail.thread"]
    _description = "Benchmark"

    name = fields.Char(required=True, tracking=True, string="Název")
    value_ids = fields.One2many("investra.benchmark.value", "benchmark_id", string="Hodnoty")

    def _value_at(self, day):
        self.ensure_one()
        record = self.value_ids.filtered(lambda v: v.date <= day).sorted("date")
        if not record:
            raise UserError(self.env._("Benchmark %(name)s nemá hodnotu k %(day)s.", name=self.name, day=day))
        return record[-1].value


class InvestraBenchmarkValue(models.Model):
    _name = "investra.benchmark.value"
    _inherit = ["investra.line.tracking.mixin"]
    _description = "Hodnota benchmarku"
    _order = "date desc"

    _line_tracking_parent = "benchmark_id"

    benchmark_id = fields.Many2one("investra.benchmark", required=True, ondelete="cascade", string="Benchmark")
    date = fields.Date(required=True, tracking=True, string="Datum")
    value = fields.Float(digits=(20, 8), required=True, tracking=True, string="Hodnota")
    source = fields.Char(tracking=True, string="Zdroj")

    def _line_tracking_desc(self):
        return self.env._("Hodnota benchmarku")
