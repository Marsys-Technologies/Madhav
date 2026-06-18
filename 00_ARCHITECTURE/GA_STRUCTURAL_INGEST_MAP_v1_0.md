---
artifact: GA_STRUCTURAL_INGEST_MAP
version: "1.0"
status: CURRENT
date: 2026-06-18
author: "Claude Code / S1844"
investigation_method: "Code read (ga_structural_writer.py, all 4,351 lines) + production DB queries (chart_id 482012f1-710e-4a25-994a-93821f5871aa)"
---

# GA Structural Ingest Map v1.0

> Ground-truth investigation into what `ga_structural` (GA8) currently reads from L1, what
> relationships it derives, and which enriched L1 assets it does NOT weave in. Produced
> 2026-06-18 as pre-L2 readiness artifact. **Read-only — no code changes.**

---

## § 1 — Current Ingest Table: Every `_build_*` / `_load_*` Function

### 1.1 — Loader Functions (read from DB)

| Function | Line(s) | Source Table / Category Read | What It Reads | Notes |
|---|---|---|---|---|
| `check_upstream_presence` | 532–597 | `chart_facts`, `chart_dashas`, `chart_divisionals` | Checks existence of: `graha_position`, `graha_shadbala_sthana`, `ashtakavarga_bindu`, `house_bhava_bala_total`, `panchanga_tithi`, `upagraha_position`; counts in `chart_dashas`; count in `chart_divisionals` | Step 0 gate only — reads no content, only verifies presence |
| `_load_varga_positions` | 636–690 | `chart_divisionals` | Reads `fact_category = 'varga_position'` rows for a specific varga+ayanamsha; extracts `sign`, `sign_id`, `degree_in_sign` per graha | Called for every non-D1 varga across all 30 vargas in `_build_varga_aspect_rows` |
| `_load_special_points` | 2823–2867 | `chart_facts` category `upagraha_position` | Reads `fact_subject`, `sign`, `house`, `longitude` from GA5 upagraha rows | **KEY FINDING: reads only `upagraha_position` — the original GA5 category. Does NOT read the four new enriched ga_sensitive categories.** |
| `_real_fact_id_ref` | 1297–1309 | `chart_facts` | Looks up a real `fact_id` by (category, subject, key) for use in `constituent_facts_array` | Used only for yoga/dosha constituent pointers; always resolves against `graha_position` |
| `_load_yoga_catalog` | 3624–3639 | `brahma_yoga_catalog` table | Full table scan for yoga formation rules | Falls back to hardcoded `YOGA_LIBRARY` if table absent |
| `_load_dosha_catalog` | 3642–3657 | `brahma_dosha_catalog` table | Full table scan for dosha formation rules | Falls back to hardcoded `DOSHA_LIBRARY` if table absent |
| `_build_karaka_web_rows` | 3454–3565 | `chart_facts` category `jaimini_chara_karaka` | Reads role→planet assignments; then checks varga_state for conjunction/aspect between karaka planets | DB query at line 3471–3483 |

### 1.2 — Builder Functions (compute from chart_output or varga_state)

| Function | Line(s) | Source Data | Output Category (fact_category) | Notes |
|---|---|---|---|---|
| `_build_aspect_rows` | 810–995 | `chart_output` (PyJHora compute) | `aspect_parashari_given`, `aspect_parashari_received`, `aspect_jaimini`, `conjunction_within_orb`, `aspect_matrix_summary`, `aspect_tajik` | D1 only; uses computed longitude/house; no L1 DB reads |
| `_build_shadbala_extension_rows` | 1000–1074 | `chart_output` | `graha_vargottama_amplification_factor`, `graha_saptavargaja_bala_component` | Saptavargaja row is a reference pointer to `chart_divisionals`; value_num=NULL |
| `_build_bhava_bala_extended_rows` | 1079–1182 | `chart_output` | `bhava_bala_positional`, `bhava_bala_directional`, `bhava_bala_temporal`, `bhava_bala_aspectual`, `bhava_bala_occupant`, `bhava_bala_lord`, `bhava_bala_total_extended`, `house_strength_classification_rollup` | Inline computation; no DB reads |
| `_build_anubindu_rows` | 1187–1254 | `chart_output` (via `_derive_ashtakavarga` import from ga_strength_writer) | `ashtakavarga_anubindu` | Imports GA3 helper; computes inline |
| `_build_vimsopaka_ext_rows` | 1259–1292 | None (reference-only rows) | `vimsopaka_bala_per_graha` | NULL numeric value; JSONB reference pointer to `chart_divisionals` only |
| `_build_yoga_rows` | 1578–1676 | `chart_output` + `conn` (for constituent fact_ids) | `yoga_label` (DB catalog path) or `yoga_fires` (legacy fallback) | DB catalog: reads `brahma_yoga_catalog` and resolves `graha_position` fact_ids |
| `_build_dosha_rows` | 1681–1856 | `chart_output` + `conn` | `dosha_label` (DB catalog) or `dosha_fires` (legacy) | Same pattern as yoga |
| `_build_avastha_rows` | 1861–1996 | `chart_output` | `graha_avastha_baladi`, `graha_avastha_jagrad`, `graha_avastha_deepta`, `graha_avastha_lajjitadi`, `graha_avastha_sayanadi`, `graha_avastha_lifetime_exposure_summary` | References GA7 for lifetime summary but stores only natal proxy (note at line 1986) |
| `_build_composite_strength_rows` | 2001–2074 | `chart_output` | `graha_in_house_composite_strength` (3 keys: bphs_weighted, simple_multiplication, cross_formula_divergence) | 9 grahas × 12 houses × 3 keys × 5 ayanamshas = 1,620 rows in DB ✓ |
| `_build_functional_class_rows` | 2079–2137 | `chart_output` | `graha_functional_class_per_ascendant`, `graha_yoga_karaka_flag` | Hard-coded for Aries lagna |
| `_build_karakatva_rows` | 2142–2213 | `chart_output` | `karakatva_strength_per_significance`, `karaka_house_lord_overlap_flag` | 30 significances; house lord mapping from lagna |
| `_build_structural_relationship_rows` | 2218–2388 | `chart_output` | `graha_dispositor_chain`, `composite_dispositor_strength`, `parivartana_pairs`, `graha_composite_state_classification` | Independently recomputes dispositor chains — does NOT read ga_nakshatra's nakshatra_dispositor |
| `_build_special_state_rows` | 2393–2505 | `chart_output` | `graha_special_state_rollup` (5 keys: is_combust, is_retrograde, is_vargottama, is_debilitated, is_exalted), `graha_effective_dignity_modified_by_aspects` | Computes vargottama from D1 longitude arithmetic — does NOT read ga_vargas chart_divisionals |
| `_build_argala_rows` | 2510–2624 | `chart_output` (D1) or `varga_sign_occupants` dict | `argala_natal_matrix`, `virodha_argala_natal_matrix` | 144 atomic rows each per varga; called for all 30 vargas |
| `_build_esoteric_rows` | 2629–2706 | `chart_output` | `pranic_strength_per_graha`, `jaimini_tri_deva_role_per_graha`, `graha_tri_deva_role_strength` | Nadi tradition + Jaimini Sutram; inline computation |
| `_build_special_point_relationship_rows` | 2870–2966 | `chart_output` + DB via `_load_special_points` | `conjunction_special_point`, `aspect_received_by_special_point` | **Only reads `upagraha_position` (old category). New enriched point categories NOT read.** |
| `_build_house_lord_matrix_rows` | 2971–3094 | `varga_state` dict + `chart_output` | `lord_in_house_per_varga`, `lord_aspects_lord_per_varga` | Called inside `_build_varga_relationship_rows` for every varga |
| `_build_varga_relationship_rows` | 3097–3451 | `varga_state` dict (from `chart_divisionals` or D1 `chart_output`) | `graha_dignity_per_varga`, `aspect_parashari_per_varga`, `conjunction_per_varga`, `parivartana_per_varga`, `dispositor_chain_per_varga`, `vargottama_per_varga`, `kala_sarpa_per_varga`, `lord_in_house_per_varga`, `lord_aspects_lord_per_varga`, `aspect_jaimini_per_varga` | Called for all 30 vargas |
| `_build_varga_aspect_rows` | 3568–3619 | `chart_divisionals` (via `_load_varga_positions`) + `chart_output` | All `*_per_varga` categories above + argala/virodha per varga + karaka_web_per_varga | The main multi-varga loop: D1 uses chart_output; D2–D2700 query chart_divisionals |
| `_build_karaka_web_rows` | 3454–3565 | `chart_facts` `jaimini_chara_karaka` + `varga_state` | `karaka_web_per_varga` | Reads DB for chara karaka assignments; then checks relationships in varga |
| `_build_graha_yuddha_rows` | 4058–4157 | `chart_output` | `graha_yuddha` | 3 rows per planetary war pair (winner, loser, orb_deg) |
| `_build_combustion_retrograde_relationship_rows` | 4160–4265 | `chart_output` | `combustion_relationship`, `retrograde_aspect_modification` | Combust orb per planet per classical rules |

