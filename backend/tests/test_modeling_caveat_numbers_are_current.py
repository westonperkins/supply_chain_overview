"""Pass Q.1 §2 — guard test: modeling_caveat asserted numbers must not
outlive the numbers they describe.

The defect this test catches: Pass N's aggregator switch (HHI → noisy-
OR) silently falsified two committed caveats. Quanta's caveat asserted
"Inbound HHI reads 1.0" — true under HHI-normalize=true, false under
noisy-OR where a single 0.30 share reads exactly 0.30. Copper's caveat
asserted "Refining HHI reads roughly 0.29" — true under HHI-normalize=
false, false under noisy-OR (~0.70). Both survived through Pass Q's
caveat check because that check tested whether an axis MOVED and which
one DOMINATES — it could not detect a caveat whose PROSE ASSERTS A
NUMBER THAT IS FALSE.

Contract: for every node with a `modeling_caveat` (literal OR resolved
via the `caveat:<key>` narration convention), every decimal literal in
[0.0, 1.0] in the prose must match the node's current computed
inbound_hhi, outbound_criticality, or concentration within tolerance
0.05. A caveat that wants to assert a number must keep that number
current; a caveat that wants to sit through aggregator changes must
state the structural claim without asserting a specific number.

Corrected caveat check specification, for future passes:
  - Branch A (Pass Q): axis stable, inbound-dominant, caveat stands.
  - Branch B (Pass Q): axis stable, outbound dominant, caveat scope-stale.
  - Branch C (Pass Q): axis moved, stop and investigate.
  - Branch D (Pass Q.1, this test): caveat prose asserts a false number,
    regardless of whether any axis moved. Fix in the pass that finds it.

Runs branch D mechanically on every committed caveat, every pass.
"""

import re
from pathlib import Path

import yaml

from app.graph import SupplyChainGraph
from app.scoring import ScoringConfig, refresh_all_derived, propagate_event


REPO = Path(__file__).resolve().parents[2]

# Tolerance for a caveat's asserted number to match a computed value.
# Caveats are prose ("reads roughly", "on the order of") — full-precision
# equality would be too strict. 5% absolute is loose enough for the
# structural claim but tight enough to catch the Pass N/Pass Q class of
# aggregator-induced staleness (which moves values by 0.3+ typically).
TOLERANCE = 0.05

# Free-standing decimal in prose (e.g. "0.29", "1.0"). Excludes tokens
# followed by units like `%`, `x`, `yr`, `Mt`, or a digit (dates,
# ranges) — those aren't concentration readings.
_DECIMAL_RE = re.compile(
    r"(?<![\d.])"           # not preceded by a digit or dot
    r"(\d+\.\d+)"           # capture the decimal
    r"(?!\s*[%xX])"         # not followed by unit chars
    r"(?![\d.])"            # not followed by a digit or dot
)


def _load_scored_graph():
    g = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
    c = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    refresh_all_derived(g, c)
    for e in g.events.values():
        propagate_event(e, g, c)
    return g


def _load_modeling_caveats_config() -> dict:
    with (REPO / "config" / "narration.yaml").open() as f:
        return (yaml.safe_load(f) or {}).get("modeling_caveats", {})


def _resolve_caveat(raw: str, caveats_cfg: dict) -> str:
    if raw.startswith("caveat:"):
        key = raw[len("caveat:"):]
        text = caveats_cfg.get(key, "")
        return " ".join(text.split())
    return raw


def test_no_modeling_caveat_asserts_a_stale_concentration_number():
    g = _load_scored_graph()
    caveats_cfg = _load_modeling_caveats_config()
    failures: list[str] = []
    for nid, node in g.nodes.items():
        raw = node.static.modeling_caveat
        if not raw:
            continue
        text = _resolve_caveat(raw, caveats_cfg)
        matches = _DECIMAL_RE.findall(text)
        # Only decimals in [0.0, 1.0] are potential concentration readings.
        candidates = [float(m) for m in matches if 0.0 <= float(m) <= 1.0]
        if not candidates:
            continue
        allowed_values = [
            node.dynamic.inbound_hhi,
            node.dynamic.outbound_criticality,
            node.dynamic.concentration,
        ]
        allowed_values = [v for v in allowed_values if v is not None]
        for asserted in candidates:
            if not any(
                abs(asserted - v) <= TOLERANCE for v in allowed_values
            ):
                failures.append(
                    f"{nid}: caveat asserts {asserted} but node's current "
                    f"inbound_hhi/outbound/concentration are "
                    f"{allowed_values} (all beyond tolerance {TOLERANCE}). "
                    f"Rewrite the caveat to remove the specific number OR "
                    f"update it to match the current value. See Pass Q.1 §2."
                )
    assert not failures, (
        "modeling_caveat prose asserts numbers that no longer match the "
        "node's computed values. Failures:\n" + "\n".join(failures)
    )
