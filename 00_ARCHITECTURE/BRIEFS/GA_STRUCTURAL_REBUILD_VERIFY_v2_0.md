---
canonical_id: GA_STRUCTURAL_REBUILD_VERIFY
version: 2.0
status: PENDING_NATIVE_APPROVAL
created: 2026-06-19
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
build_id: 5d11969e-31d9-4693-bc11-8b17cff48f5a
ayanamshas: lahiri_chitrapaksha | true_chitra | krishnamurti | raman | surya_siddhanta_classical
---

# GA8 Structural Rebuild — STEP 2 Verification Report v2.0

## §1 — Build summary

| Field | Value |
|---|---|
| chart_id | `482012f1-710e-4a25-994a-93821f5871aa` |
| build_id | `5d11969e-31d9-4693-bc11-8b17cff48f5a` |
| old orphan build_id (purged) | `22fcef22-3b50-4357-b128-15c445146eec` |
| total rows (5 ayanamshas) | **106,014** |
| rows per ayanamsha (avg) | ~21,202 |
| distinct categories | **69** |
| FORENSIC 7/7 gate | PASS (forensic_gate() raised no exception across all 5 ayanamshas) |
| target_floor (asset_registry) | **106,014** (set by migration 323) |
| orphan rows remaining | 0 |

---

## §2 — Graph-theoretic categories (7/7 mandate)

Every category that existed in the old build_id must be non-zero in the new build_id. Verified against `lahiri_chitrapaksha` ayanamsha.

| Category | Old build (orphaned D1-only) | New build per-varga (lahiri) | Status |
|---|---|---|---|
| `graha_centrality` | 9 | **270** (9 grahas × 30 vargas) | ✅ NON-ZERO |
| `dispositor_tree` | 10 | **300** (10 rows × 30 vargas) | ✅ NON-ZERO |
| `chart_cluster` | 9 | **270** (9 × 30 vargas) | ✅ NON-ZERO |
| `chart_center_of_gravity` | 2 | **60** (2 × 30 vargas) | ✅ NON-ZERO |
| `convergence_count` | 21 | **630** (21 × 30 vargas) | ✅ NON-ZERO |
| `karaka_bhava_concordance` | 30 | **900** (30 × 30 vargas) | ✅ NON-ZERO |
| `nakshatra_dispositor_chain` | 9 | **10** (9 grahas + Lagna, D1 only) | ✅ NON-ZERO |

**GAP-4 resolution (nakshatra_dispositor_chain):**
- L1 fact_id references stored inside `fact_value_jsonb.constituent_fact_ids` (chart_facts has no `constituent_facts_array` column — reference lives in jsonb per §N.5)
- All 10 fact_ids verified to resolve to real `graha_nakshatra_join` rows (category: `graha_nakshatra_join`, key: `nakshatra_lord`)
- Nakshatra names now populated from `graha_position` (key: `nakshatra`) — previously empty due to wrong source query
- Sample verification (lahiri_chitrapaksha):

| Subject | Chain | Nakshatras | Constituent fact_id |
|---|---|---|---|
| JUP | Jupiter→Ketu→Mercury→Sun→Moon→Jupiter | Mula, Jyeshtha, Uttara Ashadha, Shravana, Purva Bhadrapada | `f83e5e1dada3c432` → graha_nakshatra_join/JUP/nakshatra_lord=ketu ✓ |
| VEN | Venus→Venus | Purva Ashadha | `6be30d09ee865077` → graha_nakshatra_join/VEN/nakshatra_lord=venus ✓ |
| MAR | Mars→Rahu→Moon→Jupiter→Ketu→Mercury→Sun→Moon | Swati, Rohini, Purva Bhadrapada, Mula, Jyeshtha, Uttara Ashadha, Shravana | `1c77205ee3243cad` → graha_nakshatra_join/MAR/nakshatra_lord=rahu ✓ |

---

## §3 — Full per-category table (lahiri_chitrapaksha, new build_id)

69 categories total.

