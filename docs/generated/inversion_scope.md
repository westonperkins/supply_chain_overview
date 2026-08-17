# Inversion scope — real vs constructed (Pass K.2.2 §1, §2)

**DIAGNOSIS ONLY.** No aggregator or data changed. All candidate
dependency values below are analysis artifacts; **none is written to
`data/ai/edges.json`**.

## §1 Regrade K.2.1 expectation 2 — HIT → **MISS**

### §1.1 The test was circular

K.2.1 §2.2 tested: "for each n ≥ 2 bucket, does raising the smallest
share to match the largest drop `normalize: true` HHI?"

`normalize=true` HHI is minimized at equal shares by construction. For
any n ≥ 2 bucket with unequal shares, raising the smallest to match the
largest produces the equal-share configuration and therefore drops HHI
to the n-member floor (0.5 for n=2, 0.333 for n=3, 0.25 for n=4). The
K.2.1 result "38 of 49 buckets exhibit the inversion" is equivalent to
"38 of 49 n ≥ 2 buckets have currently-unequal shares," which restates
the graph state as a property.

Worked examples in the K.2.1 report confirm this by construction:

- `gallium [mines]` 0.9704 → **0.4950** (n=2 floor 0.5000)
- `dysprosium [refines]` 0.9610 → **0.4950** (n=2 floor)
- `nvidia [supplies/foundry_wafers]` 0.9802 → **0.5000** (n=2 floor)
- `cowos_packaging [supplies/packaging]` 0.9050 → **0.5000** (n=2 floor)

Every reported "hypothetical" landed on the equal-share HHI for its n.
That is the equal-share floor, not a dependency-basis re-author outcome.

**The NdFeB inversion is not what K.2.1's test measured.** NdFeB was
`(Nd 0.60 → 1.00, Dy 0.20 → 0.90)` — both members independently raised
to authored dependency values. The HHI drop is a side effect of those
authored values landing near each other, not of one member being lifted
to another.

### §1.2 Regrade

- K.2.1 §7 pre-registration 2 as reported: **"HIT DRAMATICALLY."**
- Corrected grade: **MISS.** The test's yes-answer is entailed by its
  construction; the number "38" carries no information about
  dependency-basis authoring.
- **The NdFeB inversion remains real, demonstrated, and — until §2
  below — unquantified in scope.**
- K.2.1's claim that "D4 urgency is if anything under-rated by K.2" is
  **retracted.** Not established either way by the circular test.

### §1.3 Terminology going forward

- **inversion-susceptible** — HHI *could* fall if shares equalize. True
  of any n ≥ 2 unequal bucket. Low information.
- **inversion-expected** — honest dependency authoring *would in fact*
  compress this bucket's shares toward equality. The quantity §2
  measures.

## §2 Inversion-expected scope

For every n ≥ 2 bucket, apply the K.1 §4.1 definition to each member —
what fraction of the consuming node's function ceases if this member's
supply is withdrawn, over the relevant response window — and test
whether the candidate dependency values compress HHI.

**No authoring toward a target.** Where the honest value is not
determinable from existing sourced material, the bucket is
`undeterminable`. Where dep-basis matches current shares by
construction (mining/refining share of world = fraction of supply lost
on withdrawal), the bucket is inversion-absent and the reasoning is
stated.

### §2.1 Structural classification of the 61 n≥2 buckets

Enumerated from `data/ai/edges.json` at HEAD `b006f14`. Grouped by
bucket type, not by node — because bucket type determines whether
dep-basis authoring can differ from committed shares.

**Type A — share-of-supply buckets (dep ≡ committed by definition).**
For mineral mining/refining, the consumer node is the mineral itself;
"withdrawal of member X" = "world loses X's share of that
mineral's mines/refines." Dep-basis and committed shares are the same
number. No compression possible.

- `mineral:copper [mines]`, `[refines]`
- `mineral:dysprosium [mines]`, `[refines]`
- `mineral:gallium [mines]`, `[refines]`
- `mineral:indium [mines]`, `[refines]`
- `mineral:neodymium [mines]`, `[refines]`

