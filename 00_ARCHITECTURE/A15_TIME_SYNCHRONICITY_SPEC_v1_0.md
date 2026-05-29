---
artifact: A15_TIME_SYNCHRONICITY_SPEC_v1_0.md
document: A15 — Time-Synchronicity Stack Specification
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed: full lock; magical nugget #1 for cosmic-pattern reveal)
intended_for: Claude Code sub-agents implementing the A15 Time-Synchronicity writer to L2.5 layer
prime_directive: Only computed facts. Multi-cycle time arithmetic + convergence detection. No narrative.
depends_on: A7 chart_dashas (3 systems), A9 Sade Sati, A4 panchanga (eclipses + lunar phase + hora + choghadiya), A12 CGM (per_graha_story_arc for natal point hits)
window: 1950-01-01 → 2100-12-31
technology_stack: Cloud SQL Postgres + native PG declarative range partitioning by date_iso + pgvector (window embeddings).
---

# A15 — Time-Synchronicity Stack Specification

## §0 — Mission

For each chart per ayanamsha, materialize the lifetime time-cycle convergence map. For every KEY DATE in 1950-2100 (Maha boundaries + Antar boundaries + eclipse hits to natal points + Saturn/Jupiter/Rahu returns + Sade Sati phase transitions + significant transit hits), compute which time cycles are converging within ±30 days and emit a single synchronicity row. This reveals the cosmic-resonance windows no acharya can mentally compute.

## §1 — Locked decisions

1. Key-date set: Maha boundaries (3 systems) + Antar boundaries (3 systems) + Solar/Lunar eclipses with natal-point hits + Saturn/Jupiter/Rahu returns + Sade Sati phase transitions + significant transit hits (slow planet stations on natal points)
2. Convergence window: ±30 days
3. Convergence index decomposed into named factors (no black-box scores)
4. Predictive resonance class (5-tier categorical)
5. Panchanga of the resonance moment included
6. Per-window pgvector embedding for cross-chart cohort window comparison
7. Native PG range partitioning by date_iso
8. WIPE existing l25_time_synchronicity rows before rebuild
9. Two-pass verification + ephemeris_audit_jsonb dual-source

## §2 — Storage

