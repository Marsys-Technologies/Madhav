---
artifact: 04_mi_pramana_SPEC_v1_0.md
canonical_id: L5_SPEC_MI_PRAMANA
asset_id: mi_pramana
asset_kind: data
scope: per_chart
activation: v1
version: 1.0
status: DRAFT — build-ready spec
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
matrix_rows_owned: [§C matcher, §C scorecard, §C falsifier-as-judge, §C graded credit, §C base-rate/null-models, §C reliability/Brier/ECE, §C held-out gate + min-n honesty, §C pre-registration admissibility check, §C no-post-hoc-widening enforce, §F no-LEL mode, §G frozen formulas]
---

# mi_pramana — Matcher + Multi-Dimensional Scorecard + Calibration Engine

> Sanskrit: *Pramāṇa* ("valid proof / means of knowledge"). The heart of L5. It deterministically matches
> due predictions to admissible life events (many-to-many), scores each match on a **multi-dimensional
> scorecard** (timing / magnitude / domain / falsifier / manifestation), and aggregates into
> **base-rate-adjusted, held-out-gated reliability curves** with honest meta-calibration. The falsifier
> is the judge; the math is deterministic and reproducible.

## §1 — Purpose & value
Turns "we predicted X" + "Y happened" into an honest, multi-axis verdict and a calibration picture — the
thing no human acharya can do at scale: score a lifetime of predictions on multiple dimensions at once,
adjusted for base rates, gated on held-out evidence, and report how well-calibrated the instrument's own
confidence is.

## §2 — Inputs
| source | what |
|---|---|
| `mimamsa_predictions` + `mimamsa_manifestation_sets` (`mi_bhavisya`) | the frozen bundles to score |
| `vw_mimamsa_admissible_clean` + `vw_mimamsa_held_out` (`mi_jivanaghatana`) | the evidence (clean / held-out) |
| `mi_kula` | family ids + base-rate/null-model context |
| pinned external data (via `mi_kula`) | for external-family falsifier evaluation |

## §3 — Output schema (build-ready)

### Table: `mimamsa_calibration`  (per scored prediction×event match)
```
chart_id                 uuid       not null
match_id                 text       not null     -- unique per (prediction × event) scored pair
prediction_id            text       not null     -- FK → mimamsa_predictions
event_id                 text       not null     -- FK → mimamsa_event_provenance
-- scorecard dimensions (each 0..1, deterministic):
score_timing             numeric    not null     -- in-window? distance-graded
score_magnitude          numeric    not null     -- predicted vs assessed intensity
score_domain             numeric    not null     -- domain/character specificity
score_falsifier          numeric    not null     -- frozen {metric,comparison,threshold} evaluated (THE JUDGE)
score_manifestation      numeric    not null     -- literal=1.0 / alternate_cited=partial / resonance-only<partial / none=0
manifestation_channel    text                    -- WHICH channel fired (recorded; feeds mi_sambandha)
composite_verdict        text       not null     -- 'confirmed'|'partial'|'denied'|'pending'
composite_score          numeric    not null     -- graded composite
base_rate_adjusted_skill numeric                  -- composite discounted by base_rate (R-1)
evidence_admissibility   text       not null     -- 'clean'|'contaminated'|'held_out' (which grade it feeds)
n_for_stratum            int        not null      -- the n behind this (R5 trust)
leakage_status           text       not null      -- inherited from evidence provenance
scoring_formula_version  text       not null      -- versioned (D-2)
scored_at                timestamptz not null
PRIMARY KEY (chart_id, match_id)
```

### Table: `mimamsa_reliability`  (aggregated calibration curves)
```
chart_id                 uuid       not null
stratum_key              text       not null     -- e.g. 'domain=career|tier=moderate|family=T-NAKPADA'
predicted_prob_bin       numrange   not null     -- the confidence bin
observed_rate            numeric                  -- actual hit rate in that bin (NULL if < min_n)
n                        int        not null
ci_low                   numeric                  -- bootstrapped
ci_high                  numeric
brier_score              numeric                  -- diagnostic
log_loss                 numeric                  -- diagnostic
ece                      numeric                  -- expected calibration error (diagnostic)
hit_rate_by_tier         numeric                  -- headline metric
held_out_validity        text       not null      -- 'pass'|'fail'|'insufficient_n'
evidence_grade           text       not null      -- 'empirical'|'prior_only'|'structural'
calibration_formula_ver  text       not null
computed_at              timestamptz not null
PRIMARY KEY (chart_id, stratum_key, predicted_prob_bin)
```

## §4 — Computation logic (deterministic)

### 4.1 — Many-to-many candidate matching (COMPARISON §4)
```
for each due prediction P (lifecycle_status='due'):
  candidates = admissible events E where
       E.event_date ∈ (P.observation_window ± tolerance)          -- timing gate
   AND domain_compatible(E.domain, P.domain ∪ P.manifestation_set.domains)   -- domain gate (incl. alternates)
   AND falsifier_addressable(E, P.falsifier_jsonb)                -- can E speak to P's test?
  for each candidate E: emit a match row (one prediction may score many events; one event many predictions)
```
All gates are computed predicates → same inputs yield same candidate set (RL-1). No LLM.

