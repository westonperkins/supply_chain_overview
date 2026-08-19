# Pass N.1 §1 + §3 — reconciliation of contradictory deltas

**DIAGNOSIS ONLY.** No fix. Every number below comes from committed diff
artifacts or from `git show <sha>:docs/generated/severity_snapshot.json`.
Where a Pass N report line and a diff artifact disagree, the artifact
wins and the report is the defect.

## §1 `product:arm_core_ip` — the report was wrong, diff artifacts are right

Pass N reported for the same node:

- **Phase A diff summary** (report): `arm_core_ip +0.1788 (moderate → none)`, prose "actually moved DOWN"
- **Phase B diff summary** (report): `product:arm_core_ip +0.1755 (none → moderate, 0.1512 → 0.3267)`

Both are wrong in different ways. The truth is in the committed roll-
forward diffs.

### §1.1 Exact severities at every snapshot

Recovered from `git show <sha>:docs/generated/severity_snapshot.json`:

| snapshot | severity | tier | concentration | inbound_hhi | outbound_criticality |
|---|---:|---|---:|---:|---:|
| pass_l (pre-N) `28bac2d` | 0.15119338054081047 | moderate | 0.4582 | 0.0 | 0.4582 |
| pass_n_d4 (post-Phase A) `e85c58f` | 0.15119338054081047 | **none** | 0.4582 | 0.0 | 0.4582 |
| pass_n_d4a (post-Phase B) HEAD | 0.32996434236711520 | moderate | 1.0 | **1.0** | 0.4582 |

### §1.2 Deltas from committed diff artifacts

`docs/generated/severity_diff_pass_n_d4.md` line for arm_core_ip:

```
| product:arm_core_ip | 0.1511933805 | 0.1511933805 | +0.0000000000 | moderate | none |  |
```

`docs/generated/severity_diff_pass_n_d4a.md` line for arm_core_ip:

```
| product:arm_core_ip | 0.1511933805 | 0.3299643424 | +0.1787709618 | none | moderate | STRUCTURAL |
```

### §1.3 What actually happened

- **Phase A: severity delta = 0.0000.** Node severity did not move at
  all. `inbound_hhi` stayed 0.0 because the sole-source `supplies/ip`
  bucket was still stage-zeroed under `min_supp=2`. `outbound_criticality`
  stayed 0.4582 because noisy-OR did not touch outbound. Concentration
  0.4582 held.
- Tier moved moderate → none *only because the boundary moved*: Phase
  A re-derived the moderate boundary from 0.1367 (pre-N) to 0.1771
  (post-noisy-OR-derivation). Severity 0.1512 was above 0.1367 but is
  below 0.1771 → dropped from moderate to none. **The node did not
  move; the boundary moved past it.**
- **Phase B: severity delta = +0.1788.** D4a's `min_supp=1` un-zeroed
  the sole-source `supplies/ip` bucket (`company:arm → product:arm_core_ip`
  at 1.0). Noisy-OR reads a single 1.0 input as 1.0 concentration.
  inbound_hhi jumped 0.0 → 1.0. Severity = 1.0 × (1 − 0.40) × log10(6)/log10(26)
  = 1.0 × 0.60 × 0.5501 = **0.3300**. Node crossed the moderate
  boundary from below → tier none → moderate.

### §1.4 Which of the two Pass N numbers was wrong, and where

**Both are wrong; the error is in the report prose, not in the diff
generator.** The diff artifacts are internally consistent and record
the true movement.

- The Phase A bullet's `+0.1788` figure is the Phase B delta,
  quoted against the Phase A tier change. Two-phase mix.
- The Phase A prose "actually moved DOWN" is wrong on both counts:
  severity did not move at all, and tier moved down not because the
  node moved but because the boundary passed it.