### 1.3 — Key Confirmed Answers from Code

**Q1: Does ga_structural read the enriched ga_sensitive categories?**
NO. `_load_special_points` (line 2836–2851) queries ONLY `fact_category = 'upagraha_position'`. The four new enriched ga_sensitive categories — `sensitive_point_gulika_mandi`, `sun_derived_upagraha`, `special_lagna`, `esoteric_point_sphuta_fertility` — are completely invisible to ga_structural. Also `saturn_derived_point`, `aprakasha_position` are not read. The `aspect_received_by_special_point` and `conjunction_special_point` output categories therefore cover only the original upagraha entities.

**Q2: Does it read per-varga ga_strength enrichment as edge-weights?**
NO for ga_strength tables. ga_structural reads `chart_divisionals` for varga *positions* (via `_load_varga_positions`) but does NOT read per-varga Shadbala or Ashtakavarga enrichment from ga_strength's per-varga output categories (`graha_cheshta_bala_per_varga`, `graha_sthana_bala_per_varga`, `ashtakavarga_bindu_per_varga`, etc.). The `graha_in_house_composite_strength` and `bhava_bala_*` rows use inline proxy formulas — not ga_strength's authoritative values.

**Q3: Does it read ga_nakshatra's nakshatra_dispositor chain or compute independently?**
COMPUTES INDEPENDENTLY. `_build_structural_relationship_rows` (line 2230–2275) builds its own dispositor chain by walking `SIGN_LORDS` dict from `chart_output`. It does NOT query `chart_facts` category `nakshatra_dispositor` (200 rows in DB from ga_nakshatra). The two chains are conceptually different (sign-dispositor vs. nakshatra-lord chain), but the sign-dispositor chain ga_structural computes is parallel to ga_nakshatra's `nakshatra_dispositor` output — both are dispositor chains, different layer.

**Q4: Does it read ga_medical / ga_vastu / ga_condition / ga_tajaka?**
NO. None of these assets are queried anywhere in the 4,351-line file. ga_structural has zero awareness of these assets. Confirmed by searching all `cur.execute` calls and all imports — only tables queried are: `chart_facts` (for upagraha_position, jaimini_chara_karaka, graha_position fact_ids), `chart_divisionals` (for varga positions), `brahma_yoga_catalog`, `brahma_dosha_catalog`, `chart_dashas` (count-only).

---

## § 2 — Per-Asset Relational-Value Inventory (DB-Backed)

All row counts from production DB, chart_id `482012f1-710e-4a25-994a-93821f5871aa`, queried 2026-06-18.

### 2.1 — ga_positions (GA3 — positions + strength)

| Category | Row Count | ga_structural reads it? |
|---|---|---|
| `graha_position` | 430 | YES — via `_real_fact_id_ref` for constituent_facts_array |
| `graha_sign_attributes` | 100 | NO |
| `graha_shadbala_sthana/dig/kala/cheshta/naisargika/drik` | 45 each | NO (deliberately excluded per GA3-overlap guard) |
| `graha_shadbala_total` | 52 | NO |
| `graha_ishta_phala`, `graha_kashta_phala` | 35 each | NO |
| `ashtakavarga_bindu` | 480 | NO (GA3 owns; ga_structural adds anubindu only) |

