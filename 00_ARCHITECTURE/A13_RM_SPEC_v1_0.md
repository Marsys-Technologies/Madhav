---
artifact: A13_RM_SPEC_v1_0.md
document: A13 — RM (Resonance Map) Specification
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed: all 15 clarifications = YES; full critical + non-critical scope included; G27 pre-flight audit declared parallel prerequisite)
intended_for: Claude Code sub-agents implementing the A13 RM writer to L2.5 layer
prime_directive: Only computed facts. Every remedy carries a classical-source citation. No narrative recommendations, no opinion-flavored guidance — the assignment of remedies to targets is deterministic, derived from formulas and corpus matches, never inferred from interpretation.
depends_on: A8 T1 structural (shadbala/bhava_bala/cancellation), A10 MSR (salience-ranked signals), A11 CDLM (cell_remedy_priority + pattern_remedy_theme + cluster + chart_typology), A12 CGM (motif_class + conflict_resolution_edges + fingerprint_hash), A7 chart_dashas (3 systems × Maha-Antar), A9 Sade Sati (phase + cancellations), G19 karakas (natural + chara), G27 remedy corpus (exhaustiveness-audit prerequisite)
window: 1950-01-01 → 2100-12-31 per A7 rule
technology_stack: Cloud SQL Postgres + pgvector (remedy embeddings) — same as A12. No Apache AGE, no TimescaleDB.
parallel_prerequisite: G27 corpus exhaustiveness audit (BRIEF authored at A13 implementation kickoff)
---

# A13 — RM (Resonance Map) Specification

## §0 — Mission

For each chart per ayanamsha, compute (a) the resonance map of weakest grahas and their classical-source remedy candidates from corpus G27, (b) per-tradition prescription chains across 6 traditions × 18 remedy categories, (c) dasha-windowed temporal calibration of remedies to A7 chart_dashas across 3 systems (Vimshottari + Chara Karaka + Yogini), (d) per-dosha remedy bundles, (e) per-pattern-cluster + per-motif remedy themes, (f) chart-level remedy priority + phase-sequenced intensity profile + cross-chart remedy embeddings, (g) chronobiology-aligned timing (hora + choghadiya + lunar phase + direction). All deterministic. Two-pass verified. Classical-source-cited per prescription. Counter-indications + compatibility checks + acharya-review flags enforced.

## §1 — Locked decisions (all 15 = YES + full critical + non-critical scope)

### Q1-Q15 clarifications:
1. **Tradition scope**: All 6 — Parashari + Tantric + KP + Tajik + Lal Kitab + Ayurveda-Jyotish
2. **Remedy categories**: All 18 — mantra, bija_mantra, stotra, gem, substitute_gem, yantra, color, dana, vrata, pilgrimage, seva, direction, vastu, homa, snan, lal_kitab_object, ayurveda_constitutional, tantric_heavy
3. **Dasha-windowed temporal calibration**: Yes — per-Maha across 3 systems (Vim + Chara + Yogini)
4. **Sade Sati phase-specific remedies**: Yes — 4 distinct phase bundles
5. **Tantric heavy-grade**: Include + `requires_acharya_review_flag=true`
6. **Counter-indications + compatibility checks**: Yes — full counter_indications + incompatible_with_prescription_ids
7. **Feasibility scoring**: Yes — cost + time + complexity per prescription
8. **Chart-typology-driven selection bias**: Yes — bias by A11 chart_typology
9. **pgvector remedy embeddings**: Yes — for cross-chart remedy peer search
10. **M6 outcome tracking placeholder**: Yes — empty JSONB at write
11. **Remedy phase sequencing**: Yes — foundation → intensification → maintenance
12. **Substitute gem alternatives**: Yes — upa-ratnas included
13. **Pilgrimage remedies**: Yes — graha-sacred-site mappings
14. **Wipe existing l25_rm_*** rows before rebuild
15. **G27 pre-flight audit**: Yes — author G27 audit brief now, before A13 implementation

