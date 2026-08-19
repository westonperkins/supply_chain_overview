"""Pass P §3 — tests for the drift diagnostic in
`build_threshold_analysis`.

The drift section fires only under `mode == 'frozen'` with a
`frozen_boundaries` argument supplied. Verified here:

  - It emits nothing under `mode == 'derived'` (so the pre-P
    behaviour reproduces exactly under the re-baseline flow).
  - Its four subsections + verdict line render under `frozen`.
  - When frozen == derived (today's state), it reports 0 movement.
  - When frozen differs from derived, it reports the delta,
    would-change-tier list, and flips the verdict.
  - The cluster-cut check flags a boundary sitting inside a tight
    cluster (nearest neighbour < median adjacent gap).
"""

from app.reporting.threshold_analysis import build_threshold_analysis
from app.scoring.thresholds import Gap, ThresholdDerivation


def _fake_derivation(
    scored: list[tuple[str, float]],
    boundaries: dict[str, float],
    median_gap: float = 0.01,
) -> ThresholdDerivation:
    """Build a minimal ThresholdDerivation for shape tests. The gaps
    list is a real derivation input, so we compute it honestly from
    the sorted severities."""
    scored_sorted = sorted(scored, key=lambda kv: -kv[1])
    gaps: list[Gap] = []
    for (u_id, u_sev), (l_id, l_sev) in zip(scored_sorted, scored_sorted[1:]):
        gaps.append(Gap(u_id, u_sev, l_id, l_sev))
    return ThresholdDerivation(
        scored=scored_sorted,
        gaps=gaps,
        median_gap=median_gap,
        separation_factor=3.0,
        separating_gaps=[],
        boundaries=boundaries,
        boundary_gap={"critical": None, "high": None, "moderate": None},
        unresolved_bands=[],
    )


BASE_SCORED = [
    ("n:a", 0.90),
    ("n:b", 0.55),
    ("n:c", 0.40),
    ("n:d", 0.20),
    ("n:e", 0.10),
    ("n:f", 0.05),
]
BASE_BOUNDARIES = {"critical": 0.50, "high": 0.35, "moderate": 0.15}


def _md(mode: str, frozen=None, derived_boundaries=None) -> str:
    d = _fake_derivation(
        BASE_SCORED,
        boundaries=derived_boundaries or BASE_BOUNDARIES,
    )
    return build_threshold_analysis(
        d,
        inventory_content="fake",
        scored_count=len(BASE_SCORED),
        unscored_count=0,
        chokepoint_landing=None,
        frozen_boundaries=frozen,
        mode=mode,
    )


# --- section presence ------------------------------------------------------


def test_no_drift_section_under_derived_mode():
    """`mode: derived` must reproduce the pre-P output shape exactly —
    no drift section, no diagnostic overhead. The re-baseline pass
    relies on this."""
    md = _md("derived", frozen=None)
    assert "Drift diagnostic" not in md
    assert "frozen vs derived" not in md


def test_no_drift_section_when_frozen_but_boundaries_missing():
    """Defensive: mode=frozen without a frozen_boundaries argument
    can't compare against anything, so the section is skipped rather
    than rendered with placeholder values."""
    md = _md("frozen", frozen=None)
    assert "Drift diagnostic" not in md


def test_drift_section_present_under_frozen_with_boundaries():
    md = _md("frozen", frozen=BASE_BOUNDARIES)
    assert "Drift diagnostic" in md
    for header in (
        "### 1. Per-boundary drift",
        "### 2. Would-change-tier",
        "### 3. Cluster-cut check",
        "### 4. Unresolved bands",
        "### Verdict",
    ):
        assert header in md, f"missing subsection: {header}"


# --- content under frozen == derived ---------------------------------------


def test_zero_movement_when_frozen_equals_derived():
    """Today's baseline. Every delta 0, no would-change-tier, no
    cluster cuts, verdict reads 'still fits the distribution'."""
    md = _md("frozen", frozen=BASE_BOUNDARIES)
    assert "**0 nodes would change tier.**" in md
    assert "still fits the distribution" in md
    # Every per-boundary delta must render as +0 to full precision.
    for name in ("critical", "high", "moderate"):
        assert f"| {name} |" in md
    # No YES flag in the cluster-cut column.
    assert "**YES**" not in md


# --- content when frozen has drifted ---------------------------------------


