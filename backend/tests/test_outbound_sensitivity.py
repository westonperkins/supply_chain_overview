"""Test 11 — Outbound normalization sensitivity. Probe, not pass/fail.

outbound_criticality normalizes to graph max, so any single node's raw
score can drag every other node's score. When robotics joins the same
graph, AI tiers may move for no AI-related reason. This size-check tells
us how fragile that is.

Written to `_out/outbound_sensitivity.txt`.
"""
from pathlib import Path

from .helpers import outbound_sensitivity_probe

_OUT = Path(__file__).parent / "_out"
_OUT.mkdir(exist_ok=True)


def test_outbound_sensitivity_recorded(graph, config):
    result = outbound_sensitivity_probe(graph, config)
    path = _OUT / "outbound_sensitivity.txt"
    with path.open("w") as f:
        f.write(
            f"Removing the single highest-outbound node "
            f"({result['removed_node_name']}, id={result['removed_node_id']}, "
            f"score={result['removed_original_score']:.3f}) and "
            f"renormalizing changes:\n\n"
            f"  {result['n_changed_tiers']} node(s) shift tier.\n\n"
        )
        if result["changed"]:
            f.write("Changed:\n")
            for nid, old, new in result["changed"]:
                f.write(f"  {nid:<35}  {old:>9} → {new:<9}\n")
        else:
            f.write("No tier shifts under perturbation.\n")
    assert path.exists()
