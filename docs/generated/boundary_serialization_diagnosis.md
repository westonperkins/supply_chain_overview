# Boundary serialization + chokepoint regression — diagnosis (Pass K.2 §3, §4)

**DIAGNOSIS ONLY.** No code changed. §5 D5 records the process decision this
feeds; §6 records the paper-vs-model reframe on the ledger.

## §3.1 `unresolved_bands` never reaches config — VERIFIED

`derive_thresholds` constructs `UnresolvedBand` objects correctly on both
branches (`backend/app/scoring/thresholds.py:96, :144, :180`).
`build_threshold_analysis` prints them (`threshold_analysis.py:120-127`).
The committed `docs/generated/threshold_analysis.md` currently declares:

> ## Unresolved bands — moderate / none
> - Span: [0.0000000000, 0.4118946229]
> - Reason: moderate/none boundary 0.24581 sits above the median scored severity 0.19495 — bottom partition is degenerate…
> - Nodes inside (27): company:nvidia, product:cowos_packaging, company:samsung, …

Full 27-node membership listed correctly.

**But `_write_boundaries_to_config` in `backend/scripts/generate_inventory.py`
writes only the three boundary floats.** Lines 78–113 of that function
loop through `boundary_names = ("critical", "high", "moderate")` and
rewrite each `name:` line in the boundaries block. Nothing writes
`unresolved_bands`.

Grep across the repo (`grep -rn "unresolved_bands" backend/ config/`):

| location | kind |
|---|---|
| `backend/app/scoring/thresholds.py:71, :96, :200` | derivation output (write to in-memory object) |
| `backend/app/reporting/threshold_analysis.py:120, :123` | doc rendering (read → markdown) |
| `backend/app/scoring/engine.py:481` | ambiguity check (**read from config**) |
| `backend/app/scoring/config.py:265` | config accessor (**read from yaml**) |
| `backend/tests/fixtures/scoring.yaml:252` | stale hand-entry `[]` |
| `config/scoring.yaml:252` | stale hand-entry `[]` |

**No writer.** The `unresolved_bands: []` in committed config is a stale
hand-entry that no code path updates.

**Consequence:** `compute_tier_ambiguity` reads
`config.threshold_unresolved_bands`, sees an empty list, and returns
`(False, None)` for every node. All 27 band-member nodes are silently
unflagged.

### §3.1.1 §7(4)+(5) verification

**§7(4) — no code path writes `unresolved_bands` to config.** HIT.

**§7(5) — zero of the 27 band members carry `tier_ambiguous` in
`node_inventory.md`.** HIT — verified via `grep -c "tier_ambiguous"
docs/generated/node_inventory.md` = 0. Two overlapping reasons:

1. The `compute_tier_ambiguity` check reads the (empty) config `unresolved_bands` and always returns False.
2. Even if the flag were set on nodes, `build_inventory` in
   `backend/app/reporting/inventory.py` does not emit `tier_ambiguous` as
   a column in the Scored-nodes table. So the flag would be invisible even
   if it were set.

Two independent silent-drops on the same signal.

## §3.2 Latent scanner defect — REPORT, DO NOT FIX

In `_write_boundaries_to_config` (`generate_inventory.py:78-113`):

```python
inside_boundaries = False
for line in lines:
    stripped = line.strip()
    if stripped.startswith("boundaries:"):
        inside_boundaries = True; out.append(line); continue
    if inside_boundaries:
        # An unindented (or top-level) sibling ends the block.
        if line and not line.startswith(" "):
            inside_boundaries = False; out.append(line); continue
        # Rewrite the three boundary lines with derivation values.
        for name in ("critical", "high", "moderate"):
            prefix = f"    {name}:"                   # ← DEAD ASSIGNMENT
            if stripped.startswith(f"{name}:"):
                ...
```

The scanner exit is `if line and not line.startswith(" ")` — it exits
only when a fully-unindented sibling line is reached. But
`unresolved_bands:` in `config/scoring.yaml` sits at 2-space indent (same
level as `boundaries:`), so **the scanner does NOT exit at the end of the
boundaries block.** It stays inside_boundaries=True through the
`unresolved_bands:` line and any indented lines below it, until a fully
unindented sibling appears.

Any line in that span whose stripped form begins with `critical:`,
`high:`, or `moderate:` would be silently rewritten with a boundary value.

Not firing today because `unresolved_bands` is currently `[]` and has no
child items named after tier words. But if a future serializer wrote:

```yaml
  unresolved_bands:
    - lower: 0.0
      upper: 0.4118946228794891
      tiers:
        - moderate       # ← "moderate:" not matched (no colon after 'moderate')
        - none
      moderate: 0.5      # ← if any key here starts with the tier word, silent rewrite
```

…the risk becomes real. Latent.

**Dead assignment.** `prefix = f"    {name}:"` (line 103) is assigned and
never read. Dead. Latent (cosmetic).

## §3.3 Process finding

