-- Migration 479: kala_field_provenance — the item-11 provenance edges
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · Wave W2 · Lane C. Spec: KALA_W2_FIELD_DESIGN_v1_0.md
-- §5.4 (schema + THE RECONCILIATION INVARIANT), §8.2 (item 44 authority basis),
-- §9.3 row 479.
--
-- ── THE GRAIN: one row per (target × term) ───────────────────────────────────
-- A "term" is ONE multiplicative factor of the §5.1 hazard formula
--       λ_e(t) = λ⁰_e · P̃_e · C_e(t) · M_e(t) · S_e(t)
-- evaluated at the target's peak. Rows are persisted AT FIELD-WRITE TIME, inside
-- the SAME substep transaction as the row they explain — never backfilled. A
-- backfilled provenance edge is an explanation of a value that has already been
-- served unexplained, which is the failure mode this table exists to remove.
--
-- ── THE RECONCILIATION INVARIANT (the §N.7/§N.8 detector) ────────────────────
-- For every `window` target:
--     | ln(lambda_peak) − Σ log_contribution over that window's rows |  ≤ 1e-9
-- The `baseline` and `promise` rows carry ln λ⁰_e and ln P̃_e respectively, so
-- the sum is COMPLETE BY CONSTRUCTION. This is asserted in the writer (halting
-- the substep with `provenance_reconciliation_failed`) AND in CI over both
-- canonical charts.
--
-- WHY THIS IS THE WHOLE POINT (§5.4, verbatim): "A provenance row set that does
-- not reconstruct the value it explains is not weak evidence — it is no
-- evidence, and the build fails." A provenance table that is merely DECORATIVE
-- — rows that look like reasons but were never checked against the number they
-- claim to explain — is precisely the Earned-Signal defect class of CLAUDE.md
-- §N.8: a signal whose detector measures a proxy (rows exist) rather than the
-- claim (the rows reconstruct the value). The invariant above is the detector
-- with the power to fail, and the code path that makes it correctly read false
-- is any term added to λ without a matching edge, or any edge whose stored
-- term_value drifts from what the hazard evaluator actually multiplied in.
--
-- ── THE CITATION JOIN (§N.5 / B.3) ──────────────────────────────────────────
-- `source_fact_id` resolves back to chart_facts.fact_id (or an L2 signal id). CI
-- asserts 100% resolution: a dangling source_fact_id FAILS the build. An L2+
-- claim never restates an L1 computed value as its own truth — it REFERENCES the
-- fact and inherits the value.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS kala_field_provenance (
  id                 BIGSERIAL PRIMARY KEY,
  chart_id           UUID NOT NULL,
  field_snapshot_id  TEXT NOT NULL,
  target_kind        TEXT NOT NULL CHECK (target_kind IN ('window','segment','insight')),
  target_id          TEXT NOT NULL,   -- window_id | '<event_class>#<segment_index>' | insight_id
  term_role          TEXT NOT NULL CHECK (term_role IN
                       ('baseline','promise','route','clock','modifier','suppression','gate')),
  term_key           TEXT NOT NULL,   -- 'baseline' | 'promise' | 'route:rank2'
                                      -- | 'clock:vimshottari:AD:Ke'
                                      -- | 'modifier:x4_av_kaksha_gate'
                                      -- | 'suppression:vedha:Sa->10'
                                      -- | 'gate:legacy_sweep_xref'
  term_value         DOUBLE PRECISION NOT NULL,  -- the factor's VALUE at t_peak (a_s^{w_s}, exp(β_j x_j), …)
  log_contribution   DOUBLE PRECISION NOT NULL,  -- ln(term_value)
  weight_id          TEXT,                       -- 'w_s:vimshottari' | 'beta:x4' | 'rho:vedha' | NULL
  weight_value       DOUBLE PRECISION,
  weights_version    TEXT NOT NULL,
  source_kind        TEXT NOT NULL CHECK (source_kind IN
                       ('l0_reference','l1_fact','l2_signal','l3_row','derived')),
  source_table       TEXT,
  source_pk          TEXT,
  source_fact_id     TEXT,
  authority_basis    TEXT NOT NULL,   -- the window_id this edge's target inherits (item 44)
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT kala_field_provenance_positive_term_ck CHECK (term_value > 0),
  CONSTRAINT kala_field_provenance_natural_key
    UNIQUE (chart_id, field_snapshot_id, target_kind, target_id, term_key)
);

CREATE INDEX IF NOT EXISTS idx_kfp_target
  ON kala_field_provenance (chart_id, target_kind, target_id);
CREATE INDEX IF NOT EXISTS idx_kfp_fact
  ON kala_field_provenance (source_fact_id);
CREATE INDEX IF NOT EXISTS idx_kfp_authority
  ON kala_field_provenance (authority_basis);

COMMENT ON TABLE kala_field_provenance IS
  'ṢAḌ-DARŚANA W2 item 11 / §5.4. One row per (target × multiplicative term of '
  'the §5.1 hazard), evaluated at the target''s peak, written inside the SAME '
  'substep transaction as the row it explains. THE RECONCILIATION INVARIANT: '
  'for every window target, |ln(lambda_peak) − Σ log_contribution| ≤ 1e-9, '
  'asserted in the writer AND in CI. A row set that does not reconstruct the '
  'value it explains is not weak evidence — it is NO evidence, and the build '
  'fails (CLAUDE.md §N.8 Earned-Signal).';

COMMENT ON COLUMN kala_field_provenance.term_value IS
  'CHECK (term_value > 0) is not decoration: every factor of the §5.1 product is '
  'strictly positive by construction — λ⁰ > 0, P̃ ≥ P_floor = 0.05, a_s > 0 so '
  'a_s^{w_s} > 0, exp(βx) > 0, and (1 − ρ·u) ≥ 0.05 because ρ ≤ 0.95. A '
  'non-positive term_value means the hazard model has been broken somewhere '
  'upstream, and ln(term_value) would not exist. Fail at write time.';

COMMENT ON COLUMN kala_field_provenance.authority_basis IS
  'item 44 / SINGLE TEMPORAL AUTHORITY rail: the kala_field_windows.window_id '
  'this edge''s target inherits. Every temporal claim product-wide cites a field '
  'window-id through this value. W2 REPORTS the census scoreboard; W6 GATES it.';

COMMENT ON COLUMN kala_field_provenance.source_fact_id IS
  '§N.5 / B.3: resolves to chart_facts.fact_id or an L2 signal id. CI asserts '
  '100% resolution — a dangling id fails the build. An L2+ derivation REFERENCES '
  'an L1 value and inherits it; it never restates it as its own truth.';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS kala_field_provenance;
--   COMMIT;
-- =============================================================================
