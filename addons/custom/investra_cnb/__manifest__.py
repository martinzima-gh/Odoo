{
    "name": "Investra CNB",
    "summary": "Převodová tabulka rolí účtů na řádky výkazů ČNB s platností",
    "version": "20.0.0.7.0",
    "category": "Accounting",
    "author": "Investra",
    "license": "LGPL-3",
    "depends": ["investra_instruments"],
    "data": ["security/ir.access.csv", "data/cnb_map.xml", "views/cnb_views.xml"],
    "installable": True,
    "application": False,
}
