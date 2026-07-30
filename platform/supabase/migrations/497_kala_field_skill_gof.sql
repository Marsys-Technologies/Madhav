-- migration 497: kala_field_skill + kala_field_gof + the mi_bhara asset_registry row
--                (ṢAḌ-DARŚANA W2, Lane E, stage 9 — registry items 21/39, E1's D3 fit)
-- =============================================================================
-- Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.3 (the two tables, verbatim), §7.5 (weights
--        versioning + the acyclicity rule), §9.2 (the `mi_bhara` seed row), §9.3 (the
--        migration table, which reserves 483 for this family).
--
-- ── WHAT STAGE 9 IS, AND WHY IT IS THE ONLY STAGE THAT MAY SEE THE LEL ───────────────
-- Design §2: "Stages 0–8 are pure functions of (chart, corpus_pin, config_pin,
-- weights_version). Stage 9 is the only state that grows, and it is the only stage that
-- may see the LEL." These two tables are stage 9's published output:
--
--   kala_field_skill — the temporal SKILL SCORE: a log-likelihood-ratio, in nats per
--     event, of the fitted hazard against the chart's OWN circular-shifted null (§5.5).
--     SS = 0 is exactly the null hypothesis "this field carries no temporal information."
--     `skill_state` is three-valued on purpose: `established` / `not_established` /
--     `underpowered`. We publish the number in ALL THREE states — `not_established` is a
--     legitimate, shippable, honest result (§7.3; CLAUDE.md §N.8 Earned-Signal: a PASS
--     needs a detector with the power to fail, and this one has it).
--
--   kala_field_gof — the TIME-RESCALING goodness-of-fit test. By the time-rescaling
--     theorem, τ_k = Λ(t_{k−1}, t_k) are i.i.d. Exp(1) and z_k = 1 − exp(−τ_k) are
--     i.i.d. U(0,1) iff the intensity is correct. Two statistics, both required: a
--     one-sample Kolmogorov–Smirnov test of {z_k} against U(0,1), and a Ljung–Box test
--     on {z_k} at lags 1..5 (dependence in the rescaled times means a missing
--     clustering/refractory term, which KS alone cannot see). `n < 8` is reported as
--     `underpowered`, NEVER as a pass.
--
-- ── THE ACYCLICITY RULE THIS MIGRATION IS PART OF (§7.5) ─────────────────────────────
-- `mi_bhara.depends_on = ['ka_kshetra']`, and `ka_kshetra.depends_on` MUST NOT contain
-- `mi_bhara` — that edge would form the cycle ka_kshetra → mi_bhara → ka_kshetra and
-- `resolveBuildPlan`'s topoSort would reject EVERY plan containing them, breaking every
-- future chart build. The calibration loop closes by VERSION PIN, not by DAG edge:
-- weights v0 is seeded by migration (476, Lane C's keystone — deliberately NOT duplicated
-- here); `ka_kshetra` READS the newest active version (a data dependency); `mi_bhara`
-- INSERTs a new version row; the NEXT `ka_kshetra` rebuild pins the newer version. The
-- loop closes ACROSS builds while the DAG stays acyclic WITHIN every build.
--
-- ── SCOPE NOTE on §9.3's row for 483 ─────────────────────────────────────────────────
-- §9.3 groups the `ka_kshetra` / `mi_bhara` / `mi_sankalpa` asset_registry rows into this
-- migration. Only `mi_bhara`'s lands here, deliberately:
--   • `ka_kshetra` is Lane C's asset (§0 lane table) and its seed row lands in Lane C's
--     PR, per brief §2.5.1 ("seed row in the same PR as the writer"). Writing it from
--     here would be Lane E declaring another lane's DAG edges.
--   • `mi_sankalpa` is a **W4** asset (brief §1 item 42) with no writer yet. A seed row
--     for a non-existent writer would be a row Nirmāṇa can never build — an unearned
--     catalog entry (§N.8). It lands with its writer at W4.
-- Both are recorded here rather than silently dropped.
--
-- Idempotency (§N.3, L1+ = per-chart delete-then-insert): the mi_bhara writer deletes
-- WHERE chart_id = %s AND weights_version = %s AND field_snapshot_id = %s before
-- inserting. The UNIQUE indexes below are the natural keys.
-- =============================================================================

BEGIN;

