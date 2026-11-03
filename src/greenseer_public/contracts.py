"""Typed contracts that keep interpretation, evidence and routing separate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class InterventionRecord:
    intervention_id: str
    sector: str
    mechanism: str
    operational_start: date | None
    target_emissions: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceInventory:
    source_months: bool = False
    ambient_measurements: bool = False
    comparison_units: bool = False
    weather: bool = False


@dataclass(frozen=True)
class RouteDecision:
    template_id: str
    eligible: bool
    causal_eligible: bool
    evidence_status: str
    reasons: tuple[str, ...]
