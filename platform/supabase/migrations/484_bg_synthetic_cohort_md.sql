-- Migration 484: bg_synthetic_cohort_md — age-based Vimśottarī MD-lord chain
-- for the synthetic reference cohort (ṢAḌ-DARŚANA campaign, ANTARYĀMIN ADJUDICATION-1)
-- =============================================================================
-- Context: KALA_W2_FIELD_DESIGN_v1_0.md §6.3 (corrected 2026-07-30, PR #918) authorizes
-- this NEW table on the ruling that resolved the missing "MD lord" matching key that
-- `bg_synthetic_cohort` (migration 472)'s own docstring flagged as out of scope
-- ("no dashas … no MD-lord — the other §12.3 matching key — since that needs the dasha
-- engine, out of scope here"). This migration creates ONLY the table; the ~100,000 rows
-- (10 per synthetic chart, 9 in the measure-zero boundary case) are computed and written
-- by the SAME writer that already builds bg_synthetic_cohort
-- (platform/python-sidecar/pipeline/orchestrator/writers/bg_cohort.py,
-- `compute_md_lord_chain()`) — a second pass of `asset_id='bg_cohort'`, NOT a new asset:
-- per §6.3, no new asset_registry row, no new depends_on edge. The chain derives PURELY
-- from the Moon `sidereal_longitude` already stored in bg_synthetic_cohort.positions —
-- no new ephemeris call, no swisseph, no PyJHora at build time.
--
-- Migration number: 473 was the confirmed live max as of the §6.3 correction (2026-07-30);
-- 474-483 are reserved by that same correction for the other W2 lanes' tables (Lane A-E,
-- see KALA_W2_FIELD_DESIGN_v1_0.md §0/§9). 484 is the next free number after that
-- reservation — re-verified against the live `platform/supabase/migrations/` directory
-- immediately before writing this file (origin/main HEAD was still edc757b2 / #918 at that
-- point, so no lane had yet claimed 474-483).
--
-- WHY AN AGE-INTERVAL CHAIN, NOT A SCALAR md_lord COLUMN (§6.3's own reasoning, recorded
-- here so a future migration does not "simplify" it back): the cohort's births span
-- 1900-2099, so roughly half are in the future relative to any fixed "today" — "the
-- current MD lord as of <date>" is undefined for a chart born in 2074 and goes stale for
-- every chart the moment the fixed date passes. Age is birth-relative and therefore
-- comparable across the entire 200-year sample, which is what the matching question
-- actually means: "how often does a chart with lagna X also sit in a Ketu mahādaśā at the
-- same life-stage the native is in."
--
-- THE ALGORITHM (verified against the shipped dasha engine's own constants — see
-- bg_cohort.py's compute_md_lord_chain() docstring for the full derivation):
--   platform/python-sidecar/pyjhora_adapter/dashas.py::_VIMSHOTTARI_YEARS (keyed by
--   PyJHora planet id via _names.py::PLANET_NAMES) = Sun 6, Moon 10, Mars 7, Mercury 17,
--   Jupiter 16, Venus 20, Saturn 19, Rahu 18, Ketu 7 (Σ=120y); nakshatra-lord cycle from
--   _names.py::_NAK_LORD_CYCLE = [Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn,
--   Mercury]. Row 1 is the birth MD's remaining balance (partial unless the Moon sits
--   exactly on a nakshatra boundary); rows 2-9 are the next eight lords at their full
--   classical length; row 10 (present unless the balance was exactly zero) restarts the
--   cycle to close the cover at exactly age 120 — the same thing that actually happens in
--   life for any chart whose birth MD balance consumed part of the first cycle.
--
-- Idempotency (§N.3 — L0 = global reference, safe to upsert): ON CONFLICT
-- (synthetic_id, md_index) DO NOTHING in the writer — the chain is a pure function of the
-- already-stored Moon longitude, so a rebuild recomputes byte-identical rows.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS bg_synthetic_cohort_md (
    id               BIGINT   GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    synthetic_id     INTEGER  NOT NULL
                       REFERENCES bg_synthetic_cohort (synthetic_id) ON DELETE CASCADE,
    md_index         SMALLINT NOT NULL CHECK (md_index BETWEEN 1 AND 10),
    md_lord          TEXT     NOT NULL CHECK (md_lord IN
                       ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu')),
    start_age_years  NUMERIC(9,6) NOT NULL CHECK (start_age_years >= 0),
    end_age_years    NUMERIC(9,6) NOT NULL,
    md_full_years    SMALLINT NOT NULL,      -- canonical Vimshottari length of md_lord
    is_partial       BOOLEAN  NOT NULL,      -- TRUE iff interval length < md_full_years
    chain_version    TEXT     NOT NULL,      -- 'vim_md_age_v1'
    computed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT bg_synthetic_cohort_md_uk UNIQUE (synthetic_id, md_index),
    CONSTRAINT bg_synthetic_cohort_md_interval_ck CHECK (end_age_years > start_age_years),
    CONSTRAINT bg_synthetic_cohort_md_span_ck     CHECK (end_age_years <= 120.000001)
);

CREATE INDEX IF NOT EXISTS idx_bgsc_md_lord_age
    ON bg_synthetic_cohort_md (md_lord, start_age_years, end_age_years);
CREATE INDEX IF NOT EXISTS idx_bgsc_md_synthetic ON bg_synthetic_cohort_md (synthetic_id);

COMMENT ON TABLE bg_synthetic_cohort_md IS
  'KALA_W2_FIELD_DESIGN_v1_0.md §6.3 (ANTARYAMIN ADJUDICATION-1): age-based Vimshottari '
  'mahadasha-lord CHAIN for the synthetic reference cohort (bg_synthetic_cohort), one '
  'row per (synthetic_id, md_index) spanning ages [0,120) years. Populated by a second '
  'pass of the SAME writer as bg_synthetic_cohort (pipeline/orchestrator/writers/'
  'bg_cohort.py, compute_md_lord_chain()) — not a new asset; no asset_registry row, no '
  'depends_on edge. Derived purely from the already-stored Moon sidereal_longitude '
  '(bg_synthetic_cohort.positions) — no new ephemeris call.';

COMMENT ON COLUMN bg_synthetic_cohort_md.md_index IS
  '1..10 chain position (1 = birth MD balance; 2-9 = next eight full-length lords; '
  '10 = the cycle restarting to close the cover at age 120, present unless the birth '
  'balance was exactly a full period).';
COMMENT ON COLUMN bg_synthetic_cohort_md.start_age_years IS
  'Native age in years (birth-relative, not calendar-relative) at which this MD lord '
  'begins. Contiguous, gapless [0,120) cover per synthetic_id — half-open predicate '
  '(start <= age < end) returns exactly one row per chart for any reference age.';
COMMENT ON COLUMN bg_synthetic_cohort_md.chain_version IS
  'Algorithm version tag (''vim_md_age_v1''), NOT a per-row content hash — folded into '
  'cohort_client.py''s cohort_version content fingerprint (§6.3).';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS bg_synthetic_cohort_md;
--   COMMIT;
-- =============================================================================
