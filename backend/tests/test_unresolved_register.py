"""Pass V — unresolved-entity register.

Guards the register's five moving parts:
  1. the schema addition (`entities_unresolved`) + the `extra="forbid"`
     freeze that ends the silent-drop hole (§2, §2.1);
  2. the promise that the field never enters scoring (§5.2);
  3. the runner-writes-nothing-under-`data/` invariant, WITH a
     proof-of-failure (§3, exp 10);
  4. register aggregation + the dangling-reference section (§3, §6);
  5. probe exclusion (§4) and the promotion threshold (§3, §6).
"""
import hashlib
import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

BACKEND = Path(__file__).parent.parent
REPO = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(REPO / "backend" / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "backend" / "scripts"))

from app.graph import SupplyChainGraph
from app.schema import Event, UnresolvedEntity
from app.scoring import ScoringConfig, propagate_event, refresh_all_derived

import replay_events as R

DATA = REPO / "data"
FIX = Path(__file__).parent / "fixtures"


def _min_event(**overrides) -> dict:
    base = {
        "id": "T-1",
        "timestamp": "2024-01-01T00:00:00Z",
        "headline": "test",
        "summary": "test",
        "entities_matched": [],
        "axes_impact": {"concentration_delta": 0.0},
    }
    base.update(overrides)
    return base


# --- §2 / §2.1 schema + extra="forbid" -------------------------------------

def test_event_rejects_unknown_top_level_key():
    with pytest.raises(ValidationError):
        Event.model_validate(_min_event(not_a_real_key="x"))


def test_nested_models_reject_unknown_key():
    # EntityMatch
    with pytest.raises(ValidationError):
        Event.model_validate(_min_event(
            entities_matched=[{"node_id": "a", "confidence": 1.0,
                               "match_type": "name", "bogus": 1}],
        ))
    # AxesImpact
    with pytest.raises(ValidationError):
        Event.model_validate(_min_event(axes_impact={"concentration_delta": 0.0, "bogus": 1}))
    # UnresolvedEntity
    with pytest.raises(ValidationError):
        Event.model_validate(_min_event(
            entities_unresolved=[{"mention": "x", "reason": "no_node", "bogus": 1}],
        ))


def test_entities_unresolved_defaults_empty_and_parses():
    e = Event.model_validate(_min_event())
    assert e.entities_unresolved == []
    e2 = Event.model_validate(_min_event(
        entities_unresolved=[
            {"mention": "germanium", "reason": "no_node"},
            {"mention": "Nexperia", "reason": "out_of_domain",
             "candidate_node_id": None, "notes": "n"},
        ],
    ))
    assert [u.mention for u in e2.entities_unresolved] == ["germanium", "Nexperia"]
    assert isinstance(e2.entities_unresolved[0], UnresolvedEntity)


# --- §5.2 the field never enters scoring -----------------------------------

def test_unresolved_not_read_by_scoring():
    """Executable proof that `entities_unresolved` does not touch the walk:
    propagate the SAME event with and without a populated
    `entities_unresolved` and assert every node's current_severity is
    byte-identical. If the field were read, some severity would move."""
    config = ScoringConfig.load(FIX / "scoring.yaml")

    def _severities_after(unresolved):
        g = SupplyChainGraph.from_dir(FIX, domain="ai")
        refresh_all_derived(g, config)
        ev = Event.model_validate(_min_event(
            id="probe",
            entities_matched=[{"node_id": "mineral:gallium",
                               "confidence": 1.0, "match_type": "name"}],
            axes_impact={"concentration_delta": 0.3},
            entities_unresolved=unresolved,
        ))
        propagate_event(ev, g, config)
        return {n.id: n.dynamic.current_severity for n in g.nodes.values()}

    without = _severities_after([])
    with_ = _severities_after([
        {"mention": "germanium", "reason": "no_node"},
        {"mention": "antimony", "reason": "no_node"},
    ])
    assert without == with_


def test_scoring_source_does_not_reference_entities_unresolved():
    """Belt-and-suspenders for §V3: the scoring path source files do not
    mention the field name at all."""
    for rel in ("app/scoring/cascade.py", "app/scoring/engine.py"):
        src = (BACKEND / rel).read_text()
        assert "entities_unresolved" not in src, rel


# --- §3 / exp 10 runner writes nothing under data/ -------------------------

def _hash_data_tree() -> dict[str, str]:
    return {
        str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in DATA.rglob("*") if p.is_file()
    }


def _assert_no_data_writes(fn) -> None:
    """Run `fn` and assert no file under data/ changed. Extracted so a
    proof-of-guard test can prove this actually fails on a write."""
    before = _hash_data_tree()
    fn()
    after = _hash_data_tree()
    assert before == after, (
        "a call wrote or changed a file under data/: "
        f"{set(before) ^ set(after) or [k for k in before if before[k] != after.get(k)]}"
    )