### Critical items (A-Y) locked:
- A. G27 exhaustiveness audit declared parallel prerequisite (§7)
- B. Per-tradition coverage audit included in G27 prereq
- C. Per-graha complete remedy fingerprint (mantra + bija + stotra + gem + yantra + color + dana + vrata + ...) per weakest graha
- D. Dasha-windowed per-Maha calibration across 3 systems
- E. Sade Sati 4-phase remedy bundles (Janma, Kantaka, Ardha Ashtama + Anumukha phases)
- F. counter_indications_array + incompatible_with_prescription_ids_array
- G. feasibility_score + estimated_cost_inr_range_jsonb + estimated_time_minutes_daily + ritual_complexity_class
- H. requires_acharya_review_flag on all Tantric heavy + Lal Kitab severe + counter-indicated
- I. cross_tradition_corroboration_count + cross_tradition_corroborating_traditions_array (boost when 4+ agree)
- J. CGM motif → remedy theme bridges (l25_rm_pattern_remedies)
- K. CDLM pattern cluster → remedy theme bridges (l25_rm_pattern_remedies)
- L. Chart-typology bias factor in resonance_match_score
- M. Dosha-specific bundles (Mangal, Kala Sarpa, Pitra, Sade Sati phases, Ashtama Shani, Kantaka Shani, Guru Chandala, Visha Yoga, etc.)
- N. Yoga-karaka bonus targeting (is_yoga_karaka_flag in resonance)
- O. Chara karaka role targeting (AK gets soul-graha amplification)
- P. Tantric heavy + counter-indications protection enforced
- Q. Lal Kitab unique household-object remedy category
- R. Ayurveda-Jyotish constitutional remedies (graha-prakriti pairings)
- S. M6 outcome_tracking_placeholder_jsonb on every prescription
- T. pgvector prescription_embedding_vec + chart_remedy_embedding_vec
- U. Remedy phase sequencing (foundation/intensification/maintenance)
- V. substitute_gem category for affordable upa-ratnas
- W. Yantra geometry + consecration (pranapratishtha) prescriptions
- X. Pilgrimage remedies with priority ranking per graha
- Y. Wipe existing l25_rm_* before rebuild
- Z. Per-acharya tradition variants (e.g., Tantric: Kaula vs Mishra vs Samaya) via sub_tradition field

### Non-critical items (AA-CC) locked:
- AA. Chronobiology-aligned timing — hora + choghadiya integration from A4 panchanga (`recommended_hora_lord_array`, `recommended_choghadiya_window_array`)
- BB. Lunar phase recommendations for mantra initiations (`initiation_lunar_phase_recommendation_array` — e.g., Shukla Pratipada for new mantras, Purnima for Devi)
- CC. Per-direction remedy practices (East for Sun, North for Mercury, etc. — `recommended_facing_direction`)

## §2 — Inputs (upstream consumption matrix)

| From | Field | Use in A13 |
|---|---|---|
| A8 T1 structural | shadbala_normalized, bhava_bala_normalized, combustion_score, debility_score, affliction_count, cancellation_modifier, dispositor_chain_weakness, vargottama_absence | Compute resonance_score weakness component |
| A10 MSR | salience-ranked signals, contradicts_signals_array | contradiction_factor in resonance |
| A11 CDLM | cell_remedy_priority_rank, weakest_constituent_graha_jsonb, pattern_remedy_theme_jsonb, cell_remedy_hooks_array, chart_typology_class, pattern_clusters | Pre-shaped remedy hooks per cell + pattern; typology bias |
| A12 CGM | motif_class, motif_name, conflict_resolution_edges, fingerprint_hash | Motif-level remedy themes; cross-chart remedy peer lookup via motif fingerprint |
| A7 chart_dashas | Vim+Chara+Yogini Maha-Antar windows | Temporal calibration windows |
| A9 Sade Sati | active_phase, cancellation_count, phase_intensity | Sade Sati phase-specific bundles |
| A4 panchanga | hora, choghadiya, lunar phase | Chronobiology-aligned timing (AA, BB, CC) |
| G19 karakas | natural + chara karaka assignments | is_yoga_karaka_flag, is_chara_karaka_role |
| **G27 corpus** | classical remedy library | All prescription source-of-truth |

