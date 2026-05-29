---
artifact: A8_T1_STRUCTURAL_SPEC_v1_0.md
document: A8 — T1 Structural Facts Specification
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed: include everything A-AI; per-category two-pass declared in schema)
intended_for: Claude Code sub-agents implementing the A8 T1 structural writer
prime_directive: Only computed facts. Classical structural composites = deterministic predicate evaluations of A1-A7 atoms against G12/G13/G17 global rules. No narrative, no opinion.
depends_on: A1-A7 (all atomic positions, panchanga, sensitive points, vargas, dashas), G12 yoga library (200+), G13 dosha library, G17 aspect rules, G18 friendship reference, G19 karaka assignments
---

# A8 — T1 Structural Facts Specification

## §0 — Mission

For each chart per ayanamsha, compute every classical structural composite — every deterministic fact derived by evaluating classical predicates (from G12/G13/G17) against A1-A7 atoms. Output is pure FACT (no interpretation). Per-category two-pass verification declared in `CHART_FACTS_SCHEMA.json`. ~2,000-2,500 rows per (chart, ayanamsha).

## §1 — Locked decisions

**10 clarification answers (final):**
- Q1: Full quarter-strength Parashari model (1.0/0.75/0.5/0.25 per aspect type)
- Q2: 10° default orb for `conjunction_within_orb`
- Q3: All 200+ yogas from G12 fire-checked in default A8 pass
- Q4: All classical yoga cancellation rules (BPHS + Phaladeepika)
- Q5: BOTH BPHS canonical + Raman variant functional benefic/malefic tables via `formula_id`
- Q6: All 30 karakatva significances analyzed (G19 full set)
- Q7: BOTH BPHS-weighted + simple-multiplication graha-in-house strength formulas via `formula_id`
- Q8: Disposer chain emitted until cycle detected (variable depth)
- Q9: Anubindu calculations included (post-Trikona, post-Ekadhipathya residual)
- Q10: Explicit Mahapurusha yoga strength bonus value per BPHS formula

**Additions A-AI (all included; AG cross-referenced, AF skipped):**
A, B, C, G, I, J, K, L, O, P, Q, R, T, V, W, X, Y, Z, AB, AD, AE, AH, AI, AJ, AK — all IN.
AG (Tajik Hadda strengths) — cross-reference A6, no duplicate emission.
AF (Saturn-Jupiter mundane marker) — skip (not per-chart).

## §2 — Categories A8 emits (~35 categories)

### Group A — Aspects (6 categories)

- `aspect_parashari_given` — per graha; subject = `<GRAHA>`; per-target row with `aspect_strength` ∈ {1.0/0.75/0.5/0.25}, `aspect_orb_deg`, `mutual_aspect_flag`, `formula_id`
- `aspect_parashari_received` — inverse view per graha/house
- `aspect_jaimini` — Rasi-drishti 12×12 matrix; fixed-sign rules per Jaimini Sutram Ch.4
- `aspect_tajik` — 5 Tajik aspect types (Ithasala, Eesarpha, Nakta, Yamaya, Manaau)
- `conjunction_within_orb` — graha conjunctions; default orb 10°; emits per-pair row with `orb_deg`, `applying_or_separating`
- `aspect_matrix_summary` — composite rollup per house: total aspects received, dominant aspecting graha, net benefic/malefic balance

### Group B — Shadbala (8 categories + W amplification)

- 6 sub-balas: `graha_shadbala_sthana / dig / kala / cheshta / naisargika / drik`
- `graha_shadbala_total` — sum + rank + required + surplus/deficit
- `graha_ishta_phala`, `graha_kashta_phala`
- `graha_vargottama_amplification_factor` (Addition W) — explicit BPHS multiplier when graha is vargottama
- `graha_saptavargaja_bala_component` (Addition V) — pulls from A6 `varga_saptavargaja_bala_component` and rolls into Sthana bala

### Group C — Bhava Bala (7 categories + composite house strengths)

- 6 sub-balas per house + `house_bhava_bala_total`
- `house_strength_classification_rollup` — strong/weak/normal per house; kendra-strength composite; trikona-strength composite; dushtana-strength composite

### Group D — Ashtakavarga (8 categories incl. Anubindu)

- `ashtakavarga_bindu` — 8 × 12 = 96 BAV cells per ayanamsha
- `ashtakavarga_pinda_sodhita`, `_bhinna`, `_sarva`
- `ashtakavarga_kakshya` — 8 zones per graha
- `ashtakavarga_trikona_shodhana`, `_ekadhipathya_shodhana`
- `ashtakavarga_anubindu` (Q9 = A) — residual bindus after both shodhana steps; classical refinement

