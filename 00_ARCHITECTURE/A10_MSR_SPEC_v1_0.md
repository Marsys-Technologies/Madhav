---
artifact: A10_MSR_SPEC_v1_0.md
document: A10 — MSR (Multi-System Register) Specification
status: LOCKED
version: 1.2
date: 2026-05-29
changelog:
  - v1.2 (2026-06-14, L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0.md §4+§6): Architecture
    decision purges predicate-firing model from MSR. (a) §0 mission rewritten: MSR INHERITS
    exhaustively-enumerated relational fabric from `ga_structural` (L1) — does NOT re-fire
    predicates, does NOT re-derive intrinsic strength. MSR ADDS population-level enrichment
    impossible at L1: salience ranking, convergence/contradiction mapping, domain-weighted
    significance. (b) `prime_directive` updated: population-level enrichment over ga_structural
    enumeration replaces "Structural predicate firings." (c) `depends_on` updated: primary
    dependency is `ga_structural`; G52 `signal_type_registry` role changed from firing registry
    to name/citation catalog for labeling only. (d) §5 G52 role clarified. (e) §12/§13 updated.
    Governing decision: `00_ARCHITECTURE/L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0.md`.
  - v1.1 (2026-06-12, L2 Bodha §13.1 amendment): (a) Table `l25_msr_signals` → `bodha_msr_signals`
    per the native naming decision (L2_BODHA_BUILD_CAMPAIGN §3.1); ~50-col schema unchanged.
    (b) The `contradicts_signals_array` column REMAINS on `bodha_msr_signals`, but contradiction
    PAIRS are additionally promoted to a first-class `bodha_contradictions` table (owned by
    `bo_karanajala`, documented in A12 v1.1 §5.6) — A10 emits the array; A12 materializes the pairs.
    (c) `bo_laksana` (the A10 writer) `depends_on` corrected to `['ga_structural','signal_type_registry']`.
    `signal_type_registry` (G52) built by migration 226 + seeded (starter ~80; full 500-700 pending).
    Tables built by migration 226.
  - v1.0 (2026-05-29): initial LOCKED spec, native sign-off.
authored_by: Cowork (native-confirmed: exhaustive scope; ~800-1,250 signals per (chart, ayanamsha); synthetic signals included; downstream-driven enrichments included)
intended_for: Claude Code sub-agents implementing the bo_laksana (A10 MSR) writer to bodha_msr_signals table (L2 layer)
prime_directive: Only computed facts. Population-level enrichment over ga_structural exhaustive enumeration (salience ranking, convergence, contradiction, domain-salience). No re-firing of predicates already enumerated at L1. No narrative. Two-pass verification mandatory. Closes Contamination C2 (no threshold drop — strength as column not gate).
depends_on: ga_structural (PRIMARY — exhaustive L1 relational enumeration; MSR inherits, does not re-fire), G1 classical corpus, G27 remedies, G28 worked examples, G52 signal_type_registry (name/citation CATALOG for labeling only — NOT a firing mechanism)
---

# A10 — MSR (Multi-System Register) Specification

## §0 — Mission

For each chart per ayanamsha, **inherit** the exhaustively-enumerated relational fabric from
`ga_structural` (L1) and compute population-level enrichment over that fabric.

**What MSR inherits from ga_structural (does NOT re-compute):** every aspect, conjunction, dispositor
chain, parivartana, argala cell, composite state, and avastha across all vargas + dasha-time-windows —
produced by exhaustive enumeration at L1 (all grahas × all houses × all signs), stored with
`constituent_facts_array` back to `chart_facts.fact_id`, and labeled with classical names where a
match exists in G52 `signal_type_registry`. `ga_structural` is the sole enumeration engine.

**What MSR adds (population-level — impossible to compute from any single relationship in isolation):**
- `top_k_salience_rank` — this signal's rank relative to all others in the chart
- `system_convergence_count` — how many of 6 traditions agree on this signal
- `contradicts_signals_array` — which other signals this one structurally opposes
- `domain_salience_jsonb` / `domains_affected_array` — per-life-area weighting across the full signal set
- `computed_salience` — the composed significance score that ranks signals against each other

Emit ONE row per inherited relationship — **no threshold drop**, strength is a column not a gate. Each
row carries decomposed salience components (deterministic_strength, verification_certainty, computed_salience
per salience_formula_v1), all downstream-accuracy enrichments, and the `constituent_facts_array` resolved
to `chart_facts.fact_id` via `ga_structural`. Stored in `bodha_msr_signals` (L2 layer).

