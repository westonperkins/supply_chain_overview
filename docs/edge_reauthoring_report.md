---
title: "Edge re-authoring pass — final report"
subtitle: "AI Supply Chain Terminal"
date: "2026-07-21"
---

## 1. What this pass did

Re-authored 53 edges — the 47 previously rescaled + the gallium/RF override + 5 adjacent HBM input_to edges that carried the same rescaling problem — from the paper. Not from arithmetic. Post-pass, no `supplies` or `input_to` bucket sums to exactly 1.0 by construction. Bucket incompleteness is the deliverable, not a bug.

Populated one `output_share` (HBM → NVIDIA = 0.90) from the paper's own figure on the paper's own edge.

Assertions:

```
OK  A1  no supplies / input_to bucket sums to exactly 1.0 by construction
OK  A2  every changed input_share has a source_note
OK  A3  every output_share has a source_note (1 / 1 populated)
OK  A4  edge count unchanged (167)
OK  A5  63 nodes score under both normalize modes
OK  A6  no inbound_hhi > 1.0 under either mode  (norm: 0, unnorm: 0)
```

## 2. Re-authoring ledger — 53 edges

Every value has a paper-cited or explicit "no direct paper basis; industry-informed estimate" source note on the edge. Grouped by target-bucket:

### company:tsmc supplies
Paper §2D anchors ASML as sole EUV maker. Paper does not quantify per-supplier share of a foundry's equipment input; the values below are industry-informed estimates of leading-edge fab tool-spend mix.

| edge                    | old   | new   |
|-------------------------|------:|------:|
| ASML → TSMC             | 0.514 | 0.400 |
| AMAT → TSMC             | 0.171 | 0.100 |
| LRCX → TSMC             | 0.114 | 0.080 |
| KLA → TSMC              | 0.086 | 0.050 |
| TEL → TSMC              | 0.114 | 0.080 |
| **bucket sum**          | 1.000 | **0.710** |

### company:samsung supplies
Same rationale; slightly different mix because Samsung's memory business raises AMAT / LRCX share.

| edge                    | old   | new   |
|-------------------------|------:|------:|
| ASML → Samsung          | 0.250 | 0.200 |
| AMAT → Samsung          | 0.250 | 0.120 |
| LRCX → Samsung          | 0.208 | 0.120 |
| KLA → Samsung           | 0.125 | 0.060 |
| TEL → Samsung           | 0.167 | 0.100 |
| **bucket sum**          | 1.000 | **0.600** |

### product:hbm input_to (per-buyer BOM share)
Paper §2C names HBM a co-equal bottleneck with the GPU. Does not quantify HBM's cost share; industry-informed: HBM ~25–35% of AI-GPU BOM.

| edge              | old   | new   |
|-------------------|------:|------:|
| HBM → NVIDIA      | 0.486 | 0.300 |
| HBM → AMD         | 0.469 | 0.250 |
| HBM → Broadcom    | 0.276 | 0.150 |
| HBM → Google      | 0.350 | 0.150 |
| HBM → Amazon      | 0.250 | 0.120 |
| HBM → Microsoft   | 0.250 | 0.120 |
| HBM → Meta        | 0.250 | 0.120 |

### product:cowos_packaging input_to
Paper §2E: CoWoS repeatedly gated GPU output. Paper does not quantify cost share; industry: advanced packaging ~15–25% of AI-GPU cost.

| edge                | old   | new   |
|---------------------|------:|------:|
| CoWoS → NVIDIA      | 0.513 | 0.200 |
| CoWoS → AMD         | 0.531 | 0.180 |
| CoWoS → Broadcom    | 0.621 | 0.150 |
| CoWoS → Google      | 0.600 | 0.150 |

### product:rf_power_semis input_to
| edge                | old  | new  |
|---------------------|-----:|-----:|
| RF → Broadcom       | 0.103 | 0.100 |

### mineral:gallium → product:rf_power_semis (paper override, restated)
**Paper basis, restated independently of tier effect:** Paper §1A: *"Gallium (GaAs/GaN wafers, RF chips, power electronics)."* RF & Power Semiconductors ARE gallium-material devices; the paper explicitly names gallium as the semiconductor input for this device class. Value stands on that paper claim alone.

| edge                                | old  | new  |
|-------------------------------------|-----:|-----:|
| gallium → rf_power_semis            | 0.90 | 0.90 |

### Hyperscaler supplies (chip supply into cloud/AI-lab operators)
Paper §2G names the hyperscaler / custom-silicon design pairings but does not quantify per-supplier share. Values are industry-informed estimates. Buckets deliberately incomplete.

