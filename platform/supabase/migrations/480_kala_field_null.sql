-- Migration 480: kala_field_null + the `ka_kshetra` asset_registry seed row
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · Wave W2 · Lane C. Spec: KALA_W2_FIELD_DESIGN_v1_0.md
-- §5.5 (the circular-shift null), §9.1 (DAG edges), §9.2 (seed row), §9.3 row 480.
--
-- ── WHAT THE NULL IS, AND WHY IT IS NOT A TUNING KNOB (§5.5) ────────────────
-- The TRANSIT STREAM is circularly shifted; the NATAL STRUCTURE and the DAŚĀ
-- LADDER are held FIXED. Shifting the ladder would destroy the chart's identity;
-- shifting the natal points would destroy the chart. That asymmetry IS the null
-- hypothesis: "the sky's timing carries no information about this chart's events
-- beyond what the clocks already say."
--
-- Fully deterministic — NO RNG ANYWHERE. The shift grid is δ_r = r·(H/R) for
-- r = 1..R, computed, never drawn, because hash-replay must hold: two builds of
-- the same chart under the same pins must produce a bit-identical field, and a
-- seeded-RNG null would make that depend on library-internal PRNG behaviour.
--
-- `q_threshold` is the null's 95th-percentile RATE, and it is what DEFINES a
-- window (§5.2): a window is a maximal stretch where this chart's own hazard
-- exceeds what its own shifted sky would produce 95% of the time. Not a
-- threshold someone chose — a threshold the chart's own null computes.
--
-- `null_max_stats` stores M_r(L) for r = 1..R at ONE duration bucket L, so the
-- per-window permutation p-value
--     null_p = (1 + #{r : M_r(L*) ≥ Λ_obs}) / (R + 1)
-- is REPRODUCIBLE FROM THE STORED DATA, not merely asserted. The +1 correction is
-- the standard one, and `null_resolution = 1/(R+1)` is served alongside p so a
-- consumer can never mistake p = 0.0039 for p = 0 (LAW ZERO: never report a
-- precision the replicate count cannot support).
--
-- ── WHY THE ASSET_REGISTRY ROW IS HERE AND NOT IN 483 ───────────────────────
-- §9.3 tabulates the ka_kshetra/mi_bhara/mi_sankalpa registry rows under
-- migration 483 (Lane E). But §9.2 is binding on THIS lane's PR: "The
-- catalog-reconciliation CI check (every @register id ↔ seed row) must be GREEN
-- IN THE SAME PR" as the writer — and Lane C is the lane that writes
-- `@register('ka_kshetra')` (§0: "The orchestration shim ... is written ONCE by
-- Lane C"). A writer without a seed row is invisible to Nirmāṇa, so shipping the
-- shim without the row would land the wave gate red. The row is therefore seeded
-- HERE, with ON CONFLICT DO UPDATE, and migration 483 may re-assert the same
-- values idempotently — the two are consistent by construction because both
-- transcribe §9.2's table. 483 remains the home of the mi_bhara / mi_sankalpa
-- rows, which Lane C does not own and does not seed.
--
-- ── THE TWO DEPENDS_ON TRAPS, BOTH REAL, BOTH DELIBERATELY AVOIDED ──────────
-- (1) `bg_sky_calendar` is NOT listed. Brief §2.5.3 proposes it as a dependency,
--     but it is a W3 asset; §2.5.1 requires every edge to resolve to an EXISTING
--     asset_id and resolveBuildPlan's topoSort cannot resolve an edge to an id
--     with no seed row. W3 adds that edge IN THE SAME PR that lands
--     bg_sky_calendar's seed row — never before. (§9.1 EDGE-STAGING RULE: "A W2
--     lane that 'helpfully' pre-declares the edge breaks production.")
--     [Live note: 473_bg_sky_calendar.sql has since landed, so the edge would
--     now resolve — but the staging rule is a SEQUENCING contract owned by W3,
--     not a liveness test this lane may re-adjudicate. W2 declares eight edges.]
-- (2) `mi_bhara` is NOT listed. Combined with the necessary
--     mi_bhara.depends_on = ['ka_kshetra'], that edge forms the cycle
--     ka_kshetra → mi_bhara → ka_kshetra, which topoSort rejects — breaking
--     EVERY chart build, not just this wave's. The calibration loop closes by
--     VERSION PIN across builds instead (§7.5 / migration 476), never by a DAG
--     edge. A CI guard asserts both halves of this positively.
--
-- ── L0 GATING CONSEQUENCE (brief §2.5.2, correct behaviour not a defect) ────
-- `bg_cohort` is a bg_* GLOBAL asset built only via an explicit super-admin L0
-- trigger. A per-chart build whose bg_cohort upstream is dormant shows
-- ka_kshetra as BLOCKED ("L0 dependency not built — run the Brahmagyan layer
-- first"). The W2 gate therefore requires bg_cohort built in PRODUCTION before
-- the first per-chart ka_kshetra build.
--
-- ── target_floor ────────────────────────────────────────────────────────────
-- Seeded at 0. §N.4: floors are ASPIRATIONAL, NOT GATES — set target_floor to
-- the ACHIEVED count after the first real build; never fabricate rows to hit a
-- number, and never seed a number the build has not yet produced.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS kala_field_null (
  id                 BIGSERIAL PRIMARY KEY,
  chart_id           UUID NOT NULL,
  event_class        TEXT NOT NULL,
  replicates         INT  NOT NULL CHECK (replicates > 0),
  horizon_days       DOUBLE PRECISION NOT NULL CHECK (horizon_days > 0),
  q_threshold        DOUBLE PRECISION NOT NULL,          -- q_e: the null's 95th-percentile RATE
  bucket_days        INT  NOT NULL CHECK (bucket_days > 0),
  null_max_stats     DOUBLE PRECISION[] NOT NULL,        -- M_r(L) for r = 1..R, this bucket
  shift_grid_step    DOUBLE PRECISION NOT NULL,          -- H/R — the DETERMINISTIC grid, never drawn
  weights_version    TEXT NOT NULL,
  x_schema_version   TEXT NOT NULL,
  field_snapshot_id  TEXT NOT NULL,
  computed_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT kala_field_null_natural_key
    UNIQUE (chart_id, event_class, bucket_days, field_snapshot_id)
);

CREATE INDEX IF NOT EXISTS idx_kala_field_null_lookup
  ON kala_field_null (chart_id, event_class, bucket_days);

COMMENT ON TABLE kala_field_null IS
  'ṢAḌ-DARŚANA W2 item 23 / §5.5: the circular-shift null. The TRANSIT stream is '
  'shifted; the natal structure and the daśā ladder are held FIXED — that '
  'asymmetry IS the null hypothesis. Deterministic shift grid δ_r = r·(H/R), NO '
  'RNG anywhere, so hash-replay holds. null_max_stats stores every replicate''s '
  'sliding-window maximum of the integrated hazard at this duration bucket, so a '
  'served null_p is REPRODUCIBLE from the stored data rather than merely asserted.';

COMMENT ON COLUMN kala_field_null.q_threshold IS
  'q_e = the 0.95 quantile of {λ^{(r)}_e(t_g)} over all replicates r and all '
  '1-day grid points t_g. §5.2 defines a WINDOW as a maximal interval where '
  'λ_e(t) ≥ q_e — so windows are null-calibrated BY CONSTRUCTION. This is a '
  'definition, not a tuning knob.';

COMMENT ON COLUMN kala_field_null.null_max_stats IS
  'M_r(L) = max over t on a 1-day grid of Λ^{(r)}_e(t, t+L) — a matched filter '
  'at scale L. Stored per replicate so the permutation p-value '
  '(1 + #{r : M_r ≥ Λ_obs})/(R+1) can be RECOMPUTED and audited, not taken on '
  'trust.';

-- ── asset_registry seed row for `ka_kshetra` (§9.2, verbatim) ────────────────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status, asset_kind
) VALUES (
    'ka_kshetra',
    'kala',
    110,
    'Kāla Kṣetra',
    'Temporal Field',
    'ṢAḌ-DARŚANA W2: the ten-stage point-process temporal field. λ_e(t) as a '
    'strictly-positive hazard rate (events/day) composed multiplicatively from a '
    'classical baseline, a noisy-OR promise prior, per-daśā-system clock terms '
    '(proportional hazards), twelve log-linear covariates and multiplicative '
    'vighna thinning — stored as log-linear segments that integrate EXACTLY in '
    'closed form, with every factor persisted as a provenance edge that must '
    'reconstruct the value it explains. Windows are calibrated against the '
    'chart''s OWN circular-shifted sky (item 23). HEAVY writer. Built BESIDE the '
    'legacy ka_gochara_sweep (strangler-fig): reads it read-only as a cross-check '
    'corpus and writes ZERO rows to any legacy table.',
    'postgres_table', 'kala_field',
    'SELECT COUNT(*) FROM kala_field WHERE chart_id=$1',
    NULL,
    0, 'per_chart', true, true, true,
    1800,
    'Kāla', 'L3', 'CURRENT', 'data'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql               = EXCLUDED.count_sql,
    target_table            = EXCLUDED.target_table,
    has_writer              = EXCLUDED.has_writer,
    has_substeps            = EXCLUDED.has_substeps,
    writer_timeout_seconds  = EXCLUDED.writer_timeout_seconds,
    sort_order              = EXCLUDED.sort_order,
    scope                   = EXCLUDED.scope,
    is_active               = EXCLUDED.is_active,
    sanskrit_name           = EXCLUDED.sanskrit_name,
    english_name            = EXCLUDED.english_name,
    english_description     = EXCLUDED.english_description;

-- The EIGHT edges of §9.1 — and exactly those eight. See the header for why
-- 'bg_sky_calendar' (edge-staging rule) and 'mi_bhara' (acyclicity rule) are
-- deliberately absent.
UPDATE asset_registry SET depends_on = ARRAY[
    'ka_dasha_kala',          -- clocks / dasha eligibility (L3)
    'ka_gochara_sweep',       -- legacy sweep, read-only cross-check corpus (L3)
    'ka_gochara_resonance',   -- gochara_resonance_map targets (L3)
    'ga_panchanga',           -- panchanga limbs, referenced not recomputed (L1)
    'bo_pratijna',            -- promise (L2)
    'bo_sangati',             -- relational structure for the promise graph (L2)
    'bo_upaya',               -- intervention/suppression links (L2)
    'bg_cohort'               -- L0 global — rarity + specificity cohort
]::text[]
WHERE asset_id = 'ka_kshetra';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'ka_kshetra';
--   DROP TABLE IF EXISTS kala_field_null;
--   COMMIT;
-- =============================================================================
