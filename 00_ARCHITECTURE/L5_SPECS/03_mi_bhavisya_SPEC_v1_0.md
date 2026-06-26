---
artifact: 03_mi_bhavisya_SPEC_v1_0.md
canonical_id: L5_SPEC_MI_BHAVISYA
asset_id: mi_bhavisya
asset_kind: data
scope: per_chart
activation: v1
version: 1.0
status: DRAFT — build-ready spec (reconcile [P2] vs sealed phala_pramana column contract)
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
matrix_rows_owned: [§C frozen bundle, §C manifestation_set gen, §C pre-registration emitted_at, §C no-post-hoc-widening freeze, §H L4 leverage]
---

# mi_bhavisya — Prediction Registry (Frozen Bundle + Manifestation Set)

> Sanskrit: *Bhaviṣya* ("the future / predictions"). Mirrors every falsifiable L4 prediction into a
> **scorable, frozen bundle** — the atomic unit calibration scores against. It freezes not just the
> outcome but the WHOLE context (window, confidence, magnitude, domain, driving signals, falsifier,
> base rate) plus the **legitimate manifestation set**, at emission, pre-registered, never widened.

## §1 — Purpose & value
- Reads L4 `phala_pramana` (the falsifiability registry) + `phala_anchors`/`phala_phaladesa` and produces
  one **frozen prediction bundle** per prediction.
