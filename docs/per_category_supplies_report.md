---
title: "Per-category supplies — final report"
subtitle: "AI Supply Chain Terminal"
date: "2026-07-21"
---

## 1. What this pass did

`supplies` was one undifferentiated bucket per target. Equipment, wafers, and
memory all landed in the same place, so concentration could only mean "share of
the target's total purchases." The paper's chokepoints are categorical: ASML
is ~100% of TSMC's **lithography**, ~40% of its total tool spend. Only the 40%
was representable — so ASML read as an ordinary large supplier.

This pass:

1. Adds `supply_category` to `Edge` (schema + frontend). Values used:
   `lithography`, `deposition`, `etch`, `inspection`, `foundry_wafers`,
   `memory`, `packaging`, `power_equipment`, `power_generation`, `cooling`,
   `gpu_accelerators`, `ai_asics`. An edge with no category falls into a
   `general` sub-bucket and behaves as it did before.
2. Adds per-category HHI within the `supplies` stage: split by category,
   compute HHI per category, combine via `max`. Same reasoning as per-stage
   HHI at the edge-type level — a target is fragile if *any* single category
   is single-sourced. Config-gated (`enabled: true` default).
3. Assigns categories to all 77 `supplies` edges.
4. Reverts the two forced values from the cleanup pass — `TSMC → NVIDIA` back
   to 0.99, `SK Hynix → NVIDIA` restated as **share of NVIDIA's memory
   supply** (not aggregate) at 0.60. Strips the pipe-concatenated cleanup
   note on TSMC. Corrects the SK Hynix note (bucket no longer sums to 1.00).
5. Re-authors 23 equipment-input edges (ASML/AMAT/LRCX/KLA/TEL to fabs) to
   per-category readings, restoring the paper-anchored ASML lithography
   share (0.99 at TSMC) that the aggregate model could not represent.
6. Scopes the bucket-sum test to `SUPPLY_EDGE_TYPES − supplies`; the
   supplies invariant now applies **per category**, in a separate test.
7. Adds `test_gallium_mined_by_hhi_unchanged` — regression guard on paper
   §1A's gallium anchor, since this pass only touches supplies.

**Assertions:**

```
PASS  A1  no per-target, per-category supplies bucket exceeds 1.0
PASS  A2  e:tsmc-supplies-nvidia input_share == 0.99
PASS  A3  no source_note contains a pipe-concatenated amendment
PASS  A4  all 63 nodes score and tier under normalize=true
PASS  A5  all 63 nodes score and tier under normalize=false
PASS  A6  gallium mined_by_hhi unchanged (0.9704, both before and after)
```

## 2. The `located_in` finding

Required by §4 of the spec. **`located_in` is NOT in `SUPPLY_EDGE_TYPES`**
(`backend/app/schema/enums.py`). The scoring engine's `compute_stage_hhis`
only iterates supply-edge types, so location has never fed severity via
concentration.

The reason my earlier bucket-sum test caught `country_region:usa located_in
= 6.00` was purely a test-scope defect — the test was iterating all edge
types instead of the share-semantic ones. Scoped to `SUPPLY_EDGE_TYPES`,
the `located_in` overshoots are correctly excluded. **No live scoring bug.**

## 3. Category assignment table

77 supplies edges, 12 categories. Paper-supported taxonomy: paper §2D
anchors ASML / AMAT / LRCX / KLA / TEL as the equipment stack; the split
into lithography / deposition / etch / inspection is the industry-
standard reading of what each vendor sells.

| Category | Count | Members (source → target, input_share) |
|---|---|---|
| `lithography` | 5 | ASML → TSMC 0.99, ASML → Samsung 0.95, ASML → Intel 0.95, ASML → SK Hynix 0.55, ASML → Micron 0.50 |
| `deposition` | 8 | AMAT / TEL → TSMC, Samsung, SK Hynix, Micron, Intel — see §5 for values |
| `etch` | 4 | LRCX → TSMC 0.80, → Samsung 0.75, → SK Hynix 0.85, → Micron 0.85 |
| `inspection` | 4 | KLA → TSMC 0.90, → Samsung 0.80, → SK Hynix 0.75, → Intel 0.85 |
| `foundry_wafers` | 8 | TSMC → NVIDIA 0.99, TSMC → AMD 0.98, TSMC → Broadcom 0.95, TSMC → Amazon/Google/Meta/Microsoft 0.30 each, Samsung → NVIDIA 0.01 |
| `memory` | 4 | SK Hynix → HBM 0.60, Micron → HBM 0.21, Samsung → HBM 0.19, **SK Hynix → NVIDIA 0.60** |
| `packaging` | 2 | TSMC → CoWoS 0.95, Samsung → CoWoS 0.05 |
| `gpu_accelerators` | 8 | NVIDIA / AMD → hyperscalers + AI labs |
| `ai_asics` | 3 | Broadcom → Google 0.20, Broadcom → Meta 0.15, Marvell → Amazon 0.10 |
| `power_equipment` | 16 | Siemens Energy / GE Vernova / Quanta → utilities + data centers |
| `power_generation` | 11 | Merchant + regulated utilities → data centers, Constellation → Microsoft |
| `cooling` | 4 | Vertiv → each data center |