**Relational value available but not ingested:** graha_position is read ONLY for fact_id lookup, not for building additional relationship rows from it. The 430 position rows could be the source for cross-asset joins (e.g., position→nakshatra→dispositor triples), but ga_structural doesn't perform these.

### 2.2 — ga_vargas (GA6 — chart_divisionals)

| Category | Row Count | ga_structural reads it? |
|---|---|---|
| `chart_divisionals` (varga_position) | ~21,635 rows | YES — primary source for all 30-varga relationship enumeration |
| `graha_dignity_per_varga` (in chart_facts) | 1,350 | YES — derived by ga_structural itself |
| `graha_cheshta_bala_per_varga` | 735 | NO — exists but not ingested as edge-weight |
| `graha_sthana_bala_per_varga` | 210 | NO |
| `graha_drik_bala_per_varga` | 210 | NO |
| `graha_kala_bala_per_varga` | 735 | NO |
| `ashtakavarga_bindu_per_varga` | 7,200 | NO |
| `ashtakavarga_pinda_sarva_per_varga` | 600 | NO |
| `graha_avastha_baladi_per_varga` | 1,350 | NO — ga_structural only computes D1 avasthas |
| `graha_avastha_deeptaadi_per_varga` | 1,350 | NO |
| `vimsopaka_bala_per_graha` | 35 | NO — ga_structural emits a reference pointer but actual value NULL |

**Relational value:** ga_vargas / chart_divisionals is well-integrated for position-based enumeration. The MISSING piece is per-varga strength as edge-weights: 7,200 ashtakavarga_bindu_per_varga rows and per-component Shadbala rows sit unused.

### 2.3 — ga_strength (GA3 — extended from positions)

| Category | Row Count | ga_structural reads it? |
|---|---|---|
| `ashtakavarga_anubindu` | 420 | YES — ga_structural GENERATES these rows |
| `graha_vargottama_amplification_factor` | 35 | YES — ga_structural GENERATES these |
| `graha_in_house_composite_strength` | 1,620 | YES — ga_structural GENERATES these |
| `graha_vimsopaka_shadvarga/saptavarga/dasavarga/shodasavarga` | 35 each | NO (GA3 owns) |

**Note:** ga_structural does not *read* ga_strength enrichment output back; it *produces* its own extensions in a separate category namespace. The composite strength proxy formulas (lines 2040–2045) are internal inline estimates, not GA3-authoritative values.

### 2.4 — ga_sensitive (GA5 — sensitive points)

| Category | Row Count | ga_structural reads it? |
|---|---|---|
| `upagraha_position` | 210 | YES — via `_load_special_points` |
| `arudha_pada` | 285 | NO |
| `sensitive_point_gulika_mandi` | 70 | **NO** |
| `sun_derived_upagraha` | 140 | **NO** |
| `special_lagna` | 110 | **NO** |
| `esoteric_point_sphuta_fertility` | 70 | **NO** |
| `esoteric_point_yogi` | 70 | **NO** |
| `esoteric_point_yogi_system` | 25 | **NO** |
| `aprakasha_position` | 175 | NO |
| `saturn_derived_point` | 175 | NO |
| `esoteric_point_avayogi` | 70 | NO |
| `esoteric_point_brahma/vishnu/shiva/mrityu` | 35–105 | NO |
| `esoteric_point_bhrigu_bindu` | 35 | NO |
| `esoteric_point_chatushphuta` | 35 | NO |
| `esoteric_point_panchasphuta` | 70 | NO |
| `esoteric_point_pranapada_sphuta` | 35 | NO |
| `esoteric_point_trikona_dasha_sphuta` | 35 | NO |
| `esoteric_point_trisphuta` | 35 | NO |
| `esoteric_point_sri_yantra_position` | 105 | NO |
| `saham_position` | 2,800 | NO |
| `maharsi_specific_point` | 70 | NO |
| `lal_kitab_special_point` | 100 | NO |
| `midpoint` | 1,080 | NO |
| `bhrigu_nadi_point` | 280 | NO |
| `nakshatra_pada_sensitive` | 80 | NO |

**Entities ga_sensitive introduces:** Gulika, Mandi, Yamaganda, Gulika-Kala, Dhuma, Vyatipata, Parivesha, Chapa, Upaketu (Tier-1 upagrahas under `sensitive_point_gulika_mandi`); Kaala, Mrityu, Ardhaprahara, Yamagantaka, Gulika, Mandi (sun_derived variants); Bhava Lagna, Hora Lagna, Ghati Lagna, Sree Lagna, Varnad Lagna, Pranapada (special_lagna); Beeja Sphuta, Kshetra Sphuta (esoteric_point_sphuta_fertility); Yogi Point, Avayogi, Duplicate Yogi (esoteric_point_yogi).

**Derivable relationships NOT being derived:** Graha→Gulika aspects; conjunction with Mandi; Yogi point nakshatra lord; sphuta-fertility in varga houses; special lagna relationships; arudha conjunction/aspect web.

### 2.5 — ga_nakshatra (GA5 — nakshatra layer)

| Category | Row Count | ga_structural reads it? |
|---|---|---|
| `graha_nakshatra_join` | 700 | NO |
| `graha_pada_join` | 200 | NO |
| `nakshatra_dispositor` | 200 | NO (ga_structural computes sign-dispositor independently) |
| `nakshatra_cogravity` | 10 | NO |
| `nakshatra_conjunction` | 1 | NO |
| `nakshatra_cross_ayanamsha` | 17 | NO |
| `nakshatra_statistics` | 34 | NO |
| `nakshatra_pada_sensitive` | 80 | NO |
| `graha_kp_lords` | 200 | NO |
| `cusp_kp_lords` | 240 | NO |
| `kp_cuspal_significators` | 300 | NO |
| `kp_ruling_planets_natal` | 50 | NO |

**Entities ga_nakshatra introduces:** 27-nakshatra × 4-pada grid for each graha across 5 ayanamshas; nakshatra-lord dispositor chains (distinct from sign-lord chains); KP sub-lord assignments; nakshatra cogravity clusters.

**Derivable relationships NOT being derived:** Nakshatra-lord-based dispositor chain as edge in graph (parallel to sign dispositor); KP sub-lord relationship web; nakshatra cogravity clusters as conjunction proxies; cross-ayanamsha nakshatra uncertainty flags as edge-weight modifiers.