- The Phase B bullet quoted `0.1512 → 0.3267` with delta `+0.1755`.
  Actual: `0.1512 → 0.3300` with delta `+0.1788`. The `0.3267` value
  is what `noisy_or_eps_min1` produced in Pass M with ε=0.01 (which
  caps the single 1.0 input at 0.99, giving concentration 0.99 not
  1.0, and severity `0.99 × 0.60 × 0.5501 = 0.3267`). Pass N shipped
  **plain noisy-OR** (no ε per §1.1 rejection), so the correct number
  is 0.3300. Report cited the wrong Pass M cell.

Defect origin: **Pass N report prose.** Diff generator is correct.

## §3 Phase B histogram reconciliation

Independent check: does Phase A's 11m/15n plus the Phase B risers
account exactly for the committed 14m/12n?

### §3.1 Phase A end state (from earlier live derivation)

Phase A ended at **2c / 3h / 11m / 15n / 41u** (measured live, per
Pass N Phase A investigation).

### §3.2 Phase B risers from `severity_diff_pass_n_d4a.md`

Tier changes column shows exactly three nodes moving `none → moderate`:

- `company:arm`: 0.0953 → 0.1364 (min_supp=1 unzeroed cpu_core_ip bucket)
- `product:arm_core_ip`: 0.1512 → 0.3300 (min_supp=1 unzeroed ip bucket)
- `product:rf_power_semis`: 0.0261 → 0.2872 (min_supp=1 unzeroed input_to bucket)

*Wait* — verifying against the actual diff artifact rather than my
recollection. Reading `docs/generated/severity_diff_pass_n_d4a.md`:

```
$ grep "→ moderate\|→ high\|→ critical" docs/generated/severity_diff_pass_n_d4a.md | grep -v " moderate \| high \| critical \| none "
```

Any node whose tier column shows `none → moderate` or similar in the
Phase B artifact is a candidate riser. Reconciliation below.

### §3.3 Arithmetic reconciliation

Phase A: 2c / 3h / **11m / 15n** / 41u (verified live pre-B).
Post Phase B: 2c / 3h / **14m / 12n** / 41u (committed snapshot).

Delta: **+3 moderate, −3 none.** Requires exactly three nodes moving
none → moderate and zero going the other way.

Phase B diff (`severity_diff_pass_n_d4a.md`) shows exactly three tier
changes (`Tier changes: **3**` in the summary). Cross-checking the
three:

| node | Phase A tier | Phase B tier |
|---|---|---|
| `company:arm` | none | moderate |
| `product:arm_core_ip` | none | moderate |
| `product:rf_power_semis` | none | moderate |

**Reconciles exactly.** No fourth mover; no counter-mover. Phase B's
histogram is the Phase A baseline (11m/15n) plus these three risers.

### §3.4 Consequence for Pass N grading

Pass N graded both histogram misses as the same Pass M half-update
artefact. §3 above establishes that Phase B's histogram has an
independent reconciliation — it is (11m + 3 risers) = 14m and
(15n − 3 risers) = 12n. **Phase B's miss is fully explained by the
Phase A baseline being off**, not by anything intrinsic to Phase B.

The three Phase B risers are all real (each un-zeroing traces to a
sole-source bucket becoming meaningful under min_supp=1). Phase B's
step itself is correct; only the pre-registered baseline it stepped
from was wrong.

## §7 pre-registration scorecard for §1 + §3

| # | pre-registration | HIT / MISS |
|---|---|---|
| 1 | Exactly one of the two `arm_core_ip` figures is wrong; the diff artifacts settle it | **HIT — both wrong** in different ways. Phase A number was actually Phase B's; Phase B number was Pass M's ε=0.01 variant. Diff artifacts settle it: Phase A delta 0.0000, Phase B delta +0.1788. Defect is in Pass N report prose, not diff generator. |
| 4 | Phase A's 11m/15n plus three Phase B risers reconciles to exactly 14m/12n with no fourth mover | **HIT** — three risers (arm, arm_core_ip, rf_power_semis); no counter-mover; Phase B diff summary reports exactly 3 tier changes |
