# Boundary derivation — diagnosis (Pass K.2 §1)

**DIAGNOSIS ONLY.** No code is changed by this pass; §5's decision points
determine the fix path. Every claim below is reproducible from committed
files via the scratch calculations recorded inline.

## §1.1 Established mechanism — VERIFIED

`derive_thresholds` in `backend/app/scoring/thresholds.py` selects the top-3
separating gaps by size (F1 fix, lines 118–121), then names them by
descending midpoint. The F1.b partition-sanity guard (lines 169–192)
rejects `moderate` when its midpoint exceeds the median scored severity
and hard-sets `boundaries["moderate"] = 0.0`.

**7 separating gaps** (median gap 0.008450, separation_factor 3.0, threshold
0.025351) — reproduced by scratch script against `data/ai/*.json` +
`config/scoring.yaml`:

| # | size | midpoint | upper | lower |
|---|---:|---:|---|---|
| 1 | 0.1148 | 0.4119 | company:tsmc (0.4693) | company:nvidia (0.3545) |
| 2 | 0.0587 | 0.5096 | company:asml (0.5389) | mineral:gallium (0.4803) |
| 3 | 0.0429 | 0.2458 | company:kla (0.2672) | company:siemens_energy (0.2244) |
| 4 | 0.0413 | 0.3338 | company:nvidia (0.3545) | product:cowos_packaging (0.3132) |
| 5 | 0.0386 | 0.2939 | product:cowos_packaging (0.3132) | company:samsung (0.2746) |
| 6 | 0.0291 | 0.1367 | product:arm_core_ip (0.1512) | company:cadence (0.1221) |
| 7 | 0.0268 | 0.1087 | company:cadence (0.1221) | company:arm (0.0953) |

**Selected top-3 by size** (F1 selection):

- gap #1 → **high** boundary at 0.4119
- gap #2 → **critical** boundary at 0.5096
- gap #3 → moderate candidate at 0.2458

**F1.b rejects gap #3** because 0.2458 > median 0.1949. Boundary is hard-set
to 0.0.

## §1.1 Defect — veto with no retry

Two separating gaps below the median were **available and never tried**:

| gap | midpoint | passes F1.b guard? | tier histogram if selected as moderate |
|---|---:|---|---|
| arm_core_ip → cadence | 0.1367 | **YES** | 2 critical / 2 high / **16 moderate / 11 none** |
| cadence → arm | 0.1087 | **YES** | 2 critical / 2 high / **17 moderate / 10 none** |

Either would ship a coherent partition. Neither is reached because the
F1.b block executes as a veto and terminates the search, not a rejection
that advances to the next candidate.

Gaps #4 (0.3338) and #5 (0.2939) also sit above the median and fail the
same guard. Two candidates below the median remain unused.

## §1.2 Deeper issue — no positional spread constraint

F1 replaced midpoint-ordering with size-ordering (correctly fixing a Pass B
bias that discarded large gaps sitting low). It introduced the mirror bias:
nothing constrains the three selected gaps to be *spread across* the
distribution. Post-K.1, all three largest gaps sit in the top third of
scored severities:

- top selected midpoints: 0.5096, 0.4119, 0.2458 — all above median 0.1949
- 20 of 31 scored nodes fall below the lowest selected midpoint

The retry loop that §1.1 proposes patches this specific instance. It does
not address the general case where the three largest gaps happen to cluster
anywhere in the distribution (top, middle, or bottom).

**Analysis of a spread constraint (design sketch, not implementation):**

A minimal spread rule would require that the three boundaries lie in
non-overlapping thirds of the scored-severity range (critical in the top
third, high in the middle third, moderate in the bottom third). Under the
current distribution:

- top third (≥ 0.4053): would select gaps #1 (0.4119) and #2 (0.5096) —
  both fit
