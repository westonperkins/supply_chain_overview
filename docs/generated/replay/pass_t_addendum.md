# Pass T addendum — corrections and reconciliation

**Type:** Reporting correction. No scoring change, no commits to data or config. All numbers read from `docs/generated/pass_t_facts.json` at commit `1dbdd46` and re-derived in-place from `pass_t_facts.json.candidates[*].node_matrix`.

Five items addressed. The last one changes the recommendation.

---

## 1 — ASML's tier under FR-B derived boundaries

**Artifact reports:** FR-B derived boundaries are `critical = 0.6357690337703887`, `high = 0.5247316525037853`, `moderate = 0.18767003183519004`. ASML's FR-B severity is `0.4667813528278457`.

Applying the lower-bound tier rule: `0.4668 < 0.5247` (below high) and `0.4668 > 0.1877` (above moderate) → **ASML tier under FR-B derived is `moderate`.**

**Movement:** committed `critical` → FR-B derived `moderate` = **2 tiers**, not 1.

**Which Pass T section was right, which was wrong:**

- Q9 said *"ASML: critical → moderate."* **Correct.**
- The ledger said *"under FR-B + derived (critical 0.6357…) they stay `high` (with dysprosium's severity unchanged at 0.5618 and ASML falling to 0.4668)."* **Wrong.** ASML at 0.4668 sits below FR-B's high boundary of 0.5247; it does not stay high.

**Retracted:** the ledger sentence quoted above is retracted. ASML moves 2 tiers under FR-B derived, matching Q9.

---

## 2 — Reconciling the FR-B five-node tier-change list

Re-derived directly from `pass_t_facts.json.candidates["FR-B"].node_matrix`, comparing each node's committed tier to the tier its FR-B severity would sit at under FR-B's derived boundaries. Result matches `pass_t_facts.json.candidates["FR-B"].moved_under_derived` exactly:

| node | committed sev | FR-B sev | committed tier | FR-B derived tier | tiers moved | direction |
|---|---:|---:|---|---|---:|---|
| `mineral:gallium` | 0.4876333076 | 0.4876333076 | high | moderate | 1 | ↓ |
| `mineral:dysprosium` | 0.5618299974 | 0.5618299974 | critical | high | 1 | ↓ |
| `company:tsmc` | 0.4692819869 | 0.4646359779 | high | moderate | 1 | ↓ |
| `company:asml` | 0.5389417592 | 0.4667813528 | critical | **moderate** | **2** | ↓↓ |
| `company:applied_materials` | 0.2015481248 | 0.1647214707 | moderate | none | 1 | ↓ |

**`applied_materials` — does it move?** Yes. Committed and FR-B side-by-side from `pass_t_facts.json`:

- Committed: `inbound_hhi = 0.0`, `outbound_criticality = 0.6766891505870234`, `severity = 0.2015481248`, `tier = moderate`, dominant axis **outbound**.
- FR-B: `inbound_hhi = 0.0`, `outbound_raw = 1.1308419667`, `outbound_normalized = 0.5530452451`, not clamped, `outbound_criticality = 0.5530452451`, `severity = 0.1647214707`, `tier_under_frozen = none`, dominant axis **outbound**.

**Dominant axis before and after: `outbound` in both cases** (inbound is 0.0, so any positive outbound wins the max). AMAT's outbound raw is 1.1308; under the frozen `fixed_reference` 1.6711 it normalizes to 0.6767; under FR-B's 2.0448 it normalizes to 0.5530. That drop of 0.1237 in concentration flows directly into severity: 0.2015 → 0.1647 (Δ = −0.0369). Under FR-B derived's moderate boundary of 0.1877, the FR-B severity 0.1647 falls just below → `none`.

**The Pass T ledger claim.** *"Net movement: 2 nodes drop under FR-B derived versus 4 under the current drift comparison."*

Directly comparable ground-truth from `pass_t_facts.json`:

- **FR-A (status quo)** `moved_under_derived`: 4 nodes — dysprosium (crit→high), asml (crit→high), gallium (high→mod), tsmc (high→mod). Matches the drift diagnostic in `threshold_analysis.md`.
- **FR-B** `moved_under_derived`: **5 nodes** — the four above plus **applied_materials (moderate→none)**, and ASML's movement extends from 1 tier to 2 tiers.

