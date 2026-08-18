# ε sweep — Pass M §4

**MEASUREMENT ONLY.** Sweep ε ∈ {0.001, 0.005, 0.01, 0.02, 0.05, 0.10}
under `nor_eps + min_supp=1` (the D4+D4a pairing K.2.2 recommended).
Both current graph and projected (K.2.2 §2 dep-value overrides).

Every value produced by
`backend/scripts/aggregator_validation.py::epsilon_sweep()`. Raw data
in `docs/generated/aggregator_validation_data.json`.

## §4.1 Current graph sweep

| ε | tier histogram | separating gaps | at 1.0 | ≥ 0.99 |
|---:|---|---:|---:|---:|
| **0.001** | 2c / 3h / 17m / 9n / 41u | 3 | 0 | 6 |
| **0.005** | 2c / 3h / 17m / 9n / 41u | 3 | 0 | 6 |
| **0.010** | 2c / 3h / 17m / 9n / 41u | 3 | 0 | 6 |
| **0.020** | 2c / 3h / 17m / 9n / 41u | 2 | 0 | 1 |
| **0.050** | 2c / 3h / 17m / 9n / 41u | 3 | 0 | 1 |
| **0.100** | 2c / 3h / 17m / 9n / 41u | 1 | 0 | 1 |

## §4.2 Projected graph sweep

| ε | tier histogram | separating gaps | at 1.0 | ≥ 0.99 |
|---:|---|---:|---:|---:|
| **0.001** | 2c / 3h / 18m / 8n / 41u | 2 | 0 | 6 |
| **0.005** | 2c / 3h / 18m / 8n / 41u | 2 | 0 | 6 |
| **0.010** | 2c / 3h / 18m / 8n / 41u | 2 | 0 | 6 |
| **0.020** | 2c / 3h / 18m / 8n / 41u | 2 | 0 | 1 |
| **0.050** | 2c / 3h / 18m / 8n / 41u | 3 | 0 | 1 |
| **0.100** | 2c / 3h / 18m / 8n / 41u | 1 | 0 | 1 |

## §4.3 Plateau analysis

**A plateau exists in the tier histogram.**

- Current: **2c / 3h / 17m / 9n / 41u** — identical across every ε
  from 0.001 to 0.100 (100× range).
- Projected: **2c / 3h / 18m / 8n / 41u** — identical across the same
  range.

Under the "plateau" definition in the K.2.2 spec (a range over which
the tier histogram is stable), the plateau **spans the entire tested
range** on both graphs. Any ε in [0.001, 0.100] produces the same
tier assignments.

**A value chosen from anywhere in this range is defensible on tier-
assignment grounds.** ε=0.01 sits comfortably in the middle; ε=0.05
also stable; ε=0.001 stable at the low end.

### §4.3.1 Where ε does affect the graph

Not the tier histogram, but two secondary quantities move:

1. **Nodes at ≥ 0.99 inbound**: drops from 6 to 1 as ε increases from
   0.010 to 0.020. This is the "cushion" ε buys — larger ε moves
   nodes farther from the 1.0 ceiling.
2. **Separating gap count**: fluctuates 1–3 across ε values without a
   clean monotonic trend. The variation is inside the derivation's
   noise floor and does not affect tier assignments because the
   number of boundaries selected is still 3 in every case.

**Neither secondary quantity changes tier assignments** — the plateau
is real.

### §4.3.2 Ordering changes across ε

Nodes' rank order across ε ∈ {0.001, 0.005, 0.01, 0.02, 0.05, 0.10}
on the current graph:

**7 pair-order swaps observed:**

| pair | note |
|---|---|
| `mineral:dysprosium` ↔ `company:asml` | #1/#2 swap — ASML has concentration=1.0 under noisy-OR, dysprosium 0.99; ε affects which reads higher |
| `mineral:gallium` ↔ `company:tsmc` | mid-top swap |
| `company:nvidia` ↔ `product:ndfeb_magnets` | rank 6/7 swap |
| `product:arm_core_ip` ↔ `product:cowos_packaging` | mid swap |
| `product:arm_core_ip` ↔ `product:hbm` | mid swap |
| `company:samsung` ↔ `company:lam_research` | mid swap |
| `company:arm` ↔ `company:applied_materials` | lower-mid swap |

**Projected graph: 8 pair-order swaps** (similar shape, arm_core_ip and
samsung swap with a couple additional neighbours).

**Consequence.** The tier plateau is real, but *within* a tier ε can
change which of two nodes is ranked higher. Downstream ranking
consumers (heaviest-path breadcrumb, glance-strip "top affected")
would show different orderings under different ε values within the
same tier.

Whether that matters depends on how the ranked output is used:

- **Tier chip** (single tier label): plateau protects it; ε choice
  invisible.
- **Sorted top-N under a tier**: sensitive to ε within the top-5 to
  top-10 band; the #1 slot itself swaps between ASML and dysprosium
  as ε moves.

### §4.3.3 The value that would need to be chosen

Under §4(4), if ε is adopted it needs the same treatment as
`fixed_reference`: **frozen literal + comment stating why the value
was chosen + guard test**. This diagnosis pass does NOT recommend or
freeze; recording the requirement so the fix pass author has it:

- Any value in [0.001, 0.10] gives the same tier plateau on both
  graphs.
- `at ≥ 0.99` count drops from 6 to 1 as ε passes 0.010 → 0.020. If
  the choice criterion is "no near-saturated nodes above 0.99", ε ≥
  0.020 delivers it. If the criterion is "smallest cushion that
  still avoids exact saturation", ε = 0.001 works.
- Ordering changes exist across the range. A value chosen with intent
  to preserve a specific ordering (e.g. ASML at #1) is a tuned
  constant; a value chosen with intent to sit in the tier-plateau
  middle is not.

**Not a recommendation. Recording the trade space.**

## §6 pre-registration scorecard for §4

| # | pre-registration | HIT / MISS |
|---|---|---|
| 3 | An ε plateau exists on the current graph | **HIT** — tier histogram identical across ε ∈ [0.001, 0.100] on both current and projected graphs |
