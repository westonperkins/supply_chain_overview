"""Pass P §2 — guard tests for the frozen tier boundaries.

Boundaries are the second value in the codebase to be frozen against
silent drift; `fixed_reference` was the first (Pass K.1 §5.4). Both
have the same failure mode: a value that scoring depends on being
rewritten by tooling on every run, so the meaning of every downstream
number could change without any node or edge changing.

The guard here fails whenever a boundary literal in
`config/scoring.yaml` differs from the value frozen at Pass P. If the
committed boundaries change, this test must change in the SAME commit,
citing the authorizing spec. The defect being caught is silent drift,
not the values themselves.
"""

from pathlib import Path

import pytest
import yaml


REPO = Path(__file__).resolve().parents[2]


# --- Frozen tier-boundary literals ------------------------------------------
#
# These are the boundary values currently in force. They match the
# `thresholds.boundaries` block in `config/scoring.yaml` byte-for-byte.
# Changing any value here requires an authorizing spec + a re-baseline
# of committed snapshots + a matching update to the config literal in
# the same commit.
#
# Pass U (FR-C, re-baseline Phase B) — authorizing spec. The triple
# below is the natural-breaks derivation of the FR-C severity
# distribution (fixed_reference = 2.5) at separation_factor 3.0, as
# measured by Pass T (docs/generated/pass_t_facts.json →
# candidates["FR-C"].derivation_at_3.0) and re-verified byte-identically
# against the post-change engine in Pass U §4. Prior (Pass P → Pass T)
# frozen triple was critical 0.5178454839188712 / high
# 0.41368488092014066 / moderate 0.17711108045794494.
FROZEN_BOUNDARIES: dict[str, float] = {
    "critical": 0.5247316525037853,
    "high":     0.42320867926942163,
    "moderate": 0.15668443545638666,
}


FROZEN_MODE = "frozen"


def _load_config_thresholds() -> dict:
    with (REPO / "config" / "scoring.yaml").open() as f:
        return yaml.safe_load(f).get("thresholds", {})


def _assert_frozen(boundaries: dict, mode: str) -> None:
    """Raises AssertionError if boundaries or mode differ from the
    frozen set. Extracted so a proof-of-guard test can exercise the
    failure branch without editing config/scoring.yaml on disk."""
    assert mode == FROZEN_MODE, (
        f"thresholds.mode must be {FROZEN_MODE!r} (Pass P §1); "
        f"got {mode!r}. Switching to 'derived' is only valid in a "
        f"pre-approved re-baseline pass with its own diff scope."
    )
    for name, expected in FROZEN_BOUNDARIES.items():
        actual = boundaries.get(name)
        assert actual == expected, (
            f"thresholds.boundaries.{name} drifted from the Pass P frozen "
            f"literal. expected={expected!r}, got={actual!r}. Changing a "
            f"frozen tier boundary requires updating both this test and "
            f"the config literal in the same commit, citing the authorizing "
            f"spec. Silent drift is the defect being caught here."
        )


def test_thresholds_mode_is_frozen():
    """The default mode is `frozen`; `derived` is only valid in an
    authorized re-baseline pass."""
    thresholds = _load_config_thresholds()
    assert thresholds.get("mode") == FROZEN_MODE, (
        f"config/scoring.yaml thresholds.mode is "
        f"{thresholds.get('mode')!r}, not {FROZEN_MODE!r}."
    )


def test_thresholds_boundaries_are_frozen():
    """Every committed boundary matches the Pass P frozen literal."""
    thresholds = _load_config_thresholds()
    _assert_frozen(thresholds.get("boundaries", {}), thresholds.get("mode"))


def test_guard_actually_fails_when_a_literal_is_altered():
    """Proof-of-guard test (spec §4.6: prove it, don't assert it).

    Pass an in-memory boundaries dict with one value shifted. If the
    guard silently accepts the drifted value, the whole freeze is
    theatre. This test proves the guard rejects it."""
    drifted = dict(FROZEN_BOUNDARIES)
    drifted["moderate"] = FROZEN_BOUNDARIES["moderate"] + 1e-9
    with pytest.raises(AssertionError) as exc_info:
        _assert_frozen(drifted, FROZEN_MODE)
    # The failure message must name the drifted boundary and the
    # authorizing-spec requirement so the fix path is obvious.
    msg = str(exc_info.value)
    assert "moderate" in msg
    assert "authorizing spec" in msg


def test_guard_actually_fails_when_mode_is_derived():
    """A committed `mode: derived` outside an authorized re-baseline
    pass is the specific failure Pass P exists to prevent."""
    with pytest.raises(AssertionError) as exc_info:
        _assert_frozen(FROZEN_BOUNDARIES, "derived")
    assert "'frozen'" in str(exc_info.value)
