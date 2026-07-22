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

    # F1 fix — natural-breaks selection.
    # Select boundary gaps by SIZE (largest first). Pass B selected by
    # midpoint position, which discarded the second-largest gap in the
    # distribution because it sat low — an inspection tool ordering, not
    # a tier one. Tie-break: higher midpoint, then upper_id lex, so
    # selection is deterministic. Order the SELECTED gaps by midpoint
    # descending for boundary naming (tiers are monotonic in severity).
    selected = sorted(
        separating,
        key=lambda g: (-g.size, -g.midpoint, g.upper_id),
    )[:3]
    selected_by_midpoint = sorted(selected, key=lambda g: -g.midpoint)

    boundary_names = ["critical", "high", "moderate"]
    boundaries: dict[str, float] = {}
    boundary_gap: dict[str, Optional[Gap]] = {}
    unresolved: list[UnresolvedBand] = []

    def _tier_pair(name: str) -> list[str]:
        if name == "critical":
            return ["critical", "high"]
        if name == "high":
            return ["high", "moderate"]
        return ["moderate", "none"]

    for i, name in enumerate(boundary_names):
        if i < len(selected_by_midpoint):
            g = selected_by_midpoint[i]
            boundaries[name] = g.midpoint
            boundary_gap[name] = g
        else:
            # No separating gap for this boundary — declare unresolved.
            upper_boundary = boundaries.get(boundary_names[i - 1], scored[0][1])
            unresolved.append(UnresolvedBand(
                lower=0.0,
                upper=upper_boundary,
                tiers=_tier_pair(name),
                reason=(
                    f"no separating gap ≥ {threshold:.5f} for the "
                    f"{name}/{_tier_pair(name)[1]} boundary"
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

    # F1.b — partition sanity guard. If the moderate/none boundary sits
    # above the median scored severity, the bottom partition is
    # degenerate (`none` would swallow the majority of scored nodes).
    # Reroute the boundary to the unresolved-band mechanism rather than
    # ship a degenerate partition. Pure structural check on the boundary
    # vs the median — does not reference any node by name and is not
    # tunable to any tier membership. See spec §F1.b.
    scored_sevs = [s for _, s in scored]
    median_scored = median(scored_sevs)
    if boundaries.get("moderate", 0.0) > median_scored:
        prev_boundary = boundaries.get("high", scored[0][1])
        unresolved.append(UnresolvedBand(
            lower=0.0,
            upper=prev_boundary,
            tiers=["moderate", "none"],
            reason=(
                f"moderate/none boundary {boundaries['moderate']:.5f} sits "
                f"above the median scored severity {median_scored:.5f} — "
                f"bottom partition is degenerate (`none` would hold the "
                f"majority of scored nodes). Rerouted to unresolved band."
            ),
        ))
        boundaries["moderate"] = 0.0
        boundary_gap["moderate"] = None

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
    tier_name: str,
    derivation: ThresholdDerivation,
) -> tuple[bool, Optional[list[str]]]:
    """For a scored severity, return (tier_ambiguous, tier_ambiguous_with).

    A node is ambiguous when its severity falls inside an unresolved
    band. `tier_ambiguous_with` names the OTHER tier(s) the node could
    plausibly belong to — EXCLUDING its own derived tier. The tier
    itself is still assigned by the derived boundary so downstream tier
    enums do not need a new member.

    F4 fix (Pass C): returns only the other tier(s), not both, matching
    the docstring's stated contract. The prior implementation returned
    `list(band.tiers)` which included the node's own tier — dead-code
    branch, so uncaught."""
    for band in derivation.unresolved_bands:
        if band.lower <= severity <= band.upper:
            others = [t for t in band.tiers if t != tier_name]
            return True, others or None
    return False, None
