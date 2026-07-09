-- Migration 427: panchanga_daily_reprovision
-- Created: 2026-07-09
--
-- R5.1 C3 (CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md) — Forward Panchanga.
-- "the ONE sanctioned new data surface — it is date-keyed reference, not chart data"
--
-- Re-provisions public.panchanga_daily as a REAL date-keyed table, replacing the
-- WHERE-FALSE compatibility view created by 365_w4_l4_schema_drift_fix.sql §5
-- (which always returned 0 rows — a deliberate graceful-empty placeholder, not
-- live data). This migration converts the placeholder into a real table backed
-- by a deterministic writer (platform/python-sidecar/scripts/panchanga_daily_writer.py)
-- that populates a rolling +12-month window using panchang_engine.compute_panchang()
-- (Swiss Ephemeris — pyswisseph), the SAME deterministic engine already used by
-- ka_muhurta_seva / muhurat.finder for engine-direct scoring.
--
-- Schema note — this migration is a SUPERSET of two pre-existing, drifted
-- consumer contracts so that NEITHER downstream reader needs a query change:
--   (a) platform/python-sidecar/brahmagyan/phala/outlook.py._fetch_auspicious_windows
--       expects: date, tithi (SMALLINT id — matches archived 060 schema exactly,
--       NOT a text name despite the column being reused as a friendly alias
--       elsewhere in this file's column list), vara/moon_nakshatra/yoga/karana
--       (TEXT names), auspicious, choghadiya, hora (JSONB).
--   (b) platform/python-sidecar/panchang_engine/panchang_daily_reader.py.fetch_panchanga_range
--       expects: date, tithi_id, nakshatra_id, vara_id, yoga_id, karana_id (SMALLINT ids),
--       sunrise_utc, sunset_utc, moon_phase, special_yogas, choghadiya, hora,
--       inauspicious, auspicious.
-- migration-guard review caught a real shape conflict: outlook.py's `auspicious`
-- handling was written against the archived table's expectation of a dict-shaped
-- JSONB value, but panchang_engine's canonical `auspicious` output (and (b)'s
-- contract) is list-shaped (list[Timing dict]). Rather than split the column
-- (which would reintroduce the "two independent derivations of the same fact"
-- anti-pattern this migration exists to avoid), outlook.py's consumer code was
-- patched to accept the list shape and fold it into the same dict output it already
-- returns to its own callers (see brahmagyan/phala/outlook.py — one-line change,
-- serving-plane, not a build writer). The column stays list-shaped, matching the
-- engine's one true serialization (serialize.py).
-- Both column families are populated by the same writer from one panchang_engine
-- compute_panchang() call per date — never two independent derivations of the
-- same fact (B.10 / B.3 discipline).
--
-- Location default: single-observer table, Bhubaneswar (native's location default;
-- see panchang_engine/panchang_daily_reader.py BHUBANESWAR_LAT/LON + the historical
-- single-observer note in the archived 060 migration). lat/lon/tz_offset_minutes are
-- carried per row for provenance/audit, not as part of the key — this table is NOT
-- multi-observer (that was flagged as future M7 scope in 060 and remains deferred).
--
-- Must-not-touch discipline: this table is reference/serving-plane data (date-keyed,
-- location-anchored), never chart data. No orchestrator writer, no ga_/bo_/ka_/ph_/mi_
-- asset_id is created here. Not registered in asset_registry (that registry is for
-- chart-scoped build assets only).

BEGIN;

-- ── §1 — drop the WHERE-FALSE compatibility view (re-run-safe relkind guard) ──
-- migration-guard review: a bare `DROP VIEW IF EXISTS` only succeeds while the
-- object is still a view. Once this migration has run once, panchanga_daily is
-- a TABLE, and a plain DROP VIEW would raise PG 42809 ("wrong object type") on
-- any re-run. Mirrors the relkind guard already established in
-- 365_w4_l4_schema_drift_fix.sql §3.
DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relname = 'panchanga_daily' AND n.nspname = 'public' AND c.relkind = 'v'
  ) THEN
    DROP VIEW public.panchanga_daily;
  END IF;
END $$;

