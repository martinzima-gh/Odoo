{
    "name": "Investra Rates",
    "summary": "Kurzy ČNB a ECB se zdrojem a datem stažení",
    "version": "20.0.0.2.0",
    "category": "Accounting",
    "author": "Investra",
    "license": "LGPL-3",
    "depends": ["investra_entity", "mail"],
    "data": [
        "security/ir.access.csv", "data/cron.xml", "data/validity.xml",
        "views/rate_views.xml", "views/validity_views.xml",
    ],
    "installable": True,
    "application": False,
}