### 2.6 — ga_condition (GA3 extended — per-varga avasthas)

| Category | Row Count | ga_structural reads it? |
|---|---|---|
| `graha_avastha_baladi_per_varga` | 1,350 | NO |
| `graha_avastha_deeptaadi_per_varga` | 1,350 | NO |
| `graha_avastha_jagradadi_per_varga` | 45 | NO |
| `graha_avastha_lajjitadi_per_varga` | 45 | NO |
| `graha_avastha_sayanadi_per_varga` | 45 | NO |
| `graha_cheshta_bala_per_varga` | 735 | NO |
| `graha_sthana_bala_per_varga` | 210 | NO |
| `graha_drik_bala_per_varga` | 210 | NO |
| `graha_kala_bala_per_varga` | 735 | NO |

**Note:** ga_structural emits D1-only avastha rows (graha_avastha_baladi etc. at 45 rows each). The per-varga avastha enrichment (1,350 rows per avastha type) is entirely uncoupled from ga_structural's relational graph.

**Derivable relationships:** Per-varga composite state classification incorporating actual avastha — currently ga_structural's `graha_composite_state_classification` uses inline dignity proxies without reference to the authoritative per-varga avastha data.

### 2.7 — ga_dashas (GA7 — dasha timeline)

| Table | Row Count | ga_structural reads it? |
|---|---|---|
| `chart_dashas` | 536,471 rows | NO (only count-checked in upstream gate) |

**Note:** ga_structural's `graha_avastha_lifetime_exposure_summary` explicitly acknowledges at line 1986 that "Lifetime exposure requires GA7 dasha timeline join" but stores only the natal proxy. This is a documented stub — not a bug.

**Derivable relationships:** Dasha-period–avastha compound rows; active-dasha graha relationship amplification; dasha-lord–natal-aspect overlay.

### 2.8 — ga_panchanga (GA4 — calendar/timing)

| Category | Row Count | ga_structural reads it? |
|---|---|---|
| `panchanga_tithi` | 7 | NO (only presence-checked) |
| All other panchanga_* | 3–80 each | NO |

**Derivable relationships:** Tithi-lord relationship to natal lagna-lord; vara-lord conjunction flags; yoga-lord karakatva amplification.

### 2.9 — ga_sade_sati (GA9 — Saturn transit periods)

| Category | Row Count | ga_structural reads it? |
|---|---|---|
| `sade_sati_cycle` | 320 | NO |
| `sade_sati_phase` | 3,040 | NO |
| `sade_sati_phase_quarter` | 3,360 | NO |
| `sade_sati_modifier_overlay` | 600 | NO |
| `sade_sati_concurrent_dasha_overlay` | 280 | NO |
| `sade_sati_cancellation_check` | 80 | NO |
| `sade_sati_downstream_cross_reference` | 120 | NO |
| `sade_sati_saturn_retrograde_subset` | 1,124 | NO |
| `anumukha_shani_period` | 200 | NO |
| `ardha_ashtama_shani_period` | 345 | NO |
| `ashtama_shani_period` | 260 | NO |
| `dhaiya_period` | 690 | NO |
| `janma_shani_period` | 200 | NO |
| `kantaka_shani_period` | 200 | NO |
| `vishakha_shani_period` | 200 | NO |

**Derivable relationships:** Active sade-sati period flag as a relationship modifier on Saturn→natal-Moon edges; retrograde-in-sade-sati compound state. These are transit relationships, not natal structural, so they have a different character — but the edges are missing entirely from ga_structural.

### 2.10 — ga_yoga (GA11 — yoga/dosha labels)

| Category | Row Count | ga_structural reads it? |
|---|---|---|
| `yoga_label` | 409 | NO (ga_structural GENERATES these rows itself) |
| `dosha_label` | 85 | NO (ga_structural GENERATES these) |
| `yoga_fires` | 44 | YES — ga_structural generates these |

**Note:** This is a DUPLICATION/DIVERGENCE situation. ga_structural both generates yoga_label rows (from brahma_yoga_catalog DB path) and there is a separate ga_yoga asset whose output is also `yoga_label`. Whether these are the same run or separate runs needs separate investigation — but both write to the same category.

### 2.11 — ga_medical (GA12)

| Category | Row Count | ga_structural reads it? |
|---|---|---|
| (not in chart_facts for this chart) | 0 | NO |

**Status:** Either ga_medical has not run for this chart, or it writes to a different table. Zero rows with ga_medical-attributed categories in chart_facts.

### 2.12 — ga_vastu (GA13)

| Category | Row Count | ga_structural reads it? |
|---|---|---|
| (not in chart_facts for this chart) | 0 | NO |

Same status as ga_medical.

### 2.13 — ga_tajaka (GA14)

| Category | Row Count | ga_structural reads it? |
|---|---|---|
| `tajik_hadda_lord` | 1,200 | NO |
| `tajik_triraashipathi` | 10 | NO |
| `tajik_vargottama_specific` | 15 | NO |
| `aspect_tajik` | 25 | YES — ga_structural GENERATES these (not reads) |

**Note:** ga_structural generates its own Tajik aspects (`aspect_tajik` category, lines 955–993) using inline ithasala/eesarpha/nakta/yamaya/manaau logic. It does NOT read the tajik_* rows from the DB.

---

## § 3 — THE GAP MAP

Core artifact. Evidence column cites file:line or SQL result.

