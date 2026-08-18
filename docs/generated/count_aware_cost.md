# Count-aware concentration — cost enumeration + ordering-break test (Pass M §5)

**MEASUREMENT ONLY.** K.2.2 recommended pairing ε with a count-aware
auxiliary signal (share ≥ 0.90 threshold), calling downstream work
"shims." Pass M §5 tests whether that pairing is actually needed on
the current or projected graph, and enumerates what the shims would
touch if adopted.

## §5.1 Cost enumeration — every consumer of `concentration`

`concentration` is read at 8 surfaces in the codebase. `(scalar,
count)` would change the type of the model's central quantity.

| # | consumer | read where | change kind |
|---|---|---|---|
| 1 | **severity formula** | `config/scoring.yaml`:`formula: "concentration × (1 − substitutability) × lead_time"` — a scalar-arithmetic expression; `count` cannot multiply into it | **code-change** — either extend the formula to `concentration_scalar × (1 − sub) × lt × f(count)` where f is authored, or keep the formula on scalar-only and use `count` only for ranking |
| 2 | **cascade propagation** | `backend/app/scoring/cascade.py` — event walk multiplies inputs by shares, treats concentration as a scalar during propagation | **code-change** — cascade would need to decide whether to propagate count (probably not, since events are perturbations of a single scalar magnitude) |
| 3 | **derive_thresholds & tier assignment** | `backend/app/scoring/thresholds.py` — reads severity (scalar) to compute gaps and boundaries; tier assignment is scalar-only | **code-change if count enters tiering**; otherwise **no-change** (tiers stay severity-scalar-driven) |
| 4 | **severity_snapshot.json schema** | `backend/app/reporting/inventory.py::snapshot_severity` writes `{severity, tier, concentration, inbound_hhi, outbound_criticality}` per node | **data-change** — add `concentration_count` field; existing readers ignore unknown fields |
| 5 | **severity_diff generator** | `backend/app/reporting/inventory.py::build_severity_diff` reads concentration for change classification (RESCALE vs STRUCTURAL) | **code-change** — augment classifier with count-change detection, or leave count out of diffing |
| 6 | **node_inventory renderer** | `backend/app/reporting/inventory.py::build_inventory` emits `concentration`, `inbound_hhi`, `outbound_raw`, `outbound_normalized` columns | **data-change** — add `concentration_count` column alongside |
| 7 | **narration payload** | `backend/app/narration/builder.py` reads `dominant_axis` and `concentration` for scale-phrase lookups (`concentration_inbound`, `concentration_outbound`) — the tier chip and glance sentences | **code-change** — either author new `concentration_count` scale phrases or ignore count in narration |
| 8 | **frontend contract** | `frontend/src/types.ts::DynamicFields.concentration?: number` — a scalar field | **code-change** — extend to `concentration?: number | { scalar: number; count: number }`; downstream React components handle both shapes |
| 9 | **tests** | ~7 test files reference `concentration`, `inbound_hhi`, or tier landings that transitively depend on concentration | **code-change per test that asserts on concentration value** — mostly `test_bounds.py`, `test_tier_coherence.py`, `test_scoring_correctness.py` |

**Summary: 6 code-changes + 2 data-changes.** Not "shims" — a structural
change to the model's central quantity, with reach into every consumer
that reads concentration.

## §5.2 Ordering-break test — the question that actually decides it

For the best scalar-only candidate (nor_eps_001 + min_supp=1 on the
current graph): are there node pairs where scalar-only ties or inverts,
and where the binary-member count would resolve them differently?

### §5.2.1 Concentration ties (scalar-only)

Two strict ties at concentration level:

| pair | concentration | member counts (share ≥ 0.90) |
|---|---:|---|
| `company:asml` ↔ `company:tsmc` | both **1.0000** | ASML 0, TSMC 2 |
| `product:arm_core_ip` ↔ `company:arm` | both **0.9900** | arm_core_ip 1, arm 2 |
| `company:sk_hynix` ↔ `company:micron` | both **0.8690** | both 0 — count would NOT help |