| edge                              | old   | new   |
|-----------------------------------|------:|------:|
| TSMC → Amazon                     | 0.586 | 0.300 |
| Marvell → Amazon                  | 0.207 | 0.100 |
| NVIDIA → Amazon                   | 0.207 | 0.200 |
| TSMC → Google                     | 0.529 | 0.300 |
| Broadcom → Google                 | 0.294 | 0.200 |
| NVIDIA → Google                   | 0.176 | 0.100 |
| TSMC → Meta                       | 0.486 | 0.300 |
| Broadcom → Meta                   | 0.229 | 0.150 |
| NVIDIA → Meta                     | 0.286 | 0.250 |
| TSMC → Microsoft                  | 0.567 | 0.300 |
| NVIDIA → Microsoft                | 0.333 | 0.300 |
| Constellation → Microsoft         | 0.100 | 0.100 |

### Data-centre facility supplies
Paper §3–4 name Vertiv (cooling leader), Siemens Energy / GE Vernova (grid equipment with multi-year backlogs), Constellation / NextEra / Vistra / Talen (utilities). Paper does not quantify per-facility share. Industry-informed estimates.

12 edges into `facility:colossus` / `facility:stargate_abilene` / `facility:vantage_frontier` at values 0.05–0.20 each. Full list in the edges.json diff.

## 3. `output_share` population

Only one edge populated, per spec ("populate only what the paper quantifies").

| edge                 | value | paper basis                                                                                                                                                                                                                                                                                            |
|----------------------|------:|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| HBM → NVIDIA         |  0.90 | Paper §5: *"SK Hynix ~90% reliant on NVIDIA for HBM."* Applied to HBM → NVIDIA as the closest existing edge in the two-hop path SK Hynix → HBM → NVIDIA. Previous 0.70 (world-HBM-share arithmetic across three makers, a constructed number) overwritten with the paper's own figure on the paper's own edge. |

The previous pass's constructed 0.70 (world-HBM-share arithmetic across three makers) has been overwritten by the paper's stated 0.90.

## 4. Per-target sum table

| type       | targets | sum > 1.0 | min  | median | max  |
|------------|--------:|----------:|-----:|-------:|-----:|
| mines      |       5 |         1 | 0.65 |   1.00 | 1.17 |
| refines    |       5 |         2 | 0.90 |   1.00 | 1.10 |
| supplies   |      23 |         0 | 0.15 |   0.60 | 1.00 |
| input_to   |      21 |         0 | 0.08 |   0.15 | 1.00 |
| operates   |       5 |         0 | 1.00 |   1.00 | 1.00 |
| located_in |       8 |         2 | 1.00 |   1.00 | 6.00 |

Every `supplies` and `input_to` bucket sums to less than or equal to 1.0. Most are meaningfully below 1.0 — that is the honest reading, not a regression. The share-completeness backlog now correctly counts these as incomplete.

`mines` / `refines` / `located_in` sums over 1.0 come from country + facility double-counting that this task is scope-out to fix.

## 5. Full 63-node before/after — 1 tier change

Only one node moved on the default normalize=true.

| node | old sev → new sev | old tier → new tier |
|---|---:|---|
| **ASML** | 0.244 → 0.202 | **critical → high** |

Every other tier is stable across this pass on the default measure. Neodymium's severity moved slightly (0.220 → same), a handful of low-severity nodes moved a few thousandths — all within the same tier.

The single tier change matters, so §6 investigates it.

## 6. ASML investigation — the required §4 explanation

**Which axis moved: outbound.** ASML has no inbound supply edges in the graph, so `inbound_hhi = 0` under both modes. All of its severity comes from `outbound_criticality`.

**Which specific edge changes:** ASML supplies TSMC, Samsung, Intel, SK Hynix, Micron. Two of its five outbound edges were re-authored in this pass, both proportionally reduced from the previous rescaled values:

| edge              | pre-rescale (initial) | after rescale | after re-authoring |
|-------------------|----------------------:|--------------:|-------------------:|
| ASML → TSMC       |                 0.900 |         0.514 |              0.400 |
| ASML → Samsung    |                 0.300 |         0.250 |              0.200 |
| ASML → Intel      |                 0.250 |         0.250 |              0.250 |
| ASML → SK Hynix   |                 0.150 |         0.150 |              0.150 |
| ASML → Micron     |                 0.100 |         0.100 |              0.100 |

Cascade + outbound_criticality still read `input_share` (per spec), so as ASML's input_shares on its most consequential downstream edge (TSMC) declined across two passes (0.900 → 0.514 → 0.400), ASML's outbound_criticality declined too.

| pass                    | outbound_criticality | severity | tier      |
|-------------------------|---------------------:|---------:|-----------|
| before per-stage HHI    |                0.732 |    0.393 | critical  |
| after edge-weight split |                0.453 |    0.244 | critical  |
| after re-authoring      |                0.375 |    0.202 | **high**  |

**Position: sitting on the boundary.** ASML is at severity 0.202, threshold is 0.225. It is 0.023 below critical — the smallest possible gap that produces a tier change. Not stable.

