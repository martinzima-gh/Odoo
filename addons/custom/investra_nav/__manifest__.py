{
    "name": "Investra NAV",
    "summary": "Pravidla úplat, ocenění, NAV tříd, schvalování a balíček pro depozitáře",
    "version": "20.0.0.17.0",
    "category": "Accounting",
    "author": "Investra",
    "license": "LGPL-3",
    "depends": ["investra_instruments", "investra_allocation"],
    "data": ["security/ir.access.csv", "data/cron.xml", "views/nav_views.xml", "views/lock_exception_views.xml"],
    "installable": True,
    "application": False,
}