`moderate: 0.0` entered committed config through
`_write_boundaries_to_config` — a documentation-generation script. That is
F3 (Pass C) working exactly as designed: config is a rendering of
derivation output, not a parallel hand-entry.

**But it means a degenerate boundary was committed with no human decision
point anywhere in the loop.** The value moved from `derivation.boundaries`
straight to `config/scoring.yaml` via a script; no test caught it (the
sync test only checks that config matches derivation); no reviewer was
asked (the script runs in `generate_inventory.py`); the K.1 report §6
missed it (K.2 §6 corrects that).

Whether generated config values should be able to reach a commit unreviewed
is D5 in `k2_decisions.md`. **This diagnosis observes the outcome; it does
not decide the process.**

## §4 Chokepoint regression — walk the history

The original "every chokepoint the paper names lands in `critical`" claim
was reframed in Pass C (F2 fix) from tier-landing to
severity-above-median. But the chokepoint tier-landing table in
`threshold_analysis.md` continues to report the current tier of each,
and it currently reads:

| chokepoint | severity | current tier |
|---|---:|---|
| dysprosium | 0.5453 | critical |
| ASML | 0.5389 | critical |
| gallium | 0.4803 | **high** |
| TSMC | 0.4693 | **high** |
| CoWoS | 0.3132 | **moderate** |
| HBM | 0.1779 | **moderate** |
| RF & Power Semis | 0.0261 | **moderate** |

Two of seven remain in `critical`. Walked
`git log docs/generated/threshold_analysis.md`:

| pass | commit | chokepoint tiers |
|---|---|---|
| Pass B | `f05b307` | (chokepoint landing section not yet in doc) |
| Pass C | `d9fb92c` | TSMC:high / ASML:critical / gallium:high / dysprosium:critical / HBM:moderate / CoWoS:moderate / RF:none |
| Pass H | `a1041d2` | same as Pass C |
| Pass H.1 | `7345179` | same as Pass C |
| Pass K | `fc7ee3e` | same, RF still `none` (0.0246 under Pass K's fixed_reference=1.7710) |
| **Pass K.1** | `7843439` | same, **RF flipped `none → moderate`** because Pass K.1 boundary derivation set moderate=0.0 (§1 finding) |

**Two distinct events produced the current state:**

1. **Pass C** (F1 threshold rewrite): switched from the hand-set 0.225
   critical threshold to distribution-anchored natural-breaks. Under this
   derivation only ASML and dysprosium land in `critical`. The other
   five chokepoints score high enough by the model to be above the
   scored-severity median (F2 reframe validated them by that measure) but
   below the natural-breaks critical boundary. **Divergence began at
   Pass C. Recorded in that pass; not fresh.**
2. **Pass K.1** (moderate boundary collapse): RF & Power flipped
   `none → moderate` when the moderate boundary derived to 0.0 (§1).
   No node moved OUT of critical here; the flip was at the bottom.

**Nothing in K.1 moved a chokepoint OUT of critical.** All five non-critical
chokepoints have been non-critical since Pass C. The K.2 spec's phrasing
"5 of 7 remain" is accurate; "the model's validity claim is currently
false" is accurate as a paper-vs-model observation; but neither is a
K.1-introduced regression. It is a Pass C decision the project has
consciously carried since (see `test_paper_chokepoints.py` docstring
"reframed in Pass C (F2)" for the deliberate reframe).

### §4.1 What the current test enforces (for completeness)

`test_paper_chokepoint_severity_above_median` (K.1 §5-converted to
conditional xfail) checks whether each chokepoint's severity exceeds the
median. Post-K.1 median is **0.1949**. Results:

| chokepoint | severity | > median? |
|---|---:|---|
| dysprosium | 0.5453 | yes |
| ASML | 0.5389 | yes |
| gallium | 0.4803 | yes |
| TSMC | 0.4693 | yes |
| CoWoS | 0.3132 | yes |
| HBM | 0.1779 | **no → XFAIL** (pinned; reason unchanged) |
| RF & Power Semis | 0.0261 | **no → XFAIL** (pinned; reason unchanged) |

Under the K.1-mechanically-collapsed moderate boundary at 0.0, RF & Power
displays `moderate` but its severity is still below median — the tier
label moved without the underlying signal moving.

### §4.2 Recorded in `grading.md` (see §6)

The paper-vs-model validity claim needs plain reflection in the ledger.
It is a headline claim about the model's fidelity to the paper; it has
been false since Pass C (2 of 7 in critical instead of 7 of 7); the F2
reframe was the acknowledgment. K.2 §6.9 restates it plainly so the
ledger carries the reframe with its consequences named.

## §7 pre-registration scorecard for §3 + §4

| # | pre-registration | HIT / MISS |
|---|---|---|
| 4 | No code path writes `unresolved_bands` to `config/scoring.yaml` | **HIT** — grep verified above |
| 5 | Zero of the 27 band-member nodes carry `tier_ambiguous` in `node_inventory.md` | **HIT** — for two overlapping reasons; §3.1.1 |
