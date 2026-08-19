# Re-baseline candidate comparison — Pass T Phase A

Generated from `docs/generated/pass_t_facts.json`. Committed graph state is untouched; every candidate below is scored in-process against a candidate `fixed_reference`.

## Committed baseline

- Nodes / edges / scored: **72 / 259 / 31**
- `fixed_reference` (frozen): **1.6711394969**
- Boundaries (frozen): critical **0.5178454839**, high **0.4136848809**, moderate **0.1771110805**
- Aggregator: `noisy_or`, `eps_applied: None`

## Candidate summary

| id | label | `fixed_reference` | clamp | n clamped | axis flips | tier changes (frozen boundaries) | tier changes (derived boundaries) | min sev | median sev | max sev |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| FR-A | Status quo (ASML anchor, frozen K.1 value) | 1.6711394969 | on | 3 | 0 | 0 | 4 | 0.0036 | 0.2716 | 0.7097 |
| FR-B | Re-anchor to copper's current raw | 2.0447548854 | on | 0 | 1 | 2 | 5 | 0.0029 | 0.2627 | 0.7097 |
| FR-C | Headroom constant 2.5 | 2.5000000000 | on | 0 | 1 | 2 | 2 | 0.0024 | 0.2627 | 0.5805 |
| FR-D | Frozen value, clamp DISABLED | 1.6711394969 | off | 3 | 0 | 0 | 4 | 0.0036 | 0.2716 | 0.8684 |

## FR-A — Status quo (ASML anchor, frozen K.1 value)

- `fixed_reference` = **1.6711394969**
- clamp enabled: **True**
- Nodes clamped at this candidate: **3**
- Nodes whose dominant axis flipped vs committed: **0**
- Tier changes vs committed under FROZEN boundaries: **0**
- Tier changes vs committed under DERIVED boundaries (SF=3.0): **4**

### Per-node matrix under FR-A — scored nodes only

| node | inbound_hhi | outbound_raw | outbound_normalized | clamped | outbound_criticality | concentration | dominant_axis | severity | Δ vs committed | tier @ frozen |
|---|---:|---:|---:|---|---:|---:|---|---:|---:|---|
| company:applied_materials | 0.0000 | 1.1308 | 0.6767 | no | 0.6767 | 0.6767 | outbound | 0.201548 | 0.000000 | moderate |
| company:arm | 0.9900 | 0.7487 | 0.4480 | no | 0.4480 | 0.9900 | inbound | 0.210619 | 0.000000 | moderate |
| company:asml | 0.0000 | 1.7710 | 1.0597 | yes | 1.0000 | 1.0000 | outbound | 0.538942 | -0.000000 | critical |
| company:cadence | 0.0000 | 0.5903 | 0.3532 | no | 0.3532 | 0.3532 | outbound | 0.122139 | 0.000000 | none |
| company:canon | 0.0000 | 0.0295 | 0.0177 | no | 0.0177 | 0.0177 | outbound | 0.003572 | 0.000000 | none |
| company:ge_vernova | 0.9650 | 0.3040 | 0.1819 | no | 0.1819 | 0.9650 | inbound | 0.318416 | 0.000000 | moderate |
| company:hitachi_high_tech | 0.0000 | 0.0731 | 0.0438 | no | 0.0438 | 0.0438 | outbound | 0.008856 | 0.000000 | none |
| company:kla | 0.0000 | 1.6148 | 0.9663 | no | 0.9663 | 0.9663 | outbound | 0.267247 | 0.000000 | moderate |
| company:lam_research | 0.0000 | 1.5241 | 0.9120 | no | 0.9120 | 0.9120 | outbound | 0.271630 | -0.000000 | moderate |
| company:micron | 0.9500 | 0.1576 | 0.0943 | no | 0.0943 | 0.9500 | inbound | 0.242531 | -0.000000 | moderate |
| company:nikon | 0.0000 | 0.1390 | 0.0831 | no | 0.0831 | 0.0831 | outbound | 0.020781 | 0.000000 | none |
| company:nvidia | 0.9901 | 0.9026 | 0.5401 | no | 0.5401 | 0.9901 | inbound | 0.358088 | 0.000000 | moderate |
| company:quanta_services | 0.3000 | 0.2546 | 0.1524 | no | 0.1524 | 0.3000 | inbound | 0.076589 | 0.000000 | none |
| company:samsung | 0.9520 | 0.1468 | 0.0879 | no | 0.0879 | 0.9520 | inbound | 0.283543 | -0.000000 | moderate |
| company:siemens_eda | 0.0000 | 0.2214 | 0.1325 | no | 0.1325 | 0.1325 | outbound | 0.036634 | 0.000000 | none |
| company:siemens_energy | 0.9550 | 0.2853 | 0.1707 | no | 0.1707 | 0.9550 | inbound | 0.315116 | 0.000000 | moderate |
| company:sk_hynix | 0.9500 | 0.7106 | 0.4252 | no | 0.4252 | 0.9500 | inbound | 0.262741 | 0.000000 | moderate |
| company:synopsys | 0.0000 | 0.7379 | 0.4415 | no | 0.4415 | 0.4415 | outbound | 0.152674 | 0.000000 | none |
| company:tokyo_electron | 0.0000 | 0.5613 | 0.3359 | no | 0.3359 | 0.3359 | outbound | 0.092895 | 0.000000 | none |
| company:tsmc | 0.9901 | 1.7524 | 1.0486 | yes | 1.0000 | 1.0000 | outbound | 0.469282 | 0.000000 | high |
| company:vertiv | 0.4526 | 0.3447 | 0.2063 | no | 0.2063 | 0.4526 | inbound | 0.068676 | 0.000000 | none |
| mineral:copper | 0.6999 | 2.0448 | 1.2236 | yes | 1.0000 | 1.0000 | outbound | 0.709708 | 0.000000 | critical |
| mineral:dysprosium | 0.9902 | 0.6476 | 0.3875 | no | 0.3875 | 0.9902 | inbound | 0.561830 | 0.000000 | critical |
| mineral:gallium | 0.9852 | 0.6490 | 0.3884 | no | 0.3884 | 0.9852 | inbound | 0.487633 | 0.000000 | high |
| mineral:indium | 0.7108 | 0.0212 | 0.0127 | no | 0.0127 | 0.7108 | inbound | 0.119844 | 0.000000 | none |
| mineral:neodymium | 0.9190 | 0.7196 | 0.4306 | no | 0.4306 | 0.9190 | inbound | 0.295080 | 0.000000 | moderate |
| product:arm_core_ip | 1.0000 | 0.7657 | 0.4582 | no | 0.4582 | 1.0000 | inbound | 0.329964 | 0.000000 | moderate |
| product:cowos_packaging | 0.9525 | 0.8696 | 0.5204 | no | 0.5204 | 0.9525 | inbound | 0.329619 | 0.000000 | moderate |
| product:hbm | 0.7440 | 0.3866 | 0.2314 | no | 0.2314 | 0.7440 | inbound | 0.300754 | 0.000000 | moderate |
| product:ndfeb_magnets | 1.0000 | 0.2380 | 0.1424 | no | 0.1424 | 1.0000 | inbound | 0.340394 | 0.000000 | moderate |
| product:rf_power_semis | 0.9000 | 0.2475 | 0.1481 | no | 0.1481 | 0.9000 | inbound | 0.287207 | -0.000000 | moderate |