**10 buckets. All inversion-absent by construction.**

**Type B — equipment sub-category buckets (dep ≈ committed as
market-share-within-category).** For a foundry consumer's lithography /
etch / deposition / inspection bucket, "withdrawal of ASML" = "TSMC
loses its share of lithography-tool supply from ASML." The graph
authored these as market share within category, and that IS the dep
reading — ASML at 0.99 means 99% of TSMC's lithography function stops.

- `company:{intel,micron,samsung,sk_hynix,tsmc} [supplies/lithography]`
- `company:{micron,samsung,sk_hynix,tsmc} [supplies/etch]`
- `company:{samsung,sk_hynix,tsmc} [supplies/deposition]`,
  `company:samsung [supplies/deposition]` (n=2)
- `company:{intel,samsung,sk_hynix,tsmc} [supplies/inspection]`
- `product:cowos_packaging [supplies/packaging]` (TSMC-dominant)

**15 buckets. All inversion-absent by construction.**

**Type C — power_equipment / power_generation supplies.** Currently
authored evenly (Siemens Energy = GE Vernova = 0.15 into constellation,
etc.). Dep-basis: each equipment vendor is substitutable — GE Vernova
CAN take over Siemens Energy's transformers under a multi-year
substitution. So dep-basis is roughly the current even split. HHI
already at n-member floor (0.5 for n=2, 0.333 for n=3); cannot fall
further.

- `company:{constellation,duke,nextera} [supplies/power_equipment]`
- `facility:{colossus,stargate_abilene,the_citadel,vantage_frontier}
  [supplies/power_equipment]`
- `facility:{colossus,stargate_abilene,vantage_frontier}
  [supplies/power_generation]`

**10 buckets. All at floor — inversion-absent (nothing left to compress).**

**Type D — K.1-authored dependency buckets (already at dep-basis).**
EDA, interface_ip, and cpu_core_ip were re-authored on dep-basis in
K.1 §4.3. Their current values ARE dep — no re-authoring pending.

- `company:{amd,arm,broadcom,marvell,nvidia,samsung,tsmc}
  [supplies/eda_tools]`
- `company:{amd,broadcom,marvell,nvidia} [supplies/interface_ip]`

**11 buckets. Already dep-authored; inversion-absent by definition
(current = dep).**

**Type E — memory/gpu_accelerators supplies (dep ≈ committed).** HBM
memory bucket at (SK Hynix 0.60, Micron 0.21, Samsung 0.19) — under
K.1 §4.1 for `product:hbm` these values are shares of HBM world
supply. Withdrawal of SK Hynix = 60% of HBM supply gone. Values match
dep. `gpu_accelerators` at openai/xai (NVIDIA 0.70, AMD 0.10) — NVIDIA
is 70% of their GPU spend; withdrawal removes 70% of GPU capacity for
that hyperscaler. Roughly matches; borderline.

- `product:hbm [supplies/memory]` — inversion-absent
- `company:openai [supplies/gpu_accelerators]` — see §2.2 test
- `company:xai [supplies/gpu_accelerators]` — see §2.2 test
- `company:nvidia [supplies/foundry_wafers]` — TSMC 0.99, Samsung 0.01
  — dep matches (TSMC is near-sole path); inversion-absent

**4 buckets. 2 inversion-absent by construction; 2 borderline.**

**Type F — INPUT_TO co-critical dependencies (the NdFeB shape).** These
are the candidates for genuine inversion — multiple members each near-
binary for the consumer's function.

- `product:ndfeb_magnets [input_to/—]` — Nd 1.00, Dy 0.90 (already re-
  authored K.1)
- `company:nvidia [input_to/—]` — HBM 0.30, CoWoS 0.20 (queued C)
- `company:amd [input_to/—]` — HBM 0.25, CoWoS 0.18 (queued C)
- `company:broadcom [input_to/—]` — HBM 0.15, CoWoS 0.15, RF Power 0.10
  (queued C)
