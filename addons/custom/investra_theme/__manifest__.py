{
    "name": "Investra Theme",
    "summary": "Firemní identita Investra ve vzhledu Odoo: barvy a písmo podle Brand manuálu 1.0",
    "version": "20.0.0.1.0",
    "category": "Hidden",
    "author": "Investra",
    "license": "LGPL-3",
    "depends": ["web"],
    "assets": {
        # Proměnné musí být před výchozími hodnotami Odoo (ty jsou !default), proto prepend.
        "web._assets_primary_variables": [
            ("prepend", "investra_theme/static/src/scss/primary_variables.scss"),
        ],
        "web.assets_backend": [
            "investra_theme/static/src/scss/fonts.scss",
            "investra_theme/static/src/scss/theme.scss",
        ],
    },
    "installable": True,
    "application": False,
}