## §3 — Resonance score formula v1.0 (versioned + unit-tested)

```python
def resonance_score_v1(graha, chart_state):
    weakness_score = (
        (1.0 - graha.shadbala_normalized) * 0.30 +
        (1.0 - graha.bhava_bala_normalized) * 0.15 +
        graha.combustion_score * 0.10 +
        graha.debility_score * 0.10 +
        graha.affliction_count_normalized * 0.10 +
        graha.cancellation_burden * 0.10 +
        graha.dispositor_chain_weakness * 0.05 +
        graha.vargottama_absence_score * 0.05 +
        graha.dasha_proximity_activation_score * 0.05
    )
    contradiction_factor = normalized(sum(msr_signals_in_conflict_ref_graha))
    domain_burden = normalized(sum(cdlm_weakest_constituent_count))
    motif_burden = normalized(sum(cgm_motifs_with_graha_as_weakest_node))
    yoga_karaka_amp = 1.20 if graha.is_yoga_karaka else 1.0
    chara_karaka_amp = {'AK': 1.30, 'AmK': 1.15, 'BK': 1.10, 'MK': 1.05, 'PK': 1.05, 'PiK': 1.05, 'DK': 1.10}.get(graha.chara_role, 1.0)

    resonance = (
        weakness_score
        * (1 + contradiction_factor * 0.20)
        * (1 + domain_burden * 0.15)
        * (1 + motif_burden * 0.10)
        * yoga_karaka_amp
        * chara_karaka_amp
    )
    return resonance
```

Resonance-match score (how well a prescription matches a target):

```python
def resonance_match_score_v1(prescription, target_resonance, chart):
    base = prescription.classical_strength_for_graha[target_resonance.graha]
    typology_bias = TYPOLOGY_BIAS_MATRIX[chart.typology][prescription.remedy_category]
    cross_tradition_boost = math.log(1 + prescription.cross_tradition_corroboration_count) * 0.10
    pattern_alignment = 0.15 if prescription.targets_motif_id in chart.active_motifs else 0.0
    cancellation_penalty = 0.5 if prescription.has_active_counter_indication(chart) else 1.0
    return base * (1 + typology_bias) * (1 + cross_tradition_boost + pattern_alignment) * cancellation_penalty
```

## §4 — Storage architecture (6 tables)

### Table 1 — `l25_rm_resonances` (per-graha resonance targets)

```sql
CREATE TABLE l25_rm_resonances (
  resonance_id UUID PRIMARY KEY,
  chart_id UUID NOT NULL, ayanamsha_id TEXT NOT NULL, build_id UUID NOT NULL,
  snapshot_type TEXT NOT NULL,                     -- 'static_natal' | 'dynamic_maha_<system>_<lord>' | 'sade_sati_phase_<N>' | 'transit_hit_<event>'
  graha TEXT NOT NULL,
  resonance_score NUMERIC NOT NULL,
  resonance_score_formula_version TEXT NOT NULL,
  weakness_score NUMERIC,
  contradiction_factor NUMERIC,
  domain_burden NUMERIC,
  motif_burden NUMERIC,
  is_yoga_karaka_flag BOOLEAN,
  is_chara_karaka_role TEXT,                       -- AK | AmK | BK | MK | PK | PiK | DK | null
  weakest_rank_in_chart INT,
  remedy_priority_class TEXT,                      -- 'urgent' | 'recommended' | 'optional'
  associated_doshas_array TEXT[],
  associated_motifs_array UUID[],
  associated_cdlm_cells_array UUID[],
  ephemeris_audit_jsonb JSONB,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, graha)
);

CREATE INDEX rm_resonances_chart_idx ON l25_rm_resonances (chart_id, ayanamsha_id);
CREATE INDEX rm_resonances_rank_idx ON l25_rm_resonances (chart_id, ayanamsha_id, weakest_rank_in_chart);
CREATE INDEX rm_resonances_doshas_gin ON l25_rm_resonances USING gin (associated_doshas_array);
```

