# Pass K.2 — Decision points

**These are decisions for Weston, not recommendations to execute.** Each
point summarises the case on both sides plus a recommendation with
reasoning. The fix-pass that follows K.2 acts on whatever Weston picks;
K.2 itself makes zero of these changes.

The five decisions are ordered by how much other work depends on them —
D1 and D4 gate several potential later passes; D5 is a process
observation with wider implications; D2 and D3 are more contained.

---

## D1 — Unresolvable boundary: keep `0.0` or introduce a withheld tier?

**Case for withheld tier.** Consistent with the project's existing
`missing_static_axes: unscored` pattern (`docs/scoring_honesty_fixes_spec.md`
§2): when the model lacks the data to say what a node's value is, the
correct output is a distinct not-scored state, not a substituted zero.
`0.0` on the moderate boundary is a substituted zero at the tier layer —
same shape, same defect. A withheld tier honestly says "the derivation
could not separate these tiers; each node in the band is not tier-scored
but its severity number stands." Downstream consumers can render it with
a distinct visual (see §1.3 blast-radius enumeration in
`boundary_derivation_diagnosis.md`).

**Case for keeping 0.0.** Every scored node gets a tier under the current
scheme. A withheld tier is contagious — cascade, narration, frontend,
tests, and the tier-histogram all need to know about it. The K.1 K.2
review already surfaced a smaller version (K.1 §7.3 frontend visual
treatment deferred). Introducing a new tier member is a schema change with
migration cost across ~8 surfaces. Full blast radius in `boundary_derivation_diagnosis.md`
§1.3.

