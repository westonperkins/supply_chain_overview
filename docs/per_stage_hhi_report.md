---
title: "Per-stage HHI — final report"
subtitle: "AI Supply Chain Terminal"
date: "2026-07-21"
---

## 0. Diagnosis verified before any code

Gallium's actual derived shares:

```
mines:   China 0.985, Japan 0.010, South Korea 0.005   → HHI 0.970
refines: China 0.60,  Canada 0.15, Japan 0.10, USA 0.05 → HHI 0.488
blended (strongest-per-source):                        → HHI 0.604
```

Not a misdiagnosis. Mining edges are correct; the 0.60 blended reading was exactly the dilution artefact the spec describes.


## 1. Scope-fence honored

Touched exactly the four files in scope:

- `data/ai/nodes.json` — copper's `modeling_caveat` rewritten to reflect the new state.
- `backend/app/scoring/engine.py` — `per_stage_hhi()` + `combine_per_stage()`; `hhi_from_derived_shares()` kept and re-tagged as legacy → `combined_hhi`; `refresh_all_derived` now populates the three per-stage fields.
- `config/scoring.yaml` — `inbound.per_stage` block added; the copper per-stage TODO removed and replaced with the scale-axis note per spec.
- `backend/app/schema/node.py` — three new derived fields (`mined_by_hhi`, `refined_by_hhi`, `supplied_by_hhi`) plus `combined_hhi` kept for before/after.

**Untouched:** cascade, outbound criticality, rating, ratings config, all narration code and yaml, everything frontend, thresholds themselves (only proposal below).


## 2. Assertions

```
OK   mineral nodes have per-stage HHIs where edges exist
OK   no HHI outside [0, 1]
OK   gallium mined_by_hhi = 0.970  ≥ 0.85
OK   inbound_hhi == max(present per-stage) for every node
OK   all 63 nodes score and tier without exception
OK   all six five-alarm nodes remain critical
```


## 3. Five-alarm check

| Node       | new inbound_hhi | new severity | new tier |
|------------|-----------------:|--------------:|----------|
| TSMC       | 0.327            | 0.469         | critical |
| ASML       | 0.000            | 0.393         | critical |
| Dysprosium | 0.961            | 0.545         | critical |
| Gallium    | 0.970            | 0.480         | critical |
| HBM        | 0.440            | 0.234         | critical |
| CoWoS      | 0.905            | 0.313         | critical |

**All six remain critical.**


## 4. HBM / Siemens boundary

The 0.004 gap the previous calibration warned about has opened up dramatically — but not for the reason we hoped.

|                 | old sev  | new sev  |
|-----------------|---------:|---------:|
| HBM             | 0.2288   | 0.2344   |
| Siemens Energy  | 0.2244   | 0.0613   |
| **gap**         | **+0.0044** | **+0.1731** |

Siemens Energy's inbound edges are `input_to` from copper and RF & Power — **not** in the spec's `[mines, refines, supplies]` stages, so its inbound_hhi collapses to 0. HBM's `supplies` edges from SK Hynix / Micron / Samsung are covered, so it holds. The boundary widened by 0.17, but on Siemens' side, not HBM's.


## 5. Full before/after diff — ten tier changes

| Node              | old → new         | old sev → new sev | interpretation |
|-------------------|-------------------|--------------------|----------------|
| **Copper**        | high → **critical** | 0.216 → 0.710     | refined_by_hhi = 1.0 because only China is modelled as refiner. Data-driven honest reading; **thin-graph artefact**, updated caveat below. |
| Neodymium         | moderate → high   | 0.103 → 0.220     | refined_by_hhi 0.686 wins over combined 0.320. Correct: paper says China does ~90% of separation. |
| Broadcom          | none → moderate   | 0.035 → 0.106     | supplied_by_hhi 1.0 (single edge from TSMC 0.95). Single-source reading. |
| AMD               | none → moderate   | 0.036 → 0.106     | same pattern (TSMC 0.98). |
| GE Vernova        | **high → moderate** | 0.216 → 0.064   | inbound was 0.654 blended, now 0.000 — inputs are `input_to` from copper + RF/Power, not in spec's stages. |
| Siemens Energy    | **high → moderate** | 0.224 → 0.061   | same reason. |
| Vertiv            | moderate → none   | 0.064 → 0.043     | same reason. |
| NdFeB Magnets     | **high → none**   | 0.213 → 0.043     | inputs are `input_to` from Nd + Dy. Same. |
| RF & Power Semis  | **critical → none** | 0.319 → 0.028   | single `input_to` edge from gallium. Same. |
| Quanta Services   | moderate → none   | 0.106 → 0.014     | The thin-graph caveat now bites: single `input_to` edge from copper, not in stages. **Semantic win** — matches the caveat. |

**Two findings worth surfacing separately (see §7):**

