import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class DocumentationTests(unittest.TestCase):
    def setUp(self):
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_readme_has_positioning_team_metrics_and_quick_start(self):
        required = [
            "auto-ML-inspired environmental intervention intelligence system",
            "Andrew Kutsch",
            "Gamid Muratbekov",
            "Adil Syed",
            "12,811 searchable intervention and evidence records",
            "4,815 EPA ambient monitoring sites",
            "36 completed source-level intervention comparisons",
            "1,197 retained intervention-to-nearby-air comparison links",
            "Quick start",
            "Repository map",
            "SAS Viya",
            "Limitations",
        ]
        for phrase in required:
            self.assertIn(phrase, self.readme)

    def test_readme_separates_implemented_prototype_and_future_scope(self):
        self.assertIn("Implemented", self.readme)
        self.assertIn("Prototype", self.readme)
        self.assertIn("Future scope", self.readme)
        self.assertIn("tenant is no longer live", self.readme)
        self.assertNotRegex(self.readme, r"https?://[^\s\"')]*engage\.sas\.com")
        for forbidden in ("12,811 policies", "proves which policy", "fully autonomous AutoML"):
            self.assertNotIn(forbidden.lower(), self.readme.lower())

    def test_technical_docs_and_source_names_exist(self):
        docs = [
            ROOT / "docs" / "architecture.md",
            ROOT / "docs" / "evidence-and-limitations.md",
            ROOT / "docs" / "data-sources.md",
            ROOT / "docs" / "sas-viya-implementation.md",
        ]
        for path in docs:
            self.assertTrue(path.exists(), path.name)
            self.assertGreater(len(path.read_text(encoding="utf-8")), 300)
        sources = (ROOT / "docs" / "data-sources.md").read_text(encoding="utf-8")
        for name in ("EPA CAMPD", "EPA AQS AirData", "NOAA NCEI", "DOE AFDC", "original studies"):
            self.assertIn(name, sources)

    def test_public_media_is_manifested_and_below_release_limit(self):
        manifest = json.loads((ROOT / "media" / "media-manifest.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(manifest["items"]), 2)
        for item in manifest["items"]:
            path = ROOT / item["file"]
            self.assertTrue(path.exists(), item["file"])
            self.assertLess(path.stat().st_size, 50_000_000, item["file"])
            self.assertTrue(item["source_artifact"])
            self.assertTrue(item["edits"])
            self.assertTrue(item["license_status"])


if __name__ == "__main__":
    unittest.main()
