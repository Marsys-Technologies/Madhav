---
artifact: A8_A11_A12_CROSS_CUTTING_AMENDMENTS_v1_0.md
document: Cross-cutting amendments to A8, A11, A12 — folding UCD truly-new items + magical nuggets B/C/D
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed: 5 UCD truly-new items + nuggets B/C/D land as column additions to existing summary tables)
---

# A8 + A11 + A12 cross-cutting amendments

## §0 — Mission

Fold the 5 UCD truly-new items + 3 magical nuggets (B, C, D) into A8/A11/A12 chart_summary tables. Zero new writer pipelines. Net: ~12 column additions across 3 existing tables.

## §1 — A8 spec amendments

Add to A8 chart_summary (or appropriate A8 aggregation row):

```sql
ALTER TABLE l1_a8_chart_summary
  ADD COLUMN purushartha_quadrant_strengths_jsonb JSONB,            -- {dharma: 0.78, artha: 0.62, kama: 0.45, moksha: 0.82, dominant: 'moksha'}
  ADD COLUMN dominant_purushartha TEXT,
  ADD COLUMN near_miss_yogas_jsonb JSONB,                            -- (NUGGET B): yogas that almost fire but blocked
  -- {yoga_name, missing_condition, blocked_by, classical_citation, structural_implication, severity_of_denial, activation_potential_conditions_jsonb, compensation_pathway_jsonb}[]
  ADD COLUMN near_miss_yoga_count INT,
  ADD COLUMN cross_tradition_near_miss_alignment_jsonb JSONB;
```

Per-graha amendment (NUGGET B, per-graha near-miss context):

```sql
ALTER TABLE l1_a8_graha_summary
  ADD COLUMN near_miss_yoga_constituent_array TEXT[];                -- which near-miss yogas this graha is part of
```

## §2 — A11 CDLM spec amendments

Add to `l25_cdlm_chart_summary`:

```sql
ALTER TABLE l25_cdlm_chart_summary
  ADD COLUMN classical_archetype_assignments_jsonb JSONB,           -- (UCD truly-new): G8 archetype library matches
  -- {primary: {archetype, confidence, matching_criteria}, alternates: [...], library_version}
  ADD COLUMN primary_classical_archetype TEXT,
  ADD COLUMN archetype_confidence NUMERIC,

  ADD COLUMN master_convergence_index NUMERIC,                      -- (UCD truly-new): 0-1 chart coherence
  ADD COLUMN master_convergence_decomposition_jsonb JSONB,          -- {cross_tradition: 0.85, cross_ayanamsha: 0.79, motif_clustering: 0.71, anti_yoga_rate: 0.62, ...}

  ADD COLUMN magnification_index_jsonb JSONB,                       -- (NUGGET D): structural points where ≥4 channels light up
  -- [{structural_point, channel_count, channels_array, amplification_class, time_varying_jsonb}, ...]
  ADD COLUMN anti_magnification_index_jsonb JSONB,                  -- (NUGGET D extension): where channels DISAGREE
  ADD COLUMN top_magnified_structural_points_array TEXT[];
```

## §3 — A12 CGM spec amendments

Add to `l25_cgm_chart_topology_summary`:

```sql
ALTER TABLE l25_cgm_chart_topology_summary
  ADD COLUMN karmic_signature_jsonb JSONB,                          -- (UCD truly-new): Rahu+Ketu+12H+outer planet aggregation
  -- {karmic_direction_summary, karmic_release_summary, past_life_indicators, karmic_axis_node, karmic_signature_class, karmic_signature_embedding_vec}
  ADD COLUMN karmic_signature_embedding_vec VECTOR(768),
  ADD COLUMN karmic_signature_class TEXT,

  ADD COLUMN arudha_lagna_divergence_score NUMERIC,                 -- (UCD truly-new): how much Arudha-self differs from Lagna-self
  ADD COLUMN arudha_lagna_divergence_jsonb JSONB,                   -- {visible_self_node, hidden_self_node, divergence_dimensions_array, divergence_per_dasha_jsonb}
  ADD COLUMN arudha_divergence_per_dasha_jsonb JSONB,               -- time-varying divergence

  ADD COLUMN chart_signature_embedding_vec VECTOR(768),             -- (UCD truly-new): chart-level signature embedding (different axis from topology_embedding_vec)
  ADD COLUMN dominant_theme_embedding_vec VECTOR(768),              -- (UCD truly-new): theme-axis embedding
  ADD COLUMN spiritual_progress_vector_jsonb JSONB;                 -- atma-karaka journey through dashas
```

Add to `l25_cgm_nodes` (NUGGET C — Recursive Influence Reach):

```sql
ALTER TABLE l25_cgm_nodes
  ADD COLUMN transitive_influence_reach_jsonb JSONB,                -- (NUGGET C): 2-3 hop reach
  -- {1_hop_targets, 2_hop_targets_via, 3_hop_targets_via, indirect_reach_score, decay_function_version, loop_detection_jsonb, asymmetry_jsonb, per_tradition_reach_jsonb}
  ADD COLUMN indirect_reach_score NUMERIC,
  ADD COLUMN karmic_feedback_loop_flag BOOLEAN,                     -- when influence chain loops back to self
  ADD COLUMN reach_embedding_vec VECTOR(768);                       -- per-graha reach pattern embedding for cohort comparison
```

