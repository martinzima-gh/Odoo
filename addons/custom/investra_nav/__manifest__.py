{
    "name": "Investra NAV",
    "summary": "Pravidla úplat, ocenění, NAV tříd, schvalování a balíček pro depozitáře",
    "version": "20.0.0.27.0",
    "category": "Accounting",
    "author": "Investra",
    "license": "LGPL-3",
    "depends": ["investra_instruments", "investra_allocation"],
    "data": ["security/ir.access.csv", "data/cron.xml", "views/nav_views.xml", "views/lock_exception_views.xml", "views/trade_views.xml"],
    "assets": {
        "web.assets_backend": [
            "investra_nav/static/src/class_price_chart/class_price_chart.js",
            "investra_nav/static/src/class_price_chart/class_price_chart.xml",
            "investra_nav/static/src/class_price_chart/class_price_chart.scss",
        ],
    },
    "installable": True,
    "application": False,
}
