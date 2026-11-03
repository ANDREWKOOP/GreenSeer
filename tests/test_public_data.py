import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PUBLIC_ROOT = Path(__file__).parents[1]
PROJECT_ROOT = PUBLIC_ROOT.parents[1]
MODULE_PATH = PUBLIC_ROOT / "scripts" / "build_public_data.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_public_data", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PublicDataTests(unittest.TestCase):
    def setUp(self):
        self.module = load_builder()
        self.payload = self.module.build_public_payload(PROJECT_ROOT)

    def test_scale_metrics_keep_counts_and_meanings_together(self):
        actual = {item["id"]: (item["value"], item["meaning"]) for item in self.payload["metrics"]}
        self.assertEqual((12811, "searchable intervention and evidence records"), actual["records"])
        self.assertEqual((4815, "EPA ambient monitoring sites represented in the retained archive"), actual["monitoring_sites"])
        self.assertEqual((36, "completed source-level intervention comparisons"), actual["source_comparisons"])
        self.assertEqual((1197, "retained intervention-to-nearby-air comparison links"), actual["nearby_air_comparisons"])

    def test_results_retain_context_and_claim_boundaries(self):
        required = {"place", "period", "outcome", "unit", "evidence_type", "source", "claim_boundary"}
        self.assertGreaterEqual(len(self.payload["cases"]), 4)
        for case in self.payload["cases"]:
            self.assertTrue(required.issubset(case), case.get("id"))
            self.assertTrue(case["source"])
            self.assertTrue(case["claim_boundary"])

    def test_sammis_is_source_intensity_not_ambient_or_causal(self):
        sammis = next(case for case in self.payload["cases"] if case["id"] == "sammis")
        self.assertEqual("source_emissions_intensity", sammis["outcome_type"])
        self.assertEqual("lb SO2/MMBtu", sammis["unit"])
        self.assertEqual("observed_source_change", sammis["evidence_type"])
        self.assertFalse(sammis["causal_effect"])

    def test_model_rows_share_one_later_evaluation_period(self):
        rows = self.payload["model_comparison"]
        self.assertEqual({"2013-01 through 2013-12"}, {row["evaluation_period"] for row in rows})
        self.assertEqual({"lb SO2/MMBtu"}, {row["unit"] for row in rows})
        self.assertEqual({"test"}, {row["block"] for row in rows})
        self.assertEqual(4, len(rows))

    def test_writer_creates_parseable_compact_outputs(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp_dir:
            output = Path(temp_dir)
            report = self.module.write_public_outputs(PROJECT_ROOT, output)
            self.assertEqual(4, report["file_count"])
            project = json.loads((output / "project.json").read_text(encoding="utf-8"))
            self.assertEqual("GreenSeer", project["project"])
            self.assertTrue((output / "sammis-monthly.csv").exists())
            self.assertTrue((output / "model-comparison.csv").exists())
            manifest = json.loads((output / "source-manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(all(item["public_url"].startswith("https://") for item in manifest["sources"]))


if __name__ == "__main__":
    unittest.main()