> **Architecture note (v1.2):** The prior §0 described evaluating predicates against A1-A9 atoms.
> That model is superseded by `L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0.md §4`. The L1/L2
> boundary is intrinsic (ga_structural) vs. population-level (MSR). No re-firing; no silent drops;
> no predicate registry as gating mechanism.

## §1 — Locked decisions

- Signal scope: exhaustive (~800-1,250 per (chart, ayanamsha), × 5 ayanamshas = ~4,000-6,250 per chart)
- Synthetic signals: **INCLUDED** (deterministic composite predicates over primary signals)
- All additions A-V from elaboration §7: **INCLUDED**
- All 10 clarifications: per native answers (§3 below)
- Downstream-driven enrichments: **INCLUDED** (CDLM/CGM/RM/UCN-specific fields added to schema)
- Two-pass verification: **MANDATORY** per row
- Salience formula: v1 (versioned; reproducible)

## §2 — Schema decisions (native answers locked)

- Q1: A — proposed salience formula weights as v1.0
- Q2: C — BOTH per-text corroboration count + per-verse corroboration count emitted as separate fields
- Q3: A — confidence interval per signal (P10/P50/P90 under input perturbation)
- Q4: A — all 7 dasha systems contribute to `dasha_activation_proximity_score`
- Q5: A — G52 `signal_type_registry` authored as new global asset
- Q6: A — 9 standard CDLM domains (career, relationships, health, wealth, family, learning, spirituality, longevity, character)
- Q7: A — all 6 traditions emitted via `signal_tradition` discriminator
- Q8: A — cross-ayanamsha consistency score computed per signal
- Q9: A — strength normalized per chart globally
- Q10: A — cancellation modifier = 0.1 (kept queryable but tanked)

## §3 — `l25_msr_signals` row schema (full, ~50 columns)