### Group E — Vimsopaka (4 categories)

- `graha_vimsopaka_shadvarga / saptavarga / dasavarga / shodasavarga` — consumed from A6's per-varga emissions

### Group F — Yogas firing (200+ from G12)

- `yoga_fires` — per fired yoga: `yoga_name`, `constituent_facts_array`, `classical_citation_id`, `yoga_strength_score` (Addition AI), `yoga_arudha_attribution` (Addition J — which constituent contributes most), `cancellation_flag` (Addition I), `cancelled_by_yoga_name`, `mahapurusha_strength_bonus` (Addition AE; explicit BPHS bonus value for Pancha Mahapurusha yogas only)

### Group G — Doshas firing

- `dosha_fires` — per fired dosha; same shape as yoga_fires; cancellation rules applied

### Group H — Avasthas (5 schemes × 9 grahas + lifetime exposure)

- `graha_avastha_baladi / jagrad / deepta / lajjitadi / sayanadi`
- `graha_avastha_lifetime_exposure_summary` (Addition AB) — precomputed per-graha-per-avastha period count over 1950-2100 from A7 dasha timeline × A8 avastha state at each period

### Group I — Composite per-graha-per-house strength (Q7 + Addition Q)

- `graha_in_house_composite_strength` — TWO formula_id rows per (graha, house):
  - `bphs_weighted` — classical formula combining (dignity × shadbala_total × house_bhava_bala_total × aspect_modifier)
  - `simple_multiplication` — for cross-tradition validation

### Group J — Functional benefic/malefic (Q5 — BOTH tables emitted)

