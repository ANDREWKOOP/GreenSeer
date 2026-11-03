import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).parents[1]
DOCS = ROOT / "docs"


class ContractParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1_count = 0
        self.ids = set()
        self.local_refs = []
        self.skip_links = []
        self.noscript_text = []
        self._in_noscript = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        if values.get("id"):
            self.ids.add(values["id"])
        if tag == "a" and "skip-link" in values.get("class", ""):
            self.skip_links.append(values.get("href"))
        if tag == "noscript":
            self._in_noscript = True
        for key in ("href", "src"):
            value = values.get(key, "")
            if value and not value.startswith(("#", "http://", "https://", "mailto:")):
                self.local_refs.append(value.split("?")[0].split("#")[0])

    def handle_endtag(self, tag):
        if tag == "noscript":
            self._in_noscript = False

    def handle_data(self, data):
        if self._in_noscript:
            self.noscript_text.append(data)


class SiteContractTests(unittest.TestCase):
    def setUp(self):
        self.html_path = DOCS / "index.html"
        self.css_path = DOCS / "styles.css"
        self.js_path = DOCS / "app.js"

    def test_semantic_sections_and_accessible_fallback_exist(self):
        html = self.html_path.read_text(encoding="utf-8")
        parser = ContractParser()
        parser.feed(html)
        self.assertEqual(1, parser.h1_count)
        self.assertTrue({"overview", "workflow", "evidence", "models", "sas", "sources"}.issubset(parser.ids))
        self.assertIn("#main-content", parser.skip_links)
        fallback = " ".join(parser.noscript_text).lower()
        self.assertIn("environmental intervention", fallback)
        self.assertIn("evidence", fallback)

    def test_all_local_assets_exist_and_no_private_sas_tenant_is_linked(self):
        html = self.html_path.read_text(encoding="utf-8")
        parser = ContractParser()
        parser.feed(html)
        for reference in parser.local_refs:
            self.assertTrue((DOCS / reference).exists(), reference)
        self.assertNotRegex(html, r"https?://[^\s\"']*engage\.sas\.com")

    def test_site_loads_only_local_payload_and_exposes_public_functions(self):
        js = self.js_path.read_text(encoding="utf-8")
        self.assertIn("async function loadProjectData", js)
        self.assertIn("function selectSector", js)
        self.assertIn("function selectCase", js)
        self.assertIn("data/project.json", js)
        self.assertNotRegex(js, r"fetch\(\s*['\"]https?://")

    def test_responsive_contract_and_no_oversized_fixed_layout(self):
        css = self.css_path.read_text(encoding="utf-8")
        self.assertRegex(css, r"@media\s*\([^)]*max-width")
        self.assertNotRegex(css, r"width:\s*(?:1[3-9]\d\d|[2-9]\d{3,})px")
        self.assertIn("max-width: 100%", css)

    def test_sector_assets_have_auditable_manifest(self):
        manifest = json.loads((DOCS / "assets" / "asset-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(4, len(manifest["assets"]))
        for item in manifest["assets"]:
            self.assertEqual("ai_generated_illustration", item["status"])
            self.assertTrue((DOCS / item["file"]).exists())
            self.assertTrue(item["source_artifact"])


if __name__ == "__main__":
    unittest.main()
