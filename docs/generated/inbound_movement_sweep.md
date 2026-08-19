# Pass N.1 §2 — inbound_hhi movement sweep, pre-N vs post-Phase-A

**DIAGNOSIS ONLY.** All values recovered from committed
`severity_snapshot.json` files via
`git show <sha>:docs/generated/severity_snapshot.json`. No engine
computation redone from data; every number below is a committed
value at a specific pass.

## §2.1 Why this needs a mechanism

Pass N's Phase A section attributed `ge_vernova` and `siemens_energy`
downward movement to "noisy-OR reads its inbound differently." That
restates the movement without naming the cause.

Under the aggregator change, the **expected** direction is upward:
for a multi-member bucket, noisy-OR reads higher than normalize=true
HHI (that is the copper +0.29 result). A node's inbound falling
under the switch is the opposite of expected and needs a named cause.

## §2.3 Full sweep — inbound_hhi movement for every scored node

Reproduced from `pass_l` snapshot (commit `28bac2d`) vs `pass_n_d4`
snapshot (commit `e85c58f`). 31 scored nodes total.

| node | pre-N HHI | post-A NOR | Δ | direction |
|---|---:|---:|---:|:---:|
| company:ge_vernova | 0.6543 | 0.4150 | **−0.2393** | ↓ |
| company:siemens_energy | 0.6800 | 0.4600 | **−0.2200** | ↓ |
| company:applied_materials | 0.0000 | 0.0000 | +0.0000 | — |
| company:asml | 0.0000 | 0.0000 | +0.0000 | — |
| company:cadence | 0.0000 | 0.0000 | +0.0000 | — |
| company:canon | 0.0000 | 0.0000 | +0.0000 | — |
| company:hitachi_high_tech | 0.0000 | 0.0000 | +0.0000 | — |
| company:kla | 0.0000 | 0.0000 | +0.0000 | — |
| company:lam_research | 0.0000 | 0.0000 | +0.0000 | — |
| company:nikon | 0.0000 | 0.0000 | +0.0000 | — |
| company:quanta_services | 0.0000 | 0.0000 | +0.0000 | — |
| company:siemens_eda | 0.0000 | 0.0000 | +0.0000 | — |
| company:synopsys | 0.0000 | 0.0000 | +0.0000 | — |
| company:tokyo_electron | 0.0000 | 0.0000 | +0.0000 | — |
| product:arm_core_ip | 0.0000 | 0.0000 | +0.0000 | — |
| product:rf_power_semis | 0.0000 | 0.0000 | +0.0000 | — |
| company:nvidia | 0.9802 | 0.9901 | +0.0099 | ↑ |
| company:tsmc | 0.9801 | 0.9901 | +0.0099 | ↑ |
| mineral:gallium | 0.9704 | 0.9852 | +0.0149 | ↑ |
| mineral:dysprosium | 0.9610 | 0.9902 | +0.0292 | ↑ |
| company:vertiv | 0.4233 | 0.4526 | +0.0293 | ↑ |
| company:samsung | 0.9218 | 0.9520 | +0.0301 | ↑ |
| product:cowos_packaging | 0.9050 | 0.9525 | +0.0475 | ↑ |
| company:micron | 0.7636 | 0.8690 | +0.1054 | ↑ |
| company:sk_hynix | 0.7636 | 0.8690 | +0.1054 | ↑ |
| mineral:neodymium | 0.6860 | 0.9190 | +0.2330 | ↑ |
| company:arm | 0.3923 | 0.6410 | +0.2487 | ↑ |
| mineral:indium | 0.4381 | 0.7108 | +0.2727 | ↑ |
| product:hbm | 0.4402 | 0.7440 | +0.3038 | ↑ |
| mineral:copper | 0.2916 | 0.6999 | +0.4083 | ↑ |
| product:ndfeb_magnets | 0.5014 | 1.0000 | +0.4986 | ↑ |

**Summary: 2 fell, 15 rose, 14 unchanged (all at 0.0 → 0.0 — stage-
zeroed under min_supp=2).**

## §2.2 Hypothesis test — thin-bucket incompleteness

Pass N.1 §2.2 hypothesised: `normalize: true` divides shares by their
sum before squaring, which discards incompleteness — a bucket
summing to 0.15 reads as if it summed to 1.0. Noisy-OR reads raw
magnitudes without renormalization. Under the switch, thin buckets
that read artificially high under HHI now read honestly low.

### §2.2.1 Test on the two falling nodes

Both fallers are power-layer input consumers with **incomplete
modelled input buckets**:

**`company:ge_vernova` input_to bucket:**

| member | share |
|---|---:|
| mineral:copper | 0.350 |
| product:rf_power_semis | 0.100 |
| **sum** | **0.450** (incomplete — no steel, no rare-earth magnets, no glass fibre) |

