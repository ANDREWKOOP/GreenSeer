import sys
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from greenseer_public.contracts import EvidenceInventory, InterventionRecord
from greenseer_public.router import route_intervention


class RouterTests(unittest.TestCase):
    def test_power_source_case_routes_to_source_intensity_without_causal_claim(self):
        record = InterventionRecord("power-1", "power", "scrubber", date(2010, 3, 11), ("SO2",))
        evidence = EvidenceInventory(source_months=True, ambient_measurements=True, comparison_units=False, weather=False)
        decision = route_intervention(record, evidence)
        self.assertTrue(decision.eligible)
        self.assertEqual("source_intensity_existing_v1", decision.template_id)
        self.assertEqual("observed_source_change", decision.evidence_status)
        self.assertFalse(decision.causal_eligible)
        self.assertIn("source-level", " ".join(decision.reasons).lower())

    def test_ambient_only_case_routes_to_descriptive_template(self):
        record = InterventionRecord("industrial-1", "industrial", "retirement", date(2016, 1, 1), ("SO2",))
        evidence = EvidenceInventory(source_months=False, ambient_measurements=True, comparison_units=False, weather=False)
        decision = route_intervention(record, evidence)
        self.assertTrue(decision.eligible)
        self.assertEqual("ambient_period_summary_v1", decision.template_id)
        self.assertEqual("observed_ambient_change", decision.evidence_status)
        self.assertFalse(decision.causal_eligible)

    def test_missing_operational_date_requires_review(self):
        record = InterventionRecord("unknown-1", "transport", "incentive", None, ("NO2",))
        evidence = EvidenceInventory(source_months=False, ambient_measurements=True, comparison_units=True, weather=True)
        decision = route_intervention(record, evidence)
        self.assertFalse(decision.eligible)
        self.assertEqual("review_required", decision.template_id)
        self.assertFalse(decision.causal_eligible)
        self.assertIn("operational start", " ".join(decision.reasons).lower())


if __name__ == "__main__":
    unittest.main()