### Boundary derivation for FR-A (SF=3.0)

- Median adjacent gap: 0.0131436986
- Separating threshold (3.0 × median): 0.0394310959
- Separating gaps: 4
- Boundaries: critical **0.6357690338**, high **0.5132875334**, moderate **0.1771110805**
- Tier histogram under DERIVED boundaries: {'moderate': 18, 'none': 10, 'high': 2, 'critical': 1, 'unscored': 41}
- Tier histogram under FROZEN boundaries: {'high': 2, 'none': 10, 'moderate': 16, 'critical': 3, 'unscored': 41}

#### Nodes moving tier vs committed under DERIVED boundaries

| node | severity (candidate) | tier committed | tier derived |
|---|---:|---|---|
| mineral:gallium | 0.4876 | high | moderate |
| mineral:dysprosium | 0.5618 | critical | high |
| company:tsmc | 0.4693 | high | moderate |
| company:asml | 0.5389 | critical | high |

### Cluster-cut check for FR-A (against derived boundaries)

| boundary | value | nearest below | Δ below | nearest above | Δ above | inside cluster? |
|---|---:|---:|---:|---:|---:|---|
| critical | 0.6357690338 | 0.5618 | 0.0739 | 0.7097 | 0.0739 | no |
| high | 0.5132875334 | 0.4876 | 0.0257 | 0.5389 | 0.0257 | no |
| moderate | 0.1771110805 | 0.1527 | 0.0244 | 0.2015 | 0.0244 | no |

### `separation_factor` sensitivity for FR-A

