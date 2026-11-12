{
    "name": "Investra Entity",
    "summary": "Registr účetních knih a role účtů",
    "version": "20.0.0.6.0",
    "category": "Accounting",
    "author": "Investra",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": [
        "security/groups.xml",
        "security/ir.access.csv",
        "data/account_role.xml",
        "views/entity_views.xml",
    ],
    "installable": True,
    "application": False,
}
