---
artifact: TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md
document: Temporal Spine Enhancements — UTEE + Cross-Asset Bridges + META-ζ + A22 + per-tradition variants + falsifiability extensions
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed: full lock; integrate without redundancy; LLM-synthesis-optimized; thorough cross-asset audit)
intended_for: Claude Code sub-agents implementing the temporal-spine integration layer
prime_directive: One temporal-event shape for the synthesis LLM. Every temporal event uses the same envelope, surfaces the same outcome-tracking contract, and links to every other temporal event via explicit foreign keys. No narrative.
binds: A15 + A16 + A18 + A19 + A20 + A21 + NEW A22 + NEW META-ζ + NEW interaction table; RETRIEVAL_INTERFACE_REGISTER conformance
---

# Temporal Spine Enhancements Specification

## §0 — Mission

Bind the temporal-event spine (A15 + A16 + A18 + A19 + A20 + A21) into one coherent LLM-consumable surface:

1. **UTEE — Unified Temporal Event Envelope.** Every temporal event carries the same envelope-field schema. The LLM learns ONE shape, applies it everywhere.
2. **Cross-Asset Bridge Matrix.** Five FK column families + one interaction table making A15↔A16↔A18↔A19↔A20↔A21 relationships explicit.
3. **META-ζ — TEMPORAL_UNIFIED_LATTICE.** A range-query view UNIONing all six temporal sources with UTEE-projected envelope. Sibling to META-α (which handles single-moment queries).
4. **A22 — Per-Varsha Yearly Digest.** Yearly-resolution summary table joining all 5 temporal sources + active dashas + Sade Sati per varsha year.
5. **Per-tradition variants** for A15 (per-tradition convergence) + A18 (per-tradition vedha rules) where classically meaningful.
6. **Falsifiability + outcome ontology + M6 placeholder** extensions to A15 + A18 + A19 + A20 (currently only A16 carries these mandatorily).

Net result: the synthesis LLM gets ONE temporal-event surface with standardized shape, complete cross-asset linkage, M6-calibration-ready outcome tracking on every event, and three retrieval surfaces (META-α moment + META-ζ range + A22 yearly).

## §1 — UTEE — Unified Temporal Event Envelope

### §1.A — UTEE field dictionary

The canonical envelope every temporal-event row carries. Names are LLM-facing semantic — not internal Postgres conventions.

| UTEE field | Type | Semantics |
|---|---|---|
| `event_iso` | TIMESTAMPTZ | Canonical moment of the event |
| `event_window_start_iso` | TIMESTAMPTZ | Start of the event's effective window |
| `event_window_end_iso` | TIMESTAMPTZ | End of the event's effective window |
| `severity_normalized_0_1` | NUMERIC | Normalized severity/intensity (0-1) |
| `severity_decomposition_jsonb` | JSONB | Named-factor breakdown of severity |
| `confidence_normalized_0_1` | NUMERIC | Normalized confidence (0-1) |
| `confidence_class` | TEXT | 'high' \| 'medium' \| 'low' \| 'speculative' |
| `expected_outcome_class` | TEXT | Structured outcome category (drawn from ~30-class outcome ontology) |
| `outcome_ontology_class` | TEXT | 'binary' \| 'categorical' \| 'ordinal' \| 'continuous' |
| `outcome_ontology_definition_jsonb` | JSONB | Structured outcome shape (thresholds, magnitudes) |
| `falsifiability_statement` | TEXT | "If X is not observed by date Y, prediction was wrong" |
| `falsifier_date_iso` | TIMESTAMPTZ | Date by which the event must be observable |
| `cross_ayanamsha_stability_score` | NUMERIC | 0-1: how stable this event is across 5 ayanamshas |
| `per_tradition_variant_jsonb` | JSONB | {parashari: {...}, jaimini: {...}, tajik: {...}, kp: {...}} where applicable; NULL for single-tradition events |
| `inside_a15_cluster_ids_array` | UUID[] | A15 convergence cluster(s) this event belongs to |
| `associated_synchronicity_ids_array` | UUID[] | A15 synchronicity rows this event participates in |
| `feeder_event_ids_array` | UUID[] | Events that fed into this one (e.g., A21 exact aspects feeding A15 windows) |
| `mitigates_event_ids_array` | UUID[] | Events this event mitigates (e.g., A18 vedha mitigating A16 anchor) |
| `amplifies_event_ids_array` | UUID[] | Events this event amplifies |
| `seeds_anchor_ids_array` | UUID[] | A16 anchors this event seeds (e.g., A19 Bhrigu hit seeding anchor) |
| `mitigated_by_vedha_ids_array` | UUID[] | A18 vedhas mitigating this event |
| `channel_render_priority_jsonb` | JSONB | {chat, report, visual, audio, dashboard} per-channel priority |
| `temporal_event_embedding_vec` | VECTOR(768) | pgvector axis for cross-chart cohort similarity |
| `m6_outcome_tracking_placeholder_jsonb` | JSONB | empty {} at write; user populates via record_outcome |