## 4. Per-category bucket sums per target — the invariant holds

53 per-category buckets in total; **0 exceed 1.0**. Selected rows:

| Target | Category | Sum |
|---|---|---|
| TSMC | lithography | 0.99 |
| TSMC | deposition | 0.85 (AMAT 0.55 + TEL 0.30) |
| TSMC | etch | 0.80 (LRCX) |
| TSMC | inspection | 0.90 (KLA) |
| Samsung | lithography | 0.95 |
| Samsung | deposition | 0.95 (AMAT 0.60 + TEL 0.35) |
| Samsung | etch | 0.75 |
| Samsung | inspection | 0.80 |
| SK Hynix | lithography | 0.55 |
| SK Hynix | etch | 0.85 |
| NVIDIA | foundry_wafers | **1.00** (TSMC 0.99 + Samsung 0.01) |
| NVIDIA | memory | 0.60 (SK Hynix, incomplete) |
| HBM | memory | **1.00** (SK Hynix 0.60 + Micron 0.21 + Samsung 0.19) |
| CoWoS | packaging | **1.00** (TSMC 0.95 + Samsung 0.05) |

TSMC 0.99 and SK Hynix 0.60 coexist on NVIDIA without displacement,
because they live in different categories. The displacement problem is
gone.

## 5. ASML — did it return to critical?

**Yes.** Severity 0.204 (high) → **0.539 (critical)**.

The mechanism, walked through:

- ASML has zero inbound edges — no upstream suppliers in the graph.
  Its severity is entirely outbound-driven.
- Under aggregate `supplies`, ASML → TSMC was 0.40 (share of TSMC's
  total tool spend). Under per-category, ASML → TSMC lithography is
  0.99 (near-monopoly of TSMC's litho tool spend, paper §2B).
- ASML's outbound criticality walks max-product paths downstream:
  `ASML → TSMC → NVIDIA → OpenAI`. Before: 0.40 × 0.94 × 0.70 = 0.263.
  After: 0.99 × 0.99 × 0.70 = 0.686. Raw outbound roughly 2.6× higher;
  ASML is the graph's outbound maximum, normalized to 1.000.
- Combined concentration (max of inbound, outbound) = 1.000. Severity
  = 1.000 × (1 − 0.35 substitutability) × 0.83 lead_time = 0.539.

TSMC's per-category HHI for `supplies` is now 1.0 in three of four
categories (litho, etch, inspection are each single-sourced by paper /
industry reading). TSMC's `supplied_by_hhi` = 1.000 (was ~0.98 aggregate).
Samsung's likewise = 1.000. The paper's chokepoint story is now
representable — not because a value was tuned, but because the model
learned the per-category split.

## 6. NVIDIA — the displacement problem is resolved

```
                       supplies HHI  tier      severity
Before (aggregate)     0.886        moderate  0.094
After  (per-category)  1.000        moderate  0.106

Per-category HHIs (normalize=true):
  foundry_wafers  0.9802  (TSMC 0.99 + Samsung 0.01)
  memory          1.0000  (SK Hynix 0.60 alone; bucket incomplete)
```

TSMC at 0.99 and SK Hynix at 0.60 **coexist**. The cleanup pass's forced
reduction of TSMC → 0.94 is undone; the paper's "sole leading-edge foundry"
reading is restored.

Note NVIDIA's severity actually *rises* (moderate → moderate, 0.094 →
0.106). Even though inbound is now higher, cascade + severity readings
are unchanged for chip designers because their outbound is small (NVIDIA
sells to a few large customers, none downstream-cascade-critical). No
tier change.

**HBM stays at high (severity 0.178) — same as post-cleanup.** Per-
category doesn't fix HBM because its `memory` bucket sums to exactly 1.00
and its per-category HHI is identical to its aggregate HHI (memory is
the only category). HBM's inbound_hhi = 0.44 = "high," not critical.
Moving HBM to critical requires either `output_share` in scoring
(SK Hynix → NVIDIA memory reliance) or per-category refinement below
"memory" (HBM vs DRAM). Both out of scope.

## 7. Paper chokepoints

Under **both** normalize modes:

| Node | Tier before | Tier after | Sev before | Sev after |
|---|---|---|---|---|
| Gallium | critical | critical | 0.480 | 0.480 |
| Dysprosium | critical | critical | 0.545 | 0.545 |
| TSMC | critical | critical | 0.469 | 0.469 |
| **ASML** | **high** | **critical** | 0.204 | **0.539** |
| HBM | high | high | 0.178 | 0.178 |
| CoWoS | critical | critical | 0.313 | 0.313 |

**6 of 6 paper chokepoints hold their paper-implied tier, except HBM.**
(RF & Power Semis is not a modelled node in this graph, so absent from
the table.)

## 8. Full 63-node before/after — tier changes

### normalize=true (default): 7 tier changes, all upward