| SF | critical | high | moderate | n separating | n unresolved | tier histogram |
|---:|---:|---:|---:|---:|---:|---|
| 2.0 | 0.635769 | 0.513288 | 0.226575 | 8 | 0 | {'moderate': 16, 'none': 12, 'high': 2, 'critical': 1, 'unscored': 41} |
| 2.5 | 0.635769 | 0.513288 | 0.177111 | 4 | 0 | {'moderate': 18, 'none': 10, 'high': 2, 'critical': 1, 'unscored': 41} |
| 3.0 | 0.635769 | 0.513288 | 0.177111 | 4 | 0 | {'moderate': 18, 'none': 10, 'high': 2, 'critical': 1, 'unscored': 41} |
| 3.5 | 0.635769 | 0.513288 | 0.177111 | 4 | 0 | {'moderate': 18, 'none': 10, 'high': 2, 'critical': 1, 'unscored': 41} |
| 4.0 | 0.635769 | 0.413685 | 0.000000 | 2 | 1 | {'high': 4, 'moderate': 26, 'critical': 1, 'unscored': 41} |

## FR-B — Re-anchor to copper's current raw

- `fixed_reference` = **2.0447548854**
- clamp enabled: **True**
- Nodes clamped at this candidate: **0**
- Nodes whose dominant axis flipped vs committed: **1**
- Tier changes vs committed under FROZEN boundaries: **2**
- Tier changes vs committed under DERIVED boundaries (SF=3.0): **5**

### Per-node matrix under FR-B — scored nodes only

| node | inbound_hhi | outbound_raw | outbound_normalized | clamped | outbound_criticality | concentration | dominant_axis | severity | Δ vs committed | tier @ frozen |
|---|---:|---:|---:|---|---:|---:|---|---:|---:|---|
| company:applied_materials | 0.0000 | 1.1308 | 0.5530 | no | 0.5530 | 0.5530 | outbound | 0.164721 | -0.036827 | none |
| company:arm | 0.9900 | 0.7487 | 0.3662 | no | 0.3662 | 0.9900 | inbound | 0.210619 | 0.000000 | moderate |
| company:asml | 0.0000 | 1.7710 | 0.8661 | no | 0.8661 | 0.8661 | outbound | 0.466781 | -0.072160 | high |
| company:cadence | 0.0000 | 0.5903 | 0.2887 | no | 0.2887 | 0.2887 | outbound | 0.099822 | -0.022317 | none |
| company:canon | 0.0000 | 0.0295 | 0.0144 | no | 0.0144 | 0.0144 | outbound | 0.002919 | -0.000653 | none |
| company:ge_vernova | 0.9650 | 0.3040 | 0.1487 | no | 0.1487 | 0.9650 | inbound | 0.318416 | 0.000000 | moderate |
| company:hitachi_high_tech | 0.0000 | 0.0731 | 0.0358 | no | 0.0358 | 0.0358 | outbound | 0.007238 | -0.001618 | none |
| company:kla | 0.0000 | 1.6148 | 0.7897 | no | 0.7897 | 0.7897 | outbound | 0.218416 | -0.048831 | moderate |
| company:lam_research | 0.0000 | 1.5241 | 0.7454 | no | 0.7454 | 0.7454 | outbound | 0.221998 | -0.049632 | moderate |
| company:micron | 0.9500 | 0.1576 | 0.0771 | no | 0.0771 | 0.9500 | inbound | 0.242531 | -0.000000 | moderate |
| company:nikon | 0.0000 | 0.1390 | 0.0680 | no | 0.0680 | 0.0680 | outbound | 0.016984 | -0.003797 | none |
| company:nvidia | 0.9901 | 0.9026 | 0.4414 | no | 0.4414 | 0.9901 | inbound | 0.358088 | 0.000000 | moderate |
| company:quanta_services | 0.3000 | 0.2546 | 0.1245 | no | 0.1245 | 0.3000 | inbound | 0.076589 | 0.000000 | none |
| company:samsung | 0.9520 | 0.1468 | 0.0718 | no | 0.0718 | 0.9520 | inbound | 0.283543 | -0.000000 | moderate |
| company:siemens_eda | 0.0000 | 0.2214 | 0.1083 | no | 0.1083 | 0.1083 | outbound | 0.029940 | -0.006694 | none |
| company:siemens_energy | 0.9550 | 0.2853 | 0.1395 | no | 0.1395 | 0.9550 | inbound | 0.315116 | 0.000000 | moderate |
| company:sk_hynix | 0.9500 | 0.7106 | 0.3475 | no | 0.3475 | 0.9500 | inbound | 0.262741 | 0.000000 | moderate |
| company:synopsys | 0.0000 | 0.7379 | 0.3609 | no | 0.3609 | 0.3609 | outbound | 0.124778 | -0.027896 | none |
| company:tokyo_electron | 0.0000 | 0.5613 | 0.2745 | no | 0.2745 | 0.2745 | outbound | 0.075921 | -0.016974 | none |
| company:tsmc | 0.9901 | 1.7524 | 0.8570 | no | 0.8570 | 0.9901 | inbound | 0.464636 | -0.004646 | high |
| company:vertiv | 0.4526 | 0.3447 | 0.1686 | no | 0.1686 | 0.4526 | inbound | 0.068676 | 0.000000 | none |
| mineral:copper | 0.6999 | 2.0448 | 1.0000 | no | 1.0000 | 1.0000 | outbound | 0.709708 | 0.000000 | critical |
| mineral:dysprosium | 0.9902 | 0.6476 | 0.3167 | no | 0.3167 | 0.9902 | inbound | 0.561830 | 0.000000 | critical |
| mineral:gallium | 0.9852 | 0.6490 | 0.3174 | no | 0.3174 | 0.9852 | inbound | 0.487633 | 0.000000 | high |
| mineral:indium | 0.7108 | 0.0212 | 0.0104 | no | 0.0104 | 0.7108 | inbound | 0.119844 | 0.000000 | none |
| mineral:neodymium | 0.9190 | 0.7196 | 0.3519 | no | 0.3519 | 0.9190 | inbound | 0.295080 | 0.000000 | moderate |
| product:arm_core_ip | 1.0000 | 0.7657 | 0.3745 | no | 0.3745 | 1.0000 | inbound | 0.329964 | 0.000000 | moderate |
| product:cowos_packaging | 0.9525 | 0.8696 | 0.4253 | no | 0.4253 | 0.9525 | inbound | 0.329619 | 0.000000 | moderate |
| product:hbm | 0.7440 | 0.3866 | 0.1891 | no | 0.1891 | 0.7440 | inbound | 0.300754 | 0.000000 | moderate |
| product:ndfeb_magnets | 1.0000 | 0.2380 | 0.1164 | no | 0.1164 | 1.0000 | inbound | 0.340394 | 0.000000 | moderate |
| product:rf_power_semis | 0.9000 | 0.2475 | 0.1210 | no | 0.1210 | 0.9000 | inbound | 0.287207 | -0.000000 | moderate |