The ledger claim was **inverted and off by a count.** Under FR-B derived boundaries, **more nodes move, not fewer.** The correct statement:

> Under FR-B + derived boundaries at SF=3.0, **5 scored nodes change tier vs committed** (dysprosium, ASML, gallium, TSMC, applied_materials), with ASML moving **2 tiers down** (critical → moderate). This is more movement than the FR-A drift diagnostic shows (4 nodes, all 1-tier drops), not less. The extra movement — ASML's second tier and AMAT's tier drop — is a real cost of FR-B and belongs in the ship-pass attribution.

**Retracted:** the "Net movement: 2 nodes drop under FR-B derived versus 4 under the current drift comparison" sentence in the Pass T ledger.

---

## 3 — Blast radius for FR-C (identical shape to Q9)

Read from `pass_t_facts.json.candidates["FR-C"]`. FR-C derived boundaries are `critical = 0.5247316525037853`, `high = 0.42320867926942163`, `moderate = 0.15668443545638666`.

### Nodes changing tier under FR-C + derived boundaries

`pass_t_facts.json.candidates["FR-C"].moved_under_derived` — **exactly 2 nodes**:

| node | committed sev | FR-C sev | committed tier | FR-C derived tier | tiers moved |
|---|---:|---:|---|---|---:|
| `company:asml` | 0.5389417592 | 0.3817813806 | critical | **moderate** | **2** |
| `company:applied_materials` | 0.2015481248 | 0.1347260127 | moderate | none | 1 |

