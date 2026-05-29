---
artifact: A16_PHASE_LOCKED_EVENT_ANCHORS_SPEC_v1_0.md
document: A16 — Phase-Locked Event Anchor Map Specification
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed: full lock; magical nugget #5; M6 calibration ground truth)
intended_for: Claude Code sub-agents implementing the A16 Phase-Locked Event Anchors writer
prime_directive: Only computed facts. Predicted-event calendar from classical timing rules. Every prediction has explicit falsifier. No narrative.
depends_on: A7 chart_dashas (3 systems), A8 T1 structural (yoga-firing rules), A9 Sade Sati, A11 CDLM (cell evolution gradients), A12 CGM (motif activation), A15 Time-Synchronicity (high-resonance windows), classical timing rule catalog (NEW global asset)
window: 1950-01-01 → 2100-12-31
technology_stack: Cloud SQL Postgres + native PG range partitioning + pgvector (anchor embeddings).
parallel_prerequisite: Classical Timing Rule Catalog (~200 rules) authored at A16 implementation kickoff
---

# A16 — Phase-Locked Event Anchor Map Specification

## §0 — Mission

For each chart per ayanamsha, materialize a predicted-event lattice spanning 1950-2100. Each anchor is one classical-timing-rule-derived prediction: predicted_event_class + predicted_iso_window + triggering_rules + expected_intensity + falsifiability_statement + outcome_tracking_placeholder. M6 uses these as ground truth for prospective testing. Without this, M6 has nothing to calibrate against.

## §1 — Locked decisions

