"""Deterministic, auditable routing into approved public templates."""

from __future__ import annotations

from .contracts import EvidenceInventory, InterventionRecord, RouteDecision


SOURCE_MECHANISMS = {"scrubber", "catalytic_control", "combustion_control", "retirement"}


def route_intervention(record: InterventionRecord, evidence: EvidenceInventory) -> RouteDecision:
    """Select an approved workflow from facts and data availability, never effect size."""
    if record.operational_start is None:
        return RouteDecision(
            template_id="review_required",
            eligible=False,
            causal_eligible=False,
            evidence_status="missing_timing",
            reasons=("A verified operational start is required to define before and after periods.",),
        )

    if record.sector == "power" and record.mechanism in SOURCE_MECHANISMS and evidence.source_months:
        return RouteDecision(
            template_id="source_intensity_existing_v1",
            eligible=True,
            causal_eligible=False,
            evidence_status="observed_source_change",
            reasons=(
                "Monthly source-level emissions and operating activity support an emissions-intensity comparison.",
                "No reviewed counterfactual is available, so the route remains descriptive rather than causal.",
            ),
        )

    if evidence.ambient_measurements:
        reasons = ["Compatible ambient measurements support a descriptive period comparison."]
        if not evidence.comparison_units:
            reasons.append("No eligible comparison unit is available for a causal contrast.")
        if not evidence.weather:
            reasons.append("Weather adjustment is unavailable in this compact public example.")
        return RouteDecision(
            template_id="ambient_period_summary_v1",
            eligible=True,
            causal_eligible=False,
            evidence_status="observed_ambient_change",
            reasons=tuple(reasons),
        )

    return RouteDecision(
        template_id="not_currently_evaluable",
        eligible=False,
        causal_eligible=False,
        evidence_status="insufficient_observations",
        reasons=("The retained evidence does not contain compatible source or ambient outcome measurements.",),
    )