### §1.B — Per-asset mapping (existing column ↔ UTEE field)

| UTEE field | A15 (Synchronicity) | A16 (Anchors) | A18 (Vedha) | A19 (Bhrigu) | A20 (Varsha) | A21 (Exact aspect) |
|---|---|---|---|---|---|---|
| event_iso | `date_iso` ✅ | `predicted_iso_window_centroid` ✅ | **ADD** | `transit_hit_iso` ✅ | `varsha_start_iso` ✅ | `exact_aspect_iso` ✅ |
| event_window_start_iso | `date_window_start_iso` ✅ | `predicted_iso_window_start` ✅ | **ADD** (from active_iso_window_array) | =transit_hit_iso ✅ | `varsha_start_iso` ✅ | `pre_exact_window_start_iso` ✅ |
| event_window_end_iso | `date_window_end_iso` ✅ | `predicted_iso_window_end` ✅ | **ADD** | =transit_hit_iso ✅ | `varsha_end_iso` ✅ | `post_exact_window_end_iso` ✅ |
| severity_normalized_0_1 | **ADD** (normalized from convergence_intensity) | **ADD** (normalized from expected_intensity) | **ADD** (from severity_class enum → 0-1) | **ADD** (normalized from transit_severity_score) | **ADD** | **ADD** (derive from aspect_intensity_class + orb) |
| severity_decomposition_jsonb | `convergence_intensity_decomposition_jsonb` ✅ | **ADD** (decompose expected_intensity) | **ADD** | **ADD** | **ADD** | **ADD** |
| confidence_normalized_0_1 | **ADD** | `prediction_confidence` ✅ | **ADD** | **ADD** | **ADD** | **ADD** (from ephemeris audit) |
| confidence_class | **ADD** | **ADD** | **ADD** | **ADD** | **ADD** | **ADD** |
| expected_outcome_class | **ADD** | `expected_outcome_class` ✅ | **ADD** | **ADD** | **ADD** | **ADD** |
| outcome_ontology_class | **ADD** | `outcome_ontology_class` ✅ | **ADD** | **ADD** | **ADD** | **ADD** |
| outcome_ontology_definition_jsonb | **ADD** | `outcome_ontology_definition_jsonb` ✅ | **ADD** | **ADD** | **ADD** | **ADD** |
| falsifiability_statement | **ADD** | `falsifiability_statement` ✅ (mandatory) | **ADD** | **ADD** | **ADD** | **ADD** |
| falsifier_date_iso | **ADD** | `falsifier_date_iso` ✅ | **ADD** | **ADD** | **ADD** | **ADD** |
| cross_ayanamsha_stability_score | **ADD** | **ADD** | **ADD** | **ADD** | **ADD** | **ADD** |
| per_tradition_variant_jsonb | **ADD** | `per-variant anchor FKs exist; add jsonb summary` | **ADD** | NULL (Nadi-only) | NULL (Tajik-only) | **ADD** |
| inside_a15_cluster_ids_array | `convergence_cluster_id` (single) → **CONVERT to array** | **ADD** | **ADD** (active_during_a15_cluster_ids_array existed implicitly; formalize) | **ADD** | **ADD** | **ADD** |
| associated_synchronicity_ids_array | (self — own id) | `associated_synchronicity_id` (single) → **CONVERT to array** | **ADD** | **ADD** | **ADD** | **ADD** |
| feeder_event_ids_array | `feeder_assets_array` text → **CONVERT to event_ids_array UUID[]** | **ADD** | (n/a) | (n/a) | (n/a) | (n/a) |
| mitigates_event_ids_array | (n/a) | (n/a) | **ADD** | (n/a) | (n/a) | (n/a) |
| amplifies_event_ids_array | (n/a) | (n/a) | **ADD** | **ADD** (Bhrigu can amplify anchors) | **ADD** (varsha can amplify anchors) | (n/a) |
| seeds_anchor_ids_array | (n/a) | (n/a) | (n/a) | **ADD** | **ADD** | (n/a) |
| mitigated_by_vedha_ids_array | (n/a) | **ADD** | (n/a) | (n/a) | (n/a) | (n/a) |
| channel_render_priority_jsonb | already present ✅ | **ADD** | **ADD** | **ADD** | **ADD** | **ADD** |
| temporal_event_embedding_vec | `window_embedding_vec` ✅ | `anchor_embedding_vec` ✅ | **ADD** | **ADD** | **ADD** | **ADD** |
| m6_outcome_tracking_placeholder_jsonb | **ADD** | `outcome_tracking_placeholder_jsonb` ✅ | **ADD** | **ADD** | **ADD** | **ADD** |

**Legend**: ✅ = column already exists; can be aliased in UTEE view. **ADD** = new ALTER TABLE column.

**Redundancy audit confirmed**: Existing column names are preserved where they already match UTEE semantics. New columns added ONLY where the field doesn't already exist. The META-ζ view uses CASE / COALESCE aliasing to project the canonical UTEE shape from whichever underlying column is the source of truth.