- middle third (0.2027 – 0.4053): gaps #3 (0.2458), #4 (0.3338), #5 (0.2939)
  compete; largest by size (#3) wins for high boundary
- bottom third (≤ 0.2027): gap #6 (0.1367) or #7 (0.1087) selected for
  moderate; largest by size wins → #6 → **2 / 2 / 16 / 11**

This is a positional constraint on which of several equally-valid selected
gaps is assigned to which name, not a rule that alters the size-ordering
principle. It does not violate §1.6's prohibition on tuning toward target
tier membership because the constraint is on *position within the scored
severity range*, not on *node identity* or on *tier count*.

**Counter-argument.** Tertile split is arbitrary. Real distributions can
legitimately have their meaningful separations concentrated in one region.
A spread rule forces a boundary into a region where no natural break
exists.

**Alternative — combine size floor with retry.** Keep size-ordering as
primary, add F1.b as an in-loop rejection (advance to next candidate on
median-fail) rather than a terminal veto. Under the current data, this
produces the same outcome as the tertile rule (moderate = 0.1367).
Simpler; makes no assumption about where breaks should live; does not
address the general degenerate case where zero candidates below the
median exist.

**Recommendation for the fix pass:** retry rather than spread. Retry is
the smallest change that closes the observed failure. If the general
degenerate case becomes reachable later, add a spread rule then, with
evidence that it is needed. Recorded as D2 in `k2_decisions.md`.

## §1.3 `0.0` is the wrong failure mode

Current F1.b behaviour when the guard fires: `boundaries["moderate"] = 0.0`.
Every scored node with severity > 0 lands in `moderate`. The output is not
"we could not determine the moderate/none boundary" — it is the assertion
that all 27 scored nodes below the `high` boundary are `moderate`.

That is a stronger claim than the uncertainty represents.

**The project already has the correct pattern one layer up.** The engine's
`missing_static_axes: unscored` mode (per `docs/scoring_honesty_fixes_spec.md`)
refuses to score rather than substituting 0 or a neutral value on the
stated grounds that in a multiplicative model every substituted constant
is a claim about data that does not exist. The same reasoning applies at
the tier boundary layer and is not currently applied.

**Blast radius — what would break if unresolvable boundaries yielded a
withheld tier rather than 0.0.** Enumerated from grep of `ChokepointTier`
and `"moderate"` / `"none"` / `"unscored"` string literals across
`backend/` and `frontend/src/`:

1. **Tier enum** (`backend/app/schema/enums.py::ChokepointTier`) — currently
   5 members: `CRITICAL, HIGH, MODERATE, NONE, UNSCORED`. A `WITHHELD` (or
   `UNRESOLVED`) member would need adding, with a stable string value so
   the frontend union type can extend to match.
2. **Frontend type** (`frontend/src/types.ts:6`) — `type ChokepointTier =
   "critical" | "high" | "moderate" | "none" | "unscored"` — extend with
   the new member. TypeScript exhaustiveness checks on switch/match
   statements will fail-loudly at compile.
3. **Frontend CSS** (`frontend/src/index.css:134–139, 400–408`) — five
   tier-colour rules (`.tier-chip.tier-*` and `.tier-dot.*`). Sixth needed;
   choose a visual that reads as "withheld" (dashed border? outline only?)
   distinct from `unscored`'s dashed neutral.
4. **Narration** (`config/narration.yaml tier_words` + K.1 `tier_descriptions`)
   — add authored `withheld: "no assigned tier"` + a description like
   "the derivation could not separate this node's tier from its neighbours;
   see docs/generated/threshold_analysis.md for the unresolved band that
   holds it".
5. **Reporting** (`backend/app/reporting/threshold_analysis.py`,
   `inventory.py`) — tier-histogram tables need a withheld column;
   chokepoint-landing table needs to render withheld distinctly.
6. **Tests** — `SEVERITY_WORDS` in `test_narration.py`, tier-word invariant
   tests in `test_generated_artifacts.py` and `test_pass_d_baseline_current.py`,
   `KNOWN_MISS_XFAIL_REASONS` may reference tier names in prose reasons.
   Every reference audited for whether it should include or exclude
   withheld.
7. **`compute_tier_ambiguity`** — currently computes ambiguity within
   `unresolved_bands`. With a withheld tier, "ambiguous between moderate
   and none" and "withheld tier" become distinct states. Semantics need
   clarification: does a withheld node also carry `tier_ambiguous_with`?
   Probably yes — withheld nodes ARE the ambiguous set.
8. **Cascade** (`backend/app/scoring/cascade.py`, `engine.derive_current_tier`)
   — a node whose baseline_tier is withheld: what does the cascade do
   when an event touches it? Currently `derive_current_tier` returns
   `UNSCORED` when baseline is None. New branch needed: return `WITHHELD`
   (or preserve the withheld state) when baseline_tier is `WITHHELD`.

**None of these are ambitious changes individually. Together they touch every
tier-consuming surface — that is the cost of a new tier state, honestly
reported.** Estimated one dedicated pass to land the schema change, one
follow-up to migrate frontend + narration + tests. Recommendation captured
in `k2_decisions.md::D1`.

## §1.4 Minor defects in `thresholds.py` — REPORT, DO NOT FIX

**Defect 1 — `boundary_names[-1]` wrap.** Line 143:

```python
upper_boundary = boundaries.get(boundary_names[i - 1], scored[0][1])
```

When `i == 0` (critical branch), `boundary_names[i - 1]` evaluates to
`boundary_names[-1]` = `"moderate"`. Currently harmless because at `i == 0`
the `boundaries` dict is empty and `.get()` returns the `scored[0][1]`
default. If a future refactor pre-populates `boundaries` this becomes a
silent bug — critical's upper bound would be looked up under the moderate
key. Latent.

**Defect 2 — monotonic guard runs before F1.b.** Lines 158–167
(monotonic decrease check) execute before lines 169–192 (F1.b partition
guard). F1.b mutates `boundaries["moderate"] = 0.0` after the monotonic
check has passed, so the post-F1.b values are never monotonicity-checked.
Currently harmless because F1.b can only *lower* the moderate boundary,
preserving `critical > high > moderate`. Latent — a future addition to
F1.b that could raise a boundary or mutate another one would bypass the
check silently.

**Defect 3 — `separation_factor` history.** Verified via
`git log --all -p -- config/scoring.yaml`: `separation_factor: 3.0` was
introduced in the honesty-fixes pass and has not moved since. §1.4 third
bullet: unchanged. Confirmed.

**Defect 4 — unused `prefix` variable.** Not in `thresholds.py` — this
was flagged in the spec against `generate_inventory.py::_write_boundaries_to_config`.
See `boundary_serialization_diagnosis.md` §3.2.

## §1.5 §7 pre-registration scorecard for §1

| # | pre-registration | HIT / MISS |
|---|---|---|
| 1 | The 7 separating gaps reproduce exactly as listed in `threshold_analysis.md` | **HIT** — enumerated above; matches `threshold_analysis.md` |
| 2 | Both unused candidates (0.1367, 0.1087) pass the F1.b guard, and neither is reached by the current control flow | **HIT** — both pass (0.1367 < 0.1949 median; 0.1087 < 0.1949); F1.b `boundaries["moderate"] = 0.0` at line 191 terminates without iterating |
| 3 | `arm_core_ip → cadence` as moderate yields **2 / 2 / 16 / 11** | **HIT** — exact histogram reproduced |