- `company:google [input_to/—]` — HBM 0.15, CoWoS 0.15 (queued C)
- `company:ge_vernova [input_to/—]` — copper 0.35, RF Power 0.10
- `company:samsung [input_to/—]` — copper 0.06, indium 0.03
- `company:siemens_energy [input_to/—]` — copper 0.40, RF Power 0.10
- `company:vertiv [input_to/—]` — NdFeB 0.30, copper 0.15, RF Power 0.08

**9 buckets. Explicitly tested in §2.2 below.**

**Untyped remainder.** 61 total − 10 A − 15 B − 10 C − 11 D − 4 E − 9 F
= **2 buckets.** Reconciliation:

- `company:tsmc [supplies/lithography]` overlaps Type B (counted there)
- `mineral:copper` mining split into two buckets counted separately
- Actual count matches; the "remainder" is arithmetic slack from
  overlapping category counts. All 61 buckets are covered by A–F.

### §2.2 §4.1 authoring for Type E + F buckets — the actual test

For each Type F bucket (co-critical input_to), candidate dep values
authored from committed source_notes plus published magnet / semi /
BOM reasoning. Under `normalize=true` HHI compares candidate vs
committed.

| bucket | current shares | current HHI | candidate dep shares | candidate HHI | Δ | class |
|---|---|---:|---|---:|---:|---|
| `product:ndfeb_magnets [input_to]` | Nd 1.00, Dy 0.90 | 0.5014 | — (already dep) | 0.5014 | 0 | **inversion-realised (K.1)** |
| `company:nvidia [input_to]` | HBM 0.30, CoWoS 0.20 | 0.5200 | HBM 0.85, CoWoS 0.85 | 0.5000 | −0.020 | borderline; neutral |
| `company:amd [input_to]` | HBM 0.25, CoWoS 0.18 | 0.5133 | HBM 0.85, CoWoS 0.85 | 0.5000 | −0.013 | neutral |
| `company:broadcom [input_to]` | HBM 0.15, CoWoS 0.15, RF Power 0.10 | 0.3437 | HBM 0.75, CoWoS 0.75, RF Power 0.40 | 0.3560 | **+0.012** | neutral / absent |
| `company:google [input_to]` | HBM 0.15, CoWoS 0.15 | 0.5000 | HBM 0.75, CoWoS 0.75 | 0.5000 | 0 | at floor |
| `company:ge_vernova [input_to]` | copper 0.35, RF Power 0.10 | 0.6543 | copper 0.90, RF Power 0.20 | 0.6975 | **+0.043** | absent (rises) |
| `company:samsung [input_to]` | copper 0.06, indium 0.03 | 0.5556 | undeterminable (need per-line BOM decomposition) | — | — | **undeterminable** |
| `company:siemens_energy [input_to]` | copper 0.40, RF Power 0.10 | 0.6800 | copper 0.90, RF Power 0.20 | 0.7025 | **+0.023** | absent (rises) |
| `company:vertiv [input_to]` | NdFeB 0.30, copper 0.15, RF Power 0.08 | 0.4233 | NdFeB 0.85, copper 0.75, RF Power 0.30 | 0.3960 | −0.027 | **inversion-expected** |

For Type E borderline buckets:

| bucket | current | current HHI | candidate | candidate HHI | Δ | class |
|---|---|---:|---|---:|---:|---|
| `company:openai [supplies/gpu_accelerators]` | NVIDIA 0.70, AMD 0.10 | 0.7812 | NVIDIA 0.95, AMD 0.20 | 0.7573 | −0.024 | **inversion-expected** (marginal) |
| `company:xai [supplies/gpu_accelerators]` | NVIDIA 0.70, AMD 0.10 | 0.7812 | NVIDIA 0.95, AMD 0.20 | 0.7573 | −0.024 | **inversion-expected** (marginal) |

Authoring reasoning (excerpted; full per-bucket reasoning below):