### §1.C — ALTER TABLE statements (consolidated)

A15 (`l25_time_synchronicity`):
```sql
ALTER TABLE l25_time_synchronicity
  ADD COLUMN severity_normalized_0_1 NUMERIC,
  ADD COLUMN confidence_normalized_0_1 NUMERIC,
  ADD COLUMN confidence_class TEXT,
  ADD COLUMN expected_outcome_class TEXT,
  ADD COLUMN outcome_ontology_class TEXT,
  ADD COLUMN outcome_ontology_definition_jsonb JSONB,
  ADD COLUMN falsifiability_statement TEXT,
  ADD COLUMN falsifier_date_iso TIMESTAMPTZ,
  ADD COLUMN cross_ayanamsha_stability_score NUMERIC,
  ADD COLUMN per_tradition_variant_jsonb JSONB,
  ADD COLUMN feeder_event_ids_array UUID[],
  ADD COLUMN m6_outcome_tracking_placeholder_jsonb JSONB;
-- Note: convergence_cluster_id (single) is preserved; UTEE view maps it to inside_a15_cluster_ids_array.
```

A16 (`l25_phase_locked_event_anchors`):
```sql
ALTER TABLE l25_phase_locked_event_anchors
  ADD COLUMN severity_normalized_0_1 NUMERIC,
  ADD COLUMN severity_decomposition_jsonb JSONB,
  ADD COLUMN confidence_class TEXT,
  ADD COLUMN cross_ayanamsha_stability_score NUMERIC,
  ADD COLUMN per_tradition_variant_jsonb JSONB,
  ADD COLUMN inside_a15_cluster_ids_array UUID[],
  ADD COLUMN mitigated_by_vedha_ids_array UUID[],
  ADD COLUMN seeded_by_bhrigu_hit_ids_array UUID[],
  ADD COLUMN varsha_year_lord_context_id UUID,
  ADD COLUMN feeder_event_kinds_array TEXT[],
  ADD COLUMN channel_render_priority_jsonb JSONB;
-- Note: associated_synchronicity_id preserved; UTEE view maps to associated_synchronicity_ids_array.
```

A18 (`l25_vedha_calculations`):
```sql
ALTER TABLE l25_vedha_calculations
  ADD COLUMN event_iso TIMESTAMPTZ,                       -- centroid of active window
  ADD COLUMN event_window_start_iso TIMESTAMPTZ,
  ADD COLUMN event_window_end_iso TIMESTAMPTZ,
  ADD COLUMN severity_normalized_0_1 NUMERIC,
  ADD COLUMN severity_decomposition_jsonb JSONB,
  ADD COLUMN confidence_normalized_0_1 NUMERIC,
  ADD COLUMN confidence_class TEXT,
  ADD COLUMN expected_outcome_class TEXT,
  ADD COLUMN outcome_ontology_class TEXT,
  ADD COLUMN outcome_ontology_definition_jsonb JSONB,
  ADD COLUMN falsifiability_statement TEXT,
  ADD COLUMN falsifier_date_iso TIMESTAMPTZ,
  ADD COLUMN cross_ayanamsha_stability_score NUMERIC,
  ADD COLUMN per_tradition_variant_jsonb JSONB,
  ADD COLUMN applicable_tradition_ids_array TEXT[],         -- per-tradition variant tag list
  ADD COLUMN inside_a15_cluster_ids_array UUID[],
  ADD COLUMN active_during_a15_cluster_ids_array UUID[],
  ADD COLUMN associated_synchronicity_ids_array UUID[],
  ADD COLUMN mitigates_anchor_ids_array UUID[],
  ADD COLUMN channel_render_priority_jsonb JSONB,
  ADD COLUMN temporal_event_embedding_vec VECTOR(768),
  ADD COLUMN m6_outcome_tracking_placeholder_jsonb JSONB;
```

A19 (`l1_bhrigu_bindu_transits`):
```sql
ALTER TABLE l1_bhrigu_bindu_transits
  ADD COLUMN event_iso TIMESTAMPTZ,                       -- = transit_hit_iso
  ADD COLUMN event_window_start_iso TIMESTAMPTZ,
  ADD COLUMN event_window_end_iso TIMESTAMPTZ,
  ADD COLUMN severity_normalized_0_1 NUMERIC,
  ADD COLUMN severity_decomposition_jsonb JSONB,
  ADD COLUMN confidence_normalized_0_1 NUMERIC,
  ADD COLUMN confidence_class TEXT,
  ADD COLUMN expected_outcome_class TEXT,
  ADD COLUMN outcome_ontology_class TEXT,
  ADD COLUMN outcome_ontology_definition_jsonb JSONB,
  ADD COLUMN falsifiability_statement TEXT,
  ADD COLUMN falsifier_date_iso TIMESTAMPTZ,
  ADD COLUMN cross_ayanamsha_stability_score NUMERIC,
  ADD COLUMN inside_a15_cluster_ids_array UUID[],
  ADD COLUMN associated_synchronicity_ids_array UUID[],
  ADD COLUMN seeds_anchor_ids_array UUID[],
  ADD COLUMN amplifies_event_ids_array UUID[],
  ADD COLUMN channel_render_priority_jsonb JSONB,
  ADD COLUMN temporal_event_embedding_vec VECTOR(768),
  ADD COLUMN m6_outcome_tracking_placeholder_jsonb JSONB;
```