-- ── §1 — kala_field_skill ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS kala_field_skill (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chart_id           UUID        NOT NULL,
    -- NULL row = the chart-level, event-weighted aggregate (§7.3:
    -- SS = Σ_e n_e·SS_e / Σ_e n_e). Non-NULL = one event class.
    event_class        TEXT,
    weights_version    TEXT        NOT NULL,
    field_snapshot_id  TEXT        NOT NULL,

    n_events           INTEGER     NOT NULL CHECK (n_events      >= 0),
    -- The prospective/backfill split (Elevation §7): prospective resolutions are
    -- predictions filed BEFORE their outcome and are ALWAYS out-of-sample. They are
    -- reported SEPARATELY from retrodiction and are NEVER summed with it.
    n_prospective      INTEGER     NOT NULL DEFAULT 0 CHECK (n_prospective >= 0),
    n_backfill         INTEGER     NOT NULL DEFAULT 0 CHECK (n_backfill    >= 0),

    skill_score        DOUBLE PRECISION NOT NULL,   -- SS_e, nats per event
    skill_lo           DOUBLE PRECISION NOT NULL,   -- 95% percentile-bootstrap lower bound
    skill_hi           DOUBLE PRECISION NOT NULL,
    skill_state        TEXT        NOT NULL
                         CHECK (skill_state IN ('established','not_established','underpowered')),
    -- The SEPARATE prospective-only score. NULL when no prospective resolutions exist —
    -- an honest null, never 0.0 (which would read as "measured, and it is zero").
    skill_prospective  DOUBLE PRECISION,
    null_replicates    INTEGER     NOT NULL CHECK (null_replicates >= 0),
    bootstrap_resamples INTEGER    NOT NULL DEFAULT 0 CHECK (bootstrap_resamples >= 0),
    -- The deterministic bootstrap seed actually used, so a rerun is reproducible by
    -- inspection rather than by re-deriving the hash (§7.3).
    bootstrap_seed     BIGINT,
    released_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT kala_field_skill_interval_ck CHECK (skill_lo <= skill_hi),
    -- Earned-Signal (§N.8): the three states are not free-text moods, they are the exact
    -- §7.3 predicate. `underpowered` iff n < 8; `established` iff the bootstrap lower
    -- bound clears zero. A row that claims `established` on 3 events is rejected by the DB.
    CONSTRAINT kala_field_skill_state_ck CHECK (
        (skill_state = 'underpowered'     AND n_events <  8)
     OR (skill_state = 'established'      AND n_events >= 8 AND skill_lo >  0)
     OR (skill_state = 'not_established'  AND n_events >= 8 AND skill_lo <= 0)
    )
);

-- COALESCE(...) in the key because event_class IS NULL marks the chart-level aggregate and
-- NULLs do not collide in a plain UNIQUE constraint (two aggregate rows could then exist).
CREATE UNIQUE INDEX IF NOT EXISTS uq_kala_field_skill
    ON kala_field_skill (chart_id, COALESCE(event_class, ''), weights_version, field_snapshot_id);
CREATE INDEX IF NOT EXISTS idx_kala_field_skill_chart
    ON kala_field_skill (chart_id, released_at DESC);

COMMENT ON TABLE kala_field_skill IS
  'ṢAḌ-DARŚANA W2 stage 9 (Lane E) — the published temporal SKILL SCORE: a '
  'log-likelihood-ratio, in nats per event, of the fitted hazard against the chart''s own '
  'circular-shifted null (KALA_W2_FIELD_DESIGN_v1_0.md §7.3). SS = 0 is exactly the null '
  'hypothesis "this field carries no temporal information". Published in all three '
  'skill_states — `not_established` is a legitimate, shippable, honest result.';
COMMENT ON COLUMN kala_field_skill.event_class IS
  'NULL = the chart-level event-weighted aggregate. Non-NULL = one event class.';
COMMENT ON COLUMN kala_field_skill.skill_prospective IS
  'The SEPARATE prospective-only score (predictions filed before their outcome). NULL when '
  'there are none — an honest null, never 0.0. Prospective and backfill are never summed.';