### Boundary derivation for FR-B (SF=3.0)

- Median adjacent gap: 0.0120798399
- Separating threshold (3.0 × median): 0.0362395197
- Separating gaps: 6
- Boundaries: critical **0.6357690338**, high **0.5247316525**, moderate **0.1876700318**
- Tier histogram under DERIVED boundaries: {'moderate': 18, 'none': 11, 'high': 1, 'critical': 1, 'unscored': 41}
- Tier histogram under FROZEN boundaries: {'high': 3, 'none': 11, 'moderate': 15, 'critical': 2, 'unscored': 41}

#### Nodes moving tier vs committed under DERIVED boundaries

| node | severity (candidate) | tier committed | tier derived |
|---|---:|---|---|
| mineral:gallium | 0.4876 | high | moderate |
| mineral:dysprosium | 0.5618 | critical | high |
| company:tsmc | 0.4646 | high | moderate |
| company:asml | 0.4668 | critical | moderate |
| company:applied_materials | 0.1647 | moderate | none |

### Cluster-cut check for FR-B (against derived boundaries)

| boundary | value | nearest below | Δ below | nearest above | Δ above | inside cluster? |
|---|---:|---:|---:|---:|---:|---|
| critical | 0.6357690338 | 0.5618 | 0.0739 | 0.7097 | 0.0739 | no |
| high | 0.5247316525 | 0.4876 | 0.0371 | 0.5618 | 0.0371 | no |
| moderate | 0.1876700318 | 0.1647 | 0.0229 | 0.2106 | 0.0229 | no |

### `separation_factor` sensitivity for FR-B

| SF | critical | high | moderate | n separating | n unresolved | tier histogram |
|---:|---:|---:|---:|---:|---:|---|
| 2.0 | 0.635769 | 0.524732 | 0.187670 | 6 | 0 | {'moderate': 18, 'none': 11, 'high': 1, 'critical': 1, 'unscored': 41} |
| 2.5 | 0.635769 | 0.524732 | 0.187670 | 6 | 0 | {'moderate': 18, 'none': 11, 'high': 1, 'critical': 1, 'unscored': 41} |
| 3.0 | 0.635769 | 0.524732 | 0.187670 | 6 | 0 | {'moderate': 18, 'none': 11, 'high': 1, 'critical': 1, 'unscored': 41} |
| 3.5 | 0.635769 | 0.524732 | 0.187670 | 4 | 0 | {'moderate': 18, 'none': 11, 'high': 1, 'critical': 1, 'unscored': 41} |
| 4.0 | 0.635769 | 0.524732 | 0.000000 | 3 | 1 | {'moderate': 29, 'high': 1, 'critical': 1, 'unscored': 41} |

## FR-C — Headroom constant 2.5