A20 (`l1_tajik_varsha_year_lords`):
```sql
ALTER TABLE l1_tajik_varsha_year_lords
  ADD COLUMN event_iso TIMESTAMPTZ,                       -- = varsha_start_iso
  ADD COLUMN event_window_start_iso TIMESTAMPTZ,
  ADD COLUMN event_window_end_iso TIMESTAMPTZ,
  ADD COLUMN severity_normalized_0_1 NUMERIC,
  ADD COLUMN severity_decomposition_jsonb JSONB,
  ADD COLUMN confidence_normalized_0_1 NUMERIC,
  ADD COLUMN confidence_class TEXT,
  ADD COLUMN expected_outcome_class TEXT,
  ADD COLUMN outcome_ontology_class TEXT,
  ADD COLUMN outcome_ontology_definition_jsonb JSONB,
  ADD COLUMN falsifiability_statement TEXT,
  ADD COLUMN falsifier_date_iso TIMESTAMPTZ,
  ADD COLUMN cross_ayanamsha_stability_score NUMERIC,
  ADD COLUMN inside_a15_cluster_ids_array UUID[],
  ADD COLUMN associated_synchronicity_ids_array UUID[],
  ADD COLUMN seeds_anchor_ids_array UUID[],
  ADD COLUMN amplifies_event_ids_array UUID[],
  ADD COLUMN channel_render_priority_jsonb JSONB,
  ADD COLUMN temporal_event_embedding_vec VECTOR(768),
  ADD COLUMN m6_outcome_tracking_placeholder_jsonb JSONB;
```

A21 (`l1_exact_aspect_lifetime`):
```sql
ALTER TABLE l1_exact_aspect_lifetime
  ADD COLUMN event_iso TIMESTAMPTZ,                       -- = exact_aspect_iso
  ADD COLUMN event_window_start_iso TIMESTAMPTZ,
  ADD COLUMN event_window_end_iso TIMESTAMPTZ,
  ADD COLUMN severity_normalized_0_1 NUMERIC,
  ADD COLUMN severity_decomposition_jsonb JSONB,
  ADD COLUMN confidence_normalized_0_1 NUMERIC,
  ADD COLUMN confidence_class TEXT,
  ADD COLUMN expected_outcome_class TEXT,
  ADD COLUMN outcome_ontology_class TEXT,
  ADD COLUMN cross_ayanamsha_stability_score NUMERIC,
  ADD COLUMN per_tradition_variant_jsonb JSONB,
  ADD COLUMN inside_a15_cluster_ids_array UUID[],
  ADD COLUMN associated_synchronicity_ids_array UUID[],
  ADD COLUMN seeds_anchor_ids_array UUID[],
  ADD COLUMN channel_render_priority_jsonb JSONB,
  ADD COLUMN temporal_event_embedding_vec VECTOR(768),
  ADD COLUMN m6_outcome_tracking_placeholder_jsonb JSONB;
```

## §2 — Cross-Asset Bridge Matrix

### §2.A — FK column additions (covered in §1.C above)

| Bridge | Direction | Where it lives |
|---|---|---|
| A18 vedha mitigates A16 anchor | A18 → A16 | `mitigates_anchor_ids_array` on A18 + `mitigated_by_vedha_ids_array` on A16 + interaction row |
| A19 Bhrigu hit seeds A16 anchor | A19 → A16 | `seeds_anchor_ids_array` on A19 + `seeded_by_bhrigu_hit_ids_array` on A16 |
| A20 varsha year-lord seeds A16 anchor | A20 → A16 | `seeds_anchor_ids_array` on A20 + `varsha_year_lord_context_id` on A16 |
| A21 exact-aspect feeds A15 window | A21 → A15 | `feeder_event_ids_array` on A15 + `seeds_anchor_ids_array` on A21 |
| Event inside A15 cluster (all assets) | all → A15 | `inside_a15_cluster_ids_array` on every UTEE-extended table |
| Event inside A15 synchronicity window | all → A15 | `associated_synchronicity_ids_array` on every UTEE-extended table |

### §2.B — `l25_vedha_anchor_interactions` (NEW interaction table)

When A18 vedha is active during A16 anchor window, this row captures the resolved interaction:

```sql
CREATE TABLE l25_vedha_anchor_interactions (
  interaction_id UUID PRIMARY KEY,
  chart_id UUID NOT NULL, ayanamsha_id TEXT NOT NULL, build_id UUID NOT NULL,
  vedha_id UUID NOT NULL REFERENCES l25_vedha_calculations(vedha_id),
  anchor_id UUID NOT NULL REFERENCES l25_phase_locked_event_anchors(anchor_id),

  interaction_class TEXT NOT NULL,                  -- 'full_mitigation' | 'partial_mitigation' | 'inversion' | 'amplification' | 'neutralizing'
  mitigation_strength NUMERIC,                      -- 0-1; how strongly the vedha mitigates
  expected_outcome_modification_class TEXT,         -- how the outcome changes
  severity_after_mitigation NUMERIC,                -- new normalized severity post-resolution
  confidence_after_mitigation NUMERIC,              -- new confidence post-resolution

  classical_resolution_methodology TEXT,            -- the rule used to resolve
  classical_citation TEXT NOT NULL,

  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL,

  UNIQUE (chart_id, ayanamsha_id, build_id, vedha_id, anchor_id)
);

CREATE INDEX vai_chart_idx ON l25_vedha_anchor_interactions (chart_id, ayanamsha_id);
CREATE INDEX vai_anchor_idx ON l25_vedha_anchor_interactions (anchor_id);
CREATE INDEX vai_vedha_idx ON l25_vedha_anchor_interactions (vedha_id);
```

Volume: ~50-100 interactions per chart. Trivial.

The retrieval contract: when LLM asks for A16 anchors, it gets the row plus the post-mitigation severity from this interaction table. The original anchor severity is preserved; the resolved severity is the surfaced default.

## §3 — META-ζ — TEMPORAL_UNIFIED_LATTICE

### §3.A — Mission

Range-query equivalent of META-α LATTICE. One query: "all temporal events between dates X and Y for chart C" returns rows from all 6 sources unified to UTEE shape.

### §3.B — Implementation

```sql
CREATE VIEW vw_temporal_unified_lattice AS
  SELECT 'A15' AS source_asset, synchronicity_id AS source_row_id,
         chart_id, ayanamsha_id, build_id,
         date_iso AS event_iso,
         date_window_start_iso AS event_window_start_iso,
         date_window_end_iso AS event_window_end_iso,
         severity_normalized_0_1, severity_decomposition_jsonb,
         confidence_normalized_0_1, confidence_class,
         expected_outcome_class, outcome_ontology_class, outcome_ontology_definition_jsonb,
         falsifiability_statement, falsifier_date_iso,
         cross_ayanamsha_stability_score, per_tradition_variant_jsonb,
         ARRAY[convergence_cluster_id]::UUID[] AS inside_a15_cluster_ids_array,
         ARRAY[synchronicity_id]::UUID[] AS associated_synchronicity_ids_array,
         feeder_event_ids_array,
         NULL::UUID[] AS mitigates_event_ids_array,
         NULL::UUID[] AS amplifies_event_ids_array,
         NULL::UUID[] AS seeds_anchor_ids_array,
         NULL::UUID[] AS mitigated_by_vedha_ids_array,
         channel_render_priority_jsonb,
         window_embedding_vec AS temporal_event_embedding_vec,
         m6_outcome_tracking_placeholder_jsonb,
         citation_ref, citation_human, computed_at
  FROM l25_time_synchronicity
  UNION ALL
  SELECT 'A16' AS source_asset, anchor_id AS source_row_id,
         chart_id, ayanamsha_id, build_id,
         predicted_iso_window_centroid AS event_iso,
         predicted_iso_window_start AS event_window_start_iso,
         predicted_iso_window_end AS event_window_end_iso,
         severity_normalized_0_1, severity_decomposition_jsonb,
         prediction_confidence AS confidence_normalized_0_1, confidence_class,
         expected_outcome_class, outcome_ontology_class, outcome_ontology_definition_jsonb,
         falsifiability_statement, falsifier_date_iso,
         cross_ayanamsha_stability_score, per_tradition_variant_jsonb,
         inside_a15_cluster_ids_array,
         ARRAY[associated_synchronicity_id]::UUID[] AS associated_synchronicity_ids_array,
         NULL::UUID[] AS feeder_event_ids_array,
         NULL::UUID[] AS mitigates_event_ids_array,
         NULL::UUID[] AS amplifies_event_ids_array,
         NULL::UUID[] AS seeds_anchor_ids_array,
         mitigated_by_vedha_ids_array,
         channel_render_priority_jsonb,
         anchor_embedding_vec AS temporal_event_embedding_vec,
         outcome_tracking_placeholder_jsonb AS m6_outcome_tracking_placeholder_jsonb,
         citation_ref, citation_human, computed_at
  FROM l25_phase_locked_event_anchors
  UNION ALL
  SELECT 'A18' AS source_asset, vedha_id AS source_row_id, ...
  FROM l25_vedha_calculations
  UNION ALL
  SELECT 'A19' AS source_asset, transit_id AS source_row_id, ...
  FROM l1_bhrigu_bindu_transits
  UNION ALL
  SELECT 'A20' AS source_asset, varsha_id AS source_row_id, ...
  FROM l1_tajik_varsha_year_lords
  UNION ALL
  SELECT 'A21' AS source_asset, aspect_event_id AS source_row_id, ...
  FROM l1_exact_aspect_lifetime
  UNION ALL
  SELECT 'A22' AS source_asset, digest_id AS source_row_id, ...
  FROM l25_per_varsha_digest;
```

