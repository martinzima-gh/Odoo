# Fiktivní data pro ladění vzhledu – JEN databáze investra_vzhled. Spouští se v `odoo shell`.
# Postup kopíruje testy investra_nav (tests/common.py): stejné funkce jako tlačítka v UI.
# Spuštění (z ~/odoo-dev): docker compose -f docker-compose.investra.yml run --rm --no-deps -T odoo odoo shell \
#   --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/custom -d investra_vzhled \
#   --db-filter="^investra_vzhled$" --no-http --max-cron-threads=0 < tools/vzhled_fiktivni_data.py
# Fondy zakládá znovu (nové společnosti); podruhé spouštět jen do čerstvé kopie investra_vzhled.
import random
from datetime import date

assert env.cr.dbname == "investra_vzhled", env.cr.dbname
random.seed(20261113)

MONTH_ENDS = ["2026-01-31", "2026-02-28", "2026-03-31", "2026-04-30", "2026-05-31", "2026-06-30",
              "2026-07-31", "2026-08-31", "2026-09-30", "2026-10-31"]
czk = env.ref("base.CZK")


def user(login, name, group):
    found = env["res.users"].with_context(active_test=False).search([("login", "=", login)])
    if found:
        return found
    return env["res.users"].create({
        "name": name, "login": login,
        "group_ids": [(6, 0, [env.ref("base.group_user").id, env.ref(group).id])],
    })


preparer = user("vzhled_priprava", "Petra Přípravová (smyšlená)", "investra_entity.group_valuation_preparer")
approver = user("vzhled_schvaleni", "Jan Schvalovatel (smyšlený)", "investra_entity.group_valuation_approver")
admin = env.ref("base.user_admin")

INSTRUMENTS = [  # název, typ, výchozí cena, měsíční volatilita
    ("Akcie Severní energie (smyšlená)", "equity", 820.0, 0.05),
    ("Akcie Pražské technologie (smyšlená)", "equity", 1450.0, 0.08),
    ("Akcie Moravské strojírny (smyšlená)", "equity", 365.0, 0.04),
    ("Podílový fond Stabilita (smyšlený)", "fund", 1.2500, 0.015),
]