**Recommendation: WITHHELD.** The 0.0 fix is the wrong shape once the
retry (D2's recommendation) is added — retry closes the visible case;
withheld handles the residual cases without lying about them. The blast
radius is real but bounded and each surface's change is small. Pair the
decision with a schema-migration pass that touches every surface once.

---

## D2 — Does the median guard survive?

**Case against.** The F1.b guard rejects a moderate boundary if its
midpoint exceeds the median scored severity, on the grounds that the
bottom partition would then be degenerate ("`none` swallows the majority
of scored nodes"). Two observations:

1. The guard caps `none` at half the scored nodes. But a chokepoint
   model's whole thesis is *imbalance* — most nodes should be
   unremarkable; a handful are critical. Enforcing balance against a
   deliberately-imbalanced distribution is against the point.
2. On the current data the guard fires, terminates search, and produces
   the pathological `moderate = 0.0`. Two lower candidates that would
   pass the guard remain available (§1.1 arm_core_ip→cadence at 0.1367,
   cadence→arm at 0.1087) and are never tried.

**Case for.** Some degenerate outcomes are worth catching — e.g. a
distribution where only one node scores above 0 would produce a
meaningless "critical/high/moderate" separation. A guard prevents the
derivation from shipping a partition where all boundaries pile up in one
region. But "shipping a partition" is not "declaring the moderate
boundary above the median"; those are different failures.

**Recommendation: REPLACE, DON'T DELETE.** Replace the median-comparison
guard with a **retry loop**: when the top-3-by-size selection produces a
moderate above the median, advance to the next-largest separating gap
below the median. Only if no candidate below the median exists, escalate
to the withheld-tier path (D1). Retry closes the observed failure without
imposing balance assumptions on a model designed around imbalance.

Add a genuine degeneracy test — e.g., all three boundaries within a
threshold epsilon of each other — as a residual guard for pathological
distributions. This is D2's actual scope, not the median comparison.

---

## D3 — Relative or absolute tiers? (time-sensitive)

**Case for absolute thresholds.** Distribution-anchored boundaries mean a
node's tier depends on *what else is in the graph*. Adding the robotics
graph and the aerospace graph will reshuffle every AI tier — same node,
different colour, nothing about the node changed. Cross-domain scoring
requires cross-domain stability. Fixed thresholds give it.

**Case for keeping distribution-anchored.** Self-calibration. A fixed
threshold picked today would already be arbitrary; picked once and never
revisited it drifts from the distribution over time. Distribution-anchored
boundaries move with the graph, so a "critical" always means "top of the
current distribution" rather than "top of the 2026 distribution frozen in
config."

**Cost curve.** ⚠ **Pass K.2.1 §5 correction.** K.2's D3 originally
stated "the cost roughly triples if deferred past robotics; six-fold
after aerospace." **Those numbers were not derived from any committed
artifact and are withdrawn.** No costing framework exists in the repo
that produces multipliers for a domain migration; the K.2 reviewer used
"triple / six-fold" as shorthand for "materially larger, then materially
larger again." That shorthand should not have appeared as a precision
claim.

Qualitatively: the switch from distribution-anchored to absolute
thresholds requires re-baselining every committed severity snapshot,
re-noting every prior severity_diff, and re-writing every grading
claim that references a tier. Doing this once (before robotics) is
work; doing it again (after robotics but before aerospace) is more
work because the snapshot corpus is larger. **The direction is right;
the multipliers were not.**

This is the third recorded instance of asserted-precision-without-
derivation in the K sequence (§6.3 recurrence pattern). Logged for
the ledger.

**Recommendation: DEFER but flag as time-sensitive.** Before adding
robotics: pick. Before adding aerospace: definitely pick. Decision needs
Weston's read on how important cross-domain comparability is vs
self-calibration honesty; both are defensible. The switch cost grows
with the size of the snapshot / grading corpus at switch time — no
quantitative multiplier committed.

---

## D4 — What aggregates dependency shares?

**Follows from §2 diagnosis.** Four candidates evaluated in
`hhi_dependency_conflict.md` §2.3:

| option | ndfeb reading | scores well? |
|---|---:|---|
| A restore HHI summation | 0.625 | reverts K.1 §4.1, D-J-3 reopens |
| B noisy-OR over dep shares | 1.000 | matches intent |
| C max-share | 1.000 | works, loses multi-supplier info |
| D hybrid per-stage | 1.000 (input_to via B/C) | best-fit, largest cost |

**Recommendation: OPTION B (noisy-OR) WITH CAVEATS.** ⚠ **Pass K.2.1 §3
correction.** K.2's D4 recommended noisy-OR without recording its
principal weakness. Corrected here.

**Saturation is real.** Any single input at share = 1.0 forces noisy-OR
to 1.0 regardless of every other input. Under dependency semantics such
inputs are common, not rare — K.1 authored two directly (ndfeb→Nd 1.00,
arm_core_ip→arm 1.00). Full quantification in
`docs/generated/aggregator_saturation_analysis.md`:

- **2 of 31 scored nodes saturate today.** Under queued-29 re-authoring
  at honest dep values, 15 – 20 of 20 non-leaf scored nodes would sit
  at inbound noisy-OR ≥ 0.99.
- Median under noisy-OR: 0.1884 (was 0.1949). Number of separating gaps
  drops from 7 to 6 — three boundaries can still be placed, but the
  top of the distribution compresses (9 of 20 nodes at ≥ 0.99).
- **The boundary problem may migrate from the bottom (K.2 §1 moderate
  collapse) to the top** (compressed critical/high band). Diagnosis A's
  retry loop addresses the bottom; a top-of-distribution guard may be
  needed under noisy-OR + queued-29.

**Recommended pairing: B1 (0.95 cap by author convention).** Ban
`input_share = 1.0` in the authoring convention; cap dep values at
0.95. Preserves ordering under multi-input stacking (two 0.95 inputs
give noisy-OR 0.9975, distinct from a single 0.95 at 0.9500), reduces
top-of-distribution collapse. The 0.95 threshold has no principled
basis — it is an epsilon choice Weston would need to sign off on.

⚠ **Pass K.2.2 §3.1 correction: B1 is REJECTED.** B1 bends input data
to fit the model. The standing project rule is the opposite: when data
and a model constraint conflict, fix the model's resolution and report
the conflict. K.2.1 recommended B1 while rejecting B2 (evidentiary
bar) for "tuning-toward-target risk" — B1 carries the identical risk
with a different mechanism (an author who knows 1.00 is disallowed
authors against the constraint rather than against the evidence).
Saturation is a property of the noisy-OR aggregator; it belongs on the
aggregator side.

**Recommended pairing (K.2.2): noisy-OR with internal ε (=0.01) plus
count-aware auxiliary signal (share ≥ 0.90 threshold).** See
`docs/generated/aggregator_saturation_v2.md` §3.2 for the alternative
comparison.

- ε=0.01 handles saturation without capping authored values (author
  stays honest at 1.00; aggregator uses 0.99 internally). 0 nodes
  saturate today vs 2 under plain noisy-OR.
- Count-aware auxiliary preserves ordering among near-saturated nodes
  via lexicographic `(scalar, count)`. NdFeB reads (0.9990, 2 binary);
  arm_core_ip reads (0.9900, 1 binary) — distinguishable where plain
  noisy-OR ε would read them at the same scalar.
- Combined: **no top-of-distribution guard needed** (§3.3 verified).
- Cost: two-value concentration reading is a downstream integration
  item (cascade, severity formula, reporting need shims).

**Rejected mitigation: B2 (evidentiary bar for = 1.0).** Would require
per-edge author judgment on whether an input is "truly binary"; that is
tuning-toward-target risk. Not recommended.

**Rejected mitigation: bounded RMS.** Fixes saturation by giving up the
axis's core signal — dilutes concentration for all buckets, not just
saturated ones. `mineral:gallium` reads 0.4416 under RMS (down from
HHI 0.9704) — the 98.5% China dominance averaged against 1% Japan.

**Rejected mitigation: A (restore HHI summation).** Regresses K.1 §4.1
and reopens D-J-3.

⚠ **§2.4 K.2.1 evidence for D4 urgency (38 inversions) is retracted.**
K.2.1's raise-smallest-to-largest test was circular — normalize=true
HHI is minimized at equal shares by construction, so raising the
smallest share of any unequal bucket to match the largest always drops
HHI to the n-member equal-share floor. The number 38 was
"38 currently unequal n≥2 buckets." Under honest §4.1 dependency
authoring measured in `docs/generated/inversion_scope.md` §2.3, the
inversion-expected count is **3** (NdFeB + Vertiv input_to +
openai/xai gpu_accelerators). D4 urgency is real but narrower than
K.2.1 framed.

---

⚠ **Pass M validation — measured evidence supersedes approximation.**

Pass M ran all six candidate aggregators × two `min_suppliers` values
through the REAL engine via the seam added in
`backend/app/scoring/engine.py` (`compute_concentration_aggregate`).
Every K.2.2 §3 recommendation is now re-anchored on measured, not
approximated, numbers.

**Where K.2.2 approximation matched engine exactly (0% divergence):**
per-bucket concentration readings including NdFeB under every
candidate; xfail severities under D4+D4a. K.2.2's arithmetic on
isolated buckets was right.

**Where K.2.2 approximation was materially wrong:**

- Projected saturation: K.2.2 said "15–20 of 20 non-leaf scored nodes
  would sit at ≥ 0.99 after queued-29 re-authoring." Engine measured:
  **6 nodes at ≥ 0.99** (2 at exactly 1.0). K.2.2 was 3–4× too high.
  Reason: K.2.2 assumed dep values would cluster at 1.0; honest §2.5
  authoring is 0.75–0.95.
- Separating gaps under noisy-OR: K.2.2 said 6 (plain) and 5 (ε=0.05).
  Engine measured: **3 under both** on the current graph.
  K.2.2 halved.

Both distribution-wide K.2.2 errors overstated the saturation problem
noisy-OR would introduce. Post-M measurement: **saturation is real but
narrow.** Plain noisy-OR saturates ndfeb at min_supp=2 (1 node) and
ndfeb+arm_core_ip at min_supp=1 (2 nodes). ε=0.01 clears both.

**ε plateau confirmed on both graphs.** The tier histogram is stable
across ε ∈ [0.001, 0.100] on both current and projected graphs. Any
value in this range produces the same tier assignments. Ordering
within tiers changes at 7 pair-swaps across ε, but no tier crossing.

**Count-awareness is DEFERRABLE.** No pair of nodes has identical
severity to full precision on the 31-node scored set. Concentration
ties exist (ASML/TSMC at 1.0, arm_core_ip/arm at 0.99) but severity
resolves them via `(1 − sub) × lt_norm`. Downstream ranking operates
on severity, not concentration. The K.2.2 §5 recommendation to pair
ε with count-aware ordering is not needed today.

**Revised D4 recommendation (Pass M):**

- **Aggregator: noisy-OR with internal ε.** ε value chosen from the
  plateau [0.001, 0.100]. Any value works for tier assignment;
  saturation cushion (nodes at ≥ 0.99) drops from 6 to 1 as ε passes
  0.010 → 0.020. Not a decision this pass makes.
- **Pair with min_suppliers=1** (D4a) if the fix pass wants both xfails
  to XPASS. Engine confirms: under nor_eps_001_min1 both xfails read
  above the new median 0.2404 (rf_power 0.2872, HBM 0.3008).
- **Count-aware auxiliary NOT recommended.** Deferrable per §5.3 above.
  Revisit only if a downstream consumer stops resolving through
  severity.

**Cost enumeration** (Pass M §5.1): 6 code-changes + 2 data-changes to
adopt count-awareness. Not "shims." K.2.2's framing understated it.

**Recommended sequencing** (per Pass K.2.2 §5 finding, engine-confirmed):
ship D4 first, then D4a in separate commits. Under D4 alone (noisy-OR
+ min_supp=2), HBM XPASSES (0.3008 > 0.2015 median); rf_power stays
xfail (stage-zeroed). Under D4a alone (HHI + min_supp=1), rf_power
XPASSES (0.3191 > median). Under D4+D4a paired, both XPASS.

**Pair with `min_suppliers_for_concentration: 1`** (see D4a below). The
two changes are not separable — the pairing is load-bearing, not
convenient.

D4 lands before the 29 queued edges get re-authored.

### D4a — `min_suppliers_for_concentration: 1` pairing

**Complete separability analysis: paired changes are NOT separable.**
See `aggregator_saturation_analysis.md` §4.4:

- Noisy-OR alone (min_suppliers=2 unchanged) leaves rf_power_semis
  xfail unresolved (still stage-zeroed as single-source input_to).
- Min_suppliers=1 alone (HHI unchanged) reintroduces the HHI-normalizes-
  to-1 artefact for every single-source bucket — the problem the rule
  was designed to prevent.
- Together: rf_power_semis unzeroes at raw share 0.900 → noisy-OR reads
  0.900 (honest signal, not the 1.0 artefact); HBM's memory bucket
  moves from HHI 0.4402 to noisy-OR 0.744.

⚠ **Pass K.2.2 §5 correction: technically SEPARABLE; outcome-coupled.**
K.2.1's "NOT separable" was outcome-completeness language dressed as
technical coupling. Per `xfail_resolution_audit.md` §4.5–§4.6:

- D4 alone resolves **HBM** (noisy-OR turns memory bucket HHI 0.44 into
  NOR 0.744). Does NOT resolve rf_power (still stage-zeroed).
- D4a alone resolves **rf_power** (single-source stage unzeroes → HHI 1.0
  under normalize=true — artefact-heavy but XPASSES).
- D4 + D4a paired resolves both.
- Each xfail's resolution traces to ONE of the two changes; the pairing
  resolves both because the xfails have different named mechanisms.

**Recommended sequence: D4 first, then D4a in a separate commit.** Order
A per §5(4). Each commit's severity_diff is legible; each xfail's
resolution is traceable to a single change; neither commit's
intermediate state misrepresents any node's reading. Order B (D4a
first) would ship an intermediate state where every single-source
bucket reads HHI = 1.0 — the exact "cannot distinguish real monopoly
from unmodelled data" state min_suppliers=2 was designed to prevent.

**⚠ Material xfail resolution finding not recorded in K.2.** Under D4
+ D4a paired:

- `product:rf_power_semis`: severity 0.0261 → **0.2025** — passes
  median (0.1884) → XPASS.
- `product:hbm`: severity 0.1779 → **0.2121** — passes median → XPASS.

⚠ **Pass K.2.2 §4.1 correction: K.2.1 severity figures used the wrong
lt_norm.** K.2.1 used `lt_norm = lt / 10 = 0.30`; the engine uses
`log10(lt+1)/log10(26) = 0.4255` (per
`backend/app/scoring/engine.py::normalize_lead_time` line 285).

Corrected numbers:

- `product:rf_power_semis` under D4+D4a: **0.2872** (K.2.1 said 0.2025)
- `product:hbm` under D4 (alone or paired): **0.3008** (K.2.1 said 0.2121)
- Both xfails still XPASS by wider margins than K.2.1 reported.
- K.2.1's "median falling from 0.1949 → 0.1884" was an arithmetic error:
  the K.2.1 baseline used committed values (which use correct log10_1p),
  while the K.2.1 post-D4+D4a value used lt/10. Under consistent
  log10_1p the median RISES ~0.10 under D4+D4a — not falls.
  `xfail_resolution_audit.md` §4.4 has the reconciliation.

Named-mechanism check per §4.2 and §4.3: both xfail resolutions trace
DIRECTLY to mechanisms named in their own reason strings. rf_power's
reason names `min_suppliers=2 rule`; D4a ends the condition. HBM's
reason names `concentration capped at inbound_hhi 0.44`; D4 changes the
aggregation producing the 0.44. Neither resolution is an unrelated side
effect.

**Both currently-pinned xfails resolve** under D4+D4a paired. The K.1
§5 conditional-xfail mechanism (`strict=False`) reports XPASS as a
legitimate outcome — this is exactly the state the mechanism was
built to catch. When D4+D4a lands, `test_paper_chokepoint_severity_above_median[hbm-HBM]`
and `[rf_power_semis-…]` will both XPASS; SHA-256-pinned reasons need
retirement rather than deletion (recorded in the fix pass's Phase D
ledger, not silently deleted).

**Full impact enumeration** in `aggregator_saturation_analysis.md`
§4.1–§4.3: 13 stage-level and 29 category-level buckets currently
zeroed. K.2 §2.4.1 said 27 category-level; **actual count is 29**.
Logged as a K.2 correction in the ledger (§6).

---

## D5 — Should generated config values reach a commit unreviewed?

**Case for a review gate.** `moderate: 0.0` entered committed
`config/scoring.yaml` via `_write_boundaries_to_config` — a script — with
no human decision point (§3.3). The K.1 report §6 didn't catch it; the
review after commit did. A degenerate value in the config file that
guarantees "every scored node above 0 is moderate" is not a small thing
to slip through unnoticed.

**Case against.** F3 (Pass C) explicitly made config a rendering of
derivation, not a parallel hand-entry. Any review gate that requires a
human to acknowledge derivation output before it commits is halfway back
to hand-authored config, which was the failure mode F3 exists to fix.

**Recommendation: WARN, DON'T GATE.** Extend `_write_boundaries_to_config`
to emit a stderr warning when any of the three boundaries would be
rewritten to `0.0`, `1.0`, or falls outside its previous ±25% range.
Don't block the write; just make the anomaly visible before commit. The
pass author sees the warning during their normal `python generate_inventory.py`
run and knows to write it up rather than treating the diff as noise.

Complement with **D1** — if unresolvable boundaries become "withheld"
instead of 0.0, the specific 0.0 anomaly disappears, and the warning
becomes a residual sanity check rather than a load-bearing one.
