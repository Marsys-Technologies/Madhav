-- Migration 474: kala_field_kinematics + kala_field_primitives — ṢAḌ-DARŚANA
-- W2 Lane A, Stage 0 (kinematics) + Stage 1 (symbolization).
-- =============================================================================
-- Spec: KALA_W2_FIELD_DESIGN_v1_0.md §3.1 (kala_field_kinematics), §3.2
-- (kala_field_primitives). Owned by Lane A per §0's anti-collision contract —
-- Lane A owns these two tables exclusively; no other lane writes to them.
--
-- Migration-range note (§9.3, corrected 2026-07-30): this campaign reserved
-- 474-483 in platform/supabase/migrations/ for W2's five lanes; 473 was the
-- confirmed live max at the time of that correction. Re-verified immediately
-- before writing this file (per the design doc's own standing instruction):
-- 474/475 are still free as of this PR.
--
-- Both tables are Lane A's OWN per-chart derived data, populated by the
-- pipeline stage modules (services/ka_kshetra/stage0_kinematics.py,
-- stage1_symbolization.py) once `ka_kshetra` (Lane C's registered asset, NOT
-- registered here per §9.2 — no asset_registry row lands in this migration)
-- invokes them. Idempotency (§N.3): per-chart delete-then-insert, scoped
-- ONCE in ka_kshetra.plan_substeps (Lane C); row-level upserts here (ON
-- CONFLICT DO UPDATE on the natural key) are the row-grain safety net for a
-- resumed/partial substep, not a substitute for that coarser delete.
-- =============================================================================

BEGIN;

-- ── kala_field_kinematics (§3.1) ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS kala_field_kinematics (
  id                BIGSERIAL PRIMARY KEY,
  chart_id          UUID        NOT NULL,
  event_kind        TEXT        NOT NULL
                      CHECK (event_kind IN (
                        'sign_ingress', 'nakshatra_ingress', 'station', 'syzygy',
                        'contact_in', 'contact_out', 'contact_peak',
                        'contact_core_in', 'contact_core_out'
                      )),
  body              TEXT        NOT NULL,
  target_kind       TEXT        CHECK (target_kind IS NULL OR target_kind IN (
                        'natal_graha', 'natal_lagna', 'natal_special_point'
                      )),
  target_ref        TEXT,
  t_days            DOUBLE PRECISION NOT NULL,
  event_ts          TIMESTAMPTZ NOT NULL,
  longitude_deg     NUMERIC(9,6),
  velocity_dps      NUMERIC(10,7),
  latitude_deg      NUMERIC(8,6),
  episode_id        TEXT,
  dwell_days        DOUBLE PRECISION,
  dwell_weight      DOUBLE PRECISION,
  orb_deg           NUMERIC(6,3),
  orb_source        TEXT,
  eclipse_candidate BOOLEAN     NOT NULL DEFAULT FALSE,
  gamma_proxy       NUMERIC(8,6),
  precision_regime  TEXT        NOT NULL DEFAULT 'day_grade'
                      CHECK (precision_regime IN ('day_grade', 'sub_day')),
  ayanamsha_id      TEXT        NOT NULL,
  source_table      TEXT        NOT NULL DEFAULT 'ephemeris_daily',
  computed_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_kala_field_kinematics ON kala_field_kinematics
  (chart_id, event_kind, body, COALESCE(target_ref, ''), t_days);
CREATE INDEX IF NOT EXISTS idx_kfk_chart_t ON kala_field_kinematics (chart_id, t_days);
CREATE INDEX IF NOT EXISTS idx_kfk_episode ON kala_field_kinematics (chart_id, episode_id)
  WHERE episode_id IS NOT NULL;

COMMENT ON TABLE kala_field_kinematics IS
  'SAD-DARSANA W2 Lane A Stage 0: exact position-model roots (Hermite spline over '
  'ephemeris_daily, Brent root-finding) for every "when exactly" kinematic event — '
  'sign/nakshatra ingress, station, syzygy, contact episodes with dwell-time/weight. '
  'precision_regime is day_grade for every W2 row; W2G (item 19) flips it. '
  'KALA_W2_FIELD_DESIGN_v1_0.md Sec3.1.';
COMMENT ON COLUMN kala_field_kinematics.dwell_weight IS
  'w_dwell = D / (D + D_nom) in (0,1) — replaces the "stations act with full force" '
  'special case; 0.5 at mean speed, -> 1 as the body stations inside the orb.';
COMMENT ON COLUMN kala_field_kinematics.orb_source IS
  'bg_transit_rules if a per-(body,target_class) orb was found there; '
  'default_3deg otherwise — served, never silently defaulted.';

-- ── kala_field_primitives (§3.2) ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS kala_field_primitives (
  id             BIGSERIAL PRIMARY KEY,
  chart_id       UUID NOT NULL,
  primitive_kind TEXT NOT NULL CHECK (primitive_kind IN (
                    'contact_moon_ref', 'contact_lagna_ref', 'moorti_at_ingress',
                    'vedha', 'latta', 'av_kaksha_gate', 'panchanga_limb',
                    'sandhi_band', 'station_band', 'syzygy_band'
                  )),
  subject        TEXT NOT NULL,
  object_ref     TEXT,
  t_start        DOUBLE PRECISION NOT NULL,
  t_end          DOUBLE PRECISION NOT NULL,
  envelope       JSONB NOT NULL,
  polarity       TEXT NOT NULL CHECK (polarity IN ('supportive', 'obstructive', 'neutral')),
  class_label    TEXT,
  source_kind    TEXT NOT NULL CHECK (source_kind IN (
                    'l0_reference', 'l1_fact', 'l2_signal', 'l3_row', 'derived'
                  )),
  source_table   TEXT,
  source_pk      TEXT,
  source_fact_id TEXT,
  kinematics_ids BIGINT[] NOT NULL DEFAULT '{}',
  computed_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_kala_field_primitives ON kala_field_primitives
  (chart_id, primitive_kind, subject, COALESCE(object_ref, ''), t_start);
CREATE INDEX IF NOT EXISTS idx_kfp_chart_kind ON kala_field_primitives (chart_id, primitive_kind);
CREATE INDEX IF NOT EXISTS idx_kfp_chart_span ON kala_field_primitives (chart_id, t_start, t_end);

COMMENT ON TABLE kala_field_primitives IS
  'SAD-DARSANA W2 Lane A Stage 1: classical primitives symbolized from stage-0 '
  'kinematics, each an interval with a piecewise-linear strength envelope (JSONB '
  'knot array, >=2 knots, v in [0,1]) so stage 4 can consume every primitive '
  'uniformly. panchanga_limb and (where grounded) av_kaksha_gate rows REFERENCE '
  'their L1/L3 source row rather than recomputing it (SS N.5). '
  'KALA_W2_FIELD_DESIGN_v1_0.md Sec3.2.';
COMMENT ON COLUMN kala_field_primitives.envelope IS
  'JSON array of >=2 {"t": <days since J2000>, "v": <0..1>} objects, t strictly '
  'ascending (a single coincident-t pair is allowed for a step-function jump). '
  'Linear between knots; 0 outside [t_start, t_end].';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS kala_field_primitives;
--   DROP TABLE IF EXISTS kala_field_kinematics;
--   COMMIT;
-- =============================================================================