```sql
CREATE TABLE l25_msr_signals (
  -- Identity
  signal_id                            UUID PRIMARY KEY,
  chart_id                             UUID NOT NULL,
  ayanamsha_id                         TEXT NOT NULL,
  build_id                             UUID NOT NULL,

  -- Classification
  signal_type_id                       TEXT NOT NULL,         -- e.g., 'pancha_mahapurusha_hamsa', 'raja_yoga_9L_10L', 'mangal_dosha_2H', 'kp_cusp_7_significator_pattern', 'tajik_ithasala_SUN_VEN', 'bhrigu_nadi_pattern_A12', 'maharsi_vasishtha_sphuta_alignment', 'synthetic_career_transformation_window'
  signal_type_class                    TEXT NOT NULL,         -- 'yoga' | 'dosha' | 'composite_state' | 'parivartana' | 'karaka_alignment' | 'dasha_triggered' | 'sade_sati' | 'panchaka' | 'transit_overlay' | 'tradition_specific' | 'varga_pattern' | 'synthetic'
  signal_tradition                     TEXT NOT NULL,         -- 'parashari' | 'jaimini' | 'tajik' | 'kp' | 'lal_kitab' | 'nadi_bhrigu' | 'maharsi' | 'multi' (for synthetics)

  -- Structured configuration (NOT prose)
  configuration_jsonb                  JSONB NOT NULL,        -- structured predicate firing details
  constituent_facts_array              TEXT[] NOT NULL,       -- fact_ids back to chart_facts (and dasha_row_ids for dasha-triggered)
  constituent_signals_array            UUID[],                -- for synthetic signals: references to primary MSR signals

  -- Classical sourcing
  classical_sources_array              TEXT[],                -- citation_ids back to G1 corpus chunks + G12/G13 definitions
  source_corroboration_count_by_text   INT,                   -- Q2 split: by distinct text (BPHS=1, Phaladeepika=1, etc.)
  source_corroboration_count_by_verse  INT,                   -- Q2 split: by distinct verse (BPHS Ch.7 v.23 + v.45 = 2)

  -- Salience formula v1.0 — fully decomposed inputs
  orb_tightness                        NUMERIC,               -- [0,1] inverse of orb in deg
  shadbala_norm                        NUMERIC,               -- shadbala_total / required, capped at 2.0
  dignity_score                        NUMERIC,               -- exalted=1.0..debilitated=0.10 per §4
  deterministic_strength               NUMERIC NOT NULL,      -- = orb_tightness × shadbala_norm × dignity_score
  verification_certainty               NUMERIC NOT NULL,      -- log(1+source_count_by_text)/log(10)
  divisional_corroboration_count       INT,                   -- how many vargas reinforce
  dasha_activation_proximity_score     NUMERIC,               -- 0..1 across all 7 dasha systems (Q4=A)
  house_weight_multiplier              NUMERIC,
  ashtakavarga_support_multiplier      NUMERIC,
  aspect_modifier                      NUMERIC,
  vargottama_amplification             NUMERIC,
  argala_modifier                      NUMERIC,
  neechabhanga_modifier                NUMERIC,
  cancellation_modifier                NUMERIC,               -- 1.0 normal, 0.1 cancelled (Q10=A)
  computed_salience                    NUMERIC NOT NULL,      -- per salience_formula_v1.0
  salience_formula_version             TEXT NOT NULL,         -- 'v1.0'

  -- Salience confidence (Q3=A)
  salience_confidence_interval_jsonb   JSONB,                 -- {p10: ..., p50: ..., p90: ...} under input perturbation

  -- Domain + cross-domain
  domains_affected_array               TEXT[] NOT NULL,       -- subset of 9 CDLM domains
  domain_salience_jsonb                JSONB NOT NULL,        -- per-domain salience weight {career: 0.85, relationships: 0.30, ...}
  shared_factor_keys_jsonb             JSONB,                 -- for CDLM aggregation (e.g., {SUN, HOUSE_9, CAPRICORN})
  cross_domain_shared_factor_count     INT,                   -- pre-computed for CDLM

  -- Graph (for A12 CGM)
  graph_edge_pattern_jsonb             JSONB,                 -- [(from_node, to_node, edge_type, edge_weight), ...]
  graph_node_strength_contribution_jsonb JSONB,               -- per node, salience contribution
  relationship_classification          TEXT,                  -- 'aspect' | 'dispositor' | 'lordship' | 'karaka' | 'conjunction' | 'parivartana' | 'mutual_reception'

  -- Resonance map hooks (for A13 RM)
  graha_weakness_indicators_jsonb      JSONB,                 -- per weak graha: {graha, weakness_score, reason}
  remedy_hooks_array                   TEXT[],                -- remedy_ids from G27 that classically apply
  recurring_pattern_marker             TEXT,                  -- 'graha_weakness_X3' | 'house_affliction_X2' | etc.

  -- UCN digest hooks (for A14)
  top_k_salience_rank                  INT,                   -- pre-computed rank in this (chart, ayanamsha) by computed_salience
  system_convergence_count             INT,                   -- how many of 6 traditions agree on this signal
  signature_class                      TEXT,                  -- 'dominant_theme' | 'recurring_theme' | 'isolated_singularity'

  -- Contradictions (Addition H)
  contradicts_signals_array            UUID[],                -- references to other signals it contradicts

  -- Active periods (Addition F + J)
  active_duration_class                TEXT NOT NULL,         -- 'lifelong' | 'dasha_bounded' | 'transit_bounded'
  active_dasha_periods_jsonb           JSONB,                 -- {system, level, lord, start_iso, end_iso} tuples
  activation_predicted_dates_jsonb     JSONB,                 -- for calibration / prospective testing (M6 hook)
  predicted_outcome_class              TEXT,                  -- classical-text-implied outcome category (M6)

  -- Cross-ayanamsha (Addition E + Q8=A)
  cross_ayanamsha_consistency_score    NUMERIC,               -- 0..1, how many of 5 ayanamshas fire this signal

  -- Strength normalization (Addition I + Q9=A)
  strength_normalized_to_chart_max     NUMERIC,               -- 0..1, normalized per chart globally

  -- Pada precision (Addition L)
  pada_precision_flag                  BOOLEAN,

  -- Cross-system consensus (Addition M)
  cross_system_consensus_count         INT,                   -- how many of 7 dasha systems have signal's primary graha as current lord

  -- Channel rendering (multi-channel retrieval)
  channel_render_priority_jsonb        JSONB,                 -- per channel rendering priority

  -- Verification + provenance
  verification_pass_status             TEXT NOT NULL,         -- 'two_pass_verified' | 'classical_match' | 'divergent_flagged'
  verification_method                  TEXT,
  citation_ref                         TEXT NOT NULL,
  citation_human                       TEXT NOT NULL,
  computed_at                          TIMESTAMPTZ NOT NULL,
  engine_version                       TEXT NOT NULL,

  UNIQUE (chart_id, ayanamsha_id, signal_type_id, build_id, configuration_jsonb)
);

CREATE INDEX msr_chart_aya_idx ON l25_msr_signals (chart_id, ayanamsha_id);
CREATE INDEX msr_signal_type_idx ON l25_msr_signals (signal_type_id);
CREATE INDEX msr_signal_class_idx ON l25_msr_signals (signal_type_class, signal_tradition);
CREATE INDEX msr_salience_rank_idx ON l25_msr_signals (chart_id, ayanamsha_id, computed_salience DESC);
CREATE INDEX msr_domains_gin_idx ON l25_msr_signals USING gin (domains_affected_array);
CREATE INDEX msr_constituent_facts_gin_idx ON l25_msr_signals USING gin (constituent_facts_array);
CREATE INDEX msr_top_k_rank_idx ON l25_msr_signals (chart_id, ayanamsha_id, top_k_salience_rank);
CREATE INDEX msr_signature_class_idx ON l25_msr_signals (signature_class) WHERE signature_class IS NOT NULL;
CREATE INDEX msr_recurring_pattern_idx ON l25_msr_signals (recurring_pattern_marker) WHERE recurring_pattern_marker IS NOT NULL;
```

