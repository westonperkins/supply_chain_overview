"""Threshold derivation — Pass B.

Deterministic, config-driven: reads scored severities, finds separating
gaps in the distribution, places boundaries at gap midpoints. No
boundary value is hand-written; every boundary is a function of the
committed data + one config parameter (`separation_factor`).

Procedure (spec §1.3):
  1. Take all scored severities (exclude unscored).
  2. Sort descending; compute adjacent gaps.
  3. Compute the median adjacent gap.
  4. A gap is `separating` if gap >= separation_factor × median_gap.
  5. Candidate boundaries = midpoints of separating gaps.
  6. Assign the three boundaries in descending order of candidate
     midpoint; one boundary per separating gap.
  7. If a required boundary has no separating gap available, do NOT
     force a line — declare an unresolved band instead (§1.4).

Prohibitions (spec §1.6):
  - This module MUST NOT reference any known-miss chokepoint by name.
    The derivation is a function of severities and a config-committed
    separation factor — nothing else. A dedicated test in
    `test_generated_artifacts.py` scans this file for forbidden names
    to enforce A8.
  - `separation_factor` MUST NOT be tuned to produce a target tier
    membership. It is committed and does not move within a pass.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
from typing import Optional


@dataclass(frozen=True)
class Gap:
    """One adjacent gap between two sorted severities."""
    upper_id: str
    upper_sev: float
    lower_id: str
    lower_sev: float

    @property
    def size(self) -> float:
        return self.upper_sev - self.lower_sev

    @property
    def midpoint(self) -> float:
        return (self.upper_sev + self.lower_sev) / 2.0


@dataclass
class UnresolvedBand:
    """Two tiers not separable within a severity span."""
    lower: float
    upper: float
    tiers: list[str]
    reason: str


@dataclass
class ThresholdDerivation:
    """Full derivation output; the analysis artifact prints from this."""
    scored: list[tuple[str, float]]  # [(node_id, severity)] sorted desc
    gaps: list[Gap]                  # in the same order (upper → lower)
    median_gap: float
    separation_factor: float
    separating_gaps: list[Gap]       # subset of gaps that qualify
    boundaries: dict[str, float]     # {"critical": v, "high": v, "moderate": v}
    boundary_gap: dict[str, Optional[Gap]]  # which gap each boundary came from
    unresolved_bands: list[UnresolvedBand] = field(default_factory=list)


def derive_thresholds(
    severities: list[tuple[str, Optional[float]]],
    separation_factor: float,
) -> ThresholdDerivation:
    """Derive tier boundaries from the scored-severity distribution.

    `severities` may include unscored entries (severity=None) — they are
    filtered out here. Returns a ThresholdDerivation with everything the
    analysis artifact needs to reproduce the reasoning."""
    scored = sorted(
        [(nid, sev) for nid, sev in severities if sev is not None],
        key=lambda kv: -kv[1],
    )

    if len(scored) < 2:
        # No adjacent pairs to compute gaps from; boundaries stay unresolved.
        return ThresholdDerivation(
            scored=scored, gaps=[], median_gap=0.0,
            separation_factor=separation_factor,
            separating_gaps=[],
            boundaries={"critical": 1.0, "high": 1.0, "moderate": 1.0},
            boundary_gap={"critical": None, "high": None, "moderate": None},
            unresolved_bands=[UnresolvedBand(
                lower=0.0, upper=1.0,
                tiers=["critical", "high", "moderate", "none"],
                reason=f"only {len(scored)} scored node(s); cannot derive gaps",
            )],
        )

    gaps: list[Gap] = []
    for (u_id, u_sev), (l_id, l_sev) in zip(scored, scored[1:]):
        gaps.append(Gap(u_id, u_sev, l_id, l_sev))

    med = median(g.size for g in gaps)
    threshold = separation_factor * med
    separating = [g for g in gaps if g.size >= threshold]

    # Candidate midpoints in descending severity order — the top three
    # are assigned to critical/high, high/moderate, moderate/none in
    # descending order per §1.3 step 6.
    candidates = sorted(separating, key=lambda g: -g.midpoint)

    boundary_names = ["critical", "high", "moderate"]
    boundaries: dict[str, float] = {}
    boundary_gap: dict[str, Optional[Gap]] = {}
    unresolved: list[UnresolvedBand] = []

    for i, name in enumerate(boundary_names):
        if i < len(candidates):
            g = candidates[i]
            boundaries[name] = g.midpoint
            boundary_gap[name] = g
        else:
            # No separating gap for this boundary — declare unresolved.
            # Span: from previous boundary (or top of distribution) down
            # to next known separating gap (or 0.0).
            upper_boundary = boundaries.get(boundary_names[i - 1], scored[0][1])
            next_sep = candidates[i - 1].midpoint if candidates else 0.0
            # Adjacent tier pair
            if name == "critical":
                pair = ["critical", "high"]
            elif name == "high":
                pair = ["high", "moderate"]
            else:
                pair = ["moderate", "none"]
            unresolved.append(UnresolvedBand(
                lower=0.0,
                upper=upper_boundary,
                tiers=pair,
                reason=(
                    f"no separating gap ≥ {threshold:.5f} for the "
                    f"{name}/{'high' if name == 'critical' else 'moderate' if name == 'high' else 'none'} boundary"
                ),
            ))
            # Set boundary = 0 so any node with positive severity is above it;
            # tier_ambiguous will handle downstream.
            boundaries[name] = 0.0
            boundary_gap[name] = None

    # Strict monotonic guard: boundaries must decrease.
    prev = float("inf")
    for name in boundary_names:
        if boundaries[name] > prev:
            raise ValueError(
                f"Derived boundaries not monotonic decreasing: {boundaries}. "
                f"Separation factor {separation_factor} produced invalid "
                f"candidate ordering — investigate."
            )
        prev = boundaries[name]

    return ThresholdDerivation(
        scored=scored, gaps=gaps, median_gap=med,
        separation_factor=separation_factor,
        separating_gaps=separating,
        boundaries=boundaries,
        boundary_gap=boundary_gap,
        unresolved_bands=unresolved,
    )


def compute_tier_ambiguity(
    severity: float,
    derivation: ThresholdDerivation,
) -> tuple[bool, Optional[list[str]]]:
    """For a scored severity, return (tier_ambiguous, tier_ambiguous_with).

    A node is ambiguous when its severity falls inside an unresolved
    band. `tier_ambiguous_with` names the OTHER tier the node could
    plausibly belong to; the tier itself is still assigned by the derived
    boundary so downstream tier enums do not need a new member."""
    for band in derivation.unresolved_bands:
        if band.lower <= severity <= band.upper:
            # The node is ambiguous between the two tiers of the band.
            # The current tier is derived normally; the AMBIGUOUS_WITH
            # names the other one.
            # Pick whichever tier is NOT the derived one (caller resolves).
            return True, list(band.tiers)
    return False, None
