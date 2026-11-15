{
    "name": "Investra Dashboard",
    "summary": "Přehled fondů: stav ocenění, výjimky a termíny ČNB",
    "version": "20.0.0.5.0",
    "category": "Accounting",
    "author": "Investra",
    "license": "LGPL-3",
    "depends": ["investra_nav"],
    "data": ["security/ir.access.csv", "views/dashboard_views.xml"],
    "assets": {
        "web.assets_backend": [
            "investra_dashboard/static/src/fund_dashboard.scss",
            "investra_dashboard/static/src/fund_todo.js",
            "investra_dashboard/static/src/fund_todo.xml",
            "investra_dashboard/static/src/fund_summary.js",
            "investra_dashboard/static/src/fund_summary.xml",
        ],
    },
    "installable": True,
    "application": False,
}
