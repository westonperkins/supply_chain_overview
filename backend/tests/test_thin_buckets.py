"""Test 2 — Thin-bucket census. Not pass/fail.

A single-edge bucket always produces HHI 1.0, so under combine: max it
dominates whenever no other stage matches it. Sizing the number of nodes
scored by a one-edge bucket quantifies the thin-graph problem before it
gets fixed.

Written to `_out/thin_buckets.txt` on every run.
"""
from pathlib import Path

from .helpers import collect_thin_buckets

_OUT = Path(__file__).parent / "_out"
_OUT.mkdir(exist_ok=True)


def test_thin_bucket_census_reported(graph):
    rows = collect_thin_buckets(graph)
    path = _OUT / "thin_buckets.txt"
    with path.open("w") as f:
        f.write(f"thin-bucket census — {len(rows)} single-edge bucket(s)\n\n")
        f.write(f"{'won max':<8} {'bucket':>6}  {'node':<38} {'stage':<14}\n")
        # Show the buckets that won max first — they're the ones whose
        # HHI is driving their node's tier.
        rows.sort(key=lambda r: (not r["won_max"], r["node_name"]))
        for r in rows:
            marker = "yes" if r["won_max"] else "no"
            f.write(
                f"{marker:<8} {r['bucket_hhi']:>6.3f}  "
                f"{r['node_name'][:38]:<38} {r['stage']:<14}\n"
            )
        winners = sum(1 for r in rows if r["won_max"])
        f.write(f"\nnodes whose inbound_hhi is decided by a single-edge bucket: {winners}\n")

    # Not an assertion — this test only exists to produce the report file.
    # Just confirm it wrote.
    assert path.exists()
