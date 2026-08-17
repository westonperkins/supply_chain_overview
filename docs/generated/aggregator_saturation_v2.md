# Aggregator saturation — alternatives without capping the author (Pass K.2.2 §3)

**DIAGNOSIS ONLY.** No aggregator changed. This document rejects K.2.1's
B1 recommendation and evaluates aggregator-side alternatives.

## §3.1 Reject B1

K.2.1 D4 recommended capping authored `input_share` at 0.95 to prevent
noisy-OR saturation. **B1 is rejected here** for two reasons the K.2.1
report did not surface:

1. **It bends input data to fit the model.** The standing project rule
   is the opposite: when data and a model constraint conflict, fix the
   model's resolution and report the conflict. B1 fixes the data by
   convention because the aggregator cannot handle it.
2. **It carries the same tuning-toward-target risk K.2.1 used to reject
   B2.** K.2.1 rejected the evidentiary-bar mitigation (B2) on the
   stated grounds that authors would judge which inputs are "truly
   binary." B1 has the mirror problem: an author who knows 1.00 is
   disallowed authors against the constraint rather than against the
   evidence. If a dependency is genuinely binary, 1.00 IS the honest
   value; 0.95 is falsification of an axiom.

**Saturation is a property of the noisy-OR aggregator, not of the
authored data. It belongs to the aggregator.** §3.2 evaluates four
aggregator-side alternatives.

## §3.2 Aggregator-side alternatives — the actual comparison

Test setup: for each of the 20 scored nodes with modelled inbound
supply-flow edges (11 leaf nodes omitted — no inbound), compute each
aggregator's concentration reading. All values clamped to [0,1] on
input. Then estimate severity as `max(inbound_aggregate,
current_outbound) × (1 − sub) × lt_norm` and count separating gaps.

### §3.2.1 Concentration readings per candidate

| node | current HHI | plain NOR | NOR ε=0.01 | NOR ε=0.05 | bounded RMS | n_binary |
|---|---:|---:|---:|---:|---:|---:|
| mineral:gallium | 0.9704 | 0.9957 | 0.9957 | 0.9857 | 0.4416 | 1 |
| mineral:indium | 0.4381 | 0.8761 | 0.8761 | 0.8761 | 0.2601 | 0 |
| mineral:neodymium | 0.6860 | 0.9823 | 0.9823 | 0.9823 | 0.3538 | 1 |
| mineral:dysprosium | 0.9610 | 0.9978 | 0.9978 | 0.9889 | 0.5523 | 1 |
| mineral:copper | 0.2916 | 0.8526 | 0.8526 | 0.8526 | 0.1992 | 0 |
| product:hbm | 0.4402 | 0.7440 | 0.7440 | 0.7440 | 0.3831 | 0 |
| product:cowos_packaging | 0.9050 | 0.9525 | 0.9525 | 0.9525 | 0.6727 | 1 |
| **product:ndfeb_magnets** | 0.5014 | **1.0000** | 0.9990 | 0.9950 | 0.9513 | 2 |
| product:rf_power_semis | 0.0000 | 0.9000 | 0.9000 | 0.9000 | 0.9000 | 1 |
| company:nvidia | 0.9802 | 0.9996 | 0.9996 | 0.9979 | 0.4122 | 1 |
| company:tsmc | 0.9801 | **1.0000** | 1.0000 | 0.9999 | 0.4416 | 2 |
| company:samsung | 0.9218 | 0.9998 | 0.9998 | 0.9998 | 0.4120 | 1 |
| company:sk_hynix | 0.7636 | 0.9970 | 0.9970 | 0.9970 | 0.4136 | 0 |
| company:micron | 0.7636 | 0.9801 | 0.9801 | 0.9801 | 0.4143 | 0 |
| company:siemens_energy | 0.6800 | 0.4600 | 0.4600 | 0.4600 | 0.2915 | 0 |
| company:ge_vernova | 0.6543 | 0.4150 | 0.4150 | 0.4150 | 0.2574 | 0 |
| company:quanta_services | 0.0000 | 0.3000 | 0.3000 | 0.3000 | 0.3000 | 0 |
| company:vertiv | 0.4233 | 0.4526 | 0.4526 | 0.4526 | 0.1991 | 0 |
| company:arm | 0.3923 | 0.9998 | 0.9998 | 0.9991 | 0.6572 | 2 |
| **product:arm_core_ip** | 0.0000 | **1.0000** | 0.9900 | 0.9500 | 1.0000 | 1 |