Index strategy: every UTEE-extended underlying table has its `event_iso` column indexed, so range queries against the view push predicates down efficiently. No materialization needed.

### §3.C — Retrieval tools

- `query_temporal_events_in_range(chart_id, ayanamsha_id, start_iso, end_iso, source_asset_filter?, severity_min?, confidence_min?, kinds_array?)` → UTEE-shaped rows
- `query_temporal_events_next(chart_id, ayanamsha_id, from_date, source_asset_filter?)` → next N events
- `query_temporal_events_within_a15_cluster(cluster_id)` → all member events
- `query_temporal_events_seeded_by(seed_event_id)` → A16 anchors seeded by this event
- `query_temporal_events_mitigated_by(vedha_id)` → A16 anchors this vedha affects
- `query_temporal_event_peers(temporal_event_embedding, top_k=10)` → cross-chart cohort

Each tool returns UTEE shape so the LLM has one parsing path.

## §4 — A22 — Per-Varsha Yearly Digest

### §4.A — Mission

Yearly-resolution summary table joining all temporal sources + active dashas + Sade Sati per varsha year (Tajik birth-year-relative). Powers "tell me about year N" queries instantly.

### §4.B — Storage

```sql
CREATE TABLE l25_per_varsha_digest (
  digest_id UUID PRIMARY KEY,
  chart_id UUID NOT NULL, ayanamsha_id TEXT NOT NULL, build_id UUID NOT NULL,
  varsha_year INT NOT NULL,                          -- 1, 2, ..., 150
  varsha_start_iso TIMESTAMPTZ NOT NULL,
  varsha_end_iso TIMESTAMPTZ NOT NULL,
  age_at_varsha_start INT,

  -- A15 windows in this varsha
  a15_high_resonance_window_ids_array UUID[],
  a15_convergence_cluster_ids_array UUID[],
  a15_total_window_count INT,
  a15_extreme_resonance_count INT,
  a15_top_window_intensity NUMERIC,

  -- A16 anchors firing
  a16_anchor_ids_array UUID[],
  a16_top_anchor_id UUID,
  a16_high_confidence_anchor_count INT,
  a16_anchor_confidence_aggregate NUMERIC,
  a16_anchor_themes_array TEXT[],
  a16_predicted_event_classes_array TEXT[],

  -- A18 active vedhas
  a18_active_vedha_ids_array UUID[],
  a18_active_vedha_count INT,
  a18_severe_vedha_count INT,

  -- A19 Bhrigu hits
  a19_bhrigu_hit_ids_array UUID[],
  a19_bhrigu_hit_count INT,
  a19_major_hit_ids_array UUID[],

  -- A20 year-lord context (denormalized from l1_tajik_varsha_year_lords for fast lookup)
  a20_varsha_id UUID REFERENCES l1_tajik_varsha_year_lords(varsha_id),
  year_lord TEXT,
  year_lord_method TEXT,
  hadda_context_jsonb JSONB,
  muntha_position_jsonb JSONB,
  applicable_tajik_yogas_array TEXT[],

  -- A21 exact aspects in varsha
  a21_exact_aspect_event_ids_array UUID[],
  a21_high_severity_aspect_count INT,

  -- Active dashas during this varsha (composite from A7)
  active_vimshottari_lords_jsonb JSONB,              -- {maha, antar, pratyantar with transition dates}
  active_chara_lords_jsonb JSONB,
  active_yogini_lords_jsonb JSONB,

  -- Active Sade Sati phase
  sade_sati_active_during_varsha_jsonb JSONB,

  -- Aggregate
  total_temporal_event_count INT,
  varsha_intensity_aggregate NUMERIC,
  predicted_year_theme_class TEXT,                   -- aggregate predicted theme
  predicted_event_class_distribution_jsonb JSONB,    -- distribution across A16 anchors

  -- UTEE envelope (the varsha IS a temporal event)
  event_iso TIMESTAMPTZ NOT NULL,                    -- = varsha_start_iso
  event_window_start_iso TIMESTAMPTZ NOT NULL,
  event_window_end_iso TIMESTAMPTZ NOT NULL,
  severity_normalized_0_1 NUMERIC,
  severity_decomposition_jsonb JSONB,
  confidence_normalized_0_1 NUMERIC,
  confidence_class TEXT,
  expected_outcome_class TEXT,
  outcome_ontology_class TEXT,
  outcome_ontology_definition_jsonb JSONB,
  falsifiability_statement TEXT,
  falsifier_date_iso TIMESTAMPTZ,
  cross_ayanamsha_stability_score NUMERIC,
  per_tradition_variant_jsonb JSONB,
  inside_a15_cluster_ids_array UUID[],
  associated_synchronicity_ids_array UUID[],
  channel_render_priority_jsonb JSONB,
  temporal_event_embedding_vec VECTOR(768),
  m6_outcome_tracking_placeholder_jsonb JSONB,

  ephemeris_audit_jsonb JSONB,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL,

  UNIQUE (chart_id, ayanamsha_id, build_id, varsha_year)
);

CREATE INDEX varsha_digest_chart_idx ON l25_per_varsha_digest (chart_id, ayanamsha_id, varsha_year);
CREATE INDEX varsha_digest_intensity_idx ON l25_per_varsha_digest (chart_id, ayanamsha_id, varsha_intensity_aggregate DESC);
CREATE INDEX varsha_digest_event_iso_idx ON l25_per_varsha_digest (chart_id, ayanamsha_id, event_iso);
CREATE INDEX varsha_digest_embedding_hnsw ON l25_per_varsha_digest USING hnsw (temporal_event_embedding_vec vector_cosine_ops);
```

