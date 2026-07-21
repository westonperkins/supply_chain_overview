---
title: "Test suite — final report"
subtitle: "AI Supply Chain Terminal"
date: "2026-07-21"
---

## 1. What was built

A permanent pytest suite that runs against a frozen graph snapshot in
`backend/tests/fixtures/`. No live API calls, no network dependency,
deterministic across runs.

```
backend/tests/
├── conftest.py                          — session-scoped graph, config,
│                                          narration builder fixtures
├── helpers.py                           — pure helpers reused by tests
│                                          + the report script
├── fixtures/                            — frozen snapshot (no live API)
│   ├── ai/{nodes,edges,events}.json
│   ├── scoring.yaml
│   └── narration.yaml
├── test_share_completeness.py           — Test 1  (fails)
├── test_thin_buckets.py                 — Test 2  (probe)
├── test_structural_no_zero.py           — Test 3
├── test_idempotence.py                  — Test 4
├── test_tier_coherence.py               — Test 5  (+ writes schema gap)
├── test_config_coherence.py             — Test 6
├── test_bounds.py                       — Test 7
├── test_graph_integrity.py              — Test 8
├── test_paper_chokepoints.py            — Test 9
├── test_narration.py                    — Test 10
├── test_outbound_sensitivity.py         — Test 11 (probe)
├── run_report.py                        — bundles everything
└── _out/                                — one artefact per report deliverable
    ├── share_backlog.txt
    ├── thin_buckets.txt
    ├── outbound_sensitivity.txt
    └── schema_gap.txt
```

Design rule from the spec held throughout: **invariants, not values.** The
only place specific values are asserted is the paper-chokepoint list in
Test 9, per the spec's strict exception.


## 2. Pytest summary — 22 tests, 21 pass, 1 fail

**Failing by design, not fixed:**

| Test                                     | Why it fails                                                                                                                                                                                                     |
|------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `test_no_stage_bucket_sums_below_0_80`   | 26 stage buckets sum below 0.80. Largest offenders: single-edge `input_to` buckets at 0.08 sum (TSMC, SK Hynix, Micron, several data-centre facilities). Same nodes the thin-graph TODO already flagged. |

All 21 other tests pass — including `test_structural_no_zero` (the
assertion that would have caught the previous stage-list defect),
`test_every_paper_chokepoint_is_critical`, and every narration invariant.


## 3. Share-completeness backlog — 29 buckets below 0.95

The main deliverable of this task. Sorted by shortfall, worst first.

| severity | sum   | edges | node                                | stage      |
|----------|------:|------:|-------------------------------------|------------|
| FAIL     | 0.080 |     1 | TSMC                                | input_to   |
| FAIL     | 0.080 |     1 | SK Hynix                            | input_to   |
| FAIL     | 0.080 |     1 | Micron                              | input_to   |
| FAIL     | 0.080 |     1 | Colossus                            | input_to   |
| FAIL     | 0.080 |     1 | Stargate (Abilene)                  | input_to   |
| FAIL     | 0.080 |     1 | Vantage Frontier                    | input_to   |
| FAIL     | 0.080 |     1 | The Citadel                         | input_to   |
| FAIL     | 0.090 |     2 | Samsung Electronics                 | input_to   |
| FAIL     | 0.250 |     1 | Amazon                              | input_to   |
| FAIL     | 0.250 |     1 | Microsoft                           | input_to   |
| FAIL     | 0.250 |     1 | Meta                                | input_to   |
| FAIL     | 0.300 |     2 | Constellation Energy                | supplies   |
| FAIL     | 0.300 |     1 | Quanta Services                     | input_to   |
| FAIL     | 0.450 |     2 | GE Vernova                          | input_to   |
| FAIL     | 0.500 |     2 | Siemens Energy                      | input_to   |
| FAIL     | 0.530 |     3 | Vertiv                              | input_to   |
| FAIL     | 0.600 |     1 | RF & Power Semiconductors           | input_to   |
| FAIL     | 0.600 |     3 | Duke Energy                         | supplies   |
| FAIL     | 0.650 |     5 | Copper                              | mines      |
| FAIL     | 0.650 |     3 | Micron                              | supplies   |
| FAIL     | 0.700 |     3 | Intel                               | supplies   |
| FAIL     | 0.750 |     4 | Indium                              | mines      |
| FAIL     | 0.750 |     3 | NextEra Energy                      | supplies   |
| FAIL     | 0.750 |     4 | The Citadel                         | supplies   |
| FAIL     | 0.800 |     2 | xAI                                 | supplies   |
| FAIL     | 0.800 |     2 | OpenAI                              | supplies   |
| warn     | 0.800 |     2 | NdFeB Permanent Magnets             | input_to   |
| warn     | 0.900 |     4 | Gallium                             | refines    |
| warn     | 0.930 |     4 | Indium                              | refines    |

