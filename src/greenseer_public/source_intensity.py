"""Transparent source-emissions-intensity calculations for the public example."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class MonthlySourceRow:
    month: date
    so2_short_tons: float
    heat_input_mmbtu: float


@dataclass(frozen=True)
class PeriodIntensity:
    start: date
    end: date
    months: int
    so2_short_tons: float
    heat_input_mmbtu: float
    lb_per_mmbtu: float
    unit: str = "lb SO2/MMBtu"


@dataclass(frozen=True)
class IntensityComparison:
    pre: PeriodIntensity
    post: PeriodIntensity
    post_minus_pre: float
    decrease_percent: float
    evidence_type: str = "observed_source_change"
    causal_effect: bool = False


def load_monthly_rows(path: Path) -> list[MonthlySourceRow]:
    rows: list[MonthlySourceRow] = []
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        for item in csv.DictReader(handle):
            rows.append(
                MonthlySourceRow(
                    month=date.fromisoformat(f"{item['month']}-01"),
                    so2_short_tons=float(item["so2_short_tons"]),
                    heat_input_mmbtu=float(item["heat_input_mmbtu"]),
                )
            )
    return rows


def calculate_period_intensity(rows: Iterable[MonthlySourceRow], start: date, end: date) -> PeriodIntensity:
    """Calculate total SO2 pounds / total fuel-energy input for inclusive months."""
    selected = [row for row in rows if start <= row.month <= end]
    if not selected:
        raise ValueError("No monthly rows fall inside the requested period")
    total_heat = sum(row.heat_input_mmbtu for row in selected)
    if total_heat <= 0:
        raise ValueError("The selected period must have positive heat input")
    total_tons = sum(row.so2_short_tons for row in selected)
    intensity = total_tons * 2000.0 / total_heat
    return PeriodIntensity(start, end, len(selected), total_tons, total_heat, intensity)


def compare_periods(pre: PeriodIntensity, post: PeriodIntensity) -> IntensityComparison:
    if pre.lb_per_mmbtu <= 0:
        raise ValueError("Pre-period intensity must be positive for a percentage comparison")
    change = post.lb_per_mmbtu - pre.lb_per_mmbtu
    decrease = (pre.lb_per_mmbtu - post.lb_per_mmbtu) / pre.lb_per_mmbtu * 100.0
    return IntensityComparison(pre, post, change, decrease)
