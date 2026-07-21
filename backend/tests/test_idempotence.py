"""Test 4 — Idempotence.

refresh_all_derived mutates node.dynamic in place and computes derived
values from other derived values (inbound_hhi from stage_hhis, then
concentration from inbound and outbound, then severity from concentration,
then tier from severity). Ordering bugs there are silent — the same input
must produce the same output whether you run it once or twice.
"""
import math

from app.scoring import refresh_all_derived

from .helpers import snapshot_derived


def test_refresh_all_derived_is_idempotent(graph, config):
    before = snapshot_derived(graph)
    refresh_all_derived(graph, config)
    after = snapshot_derived(graph)

    diffs = []
    for node_id, b in before.items():
        a = after[node_id]
        for key, bval in b.items():
            aval = a[key]
            if isinstance(bval, dict) and isinstance(aval, dict):
                if bval != aval:
                    diffs.append((node_id, key, bval, aval))
                continue
            if bval is None and aval is None:
                continue
            if isinstance(bval, float) and isinstance(aval, float):
                if not math.isclose(bval, aval, rel_tol=1e-9, abs_tol=1e-12):
                    diffs.append((node_id, key, bval, aval))
                continue
            if bval != aval:
                diffs.append((node_id, key, bval, aval))

    assert not diffs, f"{len(diffs)} field(s) changed under second refresh: {diffs[:5]}"