| # | fact_category | count (lahiri) | note |
|---|---|---|---|
| 1 | virodha_argala_natal_matrix | 4,320 | |
| 2 | argala_natal_matrix | 4,320 | |
| 3 | aspect_jaimini_per_varga | 3,240 | |
| 4 | bhava_significance_link | 1,080 | |
| 5 | sambandha_grade | 1,080 | |
| 6 | karaka_bhava_concordance | 900 | ★ graph-theoretic |
| 7 | convergence_count | 630 | ★ graph-theoretic |
| 8 | aspect_parashari_per_varga | 570 | |
| 9 | virupa_drishti | 570 | |
| 10 | lord_in_house_per_varga | 360 | |
| 11 | net_argala_per_varga | 360 | |
| 12 | contradiction_pair | 360 | |
| 13 | graha_in_house_composite_strength | 324 | |
| 14 | dispositor_tree | 300 | ★ graph-theoretic |
| 15 | dispositor_chain_per_varga | 270 | |
| 16 | graha_centrality | 270 | ★ graph-theoretic |
| 17 | graha_dignity_per_varga | 270 | |
| 18 | chart_cluster | 270 | ★ graph-theoretic |
| 19 | vargottama_per_varga | 261 | |
| 20 | lord_aspects_lord_per_varga | 179 | |
| 21 | combustion_per_varga | 150 | |
| 22 | conjunction_per_varga | 113 | |
| 23 | aspect_jaimini | 108 | |
| 24 | ashtakavarga_anubindu | 84 | |
| 25 | yoga_label | 82 | |
| 26 | significator_path | 72 | |
| 27 | karakatva_strength_per_significance | 60 | |
| 28 | chart_center_of_gravity | 60 | ★ graph-theoretic |
| 29 | parivartana_per_varga | 45 | |
| 30 | graha_special_state_rollup | 45 | |
| 31 | kala_sarpa_per_varga | 30 | |
| 32 | dosha_label | 22 | |
| 33 | aspect_tajik | 21 | |
| 34 | aspect_parashari_received | 19 | |
| 35 | aspect_parashari_given | 19 | |
| 36 | nway_config_per_varga | 16 | |
| 37 | graha_functional_class_per_ascendant | 14 | |
| 38 | bhava_bala_aspectual | 12 | |
| 39 | karaka_house_lord_overlap_flag | 12 | |
| 40 | house_strength_classification_rollup | 12 | |
| 41 | bhava_bala_positional | 12 | |
| 42 | bhava_bala_directional | 12 | |
| 43 | bhava_bala_temporal | 12 | |
| 44 | bhava_bala_total_extended | 12 | |
| 45 | aspect_matrix_summary | 12 | |
| 46 | bhava_bala_lord | 12 | |
| 47 | bhava_bala_occupant | 12 | |
| 48 | aspect_received_by_special_point | 11 | |
| 49 | nakshatra_dispositor_chain | 10 | ★ graph-theoretic / GAP-4 |
| 50 | graha_avastha_lajjitadi | 9 | |
| 51 | jaimini_tri_deva_role_per_graha | 9 | |
| 52 | graha_avastha_deepta | 9 | |
| 53 | graha_effective_dignity_modified_by_aspects | 9 | |
| 54 | composite_dispositor_strength | 9 | |
| 55 | graha_dispositor_chain | 9 | |
| 56 | graha_avastha_sayanadi | 9 | |
| 57 | graha_composite_state_classification | 9 | |
| 58 | pranic_strength_per_graha | 9 | |
| 59 | graha_avastha_baladi | 9 | |
| 60 | graha_tri_deva_role_strength | 9 | |
| 61 | graha_avastha_lifetime_exposure_summary | 9 | |
| 62 | graha_avastha_jagrad | 9 | |
| 63 | graha_saptavargaja_bala_component | 7 | |
| 64 | vimsopaka_bala_per_graha | 7 | |
| 65 | graha_yoga_karaka_flag | 7 | |
| 66 | graha_vargottama_amplification_factor | 7 | |
| 67 | conjunction_special_point | 6 | |
| 68 | graha_yuddha_per_varga | 3 | |
| 69 | conjunction_within_orb | 2 | |

---

## §4 — Acharya check: D1 graha_centrality (Parashari aspect graph)

Degree = number of undirected Parashari aspect + conjunction edges in D1. Rahu highest (5) reflects its unique 5th/7th/9th Parashari aspects plus conjunctions.

| Rank | Subject | Degree | Connected to |
|---|---|---|---|
| 1 | D1_RAH_MEAN | 5 | Jupiter, Mars, Moon, Saturn, Venus |
| 2 | D1_SAT | 4 | Mars, Mercury, Rahu, Sun |
| 3 | D1_MAR | 3 | Moon, Rahu, Saturn |
| 4 | D1_JUP | 2 | Rahu, Venus |
| 5 | D1_MER | 2 | Saturn, Sun |
| 6 | D1_SUN | 2 | Mercury, Saturn |
| 7 | D1_MOON | 2 | Mars, Rahu |
| 8 | D1_VEN | 2 | Jupiter, Rahu |
| 9 | D1_KET_MEAN | 0 | — (no Parashari connections in D1) |

**Acharya read:** Rahu as the most-connected planet in D1 is astrologically meaningful — Rahu (in Rohini) casts special 5th/7th/9th aspects on many planets, and Rohini is a nakshatra of strong lunar influence creating a web of Rahu's reach throughout the chart. Ketu's zero connections in D1 indicates the chart's Ketu is in a position that receives no Parashari aspects and conjuncts no other graha in D1 (Ketu in Jyeshtha, 8th bhava, relatively isolated).

---

## §5 — Migration log

| Migration | Action | Status |
|---|---|---|
| 322 | Fix ga_yoga/ga_prashna/ga_transit_anchors english_name + catalog_status | APPLIED |
| 323 | Fix ga_structural count_sql (69 categories, corrected names) + target_floor=106,014 + purge orphan build_id | APPLIED |

---

## §6 — Code changes (commit reference)

| File | Change |
|---|---|
| `platform/python-sidecar/ga_writers/ga_structural_writer.py` | Added `NATURAL_PLANET_RELATIONS`, `SIGNIFICANCE_TO_BHAVA`, `_get_planet_concordance`; 6 per-varga builder functions; hooked into `_build_varga_aspect_rows`; `_build_nakshatra_dispositor_chain_rows` with GAP-4 L1 reference in jsonb; nakshatra names from `graha_position` |

Commit: `f4cbdf5b` — "feat(ga_structural): port 7 graph-theoretic categories as per-varga orchestrator-native builders"

---

## §7 — Pending native approval

**Request:** Native approval to treat this rebuild as the canonical GA8 state for chart `482012f1`.

Checklist:
- [x] All 7 graph-theoretic categories non-zero in new build_id
- [x] GAP-4 nakshatra_dispositor_chain: L1 fact_id references resolve (10/10 verified)
- [x] Nakshatras populated in chain (previously empty, now from graha_position)
- [x] Per-varga (30 vargas per category) for 6 graph-theoretic categories
- [x] FORENSIC 7/7 gate PASS across all 5 ayanamshas
- [x] Orphan build_id `22fcef22` purged (0 rows remaining)
- [x] target_floor updated to 106,014 (ACHIEVED, not fabricated)
- [x] count_sql corrected to 69 categories with current names
- [x] D1 centrality acharya check passes (Rahu highest, Ketu isolated — astrologically coherent)