## §4 — Salience formula v1.0 (versioned, unit-tested)

```python
def salience_formula_v1(s):
    """
    All inputs deterministic from chart_facts + global lookups.
    No opinion components.
    Versioned + unit-tested.
    """
    # Component 1: Deterministic structural strength
    deterministic_strength = (
        s.orb_tightness
        * s.shadbala_norm
        * s.dignity_score
    )

    # Component 2: Verification certainty
    verification_certainty = math.log(1 + s.source_corroboration_count_by_text) / math.log(10)
    verification_certainty = min(verification_certainty, 1.0)

    # Final salience composition
    computed_salience = (
        deterministic_strength
        * verification_certainty
        * (1 + s.dasha_activation_proximity_score * 0.5)
        * s.house_weight_multiplier
        * s.ashtakavarga_support_multiplier
        * (1 + s.aspect_modifier)
        * (1 + s.vargottama_amplification)
        * (1 + s.argala_modifier)
        * s.neechabhanga_modifier
        * s.cancellation_modifier
    )

    return computed_salience
```

**Dignity score table:**
```
exalted = 1.00, mooltrikona = 0.95, own = 0.85, friend = 0.65,
neutral = 0.50, enemy = 0.35, debilitated = 0.10
```

**House weight multiplier:**
```
kendra+trikona (1) = 1.30, trikona (5/9) = 1.20, kendra (4/7/10) = 1.15,
upachaya (3/6/10/11) = 1.05, other = 1.00, dusthana (6/8/12) = 0.90
```

**Ashtakavarga support multiplier:**
```
bindu ≥ 7 = 1.15, 5-6 = 1.05, 3-4 = 1.00, 1-2 = 0.85, 0 = 0.70
```

**Modifiers:**
- `aspect_modifier`: 0..0.3 (exalted/strong aspecting graha → boost)
- `vargottama_amplification`: 0 (none), 0.2 (vargottama), 0.5 (super-vargottama)
- `argala_modifier`: 0..0.2 (positive argala from key houses)
- `neechabhanga_modifier`: 1.0 (normal) or 1.3 (debilitation cancelled)
- `cancellation_modifier`: 1.0 (normal) or 0.1 (yoga/dosha cancelled — kept but tanked)

## §5 — Signal type registry (G52, new global asset)

`marsys_global.signal_type_registry`:
```sql
CREATE TABLE signal_type_registry (
  signal_type_id              TEXT PRIMARY KEY,
  signal_type_class           TEXT NOT NULL,
  signal_tradition            TEXT NOT NULL,
  activation_predicate_text   TEXT,                          -- human-readable predicate
  activation_predicate_jsonb  JSONB NOT NULL,                -- machine-executable predicate
  constituent_facts_pattern_jsonb JSONB,                     -- required atom shape
  classical_sources_array     TEXT[] NOT NULL,
  classical_citations_jsonb   JSONB,                         -- per-source chapter/verse
  default_domains_affected_array TEXT[] NOT NULL,
  salience_formula_overrides_jsonb JSONB,                    -- per-type adjustments to v1
  default_remedy_hooks_array  TEXT[],                        -- G27 remedy_ids
  predicted_outcome_class     TEXT,                          -- classical-text-implied outcome
  since_engine_version        TEXT NOT NULL
);
```