- `fixed_reference` = **2.5000000000**
- clamp enabled: **True**
- Nodes clamped at this candidate: **0**
- Nodes whose dominant axis flipped vs committed: **1**
- Tier changes vs committed under FROZEN boundaries: **2**
- Tier changes vs committed under DERIVED boundaries (SF=3.0): **2**

### Per-node matrix under FR-C — scored nodes only

| node | inbound_hhi | outbound_raw | outbound_normalized | clamped | outbound_criticality | concentration | dominant_axis | severity | Δ vs committed | tier @ frozen |
|---|---:|---:|---:|---|---:|---:|---|---:|---:|---|
| company:applied_materials | 0.0000 | 1.1308 | 0.4523 | no | 0.4523 | 0.4523 | outbound | 0.134726 | -0.066822 | none |
| company:arm | 0.9900 | 0.7487 | 0.2995 | no | 0.2995 | 0.9900 | inbound | 0.210619 | 0.000000 | moderate |
| company:asml | 0.0000 | 1.7710 | 0.7084 | no | 0.7084 | 0.7084 | outbound | 0.381781 | -0.157160 | moderate |
| company:cadence | 0.0000 | 0.5903 | 0.2361 | no | 0.2361 | 0.2361 | outbound | 0.081645 | -0.040495 | none |
| company:canon | 0.0000 | 0.0295 | 0.0118 | no | 0.0118 | 0.0118 | outbound | 0.002387 | -0.001184 | none |
| company:ge_vernova | 0.9650 | 0.3040 | 0.1216 | no | 0.1216 | 0.9650 | inbound | 0.318416 | 0.000000 | moderate |
| company:hitachi_high_tech | 0.0000 | 0.0731 | 0.0293 | no | 0.0293 | 0.0293 | outbound | 0.005920 | -0.002936 | none |
| company:kla | 0.0000 | 1.6148 | 0.6459 | no | 0.6459 | 0.6459 | outbound | 0.178643 | -0.088604 | moderate |
| company:lam_research | 0.0000 | 1.5241 | 0.6096 | no | 0.6096 | 0.6096 | outbound | 0.181573 | -0.090058 | moderate |
| company:micron | 0.9500 | 0.1576 | 0.0630 | no | 0.0630 | 0.9500 | inbound | 0.242531 | -0.000000 | moderate |
| company:nikon | 0.0000 | 0.1390 | 0.0556 | no | 0.0556 | 0.0556 | outbound | 0.013891 | -0.006890 | none |
| company:nvidia | 0.9901 | 0.9026 | 0.3610 | no | 0.3610 | 0.9901 | inbound | 0.358088 | 0.000000 | moderate |
| company:quanta_services | 0.3000 | 0.2546 | 0.1019 | no | 0.1019 | 0.3000 | inbound | 0.076589 | 0.000000 | none |
| company:samsung | 0.9520 | 0.1468 | 0.0587 | no | 0.0587 | 0.9520 | inbound | 0.283543 | -0.000000 | moderate |
| company:siemens_eda | 0.0000 | 0.2214 | 0.0885 | no | 0.0885 | 0.0885 | outbound | 0.024488 | -0.012146 | none |
| company:siemens_energy | 0.9550 | 0.2853 | 0.1141 | no | 0.1141 | 0.9550 | inbound | 0.315116 | 0.000000 | moderate |
| company:sk_hynix | 0.9500 | 0.7106 | 0.2842 | no | 0.2842 | 0.9500 | inbound | 0.262741 | 0.000000 | moderate |
| company:synopsys | 0.0000 | 0.7379 | 0.2951 | no | 0.2951 | 0.2951 | outbound | 0.102056 | -0.050618 | none |
| company:tokyo_electron | 0.0000 | 0.5613 | 0.2245 | no | 0.2245 | 0.2245 | outbound | 0.062096 | -0.030799 | none |
| company:tsmc | 0.9901 | 1.7524 | 0.7010 | no | 0.7010 | 0.9901 | inbound | 0.464636 | -0.004646 | high |
| company:vertiv | 0.4526 | 0.3447 | 0.1379 | no | 0.1379 | 0.4526 | inbound | 0.068676 | 0.000000 | none |
| mineral:copper | 0.6999 | 2.0448 | 0.8179 | no | 0.8179 | 0.8179 | outbound | 0.580472 | -0.129236 | critical |
| mineral:dysprosium | 0.9902 | 0.6476 | 0.2590 | no | 0.2590 | 0.9902 | inbound | 0.561830 | 0.000000 | critical |
| mineral:gallium | 0.9852 | 0.6490 | 0.2596 | no | 0.2596 | 0.9852 | inbound | 0.487633 | 0.000000 | high |
| mineral:indium | 0.7108 | 0.0212 | 0.0085 | no | 0.0085 | 0.7108 | inbound | 0.119844 | 0.000000 | none |
| mineral:neodymium | 0.9190 | 0.7196 | 0.2878 | no | 0.2878 | 0.9190 | inbound | 0.295080 | 0.000000 | moderate |
| product:arm_core_ip | 1.0000 | 0.7657 | 0.3063 | no | 0.3063 | 1.0000 | inbound | 0.329964 | 0.000000 | moderate |
| product:cowos_packaging | 0.9525 | 0.8696 | 0.3478 | no | 0.3478 | 0.9525 | inbound | 0.329619 | 0.000000 | moderate |
| product:hbm | 0.7440 | 0.3866 | 0.1547 | no | 0.1547 | 0.7440 | inbound | 0.300754 | 0.000000 | moderate |
| product:ndfeb_magnets | 1.0000 | 0.2380 | 0.0952 | no | 0.0952 | 1.0000 | inbound | 0.340394 | 0.000000 | moderate |
| product:rf_power_semis | 0.9000 | 0.2475 | 0.0990 | no | 0.0990 | 0.9000 | inbound | 0.287207 | -0.000000 | moderate |