### Table 2 — `l25_rm_remedy_prescriptions` (per-target × per-tradition × per-category)

```sql
CREATE TABLE l25_rm_remedy_prescriptions (
  prescription_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,
  snapshot_type TEXT NOT NULL,
  target_graha TEXT NOT NULL,
  target_resonance_id UUID NOT NULL REFERENCES l25_rm_resonances(resonance_id),

  -- Tradition + sub-tradition (Z)
  tradition TEXT NOT NULL,                         -- parashari | tantric | kp | tajik | lal_kitab | ayurveda_jyotish
  sub_tradition TEXT,                              -- tantric: kaula | mishra | samaya; etc.

  -- Remedy category (18 classes)
  remedy_category TEXT NOT NULL,                   -- mantra | bija_mantra | stotra | gem | substitute_gem | yantra | color | dana | vrata | pilgrimage | seva | direction | vastu | homa | snan | lal_kitab_object | ayurveda_constitutional | tantric_heavy

  remedy_id_g27 TEXT NOT NULL,
  remedy_label_human TEXT NOT NULL,
  prescription_detail_jsonb JSONB NOT NULL,

  -- Strength + classification
  classical_strength_rating TEXT,                  -- gentle | moderate | intense | tantric_heavy
  classical_source_citation_id TEXT NOT NULL,
  classical_source_text_jsonb JSONB,

  -- Targeting
  targets_motif_id UUID,                           -- l25_cgm_motifs
  targets_cell_id UUID,                            -- l25_cdlm_cells
  targets_dosha_class TEXT,
  resonance_match_score NUMERIC,
  match_score_formula_version TEXT,

  -- Compatibility (F)
  counter_indications_array TEXT[],                -- pregnancy | mourning | menstruation | minor_age | acute_illness
  incompatible_with_prescription_ids_array UUID[],
  prerequisite_prescription_ids_array UUID[],

  -- Feasibility (G)
  feasibility_score NUMERIC,
  estimated_cost_inr_range_jsonb JSONB,            -- {min, max, currency}
  estimated_time_minutes_daily NUMERIC,
  ritual_complexity_class TEXT,                    -- self_administered | family_assisted | priest_required | tantric_initiation_required

  -- Acharya review (H)
  requires_acharya_review_flag BOOLEAN NOT NULL,
  acharya_review_reason_array TEXT[],              -- ['tantric_heavy', 'counter_indication_present', 'lal_kitab_severe']

  -- Cross-tradition convergence (I)
  cross_tradition_corroboration_count INT,
  cross_tradition_corroborating_traditions_array TEXT[],

  -- Phase sequencing (U)
  phase_sequence_class TEXT,                       -- foundation | intensification | maintenance
  phase_duration_days INT,                         -- 40 | 108 | 365 | lifetime
  count_prescription_jsonb JSONB,                  -- {japa_count, repetitions, schedule}

  -- Substitute gem (V)
  substitute_options_jsonb JSONB,                  -- only when remedy_category='gem'

  -- Yantra (W)
  yantra_geometry_jsonb JSONB,
  pranapratishtha_required_flag BOOLEAN,

  -- Pilgrimage (X)
  pilgrimage_site_jsonb JSONB,                     -- name, lat/lon, classical citation
  pilgrimage_priority_rank INT,

  -- Chronobiology (AA, BB, CC)
  recommended_hora_lord_array TEXT[],
  recommended_choghadiya_window_array TEXT[],
  initiation_lunar_phase_recommendation_array TEXT[],
  recommended_facing_direction TEXT,

  -- M6 outcome tracking (S)
  outcome_tracking_placeholder_jsonb JSONB,        -- empty at write; user records outcome

  -- pgvector (T)
  prescription_embedding_vec VECTOR(768),

  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL,

  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, target_graha, tradition, sub_tradition, remedy_category, remedy_id_g27)
);

CREATE INDEX rm_prescriptions_chart_idx ON l25_rm_remedy_prescriptions (chart_id, ayanamsha_id);
CREATE INDEX rm_prescriptions_target_idx ON l25_rm_remedy_prescriptions (chart_id, ayanamsha_id, target_graha);
CREATE INDEX rm_prescriptions_tradition_idx ON l25_rm_remedy_prescriptions (chart_id, ayanamsha_id, tradition);
CREATE INDEX rm_prescriptions_category_idx ON l25_rm_remedy_prescriptions (chart_id, ayanamsha_id, remedy_category);
CREATE INDEX rm_prescriptions_match_score_idx ON l25_rm_remedy_prescriptions (chart_id, ayanamsha_id, resonance_match_score DESC);
CREATE INDEX rm_prescriptions_review_idx ON l25_rm_remedy_prescriptions (chart_id, ayanamsha_id) WHERE requires_acharya_review_flag = true;
CREATE INDEX rm_prescriptions_counter_gin ON l25_rm_remedy_prescriptions USING gin (counter_indications_array);
CREATE INDEX rm_prescriptions_embedding_hnsw ON l25_rm_remedy_prescriptions USING hnsw (prescription_embedding_vec vector_cosine_ops);
```

