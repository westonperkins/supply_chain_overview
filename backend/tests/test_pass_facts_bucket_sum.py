"""Pass R.1 §1 — guard test for `_bucket_sum` in pass_facts.py.

The defect: the prior `_bucket_sum` used
    getattr(e, "supply_category", None) == category or (
        isinstance(e, dict) and e.get("supply_category") == category
    )
on a list of dicts. `getattr(dict, "supply_category", None)` returns
None because dicts don't have `supply_category` as an *attribute*
(only as a *key*). When the caller passed `category=None` (correct
for `input_to` edges, which carry no supply_category) the
`None == None` short-circuit matched every edge into the target
regardless of its actual supply_category key. This inflated the four
`copper → fab` input_to bucket sums by summing every supplies-stage
edge into the fab as well — TSMC's `bucket_sum_after` reported as
5.18 rather than the correct 0.95.

The invariant this test asserts is the same one the defect violated:
**for any edge whose `bucket_members` has length 1, `bucket_sum`
equals that edge's `input_share`.** Cheap, fires on real data, and
would have caught R.1.1 at Pass R commit time.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend" / "scripts"))

from pass_facts import _bucket_sum, _bucket_members  # noqa: E402


# --- Realistic-shape fixture -----------------------------------------------
#
# Mirrors the shape of edges in `data/ai/edges.json`: dict-of-dicts, with
# `supply_category=None` for `input_to` and a real category for `supplies`.
# The pre-R.1 defect only fired on dicts with the None-category bucket,
# so the test uses that shape exactly.

_EDGES = [
    # One input_to edge into TSMC — the sole member of TSMC's `input_to`
    # bucket. Its bucket_sum must equal its own input_share.
    {"id": "e:copper-input-tsmc", "source_id": "mineral:copper",
     "target_id": "company:tsmc", "type": "input_to",
     "supply_category": None, "input_share": 0.95},
    # Many supplies-stage edges into TSMC, in various categories. Pre-fix
    # these all matched the None-category filter (because dict.getattr →
    # None) and were summed together with copper → 5.18-ish.
    {"id": "e:asml-supplies-tsmc", "source_id": "company:asml",
     "target_id": "company:tsmc", "type": "supplies",
     "supply_category": "lithography", "input_share": 0.99},
    {"id": "e:am-supplies-tsmc", "source_id": "company:applied_materials",
     "target_id": "company:tsmc", "type": "supplies",
     "supply_category": "deposition", "input_share": 0.55},
    {"id": "e:lam-supplies-tsmc", "source_id": "company:lam_research",
     "target_id": "company:tsmc", "type": "supplies",
     "supply_category": "etch", "input_share": 0.80},
]


def test_single_member_bucket_sum_equals_input_share():
    """R.1.1 §7(5) proof-of-guard — fires against the pre-fix behaviour,
    passes after."""
    members = _bucket_members(_EDGES, "company:tsmc", None)
    assert members == ["mineral:copper"], (
        f"fixture drift: expected bucket_members ['mineral:copper'], "
        f"got {members}"
    )
    bucket_sum = _bucket_sum({}, "company:tsmc", None, _EDGES)
    # copper's own input_share = 0.95. Under the pre-fix defect this was
    # 0.95 + 0.99 + 0.55 + 0.80 = 3.29 (or similar). Under the fix, 0.95.
    assert bucket_sum == 0.95, (
        f"single-member bucket sum should equal member's input_share; "
        f"got {bucket_sum!r}. The defect is R.1.1 — `_bucket_sum` matched "
        f"every edge into the target when category=None, ignoring the "
        f"actual supply_category key on each dict edge."
    )


def test_bucket_sum_respects_category_key():
    """Sanity — a real category filter matches only edges with that
    supply_category. Ensures the fix didn't over-narrow."""
    litho = _bucket_sum({}, "company:tsmc", "lithography", _EDGES)
    assert litho == 0.99, litho
    etch = _bucket_sum({}, "company:tsmc", "etch", _EDGES)
    assert etch == 0.80, etch


def test_bucket_sum_none_category_is_not_a_wildcard():
    """The specific R.1.1 defect: `category=None` used to match every
    edge into the target (dict `.supply_category` attribute miss). Under
    the fix it matches only edges whose `supply_category` key is None."""
    # If this behaved as a wildcard, the sum would be 0.95 + 0.99 + 0.55
    # + 0.80 = 3.29. Under the fix, only the input_to edge (None-category)
    # matches.
    got = _bucket_sum({}, "company:tsmc", None, _EDGES)
    assert got == 0.95, (
        f"category=None should NOT match dict edges with a non-None "
        f"supply_category key; got sum {got!r} which suggests the "
        f"pre-R.1 wildcard behaviour has returned."
    )
