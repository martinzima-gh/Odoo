from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBanner(TransactionCase):
    def test_style_is_in_backend_bundle(self):
        bundle = self.env["ir.qweb"]._get_asset_bundle("web.assets_backend", js=False)
        self.assertTrue(any("investra_env_banner" in (f.get("url") or "") for f in bundle.files))