Volume: 150 varsha × 5 ayanamshas = 750 per chart.

### §4.C — Retrieval tools

- `query_varsha_digest(chart_id, ayanamsha_id, varsha_year)` → single varsha row
- `query_varsha_digest_for_date(chart_id, ayanamsha_id, date_iso)` → which varsha contains this date
- `query_varsha_digest_range(chart_id, ayanamsha_id, start_year, end_year)` → range
- `query_top_intensity_varshas(chart_id, ayanamsha_id, top_k=5)` → highest-intensity years
- `query_varsha_peers(varsha_embedding, top_k=10)` → cross-chart varsha cohort

## §5 — Per-tradition variants

### §5.A — A15 per-tradition convergence

A15 currently emits one row per (chart × ayanamsha × date). Per-tradition variants would explode this 4×. Instead, add `per_tradition_variant_jsonb` containing per-tradition convergence detail:

```json
{
  "parashari": {"convergence_count": 4, "convergence_intensity": 0.62, "active_cycles_array": [...]},
  "jaimini": {"convergence_count": 3, "convergence_intensity": 0.51, "active_cycles_array": [...]},
  "tajik": {"convergence_count": 5, "convergence_intensity": 0.78, "active_cycles_array": [...]},
  "kp": {"convergence_count": 4, "convergence_intensity": 0.64, "active_cycles_array": [...]}
}
```

LLM queries: `query_synchronicity_at_date(..., tradition='tajik')` returns the row with `per_tradition_variant_jsonb.tajik` projected forward as the canonical convergence_intensity. Defaults to aggregate when no tradition specified.

### §5.B — A18 per-tradition vedha rules

A18 currently has one tradition's rules. Add `applicable_tradition_ids_array TEXT[]` to flag which traditions recognize the vedha. Same vedha row can be tradition-shared:

```
vedha_id=X, vedha_type='nakshatra', applicable_tradition_ids_array=['parashari', 'jaimini', 'phaladeepika'], blocked_position='MOO_NAK_ROHINI', source_position='SAT_NAK_VISHAKHA'
```

LLM queries: `query_vedhas(..., tradition='jaimini')` filters to vedhas where 'jaimini' is in applicable_tradition_ids_array.

### §5.C — A21 per-tradition aspect types

A21 already has aspect_type enum that includes Parashari (3/7/10) and Tajik (ithasala etc.). The per_tradition_variant_jsonb captures which tradition emits which aspect_type. Confirmed already covered.

## §6 — Falsifiability + outcome ontology extensions

Per §1.C, falsifiability_statement + falsifier_date_iso + outcome ontology fields + M6 outcome_tracking_placeholder are now added to A15 / A18 / A19 / A20 / A21 / A22 (previously only A16 had them mandatorily).

Compute rules for each:

| Asset | Falsifiability rule example |
|---|---|
| A15 (Synchronicity) | "If high-resonance window 2028-03-15 ±30d produces no observable life event in observable_event_class within falsifier_date 2028-09-15, prediction wrong" |
| A18 (Vedha) | "If vedha activation 2028-Q3 produces no obstruction in expected_outcome_class by falsifier_date end-of-period, mitigation occurred or prediction wrong" |
| A19 (Bhrigu Bindu) | "If transit Saturn-on-Bhrigu-Bindu 2031-Jun produces no major life event in expected_outcome_class by 2031-Dec, prediction wrong" |
| A20 (Varsha) | "If varsha 2028 produces no theme of expected_outcome_class in observable form, year-lord interpretation wrong" |
| A21 (Exact aspect) | "If exact Saturn-Mars opposition on 2028-04-12 produces no observable event in expected_outcome_class within ±30d, prediction wrong" |

Every M6 outcome_tracking_placeholder allows record_outcome at the appropriate event_id to feed calibration.

## §7 — Cumulative impact