### Boundary derivation for FR-C (SF=3.0)

- Median adjacent gap: 0.0146219902
- Separating threshold (3.0 × median): 0.0438659706
- Separating gaps: 3
- Boundaries: critical **0.5247316525**, high **0.4232086793**, moderate **0.1566844355**
- Tier histogram under DERIVED boundaries: {'high': 2, 'none': 11, 'moderate': 16, 'critical': 2, 'unscored': 41}
- Tier histogram under FROZEN boundaries: {'high': 2, 'none': 11, 'moderate': 16, 'critical': 2, 'unscored': 41}

#### Nodes moving tier vs committed under DERIVED boundaries

| node | severity (candidate) | tier committed | tier derived |
|---|---:|---|---|
| company:asml | 0.3818 | critical | moderate |
| company:applied_materials | 0.1347 | moderate | none |

### Cluster-cut check for FR-C (against derived boundaries)

| boundary | value | nearest below | Δ below | nearest above | Δ above | inside cluster? |
|---|---:|---:|---:|---:|---:|---|
| critical | 0.5247316525 | 0.4876 | 0.0371 | 0.5618 | 0.0371 | no |
| high | 0.4232086793 | 0.3818 | 0.0414 | 0.4646 | 0.0414 | no |
| moderate | 0.1566844355 | 0.1347 | 0.0220 | 0.1786 | 0.0220 | no |

### `separation_factor` sensitivity for FR-C

| SF | critical | high | moderate | n separating | n unresolved | tier histogram |
|---:|---:|---:|---:|---:|---:|---|
| 2.0 | 0.524732 | 0.423209 | 0.156684 | 5 | 0 | {'high': 2, 'none': 11, 'moderate': 16, 'critical': 2, 'unscored': 41} |
| 2.5 | 0.524732 | 0.423209 | 0.156684 | 4 | 0 | {'high': 2, 'none': 11, 'moderate': 16, 'critical': 2, 'unscored': 41} |
| 3.0 | 0.524732 | 0.423209 | 0.156684 | 3 | 0 | {'high': 2, 'none': 11, 'moderate': 16, 'critical': 2, 'unscored': 41} |
| 3.5 | 0.524732 | 0.423209 | 0.000000 | 2 | 1 | {'high': 2, 'moderate': 27, 'critical': 2, 'unscored': 41} |
| 4.0 | 0.524732 | 0.423209 | 0.000000 | 2 | 1 | {'high': 2, 'moderate': 27, 'critical': 2, 'unscored': 41} |

## FR-D — Frozen value, clamp DISABLED

- `fixed_reference` = **1.6711394969**
- clamp enabled: **False**
- Nodes clamped at this candidate: **3**
- Nodes whose dominant axis flipped vs committed: **0**
- Tier changes vs committed under FROZEN boundaries: **0**
- Tier changes vs committed under DERIVED boundaries (SF=3.0): **4**

### Per-node matrix under FR-D — scored nodes only