### 4.2 — The scorecard (COMPARISON §3 + §5A)
- `score_timing`: 1.0 in-window, graded down by distance outside.
- `score_magnitude`: closeness of `magnitude_expected` to the event's assessed magnitude.
- `score_domain`: domain + outcome-character match.
- `score_falsifier`: evaluate the **frozen** `{metric, comparison, threshold}` against the event's
  `data_source` value. **THE JUDGE:** `composite_verdict` cannot be `confirmed` unless `score_falsifier`
  passes, regardless of the other dimensions.
- `score_manifestation` (graded credit): literal channel matched → 1.0; pre-declared **alternate** channel
  matched AND falsifier met → high-partial (records `manifestation_channel`); same-domain echo that does
  NOT meet falsifier → thematic-resonance partial, **never `confirmed`**; no match → 0.
- `composite_score` = deterministic function of the five; `composite_verdict` = graded label.
- `base_rate_adjusted_skill` = composite discounted by `base_rate` (credit scales with surprise).

### 4.3 — Aggregation into reliability curves
- Group matches by `stratum_key` (domain × tier × family). Per predicted-prob bin: compute `observed_rate`
  (clean evidence only for headline), bootstrap CIs, Brier/log-loss/ECE (diagnostics), hit-rate-by-tier
  (headline). **Below `min_n` → `observed_rate=NULL`, `held_out_validity='insufficient_n'`** (B.12 honesty
  — never a fabricated number).
- **Held-out validity gate:** re-score on `vw_mimamsa_held_out`; if per-stratum calibration error within
  tolerance → `pass`; else `fail` (a `fail` blocks promotion of that stratum's families in `mi_gunanaka`).
- **Meta-calibration (HC-2):** the reliability curve IS the "when we say 70%, are we right 70%?" answer —
  surfaced as the instrument's own trustworthiness score.

### 4.4 — Pre-registration admissibility (HC-5) + no-widening enforcement
- A match counts toward calibration ONLY if `prediction.emitted_at < event.observation_window.start`
  (frozen before the window). Retrodictive matches are scored but tagged `contaminated`, never headlined.
- **No-post-hoc-widening enforcement:** verify `manifestation_set.frozen_at == prediction.emitted_at`
  for every channel scored; a channel added after the event → halt (integrity violation).

### 4.5 — No-LEL / structural-prior-only mode
- With zero admissible events: emit NO calibration rows; `mimamsa_reliability.evidence_grade='structural'`
  or `'prior_only'`; no empirical numbers produced. Families contribute at prior weight only (via overlay).
  `mi_seva` reports `calibration_mode='structural_prior_only'`.

## §5 — Retrievability contract (feeds mi_darshana)
- Reliability curves + per-prediction verdicts are retrievable insight units, each carrying **n,
  leakage_status, evidence_grade, freshness** (R5) so the LLM weights them correctly. The
  `manifestation_channel` field feeds `mi_sambandha`. The "insufficient_n" states are retrievable as
  honest "we don't know yet" (B.12 surfaced).

## §6 — Determinism & seal gates
- No LLM anywhere (D-1). Frozen `scoring_formula_version` + `calibration_formula_ver` (D-2). Re-run =
  byte-identical verdicts + curves (RL-1) — the load-bearing reliability test.
- **Falsifier-as-judge gate:** assert no `confirmed` with failing `score_falsifier`.
- **Pre-registration gate** (HC-5) + **no-widening gate** enforced here.
- **Insufficient-evidence honesty gate** (B.12): below min_n → no number.
- Degenerate-distribution guard on `composite_verdict`, `manifestation_channel`, stratum coverage (this is
  exactly where the all-Jupiter class of bug would be caught).
- Registered with drift_detector + schema_validator (RL-5).

## §7 — Frozen-orchestrator conformance
`@register('mi_pramana')` `WriterBase`; per_chart; `plan_substeps`+`run_substep` (heavy: match → score →
aggregate); delete-then-insert on `(chart_id × match_id)` and `(chart_id × stratum_key × bin)`;
`conn=ctx.db_conn` never committed; `count_sql`: `SELECT count(*) FROM mimamsa_calibration WHERE chart_id = $1`.

## §8 — `depends_on`
`['mi_bhavisya', 'mi_jivanaghatana']` (+ reads `mi_kula` for context). `[P2 reconcile]`.

## §9 — Matrix rows satisfied
matcher (§C) ✅ · scorecard incl. manifestation dim (§C/§5A) ✅ · falsifier-as-judge (§C) ✅ · graded credit
(§C) ✅ · base-rate + null-model (§C/R-1/R-2) ✅ · reliability/Brier/ECE/meta-cal (§C/HC-2) ✅ · held-out gate +
min-n honesty (§C/HC-4/B.12) ✅ · pre-registration admissibility (§C/HC-5) ✅ · no-post-hoc-widening enforce
(§C) ✅ · no-LEL mode (§F) ✅ · frozen formulas + repro + degenerate guard (§G) ✅ · R5 trust-metadata source ✅.

*End 04_mi_pramana_SPEC v1.0.*