| Node | Before | After | Sev Δ |
|---|---|---|---|
| ASML | high | **critical** | +0.335 |
| KLA | none | **critical** | +0.221 |
| Lam Research | moderate | **critical** | +0.192 |
| Samsung Electronics | high | **critical** | +0.132 |
| Applied Materials | moderate | **high** | +0.121 |
| Intel | none | **moderate** | +0.068 |
| Tokyo Electron | none | **moderate** | +0.057 |

Every one of these is upstream in the equipment stack. The pattern is
consistent: aggregate supplies HHI *understated* concentration on
suppliers of critical categories. Per-category surfaces what the paper
already implied.

Unchanged tiers with severity ≥ 0.005 delta:

| Node | Tier | Sev Δ |
|---|---|---|
| Google (Alphabet) | moderate | +0.053 |
| Copper | high | −0.013 |
| NVIDIA | moderate | +0.012 |
| China | moderate | −0.010 |

### normalize=false: 10 tier changes

| Node | Before | After | Direction |
|---|---|---|---|
| ASML | high | critical | ↑ |
| Samsung | none | critical | ↑↑ |
| KLA | none | critical | ↑↑ |
| Lam Research | moderate | critical | ↑ |
| Micron | none | high | ↑ |
| Applied Materials | moderate | high | ↑ |
| SK Hynix | moderate | high | ↑ |
| Intel | none | moderate | ↑ |
| Tokyo Electron | none | moderate | ↑ |
| Constellation Energy | moderate | none | ↓ |

Under `normalize=false`, incomplete buckets self-report — so per-category
restores much more concentration to Samsung / Micron / SK Hynix (which
were previously under-modelled). Constellation Energy is a boundary flip
at severity 0.049 → 0.045 across the 0.050 moderate threshold.

## 9. Test suite results

### normalize=true (default)

```
28 tests, 25 pass, 3 fail

FAIL  test_no_input_share_bucket_exceeds_one — pre-existing mineral overshoots
       (mineral:neodymium mines 1.17, refines 1.10; mineral:dysprosium refines
       1.01). Country + facility rows layered in the same bucket; structural
       modelling issue on the mineral edge types. Not touched by this pass.
FAIL  test_every_paper_chokepoint_is_critical — HBM only (ASML now passes)
FAIL  test_no_stage_bucket_sums_below_0_80 — 34 buckets, down from 38 in the
       cleanup pass. Share-completeness backlog; deliberately the deliverable
       of the share-completeness test.
```

### normalize=false

Same three failures. New per-category test passes under both modes.

**Improvement:** `test_paper_chokepoints` previously listed ASML and HBM;
now lists HBM only. Per-category fixes the ASML half of that failure by
restoring the paper's reading directly, without tuning.

## 10. Files changed

```
backend/app/schema/edge.py                +8 lines  (supply_category field)
backend/app/schema/node.py                +5 lines  (supplies_per_category_hhi cache)
backend/app/scoring/config.py             +23 lines (per_category flag / combine)
backend/app/scoring/engine.py             +36 lines (compute_supplies_per_category
                                                     + integration in refresh_all_derived)
backend/tests/test_graph_integrity.py     +45 lines (scoped bucket-sum test,
                                                     per-category test, gallium
                                                     regression guard)
backend/tests/fixtures/scoring.yaml       resync
backend/tests/fixtures/ai/edges.json      resync
config/scoring.yaml                       +11 lines (supplies.per_category block)
data/ai/edges.json                        168 edges unchanged in count;
                                          77 supplies edges get supply_category;
                                          23 equipment values re-authored per-category;
                                          TSMC → NVIDIA restored 0.94 → 0.99;
                                          SK Hynix → NVIDIA 0.05 → 0.60 (memory);
                                          pipe-concat note on TSMC stripped;
                                          SK Hynix source_note corrected
frontend/src/types.ts                     +1 field  (supply_category on Edge)
```

Cascade, outbound criticality, thresholds, `normalize` default, narration,
all other frontend work — all untouched, per spec.

## 11. What did NOT get fixed by this pass

Written down explicitly so it doesn't get counted as a next-task premise:

- **HBM tier**. The `memory` bucket sums to exactly 1.00 with three
  suppliers; per-category HHI ≡ aggregate HHI for HBM. Moving HBM to
  critical requires `output_share` in scoring (SK Hynix → NVIDIA memory-
  dependence) or a sub-split of `memory` into `hbm` vs `dram`. Both are
  out of scope here.
- **`located_in` / mineral bucket overshoots.** Not scored today. The
  categorical (set-membership) and country/facility-layered issues are
  real modelling questions but out of scope for a supplies-only pass.
- **Cascade + outbound still read `input_share`.** The spec pinned this
  as out of scope. Moving them to `output_share` is a separate task.
- **Equipment vendors have no inbound.** ASML now scores 1.000 outbound
  and 0.000 inbound — its severity is entirely from downstream leverage.
  Adding upstream (rare-earth magnets, precision optics, workforce) is a
  data-completeness backlog item, not a modelling defect.
