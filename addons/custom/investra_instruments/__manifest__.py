{
    "name": "Investra Instruments",
    "summary": "Nástroje, ceny a pozice",
    "version": "20.0.0.7.0",
    "category": "Accounting",
    "author": "Investra",
    "license": "LGPL-3",
    "depends": ["investra_posting", "investra_rates", "investra_fund"],
    "data": ["security/ir.access.csv", "data/instrument_type.xml", "views/instrument_views.xml"],
    "installable": True,
    "application": False,
}
