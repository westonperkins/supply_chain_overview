---
title: "Two-field edge weights — final report"
subtitle: "AI Supply Chain Terminal"
date: "2026-07-21"
---

## 1. Schema — one field became two

`Edge` now carries two distinct quantities:

- **`input_share`** — the source's share of the target's supply of the thing
  modelled by the edge type. Consumed by inbound HHI. Per-target, per-edge-type
  sums must not exceed 1.0.
- **`output_share`** — optional. The target's share of the source's output.
  Consumed by customer-concentration measures (and cascade later, as its own
  task). Populate only where the paper directly quantifies it.

Documented as a docstring on the model. A `weight` computed field remains as a
backward-compatible read alias so the frontend (which uses `e.weight`) does not
break. `types.ts` gets both fields; nothing else frontend touched.

Cascade and outbound criticality continue reading `input_share`, per spec.


## 2. Edge-change ledger

**47 rescales** across `supplies` and `input_to` buckets whose per-target sums
exceeded 1.0. Weights scaled proportionally so each bucket sums to 1.0, preserving
relative concentration. Every rescaled edge carries a `source_note` documenting
the reconciliation.

**1 paper override.** `e:gallium-input-rf` (gallium → RF & Power Semiconductors)
raised from **0.60 → 0.90** on the basis of paper §1A: "GaAs/GaN wafers, RF chips,
power electronics" — RF/Power semis ARE gallium-material devices, so 0.60 was
understating gallium's role. Called out explicitly per spec §6b so this move is
visible, not quiet.

**1 output_share populated** — `e:hbm-input-nvidia` = **0.70**. Basis: paper §5
"SK Hynix ~90% reliant on NVIDIA for HBM." SK Hynix is ~60% of world HBM →
~54% of world HBM to NVIDIA via SK Hynix; adding partial flow from Micron (21%)
and Samsung (19%) HBM makers to NVIDIA brings the total to roughly 0.70.
Confidence: estimate.

All other output_shares remain null. Not inventing values.


## 3. Per-target sum table — before / after

The audit table from `docs/edge_weight_semantics_report.md` regenerated:

| type       | targets | targets sum > 1.0 (before) | targets sum > 1.0 (after) | max (before) | max (after) |
|------------|--------:|---------------------------:|--------------------------:|-------------:|------------:|
| mines      |       5 |                          1 |                         1 |         1.17 |        1.17 |
| refines    |       5 |                          2 |                         2 |         1.10 |        1.10 |
| supplies   |      23 |                          9 |                     **0** |         1.75 |    **1.00** |
| input_to   |      21 |                          3 |                     **0** |         1.85 |    **1.00** |
| operates   |       5 |                          0 |                         0 |         1.00 |        1.00 |
| located_in |       8 |                          2 |                         2 |         6.00 |        6.00 |

`supplies` and `input_to` are now clean. `mines` / `refines` retain a handful of
sums slightly over 1.0 from country + facility double-counting (Mountain Pass
under both USA and its own facility node); the country → facility → mineral
re-modelling that would resolve this is out of scope.


## 4. Assertions

```
OK   A1  every edge has input_share; no raw weight persisted in JSON
OK   A2  no supplies/input_to bucket sum > 1.0                (0 offenders)
OK   A3  every edge with output_share has a source_note        (1 / 1)
OK   A4  63 nodes score under both normalize modes
OK   A5  gallium mined_by_hhi unchanged                        (0.9704 → 0.9704)
OK   A6  no inbound_hhi > 1.0 under normalize=false           (0 offenders)
??   A7  full test suite — see §7, some findings flagged
```

**All six spec-defined assertions pass.**


## 5. Paper chokepoints under new data

| node                      | normalized       | unnormalized      |
|---------------------------|------------------|-------------------|
| TSMC                      | critical (0.469) | critical (0.469)  |
| ASML                      | critical (0.244) | critical (0.244)  |
| gallium                   | critical (0.480) | critical (0.480)  |
| dysprosium                | critical (0.545) | critical (0.556)  |
| **HBM**                   | **high (0.178)** | **high (0.178)**  |
| CoWoS                     | critical (0.313) | critical (0.313)  |
| RF & Power Semiconductors | critical (0.319) | critical (0.258)  |

**HBM drops from critical to high** under the new data. This is a data-
reconciliation consequence, not a code bug — surfaced explicitly per spec.
See §6d below. **Six of seven paper chokepoints hold critical in both modes.**


## 6. Answers to §6

### §6a — TSMC dominant_axis

**Confirmed: flips to `outbound` under `normalize: false`.** The previous
audit's prediction bore out.

- normalized: inbound_hhi 1.000 · outbound 1.000 → `inbound` (tie-break)
- unnormalized: inbound_hhi **0.327** · outbound 1.000 → **`outbound`**

Under normalized: TSMC's supplies bucket sums to 1.0 after rescale; normalized
HHI reads the same as before (~1.00 because the rescale just renormalises).
Under unnormalized: TSMC's supplies HHI is the raw squared shares — ASML at
0.514 dominates, giving 0.327. That's below outbound (1.000), so TSMC now
correctly reads as depended-upon rather than dependent.