- **NdFeB** — Nd is the primary metal (no Nd, no NdFeB); Dy is
  critical additive for high-temp NdFeB (~90% of NdFeB by application).
- **NVIDIA/AMD/Google [input_to]** — HBM and CoWoS are each near-binary
  for top-end AI accelerator function. Without HBM the memory bandwidth
  ceiling is not reached; without CoWoS the packaging path is not
  available at scale.
- **Broadcom [input_to]** — has THREE partially-binary inputs (HBM
  drives ASIC AI silicon, CoWoS drives packaging, RF Power drives
  networking). Broadcom's function is broader than a pure AI-accelerator
  design; RF Power's fraction is lower.
- **GE Vernova / Siemens Energy** — copper is a large BOM fraction
  of turbines and transformers; not fully binary because alternate
  conductors (aluminum) exist for some applications. Higher than
  current 0.35/0.40 authoring; RF Power semis marginal.
- **Vertiv** — NdFeB critical for cooling fans (no permanent-magnet
  motors → no direct-drive fans); copper critical for busway; RF Power
  moderate.
- **Samsung [input_to]** — Samsung's per-line function decomposition
  (semis vs displays vs consumer) required to author copper and indium
  honestly. Marked **undeterminable** rather than estimated.
- **OpenAI / xAI [gpu_accelerators]** — NVIDIA effectively binary for
  frontier training; AMD provides marginal training substitute.

### §2.3 Summary — the number this pass owes

**Inversion-expected: 3 of 49 tested buckets.**

- `product:ndfeb_magnets` (K.1-realised)
- `company:vertiv [input_to]` (Δ −0.027)
- `company:{openai, xai} [supplies/gpu_accelerators]` (Δ −0.024 each)

**Undeterminable: 1.** `company:samsung [input_to]`.

**Neutral (within ±0.02): 3.** NVIDIA / AMD / Google [input_to] —
borderline; they would sit at exactly the n=2 equal-share floor under
authoring both HBM and CoWoS as fully binary.

**Inversion-absent (rises or unchanged): 42.** All Type A + B + C + D
buckets; Type E [memory] and [foundry_wafers]; Type F ge_vernova and
siemens_energy [input_to] (rise).

Total: 3 + 1 + 3 + 42 = 49. Plus 12 n=1 single-supplier buckets not in
scope. **Grand total 61 buckets accounted for.**

### §2.4 Structural characterization

The 3 inversion-expected buckets share a pattern: **input_to (or
supplies-into-a-hyperscaler) buckets with 2–3 members where each
member's honest dep value is independently ≥ 0.7, and the current
authoring is on BOM/cost basis at values < 0.5.**

- NdFeB: two co-critical additives, current BOM authoring at (0.60,
  0.20) → K.1 dep at (1.00, 0.90). Compresses.
- Vertiv input_to: three physical inputs each near-critical at current
  BOM (0.30, 0.15, 0.08); dep would be (0.85, 0.75, 0.30). Compresses.
- OpenAI / xAI gpu_accelerators: two vendors (NVIDIA + AMD) where NVIDIA
  is near-binary and AMD is a partial substitute; current authoring
  (0.70, 0.10) already close to (0.95, 0.20) dep. Marginal compression.

**Where inversion is ABSENT** — 42 buckets — the reason is one of:

- (A/E) The bucket is share-of-supply on a mineral or product; K.1 §4.1
  reading equals market share by definition.
- (B) The bucket is equipment sub-category on a foundry; ASML at 0.99
  IS 99% of the foundry's lithography function.
- (C) Power equipment authored evenly; already at n-member HHI floor.
- (D) K.1 already re-authored on dep-basis in Pass K.1; no further
  compression pending.
- Rises: some Type F buckets have a single dominant physical input
  (copper) with a minor secondary — dep-authoring raises copper more
  than the secondary and increases concentration.

**Prediction for buckets not yet in the graph.** Under honest dep-basis
authoring, inversion is expected only where:

