import posixpath
import re

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTheme(TransactionCase):
    def _bundle_urls(self):
        bundle = self.env["ir.qweb"]._get_asset_bundle("web.assets_backend", js=False)
        return [f.get("url") or "" for f in bundle.files]

    def test_theme_files_in_backend_bundle(self):
        urls = self._bundle_urls()
        for name in ("primary_variables.scss", "fonts.scss", "theme.scss"):
            self.assertTrue(any(u.endswith("investra_theme/static/src/scss/" + name) for u in urls), name)

    def test_variables_before_odoo_defaults(self):
        # Proměnné Investra musí být před primary_variables.scss z web, jinak !default vyhraje Odoo.
        urls = self._bundle_urls()
        ours = next(i for i, u in enumerate(urls) if u.endswith("investra_theme/static/src/scss/primary_variables.scss"))
        odoo = next(i for i, u in enumerate(urls) if u.endswith("web/static/src/scss/primary_variables.scss"))
        self.assertLess(ours, odoo)

    def test_compiled_css_uses_brand(self):
        # Zkompiluje SCSS backendu: chyba kompilace i chybějící barva nebo písmo testem neprojdou.
        bundle = self.env["ir.qweb"]._get_asset_bundle("web.assets_backend", js=False)
        css = b"".join(bundle.css().mapped("raw")).decode().lower()
        self.assertFalse(bundle.css_errors, bundle.css_errors)
        self.assertNotIn("css error message", css)
        self.assertIn("#112e3c", css)  # Petroleum
        self.assertIn("#0b5156", css)  # Lagoon
        self.assertIn("#e8ebec", css)  # Petroleum 4 – pozadí aplikace
        self.assertIn("#eb5b1f", css)  # Ember – akcent lišty
        self.assertIn("montserrat-semibold.ttf", css)
        # Adresa písma musí po normalizaci vést do /web/static (dříve vedla na 404).
        urls = [u.strip("'\"") for u in re.findall(r"url\(([^)]*montserrat[^)]*)\)", css)]
        self.assertTrue(urls)
        for url in urls:
            self.assertTrue(posixpath.normpath(url).startswith("/web/static/fonts/google/montserrat/"), url)
        self.assertNotIn("fonts.googleapis.com", css)
