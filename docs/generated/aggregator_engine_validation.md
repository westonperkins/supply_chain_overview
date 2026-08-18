# Aggregator engine validation — Pass M §2, §3

**MEASUREMENT ONLY.** Every number below is produced by running
`backend/scripts/aggregator_validation.py`, which drives candidate
aggregators through the REAL engine via the Pass M §2 seam
(`refresh_all_derived(..., aggregator_method=..., aggregator_eps=...,
min_suppliers_override=...)`). No committed artifact is regenerated
under a non-default setting. Intermediate data at
`docs/generated/aggregator_validation_data.json`.

Formula: `severity = concentration × (1 − substitutability) × lead_time`
with `lead_time = log10(years + 1) / log10(26)` per
`config/scoring.yaml`. Not `lt / 10` — the K.2.1 arithmetic error
K.2.2 §4.1 caught and corrected. Every number below uses the engine's
real formula.

## §2 candidate matrix (6 × 2)

Under HHI + default `normalize=true`, the six candidates evaluated
against the current committed graph, with each run at
`min_suppliers_for_concentration ∈ {2, 1}`:

- **hhi** — current committed (baseline)
- **noisy_or** — plain `1 − Π(1 − v_i)`
- **nor_eps_001** — noisy-OR with internal ε=0.01
- **nor_eps_005** — noisy-OR with internal ε=0.05
- **rms** — bounded RMS `sqrt(mean(v²))`

`min_suppliers=2` is current; `min_suppliers=1` is D4a.

### §3.1 Current graph — full 6 × 2 matrix

| candidate | tier histogram | seps | at 1.0 | ≥0.99 | median sev | boundaries (crit/high/mod) |
|---|---|---:|---:|---:|---:|---|
| **hhi_min2 (committed)** | 2c / 2h / 16m / 11n / 41u | 7 | 0 | 0 | 0.1950 | 0.5096 / 0.4119 / **0.1367** |
| hhi_min1 | 2c / 2h / 19m / 8n / 41u | 3 | 19 | 19 | — | 0.5096 / 0.4155 / **0.0** ← retry exhausts |
| noisy_or_min2 | 2c / 3h / 15m / 11n / 41u | 3 | 1 | 4 | — | 0.5178 / 0.4137 / 0.1771 |
| noisy_or_min1 | 2c / 3h / 17m / 9n / 41u | 3 | 2 | 6 | 0.2404 | 0.5178 / 0.4137 / 0.1771 |
| nor_eps_001_min2 | 2c / 3h / 15m / 11n / 41u | 3 | 0 | 4 | — | 0.5178 / 0.4137 / 0.1771 |
| **nor_eps_001_min1 (D4+D4a)** | 2c / 3h / 17m / 9n / 41u | 3 | 0 | 6 | 0.2404 | 0.5178 / 0.4137 / 0.1771 |
| nor_eps_005_min2 | 2c / 3h / 15m / 11n / 41u | 3 | 0 | 1 | — | 0.5178 / 0.4065 / 0.1771 |
| nor_eps_005_min1 | 2c / 3h / 17m / 9n / 41u | 3 | 0 | 1 | 0.2404 | 0.5178 / 0.4065 / 0.1771 |
| rms_min2 | 1c / 1h / 15m / 14n / 41u | 7 | 0 | 0 | — | 0.5041 / 0.3968 / 0.1092 |
| rms_min1 | 1c / 1h / 18m / 11n / 41u | 4 | 1 | 2 | — | 0.5041 / 0.3996 / **0.0** ← retry exhausts |

**Two meaningful degenerate cells (moderate=0.0 from retry exhaustion):**

- `hhi_min1` — dropping min_suppliers=1 under HHI reintroduces the
  HHI-normalizes-to-1 artefact for every single-source bucket, which
  creates 19 nodes at concentration exactly 1.0 and compresses the top
  of the distribution so the retry finds no candidate below the
  post-clustering median.
- `rms_min1` — RMS with single-source unzeroing produces a similar
  compression.

### §3.2 Xfail severities under each cell