- `graha_functional_class_per_ascendant` — TWO formula_id rows per graha:
  - `bphs_canonical` (12 Lagna table per BPHS)
  - `raman_variant` (BV Raman's variant)
- Plus `graha_yoga_karaka_flag` (Addition R) — graha as lord of 9th + 10th from Lagna

### Group K — Karakatva analysis (Q6 = A; all 30 significances)

- `karakatva_strength_per_significance` — per significance (30 entries per G19): natural_karaka_graha + composite (karaka's strength + karaka's house + karaka's aspects)
- `karaka_house_lord_overlap_flag` (Addition Z) — true when natural karaka of a house IS also that house's Lagna lord

### Group L — Structural relationships (Additions K, L, AH, X)

- `graha_dispositor_chain` (Addition K, Q8 = C — until cycle detected) — per graha, full chain of sign-lords stored as `chain_jsonb_atomic` with `cycle_detected_at_step_N`
- `composite_dispositor_strength` (Addition AH) — chain-terminal graha's strength rolled back to chain origin
- `parivartana_pairs` (Addition L) — mutual receptions between grahas; emitted as one row per pair with `parivartana_type` (Maha/Khala/Dainya per BPHS Ch.27)
- `graha_composite_state_classification` (Addition X) — combust + retrograde + debilitated → categorical state per graha (well-placed / weak / afflicted / canceled-debilitation / debilitation-cancelled-by-aspect)

### Group M — Special states (Addition T + Y)

- `graha_special_state_rollup` — combust count, retrograde flag, debilitated-but-mooltrikona flag, exalted-but-vargottama flag, etc.
- `graha_effective_dignity_modified_by_aspects` (Addition Y) — graha's effective dignity adjusted by benefic/malefic aspects per BPHS Ch.6

### Group N — Argala (Addition P; moved from A17 supplementary to A8 per native maximalist directive)

- `argala_natal_matrix` — 12×12: for each sign, which signs have argala (intervention) on it (positions 2/4/5/11 from the sign; argala from natural malefics is negative)
- `virodha_argala_natal_matrix` — counter-intervention matrix (positions 12/10/9/3)

### Group O — Esoteric / Jaimini specials (Additions AJ, AK)

- `pranic_strength_per_graha` (Addition AJ) — esoteric Nadi-tradition composite (graha's effective prana per breath-cycle); two-pass against G44 Nadi reference
- `jaimini_tri_deva_role_per_graha` (Addition AK) — Brahma/Vishnu/Shiva role assignment per Jaimini Sutram Ch.2; consumed from A5 esoteric_point_brahma/vishnu/shiva
- `graha_tri_deva_role_strength` — composite strength under tri-deva role

## §3 — Verification (per-category, declared in CHART_FACTS_SCHEMA.json)

Mandatory `two_pass_verified` minimum:

| Category | Primary | Secondary | Tertiary |
|---|---|---|---|
| `aspect_parashari_*` + `_jaimini` + `_tajik` | Engine geometric derivation | Independent G17 rule application | Algebraic invariants (matrix symmetry where applicable) |
| `graha_shadbala_*` | Engine 6-sub-bala formulas | Independent classical re-derivation per BPHS Ch.27-32 | Sage Parashara worked example match |
| `graha_vargottama_amplification_factor` | BPHS multiplier rule | Algebraic check | — |
| `house_bhava_bala_*` | Engine 4-sub-bala formulas | Independent | — |
| `ashtakavarga_bindu` + reductions + anubindu | Engine BAV computation | Independent BPHS table re-application | Sodhita pinda sum invariants |
| `yoga_fires` + cancellation + arudha + strength | G12 predicate evaluation | Independent classical-rule re-derivation | Classical worked-example matching (Sage Parashara's chart, BV Raman 300 Combinations) |
| `dosha_fires` | G13 predicate evaluation | Independent | — |
| `graha_avastha_*` | Engine 5-scheme formulas | Independent classical re-derivation | BPHS Ch.45 examples |
| `graha_in_house_composite_strength` | BPHS-weighted formula | Simple-multiplication formula (Q7 = C; both emitted) | Cross-formula divergence stored in `cross_formula_divergence` field |
| `karakatva_strength_per_significance` | Engine composite | Independent G19 rule application | — |
| `graha_dispositor_chain` | Engine chain walk | Cycle-detection independent re-walk | — |
| `parivartana_pairs` | Engine pair scan | Independent | — |
| `argala_natal_matrix` | Engine Jaimini argala rule | Independent G17 rule application | Jaimini Sutram Ch.5 example match |
| `pranic_strength_per_graha` | Nadi composite | Independent G44 cross-check | — |

Single (deterministic):
- `conjunction_within_orb` (geometric)

## §4 — Row count projection per (chart, ayanamsha)

| Group | Rows |
|---|---|
| Aspects (4 matrices + conjunction + summary) | ~250 |
| Shadbala (8 cats + V + W) | ~80 |
| Bhava Bala (7 + composites) | ~100 |
| Ashtakavarga (8 cats incl. Anubindu) | ~250 |
| Vimsopaka | ~28 |
| Yoga fires (200+ checks; ~40 typically fire per chart with full constituents + strength) | ~600 |
| Dosha fires | ~30 |
| Avasthas (5 × 9 grahas) + lifetime exposure | ~100 |
| Composite graha-in-house strength (BOTH formulas × 9 × 12) | ~216 |
| Functional benefic/malefic (BOTH × 9 grahas) | ~18 |
| Karakatva (30 significances) | ~60 |
| Dispositor chains (9 grahas × ~5 chain depth avg) | ~50 |
| Parivartana pairs | ~10 |
| Composite state classifications | ~30 |
| Argala + Virodha matrices | ~144 (12×12) × 2 = ~288 |
| Special state rollups | ~50 |
| Pranic + tri-deva (esoteric) | ~30 |

**Total per (chart, ayanamsha): ~2,200 rows. × 5 ayanamshas = ~11,000 per chart.**

## §5 — Citations (dual form)

Examples:

| Row | citation_ref | citation_human |
|---|---|---|
| Mars aspect on Leo | `aspect_parashari_given.MAR-LEO.aspect_strength@chart=...:ay=lahiri:...` | "Mars 4th aspect on Leo at strength 0.75 (Lahiri)." |
| Saturn shadbala total | `graha_shadbala_total.SAT.rupa@chart=...:ay=lahiri:...` | "Saturn's total shadbala: 4.19 rupa (110% of 3.79 required, surplus, Lahiri)." |
| Hamsa Mahapurusha yoga firing | `yoga_fires.HAMSA_MAHAPURUSHA.constituents@...:ay=lahiri:...` | "Hamsa Mahapurusha yoga fires; constituent: Jupiter in 4H Cancer (own sign, kendra); strength score 0.92 (Lahiri)." |
| Sun-Moon Parivartana | `parivartana_pairs.SUN-MOON.parivartana_type@...:ay=lahiri:...` | "Sun-Moon Maha-parivartana (mutual reception in own signs, Lahiri)." |
| Saturn debilitation cancelled | `graha_composite_state_classification.SAT.classification@...:ay=lahiri:...` | "Saturn debilitation cancelled by strong dispositor; effective state: well-placed (Lahiri)." |
| Argala on 7H | `argala_natal_matrix.HOUSE_7.argala_from_signs_jsonb@...:ay=lahiri:...` | "7th house Argala received from signs 8/10/11/5 (Lahiri)." |

## §6 — Materialized views

- `mv_chart_yogas_fired_summary` — joins yoga_fires + cancellation flags + strength scores into one wide row per fired yoga (natal-fixed; refresh at build close)
- `mv_chart_shadbala_summary` — already in A3 §10
- `mv_chart_bhava_bala_summary` — already in A3 §10
- `mv_chart_ashtakavarga_summary` — already in A3 §10
- `mv_chart_aspect_matrix` — pre-computed aspect matrix in compact form for fast "show me all aspects" queries
- `mv_chart_t1_composite_strengths` — joins composite graha-in-house strengths (both formulas) for fast retrieval

## §7 — Tool retrieval contract

- `query_t1_aspects(chart_id, ayanamsha_id, mode='matrix'|'per_graha'|'per_house')` → rows
- `query_t1_shadbala(chart_id, ayanamsha_id)` → 7 rows wide
- `query_t1_yogas_fired(chart_id, ayanamsha_id, scope='all'|'mahapurusha'|'raja'|'dhan'|'vipareeta'|'cancellation')` → rows
- `query_t1_doshas_fired(chart_id, ayanamsha_id)` → rows
- `query_t1_avasthas(chart_id, ayanamsha_id, scheme='baladi'|'jagrad'|'deepta'|'lajjitadi'|'sayanadi'|'all')` → rows
- `query_t1_composite_strengths(chart_id, ayanamsha_id, graha?, house?, formula='bphs'|'simple'|'both')` → rows
- `query_t1_karakatva(chart_id, ayanamsha_id, significance)` → composite strength + supporting facts

## §8 — Data flow boundaries

A8 CONSUMES (all from chart_facts via SQL joins at write time):
- A1: `graha_position`, `graha_dignity_per_varga`, `graha_combustion`, `graha_retrogression`, `graha_special_flags`
- A4: `tara_bala_natal_baseline`, `chandra_bala_natal_baseline` (for some yoga predicates)
- A5: `karaka_chara_position`, `karakamsa_position`, `swamsa_position`, `esoteric_point_brahma/vishnu/shiva`
- A6: `varga_dignity`, `varga_vargottama_flag`, `varga_saptavargaja_bala_component`, `varga_vimsopaka_contribution`
- A7: `chart_dashas` (for `triggered_yogas_jsonb_atomic` cross-reference back to dasha periods)
- G12: yoga predicates + cancellation rules
- G13: dosha predicates
- G17: aspect rules + special drishtis
- G18: friendship reference
- G19: karaka assignments

A8 PRODUCES rows that downstream:
- A10 MSR — every yoga firing → MSR signal; composite strengths feed salience computation
- A11 CDLM — cross-domain cells reference fired yogas + doshas
- A12 CGM — aspect matrices + dispositor chains form edges
- A13 RM — weakest grahas (by shadbala) feed remedy candidates
- A14 UCN — top yogas by strength feed signature digest

## §9 — Implementation notes

1. Yoga firing pass: pre-compile G12 yoga predicates into Python predicate functions; evaluate against chart_facts JOIN at write time
2. Cancellation pass: AFTER initial firing pass, apply cancellation rules from G12; mark cancelled yogas as `cancellation_flag=true`
3. Yoga strength scoring: per fired yoga, composite of (constituents' shadbala + dignity + house position) per Phaladeepika weighting
4. Disposer chain (Q8 = C): walk until graha's sign lord is itself OR cycle detected; emit chain with `cycle_detected_at_step_N`
5. Argala matrices: pre-compute 12×12 lookup once per chart; emit as 144-row natal_matrix category
6. Two-pass verification: implement per-category secondary algorithm; halt build on tolerance breach
7. Composite per-graha-per-house strength (Q7 = C): emit BOTH formula_id rows; LLM panel can use either or both based on tradition preference
8. Functional benefic/malefic (Q5 = C): emit BOTH BPHS + Raman tables; let downstream pick

## §10 — Locked decisions

1. ~35 fact_categories spanning aspects, shadbala, bhava bala, ashtakavarga, vimsopaka, yogas, doshas, avasthas, composites, structural relationships, special states, argala, esoteric
2. ~2,200 rows per (chart, ayanamsha); ~11,000 per chart × 5 ayanamshas
3. Per-category two-pass methodology declared in CHART_FACTS_SCHEMA.json
4. All 10 clarification answers locked per §1
5. All additions A-AI included (AG cross-references A6; AF skipped)
6. 6 MVs (natal-fixed, refresh at build close)
7. Tool retrieval contract defines 7 distinct query surfaces

---

*End of A8_T1_STRUCTURAL_SPEC_v1_0.md — LOCKED 2026-05-29. Native sign-off complete.*