- **Copper spiking to critical** is data-driven but flags the same under-modelling the copper caveat has always warned about.
- **RF/Power, NdFeB, GE Vernova, Siemens Energy, Vertiv, Quanta all drop** because the spec's stage list `[mines, refines, supplies]` doesn't include `input_to` or `component_of`. Their inbound is only visible under those omitted edge types.


## 6. Copper `modeling_caveat` — updated per spec

Rewrote to:

> Per-stage HHI split is now done. Mining reads diversified (mined_by_hhi ~0.25 across Chile, DRC, Peru, China, US); refining reads as a monopoly (refined_by_hhi 1.0) because China is the only refiner modelled — an under-modelling artefact, not the paper's ~47% figure. Copper's real paper story is volume plus a 17–25 year mine lead time, i.e. a scale/demand constraint the model has no axis for; concentration is absorbing risk it cannot represent.

`scoring.yaml` — dropped the "per-stage HHI TODO" block, kept the thin-graph artefacts TODO, added the scale-axis NOTE per spec.


## 7. Two findings surfaced (not fixed — flagging per spec spirit)

**Finding A — `input_to` and `component_of` are not stages.** The spec's `stages: [mines, refines, supplies]` deliberately excludes the two edge types that carry mineral → product and product → product supply. Every product whose inputs are only `input_to` edges (RF & Power, NdFeB) and every downstream company whose inputs are only `input_to` edges (Vertiv, Siemens Energy, GE Vernova, Quanta) now has inbound_hhi = 0.

Some of these drops are semantic wins (Quanta — the thin-graph caveat was warning about exactly this false criticality); some are semantic losses (RF & Power was legitimately single-sourced from gallium, and losing that is real information). **Not fixing** — the spec is prescriptive about the three stages. Flagging for the next scoping call.

**Finding B — Copper at critical.** Exactly the honest result the spec predicted. The refining edges are under-modelled (only China at 0.47), so per-stage reads refining as a monopoly. Copper's real paper story is scale/demand across a 17–25 yr mine lead time. Reflected in the updated caveat and the new scale-axis NOTE in scoring.yaml.


## 8. Threshold proposal (NOT applied)

Current thresholds (`critical=0.225, high=0.13, moderate=0.05`) still satisfy the five-alarm requirement, so **no change is strictly required**. But the distribution shape has moved and there's a natural boundary decision worth surfacing.

New sorted severities (top 15):

```
0.710  Copper
0.545  Dysprosium
0.480  Gallium
0.469  TSMC
0.393  ASML
0.313  CoWoS
0.234  HBM
———— (0.014 gap)
0.220  Neodymium
———— (0.114 gap  ← the widest natural break)
0.106  Broadcom
0.106  AMD
0.104  NVIDIA
0.098  Micron
0.094  Applied Materials
0.091  SK Hynix
```

**Two coherent options. I don't recommend one over the other — both are defensible.**

**Option A (keep current, most conservative):** `0.225 / 0.13 / 0.05`

- Critical: 7 (paper 5-alarm + HBM + Copper)
- High: 1 (Neodymium at 0.220)
- Moderate: ~9
- Reasoning: thresholds still work, distribution shifted but the paper 5-alarm still lands. Minimal disruption.

**Option B (align to the natural 0.114 gap):** `0.22 / 0.10 / 0.05`

- Critical: 8 (adds Neodymium — arguably belongs there given refined_by_hhi 0.686)
- High: 3 (Broadcom, AMD, NVIDIA — the chip-designer band that just crossed the natural break)
- Moderate: ~10
- Reasoning: the widest natural gap in the distribution is between Neodymium and Broadcom (0.114). Setting critical there gives the tier its cleanest semantic meaning.

Not committing either. Waiting for your call.


## 9. Narration re-run — the six required nodes

```
Gallium · semiconductor input · CRITICAL   [dominant_axis=inbound]
  Why it scores critical.
    One source controls almost all supply (0.97 on a 0–1 scale),
    substitutes are marginal, and replacing it would take roughly
    five to ten years.

Dysprosium · magnet input · CRITICAL   [dominant_axis=inbound]
  Why it scores critical.
    One source controls almost all supply (0.96 on a 0–1 scale),
    substitutes are marginal, and replacing it would take roughly
    five to ten years.

TSMC  · foundry           · CRITICAL   [dominant_axis=outbound]  (unchanged)
ASML  · semi equipment    · CRITICAL   [dominant_axis=outbound]  (unchanged)
HBM   · memory product    · CRITICAL   [dominant_axis=outbound]  (unchanged)
CoWoS · packaging product · CRITICAL   [dominant_axis=inbound]   (unchanged)
```

**Gallium now reads "one source controls almost all supply (0.97)"** — the primary correctness target of this task. Dysprosium jumped the same way (0.60 → 0.96), also correct. The four already-correctly-scored critical nodes are unchanged in their narrations because the axis wasn't misdiagnosed on them.