Same list is written to `backend/tests/_out/share_backlog.txt`.


## 4. Thin-bucket census — 14 single-edge buckets, all win the `max`

Every one of the 14 is decided by a bucket containing exactly one edge, so
its HHI is 1.0 by construction and it wins `combine: max` for the node's
`inbound_hhi`. This is the numeric size of the thin-graph problem.

| won max | bucket HHI | node                                | stage      |
|---------|-----------:|-------------------------------------|------------|
| yes     |      1.000 | AMD                                 | supplies   |
| yes     |      1.000 | Amazon                              | input_to   |
| yes     |      1.000 | Broadcom                            | supplies   |
| yes     |      1.000 | Colossus                            | input_to   |
| yes     |      1.000 | Meta                                | input_to   |
| yes     |      1.000 | Micron                              | input_to   |
| yes     |      1.000 | Microsoft                           | input_to   |
| yes     |      1.000 | Quanta Services                     | input_to   |
| yes     |      1.000 | RF & Power Semiconductors           | input_to   |
| yes     |      1.000 | SK Hynix                            | input_to   |
| yes     |      1.000 | Stargate (Abilene)                  | input_to   |
| yes     |      1.000 | TSMC                                | input_to   |
| yes     |      1.000 | The Citadel                         | input_to   |
| yes     |      1.000 | Vantage Frontier                    | input_to   |

Nodes whose `inbound_hhi` is decided by a single-edge bucket: **14**.


## 5. Outbound sensitivity — removing TSMC shifts 4 tiers

`outbound_criticality` normalises to graph max, so any single node's raw
score can drag every other node's score. Removing the highest-outbound
node (TSMC, raw 1.000) and renormalising:

```
mineral:copper       high → critical
company:kla          none → moderate
company:mp_materials none → moderate
company:lynas        none → moderate
```

**4 tiers move on the removal of one node.** When robotics/aerospace land
on the same graph, AI tiers will shift for non-AI reasons proportional
to this number.


## 6. Baseline-vs-current severity — schema gap, finding not fix

`scoring.yaml` says thresholds apply to *baseline* severity. The schema
has only `current_severity`, which `compute_baseline_severity` writes
into — they're the same value today, so the test cannot distinguish them.

As soon as event ingestion applies `AxesImpact` deltas,
`current_severity` will drift with the news, and tiers derived from it
will drift with the news too.

Fix path (recorded in `_out/schema_gap.txt`, NOT applied in this task):

- Add `baseline_severity` alongside `current_severity` on `DynamicFields`.
- `refresh_all_derived` writes `baseline_severity`.
- `propagate_event` writes `current_severity` per-event, without
  touching tier.
- Tier derived from `baseline_severity` only.


## 7. Two things worth flagging about the tests themselves

- **`test_prose_percentages_match_edge_weights`** currently passes, but
  its guard is fairly loose — it matches any edge weight *touching* the
  node. The strict invariant is "matches a weight of an edge in the
  specific bucket this prose sentence is about," but that requires the
  narration builder to expose which edge produced which percentage.
  Kept the looser version to avoid coupling the test to narration
  internals. Flagged so nobody thinks this test is stronger than it is.

- **`test_every_node_has_at_least_one_edge`** passes — nothing is
  currently isolated. If a future data edit adds an unreferenced country
  or facility, this test catches it before the graph renders.


## 8. How to run

```bash
# just the tests
cd backend && .venv/bin/python -m pytest -v tests/

# tests + bundled report artefacts (this document's inputs)
backend/.venv/bin/python -m backend.tests.run_report
```

Documented at the repo root in `README.md`.


## 9. What did not happen

Per the "no fixes" clause of the spec: nothing was fixed. Not one edge
added, not one weight changed, not one threshold moved, not one line of
scoring / schema / config / narration touched.

The failures and the two probes are the deliverable.