Aggregations:
- **HHI (normalize=true)**: shares renormalized (0.778, 0.222) → HHI = 0.605 + 0.049 = **0.654**
- HHI (normalize=false): raw sum of squared = 0.350² + 0.100² = **0.1325**
- **Noisy-OR**: 1 − (1 − 0.350)(1 − 0.100) = 1 − (0.65)(0.90) = **0.415**

`normalize=true` reads 0.654 by pretending the bucket sums to 1.0.
Noisy-OR reads 0.415, honestly reflecting a partial-coverage bucket.
`normalize=false` would have read 0.133, dampening the incompleteness
even more aggressively.

Post-Pass-A ge_vernova inbound reads 0.4150 exactly — matches the
noisy-OR calculation on this bucket. **Mechanism confirmed.**

**`company:siemens_energy` input_to bucket:**

| member | share |
|---|---:|
| mineral:copper | 0.400 |
| product:rf_power_semis | 0.100 |
| **sum** | **0.500** (same shape as ge_vernova) |

- HHI (normalize=true): (0.80, 0.20) → **0.680**
- Noisy-OR: 1 − (0.60)(0.90) = **0.460**

Post-Pass-A siemens_energy inbound reads 0.4600 — matches noisy-OR
exactly. **Same mechanism.**

### §2.2.2 Test does not fire elsewhere

Every other scored node either has a well-modelled bucket (sum ≥ 0.80)
or is stage-zeroed to 0.0 on both sides. Only ge_vernova and
siemens_energy have both an incomplete-but-non-zero input_to bucket
AND multiple members in that bucket.

**Consequence: 100% of the falling nodes are explained by the
thin-bucket mechanism.** Pre-registration §7(3) HIT.

## §2.4 Power-layer check

Both fallers are in the power layer (ge_vernova = turbines & wind
equipment; siemens_energy = power generation equipment). Both have
input_to buckets with copper + rf_power_semis as their only two
modelled inputs.

**No non-power node fell**, and no power-layer node with a well-
modelled input bucket fell either. The 2-of-2 correspondence is not
coincidence: **the power layer's input_to buckets are systematically
thin** because heavy-equipment BOM has many uncommonly-modelled
inputs (steel, structural composites, precision castings, control
electronics, coolant systems). Under HHI's normalize=true the
incompleteness was hidden; under noisy-OR it surfaces as a lower
inbound reading.

**This is a structural finding, not a per-node curiosity.** The
power-layer nodes' pre-Pass-N inbound was inflated in proportion to
how incomplete their input model was. Correcting to honest magnitude
is defensible behaviour, but it is a side effect of the aggregator
choice that Pass N did not name in the ledger.

## §2.5 The unremarked semantic change

**Noisy-OR does what `normalize: false` was designed to do** —
dampening incomplete buckets in proportion to their shortfall — as a
side effect of the aggregator switch.

Per `config/scoring.yaml` comment (pre-N):

> When `normalize=False`, HHI is the sum of squared RAW shares. An
> incomplete bucket is dampened in exact proportion to its shortfall;
> no tuning parameter, no threshold. If the shares sum above 1.0
> (i.e. the edge-type semantics are not "target's input share"), HHI
> can exceed 1.0 — that value is left un-clamped so the semantic
> mismatch surfaces rather than being hidden.

Pass N adopted noisy-OR as the aggregator with the K.1 §4.1
dependency-semantics justification. It did not record that the same
switch simultaneously delivers what `normalize: false` was designed
to do for market-share semantics. **Two semantic changes shipped in
one commit; only one was named.**

This is not a defect — noisy-OR's incompleteness handling is a
strict improvement over normalize=true's discarding-of-incompleteness
— but it is a second-order change that a future audit could
mistake for an intended effect of the aggregator choice rather than
a side effect. The ledger fix is a §5(2) note; no code change.

## §7 pre-registration scorecard for §2

| # | pre-registration | HIT / MISS |
|---|---|---|
| 2 | At least one node besides `ge_vernova` shows a fall in `inbound_hhi` under Phase A. If ge_vernova is the only one, the movement is idiosyncratic. | **HIT** — `company:siemens_energy` also fell (Δ −0.2200). But note: **only 2 nodes fell total**, both in the power layer with the same bucket shape. Not a widespread pattern; a structural finding about how thin buckets read under HHI vs noisy-OR. |
| 3 | §2.2's thin-bucket mechanism explains the majority of falls. If it explains none, the hypothesis is wrong. | **HIT — 100% of falls** explained by the thin-bucket mechanism. ge_vernova bucket sum 0.45 (HHI 0.654 vs noisy-OR 0.415); siemens_energy bucket sum 0.50 (HHI 0.680 vs noisy-OR 0.460). Both fell by the difference. |
