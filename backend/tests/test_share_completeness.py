"""Test 1 — Share completeness.

The most important test in this suite. compute_hhi normalizes internally,
so a bucket summing to 0.47 produces a confident HHI from incomplete data
and nothing complains. This is exactly how copper read refined_by_hhi = 1.0
from a single China edge before the refiner data was added.

Threshold bands:
  sum >= 0.95        → pass
  0.80 <= sum < 0.95 → warn (reported, does not fail)
  sum < 0.80         → fail

The full backlog is written to `backend/tests/_out/share_backlog.txt` on
every run so the shortfalls survive as an inspectable artefact for the
data-completeness pass.
"""
from pathlib import Path

import pytest

from .helpers import collect_share_shortfalls

_OUT = Path(__file__).parent / "_out"
_OUT.mkdir(exist_ok=True)


def _write_backlog(rows):
    path = _OUT / "share_backlog.txt"
    with path.open("w") as f:
        if not rows:
            f.write("no buckets below 0.95 — nothing in the backlog\n")
            return
        f.write(f"share-completeness backlog — {len(rows)} bucket(s) below 0.95\n")
        f.write(f"{'severity':<8} {'sum':>6} {'edges':>5}  {'node':<38} {'stage':<14}\n")
        for r in rows:
            sev = "FAIL" if r["sum"] < 0.80 else "warn"
            f.write(
                f"{sev:<8} {r['sum']:>6.3f} {r['n_edges']:>5}  "
                f"{r['node_name'][:38]:<38} {r['stage']:<14}\n"
            )


def test_no_stage_bucket_sums_below_0_80(graph):
    """H2 fix (Pass B): blanket xfail replaced with set-equality against
    the committed pinned known-shortfall set at
    `backend/tests/pinned/known_bucket_shortfalls.txt`.

    A NEW bucket dropping below 0.80 fails naming the new offender.
    A FIXED (previously-pinned) shortfall fails as "pinned list stale."
    The `_out/share_backlog.txt` artefact continues to regenerate every
    run.
    """
    rows = collect_share_shortfalls(graph, threshold=0.95)
    _write_backlog(rows)
    current = {(r["node_id"], r["stage"]) for r in rows if r["sum"] < 0.80}

    pinned_path = Path(__file__).parent / "pinned" / "known_bucket_shortfalls.txt"
    pinned = set()
    for line in pinned_path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        node_id, stage, _sum = line.split("\t")
        pinned.add((node_id, stage))

    new_shortfalls = current - pinned
    fixed = pinned - current
    assert not new_shortfalls, (
        f"NEW stage-bucket shortfall(s): {sorted(new_shortfalls)}. "
        f"Model the missing edges, or add to "
        f"backend/tests/pinned/known_bucket_shortfalls.txt only after "
        f"deciding the shortfall is acceptable."
    )
    assert not fixed, (
        f"pinned known-shortfall list is STALE — these no longer "
        f"shortfall: {sorted(fixed)}. Remove them from "
        f"backend/tests/pinned/known_bucket_shortfalls.txt."
    )