### §3.2.2 Candidate evaluation

**Candidate 1 — Noisy-OR with internal ε.** Aggregator treats each
input as `min(1 − ε, share)` when combining, so `share = 1.00` cannot
force a saturated output. Authoring stays honest.

- NdFeB reading: ε=0.01 gives **0.9990** (was 1.0000 plain); ε=0.05 gives
  0.9950. Both distinct from a single 0.9500 input.
- **Saturation count today: 0** at ε=0.01 (down from 2 at plain
  noisy-OR). No node reaches exactly 1.0.
- **Ordering preserved.** Ranking among near-1.0 nodes preserved (ndfeb
  < tsmc for one-input-at-1.0-plus-something ordering).
- **Separating gaps: 6** at ε=0.01 (same as plain noisy-OR). ε=0.05
  drops to 5 — the epsilon is a knob that trades off "how much room to
  distinguish saturated nodes" against "resolution loss on non-saturated
  nodes."
- Coexists with per-stage/per-category: yes, ε is a scalar applied
  identically to any noisy-OR aggregation.

**Verdict: strong candidate. ε=0.01 preserves all noisy-OR properties
except exact saturation and adds one config parameter.**

**Candidate 2 — Weighted / count-aware noisy-OR.** Aggregator emits a
scalar plus an auxiliary "binary-member count" (share ≥ threshold, e.g.
0.90). Same scalar as noisy-OR ε; the additional signal is the count.

- NdFeB reading: (0.9990, **2 binary members**).
- Combined with epsilon (Candidate 1), preserves numeric saturation
  handling AND adds discrimination for nodes that reach the same near-
  saturated scalar but have different numbers of binary dependencies.
- Downstream integration cost: every consumer of concentration must
  read both the scalar and the count. Ranking via lexicographic
  `(scalar, count)` preserves discrimination among near-saturated
  nodes.
- Distinguishes `product:ndfeb_magnets` (0.999, 2 binary) from
  `product:arm_core_ip` (0.99, 1 binary) — where plain noisy-OR ε
  reads them at the same scalar.
- Coexists with per-stage / per-category: the count aggregates by
  taking `sum` across per-stage or per-category buckets, or `max`
  across (both preserve the "how many members are binary" reading).

**Verdict: strong candidate. Fully additive to Candidate 1. Cost is
downstream integration (frontend, cascade, tests).**

**Candidate 3 — Two-part concentration.** A generalisation of
Candidate 2: aggregator emits `(scalar, structural-signals-tuple)`
where the tuple carries whatever the scalar cannot represent
(saturation flag, member count, "critical-with-no-substitute" flag).
Downstream ordering uses whatever key the application needs.

- More flexible than Candidate 2 but larger surface. K.2 §1.3
  enumerated 8 surfaces that a new tier state touches; a
  two-part concentration touches every read of the concentration axis
  (severity formula, cascade seed, narration, tests).
- **Only justified if the graph will reliably need > 1 orthogonal
  signal downstream.** For NdFeB the scalar-plus-count suffices; for
  future cases (multiple-single-source stacking) it may not.

**Verdict: keep on the shelf. Prefer Candidate 2 unless a second use
case for the tuple emerges before D4 lands.**

**Candidate 4 — Bounded RMS (root-mean-square of shares).** Aggregator:
`concentration = sqrt(mean(share_i²))`. Stays [0,1] since each share
≤ 1; monotonic in each share; no summation constraint.

- NdFeB reading: **0.9513** (sqrt of (1.00² + 0.90²)/2 = sqrt(0.905)).
- **Saturation cannot occur** unless every share = 1.0 (all-binary all-
  members).
- **But**: RMS dilutes signal for concentration. `mineral:gallium`
  reads 0.4416 (down from HHI 0.9704) — the 98.5% China dominance is
  averaged with the 1% Japan share. This is opposite the effect
  concentration is meant to capture.
- Median under RMS: 0.1092 (was 0.1949 under HHI); separating gaps: 5.
  The distribution compresses toward the middle — same shape as
  normalize=true's inversion problem, expressed differently.