| node | inbound_hhi | outbound_raw | outbound_normalized | clamped | outbound_criticality | concentration | dominant_axis | severity | Δ vs committed | tier @ frozen |
|---|---:|---:|---:|---|---:|---:|---|---:|---:|---|
| company:applied_materials | 0.0000 | 1.1308 | 0.6767 | no | 0.6767 | 0.6767 | outbound | 0.201548 | 0.000000 | moderate |
| company:arm | 0.9900 | 0.7487 | 0.4480 | no | 0.4480 | 0.9900 | inbound | 0.210619 | 0.000000 | moderate |
| company:asml | 0.0000 | 1.7710 | 1.0597 | yes | 1.0597 | 1.0597 | outbound | 0.571139 | 0.032198 | critical |
| company:cadence | 0.0000 | 0.5903 | 0.3532 | no | 0.3532 | 0.3532 | outbound | 0.122139 | 0.000000 | none |
| company:canon | 0.0000 | 0.0295 | 0.0177 | no | 0.0177 | 0.0177 | outbound | 0.003572 | 0.000000 | none |
| company:ge_vernova | 0.9650 | 0.3040 | 0.1819 | no | 0.1819 | 0.9650 | inbound | 0.318416 | 0.000000 | moderate |
| company:hitachi_high_tech | 0.0000 | 0.0731 | 0.0438 | no | 0.0438 | 0.0438 | outbound | 0.008856 | 0.000000 | none |
| company:kla | 0.0000 | 1.6148 | 0.9663 | no | 0.9663 | 0.9663 | outbound | 0.267247 | 0.000000 | moderate |
| company:lam_research | 0.0000 | 1.5241 | 0.9120 | no | 0.9120 | 0.9120 | outbound | 0.271630 | -0.000000 | moderate |
| company:micron | 0.9500 | 0.1576 | 0.0943 | no | 0.0943 | 0.9500 | inbound | 0.242531 | -0.000000 | moderate |
| company:nikon | 0.0000 | 0.1390 | 0.0831 | no | 0.0831 | 0.0831 | outbound | 0.020781 | 0.000000 | none |
| company:nvidia | 0.9901 | 0.9026 | 0.5401 | no | 0.5401 | 0.9901 | inbound | 0.358088 | 0.000000 | moderate |
| company:quanta_services | 0.3000 | 0.2546 | 0.1524 | no | 0.1524 | 0.3000 | inbound | 0.076589 | 0.000000 | none |
| company:samsung | 0.9520 | 0.1468 | 0.0879 | no | 0.0879 | 0.9520 | inbound | 0.283543 | -0.000000 | moderate |
| company:siemens_eda | 0.0000 | 0.2214 | 0.1325 | no | 0.1325 | 0.1325 | outbound | 0.036634 | 0.000000 | none |
| company:siemens_energy | 0.9550 | 0.2853 | 0.1707 | no | 0.1707 | 0.9550 | inbound | 0.315116 | 0.000000 | moderate |
| company:sk_hynix | 0.9500 | 0.7106 | 0.4252 | no | 0.4252 | 0.9500 | inbound | 0.262741 | 0.000000 | moderate |
| company:synopsys | 0.0000 | 0.7379 | 0.4415 | no | 0.4415 | 0.4415 | outbound | 0.152674 | 0.000000 | none |
| company:tokyo_electron | 0.0000 | 0.5613 | 0.3359 | no | 0.3359 | 0.3359 | outbound | 0.092895 | 0.000000 | none |
| company:tsmc | 0.9901 | 1.7524 | 1.0486 | yes | 1.0486 | 1.0486 | outbound | 0.492099 | 0.022817 | high |
| company:vertiv | 0.4526 | 0.3447 | 0.2063 | no | 0.2063 | 0.4526 | inbound | 0.068676 | 0.000000 | none |
| mineral:copper | 0.6999 | 2.0448 | 1.2236 | yes | 1.2236 | 1.2236 | outbound | 0.868377 | 0.158669 | critical |
| mineral:dysprosium | 0.9902 | 0.6476 | 0.3875 | no | 0.3875 | 0.9902 | inbound | 0.561830 | 0.000000 | critical |
| mineral:gallium | 0.9852 | 0.6490 | 0.3884 | no | 0.3884 | 0.9852 | inbound | 0.487633 | 0.000000 | high |
| mineral:indium | 0.7108 | 0.0212 | 0.0127 | no | 0.0127 | 0.7108 | inbound | 0.119844 | 0.000000 | none |
| mineral:neodymium | 0.9190 | 0.7196 | 0.4306 | no | 0.4306 | 0.9190 | inbound | 0.295080 | 0.000000 | moderate |
| product:arm_core_ip | 1.0000 | 0.7657 | 0.4582 | no | 0.4582 | 1.0000 | inbound | 0.329964 | 0.000000 | moderate |
| product:cowos_packaging | 0.9525 | 0.8696 | 0.5204 | no | 0.5204 | 0.9525 | inbound | 0.329619 | 0.000000 | moderate |
| product:hbm | 0.7440 | 0.3866 | 0.2314 | no | 0.2314 | 0.7440 | inbound | 0.300754 | 0.000000 | moderate |
| product:ndfeb_magnets | 1.0000 | 0.2380 | 0.1424 | no | 0.1424 | 1.0000 | inbound | 0.340394 | 0.000000 | moderate |
| product:rf_power_semis | 0.9000 | 0.2475 | 0.1481 | no | 0.1481 | 0.9000 | inbound | 0.287207 | -0.000000 | moderate |