**Deeper story — why this is happening.**

The `input_share` on ASML → TSMC (0.40) represents ASML's share of TSMC's *total equipment input*. That is the correct reading under the two-field schema. But the paper's chokepoint story for ASML is not "ASML is 40% of TSMC's total tool spend" — it is "ASML is the sole EUV supplier, and EUV is required for leading-edge chips."

The concentration measure rewards *large fraction of a target's total supply*. It does not represent *sole supplier of a critical category*. Under the current data model, categories inside `supplies` (litho vs. deposition vs. etch vs. inspection) are not separated — every equipment supplier feeds one bucket. So ASML at 0.40 cannot outscore the combination of AMAT (0.10) + LRCX (0.08) + KLA (0.05) + TEL (0.08) on inbound HHI, and its outbound criticality reads the 0.40 edge, not the "if this one supplier disappears, TSMC's leading-edge output stops" story.

Three ways the model could represent this properly; none of them are in scope:

- Split `supplies` into per-category buckets (litho, deposition, etch, inspection). ASML's litho bucket would be a single-edge bucket at 1.0 and would win the `max`. Schema change.
- Have cascade read `output_share` (or a hybrid) so ASML's near-100% of TSMC's litho input is what propagates downstream. Behavioural change flagged as out of scope in the two-field split spec.
- Introduce an explicit "sole supplier" / substitutability field on the edge itself. Schema change.

**Not adjusting.** The tier reading is honest given the current data model. ASML at high, 0.023 from critical, is the finding.

## 7. HBM status

Its critical → high drop persists.

| pass                    | inbound | outbound | severity | tier |
|-------------------------|--------:|---------:|---------:|------|
| before edge split       |   0.440 |    0.566 |    0.234 | critical |
| after edge split        |   0.440 |    0.424 |    0.178 | high |
| after re-authoring      |   0.440 |    0.252 |    0.178 | high |

The concentration is `max(inbound, outbound) = 0.440` and has been all along — HBM's inbound is inbound-dominated. Its severity comes from three-supplier concentration (SK Hynix 0.60 + Micron 0.21 + Samsung 0.19, HHI = 0.44).

**Restoring the paper's dependency judgment to `output_share` (0.90 on HBM → NVIDIA) does not restore HBM's tier.** Because `output_share` is not consumed by scoring anywhere — cascade still walks `input_share`. That was the spec's deliberate scope on the two-field split ("Cascade and outbound criticality stay on `input_share` for now").

The paper's chokepoint framing of HBM ("sold out through 2026", "co-equal bottleneck with the GPU") is a volume + lead-time story, plus a customer-concentration story on the supplier side. Neither maps to inbound HHI on the HBM node. The two-field split correctly moved the customer-concentration piece into `output_share`, but the current scoring path does not read that field. When it does (its own task), HBM's tier can be re-examined.

Not adjusting.

## 8. Paper chokepoint tiers

| node                      | normalized (default) | unnormalized     |
|---------------------------|----------------------|------------------|
| TSMC                      | critical (0.469)     | critical (0.469) |
| **ASML**                  | **high (0.202)**     | **high (0.202)** |
| gallium                   | critical (0.480)     | critical (0.480) |
| dysprosium                | critical (0.545)     | critical (0.556) |
| **HBM**                   | **high (0.178)**     | **high (0.178)** |
| CoWoS                     | critical (0.313)     | critical (0.313) |
| RF & Power Semiconductors | critical (0.319)     | critical (0.258) |

Five of seven paper chokepoints in both modes. ASML and HBM read as high — both explained above. RF & Power holds critical on the paper-cited gallium 0.90 (§1A), not on tier-preservation tuning.

## 9. Share-completeness backlog — grew, correctly

The backlog is larger than it was after the previous pass. Every re-authoring that lowered a supplies/input_to value pushed its bucket into the backlog. That is the deliverable, per spec ("Updated share-completeness backlog — expect it to grow, and that is correct").

## 10. Test suite

**normalize=true:** 2 failed, 23 passed
- `paper_chokepoints` — HBM and ASML at high, not critical. Explained in §6 and §7.
- `share_completeness` — the backlog. Explained in §9.

**normalize=false:** 3 failed, 22 passed
- Same two above.
- `bounds` — `combined_hhi` (legacy blended value, inspection-only, not read by scoring) can exceed 1.0 for a handful of nodes. Known finding from the previous report; a two-line clamp available but out of scope.

## 11. Files changed

```
data/ai/edges.json                        — 53 input_share re-authorings + 1 output_share
backend/tests/fixtures/ai/edges.json      — fixture synced
```

Untouched: schema, scoring, config, narration, frontend. Thresholds unchanged, `normalize` default remains `true`. Cascade and outbound criticality continue reading `input_share`.