1. Predicted event classes: ~30 structured categories (`career_peak`, `career_trough`, `relationship_initiation`, `relationship_strain`, `marriage_window`, `child_birth_window`, `health_crisis_window`, `health_recovery_window`, `wealth_peak`, `wealth_loss_window`, `spiritual_initiation`, `spiritual_awakening`, `loss_of_close_relation`, `relocation_window`, `vocational_change`, `educational_milestone`, `legal_difficulty`, `recognition_window`, `inheritance_window`, `creative_peak`, `physical_injury_risk`, `mental_health_strain`, `meditation_breakthrough_window`, etc.)
2. Multi-domain prediction: one anchor may predict multiple domain-class outcomes
3. Confidence intervals on predicted_iso_window — ±N months based on multi-rule agreement
4. Cross-rule corroboration boost when multiple classical rules predict same window
5. Falsifiability statement mandatory per anchor
6. Outcome ontology: structured (binary/categorical/ordinal/continuous), NOT freetext, so M6 can score
7. Anchor-to-anchor causal chain DAG (when P1 outcome feeds P2)
8. Per-tradition prediction variants (Parashari/Jaimini/Tajik/KP each generates predictions; cross-tradition agreement = boost)
9. Alternative outcome scenarios materialized (chart's Plan B architecture)
10. Calibration anchor set versioned
11. Native PG range partitioning by predicted_iso_window
12. WIPE existing rows before rebuild
13. Two-pass + ephemeris audit
14. Outcome_tracking_placeholder_jsonb on every anchor

## §2 — Storage

```sql
CREATE TABLE l25_phase_locked_event_anchors (
  anchor_id UUID,
  chart_id UUID NOT NULL, ayanamsha_id TEXT NOT NULL, build_id UUID NOT NULL,

  -- Prediction identity
  predicted_event_class TEXT NOT NULL,                -- one of ~30 structured classes
  predicted_domain TEXT NOT NULL,                     -- career | relationships | health | wealth | family | learning | spirituality | longevity | character
  multi_domain_predictions_array TEXT[],              -- when one anchor predicts cross-domain effects

  -- Temporal
  predicted_iso_window_start TIMESTAMPTZ NOT NULL,
  predicted_iso_window_end TIMESTAMPTZ NOT NULL,
  predicted_iso_window_centroid TIMESTAMPTZ NOT NULL,
  predicted_iso_window_confidence_class TEXT,         -- 'tight' (<3mo) | 'medium' (3-12mo) | 'wide' (12-24mo) | 'loose' (>24mo)
  predicted_iso_window_uncertainty_months NUMERIC,

  -- Triggering rules
  triggering_rule_ids_array TEXT[] NOT NULL,          -- references to Classical Timing Rule Catalog
  triggering_rules_jsonb JSONB NOT NULL,              -- per-rule contribution + classical source citation

  -- Expected intensity + class
  expected_intensity NUMERIC,
  expected_outcome_polarity TEXT,                     -- 'positive' | 'negative' | 'mixed' | 'transformational'
  expected_outcome_class TEXT,                        -- structured outcome category

  -- Cross-rule corroboration
  cross_rule_corroboration_count INT,                 -- how many rules independently predict this window
  cross_tradition_corroboration_count INT,            -- how many traditions (Parashari/Jaimini/Tajik/KP) agree
  cross_tradition_corroborating_traditions_array TEXT[],

  -- Confidence
  prediction_confidence NUMERIC,                      -- 0-1; multi-rule + cross-tradition boost
  prediction_confidence_decomposition_jsonb JSONB,

  -- Falsifiability (MANDATORY)
  falsifiability_statement TEXT NOT NULL,             -- "If event of class X is not observed by date Y, prediction was wrong"
  falsifier_date_iso TIMESTAMPTZ NOT NULL,
  falsifier_observation_class TEXT NOT NULL,          -- structured class
  falsifier_threshold_jsonb JSONB,                    -- magnitude thresholds for outcome scoring

  -- Alternative outcomes (chart's Plan B architecture)
  alternative_outcome_scenarios_jsonb JSONB,          -- 2-3 alternative outcome paths if primary doesn't fire

  -- Anchor-to-anchor causal chain
  causal_predecessor_anchor_ids_array UUID[],         -- anchors whose outcome enables this anchor
  causal_successor_anchor_ids_array UUID[],           -- anchors enabled by this one's outcome

  -- Per-tradition variant linkage
  parashari_variant_anchor_id UUID,
  jaimini_variant_anchor_id UUID,
  tajik_variant_anchor_id UUID,
  kp_variant_anchor_id UUID,

  -- Outcome ontology (structured)
  outcome_ontology_class TEXT,                        -- 'binary' | 'categorical' | 'ordinal' | 'continuous'
  outcome_ontology_definition_jsonb JSONB,            -- structured outcome ontology

  -- M6 outcome tracking placeholder (empty at write; user records outcome)
  outcome_tracking_placeholder_jsonb JSONB,           -- {observed, observed_iso, observed_class, observed_magnitude, score, calibration_version}

  -- Calibration anchor set version
  calibration_anchor_set_version TEXT NOT NULL,

  -- Active synchronicity window cross-reference
  associated_synchronicity_id UUID,                   -- FK to A15 if this anchor falls in a synchronicity window
  resonance_class_at_window TEXT,

  -- Per-anchor pgvector embedding (for cross-chart anchor cohort search)
  anchor_embedding_vec VECTOR(768),

  -- Provenance
  ephemeris_audit_jsonb JSONB,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL,
  engine_version TEXT NOT NULL,

  PRIMARY KEY (anchor_id),
  UNIQUE (chart_id, ayanamsha_id, build_id, predicted_event_class, predicted_iso_window_centroid)
) PARTITION BY RANGE (predicted_iso_window_centroid);

CREATE TABLE l25_phase_locked_event_anchors_y1950_y2000 PARTITION OF l25_phase_locked_event_anchors FOR VALUES FROM ('1950-01-01') TO ('2000-01-01');
CREATE TABLE l25_phase_locked_event_anchors_y2000_y2050 PARTITION OF l25_phase_locked_event_anchors FOR VALUES FROM ('2000-01-01') TO ('2050-01-01');
CREATE TABLE l25_phase_locked_event_anchors_y2050_y2100 PARTITION OF l25_phase_locked_event_anchors FOR VALUES FROM ('2050-01-01') TO ('2100-01-01');

CREATE INDEX anchors_chart_idx ON l25_phase_locked_event_anchors (chart_id, ayanamsha_id);
CREATE INDEX anchors_class_idx ON l25_phase_locked_event_anchors (chart_id, ayanamsha_id, predicted_event_class);
CREATE INDEX anchors_domain_idx ON l25_phase_locked_event_anchors (chart_id, ayanamsha_id, predicted_domain);
CREATE INDEX anchors_confidence_idx ON l25_phase_locked_event_anchors (chart_id, ayanamsha_id, prediction_confidence DESC);
CREATE INDEX anchors_falsifier_idx ON l25_phase_locked_event_anchors (chart_id, ayanamsha_id, falsifier_date_iso);
CREATE INDEX anchors_corroboration_idx ON l25_phase_locked_event_anchors (chart_id, ayanamsha_id, cross_tradition_corroboration_count DESC);
CREATE INDEX anchors_embedding_hnsw ON l25_phase_locked_event_anchors USING hnsw (anchor_embedding_vec vector_cosine_ops);
```

## §3 — Classical Timing Rule Catalog (parallel prerequisite)

NEW global asset: `G29_CLASSICAL_TIMING_RULES_v1_0.md`

Catalog of ~200 timing rules from:
- BPHS dasha-phala chapters
- Phaladeepika temporal sections
- Jaimini Sutram Chara dasha timing rules
- Tajik year-lord timing rules
- KP cuspal-sub-lord trigger rules
- Saravali temporal sections
- Nadi-derived predictive rules

Each rule = (trigger_condition, predicted_event_class, predicted_window_offset, expected_intensity, falsifiability_class, classical_source_citation).

Catalog authored at A16-AUDIT-S1 before A16-S1 implementation kicks off.

## §4 — Volume projection

Per chart × per ayanamsha:
- ~200 rules × 150-year window matches ≈ ~300-500 anchor firings
- Cross-tradition variants × 4 = ~1,200-2,000 anchors per (chart, ay)
- × 5 ayanamshas ≈ ~6,000-10,000 anchors per chart

**Per chart: ~8,000 anchor rows.** Manageable.

## §5 — Compute method

1. Load Classical Timing Rule Catalog (~200 rules).
2. For each rule, evaluate trigger condition against chart at each candidate window across 1950-2100.
3. Generate anchor when trigger fires.
4. Compute prediction_confidence from rule strength + cross-rule corroboration count.
5. Cross-tradition variant generation per Parashari/Jaimini/Tajik/KP.
6. Compute confidence intervals on predicted_iso_window.
7. Cross-anchor causal chain detection (P1 outcome enables P2).
8. Alternative outcome scenarios materialized.
9. Cross-reference to A15 synchronicity (FK if anchor falls in a synchronicity window).
10. Per-anchor embedding.
11. Falsifiability statement auto-generated from rule + outcome ontology.
12. Outcome ontology assignment per anchor.
13. Outcome_tracking_placeholder_jsonb empty at write.
14. Ephemeris dual-source audit.

## §6 — Retrieval contract

- `query_anchors_in_range(chart_id, ayanamsha_id, start_iso, end_iso, min_confidence?)` → anchors in range
- `query_anchors_by_class(chart_id, ayanamsha_id, predicted_event_class)` → anchors of class
- `query_anchors_at_date(chart_id, ayanamsha_id, date)` → anchors whose window includes date
- `query_next_anchor(chart_id, ayanamsha_id, from_date, min_confidence?)` → next predicted event
- `query_top_corroborated_anchors(chart_id, ayanamsha_id, top_k=10)` → highest cross-tradition agreement
- `query_anchor_causal_chain(anchor_id)` → predecessor + successor DAG walk
- `query_anchor_peers(anchor_embedding, top_k=10)` → cross-chart anchor cohort peers
- `record_outcome(anchor_id, outcome_data)` → M6 write path (populates outcome_tracking_placeholder)

## §7 — Verification

Two-pass:

| Aspect | Primary | Secondary | Tertiary |
|---|---|---|---|
| Rule trigger evaluation | Rule engine | Independent rule cross-check | Classical citation re-verification |
| Predicted_iso_window math | Date arithmetic from A7 + transit calc | Independent calculation | — |
| Cross-rule corroboration count | Set intersection | Independent set algebra | — |
| Falsifiability statement | Rule outcome ontology | Independent ontology cross-check | — |
| Anchor-to-anchor causal chain | DAG topology + outcome dependency | Independent DAG validation | Cycle detection |
| Ephemeris audit | pyswisseph | libephemeris JPL DE440 | — |

Halt on divergent_flagged.

## §8 — Final locked surface

1. ~200-classical-timing-rule catalog (G29 parallel prerequisite)
2. ~8,000 anchors per chart × ayanamsha × tradition variants
3. Mandatory falsifiability per anchor
4. Structured outcome ontology (binary/categorical/ordinal/continuous; never freetext)
5. Cross-rule + cross-tradition corroboration boost
6. Confidence intervals on predicted_iso_window
7. Alternative outcome scenarios per anchor
8. Anchor-to-anchor causal chain DAG
9. Per-tradition variant anchors
10. A15 synchronicity cross-reference
11. Outcome_tracking_placeholder for M6 calibration
12. Per-anchor pgvector embedding
13. Native PG range partitioning by predicted_iso_window_centroid
14. WIPE existing rows before rebuild
15. Two-pass + dual-source ephemeris audit

---

*End of A16_PHASE_LOCKED_EVENT_ANCHORS_SPEC_v1_0.md — LOCKED 2026-05-29.*
