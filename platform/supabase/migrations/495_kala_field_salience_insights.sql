-- migration 495: kala_field_salience + kala_insights (ṢAḌ-DARŚANA W2 Lane D)
-- =============================================================================
-- RENUMBER NOTE (2026-07-30, Conductor merge-train pass): originally landed as 487
-- (see the re-verification note below for why). By the time all five W2 lanes were
-- ready to merge together, 487 collided with a sibling lane's own independent
-- re-verification — renumbered to 495, the next free slot above the full set of
-- five lanes' claimed numbers (488-494), so all five can merge without re-colliding
-- against each other. The re-verification narrative below is preserved as-is; only
-- the final claimed number changed.
-- =============================================================================
-- Context: KALA_W2_FIELD_DESIGN_v1_0.md §6 (Lane D — Stage 6 salience +
-- submodular selection + rarity axis (item 25/15); Stage 6.5 insight synthesis
-- (E2)). §9.3 originally reserved 481 (`kala_field_salience_insights`) for this
-- migration inside a 474-483 range assumed free as of the 2026-07-30 correction.
--
-- MIGRATION NUMBER RE-VERIFICATION (per §9.3's own standing instruction: "whichever
-- lane writes the first W2 migration MUST re-verify the live max immediately before
-- use, since this reservation can go stale exactly as the original one did"): at
-- the time this file was written, `platform/scripts/ci/migration_number_guard.ts`
-- (the cross-directory guard landed by #921/MIG-1) reported live max = 486 across
-- BOTH `platform/migrations/` (474) and `platform/supabase/migrations/` (486 —
-- 484/484/485/486 had already landed for other ṢAḌ-DARŚANA/SAMĀPTI work since the
-- §9.3 correction was written). 481 is therefore STALE — using it would go
-- backwards past already-shipped migrations. The guard's own allocation rule
-- (`max(...) + 1`) gives 487, confirmed via `npx tsx scripts/ci/migration_number_guard.ts`
-- (no --json needed; the tool's own stdout states "next allocatable number: 487").
-- This migration claims 487, not 481.
--
-- Tables owned by Lane D only (§0 lane table): kala_field_salience, kala_insights.
-- Both are per-chart tables written by the (not-yet-landed) ka_kshetra heavy writer
-- (Lane C's orchestration shim) during stage 6 / stage 6.5 of the ten-stage field
-- pipeline — this migration creates ONLY the tables; no seed rows, no
-- asset_registry insert (kala_field_salience/kala_insights are sub-tables of the
-- `ka_kshetra` asset, not standalone assets — the asset_registry row for
-- `ka_kshetra` itself lands in migration 483 per §9.3's table, not here).
--
-- kala_field_salience — §6.1 salience vector + §6.2 submodular selection trace.
-- One row per (chart_id, window_id): the five-factor vector (Informativeness,
-- Consequence, Relevance, Reliability, Actionability), each nullable (a factor
-- that could not be computed is NULL and carries `not_computed` coverage upstream
-- — §6.1: "never imputed"), the versioned ordering scalar, `salience_basis`
-- (which factors were actually present, since missing factors are renormalized
-- over the present ones rather than fabricated), and the submodular selection
-- outcome for that window under the greedy lazy facility-location run this field
-- build performed (§6.2): whether it was selected, its rank, marginal gain, the
-- atoms it newly covered, and (served once per chart, denormalized onto every
-- row for cheap reads) the run's overall coverage_fraction and largest_omission.
--
-- kala_insights — §6.4 the 8-type insight catalog (7 non-LEL types are Lane D's
-- scope; `biographical_echo` is written by Lane E's biographical-join refresh
-- with `lel_derived = TRUE` — see the CIRCULARITY GUARD CARVE-OUT below). Schema
-- follows §6.4's own SQL block (KALA_W2_FIELD_DESIGN_v1_0.md lines ~1351-1370)
-- closely -- Lane D does not redesign this table, only builds it -- plus
-- `computed_at`, the `kala_insights_snapshot_or_lel_ck` CHECK, and three
-- lookup indexes the doc's snippet did not spell out but every sibling
-- `kala_*` table in this migration range carries.
--
-- CIRCULARITY GUARD CARVE-OUT (§6.4, §8.3 CG-1 — binding, not a Lane D choice):
-- the field hash (§7.4, Lane E) covers only `kala_insights` rows with
-- `lel_derived = FALSE`. Stage 6.5 (this lane, inside `ka_kshetra`, hash-covered)
-- writes ONLY the seven non-LEL types, always with `lel_derived = FALSE`. A row
-- with `lel_derived = TRUE` is written exclusively by Lane E's biographical-join
-- refresh path, never by this lane's stage65_insights.py.
--
-- Idempotency (§N.3 — L1+/per-chart = delete-then-insert scoped to
-- (chart_id × natural key), never accretes): the natural key for
-- kala_field_salience is (chart_id, window_id); for kala_insights it is
-- (chart_id, insight_id) per §6.4's own UNIQUE constraint. Deletion happens ONCE
-- in `ka_kshetra`'s `plan_substeps` (Lane C's writer, §8.1) — this migration only
-- declares the uniqueness constraints the delete-then-insert pattern depends on.
-- =============================================================================

BEGIN;

-- ── kala_field_salience (§6.1 vector + §6.2 submodular trace) ────────────────

CREATE TABLE IF NOT EXISTS kala_field_salience (
    id                      BIGSERIAL PRIMARY KEY,
    chart_id                UUID        NOT NULL,
    window_id               TEXT        NOT NULL,      -- kala_field_windows.window_id (item 44 authority_basis)
    event_class             TEXT        NOT NULL,

    -- §6.1 the five-factor vector, each in [0,1] or NULL (never imputed —
    -- a NULL factor means "not_computed", carried as honest coverage upstream,
    -- and is excluded from the weighted sum via renormalization, not scored 0).
    factor_informativeness  DOUBLE PRECISION,           -- I
    factor_consequence      DOUBLE PRECISION,           -- Q
    factor_relevance        DOUBLE PRECISION,           -- R
    factor_reliability      DOUBLE PRECISION,           -- B
    factor_actionability    DOUBLE PRECISION,           -- A

    -- The versioned ordering scalar (§6.1): Σ v_f · factor_f over PRESENT
    -- factors only, renormalized so the present weights sum to 1.
    salience                DOUBLE PRECISION NOT NULL,
    salience_weights_version TEXT       NOT NULL,       -- e.g. 'salience_v0' — the v_f vector version
    salience_basis          TEXT[]      NOT NULL,        -- factor keys actually present, e.g. {I,Q,R,B,A} minus absent

    -- §6.2 submodular selection outcome for this window under the run this
    -- field build performed. `selection_rank` is 1-based rank in selection
    -- order; NULL when not selected. `marginal_gain` / `atoms_newly_covered`
    -- are only meaningful (non-NULL / non-empty) for selected rows.
    selected                BOOLEAN     NOT NULL DEFAULT FALSE,
    selection_rank          INT,
    marginal_gain           DOUBLE PRECISION,
    atoms_newly_covered     JSONB,                       -- [{event_class, window_family_id, driver_term_key}, ...]

    -- Run-level submodular summary, denormalized onto every row of the chart's
    -- run for cheap reads (identical across all rows of one build/run).
    coverage_fraction       DOUBLE PRECISION,            -- F(S)/F(V) for this chart's selection run
    largest_omission_window_id TEXT,                     -- highest-Delta unselected candidate, if any
    largest_omission_marginal_gain DOUBLE PRECISION,

    weights_version         TEXT        NOT NULL,        -- field weights_version this window was built under (§7.3)
    cohort_version          TEXT,                         -- bg_cohort content fingerprint used for factor_informativeness (§6.3 rule 5)
    x_schema_version        TEXT        NOT NULL,
    field_snapshot_id       TEXT        NOT NULL,
    computed_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (chart_id, window_id),

    -- Defense-in-depth range CHECKs, matching the pattern the sibling
    -- kala_field table (migration 478, e.g. kala_field_suppression_range_ck)
    -- already applies -- app-layer clamp01()/min(1,...) calls make these
    -- low-risk, but a stray write bypassing the Python layer should still
    -- fail loudly rather than silently persist an out-of-range factor.
    CONSTRAINT kala_field_salience_factor_i_range_ck
      CHECK (factor_informativeness IS NULL OR factor_informativeness BETWEEN 0 AND 1),
    CONSTRAINT kala_field_salience_factor_q_range_ck
      CHECK (factor_consequence IS NULL OR factor_consequence BETWEEN 0 AND 1),
    CONSTRAINT kala_field_salience_factor_r_range_ck
      CHECK (factor_relevance IS NULL OR factor_relevance BETWEEN 0 AND 1),
    CONSTRAINT kala_field_salience_factor_b_range_ck
      CHECK (factor_reliability IS NULL OR factor_reliability BETWEEN 0 AND 1),
    CONSTRAINT kala_field_salience_factor_a_range_ck
      CHECK (factor_actionability IS NULL OR factor_actionability BETWEEN 0 AND 1),
    CONSTRAINT kala_field_salience_salience_range_ck
      CHECK (salience BETWEEN 0 AND 1),
    CONSTRAINT kala_field_salience_coverage_fraction_range_ck
      CHECK (coverage_fraction IS NULL OR coverage_fraction BETWEEN 0 AND 1),
    CONSTRAINT kala_field_salience_marginal_gain_nonneg_ck
      CHECK (marginal_gain IS NULL OR marginal_gain >= 0),
    CONSTRAINT kala_field_salience_largest_omission_gain_nonneg_ck
      CHECK (largest_omission_marginal_gain IS NULL OR largest_omission_marginal_gain >= 0)
);

CREATE INDEX IF NOT EXISTS idx_kala_field_salience_chart
    ON kala_field_salience (chart_id, selected, salience DESC);
CREATE INDEX IF NOT EXISTS idx_kala_field_salience_event_class
    ON kala_field_salience (chart_id, event_class);

COMMENT ON TABLE kala_field_salience IS
  'KALA_W2_FIELD_DESIGN_v1_0.md §6.1/§6.2 (Lane D, ṢAḌ-DARŚANA W2 item 25): one row '
  'per (chart_id, window_id) — the five-factor salience vector (Informativeness, '
  'Consequence, Relevance, Reliability, Actionability), its versioned weighted '
  'ordering scalar, and the greedy lazy facility-location submodular selection '
  'outcome (selected/rank/marginal_gain/atoms_newly_covered) for the field build '
  'run that produced it. Written by services/ka_kshetra/stage6_salience.py + '
  'submodular.py, inside the ka_kshetra heavy writer (Lane C).';

COMMENT ON COLUMN kala_field_salience.salience_basis IS
  'Factor keys among {I,Q,R,B,A} that were actually present (non-NULL) for this '
  'row. Missing factors are renormalized over the present ones per §6.1 -- never '
  'imputed as 0. An empty/single-factor basis is honest, not an error.';
COMMENT ON COLUMN kala_field_salience.atoms_newly_covered IS
  'Per §6.2 selection_trace: the information-atom universe entries '
  '{event_class, window_family_id, driver_term_key} this window newly covered '
  'when it was greedily selected. Empty/NULL for unselected rows.';

-- ── kala_insights (§6.4 — the 8-type catalog; schema per the design doc verbatim) ──

CREATE TABLE IF NOT EXISTS kala_insights (
    id BIGSERIAL PRIMARY KEY,
    chart_id UUID NOT NULL,
    insight_id TEXT NOT NULL,                 -- 'kin_' + sha256(...)[:24]; the drill id
    insight_type TEXT NOT NULL CHECK (insight_type IN
      ('concurrence','rarity_firing','biographical_echo','absence_of_expected',
       'compression','scarcity','reversal','contrast')),
    event_class TEXT, window_id TEXT,          -- the carrier window (NULL for absence_of_expected)
    t_start DOUBLE PRECISION, t_end DOUBLE PRECISION,
    statement_key TEXT NOT NULL,               -- the composer template key (NOT prose — B.10)
    statement_params JSONB NOT NULL,           -- the computed values the template fills
    fact_ids TEXT[] NOT NULL,
    cohort_surprise DOUBLE PRECISION, cohort_version TEXT, surprise_basis TEXT NOT NULL,
    robustness JSONB NOT NULL,
    insight_score DOUBLE PRECISION NOT NULL,
    lel_derived BOOLEAN NOT NULL DEFAULT FALSE,
    weights_version TEXT NOT NULL, field_snapshot_id TEXT,   -- NULL allowed iff lel_derived
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (chart_id, insight_id),
    -- CIRCULARITY GUARD CARVE-OUT (§6.4/§8.3): field_snapshot_id is required for
    -- every stage-6.5 (non-LEL) row, since the field hash covers exactly the rows
    -- that carry one; only an lel_derived=TRUE row (Lane E's biographical-join
    -- refresh, never this lane's writer) may have it NULL.
    CONSTRAINT kala_insights_snapshot_or_lel_ck
      CHECK (field_snapshot_id IS NOT NULL OR lel_derived = TRUE),
    -- Range CHECKs matching kala_field_salience's convention (above) --
    -- insight_score = cohort_surprise * carrier_salience * reliability, all
    -- three factors in [0,1], so the product is always in [0,1] too.
    CONSTRAINT kala_insights_cohort_surprise_range_ck
      CHECK (cohort_surprise IS NULL OR cohort_surprise BETWEEN 0 AND 1),
    CONSTRAINT kala_insights_score_range_ck
      CHECK (insight_score BETWEEN 0 AND 1)
);

CREATE INDEX IF NOT EXISTS idx_kala_insights_chart
    ON kala_insights (chart_id, lel_derived, insight_score DESC);
CREATE INDEX IF NOT EXISTS idx_kala_insights_type
    ON kala_insights (chart_id, insight_type);
CREATE INDEX IF NOT EXISTS idx_kala_insights_window
    ON kala_insights (chart_id, window_id);

COMMENT ON TABLE kala_insights IS
  'KALA_W2_FIELD_DESIGN_v1_0.md §6.4 (Lane D, ṢAḌ-DARŚANA W2 item E2): the 8-type '
  'insight catalog, manufactured deterministically -- never generative (B.10). '
  'Stage 6.5 (services/ka_kshetra/stage65_insights.py, this lane) writes the SEVEN '
  'non-LEL types with lel_derived=FALSE, hash-covered by the field snapshot. The '
  'eighth type, biographical_echo, is written exclusively by Lane E''s '
  'biographical-join refresh with lel_derived=TRUE and is NEVER produced by '
  'stages 0-8 (CIRCULARITY GUARD CARVE-OUT, §8.3 CG-1).';

COMMENT ON COLUMN kala_insights.lel_derived IS
  'FALSE for all seven types this lane (stage 6.5) writes -- hash-covered. TRUE '
  'only for biographical_echo rows written by Lane E''s stage-9-adjacent '
  'biographical-join refresh, which reads the LEL and is therefore excluded from '
  'the field hash (§7.4) so the Circularity Guard invariant (CG-1) holds.';
COMMENT ON COLUMN kala_insights.surprise_basis IS
  'Explains cohort_surprise''s provenance: e.g. "cohort_base_rate" when '
  'p_cohort was computable, or the specific fallback_reason (e.g. '
  '"cohort_below_minimum") when cohort_surprise was NOT surprise-credited and '
  'the 0.5 placeholder (§6.4) was used instead.';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS kala_insights;
--   DROP TABLE IF EXISTS kala_field_salience;
--   COMMIT;
-- =============================================================================
