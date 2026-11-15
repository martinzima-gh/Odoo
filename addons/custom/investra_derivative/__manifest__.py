{
    "name": "Investra Derivative",
    "summary": "FX spot, forward a swap: smlouva, nohy, ruční hodnota (zjednodušené řešení, docs/navrh-fx-derivaty.md)",
    "version": "20.0.0.1.0",
    "category": "Accounting",
    "author": "Investra",
    "license": "LGPL-3",
    "depends": ["investra_nav", "investra_counterparty", "investra_instrument_master"],
    "data": ["security/ir.access.csv", "views/derivative_views.xml"],
    "installable": True,
    "application": False,
}
