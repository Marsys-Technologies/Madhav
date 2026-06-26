---
artifact: 09_mi_darshana_SPEC_v1_0.md
canonical_id: L5_SPEC_MI_DARSHANA
asset_id: mi_darshana
asset_kind: data
scope: per_chart
activation: v1
version: 1.0
status: DRAFT — build-ready spec (NEW asset, R1–R6: THE retrievable layer)
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
matrix_rows_owned: [§B R1 insight surface, §B R2 embeddings, §B R3 query-views, §B R4 provenance chain, §B R5 trust-metadata, §B R6 negative knowledge]
---

# mi_darshana — The Insight-Retrieval Surface (the LLM's interface to L5)

> Sanskrit: *Darśana* ("seeing / showing"). The layer that makes everything L5 computes *visible and
> usable to the synthesis LLM*. It does not compute new astrology — it **reshapes** L5's outputs
> (calibration, overlays, grammar, discoveries, negative knowledge) into pre-composed, embedded,
> query-shaped, provenance-chained, trust-tagged **insight units** the LLM can retrieve and synthesize
> without re-deriving. This is the answer to "is L5 built for retrievability." (R1–R6.)

## §1 — Purpose & value
The synthesis LLM should never have to query 4 raw L5 tables and stitch them. `mi_darshana` gives it
**finished insight units**: ranked, self-describing, semantically searchable, each carrying its trust
metadata and full provenance, including what's been ruled OUT. Without this, all of L5's superhuman
computation is stranded in tables the LLM can't efficiently use. (B.9 — LLM-readability first.)