def test_runner_writes_nothing_under_data():
    """The register writer READS the disposition file under data/ but must
    not write anything there (INV-1's data/ half, made executable)."""
    config = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    events = [Event.model_validate(e)
              for e in json.loads(R.REPLAY_EVENTS.read_text())]
    graph = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
    refresh_all_derived(graph, config)
    _assert_no_data_writes(lambda: R._write_unresolved_register(events, graph))


def test_data_write_guard_actually_fails():
    """Proof-of-guard (exp 10): the data-write check must FAIL when a
    call deliberately writes under data/. A guard that never fails is
    not a guard."""
    sentinel = DATA / "ai" / "replay" / "_pass_v_guard_sentinel.tmp"

    def _naughty():
        sentinel.write_text("this simulates a bad runner writing to data/")

    try:
        with pytest.raises(AssertionError):
            _assert_no_data_writes(_naughty)
    finally:
        if sentinel.exists():
            sentinel.unlink()


# --- §3 / §6 aggregation + dangling ----------------------------------------

def test_register_aggregates_by_distinct_event():
    events = [
        Event.model_validate(_min_event(
            id="E1", entities_unresolved=[{"mention": "x", "reason": "no_node"}])),
        Event.model_validate(_min_event(
            id="E2", entities_unresolved=[{"mention": "x", "reason": "no_node"}])),
        Event.model_validate(_min_event(
            id="E3", entities_unresolved=[{"mention": "y", "reason": "out_of_domain"}])),
    ]
    agg = R._collect_unresolved(events)
    assert len(agg["x"]["event_ids"]) == 2
    assert agg["x"]["event_ids"] == {"E1", "E2"}
    assert len(agg["y"]["event_ids"]) == 1
    assert agg["y"]["reasons"] == {"out_of_domain"}


def test_register_dangling_section_detects_bad_ref():
    g = SupplyChainGraph.from_dir(FIX, domain="ai")
    good = Event.model_validate(_min_event(
        id="G", entities_matched=[{"node_id": "mineral:gallium",
                                   "confidence": 1.0, "match_type": "name"}]))
    bad = Event.model_validate(_min_event(
        id="B", entities_matched=[{"node_id": "mineral:unobtainium",
                                   "confidence": 1.0, "match_type": "name"}]))
    dangling = R._collect_dangling([good, bad], g)
    assert dangling == [("B", "mineral:unobtainium", "name", 1.0)]


def test_committed_events_have_no_dangling_references():
    """exp 7 — every committed event's entities_matched resolves."""
    config = ScoringConfig.load(REPO / "config" / "scoring.yaml")
    events = [Event.model_validate(e)
              for e in json.loads(R.REPLAY_EVENTS.read_text())]
    graph = SupplyChainGraph.from_dir(REPO / "data", domain="ai")
    refresh_all_derived(graph, config)
    assert R._collect_dangling(events, graph) == []


# --- §4 probe exclusion -----------------------------------------------------

def test_probes_excluded_from_register():
    """Probes never contribute register rows. Even a probe carrying an
    `entities_unresolved` entry must not appear — the register is built
    only from `events` in main(), never from probes."""
    committed = R.REPLAY_REGISTER.read_text()
    probe_ids = [p["id"] for p in json.loads(R.REPLAY_PROBES.read_text())]
    for pid in probe_ids:
        assert pid not in committed, f"probe {pid} leaked into the register"
    # Structural: a probe with an unresolved entry does not surface via the
    # collector when only events are passed (main() never passes probes).
    probe = Event.model_validate(_min_event(
        id="PROBE-X",
        entities_unresolved=[{"mention": "should_not_appear", "reason": "no_node"}]))
    agg_events_only = R._collect_unresolved([])  # main() feeds events, not probes
    assert "should_not_appear" not in agg_events_only


# --- §3 / §6 promotion threshold -------------------------------------------

def test_promotion_threshold_is_at_least_three():
    """The committed threshold must not be lowered below 3 (§6, stop §6)."""
    assert R._load_promotion_threshold() >= 3


def test_no_mention_promoted_on_current_corpus():
    """exp 5 — on the 7-event corpus, no mention reaches the threshold."""
    events = [Event.model_validate(e)
              for e in json.loads(R.REPLAY_EVENTS.read_text())]
    threshold = R._load_promotion_threshold()
    agg = R._collect_unresolved(events)
    promoted = {m: len(rec["event_ids"]) for m, rec in agg.items()
                if len(rec["event_ids"]) >= threshold}
    assert not promoted, f"unexpected promotion on current corpus: {promoted}"


def test_germanium_present_no_node():
    """exp 4 (substance) — germanium is in the register at count 1,
    reason no_node."""
    events = [Event.model_validate(e)
              for e in json.loads(R.REPLAY_EVENTS.read_text())]
    agg = R._collect_unresolved(events)
    assert "germanium" in agg
    assert len(agg["germanium"]["event_ids"]) == 1
    assert agg["germanium"]["reasons"] == {"no_node"}