```sql
CREATE TABLE l25_time_synchronicity (
  synchronicity_id UUID,
  chart_id UUID NOT NULL, ayanamsha_id TEXT NOT NULL, build_id UUID NOT NULL,
  date_iso TIMESTAMPTZ NOT NULL,
  date_window_start_iso TIMESTAMPTZ NOT NULL,        -- date - 30 days
  date_window_end_iso TIMESTAMPTZ NOT NULL,          -- date + 30 days

  -- Active cycles at this date (multi-system)
  vimshottari_maha_lord TEXT, vimshottari_maha_transition_flag BOOLEAN, vimshottari_maha_days_into_window INT,
  vimshottari_antar_lord TEXT, vimshottari_antar_transition_flag BOOLEAN,
  chara_karaka_lord TEXT, chara_transition_flag BOOLEAN,
  yogini_maha_lord TEXT, yogini_transition_flag BOOLEAN,
  ashtottari_maha_lord TEXT, ashtottari_transition_flag BOOLEAN,
  saturn_return_proximity_days INT,
  jupiter_return_proximity_days INT,
  rahu_return_proximity_days INT,
  ketu_return_proximity_days INT,
  sade_sati_active_flag BOOLEAN, sade_sati_phase TEXT, sade_sati_intensity_class TEXT,
  kantaka_shani_active_flag BOOLEAN, ashtama_shani_active_flag BOOLEAN,
  active_eclipse_class TEXT,                          -- 'solar' | 'lunar' | null
  eclipse_node TEXT, eclipse_natal_point_hit_array TEXT[],
  active_slow_planet_stations_jsonb JSONB,            -- Jupiter/Saturn/Rahu retrograde + direct stations
  active_transit_hits_natal_points_jsonb JSONB,

  -- Panchanga of the convergence date (from A4)
  tithi TEXT, vara TEXT, moon_nakshatra TEXT, yoga TEXT, karana TEXT,
  hora_lord TEXT, current_choghadiya_class TEXT, current_choghadiya_window TEXT,
  is_auspicious_muhurta_flag BOOLEAN, is_inauspicious_window_flag BOOLEAN,
  panchaka_class TEXT,

  -- Convergence metrics
  convergence_count INT NOT NULL,                     -- how many active cycles within window
  convergence_intensity NUMERIC NOT NULL,             -- weighted aggregate (named factors below)
  convergence_intensity_decomposition_jsonb JSONB NOT NULL,
  -- Decomposition fields:
  -- {
  --   "dasha_transition_weight": 0.25,
  --   "return_proximity_weight": 0.30,
  --   "eclipse_natal_hit_weight": 0.40,
  --   "sade_sati_weight": 0.20,
  --   "transit_hit_weight": 0.15,
  --   ...
  -- }

  -- Predictive resonance class
  cosmic_resonance_class TEXT NOT NULL,               -- 'baseline' | 'medium' | 'high' | 'extreme' | 'rare_alignment'
  predictive_resonance_class TEXT,                    -- 'transformation' | 'culmination' | 'initiation' | 'release' | 'integration' | 'observation'

  -- Cross-system divergence flagging
  cross_system_temporal_divergence_jsonb JSONB,       -- when Vim says X but Yogini says Y
  cross_system_agreement_count INT,                   -- how many of 3 systems agree on event class

  -- Classical timing rules triggered
  classical_timing_rules_triggered_array TEXT[],

  -- Convergence cluster membership
  convergence_cluster_id UUID,                        -- 3+ synchronicities within 90 days → cluster
  cluster_role TEXT,                                  -- 'cluster_centroid' | 'cluster_member' | 'isolated'

  -- pgvector for cross-chart window comparison
  window_embedding_vec VECTOR(768),

  -- Trans-lifetime narrative arc anchor (computed, not narrative)
  trans_lifetime_arc_position TEXT,                   -- 'foundation' | 'expansion' | 'peak' | 'consolidation' | 'release' | 'integration' | 'transcendence'

  -- Multi-chart cross-resonance hook (NULL at single-chart build; populated when chart cohort grows)
  multi_chart_resonance_partners_jsonb JSONB,

  -- Provenance
  ephemeris_audit_jsonb JSONB,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL,
  engine_version TEXT NOT NULL,

  PRIMARY KEY (synchronicity_id),
  UNIQUE (chart_id, ayanamsha_id, build_id, date_iso)
) PARTITION BY RANGE (date_iso);

CREATE TABLE l25_time_synchronicity_y1950_y2000 PARTITION OF l25_time_synchronicity FOR VALUES FROM ('1950-01-01') TO ('2000-01-01');
CREATE TABLE l25_time_synchronicity_y2000_y2050 PARTITION OF l25_time_synchronicity FOR VALUES FROM ('2000-01-01') TO ('2050-01-01');
CREATE TABLE l25_time_synchronicity_y2050_y2100 PARTITION OF l25_time_synchronicity FOR VALUES FROM ('2050-01-01') TO ('2100-01-01');

CREATE INDEX synchronicity_chart_idx ON l25_time_synchronicity (chart_id, ayanamsha_id);
CREATE INDEX synchronicity_intensity_idx ON l25_time_synchronicity (chart_id, ayanamsha_id, convergence_intensity DESC);
CREATE INDEX synchronicity_resonance_class_idx ON l25_time_synchronicity (chart_id, ayanamsha_id, cosmic_resonance_class);
CREATE INDEX synchronicity_cluster_idx ON l25_time_synchronicity (convergence_cluster_id);
CREATE INDEX synchronicity_embedding_hnsw ON l25_time_synchronicity USING hnsw (window_embedding_vec vector_cosine_ops);
```

Plus convergence cluster table:

