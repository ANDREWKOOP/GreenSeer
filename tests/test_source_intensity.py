import csv
import sys
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from greenseer_public.source_intensity import (
    MonthlySourceRow,
    calculate_period_intensity,
    compare_periods,
    load_monthly_rows,
)


class SourceIntensityTests(unittest.TestCase):
    def test_intensity_is_total_pounds_divided_by_total_heat(self):
        rows = [
            MonthlySourceRow(date(2020, 1, 1), 1.0, 100.0),
            MonthlySourceRow(date(2020, 2, 1), 3.0, 300.0),
        ]
        result = calculate_period_intensity(rows, date(2020, 1, 1), date(2020, 2, 1))
        self.assertAlmostEqual(20.0, result.lb_per_mmbtu)
        self.assertEqual(2, result.months)

    def test_dates_are_inclusive_and_outside_rows_are_ignored(self):
        rows = [
            MonthlySourceRow(date(2019, 12, 1), 99.0, 1.0),
            MonthlySourceRow(date(2020, 1, 1), 1.0, 1000.0),
            MonthlySourceRow(date(2020, 2, 1), 1.0, 1000.0),
            MonthlySourceRow(date(2020, 3, 1), 99.0, 1.0),
        ]
        result = calculate_period_intensity(rows, date(2020, 1, 1), date(2020, 2, 1))
        self.assertAlmostEqual(2.0, result.lb_per_mmbtu)
        self.assertEqual(2, result.months)

    def test_zero_or_absent_heat_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "heat input"):
            calculate_period_intensity([MonthlySourceRow(date(2020, 1, 1), 1.0, 0.0)], date(2020, 1, 1), date(2020, 1, 1))
        with self.assertRaisesRegex(ValueError, "No monthly rows"):
            calculate_period_intensity([], date(2020, 1, 1), date(2020, 1, 1))

    def test_comparison_reports_decrease_and_percentage(self):
        pre = calculate_period_intensity([MonthlySourceRow(date(2020, 1, 1), 1.0, 1000.0)], date(2020, 1, 1), date(2020, 1, 1))
        post = calculate_period_intensity([MonthlySourceRow(date(2021, 1, 1), .25, 1000.0)], date(2021, 1, 1), date(2021, 1, 1))
        comparison = compare_periods(pre, post)
        self.assertAlmostEqual(-1.5, comparison.post_minus_pre)
        self.assertAlmostEqual(75.0, comparison.decrease_percent)

    def test_retained_sammis_values_match_public_card(self):
        rows = load_monthly_rows(ROOT / "docs" / "data" / "sammis-monthly.csv")
        pre = calculate_period_intensity(rows, date(2007, 1, 1), date(2009, 12, 1))
        post = calculate_period_intensity(rows, date(2011, 1, 1), date(2013, 12, 1))
        comparison = compare_periods(pre, post)
        self.assertAlmostEqual(1.263998535, pre.lb_per_mmbtu, places=8)
        self.assertAlmostEqual(0.166628387, post.lb_per_mmbtu, places=8)
        self.assertAlmostEqual(86.817359, comparison.decrease_percent, places=5)
        self.assertEqual("lb SO2/MMBtu", pre.unit)


if __name__ == "__main__":
    unittest.main()