- Generates the **manifestation_set** (the legitimate alternate channels a signal may express through).
- Stamps the **pre-registration timestamp** (`emitted_at`) — the admissibility key that makes the later
  calibration honest (only predictions frozen before an event's window count).
- This is the producer of the scorable unit; `mi_pramana` is the consumer.

## §2 — Inputs
| source | what |
|---|---|
| `phala_pramana` (L4) | the falsifier `{metric, comparison, threshold, observation_window, data_source}`, window_status, eval_date, outcome hook — **[P2: exact columns from sealed ph_pramana.py]** |
| `phala_anchors` (L4) | magnitude, confidence_low/high, domain, malleability, derivation_ledger |
| `phala_phaladesa` (L4) | the delivered-outlook framing (for domain/context) |
| `mi_kula` | the classical manifestation source + family ids for `driving_signals` |
| `chart_facts`/`chart_dashas` (L1) | base-rate context + dāśā-lord at window (for binding) |
| L0 `bg_rules`/significations | the manifestation-channel classical lookup |

## §3 — Output schema (build-ready)

### Table: `mimamsa_predictions`  (the frozen bundle; per chart)
```
chart_id                 uuid       not null
prediction_id            text       not null     -- stable id
source_pramana_id        text       not null     -- FK → phala_pramana row (L-is-authority: reference, never restate)
outcome_claim            text       not null     -- what is claimed to happen
domain                   text       not null     -- career/health/relationship/...
observation_window       daterange  not null     -- {start,end}
eval_date                date       not null     -- when it becomes checkable
confidence_band          numrange   not null     -- inherited from phala_anchors (the two-key input)
magnitude_expected       text       not null     -- minor/moderate/major/rupture
falsifier_jsonb          jsonb      not null     -- the frozen {metric,comparison,threshold,window,data_source}
base_rate                numeric                  -- how often this outcome happens anyway (R-1) [computed/P2]
emitted_at               timestamptz not null     -- PRE-REGISTRATION SEAL (admissibility key)
lifecycle_status         text       not null     -- 'pending'|'due'|'confirmed'|'denied'|'partial'
driving_signals          jsonb      not null     -- [{signal_id, family_id, role: 'what'|'when'|'magnitude'}] (lineage for attribution)
frozen_bundle_hash       text       not null     -- hash of the immutable bundle (tamper/repro check)
bundle_formula_version   text       not null     -- versioned (D-2)
created_at               timestamptz not null
PRIMARY KEY (chart_id, prediction_id)
```

### Table: `mimamsa_manifestation_sets`  (the legitimate channels, frozen per prediction)
```
chart_id                 uuid       not null
prediction_id            text       not null     -- FK → mimamsa_predictions
channel_id               text       not null     -- e.g. 'mother_health','property','residence'
domain                   text       not null
source                   text       not null     -- 'classical_cited' | 'llm_flagged_cited'
citation_ref             jsonb      not null     -- REQUIRED (no channel counts without a citation)
is_literal               boolean    not null     -- the originally-predicted channel?
frozen_at                timestamptz not null     -- == prediction.emitted_at (frozen with the bundle)
PRIMARY KEY (chart_id, prediction_id, channel_id)
```

## §4 — Computation logic (deterministic)

### 4.1 — Bundle assembly (L-is-authority)
- For each `phala_pramana` row, assemble the bundle by **referencing** the L4 ids and **inheriting** their
  values (never restating/recomputing — `§N.5`). `source_pramana_id` is the anchor; a mismatch between the
  inherited value and the live L4 fact is a **halt** (not a stored divergence).
- `confidence_band` inherited from `phala_anchors` (currently capped ~0.506 at n=0 — the honest ceiling
  L5 will lift over time).

### 4.2 — base_rate (R-1)
- Deterministically estimate how often the claimed outcome occurs anyway, per domain, from the LEL domain
  frequencies + `[P2]` a classical/empirical base-rate table. Stored so `mi_pramana` can compute
  base-rate-adjusted skill (a hit on a common event is weak evidence). If no basis → `null` + flagged
  "base_rate_unavailable" (never fabricated).

### 4.3 — manifestation_set generation (HYBRID, citation-gated, FROZEN)
- **Classical spine (deterministic, L0):** look up the prediction's driving house/karaka/signal in
  `bg_rules`/significations → the canonical manifestation channels, each with its `bg_texts` citation.
  `source='classical_cited'`.
- **LLM-suggested additions (flagged, citation-required):** an LLM may propose additional channels;
  each is stored ONLY if it carries a resolvable classical citation; `source='llm_flagged_cited'`.
  Un-cited suggestions are NOT stored as scorable channels (may be logged elsewhere for review).
- The whole set is **frozen at `emitted_at`** (= `frozen_at`). **It can never be widened after the
  event** — enforced by the immutability of the bundle hash + a seal gate in `mi_pramana`.
- `is_literal=true` marks the originally-predicted channel (full credit); others are alternate
  (graded-partial credit when matched).

### 4.4 — Lifecycle + due-detection
- `lifecycle_status` starts `pending`; flips to `due` when `eval_date` passes AND candidate LEL evidence
  exists (the due-detection runs in the `mi_abhilekha` sweep, which updates this column). `confirmed/
  denied/partial` are written by `mi_pramana` after scoring.

### 4.5 — No-LEL behavior
- Predictions are still mirrored + frozen + staged (`pending`) with full bundles + manifestation sets.
  They are *ready to score* the moment events arrive. Nothing about no-LEL stops the registry.

## §5 — Retrievability contract (feeds mi_darshana)
- Each frozen bundle is a retrievable **prediction unit**: outcome, window, confidence, magnitude,
  manifestation channels (with citations), lifecycle. The LLM can pull "what was predicted for career,
  by when, at what confidence, and what would count as it coming true."
- Trust-metadata (R5): `emitted_at` (pre-registration), `confidence_band`, `base_rate` travel with the unit.

## §6 — Determinism & seal gates
- No LLM in scoring; LLM only *proposes* manifestation channels, citation-gated (D-1 holds — the stored
  scorable set is deterministic/cited).
- `frozen_bundle_hash` + `bundle_formula_version` → tamper-evident, reproducible (RL-1, D-2).
- **L-is-authority gate:** inherited values must match live L4 facts (halt on divergence).
- **Pre-registration integrity:** `emitted_at` is immutable once set.
- **No-post-hoc-widening gate** (with `mi_pramana`): the manifestation set's frozen_at == emitted_at; any
  post-event addition is a halt-worthy violation.
- Degenerate-distribution guard on `domain`, `magnitude_expected`, `lifecycle_status`.
- Registered with drift_detector + schema_validator (RL-5).

## §7 — Frozen-orchestrator conformance
`@register('mi_bhavisya')` `WriterBase`; per_chart; delete-then-insert on `(chart_id × prediction_id)`;
`conn=ctx.db_conn` never committed; `WriterResult(rows_inserted=…)`; `count_sql`:
`SELECT count(*) FROM mimamsa_predictions WHERE chart_id = $1`.

## §8 — `depends_on`  (CORRECTED — ASSET-IDs, not table names)
`['ph_pramana', 'ph_nimitta', 'ph_phaladesa', 'mi_kula', 'mi_jivanaghatana']`
(was `['bo_laksana','ka_kalasutra']` — the bug). **CRITICAL:** depends_on takes ASSET-IDs, not table
names — `ph_pramana` is the asset whose table is `phala_pramana`; `ph_nimitta` is the asset whose table is
`phala_anchors`. Using table names = a silently-dead DAG edge (see L5_BUILD_READINESS_AUDIT §2). `[P2 ratify]`.

## §9 — Matrix rows satisfied
frozen bundle (§C) ✅ · manifestation_set hybrid+citation-gated+frozen (§C/§5A) ✅ · pre-registration
emitted_at (§C/HC-5) ✅ · no-post-hoc-widening freeze (§C) ✅ · base_rate (R-1) ✅ · L4 leverage + L-is-authority
(§H) ✅ · driving_signals lineage for attribution (§C) ✅ · retrieval prediction-unit (R1/R5) ✅ · determinism
gates (§G) ✅.

*End 03_mi_bhavisya_SPEC v1.0.*