Registry seeded with ~500-700 entries spanning all 6 traditions + synthetic patterns. **Role (v1.2):**
a name/citation catalog for LABELING inherited `ga_structural` relationships — NOT a firing mechanism.
When an enumerated configuration matches a classical definition in this registry, `signal_type_id`
+ `classical_sources_array` are attached as labels. Configurations matching no registry entry are
STILL recorded (as uncatalogued structural relationships). The registry gates labels, not existence.
`activation_predicate_text` / `activation_predicate_jsonb` remain as documentation fields but are
NOT evaluated by `bo_laksana`; `ga_structural` already enumerated the relationship.

## §6 — Verification

`verification_pass_status` mandatory `two_pass_verified` minimum:

| Aspect | Primary | Secondary | Tertiary |
|---|---|---|---|
| Predicate firing | Engine evaluation against chart_facts JOIN | Independent classical-rule re-derivation | Classical worked-example match (G28) where available |
| Salience formula v1 | Engine application | Unit-test fixtures with known inputs | Reproducibility check (same inputs → same salience) |
| Synthetic signal composition | Constituent signals predicate AND-check | Independent composition rebuild | Cross-formula consistency |
| Source corroboration | G1 corpus chunk match | Distinct-text + distinct-verse counts | Manual spot-check at engine release |

`divergent_flagged` halts build.

## §7 — Row count projection (honest, per native callback)

| Source | Approx firings per (chart, ayanamsha) |
|---|---|
| Classical yogas (G12 200+; ~40-80 fire) | ~60 |
| Doshas (Mangal/Kaal Sarpa-12types/Pitru/etc.) | ~10 |
| Composite states (9 grahas × ~3 states) | ~27 |
| Parivartana (Maha/Khala/Dainya) | ~3 |
| Karaka alignments (30 significances × 8 karakas relevant) | ~60 |
| Dasha-triggered (7 systems × major periods × yoga overlays) | ~150 |
| Sade Sati phases + modifier overlays | ~30 |
| Panchaka/Agni Vasa/Disha Shul + Shoonya rashis | ~15 |
| Transit overlays at birth (eclipses, retrogrades) | ~15 |
| KP-specific (12 cusps × significator patterns) | ~40 |
| Tajik (5 aspect types × graha-pairs + Sahams + Hadda) | ~80 |
| Lal Kitab (Pakka Ghar, planet anomalies, 17-rule firings) | ~30 |
| Bhrigu Nadi (signature patterns) | ~30 |
| Maharsi rishi alignments | ~30 |
| Jaimini specifics (Argala, Chara karaka rels, tri-deva roles) | ~50 |
| Per-varga (Karakamsa, Swamsa, Pushkara × 30 vargas) | ~200 |
| Synthetic signals (composite predicates) | ~50-100 |

**Total per (chart, ayanamsha): ~880-1,250.**
**× 5 ayanamshas (per-ayanamsha as distinct instances): ~4,400-6,250 signals per chart.**

Storage: ~90MB per chart. 100 charts: ~9GB. Comfortable.

## §8 — Downstream enrichments — what MSR provides to each consumer

### For A11 CDLM (9×9 Cross-Domain Linkage Matrix)
MSR provides per signal:
- `domains_affected_array` + `domain_salience_jsonb` — per-domain salience weighting
- `shared_factor_keys_jsonb` — enables CDLM cell aggregation by shared-factor
- `cross_domain_shared_factor_count` — pre-computed cell-weight input
- `contradicts_signals_array` — cross-domain conflict detection

### For A12 CGM (Chart Graph Model)
MSR provides per signal:
- `graph_edge_pattern_jsonb` — direct edge insertion (from_node, to_node, type, weight)
- `graph_node_strength_contribution_jsonb` — per-node salience accumulation
- `relationship_classification` — edge type classification

### For A13 RM (Resonance Map)
MSR provides per signal:
- `graha_weakness_indicators_jsonb` — RM aggregates by graha; high-frequency → remedy candidate
- `remedy_hooks_array` — pre-mapped G27 remedy_ids
- `recurring_pattern_marker` — multi-signal-same-graha-weakness → strong remedy signal

### For A14 UCN digest
MSR provides per signal:
- `top_k_salience_rank` — UCN selects top-K
- `system_convergence_count` — UCN weights convergence signals higher
- `signature_class` — UCN categorizes by class
- `active_dasha_periods_jsonb` — UCN temporal contextualization

### For M6 prospective testing
MSR provides per signal:
- `predicted_outcome_class` — classical-text-implied outcome category for calibration
- `activation_predicted_dates_jsonb` — when signal "activates" predictably
- `salience_confidence_interval_jsonb` — uncertainty quantification for prediction calibration