### Boundary derivation for FR-D (SF=3.0)

- Median adjacent gap: 0.0115582982
- Separating threshold (3.0 × median): 0.0346748947
- Separating gaps: 4
- Boundaries: critical **0.7197581350**, high **0.5269646959**, moderate **0.1771110805**
- Tier histogram under DERIVED boundaries: {'moderate': 18, 'none': 10, 'high': 2, 'critical': 1, 'unscored': 41}
- Tier histogram under FROZEN boundaries: {'high': 2, 'none': 10, 'moderate': 16, 'critical': 3, 'unscored': 41}

#### Nodes moving tier vs committed under DERIVED boundaries

| node | severity (candidate) | tier committed | tier derived |
|---|---:|---|---|
| mineral:gallium | 0.4876 | high | moderate |
| mineral:dysprosium | 0.5618 | critical | high |
| company:tsmc | 0.4921 | high | moderate |
| company:asml | 0.5711 | critical | high |

### Cluster-cut check for FR-D (against derived boundaries)

| boundary | value | nearest below | Δ below | nearest above | Δ above | inside cluster? |
|---|---:|---:|---:|---:|---:|---|
| critical | 0.7197581350 | 0.5711 | 0.1486 | 0.8684 | 0.1486 | no |
| high | 0.5269646959 | 0.4921 | 0.0349 | 0.5618 | 0.0349 | no |
| moderate | 0.1771110805 | 0.1527 | 0.0244 | 0.2015 | 0.0244 | no |

### `separation_factor` sensitivity for FR-D

| SF | critical | high | moderate | n separating | n unresolved | tier histogram |
|---:|---:|---:|---:|---:|---:|---|
| 2.0 | 0.719758 | 0.526965 | 0.226575 | 8 | 0 | {'moderate': 16, 'none': 12, 'high': 2, 'critical': 1, 'unscored': 41} |
| 2.5 | 0.719758 | 0.526965 | 0.226575 | 7 | 0 | {'moderate': 16, 'none': 12, 'high': 2, 'critical': 1, 'unscored': 41} |
| 3.0 | 0.719758 | 0.526965 | 0.177111 | 4 | 0 | {'moderate': 18, 'none': 10, 'high': 2, 'critical': 1, 'unscored': 41} |
| 3.5 | 0.719758 | 0.526965 | 0.177111 | 4 | 0 | {'moderate': 18, 'none': 10, 'high': 2, 'critical': 1, 'unscored': 41} |
| 4.0 | 0.719758 | 0.526965 | 0.177111 | 4 | 0 | {'moderate': 18, 'none': 10, 'high': 2, 'critical': 1, 'unscored': 41} |

## Max-path outbound walk experiment

**Null hypothesis:** max-of-paths: A's raw contribution to D holds at sqrt(direct_influence² + (w_ab×decay)²) while indirect_influence < direct_influence, then rises when the indirect (decay-adjusted) influence exceeds the direct.

**Parameters fixed:** {'w_direct': 0.2, 'w_ab': 0.9, 'decay': 0.7}
**Decay-adjusted crossover (`w_bd_critical` = `w_direct` / (`w_ab` × `decay`)):** 0.3174603175

| w_bd | direct_influence | indirect_influence | indirect > direct? | A_raw_outbound |
|---:|---:|---:|---|---:|
| 0.05 | 0.140000 | 0.022050 | no | 0.645368 |
| 0.10 | 0.140000 | 0.044100 | no | 0.645368 |
| 0.20 | 0.140000 | 0.088200 | no | 0.645368 |
| 0.30 | 0.140000 | 0.132300 | no | 0.645368 |
| 0.32 | 0.140000 | 0.141120 | yes | 0.645612 |
| 0.35 | 0.140000 | 0.154350 | yes | 0.648632 |
| 0.40 | 0.140000 | 0.176400 | yes | 0.654230 |
| 0.50 | 0.140000 | 0.220500 | yes | 0.667473 |
| 0.70 | 0.140000 | 0.308700 | yes | 0.701567 |
| 0.90 | 0.140000 | 0.396900 | yes | 0.744600 |
| 0.95 | 0.140000 | 0.418950 | yes | 0.756584 |

**Verdict:** `max_of_paths_confirmed`

## Reproducibility check (§6(6))

- FR-A: 0 mismatches on a second independent run
- FR-B: 0 mismatches on a second independent run
- FR-C: 0 mismatches on a second independent run
- FR-D: 0 mismatches on a second independent run