## §2 — Inputs (it aggregates the whole layer)
| source | what it surfaces |
|---|---|
| `mi_pramana` (calibration, reliability) | confidence-adjusted outlooks + meta-calibration |
| `mi_adhilepa` (overlay, load-bearing) | effective adjustments + sensitivity (what's load-bearing) |
| `mi_sambandha` (grammar) | the manifestation grammar units |
| `mi_pariksha` (discoveries) | emergent laws, contradiction-dominance, rhythms |
| `mi_kula` (families, neg-controls) | active families + ruled-out / suspended (negative knowledge) |
| `mi_gunanaka` (weights) | what's trusted/distrusted, with status |
| `mi_jivanaghatana` (evidence summary) | n + freshness for trust metadata |

## §3 — Output schema (build-ready)

### Table: `mimamsa_insight_units` (R1 — pre-composed, ranked)
```
chart_id                 uuid       not null
insight_id               text       not null
insight_type             text       not null   -- 'calibrated_outlook'|'manifestation_grammar'|'emergent_law'|'load_bearing'|'negative_knowledge'|'contradiction_dominance'|'temporal_rhythm'
domain                   text                   -- career/health/... (for query-shaping)
horizon                  text                   -- 'near'|'lifetime'
question_lens            text                   -- maps to bodha_question_lenses (R3)
statement                text       not null    -- the insight, in LLM-ready prose
rank_consequence         numeric    not null    -- for "if you read nothing else" ranking
-- R5 trust-metadata ON the unit:
confidence_band          numrange
n_support                int        not null
leakage_status           text       not null
evidence_grade           text       not null    -- 'empirical'|'prior_only'|'structural'
freshness_lel_version    text       not null
last_calibrated_at       timestamptz
-- R4 provenance chain (materialized as one object):
provenance_chain         jsonb      not null    -- insight → verdict → scorecard dims → driving signals → L1 fact → L0 citation
is_negative_knowledge    boolean    not null    -- R6: "ruled OUT for this native"
surface_formula_version  text       not null
updated_at               timestamptz not null
PRIMARY KEY (chart_id, insight_id)
```

### Table: `mimamsa_insight_embeddings` (R2 — semantic retrieval)
```
chart_id, insight_id, embedding vector(768), embed_model_version, embedded_at
PRIMARY KEY (chart_id, insight_id)
```

### Views (R3 — query-shaped):
`vw_mimamsa_insight_by_domain`, `vw_mimamsa_insight_by_horizon`, `vw_mimamsa_insight_by_lens`,
`vw_mimamsa_negative_knowledge` — each pre-joins the scattered pieces into the shape a question needs.

## §4 — Computation logic (deterministic)

### 4.1 — Insight-unit composition (R1)
- Deterministically compose each L5 output into an `insight_unit` with LLM-ready `statement` text built
  from a **fixed template** over the structured fields (NOT generative — template-filled, so deterministic
  and non-fabricating). `rank_consequence` = deterministic function of confidence × consequence × n.
- Coverage rule: every promoted/supported discovery, every empirical calibration stratum, every grammar
  cell with evidence, and every active family becomes a unit. Nothing computed in L5 is left un-surfaced.

### 4.2 — Embeddings (R2) — deterministic transform
- Embed each `statement` with the pinned embedding model (the same kind used for `bodha_signal_embeddings`,
  66,738). Embeddings are a deterministic transform → allowed under D-1. Enables "find what we've learned
  relevant to a career question" semantic retrieval.

### 4.3 — Query-shaped views (R3)
- Pre-join per domain / horizon / question-lens so a single LLM query (e.g. "career outlook + what's
  load-bearing for it") hits one view, not four tables. Maps to the existing `bodha_question_lenses` for
  consistency with the Whole-Chart-Read.

### 4.4 — Provenance chain (R4)
- Materialize the FULL chain per unit as one retrievable object: insight → calibration verdict → scorecard
  dimensions → driving signals → L1 fact id → L0 classical citation. The LLM can ground any claim without
  N lookups. (Sourced from `mi_adhilepa.derived_from_pramana_ids` + `mi_pramana` + `mi_bhavisya` lineage.)

### 4.5 — Trust-metadata ON the unit (R5)
- Every unit carries confidence_band, n_support, leakage_status, evidence_grade, freshness — so the LLM
  weights what it pulls and **cannot confidently synthesize weak insight**. A `structural`/`prior_only`
  unit is visibly not `empirical`.

### 4.6 — Negative knowledge (R6)
- Surface, as retrievable units, what's been **ruled out** for this native: negative-control results,
  suspended weights/families, low-propensity manifestation channels, disproven discoveries.
  `is_negative_knowledge=true`; `vw_mimamsa_negative_knowledge` gives the LLM "do NOT attribute this to X —
  it scored null for this native." Few systems offer this — a differentiator.

### 4.7 — No-LEL behavior
- Surfaces the structural + prior units (the classical reading, the grammar baseline, the families at
  prior weight, the falsifiability staging) with `evidence_grade` honestly `structural`/`prior_only`. The
  LLM still gets a rich, retrievable, honestly-labeled L5 surface even with zero outcomes — exactly the
  "maximally valuable at n=1 today" goal.

## §5 — Contribution-control integration
- `mi_seva` reads `mimamsa_insight_units` through the toggles: `learning_influence` off → serve only
  `structural`/`prior_only` units (or base); `lel_citation` off → suppress units that quote literal LEL
  events. The retrieval surface respects the user's governance.

## §6 — Determinism & seal gates
- No generative LLM in composition (template-filled statements) (D-1). Embeddings deterministic.
  Frozen `surface_formula_version` + `embed_model_version` (D-2); re-run identical (RL-1).
- **Coverage gate:** every empirical/supported L5 output has a corresponding insight unit (nothing
  stranded) — the retrievability completeness check.
- **Trust-metadata-present gate:** no unit without confidence/n/evidence_grade/freshness (R5 enforced).
- Degenerate-distribution guard on `insight_type`, `domain`, `evidence_grade`.
- Registered with drift_detector + schema_validator (RL-5).

## §7 — Frozen-orchestrator conformance
`@register('mi_darshana')` `WriterBase`; per_chart; `plan_substeps`+`run_substep` (compose → embed →
view-refresh); delete-then-insert on `(chart_id × insight_id)`; `conn=ctx.db_conn` never committed;
`count_sql`: `SELECT count(*) FROM mimamsa_insight_units WHERE chart_id = $1`. Storage_type pgvector for the
embeddings table. **Retrieval primitives** for `L5_mimamsa` registry are defined here (the tools/resources
the LLM calls).

## §8 — `depends_on`
`['mi_pramana','mi_adhilepa','mi_sambandha','mi_pariksha','mi_gunanaka','mi_kula','mi_jivanaghatana']`
(it aggregates the layer — last data asset in the DAG). `[P2 reconcile]`.

## §9 — Matrix rows satisfied
R1 insight surface ✅ · R2 embeddings ✅ · R3 query-views ✅ · R4 provenance chain ✅ · R5 trust-metadata
on unit ✅ · R6 negative knowledge ✅ · no-LEL structural surface ✅ · contribution-control integration ✅ ·
coverage + trust-present gates ✅ · determinism (§G) ✅.

*End 09_mi_darshana_SPEC v1.0. This is THE retrievable layer the native required — the LLM's complete,
accurate, self-describing interface to everything L5 knows, including what it has ruled out.*
