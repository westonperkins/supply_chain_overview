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

**Cost curve.** This decision gets substantially more expensive after the
graph triples. Committing to distribution-anchored today then switching to
absolute later means every prior severity_snapshot / severity_diff /
grading claim needs a rescale note (see K.1's `fixed_reference`
experience — the pattern is the same one layer up). Committing to
absolute today lets the graph grow without severity comparability breaks.

**Recommendation: DEFER but flag as time-sensitive.** Before adding
robotics: pick. Before adding aerospace: definitely pick. Decision needs
Weston's read on how important cross-domain comparability is vs
self-calibration honesty; both are defensible. If deferred past robotics
onboarding, the switch cost roughly triples.

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

**Recommendation: OPTION B (noisy-OR).** The graph already has the code
path — `events.combine: noisy_or` — so implementation is small. It has
the four properties dependency shares need (monotonic, [0,1], no
summation constraint, coexists with per-stage/per-category). The
independence assumption is a known caveat that applies equally to HHI.
Pair with **`min_suppliers_for_concentration: 1`** (see §2.4) — under
noisy-OR a single supplier at share s contributes s directly, no
HHI-normalizes-to-1 artefact.

D4 lands before the 29 queued edges get re-authored. The queued
authoring will worsen the current HHI-inversion problem, so the
aggregator decision must come first.

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