**ASML moves the same 2 tiers under FR-C as under FR-B**, but the severity path is different: under FR-C, ASML's outbound normalizes to 1.7710/2.5 = 0.7084 (rather than FR-B's 0.8661), so the compression is larger (Δ = −0.1571 vs FR-B's −0.0721). Either way, the frozen-critical membership is lost.

**AMAT moves the same 1 tier** (moderate → none) under both FR-B and FR-C, via the same outbound-driven mechanism — the fixed_reference change compresses outbound_normalized enough to drop the severity below the derived moderate boundary.

### FR-C stability elsewhere

Under FR-C, `copper`, `dysprosium`, `gallium`, and `TSMC` all **hold their committed tier**:

- copper: sev 0.5805 > 0.5247 crit → **stays critical**
- dysprosium: sev 0.5618 > 0.5247 crit → **stays critical**
- gallium: sev 0.4876 > 0.4232 high → **stays high**
- TSMC: sev 0.4646 > 0.4232 high → **stays high**

FR-B moves all four of these; FR-C moves none of them.

### Snapshot re-capture

Required. Same shape as FR-B: severity_snapshot.json rolls forward to a new label (e.g. `pass_p52_rebaseline_frc`), an atomic roll-forward diff (`severity_diff_pass_p52_rebaseline_frc.md`) captures the transition, and `pass_facts.py` compares against the pre-ship HEAD.

### Committed artifacts regenerating

Same set as FR-B:

- `docs/generated/node_inventory.md` — every scored severity changes under FR-C (via the fixed_reference compression), so the inventory regenerates on every scored row.
- `docs/generated/threshold_analysis.md` — the drift verdict becomes "still fits the distribution" at ship time by construction; the derivation and per-boundary drift rows regenerate.
- `docs/generated/severity_diff.md` — the rolling diff regenerates against the new snapshot label.
- `docs/generated/severity_snapshot.json` — re-captured under the new label.
- `docs/generated/severity_diff_pass_p52_rebaseline_frc.md` — new roll-forward artifact.

### Guards forecast

- **`backend/tests/test_thresholds_frozen.py`** — `FROZEN_BOUNDARIES` literals must be updated to FR-C's derived triple `(0.5247316525037853, 0.42320867926942163, 0.15668443545638666)` in the same commit that ships FR-C. Same shape as the FR-B forecast; different literals.
- **`backend/tests/test_unscored.py::test_top_outbound_anchor_is_expected_node`** — currently asserts `mineral:copper` is rank-1 in raw outbound. Under FR-C, copper's raw is still 2.0448 vs ASML's 1.7710 (raw outbound is `fixed_reference`-independent) → copper is still rank-1 → **no change needed**. Same as the FR-B forecast: raw ranking is not affected by `fixed_reference`.
- **`backend/tests/test_generated_artifacts.py::test_config_boundaries_equal_derivation`** — currently skips under `mode: frozen`. Under FR-C, if the shipped literals equal the derivation output at ship time, the skip continues to be a no-op. Same as FR-B.

### Pinned files

No change. `known_share_offenders.txt` and `known_bucket_shortfalls.txt` are input-share files, `fixed_reference`-independent. Same as FR-B forecast.

### Blast-radius comparison FR-B vs FR-C

| | FR-B | FR-C |
|---|---|---|
| tier changes under derived boundaries | **5** | **2** |
| ASML movement | crit → moderate (2 tiers) | crit → moderate (2 tiers) |
| AMAT movement | moderate → none | moderate → none |
| dysprosium | crit → high (moves) | stays critical |
| gallium | high → moderate (moves) | stays high |
| TSMC | high → moderate (moves) | stays high |
| snapshot re-capture | required | required |
| artifacts regenerating | same set | same set |
| test literals updated | frozen boundaries + none else | frozen boundaries + none else |
| copper rank-1 test | still copper | still copper |
| pinned files | no change | no change |

**FR-C moves fewer than half as many nodes as FR-B and matches FR-B on every downstream mechanical cost.**

---

## 4 — Q6/Q8 circularity: the flip test cannot fail

The user's critique is correct.

**Q6** framed the K.1-warning question as: *"will you re-anchor again the next time the graph max moves?"* Answering "only under another authorizing spec" was the ground for calling FR-B pattern-not-syntax.

**Q8** proposed as the flip-to-FR-C condition: *"if the drift diagnostic under Pass T close still reports 4 would-change-tier under derived boundaries after FR-B is committed."*

But drift is defined as *frozen boundaries vs derivation from current distribution*. If FR-B ships with frozen boundaries set to FR-B's derived boundaries — which is what the recommendation is — then at ship time, frozen = derived by construction and drift reports **0 would-change-tier**. The flip test cannot return the refuting answer. This is the K.2.2 §6.2 pattern: a measurement whose outcome is entailed by the way it is set up.

Instance count of this pattern in project ledger:

1. K.1 §6.2
2. K.2 §6.3
3. K.2.1 §6.2
4. Pass S retraction (asserting max-path from a null result — retracted in the Pass S report correction commit `32a1ff4`)
5. **Pass T Q8 flip condition — this one.**

Now the fifth instance.

**Replacement flip condition (adopted).**

> **After FR-B ships, does any future pass's authoring push a node's raw outbound above `2.0447548854281186`?**

Falsifiability check:

- **Can return `yes`.** A future re-authoring pass could raise the input_share on any edge in a chain leading to a high-fan-out destination. Specifically, TSMC's raw (currently 1.7524) is a plausible candidate: if a future pass re-authors edges into TSMC's downstream customers (e.g., new cowos → new-consumer edges, or new supplies → new-fab edges), TSMC's max-of-paths outbound can rise. Similarly ndfeb_magnets → facility edges, if re-authored on §4 basis (they are S.7.2's undeterminable holdouts), could raise raw for upstream mineral nodes.
- **Can return `no`.** After a few passes of §4 authoring settled at Pass S close, if raw outbounds stabilize below 2.0448 for several passes, the K.1 warning does not fire and FR-B holds as a genuine one-time anchor.

If the answer becomes `yes`: FR-B is tracking the max on a lagged schedule (the second anchor cycle), the K.1 warning was correct, and FR-C's declared-arbitrariness would have been safer. That is the refuting outcome the original Q8 condition could not produce.

**Adopted:** the raw-outbound-above-`2.0447548854281186` test replaces Q8's drift-still-reports-4 test. Recorded in the ledger below.

---

## 5 — Restated recommendation

The corrections above change the arithmetic underlying the FR-B vs FR-C comparison:

| criterion | FR-B | FR-C |
|---|---|---|
| tier changes under derived boundaries | **5** | **2** |
| K.1 warning applies syntactically? | yes (fixed = max) | no (declared arbitrary) |
| K.1 warning applies on pattern reading? | possibly (item 4 test) | no |
| copper at concentration exactly 1.0? | yes | no (0.8180) |
| dynamic range restored at top? | yes | partially (top compressed) |
| ASML movement | crit → moderate (2 tiers) | crit → moderate (2 tiers) |
| AMAT movement | moderate → none | moderate → none |
| downstream tier movement (dysprosium/gallium/TSMC) | 3 nodes move | 0 nodes move |
| falsifiable flip test post-ship | yes (item 4 replacement) | not applicable (declared arbitrary) |

**Does FR-B still win once ASML's true 2-tier movement is on the table?**

**No.** The corrected picture makes the choice tighter than Pass T claimed:

- ASML's movement is a wash — **both** candidates move ASML 2 tiers.
- AMAT's movement is a wash — **both** candidates move AMAT 1 tier.
- FR-B additionally moves **dysprosium, gallium, and TSMC** — three more scored nodes changing tier, each of which the ship-pass would need to attribute to the fixed_reference change specifically (rather than to any node-level structural event).
- FR-B invites the K.1-warning discussion; FR-C sidesteps it by declaring the constant arbitrary rather than reading it off the graph.

**The dynamic-range argument for FR-B** (copper at exactly 1.0, ASML at 0.866, TSMC at 0.857) was a philosophical win, not a blast-radius win. The Pass T recommendation folded it into a claim that FR-B was preferable *overall*; the corrections invalidate the "overall" and leave the dynamic-range argument standing alone against a smaller blast radius and a cleaner relationship to the K.1 warning.

**Revised recommendation: FR-C, `fixed_reference = 2.5`, boundaries derived at SF=3.0 (critical `0.5247316525037853`, high `0.42320867926942163`, moderate `0.15668443545638666`).**

Case against FR-C, stated fairly: the concentration axis is compressed at the top (copper at 0.8180 rather than 1.0; ASML at 0.7084; TSMC at 0.7010). The three clamped-under-FR-A nodes stop being tied at 1.0, but they are not distinguishable at the axis-max either. If the ship pass values *"copper is the outbound anchor, the concentration axis reads that clearly"* over *"minimize blast radius,"* FR-B is defensible on that ground alone — but the ship pass then owes the reader an explicit attribution for each of the 5 tier movements FR-B causes, particularly the 3 that FR-C would leave untouched.

**FR-B remains a legitimate alternative** if the ship pass author reads the dynamic-range argument as load-bearing. It is not the recommendation any more.

---

## Ledger — Pass T addendum

- **ASML tier under FR-B derived is `moderate`, not `high`.** Pass T Q9 was correct; the ledger sentence *"they stay high"* was wrong. Retracted.
- **FR-B causes 5 tier changes under derived boundaries, not 2.** The ledger sentence *"Net movement: 2 nodes drop under FR-B derived versus 4 under the current drift comparison"* had the direction inverted and the counts wrong. Retracted.
- **`applied_materials` is a genuine mover.** Under both FR-B and FR-C, AMAT's severity drops from 0.2015 to 0.1647 / 0.1347 respectively, and its tier drops from `moderate` to `none` under both candidates' derived boundaries. Outbound-dominant in both states.
- **Pass T Q8's flip condition was circular.** The K.2.2 §6.2 pattern's fifth instance. Replaced with a falsifiable condition: *"after FR-B ships, does any future pass's authoring push a node's raw outbound above `2.0447548854281186`?"* If yes, FR-B was tracking the max on a lagged schedule.
- **Revised recommendation: FR-C.** Smaller blast radius (2 vs 5), cleaner relationship to the K.1 warning, matches FR-B on ASML and AMAT movement. FR-B remains defensible on the dynamic-range argument alone; ship decision belongs to Weston.
- **Every claim in this addendum reads from `pass_t_facts.json` at commit `1dbdd46`.** No scoring change, no data change, no config change — the addendum is a reporting correction. Suite unchanged at 117 pass + 1 skipped + 0 xfail.
