{
    "name": "Investra Rates",
    "summary": "Kurzy ČNB a ECB se zdrojem a datem stažení",
    "version": "20.0.0.1.0",
    "category": "Accounting",
    "author": "Investra",
    "license": "LGPL-3",
    "depends": ["investra_entity"],
    "data": ["security/ir.access.csv", "data/cron.xml", "views/rate_views.xml"],
    "installable": True,
    "application": False,
}