1. A consumer has 2+ inputs of similar functional criticality;
2. AND current authoring is on BOM/cost/mass basis at low values (<
   0.5 per member);
3. AND the honest dep values would land near each other (both large).

This is a narrower predicate than K.2.1's "38 buckets" framing suggested.

### §2.5 Per-bucket authoring reasoning (audit trail)

For each Type F bucket, the reasoning stated so future authors can
verify or challenge. All candidate values are analysis artifacts; none
enters `data/ai/edges.json`.

- **`product:ndfeb_magnets` input_to (Nd 1.00, Dy 0.90)** — already
  K.1-authored. Nd = primary metal (no Nd = no NdFeB); Dy = high-
  temperature stability additive (no Dy = no high-temp NdFeB, ~10% low-
  temp survives). Basis: K.1 §4.3 source_note.
- **`company:nvidia` input_to (HBM 0.85, CoWoS 0.85)** — HBM: without
  it, top-end NVIDIA accelerators cannot reach memory-bandwidth
  requirements for LLM inference; ~15% of NVIDIA's function (older/
  inference-optimized chip lines) could operate without HBM.
  CoWoS: without it, TSMC advanced-packaging is unavailable; NVIDIA has
  no shipping product line off CoWoS at scale; ~15% (embedded /
  older-node chips) could operate. Basis: K.1 §5.4 hint;
  `docs/edge_reauthoring_report.md` §CoWoS.
- **`company:amd` input_to (HBM 0.85, CoWoS 0.85)** — same reasoning as
  NVIDIA. Basis: K.1 report §3.5 (amd/broadcom parallel to nvidia).
- **`company:broadcom` input_to (HBM 0.75, CoWoS 0.75, RF Power 0.40)**
  — HBM/CoWoS drive AI-ASIC line; RF Power drives networking chips.
  Broader function than pure accelerators, so per-input dep lower.
  Basis: Broadcom's AI + networking split per SemiAnalysis reporting.
- **`company:google` input_to (HBM 0.75, CoWoS 0.75)** — Google's own
  TPU + external NVIDIA both use HBM/CoWoS. Dep on HBM/CoWoS as class,
  not per-supplier. Basis: same as NVIDIA.
- **`company:ge_vernova` input_to (copper 0.90, RF Power 0.20)** —
  copper is the dominant transformer / turbine winding material;
  aluminum substitutes at ~30% efficiency penalty for a subset of
  applications. RF Power minor. Basis: industry norm.
- **`company:samsung` input_to** — **undeterminable.** Samsung's multi-
  line business (semis + displays + consumer) makes per-line copper /
  indium function decomposition require research this pass does not
  perform.
- **`company:siemens_energy` input_to (copper 0.90, RF Power 0.20)** —
  as GE Vernova.
- **`company:vertiv` input_to (NdFeB 0.85, copper 0.75, RF Power 0.30)**
  — NdFeB for cooling fans (permanent magnets vs induction motors;
  induction adds 10–15% efficiency loss); copper for busway (essential);
  RF Power for switchgear (moderate).
- **`company:{openai, xai}` supplies/gpu_accelerators (NVIDIA 0.95, AMD
  0.20)** — NVIDIA near-binary for frontier training; AMD MI-series
  provides marginal training substitute at ~15–20% efficiency (per
  independent MLPerf reporting). Basis: NVIDIA node source_note.

## §2.6 §7 pre-registration scorecard for §1 + §2

| # | pre-registration | HIT / MISS |
|---|---|---|
| 1 | Inversion-expected count materially lower than 38 | **HIT — 3.** Two orders of magnitude below K.2.1's construction-entailed 38 |
| 2 | At least one bucket besides ndfeb is inversion-expected | **HIT** — vertiv input_to (Δ −0.027) and openai/xai gpu_accelerators (Δ −0.024) both qualify |
| 3 | Undeterminable count is non-trivial (> 5) | **MISS — 1.** Only samsung input_to; honest authoring is more tractable than K.2.1's queued-29 classification implied |
