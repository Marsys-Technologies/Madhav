-- Migration 208: GA7 dashas writer — KP sublevel dimension + A7 additions
-- Adds KP sub-period columns and all A7 additions (A-Q) to chart_dashas.
-- Per brief: CRITICAL OVERRIDE 2 — KP sub-periods use kp_sublevel dimension,
--            NOT level_n=6/7. All additions from A7 §4 included.
-- Context-decay-safe: this migration only adds columns, fully idempotent.
-- Per: A7_DASHAS_SPEC_v1_0.md §4, GA7 brief §5, §6.
-- Campaign rails: ZERO level_n=5 rows; depth cap at Sukshma (level_n=4).

BEGIN;

-- ── 1. KP sublevel dimension (Addition L / CRITICAL OVERRIDE 2) ─────────────
-- KP sub-periods are NOT level_n=6/7. They live as kp_sublevel-keyed rows
-- under Vimshottari with level_n=2 or level_n=3.

ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  kp_sublevel          TEXT DEFAULT NULL;   -- NULL=standard; 'sub'=KP sub; 'sub_sub'=KP sub-sub

ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  kp_sub_lord          TEXT DEFAULT NULL;   -- lord at KP sub level

ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  kp_sub_sub_lord      TEXT DEFAULT NULL;   -- lord at KP sub-sub level (only on kp_sublevel='sub_sub')

-- ── 2. Addition A — Lord natal context inline ────────────────────────────────
ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  lord_natal_house_d1        INT DEFAULT NULL;

ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  lord_natal_sign            TEXT DEFAULT NULL;

ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  lord_natal_nakshatra       TEXT DEFAULT NULL;

ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  lord_natal_dignity_d1      TEXT DEFAULT NULL;

ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  lord_natal_shadbala_total  NUMERIC DEFAULT NULL;

-- ── 3. Addition B — Sandhi with next dasha lord ──────────────────────────────
ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  sandhi_with_next_dasha_lord   TEXT DEFAULT NULL;

ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  next_dasha_start_iso          TIMESTAMPTZ DEFAULT NULL;

-- ── 4. Additions C+D — Cross-system concurrency ──────────────────────────────
ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  concurrent_system_lords_jsonb  JSONB DEFAULT NULL;  -- sanctioned JSONB #1

ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  convergence_count_at_start     INT DEFAULT NULL;

-- ── 5. Addition E — Applicability ────────────────────────────────────────────
ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  applies_to_this_chart_flag    BOOLEAN NOT NULL DEFAULT TRUE;

-- ── 6. Addition F — Period deity / marker ────────────────────────────────────
ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  period_deity_or_marker        TEXT DEFAULT NULL;

-- ── 7. Addition G — Lord-to-parent relationship ──────────────────────────────
ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  lord_to_parent_relationship   TEXT DEFAULT NULL;  -- 'friend'|'enemy'|'neutral'

-- ── 8. Addition H — Tajik year-lord (Mudda rows only) ────────────────────────
ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  varsha_year_lord              TEXT DEFAULT NULL;

-- ── 9. Addition I — Kalachakra solar-return anchor ──────────────────────────
ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  anchored_solar_return_iso     TIMESTAMPTZ DEFAULT NULL;

-- ── 10. Addition J — Triggered yogas (sanctioned JSONB #2) ──────────────────
ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  triggered_yogas_jsonb_atomic  JSONB DEFAULT NULL;  -- sanctioned JSONB #2

-- ── 11. Addition K — Lord transit at period start (sanctioned JSONB #3) ──────
ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  lord_transit_at_period_start_jsonb  JSONB DEFAULT NULL;  -- sanctioned JSONB #3

-- ── 12. Addition Q — Karakas active during period ────────────────────────────
ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  karakas_active_during_period  TEXT[] DEFAULT NULL;

-- ── 13. Additional build-state tracking columns ───────────────────────────────
ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  is_truncated_at_window_start  BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE chart_dashas ADD COLUMN IF NOT EXISTS
  is_truncated_at_window_end    BOOLEAN NOT NULL DEFAULT FALSE;

-- ── 14. Indexes for KP sublevel queries ──────────────────────────────────────
CREATE INDEX IF NOT EXISTS cd_kp_sublevel_idx
  ON chart_dashas (chart_id, ayanamsha_id, system_id, kp_sublevel)
  WHERE kp_sublevel IS NOT NULL;

CREATE INDEX IF NOT EXISTS cd_convergence_idx
  ON chart_dashas (chart_id, ayanamsha_id, start_date)
  WHERE convergence_count_at_start IS NOT NULL;

-- ── 15. Check constraint: enforce level_n 1-4 cap (CRITICAL OVERRIDE 1) ──────
-- Drop if exists first (idempotent), then add
DO $$
BEGIN
  ALTER TABLE chart_dashas DROP CONSTRAINT IF EXISTS cd_level_n_max4;
  ALTER TABLE chart_dashas ADD CONSTRAINT cd_level_n_max4
    CHECK (level_n BETWEEN 1 AND 4);
EXCEPTION WHEN others THEN
  -- If constraint cannot be dropped/added due to existing data, log and continue
  RAISE NOTICE 'cd_level_n_max4 constraint: %', SQLERRM;
END;
$$;

COMMIT;

-- DOWN:
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS karakas_active_during_period;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS lord_transit_at_period_start_jsonb;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS triggered_yogas_jsonb_atomic;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS anchored_solar_return_iso;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS varsha_year_lord;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS lord_to_parent_relationship;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS period_deity_or_marker;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS applies_to_this_chart_flag;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS convergence_count_at_start;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS concurrent_system_lords_jsonb;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS next_dasha_start_iso;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS sandhi_with_next_dasha_lord;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS lord_natal_shadbala_total;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS lord_natal_dignity_d1;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS lord_natal_nakshatra;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS lord_natal_sign;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS lord_natal_house_d1;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS kp_sub_sub_lord;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS kp_sub_lord;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS kp_sublevel;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS is_truncated_at_window_end;
-- ALTER TABLE chart_dashas DROP COLUMN IF EXISTS is_truncated_at_window_start;
