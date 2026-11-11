{
    "name": "Investra Counterparty",
    "summary": "Registr protistran a emitentů: země, sektor ESA 2010, LEI, s platností od data",
    "version": "20.0.0.2.0",
    "category": "Accounting",
    "author": "Investra",
    "license": "LGPL-3",
    "depends": ["investra_instruments"],
    "data": ["security/ir.access.csv", "data/esa_sector.xml", "views/counterparty_views.xml"],
    "installable": True,
    "application": False,
}