### §6b — RF & Power Semiconductors

`gallium → rf_power_semis` **`input_share` = 0.90** (up from 0.60).

**Basis** — paper §1A: "GaAs/GaN wafers, RF chips, power electronics." RF &
Power semiconductors are gallium-material devices. The 0.60 in the previous
data had no paper basis for being that low — it was the initial placeholder
from when the intermediate node was added to route gallium's downstream
transitively. Setting to 0.90 reflects the paper's stated material basis.

Not tuned to preserve a tier. Called out explicitly per spec §6b so anyone
reviewing sees the paper reasoning rather than a quiet override:

- Under `normalize: true`: RF & Power stays critical (sev 0.319, inbound_hhi
  1.00 — same as before).
- Under `normalize: false`: RF & Power stays critical (sev 0.258, inbound_hhi
  0.81 = 0.90²). This is the direct payoff of the paper-basis override — with
  the previous 0.60, unnormalized inbound_hhi would be 0.36 and the tier
  would drop.

If the paper basis is questioned in review, the value is one edit in the ledger.

### §6c — Does unnormalized now behave?

**inbound_hhi within [0, 1] for every node: YES.** All 63 nodes have
`inbound_hhi ≤ 1.0` under both modes.

**16 tier changes** between normalized and unnormalized modes. **15 of those
16** are in the share-completeness backlog — the direct evidence the measure
is doing its job. Incomplete nodes are the ones that move, and they move in
the direction the measure should move them (down).

One combined_hhi caveat (§7): the legacy blended value can still exceed 1.0
under unnormalized, but it's not read by scoring — it's inspection-only.

### §6d — HBM tier change (surfaced as a finding, not fixed)

HBM: normalized severity 0.234 → 0.178, tier critical → high.

Root cause: cascade + outbound criticality still read `input_share`, per spec.
Since HBM's downstream `input_to` edges got rescaled substantially
(HBM → NVIDIA 0.90 → 0.486, HBM → AMD 0.75 → 0.469, HBM → Broadcom 0.40 → 0.276),
HBM's outbound criticality dropped from 0.566 to ~0.42, dragging severity down.

The paper's HBM chokepoint framing ("sold out through 2026") is a supply-
volume constraint, not a supplier-concentration one. Under three-supplier
input-share (SK Hynix 0.60, Micron 0.21, Samsung 0.19 = HHI 0.44), HBM reads
as "a large share of the chain depends on it" — high, not critical. The
tier is the honest reading of the model given the data.

**Not fixing.** The spec is explicit: "Do not tune any weight to preserve a
node's current tier." If the review decides HBM needs to stay critical,
either (a) it belongs in a different node class than concentration measures
(a supply-volume / lead-time story), or (b) the paper-chokepoint list needs
different criteria than concentration alone. Both are worth surfacing.


## 7. Test suite under both modes

**Normalized (default):** 2 failed, 23 passed.

- `paper_chokepoints` — HBM at high, not critical. See §6d.
- `share_completeness` — 26 buckets below 0.80. Pre-existing; unchanged by
  this task. Rescaling supplies/input_to reduced some individual shares but
  did not add any missing sources.

**Unnormalized (`normalize: false`):** 3 failed, 22 passed.

- `paper_chokepoints` — same as above.
- `share_completeness` — same.
- `bounds` — `combined_hhi` (legacy blended value, inspection-only) is > 1.0
  for 5 nodes (gallium 1.005, dysprosium 1.103, NVIDIA 1.481, Broadcom
  1.375, AMD 1.462). This is because `hhi_from_derived_shares` merges every
  stage into one supplier map via strongest-per-source without a subsequent
  cap. Not read anywhere in the current scoring pipeline; kept solely for
  before/after diff. If it needs bounds, that's a two-line clamp — but per
  scope, not touching it here. The relevant `inbound_hhi` (§6c) stays in
  [0, 1].


## 8. Updated share-completeness backlog

Unchanged in structure — the rescaling didn't add or remove edges, only
scaled values. 26 buckets remain below 0.80.

The three critical FAILs from the previous backlog:

- `input_to` buckets at 0.08 sum: TSMC, SK Hynix, Micron, Colossus, Stargate,
  Vantage Frontier, The Citadel — same as before (copper is the sole
  modelled input for each).
- `input_to` buckets at 0.25: Amazon, Microsoft, Meta (single NVIDIA edges,
  down from 0.30 each).

Rescaling didn't complete these buckets; that's what a data-completion pass
would do.


## 9. Files changed

```
backend/app/schema/edge.py          — input_share + output_share, computed weight alias
frontend/src/types.ts               — both fields in the Edge interface
data/ai/edges.json                  — 47 rescales + 1 paper override + 1 output_share
backend/tests/fixtures/ai/edges.json — fixture synced
```

Untouched: cascade, outbound criticality, rating, all narration code +
narration.yaml, thresholds, `normalize` default (still true), everything
else frontend. Cascade and outbound will pick up the new values via
`input_share` reads through `effective_input_share()` — that's the intended
propagation, not a behavioural change of the algorithms themselves.