```sql
CREATE TABLE l25_time_convergence_clusters (
  cluster_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,
  cluster_start_iso TIMESTAMPTZ, cluster_end_iso TIMESTAMPTZ, cluster_duration_days INT,
  centroid_synchronicity_id UUID,
  member_synchronicity_ids_array UUID[],
  cluster_intensity_aggregate NUMERIC,
  cluster_resonance_class TEXT,
  cluster_predictive_arc_class TEXT,
  cluster_embedding_vec VECTOR(768),
  classical_archetype_match TEXT,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL
);
```

## §3 — Volume projection

Estimated key-date density:
- Vimshottari Maha boundaries: ~10 per chart over 150 years
- Vimshottari Antar boundaries: ~80
- Chara karaka transitions: ~12
- Yogini Maha transitions: ~16
- Saturn returns: 4-5
- Jupiter returns: 12-13
- Rahu/Ketu returns: ~8
- Sade Sati phase transitions: ~24
- Solar/Lunar eclipses on natal points: ~30-50 (depending on natal point density)
- Slow planet stations on natal points: ~80-120

**Per (chart, ay) key dates: ~300. × 5 ay = ~1,500 synchronicity rows per chart.**
Plus convergence clusters: ~30-80 per chart.

**Total per chart: ~1,580 rows.** Tiny.

## §4 — Compute method

1. Enumerate all key dates from A7 chart_dashas + A4 eclipses + transit calculations.
2. For each key date, compute ±30-day window.
3. Walk all time cycles; flag which are active/transitioning in the window.
4. Compute convergence_intensity from decomposition.
5. Classify cosmic_resonance_class (baseline → extreme).
6. Cross-system divergence check (where systems disagree on event class).
7. Detect convergence clusters (≥3 synchronicities within 90 days).
8. Per-window embedding (768-dim via Node2Vec-like over cycle vector + panchanga).
9. Classical archetype match for clusters (life-arc-stage archetypes from G8).
10. Multi-chart cross-resonance (NULL at single-chart build).
11. Ephemeris dual-source audit.

## §5 — Retrieval contract

- `query_synchronicity_at_date(chart_id, ayanamsha_id, date, window=30)` → matching synchronicity row(s)
- `query_synchronicity_in_range(chart_id, ayanamsha_id, start_iso, end_iso, min_intensity?, resonance_class?)` → time-range
- `query_top_resonance_windows(chart_id, ayanamsha_id, top_k=10)` → highest-intensity windows
- `query_convergence_clusters(chart_id, ayanamsha_id, resonance_class?)` → cluster rows
- `query_synchronicity_peers(window_embedding, top_k=10)` → cross-chart cohort window peers
- `query_synchronicity_decomposition(synchronicity_id)` → decomposed factors

## §6 — Verification

Two-pass per row:

| Aspect | Primary | Secondary | Tertiary |
|---|---|---|---|
| Key date enumeration | A7 chart_dashas + A4 eclipses + transit calc | Independent date math cross-check | — |
| Active cycle determination | Cycle-membership rule application | Independent rule cross-check | — |
| Convergence_intensity formula | Decomposition + aggregation | Component-wise cross-check | Algebraic invariants |
| Cluster detection | 90-day window sliding | Independent cluster algorithm | — |
| Ephemeris audit | pyswisseph | libephemeris JPL DE440 | — |

Halt on divergent_flagged.

## §7 — Final locked surface

1. Per-chart, per-ayanamsha lifetime synchronicity map
2. Multi-cycle convergence detection (±30-day window)
3. Decomposed convergence_intensity (no black-box scoring)
4. 5-tier cosmic_resonance_class + 7-tier predictive_resonance_class
5. Cross-system temporal divergence flagging
6. Convergence cluster detection (3+ within 90 days)
7. Panchanga of resonance moment included
8. Per-window pgvector embedding
9. Multi-chart cross-resonance hook (activates when cohort grows)
10. Native PG range partitioning by date_iso (3 partitions across 150 years)
11. WIPE existing rows before rebuild
12. Two-pass + dual-source ephemeris audit

---

*End of A15_TIME_SYNCHRONICITY_SPEC_v1_0.md — LOCKED 2026-05-29.*