def make_fund(name, tail):
    """tail = stavy posledních ocenění od nejstaršího; před nimi jsou ocenění zveřejněná."""
    book = env["investra.entity"].create_book(name, "fund", "cas501", czk, "investra_fund")
    company = book.company_id
    for u in (preparer, approver, admin):
        u.write({"company_ids": [(4, company.id)]})
    fenv = env(context=dict(env.context, allowed_company_ids=[company.id]))
    fund = fenv["investra.fund"].create({"entity_id": book.id, "launch_date": "2025-12-31"})
    classes = fenv["investra.fund.class"]
    for code, cname in (("A", "Třída A – růstová"), ("B", "Třída B – institucionální")):
        classes |= fenv["investra.fund.class"].create({"fund_id": fund.id, "code": code, "name": cname, "currency_id": czk.id})

    def movement(fund_class, day, amount, units, kind="subscription"):
        m = fenv["investra.class.movement"].create({
            "class_id": fund_class.id, "date": day, "manual_reason": "Fiktivní data pro vzhled",
            "movement_type": kind, "amount": amount, "units": units,
        })
        m._book()

    movement(classes[0], "2026-01-02", 60_000_000, 60_000)
    movement(classes[1], "2026-01-02", 40_000_000, 40_000)

    portfolio = fund.portfolio_ids.filtered(lambda p: p.business_model == "fair_value")[:1] or \
        fenv["investra.fund.portfolio"].create({"fund_id": fund.id, "name": "Reálná hodnota", "business_model": "fair_value"})

    instruments = []
    for iname, kind, start, vol in INSTRUMENTS:
        inst = fenv["investra.instrument"].create({
            "name": f"{iname} – {name.split()[2]}", "currency_id": czk.id,
            "type_id": env.ref(f"investra_instruments.type_{kind}").id,
        })
        fenv["investra.portfolio.classification"].create({
            "portfolio_id": portfolio.id, "instrument_id": inst.id, "valid_from": "2025-12-31",
        })
        # Ceny: náhodná procházka, k nákupu 5. 1. a ke každému konci měsíce.
        price, prices = start, {}
        for day in ["2026-01-05"] + MONTH_ENDS:
            price = round(price * (1 + random.gauss(0.004, vol)), 4 if kind == "fund" else 2)
            prices[day] = price
            p = fenv["investra.instrument.price"].with_user(preparer).create({
                "fund_id": fund.id, "instrument_id": inst.id, "date": day, "price": price, "source": "Fiktivní data",
            })
            p.with_user(approver).action_approve()
        instruments.append((inst, prices, kind))

    def trade(inst, day, settle, qty, price, side=None, state="settled"):
        vals = {"fund_id": fund.id, "portfolio_id": portfolio.id, "instrument_id": inst.id, "trade_date": day,
                "settlement_date": settle, "quantity": qty, "price": price, "fx_rate": 1}
        t = fenv["investra.trade"].with_user(preparer).create(vals)
        if state in ("unsettled", "settled"):
            t.action_book()
        if state == "settled":
            t.action_settle()
        return t

    # Nákupy 5. 1. za zhruba 85 % kapitálu, dokupy a prodeje během roku.
    weights = [0.30, 0.20, 0.15, 0.20]
    held = {}
    for (inst, prices, kind), w in zip(instruments, weights):
        qty = int(100_000_000 * w / prices["2026-01-05"])
        trade(inst, "2026-01-05", "2026-01-07", qty, prices["2026-01-05"])
        held[inst] = qty
    inst, prices, _ = instruments[1]
    trade(inst, "2026-04-15", "2026-04-17", -int(held[inst] * 0.25), round(prices["2026-03-31"] * 1.01, 2))
    inst, prices, _ = instruments[2]
    trade(inst, "2026-06-10", "2026-06-12", int(held[inst] * 0.30), round(prices["2026-05-31"] * 0.99, 2))

    # Pohyby investorů během roku.
    movement(classes[0], "2026-03-16", 5_000_000, 4_900)
    movement(classes[0], "2026-07-15", 3_000_000, 2_850, kind="redemption")

    # Ocenění měsíc po měsíci.
    states = ["published"] * (len(MONTH_ENDS) - len(tail)) + list(tail)
    for day, target in zip(MONTH_ENDS, states):
        v = fenv["investra.valuation"].with_user(preparer).create({"fund_id": fund.id, "date": day, "version": 1})
        if target == "draft":
            continue
        v.action_compute()
        if target == "computed":
            continue
        v.action_submit()
        if target == "submitted":
            continue
        v.with_user(approver).action_approve()
        if target == "approved":
            continue
        v.action_post()
        if target == "posted":
            continue
        v.action_send_depositary()
        if target == "sent":
            continue
        v.with_user(approver).action_depositary_confirm()
        if target == "confirmed":
            continue
        v.with_user(approver).action_publish()

    # Obchody po posledním ocenění: sjednané nevypořádané a návrhy.
    inst, prices, _ = instruments[0]
    trade(inst, "2026-11-04", "2026-11-18", 2_000, round(prices["2026-10-31"] * 1.005, 2), state="unsettled")
    inst, prices, _ = instruments[3]
    trade(inst, "2026-11-10", "2026-11-12", 400_000, round(prices["2026-10-31"], 4), state="unsettled")
    inst, prices, _ = instruments[2]
    trade(inst, "2026-11-12", "2026-11-14", 5_000, round(prices["2026-10-31"] * 1.02, 2), state="draft")
    inst, prices, _ = instruments[1]
    trade(inst, "2026-11-13", "2026-11-17", -1_000, round(prices["2026-10-31"] * 0.98, 2), state="draft")
    return fund


for fname, tail in (
    ("Fond Vzhled Orion (smyšlený)", ("confirmed", "sent", "posted", "approved")),
    ("Fond Vzhled Lyra (smyšlený)", ("published", "submitted")),
    ("Fond Vzhled Vega (smyšlený)", ("computed",)),
):
    fund = make_fund(fname, tail)
    env.cr.commit()
    vals = env["investra.valuation"].search([("fund_id", "=", fund.id)], order="date")
    trades = env["investra.trade"].search([("fund_id", "=", fund.id)])
    print("HOTOVO", fname, [(str(v.date), v.state) for v in vals],
          {st: len(trades.filtered(lambda t: t.state == st)) for st in set(trades.mapped("state"))}, flush=True)