### Table 3 — `l25_rm_dasha_windowed_prescriptions` (temporal calibration)

```sql
CREATE TABLE l25_rm_dasha_windowed_prescriptions (
  window_prescription_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,
  base_prescription_id UUID NOT NULL REFERENCES l25_rm_remedy_prescriptions(prescription_id),
  dasha_system TEXT NOT NULL,                      -- vimshottari | chara_karaka | yogini
  dasha_level TEXT NOT NULL,                       -- maha | antar | pratyantar
  dasha_lord TEXT NOT NULL,
  window_start_iso TIMESTAMPTZ NOT NULL,
  window_end_iso TIMESTAMPTZ NOT NULL,
  window_intensity_multiplier NUMERIC,             -- amplification or suppression during this window
  schedule_jsonb JSONB,                            -- mandala/40-day/108-day/lifetime breakdown for this window
  phase_within_window TEXT,                        -- foundation | intensification | maintenance for this window
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT, citation_human TEXT, computed_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX rm_windowed_chart_idx ON l25_rm_dasha_windowed_prescriptions (chart_id, ayanamsha_id, dasha_system);
CREATE INDEX rm_windowed_time_idx ON l25_rm_dasha_windowed_prescriptions (chart_id, ayanamsha_id, window_start_iso, window_end_iso);
```

### Table 4 — `l25_rm_dosha_remedy_bundles`

```sql
CREATE TABLE l25_rm_dosha_remedy_bundles (
  bundle_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,
  dosha_class TEXT NOT NULL,                       -- mangal_dosha | kala_sarpa_dosha | pitra_dosha | sade_sati_phase_1..4 | ashtama_shani | kantaka_shani | ardha_ashtama_shani | guru_chandala | visha_yoga | grahana_dosha | shrapit_dosha | chandal_dosha | kemadruma | pretashanchaya
  active_flag BOOLEAN NOT NULL,
  intensity_score NUMERIC,
  cancellation_count INT,
  prescription_ids_in_bundle_array UUID[] NOT NULL,
  bundle_summary_jsonb JSONB,
  classical_source_citation_id TEXT NOT NULL,
  active_dasha_windows_jsonb JSONB,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, dosha_class)
);

CREATE INDEX rm_dosha_bundles_chart_idx ON l25_rm_dosha_remedy_bundles (chart_id, ayanamsha_id);
CREATE INDEX rm_dosha_bundles_active_idx ON l25_rm_dosha_remedy_bundles (chart_id, ayanamsha_id) WHERE active_flag = true;
```

### Table 5 — `l25_rm_pattern_remedies` (CDLM patterns + CGM motifs → remedy themes)

```sql
CREATE TABLE l25_rm_pattern_remedies (
  pattern_remedy_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,
  source_kind TEXT NOT NULL,                       -- cdlm_pattern_cluster | cgm_motif
  source_id UUID NOT NULL,
  remedy_theme TEXT NOT NULL,                      -- discipline_focused | compassion_expansion | speech_purification | ancestral_reconciliation | shadow_integration | etc.
  prescription_ids_array UUID[] NOT NULL,
  theme_strength NUMERIC,
  cross_tradition_unanimity_score NUMERIC,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT, citation_human TEXT, computed_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX rm_pattern_remedies_chart_idx ON l25_rm_pattern_remedies (chart_id, ayanamsha_id, source_kind);
```