-- ── §2 — kala_field_gof ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS kala_field_gof (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chart_id           UUID        NOT NULL,
    event_class        TEXT,                        -- NULL = chart-level pooled
    weights_version    TEXT        NOT NULL,
    field_snapshot_id  TEXT        NOT NULL,

    n                  INTEGER     NOT NULL CHECK (n >= 0),
    ks_statistic       DOUBLE PRECISION,            -- D_n = sup_z |F_n(z) − z|
    ks_p               DOUBLE PRECISION CHECK (ks_p IS NULL OR (ks_p >= 0 AND ks_p <= 1)),
    ljung_box_p        DOUBLE PRECISION CHECK (ljung_box_p IS NULL OR (ljung_box_p >= 0 AND ljung_box_p <= 1)),
    ljung_box_stat     DOUBLE PRECISION,
    ljung_box_lags     INTEGER     NOT NULL DEFAULT 0 CHECK (ljung_box_lags >= 0),
    gof_state          TEXT        NOT NULL CHECK (gof_state IN ('pass','fail','underpowered')),
    -- Named exactly when gof_state='fail', so a failure always says WHICH statistic failed.
    failing_statistic  TEXT        CHECK (failing_statistic IS NULL
                                          OR failing_statistic IN ('ks','ljung_box','ks+ljung_box')),
    -- the z_k themselves, so the KS plot is reproducible by the portal without a refit
    rescaled_z         DOUBLE PRECISION[] NOT NULL DEFAULT '{}',
    -- ±1.36/√n — emitted as DATA, never as prose about it (§7.3)
    ks_band_95         DOUBLE PRECISION,
    computed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Earned-Signal (§N.8): n < 8 can never be a pass, and a `fail` must name its
    -- failing statistic. Both halves are DB-enforced, not merely conventional.
    CONSTRAINT kala_field_gof_state_ck CHECK (
        (gof_state = 'underpowered' AND n <  8 AND failing_statistic IS NULL)
     -- The IS NOT NULL clauses are load-bearing, not belt-and-braces: a Postgres CHECK
     -- passes unless it evaluates to FALSE, so `ks_p >= 0.05` alone would silently admit
     -- a `pass` row with a NULL p-value — a PASS with no detector behind it (§N.8).
     OR (gof_state = 'pass'         AND n >= 8 AND failing_statistic IS NULL
                                    AND ks_p IS NOT NULL        AND ks_p        >= 0.05
                                    AND ljung_box_p IS NOT NULL AND ljung_box_p >= 0.05)
     OR (gof_state = 'fail'         AND n >= 8 AND failing_statistic IS NOT NULL)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_kala_field_gof
    ON kala_field_gof (chart_id, COALESCE(event_class, ''), weights_version, field_snapshot_id);
CREATE INDEX IF NOT EXISTS idx_kala_field_gof_chart
    ON kala_field_gof (chart_id, computed_at DESC);

COMMENT ON TABLE kala_field_gof IS
  'ṢAḌ-DARŚANA W2 stage 9 (Lane E) — the time-rescaling goodness-of-fit test '
  '(KALA_W2_FIELD_DESIGN_v1_0.md §7.3). τ_k = Λ(t_{k−1}, t_k) are i.i.d. Exp(1) and '
  'z_k = 1 − exp(−τ_k) i.i.d. U(0,1) iff the intensity is correct; tested by one-sample '
  'KS against U(0,1) AND Ljung–Box on {z_k} at lags 1..5. n < 8 is `underpowered`, never '
  'a pass (CLAUDE.md §N.8 — a PASS needs a detector with the power to fail).';
COMMENT ON COLUMN kala_field_gof.rescaled_z IS
  'The z_k = 1 − exp(−τ_k) in event order — stored so the KS plot is reproducible by the '
  'renderer without re-running the fit.';

-- ── §3 — the mi_bhara asset_registry row (brief §2.5.1, design §9.2) ─────────────────
-- depends_on = ['ka_kshetra'] ONLY. NEVER add an edge back from ka_kshetra to mi_bhara
-- (§7.5 — that cycle breaks every chart build). `has_substeps` is false: the fit is one
-- unit of work (≤ ~25 parameters, one L-BFGS-B run per class), so a substep plan would be
-- ceremony without isolation value.
INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, expected_volume_formula, expected_volume_inputs, volume_explanation,
    depends_on, scope, is_active, has_writer,
    layer_name, layer_index, catalog_status, asset_kind
) VALUES (
    'mi_bhara', 'mimamsa', 13,
    'Kāla Bhāra', 'Field Weight Calibration',
    'Stage 9 of the temporal-field pipeline: fits the hazard field''s weights against '
    'this chart''s recorded life events (blocked forward-chaining CV, shrinkage to the '
    'classical structural priors), publishes a new versioned weights artifact, and '
    'reports the temporal skill score and the time-rescaling goodness-of-fit. The ONLY '
    'stage permitted to read the LEL (CIRCULARITY GUARD). ṢAḌ-DARŚANA items 21/39.',
    'postgres_table', 'kala_field_weight_versions',
    'SELECT COUNT(*) FROM kala_field_skill WHERE chart_id = $1',
    'SELECT pg_total_relation_size(''kala_field_skill'')',
    -- target_floor stays NULL: §N.4 "floors are aspirational, not gates" — it is set to
    -- the ACHIEVED count after the first real build, never fabricated ahead of one.
    NULL, NULL, NULL,
    'One skill row per scored event class plus one chart-level aggregate; grows only as '
    'the LEL grows. A chart with no LEL correctly produces the structural-prior state '
    'with skill_state = underpowered — an honest zero, not an error.',
    ARRAY['ka_kshetra']::text[], 'per_chart', true, true,
    'Mīmāṃsā', 'L5', 'DRAFT', 'data'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql             = EXCLUDED.count_sql,
    target_table          = EXCLUDED.target_table,
    has_writer            = EXCLUDED.has_writer,
    depends_on            = EXCLUDED.depends_on,
    english_description   = EXCLUDED.english_description,
    volume_explanation    = EXCLUDED.volume_explanation;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback — migrate.ts is forward-apply-only; run this by hand):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'mi_bhara';
--   DROP TABLE IF EXISTS kala_field_gof;
--   DROP TABLE IF EXISTS kala_field_skill;
--   COMMIT;
-- =============================================================================
