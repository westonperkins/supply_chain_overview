"""Test 14 — Outbound walk reads output_share when populated.

Guards the config-gated switch in outbound criticality and cascade.
The DEFAULT is `input_share` as of the honesty-fixes pass (2.8%
output_share coverage was ranking KLA above ASML — see
docs/scoring_honesty_fixes_report.pdf §2). This test still covers
the `output_share` code path so it does not bit-rot before coverage
rises. When outbound.share_field is `output_share`, an edge with
output_share populated must use that value, not input_share. Where
output_share is null, fallback to input_share applies. Under the
`input_share` mode, the walk uses input_share throughout, regardless
of whether output_share is populated.
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.scoring.engine import _outbound_share_for


class _Edge:
    def __init__(self, input_share, output_share):
        self._is = input_share
        self.output_share = output_share

    def effective_weight(self):
        return self._is


def test_output_share_returned_when_populated():
    e = _Edge(input_share=0.99, output_share=0.40)
    assert _outbound_share_for(e, "output_share", fallback=True) == 0.40
    assert _outbound_share_for(e, "output_share", fallback=False) == 0.40


def test_fallback_to_input_share_when_null():
    e = _Edge(input_share=0.99, output_share=None)
    assert _outbound_share_for(e, "output_share", fallback=True) == 0.99


def test_no_fallback_returns_none_when_null():
    e = _Edge(input_share=0.99, output_share=None)
    assert _outbound_share_for(e, "output_share", fallback=False) is None


def test_input_share_mode_ignores_output_share():
    e = _Edge(input_share=0.99, output_share=0.40)
    assert _outbound_share_for(e, "input_share", fallback=True) == 0.99
    assert _outbound_share_for(e, "input_share", fallback=False) == 0.99


def test_asml_outbound_drops_when_reading_output_share(graph, config):
    """Integration check — asserts the sign of the delta.

    Historical: under `output_share`, ASML's severity is ~0.29; under
    `input_share`, it's ~0.54. The DEFAULT is now `input_share` (see
    module docstring) but this integration test still forces both
    modes explicitly so the axis-choice mechanism is covered. If this
    test starts failing, output_share coverage has probably risen
    high enough that ASML no longer drops when switching modes — at
    which point revisit the default in scoring.yaml."""
    from app.graph import SupplyChainGraph
    from app.scoring import (
        ScoringConfig, refresh_all_derived, propagate_event,
    )
    root = Path(__file__).parent.parent.parent
    g_out = SupplyChainGraph.from_dir(
        Path(__file__).parent / "fixtures", domain="ai"
    )
    c_out = ScoringConfig.load(Path(__file__).parent / "fixtures" / "scoring.yaml")
    c_out.raw["concentration"]["outbound"]["share_field"] = "output_share"
    refresh_all_derived(g_out, c_out)

    g_in = SupplyChainGraph.from_dir(
        Path(__file__).parent / "fixtures", domain="ai"
    )
    c_in = ScoringConfig.load(Path(__file__).parent / "fixtures" / "scoring.yaml")
    c_in.raw["concentration"]["outbound"]["share_field"] = "input_share"
    refresh_all_derived(g_in, c_in)

    asml_out = g_out.nodes["company:asml"].dynamic.current_severity
    asml_in = g_in.nodes["company:asml"].dynamic.current_severity
    assert asml_out < asml_in, (
        f"ASML severity did NOT drop when switching to output_share: "
        f"input_share={asml_in:.3f} output_share={asml_out:.3f}"
    )
