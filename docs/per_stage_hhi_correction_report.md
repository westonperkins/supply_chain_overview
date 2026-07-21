---
title: "Per-stage HHI correction — final report"
subtitle: "AI Supply Chain Terminal"
date: "2026-07-21"
---

## 0. Both defects fixed

**Defect 1 (spec-level).** `stages: [mines, refines, supplies]` excluded `input_to` and `component_of`, which is where the graph carries mineral → product and product → product supply. Seven nodes lost all inbound visibility and read `inbound_hhi = 0`. RF & Power Semiconductors — single-sourced from gallium (0.97) — went critical → none.

**Defect 2 (implementation-level).** `refresh_all_derived` hardcoded `mined_by_hhi`, `refined_by_hhi`, `supplied_by_hhi` in Python, and the combine logic only recognised those three keys. Changing `stages` in the yaml would have silently no-op'd. Fixed properly rather than by editing the list.


## 1. Assertions — all pass

```
OK    A1  stage_hhis == stages with edges present on every node
OK    A2  inbound_hhi == max(stage_hhis) under default config
OK    A3  no node with inbound supply edges reads inbound_hhi = 0
OK    A4  invalid stage in config raises ValueError at load
OK    A5  all 63 nodes score and tier (63 present)
OK    A6  gallium mined_by_hhi = 0.970 ≥ 0.85
OK    A7  RF & Power Semiconductors tier = critical
OK    A8  copper has 5 refiner edges (≥ 3 required)
```

A3 is the structural assertion the spec asked for. It's now in the test script — it would have caught the original defect without needing anyone to notice a symptom.

A4 was verified by a subprocess that mutates the yaml with a bogus stage (`nonsense_edge_type`) and loads the config — raises `ValueError` at load, does not silently accept it.


## 2. Widened validation set

| Node                                | old sev → new sev  | old tier → new tier         |
|-------------------------------------|--------------------|-----------------------------|
| TSMC                                | 0.469 → 0.469      | critical → critical         |
| ASML                                | 0.393 → 0.393      | critical → critical         |
| gallium                             | 0.480 → 0.480      | critical → critical         |
| dysprosium                          | 0.545 → 0.545      | critical → critical         |
| HBM                                 | 0.234 → 0.234      | critical → critical         |
| CoWoS                               | 0.313 → 0.313      | critical → critical         |
| **RF & Power Semiconductors**       | **0.028 → 0.319**  | **none → critical** ✓        |
| **Siemens Energy**                  | 0.061 → 0.224      | moderate → high             |
| **GE Vernova**                      | 0.064 → 0.216      | moderate → high             |
| **copper**                          | **0.710 → 0.207**  | **critical → high**         |
| **NdFeB Permanent Magnets**         | 0.043 → 0.213      | none → high                 |
| neodymium                           | 0.220 → 0.220      | high → high                 |

**All six five-alarm remain critical. RF & Power returns to critical (from none) — the primary correctness target of this task.**


## 3. Copper — per-stage values with the new refiner edges

New refiner edges (`refines`, confidence `estimate`):

| source | weight |
|--------|-------:|
| China  | 0.47 (paper explicit) |
| Chile  | 0.15 |
| DRC    | 0.13 |
| Peru   | 0.13 |
| USA    | 0.12 |

All ex-China shares carry an identical source note explaining the paper only quantifies China's ~47%; the ex-China share is distributed across the countries the paper names in the copper section, proxied from mining prominence.

```
mined_by_hhi   = 0.2488
refined_by_hhi = 0.2916    ← was 1.0000 (single edge)
combined_hhi   = 0.2740    (legacy blended, kept for inspection)
inbound_hhi    = 0.2916    (max under default)
severity       = 0.2070
tier           = high      (was critical, dropped one tier)
```

Refined HHI landed exactly in the 0.25–0.30 band the spec predicted. Copper leaves critical because the data got better, not because the weights were tuned. Its updated caveat now names the remaining exposure — the scale axis — rather than the refiner monopoly.


## 4. Full 63-node before/after — 18 tier changes

Sorted by new severity; every node with a tier change flagged. Summary of the shape:

| tier change                         | count |
|-------------------------------------|------:|
| none → critical                     | 1 (RF & Power) |
| moderate → critical                 | 2 (SK Hynix, Micron) |
| critical → high                     | 1 (copper) |
| moderate → high                     | 2 (Siemens Energy, GE Vernova) |
| none → high                         | 1 (NdFeB) |
| moderate → high (Samsung inbound)   | 1 |
| none → moderate                     | 10 (Vertiv, Quanta, Google, Amazon, Microsoft, Meta, Colossus, Stargate, Vantage, Citadel) |

**Two categories of change worth naming:**

- **The intended fixes:** RF & Power → critical; NdFeB, Siemens Energy, GE Vernova → high; copper → high (from better data). These are the changes the correction was for.
- **The thin-graph nodes returning to their real scores:** Quanta went `none → moderate` because its single-modelled input (copper) once again shows an `input_to` HHI of 1.0. The spec explicitly predicted this and called out that it "will return to 1.0 once this is fixed, and the thin-graph TODO remains the correct place for it." Same explanation covers SK Hynix / Micron / Samsung / NVIDIA / Broadcom / AMD (single modelled copper input), the hyperscalers (single modelled NVIDIA input), and the data-center facilities (single modelled NdFeB input).

The thin-graph TODO in `scoring.yaml` remains — that's where these nodes' story lives. **No weights were tuned to push any of them back down.**


## 5. Structural sweep

```
No node with inbound supply edges has inbound_hhi = 0.
```

The A3 assertion applied across all 63 nodes — every node that has any inbound `mines` / `refines` / `supplies` / `input_to` / `component_of` edge now reads a non-zero HHI. The seven-node black hole from the previous state is gone.


## 6. Caveat updates

**Copper — rewritten to the post-fix state:**

> Per-stage HHI split done and refiner edges now modelled across the paper's named copper countries (China ~47% from paper; Chile, DRC, Peru and US distributing the ex-China share proxied from mining prominence, since the paper does not detail ex-China refining). Refining HHI reads roughly 0.29 as a result. The remaining exposure the model does not represent is the scale axis — the paper's copper story is a ~23 Mt/yr volume against a 17–25 year mine lead time, i.e. a scale/demand constraint, not a concentration one. Concentration is no longer absorbing that risk.

**Quanta, xAI, OpenAI caveats stand** — their thin-graph problem is unchanged by this task and remains a data-completeness item.


## 7. Six-narration re-run — one flagged shift, no regressions

- **Gallium:** "One source controls almost all supply (0.97 on a 0–1 scale)." ✓ (unchanged from previous fix)
- **Dysprosium:** "One source controls almost all supply (0.96 on a 0–1 scale)." ✓
- **ASML:** "Almost everything downstream runs through it (0.73 on a 0–1 scale)." ✓
- **HBM:** "A large share of the chain depends on it (0.58 on a 0–1 scale)." ✓
- **CoWoS:** "One source controls almost all supply (0.90 on a 0–1 scale)." ✓
- **TSMC:** `dominant_axis` flipped `outbound → inbound`. Now reads: "One source controls almost all supply (1.00 on a 0–1 scale)." This is the input_to inflation biting: TSMC's supplies-side HHI is 0.33 (equipment spread), but its input_to has only copper (single edge → HHI 1.00), and max wins the inbound axis. Semantically TSMC's chokepoint story is outbound (single foundry for the world), not inbound. **Flagging as a finding**, not a regression to fix here — the thin-graph TODO owns it, and adding real input edges for TSMC (silicon wafer feedstock, gases, chemicals, staff) is a data task, not a scoring task.


## 8. What's untouched (scope fence held)

- The severity formula, cascade, outbound criticality, rating: untouched.
- `narration.yaml`, `builder.py`, any narration code: untouched.
- Frontend: untouched.
- Thresholds (values): **not proposed, not applied**, per spec. Producing the corrected distribution was the deliverable; recalibration is a separate task against trustworthy numbers now that the seven-node zero-black-hole and copper's inflation are both gone.


## 9. Files changed

```
backend/app/scoring/engine.py      — stage set derived, not hardcoded
backend/app/scoring/config.py      — stages Optional; validate at load raises loudly
backend/app/schema/node.py         — stage_hhis: Optional[dict[str, float]]
config/scoring.yaml                — stages: null with explanatory comment
data/ai/edges.json                 — 4 new copper refines edges
data/ai/nodes.json                 — copper modeling_caveat rewritten
```
