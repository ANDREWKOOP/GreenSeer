"""Reproduce the public W. H. Sammis source-intensity result card."""

from datetime import date
from pathlib import Path
import sys


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from greenseer_public.contracts import EvidenceInventory, InterventionRecord
from greenseer_public.router import route_intervention
from greenseer_public.source_intensity import calculate_period_intensity, compare_periods, load_monthly_rows


rows = load_monthly_rows(ROOT / "docs" / "data" / "sammis-monthly.csv")
pre = calculate_period_intensity(rows, date(2007, 1, 1), date(2009, 12, 1))
post = calculate_period_intensity(rows, date(2011, 1, 1), date(2013, 12, 1))
comparison = compare_periods(pre, post)
route = route_intervention(
    InterventionRecord("EPA_FGD_2866_1_2010-03-11", "power", "scrubber", date(2010, 3, 11), ("SO2",)),
    EvidenceInventory(source_months=True, ambient_measurements=True),
)

print("GreenSeer public example - W. H. Sammis unit 1")
print(f"Pre-period intensity (2007-2009):  {pre.lb_per_mmbtu:.3f} {pre.unit}")
print(f"Post-period intensity (2011-2013): {post.lb_per_mmbtu:.3f} {post.unit}")
print(f"Observed decrease:                  {comparison.decrease_percent:.2f}%")
print(f"Selected template:                 {route.template_id}")
print(f"Evidence label:                    {comparison.evidence_type}")
print(f"Causal effect estimated:           {comparison.causal_effect}")