### For multi-channel retrieval (per A3 §11 channel adapters)
- `channel_render_priority_jsonb` — per-channel signal prominence

## §9 — Citations (dual form)

Examples:

| Row | citation_ref | citation_human |
|---|---|---|
| Hamsa Mahapurusha firing | `l25_msr_signals.pancha_mahapurusha_hamsa@chart=362f9f17:ay=lahiri:salience=0.92` | "Hamsa Mahapurusha yoga fires: Jupiter in 4H Cancer (kendra, own sign); deterministic strength 0.88; verification certainty 0.92; computed salience 0.92 (Lahiri); domains: spirituality+character+wealth." |
| Synthetic career transformation | `l25_msr_signals.synthetic_career_transformation_window.<period>@chart=...:ay=lahiri:...` | "Synthetic signal: Career Transformation Window during 2030-2032 — composite of (Saturn-Mercury Raja yoga active) + (Saturn return concurrent) + (Sade Sati Anumukha exit); salience 0.78 (Lahiri); domains: career+wealth." |
| Mangal Dosha cancelled | `l25_msr_signals.mangal_dosha_7H@chart=...:ay=lahiri:salience=0.06` | "Mangal Dosha 7H fires but is cancelled (Jupiter aspect to Mars); cancellation_modifier 0.1; effective salience 0.06 (Lahiri)." |

## §10 — Tool retrieval contract

- `query_msr_signals(chart_id, ayanamsha_ids[], scope_filter='all'|'top_K'|'<class>'|'<tradition>'|'<domain>')` → rows
- `query_msr_top_signals(chart_id, ayanamsha_id, top_k=20)` → top-K by computed_salience
- `query_msr_for_domain(chart_id, ayanamsha_id, domain)` → all signals tagged for this domain, ranked by domain_salience
- `query_msr_recurring_patterns(chart_id, ayanamsha_id)` → distinct recurring_pattern_marker groups
- `query_msr_active_at_date(chart_id, ayanamsha_id, date)` → signals whose active_duration_class fires at date
- `query_msr_convergence(chart_id, ayanamsha_id, min_convergence=3)` → signals with system_convergence_count ≥ N
- `query_msr_contradictions(chart_id, ayanamsha_id)` → contradiction pairs

## §11 — Materialized views

- `mv_msr_top_signals_per_chart` — top-100 by salience per (chart, ayanamsha); natal-fixed; refresh at build close
- `mv_msr_recurring_patterns_per_chart` — recurring_pattern_marker aggregations; natal-fixed
- `mv_msr_domain_summary` — per-domain signal counts + total salience contribution; natal-fixed

## §12 — Implementation notes

1. `ga_structural` rows for the chart must exist before `bo_laksana` runs — bo_laksana reads the
   exhaustive L1 enumeration and projects it into `bodha_msr_signals` with population-level enrichment.
   G52 `signal_type_registry` must be seeded before `bo_laksana` runs — as the name/citation catalog
   used for labeling (NOT as a predicate source).
2. Salience formula v1 implemented as pure function; unit tests validate (known inputs → known outputs)
3. Synthetic signal pass runs LAST (after primary signals committed); reads primary MSR rows, computes
   composite population-level enrichment over them
4. Cross-ayanamsha consistency pass runs after all 5 ayanamshas computed; joins across to compute per-signal consistency_score
5. Downstream-enrichment fields (graph_edge_pattern_jsonb, graha_weakness_indicators_jsonb, etc.) populated at write time
6. top_k_salience_rank pre-computed per chart globally after all signals committed
7. Two-pass verification per signal per G52 registry methodology
8. Halt build on divergent_flagged

## §13 — Locked decisions (final committed surface)

1. l25_msr_signals table schema with ~50 columns (full §3)
2. Salience formula v1.0 versioned + unit-tested
3. G52 signal_type_registry as name/citation catalog (~500-700 entries; gates labels, not existence)
4. All 12 signal_type_class enumerations + 7 traditions
5. Synthetic signals INCLUDED
6. All A-V additions + all 10 clarification answers locked
7. ~880-1,250 signals per (chart, ayanamsha); ~4,400-6,250 per chart total
8. Downstream-driven enrichments for CDLM/CGM/RM/UCN/M6/multi-channel
9. 3 materialized views (natal-fixed, refresh at build close)
10. Two-pass verification mandatory per row

---

*End of A10_MSR_SPEC_v1_0.md — LOCKED 2026-05-29. Native sign-off complete.*