**Verdict: rejected. Solves saturation by giving up the axis's core
function.**

### §3.2.3 Ordering property comparison

Test: does each aggregator preserve monotonicity as an author raises
a single input's share?

| aggregator | monotonic per input | monotonic across nodes | in [0,1] |
|---|:---:|:---:|:---:|
| current HHI (normalize=true) | **NO** (inversion) | — | yes |
| plain noisy-OR | yes | yes (until saturation) | yes |
| noisy-OR ε=0.01 | yes | yes (asymptotic to 1−0 as inputs stack) | yes |
| count-aware noisy-OR | yes on scalar; count is stepwise | full ordering via (scalar, count) | yes |
| bounded RMS | yes | yes but heavily dilutive | yes |

**Only current HHI fails per-input monotonicity** — that is the K.2.1
diagnosis. All four candidates fix it.

## §3.3 Migrated-boundary problem — top-of-distribution guard

K.2.1 §3.2.3 established that noisy-OR moves resolution loss from the
bottom (K.2 §1's `moderate = 0.0`) to the top: 9 of 20 non-leaf scored
nodes at ≥ 0.99 today, 15–20 of 20 after queued-29. Diagnosis A's
retry addresses only the bottom.

Per §3.2.1 saturation-count results:

| aggregator | nodes at ≥ 0.99 today | needs top-guard? |
|---|---:|---|
| plain noisy-OR | 9 | **yes** |
| noisy-OR ε=0.01 | 8 (0 exact 1.0) | yes (compression persists just off saturation) |
| noisy-OR ε=0.05 | 4 | probably not; ε trades resolution for cushion |
| count-aware noisy-OR | 8 scalar, but count breaks ties | **no** (count discriminates) |
| bounded RMS | 1 (arm_core_ip 1.0000 by construction) | no; but §3.2.2 rejected on other grounds |

**Count-aware noisy-OR (Candidate 2) is the only shortlisted option
that avoids needing a top-of-distribution guard.** The count preserves
ordering among near-saturated nodes without requiring the boundary
selection to arbitrate them.

For plain noisy-OR or noisy-OR ε, a top-of-distribution guard would
be needed. **Would that be a second instance of the veto-without-retry
defect K.2 §1 found in F1.b?** Depends on how it is designed:

- Rejecting `critical/high` when both fall in a compressed band and
  hard-setting `critical = 1.0` (analogue of K.2's `moderate = 0.0`
  at the bottom) → **yes, same defect shape.**
- Advancing to a lower-midpoint candidate on rejection → retry pattern,
  not the same defect.

**This diagnosis does not design the guard.** It establishes that:

1. Noisy-OR and noisy-OR-ε need one.
2. Count-aware noisy-OR does not.
3. If a guard is designed, retry-not-veto is the shape.

## §3.4 Recommendation update to D4

**Aggregator: count-aware noisy-OR with ε=0.01** (Candidate 1 +
Candidate 2 combined). The two are additive:

- ε=0.01 handles the saturation without capping authored values.
- Count-aware (share ≥ 0.90 threshold) preserves ordering among
  near-saturated nodes.
- Combined, no top-of-distribution guard needed.

Cost: **the count is a downstream integration item** — cascade, severity
formula, and reporting need to accept a two-value concentration reading.
K.2 §1.3's tier-withhold blast-radius enumeration applies here in a
smaller form: any consumer of `inbound_hhi` needs a shim to read
`(scalar, count)`. Enumerate in the fix pass.

**Rejected: B1 (author-side cap).** Bends data to fit model.

**Rejected: bounded RMS.** Fixes saturation by giving up the axis's
core signal.

**Deferred: two-part general (Candidate 3).** Keep on shelf; Candidate 2
suffices for the concrete cases §2 identified.

## §3.5 §7 pre-registration scorecard for §3

| # | pre-registration | HIT / MISS |
|---|---|---|
| 4 | At least one §3.2 aggregator alternative avoids saturation without capping authored values | **HIT** — noisy-OR with internal ε (Candidate 1) at ε=0.01 has 0 saturating nodes today; count-aware noisy-OR (Candidate 2) preserves ordering without capping |