| candidate | rf_power sev | HBM sev | rf_power > median? | HBM > median? |
|---|---:|---:|:---:|:---:|
| hhi_min2 (committed) | 0.0261 | 0.1779 | no | no (0.1779 < 0.1950) |
| noisy_or_min2 (D4 alone) | 0.0261 | 0.3008 | no | **yes** |
| noisy_or_min1 | 0.2872 | 0.3008 | **yes** | **yes** |
| nor_eps_001_min1 (D4+D4a) | 0.2872 | 0.3008 | **yes** | **yes** |
| nor_eps_005_min1 | 0.2872 | 0.3008 | **yes** | **yes** |

**Both xfails XPASS under D4+D4a paired.** Result matches K.2.2 §4
qualitative conclusion. Severity numbers match K.2.2's corrected
(log10_1p) figures: rf_power 0.2872, HBM 0.3008. ✓

### §3.3 NdFeB inbound concentration per candidate — the K.2.2 approximation check

Under min_supp=2 on the current graph (`product:ndfeb_magnets` input_to
bucket has 2 members ≥ min):

| candidate | ndfeb inbound | K.2.2 predicted | delta |
|---|---:|---:|---:|
| hhi | 0.5014 | 0.5014 | 0.0000 |
| noisy_or | 1.0000 | 1.0000 | 0.0000 |
| nor_eps_001 | **0.9990** | 0.9990 | 0.0000 |
| nor_eps_005 | **0.9950** | 0.9950 | 0.0000 |
| rms | **0.9513** | 0.9513 | 0.0000 |

**K.2.2's NdFeB predictions match the engine EXACTLY** (0.00% divergence).
The scalar computation on a single 2-input bucket doesn't involve the
per-stage / per-category logic, so the approximation was arithmetically
identical to the engine.

## §3.2 Projected graph (K.2.2 §2 dep-value overrides)

**23 edges overlaid** as scenario values from K.2.2 §2 candidate
authoring (0 unmatched — every override targets a real edge). Labelled
**projected** throughout; nothing written to `data/ai/edges.json`.

| candidate | tier histogram | seps | at 1.0 | ≥0.99 | rf_power | HBM | NdFeB |
|---|---|---:|---:|---:|---:|---:|---:|
| hhi_min2 | 2c / 3h / 15m / 11n / 41u | 4 | 0 | 0 | 0.0789 | 0.3865 | 0.1707 |
| hhi_min1 | 2c / 3h / 18m / 8n / 41u | 2 | 19 | 19 | 0.3191 | 0.3865 | 0.1707 |
| noisy_or_min2 | 2c / 3h / 16m / 10n / 41u | 2 | 1 | 4 | 0.0789 | 0.3865 | 0.3404 |
| noisy_or_min1 | 2c / 3h / 18m / 8n / 41u | 2 | 2 | 6 | 0.2872 | 0.3865 | 0.3404 |
| nor_eps_001_min1 | 2c / 3h / 18m / 8n / 41u | 2 | 0 | 6 | 0.2872 | 0.3865 | 0.3401 |
| nor_eps_005_min1 | 2c / 3h / 18m / 8n / 41u | 3 | 0 | 1 | 0.2872 | 0.3865 | 0.3387 |
| rms_min2 | 1c / 2h / 16m / 12n / 41u | 8 | 0 | 0 | 0.0789 | 0.3865 | 0.3238 |
| rms_min1 | 1c / 2h / 19m / 9n / 41u | 9 | 1 | 2 | 0.2872 | 0.3865 | 0.3238 |

**Projected saturation: 4–6 at ≥0.99 under noisy-OR variants.** K.2.2
§3.2.3 said "15–20 of 20 non-leaf scored nodes would sit at ≥ 0.99
after queued-29" — actual is **6 at most**, and only 2 at exactly 1.0.

Divergence: K.2.2's projection assumed dep values would cluster at 1.0
across the board. Honest §2.5 values are 0.75–0.95 for most co-critical
inputs, so they don't stack into saturation.

## §3.3 Divergence from K.2.2 approximation

Confirm/refute the five K.2.2 §3 claims:

| K.2.2 claim | K.2.2 value | engine measured | delta |
|---|---|---|---|
| NdFeB under noisy-OR ε=0.01 reads 0.9990 | 0.9990 | **0.9990** | **0.00%** ✓ |
| 2 nodes saturate today under plain noisy-OR | 2 | **1 at min_supp=2 (ndfeb); 2 at min_supp=1 (ndfeb + arm_core_ip)** | matches at min_supp=1; off by 1 at min_supp=2 |
| 15–20 of 20 non-leaf scored nodes saturate under projected | 15–20 | **6** at ≥0.99 (2 at 1.0) | **major divergence** — K.2.2 was 3–4× too high |
| 6 separating gaps under noisy-OR, 5 under ε=0.05 | 6 / 5 | **3 under both** (current graph, min_supp=2) | **halved** — divergence 50% |
| rf_power 0.2872 and HBM 0.3008 under D4+D4a | 0.2872 / 0.3008 | **0.2872 / 0.3008** | **0.00%** ✓ |

**Divergence bimodal.** Per-bucket concentration readings (NdFeB, xfail
severities) match K.2.2's corrected numbers **exactly** — the arithmetic
on isolated buckets was right. But **distribution-wide claims are
significantly off**:

- Projected saturation was 3–4× over-estimated (K.2.2 said 15–20; actual 6)
- Separating gap count halved from K.2.2's 6/5 to actual 3/3

Both distribution-wide errors came from K.2.2 treating the graph as if
noisy-OR would saturate everywhere under dep authoring. In reality:

1. Most Type A / B buckets stay at HHI-like readings under noisy-OR
   because per-stage/per-category logic runs first, and single-vendor-
   dominant stages don't cluster additional inputs.
2. The projected §2 authorings are 0.75–0.95, not 1.0, so noisy-OR
   stacking of 2 inputs gives ~0.99 not 1.0.

**Consequence for D4.** K.2.2's saturation concern was overstated —
plain noisy-OR at min_supp=2 saturates only ndfeb on the current graph
and only 2 nodes on the projected graph. ε=0.01 avoids even those 2.
The top-of-distribution collapse K.2.2 worried about does not
materialise.

## §3.4 Chokepoint landing table under D4+D4a (nor_eps_001_min1)

Compared against committed post-L (hhi_min2):

| chokepoint | severity | pre-M tier (hhi_min2) | post-M projection (nor_eps_001_min1) |
|---|---:|---|---|
| mineral:dysprosium | 0.5453→0.5618 | critical | critical |
| company:asml | 0.5389 | critical | critical |
| mineral:gallium | 0.4803→0.4876 | high | high |
| company:tsmc | 0.4693 | high | high |
| product:cowos_packaging | 0.3132→0.3296 | moderate | moderate |
| product:hbm | 0.1779→0.3008 | moderate | moderate |
| product:rf_power_semis | 0.0261→0.2872 | none | moderate |

**5 of 7 in moderate or above under D4+D4a on the current graph** —
HBM and RF & Power both land in moderate under the shifted median.
Neither XFAILS under the severity-above-median test because both now
exceed the new median 0.2404.

## §6 pre-registration scorecard for §3

| # | pre-registration | HIT / MISS |
|---|---|---|
| 1 | Engine-measured values diverge from K.2.2's approximation by a measurable amount | **HIT — bimodal.** Per-bucket concentrations 0.00% divergence; distribution-wide (saturation, gaps) 50–75% divergence. K.2.2's approximation caveat was over-weighted on per-bucket claims and under-weighted on distribution-wide claims. |
| 2 | At least one K.2.2 conclusion changes under engine measurement | **HIT** — K.2.2's saturation-count claim ("15–20 nodes at ≥0.99 projected") demoted to 6. K.2.2's gap count halved. NdFeB and xfail severities stand. |
| 4 | Under post-L derivation, at least one candidate produces a tier histogram materially different from K.2.2's pre-L numbers | **HIT** — K.2.2 reported the pre-L collapsed distribution as baseline (2c/2h/27m/0n). Under post-L retry (hhi_min2), baseline is 2c/2h/16m/11n. All candidate tier histograms measured against post-L baseline. |
