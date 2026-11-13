{
    "name": "Investra NAV",
    "summary": "Pravidla úplat, ocenění, NAV tříd, schvalování a balíček pro depozitáře",
    "version": "20.0.0.28.0",
    "category": "Accounting",
    "author": "Investra",
    "license": "LGPL-3",
    "depends": ["investra_instruments", "investra_allocation", "investra_fx_revaluation"],
    "data": ["security/ir.access.csv", "data/cron.xml", "views/nav_views.xml", "views/lock_exception_views.xml", "views/trade_views.xml"],
    "assets": {
        "web.assets_backend": [
            "investra_nav/static/src/valuation_summary/valuation_summary.js",
            "investra_nav/static/src/valuation_summary/valuation_summary.xml",
            "investra_nav/static/src/valuation_summary/valuation_summary.scss",
        ],
    },
    "installable": True,
    "application": False,
}
