"""Build the compact, auditable data package used by the public GreenSeer site."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


CASE_IDS = (
    "EPA_FGD_2866_1_2010-03-11",
    "residential_fairbanks_2020",
    "TRANSPORT_EUREKA_ELECTRIC_SCHOOL_BUS",
    "INDUSTRIAL_SHENANGO_COKE_2016",
)

PUBLIC_IDS = {
    "EPA_FGD_2866_1_2010-03-11": "sammis",
    "residential_fairbanks_2020": "fairbanks",
    "TRANSPORT_EUREKA_ELECTRIC_SCHOOL_BUS": "eureka-school-bus",
    "INDUSTRIAL_SHENANGO_COKE_2016": "shenango",
}

MODEL_LABELS = {
    "mean": "Training-average baseline",
    "ridge": "Ridge regression",
    "hist_gradient_boosting": "Histogram gradient boosting",
    "catboost": "CatBoost",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalise_unit(value: str | None) -> str:
    unit = (value or "Not reported").strip()
    replacements = {
        "lb SO₂ / million Btu": "lb SO2/MMBtu",
        "lb SO2/million Btu": "lb SO2/MMBtu",
        "lb SO₂/million Btu": "lb SO2/MMBtu",
    }
    return replacements.get(unit, unit)


def _first_public_source(case: dict[str, Any]) -> str:
    for citation in case.get("citations", []):
        if isinstance(citation, dict) and str(citation.get("url", "")).startswith("https://"):
            return str(citation["url"])
    classification_source = case.get("classification", {}).get("source", {}).get("citation", "")
    if str(classification_source).startswith("https://"):
        return str(classification_source)
    return "https://www.epa.gov/data"


def _case_unit(case: dict[str, Any]) -> str:
    summary = case.get("summary", {})
    if summary.get("unit"):
        return _normalise_unit(str(summary["unit"]))
    for metric in case.get("metrics", []):
        if metric.get("unit") and metric.get("unit") != "percent":
            return _normalise_unit(str(metric["unit"]))
    return "See source record"


def _case_period(case: dict[str, Any]) -> str:
    if case.get("display_period"):
        return str(case["display_period"])
    dates = case.get("dates", {})
    before = dates.get("before") or dates.get("pre")
    after = dates.get("after") or dates.get("post")
    if before and after:
        return f"{before} versus {after}"
    for metric in case.get("metrics", []):
        if metric.get("period"):
            return str(metric["period"])
    return "Period reported in the cited source"


def _public_case(case: dict[str, Any]) -> dict[str, Any]:
    raw_id = str(case["id"])
    route = case.get("route", {})
    result = {
        "id": PUBLIC_IDS[raw_id],
        "canonical_intervention_id": raw_id,
        "title": case.get("title", raw_id),
        "sector": case.get("sector", "unclassified"),
        "place": case.get("location_label") or case.get("location", {}).get("name") or "Location in cited record",
        "period": _case_period(case),
        "outcome": case.get("outcome", "Outcome in cited record"),
        "unit": _case_unit(case),
        "evidence_type": case.get("evidence_type", route.get("claim_type", "descriptive_record")),
        "source": _first_public_source(case),
        "finding": case.get("finding", "See the cited record"),
        "interpretation": case.get("interpretation") or case.get("allowed_claim") or "Descriptive result from the retained evidence record.",
        "claim_boundary": "This retained comparison is descriptive; it does not by itself identify a causal policy effect.",
        "causal_effect": False,
        "template": route.get("template_id") or case.get("template_id") or case.get("method", {}).get("template_id"),
    }
    if raw_id == "EPA_FGD_2866_1_2010-03-11":
        result.update(
            {
                "outcome_type": "source_emissions_intensity",
                "unit": "lb SO2/MMBtu",
                "claim_boundary": "Observed sulfur-dioxide emissions intensity at one generating unit; not ambient concentration or a causal effect.",
                "observed_before": case.get("summary", {}).get("before"),
                "observed_after": case.get("summary", {}).get("after"),
                "observed_decrease_percent": case.get("metrics", [{}])[0].get("value"),
            }
        )
    return result


def _model_comparison(project_root: Path) -> list[dict[str, Any]]:
    path = project_root / "deliverables/model_intelligence_portfolio/v1/cases/sammis/metrics.csv"
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row["block"] != "test":
                continue
            rows.append(
                {
                    "model": MODEL_LABELS.get(row["model"], row["model"]),
                    "model_id": row["model"],
                    "block": "test",
                    "n_months": int(row["n"]),
                    "mae": float(row["mae"]),
                    "rmse": float(row["rmse"]),
                    "mean_error": float(row["mean_error"]),
                    "unit": "lb SO2/MMBtu",
                    "evaluation_period": "2013-01 through 2013-12",
                    "meaning": "Lower RMSE means predictions were closer to the measured monthly source intensity in the held-out period.",
                    "causal_effect": False,
                }
            )
    return rows


def _prediction_contributions(project_root: Path) -> list[dict[str, Any]]:
    path = project_root / "deliverables/model_intelligence_portfolio/v1/cases/sammis/shap_global.csv"
    if not path.exists():
        return []
    labels = {
        "post_start": "After reported equipment start",
        "relative_time": "Position in time",
        "log_heat_input": "Fuel-energy activity",
        "month_sin": "Seasonal cycle (sine)",
        "month_cos": "Seasonal cycle (cosine)",
    }
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row.get("block") != "test":
                continue
            rows.append(
                {
                    "feature": labels.get(row["feature"], row["feature"]),
                    "feature_id": row["feature"],
                    "mean_signed_contribution": float(row["mean_signed_shap"]),
                    "unit": "lb SO2/MMBtu of model prediction",
                    "meaning": "Predictive contribution in the held-out period; negative values moved the model prediction downward.",
                    "causal_effect": False,
                }
            )
    return rows


def build_public_payload(project_root: Path) -> dict[str, Any]:
    """Read retained artifacts and return one compact public-site payload."""
    project_root = Path(project_root).resolve()
    sector_data = _load_json(project_root / "deliverables/visual_workspace/v3/sector_data.json")
    cases = [_public_case(sector_data["cases"][case_id]) for case_id in CASE_IDS]
    return {
        "project": "GreenSeer",
        "tagline": "Taking pollution interventions to defensible insights, faster.",
        "scope": "Public portfolio artifact built from retained GreenSeer evidence and model outputs.",
        "metrics": [
            {"id": "records", "value": 12811, "meaning": "searchable intervention and evidence records"},
            {"id": "monitoring_sites", "value": 4815, "meaning": "EPA ambient monitoring sites represented in the retained archive"},
            {"id": "source_comparisons", "value": 36, "meaning": "completed source-level intervention comparisons"},
            {"id": "nearby_air_comparisons", "value": 1197, "meaning": "retained intervention-to-nearby-air comparison links"},
        ],
        "workflow": [
            {"step": 1, "name": "Evidence", "description": "Collect documents, source records and monitoring observations."},
            {"step": 2, "name": "Interpret", "description": "Structure the intervention mechanism, place and timing."},
            {"step": 3, "name": "Verify", "description": "Apply eligibility checks and governed routing rules."},
            {"step": 4, "name": "Model", "description": "Compare approved methods on the same evaluation period."},
            {"step": 5, "name": "Explain", "description": "Report results, provenance and claim boundaries."},
        ],
        "cases": cases,
        "model_comparison": _model_comparison(project_root),
        "prediction_contributions": _prediction_contributions(project_root),
        "disclosures": [
            "GreenSeer is auto-ML inspired: routing is governed and auditable, not an unrestricted autonomous model generator.",
            "Observed source changes, ambient changes, predictive explanations and causal effects are different evidence types.",
            "The public site contains compact derived tables, not the full private data archive or SAS Viya environment.",
        ],
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_public_outputs(project_root: Path, output_root: Path) -> dict[str, Any]:
    """Write the four compact public artifacts and return a small build report."""
    project_root = Path(project_root).resolve()
    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    payload = build_public_payload(project_root)
    (output_root / "project.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    source_months = project_root / "deliverables/intervention_system/v3/source_months.csv"
    sammis_rows: list[dict[str, Any]] = []
    with source_months.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row["intervention_id"] == "EPA_FGD_2866_1_2010-03-11":
                sammis_rows.append(row)
    _write_csv(output_root / "sammis-monthly.csv", sammis_rows)
    _write_csv(output_root / "model-comparison.csv", payload["model_comparison"])

    manifest = {
        "built_for": "GreenSeer public portfolio",
        "sources": [
            {"name": "EPA Clean Air Markets Program Data", "public_url": "https://campd.epa.gov/", "project_use": "Power-unit emissions, fuel energy and control records"},
            {"name": "EPA Air Quality System AirData", "public_url": "https://aqs.epa.gov/aqsweb/airdata/download_files.html", "project_use": "Ambient pollutant monitoring observations"},
            {"name": "NOAA NCEI Synoptic Summary of the Day", "public_url": "https://www.ncei.noaa.gov/oa/synoptic-summary-of-the-day/v2/access/by-year/", "project_use": "Weather context used in retained experiments"},
            {"name": "NOAA Global Historical Climatology Network Hourly", "public_url": "https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly", "project_use": "Hourly weather context used in retained experiments"},
            {"name": "U.S. DOE Alternative Fuels Data Center", "public_url": "https://afdc.energy.gov/laws", "project_use": "Transportation policy and incentive records"},
        ],
        "note": "Public outputs are compact derived artifacts. Original agencies remain the authoritative sources.",
    }
    (output_root / "source-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"file_count": 4, "case_count": len(payload["cases"]), "sammis_months": len(sammis_rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    report = write_public_outputs(args.project_root, args.output_root)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
