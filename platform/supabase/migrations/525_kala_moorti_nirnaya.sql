-- migration 525: kala_moorti_nirnaya + the `ka_moorti_nirnaya` asset_registry seed row
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · Wave W3 · Lane w3-moorti-vedha. Registry item 4:
-- Moorti-nirṇaya — the classical gold/silver/copper/iron ("svarṇa/rajata/
-- tāmra/loha") quality of a transiting graha's stay in a sign, determined by
-- the Moon's nakshatra at the moment of ingress, counted from the native's
-- janma nakshatra. Spec: SHAD_DARSHANA_BRIEF_v2_0.md §1 item 4;
-- KALA_SIX_VIEWS_DESIGN_v1_0.md §1.2 ("reference rules exist
-- (bg_transit_moorti); the per-chart, per-ingress computation does not.
-- BUILD.").
--
-- Migration number: originally authored as 522 (the next-allocatable number
-- per `npx tsx scripts/ci/migration_number_guard.ts` against the two
-- directories at that moment: platform/migrations/ [474] and
-- platform/supabase/migrations/ [521] — the sibling w3-kota-sudarshana
-- lane's 520/521 claims, merged as PR #999, confirmed clear of). RENUMBERED
-- 522 -> 525 before this PR was opened, on discovering — via a live scan of
-- every sibling ṢAḌ-DARŚANA worktree on this machine, not just pushed
-- branches — that THREE other concurrently-running lanes had independently
-- claimed 522/523/524 for unrelated content in the same window
-- (shad-darshana-l0-ne-priors: 522_brahma_class_lifetime_counts.sql;
-- shad-darshana-w3-kota-rings: 523_bg_kota_chakra_rings.sql;
-- shad-darshana-w3-abhijit-parihara:
-- 524_bg_parihara_rules_muhurta_extraction_context.sql) — none of them
-- visible via `git branch -r` at the time this lane's own 522/523 were first
-- authored, since they were local-only at that point. 525/526 (this file +
-- 526_kala_vedha_gochara.sql) were re-verified clear of all of the above
-- immediately before renumbering.
--
-- ── MOORTI TABLE CITATION ─────────────────────────────────────────────────────
-- `bg_transit_moorti` (migration 401) is the REAL, populated, cited 27-row
-- nakshatra-offset -> quality-tier lookup (Phaladeepika Ch.26 §moorti-nirnaya;
-- BPHS Ch.28) — this migration does NOT duplicate that table. This writer
-- only stores which (graha, sign-occupancy window) an ingress produced and
-- the resolved moorti classification for it — every `moorti_classical_citation`
-- value stored here is copied verbatim from bg_transit_moorti at write time
-- (§N.5 — L0 is the authority, never re-derived).
--
-- ── HONESTY DISCIPLINE: moorti_computed ──────────────────────────────────────
-- A sign-occupancy run whose start touches the scanned horizon's edge
-- (start_truncated=true) has an UNVERIFIED true ingress instant — the Moon's
-- nakshatra on the day we happened to start scanning is NOT necessarily the
-- Moon's nakshatra at the true (possibly much earlier) ingress. Such rows
-- carry moorti_computed=false and NULL moorti fields — an honest gap, never
-- a guessed classification (B.10 / §N.7 item 6). See
-- services/ka_moorti_nirnaya/logic.py module docstring for the full
-- rationale.
--
-- ── SCOPE (disclosed, not an oversight) ──────────────────────────────────────
-- Computed for the 8 grahas OTHER than the Moon (classical Gochara practice
-- reads transiting grahas against the natal Moon; "the Moon's position at
-- the Moon's own ingress" is not a distinct classical technique). Single
-- canonical ayanamsha (lahiri_chitrapaksha) — matches the L3 convention
-- (ka_kota_chakra, ka_avadhi, ka_gochara_resonance).
--
-- ── IDEMPOTENCY (§N.3) ───────────────────────────────────────────────────────
-- Per-chart delete-then-insert, scoped further to (chart_id, ayanamsha_id,
-- graha, window_start) as the natural key — a rebuild replaces every
-- sign-run row for the chart, never accretes.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS kala_moorti_nirnaya (
  id                              BIGSERIAL PRIMARY KEY,
  chart_id                        UUID NOT NULL,
  ayanamsha_id                    TEXT NOT NULL DEFAULT 'lahiri_chitrapaksha',
  graha                           TEXT NOT NULL,
  target_sign_idx                 SMALLINT NOT NULL CHECK (target_sign_idx BETWEEN 0 AND 11),
  target_sign_name                TEXT NOT NULL,
  window_start                    DATE NOT NULL,
  window_end                      DATE NOT NULL,
  start_truncated                 BOOLEAN NOT NULL,
  end_truncated                   BOOLEAN NOT NULL,
  moorti_computed                 BOOLEAN NOT NULL,
  moon_nakshatra_idx_at_ingress   SMALLINT CHECK (moon_nakshatra_idx_at_ingress BETWEEN 0 AND 26),
  moon_nakshatra_name_at_ingress  TEXT,
  janma_nakshatra_idx             SMALLINT NOT NULL CHECK (janma_nakshatra_idx BETWEEN 0 AND 26),
  janma_nakshatra_fact_id         TEXT NOT NULL,
  nakshatra_offset                SMALLINT CHECK (nakshatra_offset BETWEEN 1 AND 27),
  moorti_name                     TEXT CHECK (moorti_name IN ('swarna', 'rajata', 'tamra', 'loha')),
  quality_tier                    SMALLINT CHECK (quality_tier BETWEEN 1 AND 4),
  phala_brief                     TEXT,
  moorti_classical_citation       TEXT,
  formula_version                 TEXT NOT NULL,
  computed_at                     TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT kala_moorti_nirnaya_natural_key
    UNIQUE (chart_id, ayanamsha_id, graha, window_start),
  CONSTRAINT kala_moorti_nirnaya_window_order CHECK (window_end >= window_start),
  -- moorti_computed=false <=> all moorti-derived fields are NULL; moorti_computed=true
  -- <=> all are populated. Prevents a half-filled, ambiguous row from ever existing.
  CONSTRAINT kala_moorti_nirnaya_computed_consistency CHECK (
    (moorti_computed = FALSE
      AND moon_nakshatra_idx_at_ingress IS NULL AND moon_nakshatra_name_at_ingress IS NULL
      AND nakshatra_offset IS NULL AND moorti_name IS NULL AND quality_tier IS NULL
      AND phala_brief IS NULL AND moorti_classical_citation IS NULL)
    OR
    (moorti_computed = TRUE
      AND moon_nakshatra_idx_at_ingress IS NOT NULL AND moon_nakshatra_name_at_ingress IS NOT NULL
      AND nakshatra_offset IS NOT NULL AND moorti_name IS NOT NULL AND quality_tier IS NOT NULL
      AND phala_brief IS NOT NULL AND moorti_classical_citation IS NOT NULL)
  )
);

CREATE INDEX IF NOT EXISTS idx_kala_moorti_nirnaya_lookup
  ON kala_moorti_nirnaya (chart_id, graha, window_start, window_end);

COMMENT ON TABLE kala_moorti_nirnaya IS
  'ṢAḌ-DARŚANA W3 item 4: Moorti-nirṇaya per ingress per chart. One row per '
  '(graha, contiguous same-sign occupancy window) over a scanned +-horizon '
  'around build time, for the 8 grahas other than the Moon. moorti_name/'
  'quality_tier/phala_brief/moorti_classical_citation are copied verbatim '
  'from bg_transit_moorti (REAL, cited: Phaladeepika Ch.26, BPHS Ch.28) — '
  'keyed by the Moon''s nakshatra at the run''s start (the ingress moment), '
  'offset from the janma nakshatra. moorti_computed=false (all moorti '
  'fields NULL) when the run''s start is unverified (start_truncated=true) '
  'or the Moon ephemeris/moorti-table lookup is unavailable — an honest '
  'gap, never a guessed classification.';

COMMENT ON COLUMN kala_moorti_nirnaya.start_truncated IS
  'True when window_start lands exactly on the scanned horizon''s start '
  'edge — the graha''s true ingress into this sign is NOT verified to be '
  'window_start; we simply did not scan further back. When true, '
  'moorti_computed is forced false (see table comment).';

COMMENT ON COLUMN kala_moorti_nirnaya.end_truncated IS
  'Same discipline as start_truncated, for the horizon''s forward edge — '
  'does not affect moorti_computed (the classification is anchored to the '
  'window''s START, the ingress moment, not its end).';

-- ── asset_registry seed row for `ka_moorti_nirnaya` (Nirmāṇa contract
-- §2.5.1: seed row lands in the SAME PR as the writer) ───────────────────────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status, asset_kind,
    depends_on
) VALUES (
    'ka_moorti_nirnaya',
    'kala',
    122,
    'Mūrti-Nirṇaya',
    'Moorti-Nirṇaya (Transit Quality)',
    'ṢAḌ-DARŚANA W3 item 4: the classical gold/silver/copper/iron quality of '
    'a transiting graha''s stay in a sign, determined by the Moon''s '
    'nakshatra at the moment of ingress, offset from the janma nakshatra. '
    'Reads natal Moon longitude from chart_facts (ga_positions), transiting '
    'positions from ephemeris_daily (bg_ephemeris), and the moorti quality '
    'table verbatim from bg_transit_moorti (bg_transit_rules, real cited '
    'reference data — never re-derived).',
    'postgres_table', 'kala_moorti_nirnaya',
    'SELECT COUNT(*) FROM kala_moorti_nirnaya WHERE chart_id=$1',
    'SELECT pg_total_relation_size(''kala_moorti_nirnaya'')',
    0, 'per_chart', true, true, false,
    120,
    'Kāla', 'L3', 'CURRENT', 'data',
    ARRAY['ga_positions', 'bg_ephemeris', 'bg_transit_rules']::text[]
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql               = EXCLUDED.count_sql,
    size_sql                = EXCLUDED.size_sql,
    target_table            = EXCLUDED.target_table,
    has_writer              = EXCLUDED.has_writer,
    has_substeps            = EXCLUDED.has_substeps,
    writer_timeout_seconds  = EXCLUDED.writer_timeout_seconds,
    sort_order              = EXCLUDED.sort_order,
    scope                   = EXCLUDED.scope,
    is_active               = EXCLUDED.is_active,
    sanskrit_name           = EXCLUDED.sanskrit_name,
    english_name            = EXCLUDED.english_name,
    english_description     = EXCLUDED.english_description,
    depends_on              = EXCLUDED.depends_on;

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'ka_moorti_nirnaya';
--   DROP TABLE IF EXISTS kala_moorti_nirnaya;
--   COMMIT;
-- =============================================================================