## §4 — Magical nugget B (Anti-Yoga) extension details

For each detected near-miss yoga, populate:

```json
{
  "yoga_name": "gajakesari_yoga",
  "would_fire_if": ["jupiter_in_kendra_from_moon"],
  "blocked_by": {"factor": "jupiter_in_12H", "cancellation_class": "dusthana_placement"},
  "classical_citation": "BPHS_Ch_36_v_5",
  "structural_implication_class": "wisdom_seeking_blocked_by_renunciation",
  "severity_of_denial": 0.72,
  "activation_potential_conditions_jsonb": {
    "transit_required": "jupiter_aspect_to_moon_during_jupiter_maha",
    "dasha_window_required": "jupiter_or_moon_maha"
  },
  "compensation_pathway_jsonb": {
    "alternative_yoga_partial_firing": "lakshmi_yoga_via_venus_aspect",
    "compensating_factor": "moon_aspecting_jupiter_back"
  },
  "cross_tradition_near_miss_alignment": ["parashari", "phaladeepika", "saravali"]
}
```

## §5 — Magical nugget C (Recursive Influence Reach) details

For each graha node, compute via igraph BFS at depth 3:

```json
{
  "graha": "SAT",
  "1_hop_targets": [
    {"target": "SUN", "edge_type": "aspect_parashari", "edge_strength": 1.0},
    {"target": "MAR", "edge_type": "aspect_parashari", "edge_strength": 0.75},
    ...
  ],
  "2_hop_targets_via": [
    {"target": "MOO", "path": ["SAT", "SUN", "MOO"], "path_strength": 0.34, "decay_factor": 0.5},
    {"target": "VEN", "path": ["SAT", "HOUSE_5", "VEN"], "path_strength": 0.28, "decay_factor": 0.5}
  ],
  "3_hop_targets_via": [...],
  "indirect_reach_score": 0.67,
  "decay_function_version": "v1.0",
  "loop_detection_jsonb": {"karmic_loop_present": false, "loop_paths": []},
  "asymmetry_jsonb": {"SAT_to_MOO_reach": 0.34, "MOO_to_SAT_reach": 0.12, "asymmetry": 0.22},
  "per_tradition_reach_jsonb": {
    "parashari": {"1_hop_targets": [...], "indirect_reach_score": 0.65},
    "jaimini": {"1_hop_targets": [...], "indirect_reach_score": 0.71},
    ...
  }
}
```

Decay function: `path_strength = product(edge_strengths) × decay_factor^(hop_depth - 1)` with decay_factor = 0.5.

## §6 — Magical nugget D (Channel-Magnification Index) details

For each chart, scan all structural points and count how many of the 5 channels light it up:

```json
[
  {
    "structural_point": "SAT_in_9H",
    "channel_count": 5,
    "channels": ["A10_MSR_high_salience", "A11_CDLM_high_linkage", "A12_CGM_motif_member", "A13_RM_resonance_target", "A8_yoga_firing"],
    "amplification_class": "extreme",
    "time_varying_jsonb": {
      "vimshottari_sat_maha": {"channel_count_during_window": 5, "amplification_class": "extreme"},
      "vimshottari_jup_maha": {"channel_count_during_window": 3, "amplification_class": "medium"}
    },
    "cross_tradition_count": 4,
    "trajectory_class": "growing_with_age"
  }
]
```

Anti-magnification: same structural point where channels DISAGREE (one says weak, another says strong) → diagnostic contradiction.

## §7 — Cumulative impact

Net storage change per chart:
- ~5-6 new fields on A8 chart_summary
- ~5 new fields on A11 chart_summary
- ~7 new fields on A12 chart_topology_summary + 4 fields on l25_cgm_nodes

Net writer changes: ~3 additional compute passes appended to A8/A11/A12 close-out routines. No new writer pipelines.

Net storage cost: ~50 extra rows per chart (column additions, not row additions). Trivial.

Net LLM read-time gain: substantial. UCD becomes one tool call against joined chart_summaries; nugget B/C/D unlock structural-pattern depth.

## §8 — Final locked surface

1. A8: purushartha quadrants + dominant_purushartha + near_miss_yogas (NUGGET B)
2. A11: classical_archetype_assignments + master_convergence_index + magnification_index + anti_magnification (NUGGET D)
3. A12: karmic_signature + arudha_divergence + chart_signature_embedding + dominant_theme_embedding + spiritual_progress_vector + transitive_influence_reach (NUGGET C) on nodes
4. UCD = the conceptual surface exposed via `query_ucd()` retrieval tool that joins these 3 summary tables
5. Zero new writer pipelines
6. Per-chart impact: ~12 column additions, ~50 row equivalents

---

*End of A8_A11_A12_CROSS_CUTTING_AMENDMENTS_v1_0.md — LOCKED 2026-05-29.*