| Layer | Per-chart rows |
|---|---|
| UTEE column additions to A15/A16/A18/A19/A20/A21 | 0 new rows (column adds) |
| Vedha-Anchor interaction table | ~100 rows |
| META-ζ TEMPORAL_UNIFIED_LATTICE view | 0 (view) |
| A22 Per-Varsha Yearly Digest | ~750 rows |
| Per-tradition variants on A15 | 0 (JSONB-only) |
| Per-tradition variants on A18 | 0 (array column) |
| **Net additional rows per chart** | **~850** |

Storage cost: trivial. Retrieval leverage gain: every temporal-event question becomes one tool call with one shape.

## §8 — Retrieval Interface Register additions

Tools added per `RETRIEVAL_INTERFACE_REGISTER_v1_0.md` standards (input/output envelope + 5 channels + 3-tier filtering + citations + LLM-facing description):

| New tool | Source asset / view |
|---|---|
| `query_temporal_events_in_range` | META-ζ view (UTEE-shape; all 7 sources) |
| `query_temporal_events_next` | META-ζ view |
| `query_temporal_events_within_a15_cluster` | META-ζ view |
| `query_temporal_events_seeded_by` | META-ζ + FK walk |
| `query_temporal_events_mitigated_by` | META-ζ + vedha-anchor interactions |
| `query_temporal_event_peers` | META-ζ + temporal_event_embedding |
| `query_varsha_digest` | A22 |
| `query_varsha_digest_for_date` | A22 |
| `query_varsha_digest_range` | A22 |
| `query_top_intensity_varshas` | A22 |
| `query_varsha_peers` | A22 |
| `query_vedha_anchor_interactions` | l25_vedha_anchor_interactions |
| `query_synchronicity_per_tradition` | A15 with per_tradition_variant_jsonb projection |
| `query_vedhas_per_tradition` | A18 with applicable_tradition_ids filter |

Net new retrieval tools: ~14. Updated target retrieval surface: **~141 MCP tools** (revised from prior 127).

CAPABILITY_MANIFEST.json must be updated at A22 + META-ζ implementation close.

## §9 — Verification updates

Two-pass continues. Added invariants:

| Aspect | Invariant |
|---|---|
| UTEE envelope completeness | every UTEE-extended table has all envelope columns populated for active rows |
| Cross-FK integrity | every `inside_a15_cluster_id` resolves to existing cluster; every `mitigates_anchor_ids_array` entry resolves; every `seeds_anchor_ids_array` entry resolves |
| Falsifier date ≥ event_window_end | falsifier_date_iso must be ≥ event_window_end_iso |
| Severity normalization | all severity_normalized_0_1 in range [0, 1] |
| Confidence normalization | all confidence_normalized_0_1 in range [0, 1] |
| Tradition variant consistency | per_tradition_variant_jsonb keys match declared `applicable_tradition_ids_array` |
| Interaction-table consistency | every (vedha_id, anchor_id) interaction row corresponds to vedha and anchor windows that overlap |
| Vedha mitigation symmetry | A18.mitigates_anchor_ids_array X ↔ A16.mitigated_by_vedha_ids_array Y (bidirectional consistency) |
| A22 aggregation correctness | every A22 row's array fields list event_ids actually within its varsha window |

Halt on divergent_flagged.

## §10 — Build dependency order

A21 + A19 + A18 + A20 must complete BEFORE A15 (A15 consumes their events).
A15 must complete BEFORE A16 (A16 consumes A15 cluster membership + synchronicity associations).
A15 + A16 + A18 + A19 + A20 + A21 must complete BEFORE A22 (A22 aggregates yearly).
A22 must complete BEFORE META-ζ view materializes (view UNIONs include A22).
Vedha-Anchor interactions resolved AFTER A16 close.

Conductor session order: A17 → A18 → A19 → A20 → A21 → A15 → A16 → A22 → META-ζ refresh → Vedha-Anchor interactions.

## §11 — Final locked surface

1. UTEE — unified envelope standardized across A15+A16+A18+A19+A20+A21+A22
2. Cross-Asset Bridge Matrix — FK columns + 1 new interaction table
3. META-ζ — TEMPORAL_UNIFIED_LATTICE view, range-query surface across all 7 temporal sources
4. A22 — Per-Varsha Yearly Digest table, yearly-resolution summary
5. Per-tradition variants — A15 jsonb + A18 array; LLM-queryable per tradition
6. Falsifiability + outcome ontology + M6 placeholder — extended to A15+A18+A19+A20+A21+A22 (previously only A16)
7. ~14 new MCP retrieval tools registered (RETRIEVAL_INTERFACE_REGISTER updated; target ~141)
8. Build dependency order codified
9. Two-pass verification invariants extended
10. Net ~850 additional rows per chart; zero net new writer pipelines beyond A22 + interaction table

The synthesis LLM now has: **one envelope shape, one moment-in-time tool (META-α), one range-query tool (META-ζ), one yearly-digest tool (A22), and full cross-asset linkage between every temporal event.** Every temporal event is M6-calibration-ready.

---

*End of TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md — LOCKED 2026-05-29.*