- ASML has 0 modelled inbound edges (it's a producer, not a consumer)
  and reads 1.0 from outbound criticality (rank 1 clamp). TSMC has 2
  binary inbound suppliers (ASML at 0.99, KLA at 0.90) and reads 1.0
  from inbound HHI. Count-aware ordering would break the tie:
  `(1.0, 2) > (1.0, 0)`.
- `arm_core_ip` (single supplier `company:arm` at 0.99) vs `company:arm`
  (2 binary suppliers). Count-aware: `(0.99, 2) > (0.99, 1)`.

### §5.2.2 But severity ordering resolves these anyway

Severity multiplies concentration by `(1 − sub) × lt_norm`, and these
two axes differ between the tied pairs:

| pair | severity_A | severity_B | severity-ordered? |
|---|---:|---:|:---:|
| ASML (0.5389) vs TSMC (0.4693) | 0.5389 | 0.4693 | **yes** — ASML #2, TSMC #5 |
| arm_core_ip (0.3267) vs arm (0.2106) | 0.3267 | 0.2106 | **yes** — arm_core_ip #9, arm #18 |

**At the SEVERITY level, the ties are resolved by `(1 − sub) × lt_norm`.**
Ranking on severity produces a total order without any count auxiliary.

### §5.2.3 Close-scalar pairs where count would DIFFER

8 pairs on the current graph where severities are within 0.02 of each
other AND have different binary-member counts:

| A (sev, count) | B (sev, count) |
|---|---|
| `mineral:copper` (0.4967, 0) | `mineral:gallium` (0.4876, 1) |
| `mineral:gallium` (0.4876, 1) | `company:tsmc` (0.4693, 2) |
| `company:nvidia` (0.3581, 1) | `product:ndfeb_magnets` (0.3401, 2) |
| `product:ndfeb_magnets` (0.3401, 2) | `product:cowos_packaging` (0.3296, 1) |
| `product:hbm` (0.3008, 0) | `mineral:neodymium` (0.2951, 1) |
| `company:samsung` (0.2835, 1) | `company:lam_research` (0.2716, 0) |
| `company:micron` (0.2219, 0) | `company:arm` (0.2106, 2) |
| `company:arm` (0.2106, 2) | `company:applied_materials` (0.2015, 0) |

**In each case severity already resolves the ordering.** Count-aware
tie-break would only fire if two nodes had **identical severity to
several decimals**, which does not occur on the 31-node scored set —
the smallest gap between adjacent severities is 0.0009 (arm vs
applied_materials).

## §5.3 Verdict: count-awareness is DEFERRABLE

Under scalar-only nor_eps_001 + min_supp=1:

- **0 pairs of nodes have identical severity.** The ordering is total
  without a tie-break auxiliary.
- Concentration ties exist (2 pairs) but severity resolves them via
  the sub × lt_norm axes.
- Downstream ranking that operates on severity (all current UI and
  narration paths) is unaffected by count-awareness.
- Downstream ranking that operates on concentration alone (if any
  exists — none identified) would see ties broken by count.

**Recommendation** (per K.2.2 §5 discipline — "the question that
actually decides it"): **count-awareness is deferrable.** ε alone is
the smaller change.

### §5.3.1 If count-awareness is later needed

The predicate that would change this recommendation: a downstream
consumer starts using concentration-alone for ranking, or authoring
adds a bucket where 2+ nodes end up with identical severity to full
precision. Neither exists today on either graph.

If either happens, revisit §5.1's cost enumeration. The 6 code-changes
+ 2 data-changes cost is real; the value of paying it depends on how
many downstream ranking consumers stop resolving through severity.

## §6 pre-registration scorecard for §5

| # | pre-registration | HIT / MISS |
|---|---|---|
| 5 | The ordering-break list in §5 is non-empty under at least one candidate | **partial MISS** — under concentration ordering, 2 tie-pairs exist (ASML/TSMC at 1.0, arm_core_ip/arm at 0.99); count-aware would resolve them. But under severity ordering (the actual ranking consumers use), 0 pairs tie — count-awareness is deferrable |