### Table 6 — `l25_rm_chart_summary` (chart-level priority profile)

```sql
CREATE TABLE l25_rm_chart_summary (
  summary_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id, snapshot_type,
  top_3_resonance_targets_jsonb JSONB,
  top_10_priority_prescriptions_jsonb JSONB,
  recommended_intensity_class TEXT,                -- gentle | moderate | intense
  recommended_remedy_phase_sequence_jsonb JSONB,
  total_active_dosha_count INT,
  primary_dosha_class TEXT,
  cross_tradition_convergence_jsonb JSONB,
  remedy_chart_typology TEXT,                      -- simple_mantra_path | complex_multi_tradition | tantric_intensive | lifestyle_focused
  chart_remedy_embedding_vec VECTOR(768),
  acharya_review_required_count INT,
  feasibility_assessment_jsonb JSONB,              -- aggregate cost + daily time + ritual complexity
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT, citation_human TEXT, computed_at TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type)
);

CREATE INDEX rm_chart_summary_idx ON l25_rm_chart_summary (chart_id, ayanamsha_id);
CREATE INDEX rm_chart_summary_embedding_hnsw ON l25_rm_chart_summary USING hnsw (chart_remedy_embedding_vec vector_cosine_ops);
```

## §5 — Volume projection per (chart, ayanamsha)

| Component | Rows |
|---|---|
| Resonance targets (1 static + 38 Maha + 4 Sade Sati phases + ~10 transit hits) | ~55 |
| Remedy prescriptions (9 grahas × 6 traditions × ~10 active categories × salience filter) | ~350 |
| Dasha-windowed prescriptions (top-K × ~38 windows) | ~450 |
| Dosha bundles (~15 dosha classes) | ~15 |
| Pattern remedies (~10 CDLM patterns + ~30 CGM motifs) | ~40 |
| Chart summaries (per snapshot) | ~45 |

**Per (chart, ayanamsha): ~955 × 5 ayanamshas ≈ ~4,775 per chart.**
**For 20 charts: ~95K total rows.** Lightweight.

## §6 — G27 corpus pre-flight audit (parallel prerequisite)

Before A13 implementation kicks off, audit G27 for exhaustiveness:

```
G27_AUDIT_v1_0 brief authored at A13-impl kickoff. Coverage matrix:
  • For each of 6 traditions × 18 remedy categories × 9 grahas: confirm ≥1 G27 entry exists with classical source citation
  • Gap report: list missing (tradition, category, graha) tuples
  • Severity classification: BLOCKER (critical-tradition missing) | DEGRADED (1-2 categories missing) | ACCEPTABLE
  • If BLOCKER: pause A13 implementation; spawn G27 corpus enrichment sub-workstream
  • If DEGRADED: proceed with documented gap; mark missing tuples as 'no_classical_match_available' in A13 output
  • If ACCEPTABLE: proceed
```

Audit owner: A13 implementation Conductor session 1 (G27-AUDIT-S1) before A13-S1 begins.

## §7 — Verification

`verification_pass_status` mandatory `two_pass_verified`:

| Aspect | Primary | Secondary | Tertiary |
|---|---|---|---|
| Resonance score | Formula v1 + chart_state | Independent recomputation from facts | Sum-to-1 invariants on weakness components |
| Resonance-match score | Formula v1 + typology bias | Independent recomputation | — |
| Prescription → target binding | G27 lookup + tradition filter | Independent corpus walk | — |
| Counter-indications | Counter-indication rule engine | Independent rule cross-check | Classical text citation cross-check |
| Cross-tradition corroboration | Per-tradition prescription set intersection | Independent set algebra | — |
| Dasha-windowed scheduling | A7 chart_dashas window intersection | Independent date math | — |
| Dosha bundle activation | A8/A11 dosha detection + cancellation count | Independent rule cross-check | — |
| Feasibility scoring | Cost/time/complexity rubric | Independent recomputation | — |
| Embedding generation | Node2Vec/sentence-transformer on prescription text | Re-embed sample cross-check | Cosine similarity reproducibility |

