import os
import re
import unittest

from src.configwebui import ConfigEditor


class TestOfflineAssets(unittest.TestCase):
    def setUp(self):
        self.editor = ConfigEditor(
            app_name="OfflineTest",
            schema={"type": "object", "properties": {"a": {"type": "string"}}},
        )
        self.editor.app.config["TESTING"] = True
        self.client = self.editor.app.test_client()
        self.static_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src",
            "configwebui",
            "static"
        )
        self.template_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src",
            "configwebui",
            "templates"
        )

    def test_no_external_resources_in_html(self):
        index_html_path = os.path.join(self.template_dir, "index.html")
        with open(index_html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Find all script src and link href
        script_sources = re.findall(r'<script[^>]+src=["\'](.*?)["\']', html_content, re.IGNORECASE)
        link_hrefs = re.findall(r'<link[^>]+href=["\'](.*?)["\']', html_content, re.IGNORECASE)

        all_urls = script_sources + link_hrefs
        for url in all_urls:
            # Must not be an external URL
            self.assertFalse(
                url.startswith("http://") or url.startswith("https://") or url.startswith("//"),
                f"Found external CDN URL in HTML: {url}"
            )
            # Must be local /static URL
            self.assertTrue(url.startswith("/static/"), f"URL does not start with /static/: {url}")

    def test_static_assets_served_by_flask(self):
        assets_to_test = [
            "/static/css/bootstrap.min.css",
            "/static/css/fontawesome.all.css",
            "/static/css/index.css",
            "/static/js/jquery.slim.min.js",
            "/static/js/bootstrap.bundle.min.js",
            "/static/js/jsoneditor.min.js",
            "/static/js/index.js",
            "/static/icon/favicon.ico",
            "/static/icon/favicon-96x96.png",
            "/static/icon/apple-touch-icon.png",
            "/static/icon/site.webmanifest",
            "/static/webfonts/fa-solid-900.woff2",
            "/static/webfonts/fa-regular-400.woff2",
            "/static/webfonts/fa-brands-400.woff2",
        ]

        for asset_url in assets_to_test:
            resp = self.client.get(asset_url)
            self.assertEqual(
                resp.status_code, 200, f"Static asset returned status {resp.status_code}: {asset_url}"
            )
            self.assertGreater(len(resp.data), 0, f"Asset data is empty: {asset_url}")
            resp.close()


if __name__ == "__main__":
    unittest.main()