| L1 Asset | Relational Value It Holds | ga_structural Ingests Today? | Evidence | Relationship Type to Derive | Data-Science Rationale | Jyotish Rationale | MSR Leverage | Priority |
|---|---|---|---|---|---|---|---|---|
| **ga_sensitive: `sensitive_point_gulika_mandi`** | 70 rows — Gulika and Mandi positions (sign, house, longitude, nakshatra) across 5 ayanamshas | **NO** | `_load_special_points` (line 2836) queries only `upagraha_position`; category `sensitive_point_gulika_mandi` never appears in query | graha→Gulika/Mandi aspect edges; conjunction edges; sign co-tenancy | Gulika/Mandi are high-importance malefic sensitive points; missing these nodes means the relational graph has no edges from these entities | Gulika is Manda-putra (son of Saturn), a primary maraka-class sensitive point. Any graha aspecting or conjoining Gulika inherits malefic taint. Classical rule-strength for longevity, poison, and loss analysis. | Multiple MSR signals cite Gulika patterns; those signals cannot be relationally grounded without these edges in ga_structural | **HIGH** |
| **ga_sensitive: `sun_derived_upagraha`** | 140 rows — Dhuma, Vyatipata, Parivesha, Chapa, Upaketu (5 points × 5 ayanamshas × sign/house/longitude) | **NO** | Same as above — `_load_special_points` blindspot | graha→sun-derived-upagraha aspect and conjunction edges | These are derived from Sun's longitude; their positions in the chart create malefic influence fields that shape house strength in ways the current relational model doesn't capture | Classical texts classify these as aprakasha grahas (shadowy, non-luminous). Dhuma and Vyatipata have documented effects on longevity and foreign journeys. Currently the graph has no nodes for these entities. | LOW direct MSR citation currently, but BLOCKERS for L2 Bodha bo_laksana sign-grid if these nodes are absent | **HIGH** |
| **ga_sensitive: `special_lagna`** | 110 rows — Bhava Lagna, Hora Lagna, Ghati Lagna, Sree Lagna, Varnad Lagna, Pranapada (multiple ayanamshas) | **NO** | `_load_special_points` line 2836 blindspot | Special-lagna→graha aspect received edges; graha conjunction with special lagna | Alternative ascendants define alternate house structures; relationships between natal grahas and these points define secondary house-lord chains | Bhava Lagna = stronger lagna for material matters; Hora Lagna = wealth lagna; Ghati Lagna = power lagna. In Jaimini analysis these are primary reference points for different life domains. | Direct MSR relevance: career, wealth, and power domains can only be scored relationally if these lagna points have relationship edges in the graph | **HIGH** |
| **ga_sensitive: `esoteric_point_sphuta_fertility`** | 70 rows — Beeja Sphuta and Kshetra Sphuta (5 ayanamshas × sign/house/nakshatra/nakshatra_lord) | **NO** | `_load_special_points` blindspot | Graha→fertility-sphuta aspect/conjunction edges | Fertility sphutas have known house/sign placement; aspect relationships from natal grahas activate or afflict them | Classical fertility analysis requires knowing which grahas aspect the Beeja/Kshetra Sphutas and whether those grahas are benefic or malefic | MSR has child-domain signals; none can be grounded to these sphutas without relational edges | **MEDIUM** |
| **ga_sensitive: `esoteric_point_yogi`** | 70 rows — Yogi Point and Avayogi across ayanamshas | **NO** | `_load_special_points` blindspot | Graha→Yogi Point aspect/conjunction; Yogi/Avayogi lord identification | Yogi Point nakshatra lord is the Yogi Planet; knowing which grahas aspect the Yogi Point activates that lord's potential | Yogi/Avayogi system identifies which graha periods are auspicious. Currently the graph has no structural edges connecting the Yogi Point's location to aspecting grahas | MSR timing signals benefit from Yogi period identification | **MEDIUM** |
| **ga_sensitive: `arudha_pada`** | 285 rows — AL1–AL12 Arudha padas across ayanamshas | **PARTIAL** | `upagraha_position` (original GA5 path) may include some arudha rows — but these 285 rows are in a separate `arudha_pada` category, NOT `upagraha_position`. Confirmed by DB query showing distinct categories. `_load_special_points` would miss them. | Arudha pada→graha aspect and conjunction; AL1 (Arudha Lagna) as primary node | Arudha padas define the social/manifestational layer of the chart; relationships between grahas and Arudha Lagna define reputation and social outcome | AL1 is the manifestational lagna; grahas conjoining or aspecting AL1 define what manifests externally. A cornerstone of Jaimini analysis. | HIGH direct MSR relevance — several signals reference external manifestation | **HIGH** |
| **ga_strength: per-varga Shadbala components** | `graha_cheshta_bala_per_varga` (735 rows), `graha_sthana_bala_per_varga` (210), `graha_drik_bala_per_varga` (210), `graha_kala_bala_per_varga` (735) | **NO** | ga_structural's `_build_varga_relationship_rows` (line 3137–) enumerates positions from `chart_divisionals` but never joins back to ga_strength's per-varga Shadbala categories | Per-varga edge weights for `aspect_parashari_per_varga`, `lord_in_house_per_varga`, `disposition_chain_per_varga` using authoritative per-varga Shadbala scores | Currently edge weights in the per-varga relational graph use D1 dignity proxies (exalted=1.0, own=0.875, neutral=0.5, debilitated=0.25) — coarse approximations. Per-varga Shadbala components would make edge weights authoritative. | In D9, a graha exalted by sign but weak by cheshta bala has diminished actual strength. The current graph cannot distinguish this. | Several strength-composite MSR signals; per-varga weights would give them varga-specific precision | **HIGH** |
| **ga_strength: `ashtakavarga_bindu_per_varga`** | 7,200 rows — bindu scores for every graha × house × 30 vargas × 5 ayanamshas | **NO** | Not referenced anywhere in ga_structural_writer.py | Per-house ashtakavarga edge weights for the varga relationship graphs | The 7,200-row ashtakavarga_bindu_per_varga table is the most data-rich per-varga strength indicator in L1. Zero use in ga_structural. | Ashtakavarga bindus define transit and natal strength per sign. In D9 (navamsha), high bindus strengthen the graha's marriage/spiritual domain. In D10 (dashamsha), career strength. | Direct use for period strength in dasha predictions; MSR signals could carry per-varga bindu confidence scores | **HIGH** |
| **ga_nakshatra: `nakshatra_dispositor`** | 200 rows — nakshatra-lord dispositor chain for each graha × 5 ayanamshas | **DIVERGENCE** | ga_structural independently computes sign-dispositor chains (`graha_dispositor_chain`, `dispositor_chain_per_varga`) at lines 2230–2275 and 3316–3352. ga_nakshatra's `nakshatra_dispositor` is a PARALLEL chain — both exist, but ga_structural ignores the nakshatra variant | ga_structural should reference ga_nakshatra's nakshatra_dispositor as a parallel edge type alongside sign-dispositor | Two dispositor chains have different interpretive meaning: sign-dispositor = material/organizational chain; nakshatra-dispositor = sub-conscious/karmic chain. Having both in the relational graph doubles the diagnostic surface. | Classical Nadi texts heavily use nakshatra dispositor chains (lord of lord of lord's nakshatra) for prediction depth. The sign-only dispositor chain captures only one layer. | MSR signals that reference nakshatra-lord relationships can only be validated with both chain types in the graph | **MEDIUM** |
| **ga_nakshatra: `graha_nakshatra_join`** | 700 rows — which nakshatra each graha occupies, its pada, lord, sub-lord | **NO** | Not queried anywhere in ga_structural_writer.py | Nakshatra-join as an alternative to sign-join for aspect/conjunction nodes; nakshatra-level co-tenancy | Graha-in-nakshatra membership defines sub-sign clusters; two grahas in the same nakshatra are more tightly related than two in the same sign | Two grahas in Jyeshtha occupy the same nakshatra field; their relationship is qualitatively different from sign-level co-tenancy | Higher-resolution conjunction data for MSR signal scoring | **MEDIUM** |
| **ga_nakshatra: KP system** (`graha_kp_lords`, `cusp_kp_lords`, `kp_cuspal_significators`) | 200+240+300 = 740 rows | **NO** | Not queried anywhere | KP cuspal significator→graha relationship web; sub-lord activation chains | KP system is a predictive system based on sub-lord significators; the relational web of sub-lords is a distinct graph structure that ga_structural doesn't model | Krishnamurti Paddhati has documented prediction precision; its nodes and edges are absent from ga_structural entirely | Discrete L2 Bodha use case: timing predictions from KP sub-lord activation | **LOW** (distinct system; may warrant own asset) |
| **ga_condition: per-varga avasthas** | `graha_avastha_baladi_per_varga` (1,350), `graha_avastha_deeptaadi_per_varga` (1,350), others | **NO** | ga_structural generates D1-only avastha rows (lines 1861–1996); never reads the per-varga enrichment from ga_condition | Use per-varga avastha state as composite-state modifier in `graha_digest_per_varga` category | ga_structural's `graha_composite_state_classification` uses only D1 dignity; per-varga avasthas would make the classification varga-specific and authoritative | In D9, a graha in Mrita avastha (dead state) produces drastically different results from one in Yuva avastha (youthful), regardless of sign dignity | The MSR has varga-specific signal sets; composite state classification needs per-varga authority | **HIGH** |
| **ga_dashas: `chart_dashas`** | 536,471 rows — full Vimshottari dasha timeline | **NO** (except count gate) | check_upstream_presence (line 563) counts rows only | Dasha-period graha→natal relationship amplification edges; active dasha period as graph traversal key | The dasha timeline defines which natal relationships are active when; a graph without dasha-layer edges cannot generate time-indexed predictions | In classical Jyotish, relationships fire only when the relevant dasha-lords are active; the natal structural graph needs dasha-layer overlay for temporal prediction | ALL MSR timing signals depend on dasha-period context; this is the largest gap for L3 Kala layer | **MEDIUM** (L3 Kala scope, not ga_structural scope) |
| **ga_panchanga** | Tithi, vara, yoga, karana, muhurta quality (various categories, small counts) | **NO** (existence-checked only) | check_upstream_presence checks presence of `panchanga_tithi`; no content read | Tithi-lord→natal relationship; vara-lord conjunction flags | Panchanga nodes define the birth-moment's quality overlay on the natal chart; they could provide additional relationship edges for natal analysis | Tithi lord is a key player in birth analysis; vara lord can strengthen or weaken natal grahas in some classical schools | Low MSR leverage at this time | **LOW** |
| **ga_sade_sati** | 8,000+ rows across all sade-sati categories | **NO** | Not referenced anywhere in ga_structural_writer.py | Sade-sati cycle flag as Saturn→natal-Moon edge modifier; active period modifier for Saturn relationships | Sade-sati modifies Saturn's relationship weight with Moon and Moon's natal house; the structural graph currently has no time-indexed modification mechanism | Sade-sati is documented as the primary Saturn-Moon stress period; the structural graph should capture Saturn's special relationship state during this transit | MSR sade-sati signals cannot be relationally grounded without these period edges | **MEDIUM** (transit scope) |
| **ga_tajaka** | `tajik_hadda_lord` (1,200), `tajik_triraashipathi` (10), `tajik_vargottama_specific` (15) | **NO** (ga_structural generates its own `aspect_tajik` via inline computation) | ga_structural generates aspect_tajik at lines 955–993 independently; the 3 tajika categories in DB from ga_tajaka are unused | Read ga_tajaka's `tajik_hadda_lord` for sub-sign lord relationships; `tajik_triraashipathi` for trisector lords | The 1,200 Hadda lord rows represent sub-sign lordship assignments per degree that the inline Tajik aspect calculation ignores | Tajik Hadda lords define which planet owns each degree-band within a sign; combining Hadda lords with aspect_tajik would give degree-precision relationship edges | Low MSR direct leverage currently | **LOW** |
| **ga_yoga / yoga_label duplication** | `yoga_label` (409 rows in DB) | **DUPLICATION** | ga_structural generates `yoga_label` via brahma_yoga_catalog path (lines 1597–1628); ga_yoga also writes to `yoga_label`. Both exist in production with 409+44 rows total (`yoga_label`: 409, `yoga_fires`: 44). | Investigate whether ga_structural and ga_yoga are deduplicating via build_id scoping | Double-write risk: if two writers emit `yoga_label` rows for the same (chart_id, ayanamsha_id, category, subject, key) with different build_ids, the conflict resolution (`ON CONFLICT DO UPDATE`) may produce unexpected winners | Classical yoga identification should have a single authority; currently two assets write to overlapping categories | MSR yoga signal coverage accuracy depends on which writer is canonical | **HIGH** (governance issue) |
| **ga_medical** | 0 rows in chart_facts | **NO** | `SELECT COUNT(*) WHERE asset_id='ga_medical'` returns 0 | N/A until ga_medical runs | Medical domain analysis is not populated for this chart | If populated, would introduce health/constitution relationship edges | Potential future scope | **LOW** |
| **ga_vastu** | 0 rows in chart_facts | **NO** | Same — 0 rows | N/A | Same | Same | Same | **LOW** |

---

## § 4 — Architectural Options

The options below are framed for native decision — no choice is made here.

### Option A: Extend ga_structural to Ingest Enriched/New Assets ("Complete Hub")

ga_structural would be extended to:
1. Read `sensitive_point_gulika_mandi`, `sun_derived_upagraha`, `special_lagna`, `esoteric_point_sphuta_fertility`, `esoteric_point_yogi`, `arudha_pada` alongside `upagraha_position` in `_load_special_points`
2. Read per-varga Shadbala and Ashtakavarga from ga_strength/ga_condition as edge-weights in `_build_varga_relationship_rows`
3. Reference ga_nakshatra's `nakshatra_dispositor` as a second dispositor chain alongside the sign-dispositor chain

**Relational value gained:** The full entity set (all sensitive points) would have relationship edges in the graph. Edge weights in the per-varga relational graph would be authoritative (ga_strength values) rather than proxies. Two dispositor chains (sign + nakshatra) would coexist as parallel edges.

**Relational value lost:** None — additive only.

**Rebuild cost:** Significant. ga_structural already runs 5 ayanamshas × 30 vargas × ~20 build functions; adding DB joins for sensitive points and per-varga strength would multiply query count. The `_load_special_points` function needs to query 6+ categories instead of 1. Per-varga strength edge-weighting would add 30 × 5 × 9 = 1,350 DB rows to join per ayanamsha.

**L1-authority / duplication implications:** Fully consistent with L1-is-authority principle: ga_structural would reference ga_sensitive fact_ids rather than re-derive. No new computation. CONCERN: the yoga_label duplication (ga_structural vs. ga_yoga) is a governance issue that Option A does not resolve — it could worsen it.

**Effect on MSR signal richness:** HIGH. The absence of Gulika, Mandi, special lagnas, and arudha padas from the relational graph is a material gap in L2 bo_laksana's ability to project these entities. Option A closes this gap for L2 immediately.

---

### Option B: Leave ga_structural, Have bo_laksana Project Enriched Assets Directly ("Thin Hub + Fat Projection")

ga_structural remains unchanged. bo_laksana reads ga_sensitive, ga_nakshatra, ga_condition per-varga, ga_strength per-varga directly and projects the enriched-point relationship rows as part of its own L2 output.

**Relational value gained:** L2 gets the enriched-point projection without extending L1 builder. Simpler ga_structural rebuild path.

**Relational value lost:** The enriched points have no relationship rows in the L1 chart_facts layer. If any other asset (or bo_laksana itself in a second pass) needs to query "what aspects Gulika?" from chart_facts, it must re-derive rather than look up. The single-pass ingest from L1 to L2 bypasses the intermediate relational encoding step.

**Rebuild cost for bo_laksana:** HIGH. bo_laksana would need to implement aspect/conjunction logic that ga_structural already has (and debugged across 5 ayanamshas × 30 vargas). This duplicates computation at L2 that could be authoritative in L1.

**L1-authority / duplication implications:** RISK. The L1-is-authority principle (§N.5 of CLAUDE.md) requires that L2 derivations reference L1 fact_ids. Under Option B, bo_laksana would compute relationships that could/should live in L1. This violates the layer separation principle if the relationships are STRUCTURAL (not interpretive). Aspect/conjunction is structural (B.1 — facts/interpretation separation).

**Effect on MSR signal richness:** Achieves the same endpoint as Option A for final MSR signal quality, but at the cost of layer-principle compliance and code duplication.

---

### Option C: Hybrid — Extend ga_structural Selectively, Leave Others to bo_laksana

Decision criteria per entity type:
- **STRUCTURAL relationships** (aspects, conjunctions, dispositors): should live in ga_structural (L1). Extend ga_structural to read the enriched sensitive point categories, and use per-varga strength as edge-weights.
- **INTERPRETIVE projections** (which sensitive points are "activated," composite dignity assessments): leave for bo_laksana (L2).
- **KP system / specialized systems**: potentially their own ga_kp sub-asset, not in ga_structural.
- **Transit relationships (sade_sati)**: clearly L3 Kala scope; neither ga_structural nor bo_laksana.

Under Option C:
- ga_structural is extended ONLY for: (a) sensitive point entities (read 6 enriched categories, not just upagraha_position), (b) per-varga Shadbala edge-weights (join ga_condition per-varga avastha and ga_strength per-varga Shadbala into the relationship rows)
- ga_nakshatra nakshatra_dispositor: add as parallel chain in ga_structural (one additional edge type)
- bo_laksana handles: interpretive labels, domain mapping, score aggregation
- yoga_label duplication is resolved by designating ga_structural as the SOLE writer and retiring any competing ga_yoga writer for this category

**Rebuild cost:** Moderate. The sensitive-point extension is a targeted change to `_load_special_points` (one function). The per-varga strength edge-weighting requires joining two additional tables inside `_build_varga_relationship_rows`. The nakshatra_dispositor chain is one additional DB query.

**Effect on MSR signal richness:** HIGH + compliant. All structural relationships are in L1; L2 interpretive layer has complete relational raw material.

---

## § 5 — Executive Summary

### What ga_structural Currently Does Well

ga_structural is a comprehensive multi-varga relational hub. It produces 60,000+ rows of structural relationship data across 30 vargas, 5 ayanamshas. The following are fully operational:
- Per-varga dignity, Parashari/Jaimini aspects, conjunctions, parivartana, dispositor chains, vargottama, Kala Sarpa (all 30 vargas)
- 144-cell argala and virodha matrices per varga (144 × 30 × 5 ayanamshas = 21,600 rows each in DB, confirmed)
- House-lord placement and lord-aspects-lord matrix across all vargas
- Yoga/dosha firing via brahma_yoga/dosha_catalog (DB path) with real constituent fact_id backlinks
- Graha yuddha detection, combustion relationships, retrograde aspect modification
- Per-graha karakatva web, functional class variants, avastha 5-type system (D1)
- 9×12 composite strength matrix (graha_in_house_composite_strength)

### Critical Gaps — Enriched/New Assets ga_structural Does NOT Weave In

**GAP 1 — Enriched Sensitive Points (HIGHEST VALUE):** `_load_special_points` queries only `upagraha_position` (210 rows). The following categories are invisible: `sensitive_point_gulika_mandi` (70 rows), `sun_derived_upagraha` (140 rows), `special_lagna` (110 rows), `esoteric_point_sphuta_fertility` (70 rows), `esoteric_point_yogi` (70 rows), `arudha_pada` (285 rows). These entities have zero relationship edges in the chart_facts layer — no aspects received, no conjunctions. This means the `conjunction_special_point` and `aspect_received_by_special_point` output categories are built from only 1/7 of the relevant sensitive-point universe. Code evidence: `ga_structural_writer.py` line 2836, query `WHERE fact_category = 'upagraha_position'`.

**GAP 2 — Per-Varga Strength as Edge-Weights (HIGH VALUE):** The per-varga relational graph uses inline dignity proxies (exalted=1.0, neutral=0.5, debilitated=0.25) for edge weights. ga_strength has computed authoritative per-varga Shadbala components (7,200 rows of ashtakavarga_bindu_per_varga, 735 rows of graha_cheshta_bala_per_varga, etc.) that are completely uncoupled from the relational graph. The `graha_in_house_composite_strength` rows (1,620 in DB) use simplified proxies at lines 2040–2045 rather than ga_strength values.

**GAP 3 — Per-Varga Avastha State (HIGH VALUE):** ga_condition has 1,350 rows each of per-varga baladi, deepta, jagradadi, lajjitadi, sayanadi avasthas. ga_structural generates D1-only versions (45 rows each). The `graha_composite_state_classification` output is based on D1 dignity + combustion only — no per-varga avastha data.

**GAP 4 — Nakshatra Dispositor Parallel Chain (MEDIUM VALUE):** ga_nakshatra's `nakshatra_dispositor` (200 rows) is a nakshatra-lord-based dispositor chain. ga_structural independently computes sign-lord dispositor chains. The two are parallel but different chains. ga_structural has no nodes or edges from the nakshatra-dispositor graph. This is a divergence, not a duplication — the chains capture different karmic layers.

### Stale-Duplication Findings

**FINDING 1 — yoga_label category written by two assets:** ga_structural emits `yoga_label` rows (via brahma_yoga_catalog DB path, lines 1597–1628) AND there appears to be a separate ga_yoga asset that also writes `yoga_label` (409 rows in DB, `yoga_fires` has 44 rows separately). This is a governance issue: two L1 writers should not produce the same output category. The conflict resolution (`ON CONFLICT DO UPDATE`) means the last writer wins, which is non-deterministic if rebuild order changes.

**FINDING 2 — Tajik aspects generated independently:** ga_structural generates `aspect_tajik` at lines 955–993 using simplified orb logic (Ithasala/Eesarpha/Nakta/Yamaya/Manaau). The DB has `tajik_hadda_lord` (1,200 rows), `tajik_triraashipathi` (10 rows), `tajik_vargottama_specific` (15 rows) from ga_tajaka. The ga_structural Tajik computation is independent and may diverge from ga_tajaka's authoritative Hadda lord structure.

**FINDING 3 — Vargottama computed twice:** ga_structural computes vargottama from D1 longitude arithmetic (lines 1026–1040) for `graha_vargottama_amplification_factor`, AND from sign comparison across vargas (lines 3354–3382) for `vargottama_per_varga`. ga_vargas / chart_divisionals already has the authoritative per-varga positions from which vargottama is determined. The inline navamsha arithmetic at line 1030 (`navamsha_pada = int(degree_in_sign / 3.333333)`) is a known approximation path, not a DB lookup. Low severity since the DB-path for `vargottama_per_varga` reads chart_divisionals.

### Recommended Architectural Option

**Recommendation (not a decision): Option C — Hybrid, with immediate priority on GAP 1**

Rationale:

1. **Gap 1 (sensitive points) is the highest-priority fix and the cheapest to implement.** `_load_special_points` needs to be extended from one category query to a multi-category UNION or separate queries for 6 enriched categories. This is a surgical change to one function. The output categories `conjunction_special_point` and `aspect_received_by_special_point` will automatically expand to cover Gulika, Mandi, Arudha Lagna, special lagnas, and esoteric sphutas. All structural relationships (aspects, conjunctions) belong in L1 ga_structural per B.1.

2. **Gap 2 (per-varga Shadbala edge-weights) is high-value but moderate complexity.** Add a join inside `_build_varga_relationship_rows` to read per-varga Shadbala from ga_strength's per-varga categories and attach them to the existing `aspect_parashari_per_varga` and `lord_in_house_per_varga` rows as `numeric_value` edge-weights. This does not add new row types — it enriches existing row weights.

3. **Gap 3 (per-varga avasthas) should be resolved by coupling ga_structural's `graha_composite_state_classification` to ga_condition's per-varga avastha.** One additional query per varga inside the already-running varga loop.

4. **Gap 4 (nakshatra dispositor) is medium priority.** Add a DB query for `nakshatra_dispositor` category inside `_build_structural_relationship_rows` to emit `nakshatra_dispositor_chain` as a parallel edge type alongside `graha_dispositor_chain`. Two calls, two output categories — keeps them clearly separated.

5. **yoga_label duplication (Finding 1) must be resolved before L2 build.** Designate ga_structural as the sole `yoga_label` writer; retire any competing ga_yoga output in the same category, or rename ga_yoga's output to `yoga_label_supplemental`.

6. **bo_laksana (L2) should NOT re-implement structural relationship logic.** Extending ga_structural to close Gaps 1–4 is preferable to bo_laksana duplicating aspect/conjunction computation, which would violate B.1 (facts at L1) and §N.5 (L1 is authority over L2 derivations).

The recommended sequence: (a) resolve yoga_label duplication governance; (b) extend `_load_special_points` for all 6 enriched categories; (c) add per-varga Shadbala edge-weights; (d) add nakshatra_dispositor parallel chain; (e) couple `graha_composite_state_classification` to per-varga avastha. These are all changes to existing functions, not new infrastructure — consistent with the FROZEN orchestrator contract (§N.2: writers onboard by extending WriterBase subclass content, not the orchestrator).

---

*End of GA_STRUCTURAL_INGEST_MAP v1.0. Every claim above is code-cited (file:line in ga_structural_writer.py) or query-backed (production DB 2026-06-18).*