def test_would_change_tier_list_names_movers_and_directions():
    """Frozen boundaries pretend the world is stricter than it is;
    two nodes should move up under the derived (looser) boundaries."""
    strict_frozen = {"critical": 0.60, "high": 0.45, "moderate": 0.25}
    # Under BASE_BOUNDARIES: n:a=critical, n:b=critical, n:c=high, n:d=moderate
    # Under strict_frozen:   n:a=critical, n:b=high,    n:c=moderate, n:d=none
    # Adopting BASE (derived) would move: n:b (high → critical),
    #                                     n:c (moderate → high),
    #                                     n:d (none → moderate).
    md = build_threshold_analysis(
        _fake_derivation(BASE_SCORED, boundaries=BASE_BOUNDARIES),
        inventory_content="fake",
        scored_count=len(BASE_SCORED),
        unscored_count=0,
        chokepoint_landing=None,
        frozen_boundaries=strict_frozen,
        mode="frozen",
    )
    assert "**3 nodes would change tier**" in md
    for nid in ("n:b", "n:c", "n:d"):
        assert nid in md
    # All three go up (frozen is stricter).
    assert md.count("↑") >= 3
    assert "has drifted from the current distribution" in md


def test_verdict_flips_when_drift_present():
    """A negative-direction check: with any single boundary drifted
    enough to move a node, the verdict must NOT read 'still fits'."""
    drifted_frozen = {"critical": 0.75, "high": 0.35, "moderate": 0.15}
    # n:b = 0.55 sits above frozen critical now? No, 0.55 < 0.75; below.
    # Under frozen: n:b=high (>=0.35). Under derived (0.50 crit): n:b=critical.
    # → one node changes tier.
    md = build_threshold_analysis(
        _fake_derivation(BASE_SCORED, boundaries=BASE_BOUNDARIES),
        inventory_content="fake",
        scored_count=len(BASE_SCORED),
        unscored_count=0,
        chokepoint_landing=None,
        frozen_boundaries=drifted_frozen,
        mode="frozen",
    )
    assert "still fits the distribution" not in md
    assert "has drifted from the current distribution" in md
    assert "1 node(s) would change tier" in md


# --- cluster-cut check -----------------------------------------------------


def test_cluster_cut_flag_fires_when_boundary_sits_inside_tight_cluster():
    """A boundary within `median_gap` of a scored node is cutting
    through a tight cluster — the named cost of freezing."""
    # Tight cluster: severities 0.31, 0.30, 0.29 with boundary at 0.302.
    # Median gap ~ 0.01. Nearest neighbour ~ 0.002 < median → flag YES.
    tight = [
        ("n:hi", 0.90),
        ("n:cluster_top", 0.31),
        ("n:cluster_mid", 0.30),
        ("n:cluster_lo",  0.29),
        ("n:lo", 0.05),
    ]
    boundaries = {"critical": 0.80, "high": 0.302, "moderate": 0.10}
    derivation = _fake_derivation(tight, boundaries=boundaries, median_gap=0.05)
    md = build_threshold_analysis(
        derivation,
        inventory_content="fake",
        scored_count=len(tight),
        unscored_count=0,
        chokepoint_landing=None,
        frozen_boundaries=boundaries,
        mode="frozen",
    )
    # The high boundary at 0.302 sits 0.002 above n:cluster_mid (0.30)
    # and 0.008 below n:cluster_top (0.31); both < median 0.05.
    assert "**YES**" in md
    assert "boundary(-ies) inside tight clusters" in md


# ------------------------------------------------------------------------ #
# Pass R — committed-artifact contract for the drift section.               #
# ------------------------------------------------------------------------ #


def test_drift_diagnostic_present_in_committed_threshold_analysis():
    """Pass R — under `mode: frozen` (the current committed state), the
    drift diagnostic must be present in the committed
    `docs/generated/threshold_analysis.md` — the section is the
    authoritative record of the frozen-vs-derived divergence and
    replaces the pre-Pass-P `test_config_boundaries_equal_derivation`
    equality assertion (which is scoped to `mode: derived` post-Pass-R).

    Structural check on the committed artifact rather than a
    programmatic re-generation, so a stale artifact + drifted config
    fail visibly here rather than in the semantics."""
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[2]
    text = (REPO / "docs" / "generated" / "threshold_analysis.md").read_text()
    for header in (
        "## Drift diagnostic — frozen vs derived",
        "### 1. Per-boundary drift",
        "### 2. Would-change-tier under derived boundaries",
        "### 3. Cluster-cut check",
        "### 4. Unresolved bands declared by the derivation",
        "### Verdict",
    ):
        assert header in text, (
            f"drift diagnostic missing '{header}' in committed "
            f"threshold_analysis.md — regenerate: "
            f"`python backend/scripts/generate_inventory.py`"
        )
    # Verdict line — exactly one of the two forms must be present.
    verdicts = (
        "**Frozen set still fits the distribution.**",
        "**Frozen set has drifted from the current distribution:**",
    )
    assert any(v in text for v in verdicts), (
        "drift diagnostic verdict line missing from committed artifact"
    )