-- ── §2 — create the real date-keyed table ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.panchanga_daily (
  -- Identity — one row per calendar date (single-observer: Bhubaneswar default)
  date                  DATE          NOT NULL PRIMARY KEY,
  lat                   NUMERIC(8,5)  NOT NULL DEFAULT 20.2700,
  lon                   NUMERIC(8,5)  NOT NULL DEFAULT 85.8400,
  tz_offset_minutes     INTEGER       NOT NULL DEFAULT 330,

  -- Sun / Moon timings
  sunrise_utc           TIMESTAMPTZ   NOT NULL,
  sunset_utc            TIMESTAMPTZ   NOT NULL,
  moonrise_utc          TIMESTAMPTZ,
  moonset_utc           TIMESTAMPTZ,

  -- ── Tithi ──────────────────────────────────────────────────────────────────
  tithi                 SMALLINT      NOT NULL,   -- legacy alias (outlook.py contract) = tithi_id
  tithi_id              SMALLINT      NOT NULL,   -- panchang_daily_reader.py contract
  tithi_name            TEXT          NOT NULL,
  tithi_end_utc         TIMESTAMPTZ,
  paksha                TEXT          NOT NULL,   -- 'shukla' | 'krishna'

  -- ── Vara ───────────────────────────────────────────────────────────────────
  vara                  TEXT          NOT NULL,   -- legacy alias (outlook.py contract) = vara_name
  vara_id               SMALLINT      NOT NULL,   -- panchang_daily_reader.py contract
  vara_lord             TEXT,

  -- ── Nakshatra (Moon, sidereal Lahiri, at sunrise) ─────────────────────────────
  moon_nakshatra        TEXT          NOT NULL,   -- legacy alias (outlook.py contract) = nakshatra_name
  nakshatra_id          SMALLINT      NOT NULL,   -- panchang_daily_reader.py contract
  moon_nakshatra_pada   SMALLINT,
  moon_longitude_deg    NUMERIC(12,8),
  sun_longitude_deg     NUMERIC(12,8),
  nakshatra_end_utc     TIMESTAMPTZ,

  -- ── Yoga ───────────────────────────────────────────────────────────────────
  yoga                  TEXT          NOT NULL,   -- legacy alias (outlook.py contract) = yoga_name
  yoga_id               SMALLINT      NOT NULL,   -- panchang_daily_reader.py contract
  yoga_end_utc          TIMESTAMPTZ,

  -- ── Karana (both karanas of the tithi) ────────────────────────────────────────
  karana                TEXT          NOT NULL,   -- legacy alias (outlook.py contract) = karana_first name
  karana_id             SMALLINT      NOT NULL,   -- panchang_daily_reader.py contract (first karana id)
  karana_second_id      SMALLINT,
  karana_end_utc        TIMESTAMPTZ,

  -- ── Moon phase ─────────────────────────────────────────────────────────────
  moon_phase            NUMERIC(6,3),             -- illumination % [0,100]

  -- ── Enrichment JSONB (both readers use these directly) ────────────────────────
  special_yogas         JSONB         NOT NULL DEFAULT '[]'::JSONB,
  choghadiya             JSONB         NOT NULL DEFAULT '{}'::JSONB,
  hora                  JSONB         NOT NULL DEFAULT '[]'::JSONB,   -- 24 planetary hours (day+night)
  inauspicious           JSONB         NOT NULL DEFAULT '[]'::JSONB,   -- rahu_kalam/yamagandam/gulika_kalam/dur_muhurta
  auspicious             JSONB         NOT NULL DEFAULT '[]'::JSONB,   -- abhijit/brahma_muhurta/amrit_kalam/varjyam
  planets                JSONB,                                        -- 9 grahas sidereal at sunrise

  -- ── Provenance (B.3 / B.10) ────────────────────────────────────────────────
  ayanamsha_id           TEXT          NOT NULL DEFAULT 'lahiri',
  computation_version     TEXT          NOT NULL,  -- panchang_engine.__version__
  ephemeris_version       TEXT          NOT NULL,  -- pyswisseph version string
  source_citation         TEXT          NOT NULL DEFAULT
    'panchang_engine.compute_panchang (Swiss Ephemeris / pyswisseph, sidereal Lahiri) — '
    'BPHS + classical Muhurta Shastra (Muhurta Chintamani / Brihat Samhita) hora + choghadiya tables',
  computed_at             TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_panchanga_daily_date        ON public.panchanga_daily (date);
CREATE INDEX IF NOT EXISTS idx_panchanga_daily_tithi_id    ON public.panchanga_daily (tithi_id);
CREATE INDEX IF NOT EXISTS idx_panchanga_daily_nakshatra_id ON public.panchanga_daily (nakshatra_id);
CREATE INDEX IF NOT EXISTS idx_panchanga_daily_vara_id     ON public.panchanga_daily (vara_id);
CREATE INDEX IF NOT EXISTS idx_panchanga_daily_yoga_id     ON public.panchanga_daily (yoga_id);
CREATE INDEX IF NOT EXISTS idx_panchanga_daily_auspicious  ON public.panchanga_daily USING GIN (auspicious);
CREATE INDEX IF NOT EXISTS idx_panchanga_daily_special_yogas ON public.panchanga_daily USING GIN (special_yogas);

COMMENT ON TABLE public.panchanga_daily IS
    'R5.1 C3 — real date-keyed forward panchanga (tithi/vara/nakshatra/yoga/karana + hora + '
    'choghadiya + auspicious/inauspicious windows), single-observer Bhubaneswar (native location '
    'default), rolling +12-month window populated by scripts/panchanga_daily_writer.py '
    '(monthly refresh — see infra/scheduler/panchanga_refresh.tf or the operator runbook if not '
    'yet applied). Superset schema serves both outlook.py (name columns) and '
    'panchang_daily_reader.py (id columns) without either consumer needing a code change. '
    'Replaces the WHERE-FALSE stub view from 365_w4_l4_schema_drift_fix.sql §5. '
    'Empty-with-reason applies outside the populated window — never fabricate rows for '
    'out-of-window dates.';

COMMIT;