Halt on divergent_flagged. Halt on G27 BLOCKER (per §6).

## §8 — Retrieval contract

- `query_rm_resonances(chart_id, ayanamsha_id, snapshot_type?, top_k=3)` → weakest grahas
- `query_rm_prescriptions_for_graha(chart_id, ayanamsha_id, graha, tradition?, category?)` → prescriptions
- `query_rm_dasha_windowed(chart_id, ayanamsha_id, date)` → active prescriptions for current Maha-Antar across 3 systems
- `query_rm_dosha_bundle(chart_id, ayanamsha_id, dosha_class)` → bundle with all prescriptions
- `query_rm_pattern_remedies(chart_id, ayanamsha_id, source_kind?, source_id?)` → theme-aligned prescriptions
- `query_rm_chart_summary(chart_id, ayanamsha_id, snapshot_type)` → summary row
- `query_rm_top_priority(chart_id, ayanamsha_id, top_k=10)` → top-K priority across all categories
- `query_rm_acharya_review_queue(chart_id, ayanamsha_id)` → prescriptions flagged for review
- `query_rm_feasibility_profile(chart_id, ayanamsha_id, intensity_class)` → filtered by client capacity
- `query_rm_similar_charts(chart_remedy_embedding, top_k=10)` → cross-chart remedy peer lookup
- `query_rm_phase_sequence(chart_id, ayanamsha_id, current_phase)` → next-phase recommendations
- `record_outcome(prescription_id, outcome_data)` → M6 outcome tracking (write path)

## §9 — Implementation notes

1. **WIPE existing l25_rm_*** rows before A13 writer runs (per Y).
2. **G27 audit (per §6) MUST run BEFORE A13-S1 kicks off.** Conductor session ordering: G27-AUDIT-S1 → A13-S1.
3. Compute order: A8/A10/A11/A12 finalized → resonance scoring per graha per snapshot → G27 corpus lookup per (graha, tradition, category) → prescription generation → counter-indication + compatibility check → resonance-match scoring → dasha-windowed scheduling → dosha bundle assembly → pattern/motif remedy theme derivation → phase sequencing → chronobiology timing → feasibility scoring → acharya-review flag application → embedding generation → chart summary assembly.
4. **pgvector embeddings**: 768-dim. Generated from prescription text (tradition + category + remedy_label_human + classical_source_text). Cosine HNSW index.
5. **Counter-indication enforcement**: rule engine evaluates each prescription against chart conditions; bundles failing checks get `requires_acharya_review_flag=true` plus `acharya_review_reason_array` populated.
6. **Cross-tradition convergence boost**: when ≥4 of 6 traditions independently recommend the same graha + category, log as `cross_tradition_convergence_jsonb` in chart_summary; mark as 'urgent' priority.
7. **Phase sequencing**: foundation (40 days) → intensification (108 days) → maintenance (lifetime daily). Phase boundaries documented per prescription.
8. **Chronobiology integration (AA)**: hora + choghadiya from A4 panchanga. Recommended timing arrays populated per prescription.

## §10 — Citations (dual form)

Examples:

| Row | citation_ref | citation_human |
|---|---|---|
| Saturn resonance target | `l25_rm_resonances.static_natal.SAT@chart=...:ay=lahiri:score=0.82` | "Saturn — weakest graha rank 1; resonance 0.82; affected by Sade Sati + Ashtama position (Lahiri)." |
| Saturn mantra (Parashari) | `l25_rm_remedy_prescriptions.parashari.mantra.G27_SAT_MANTRA_001@chart=...:ay=lahiri:match=0.91` | "Saturn Parashari mantra: 'Om Sham Shanaischaraya Namah' × 108 daily at sunset, Tuesday-Saturday; BPHS Ch.78 v.23; gentle; self-administered." |
| Tantric Saturn bija | `l25_rm_remedy_prescriptions.tantric_kaula.bija_mantra.G27_SAT_BIJA_007@...:ay=lahiri:match=0.85:review_required=true` | "Saturn Kaula Tantric bija: 'Om Pram Preem Praum Sah Shanaye Namah' × 1008 daily; Mantra Maharnava Ch.14; intense; tantric_initiation_required; review_required (tantric_heavy)." |
| Sade Sati Phase 2 bundle | `l25_rm_dosha_remedy_bundles.sade_sati_phase_2@chart=...:ay=lahiri:prescriptions=12` | "Sade Sati Phase 2 (Janma): bundle of 12 prescriptions including Hanuman Chalisa daily + Black sesame seed donation Saturdays + Iron ring on middle finger (BPHS Ch.71)." |
| Cross-tradition convergence | `l25_rm_chart_summary.cross_tradition_convergence.SAT_mantra@chart=...:ay=lahiri:traditions=4` | "Saturn mantra recommended by 4/6 traditions (Parashari + Tantric Mishra + KP + Lal Kitab) — urgent priority." |

## §11 — Cross-asset locks (cumulative)

| Asset | Lock | Status |
|---|---|---|
| A7 chart_dashas | Native PG range partitioning by period_start_iso | LOCKED in A12 §2.B |
| All ephemeris-derived facts | ephemeris_audit_jsonb (pyswisseph vs libephemeris JPL DE440 delta) | LOCKED in A12 §2.C |
| All graph compute | igraph C-core, no AGE | LOCKED in A12 §2.A |
| pgvector embeddings | 768-dim HNSW cosine | LOCKED in A12 §5 + A13 §4 |
| G27 corpus | exhaustiveness audit before A13-S1 | LOCKED in A13 §6 |

## §12 — What is NOT in A13 (out of scope)

- LLM in compute path — never (prime directive)
- Narrative remedy guidance — never (prime directive)
- Apache AGE / TimescaleDB / Spanner Graph — REJECTED per A12 Option E
- NumPyro Bayesian inference — DEFERRED to M6
- Acharya-tier remedy approval workflow UI — separate workstream (consumes A13 read-side)
- Outcome-feedback Bayesian update of resonance — DEFERRED to M6 (consumes A13 outcome_tracking_placeholder_jsonb)

## §13 — Final locked surface

1. 6-table storage (resonances + prescriptions + dasha_windowed + dosha_bundles + pattern_remedies + chart_summary)
2. 6 traditions × 18 remedy categories × per-graha fingerprint
3. Resonance score formula v1 (versioned, unit-tested) — weakness components + contradiction + domain + motif + yoga-karaka + chara-karaka amplifications
4. Resonance-match score formula v1 — typology-biased + cross-tradition boosted + pattern-aligned + counter-indication penalized
5. 3 dasha systems × Maha-Antar windowed temporal calibration
6. 4 Sade Sati phase bundles + ~15 dosha bundles
7. Pattern remedy themes from CDLM + CGM
8. Counter-indications + incompatibility checks + prerequisites
9. Feasibility scoring (cost + time + complexity)
10. Acharya-review flag + reason array
11. Cross-tradition corroboration boost
12. Phase sequencing (foundation/intensification/maintenance)
13. Substitute gem alternatives
14. Yantra geometry + pranapratishtha
15. Pilgrimage site mapping + priority
16. Chronobiology integration (hora + choghadiya + lunar phase + direction)
17. pgvector prescription_embedding + chart_remedy_embedding
18. M6 outcome_tracking_placeholder per prescription
19. Per-acharya sub-tradition variant support
20. G27 pre-flight audit declared parallel prerequisite
21. WIPE existing l25_rm_* rows before rebuild
22. Two-pass verification per row + ephemeris audit halt
23. ~4,775 rows per chart × 20 charts = ~95K total — lightweight

---

*End of A13_RM_SPEC_v1_0.md — LOCKED 2026-05-29. All 15 clarifications YES. All critical (A-Y) + non-critical (AA-CC) items included. Native sign-off complete.*
