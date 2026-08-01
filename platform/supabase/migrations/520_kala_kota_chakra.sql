-- migration 520: kala_kota_chakra + the `ka_kota_chakra` asset_registry seed row
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · Wave W3 · Lane w3-kota-sudarshana. Registry item 16:
-- Kota-Chakra (the fort chakra) — transiting grahas mapped to the kota's
-- stambha/durgantara(madhya)/prakara/bahya rings relative to the janma
-- nakshatra, with entry/exit windows and an attack/defence reading.
-- Spec: SHAD_DARSHANA_BRIEF_v2_0.md §1 item 16.
--
-- ── RING TABLE CITATION (see services/ka_kota_chakra/logic.py for the full
-- disclosure) ────────────────────────────────────────────────────────────────
-- The classical ring partition (Stambha 4/11/18/25th, Durgantara
-- 3/5/10/12/17/19/24/26th, Prakara 2/6/9/13/16/20/23/27th from janma
-- nakshatra, Bahya = the remaining 7 positions) is NOT present in the
-- ingested corpus as of this migration — it is a tier-(iii) secondary-source
-- transcription per the W3K citation hierarchy (brief §3 W3K). Filed here as
-- an ADJUDICATION-PENDING corpus-ingestion gap, not silently upgraded to a
-- primary citation. `ring_table_citation` on every row carries this
-- disclosure verbatim so no served row can be mistaken for primary-sourced.
--
-- ── SCOPE (disclosed, not an oversight) ──────────────────────────────────────
-- Single canonical ayanamsha (lahiri_chitrapaksha) — matches the L3
-- convention (ka_avadhi, ka_gochara_resonance), not the L2 bo_* 5-ayanamsha
-- loop convention. Multi-ayanamsha support is a natural additive follow-on.
--
-- ── IDEMPOTENCY (§N.3) ───────────────────────────────────────────────────────
-- Per-chart delete-then-insert, scoped further to (chart_id, ayanamsha_id,
-- graha, window_start) as the natural key — a rebuild replaces every ring-run
-- row for the chart, never accretes.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS kala_kota_chakra (
  id                        BIGSERIAL PRIMARY KEY,
  chart_id                  UUID NOT NULL,
  ayanamsha_id              TEXT NOT NULL DEFAULT 'lahiri_chitrapaksha',
  graha                     TEXT NOT NULL,
  nakshatra_idx             SMALLINT NOT NULL CHECK (nakshatra_idx BETWEEN 0 AND 26),
  nakshatra_name            TEXT NOT NULL,
  count_from_janma          SMALLINT NOT NULL CHECK (count_from_janma BETWEEN 1 AND 27),
  kota_ring                 TEXT NOT NULL CHECK (kota_ring IN ('stambha', 'durgantara', 'prakara', 'bahya')),
  is_natural_malefic        BOOLEAN NOT NULL,
  posture                   TEXT NOT NULL,
  severity                  TEXT NOT NULL,
  window_start              DATE NOT NULL,
  window_end                DATE NOT NULL,
  start_truncated           BOOLEAN NOT NULL,
  end_truncated             BOOLEAN NOT NULL,
  janma_nakshatra_fact_id   TEXT NOT NULL,
  ring_table_citation       TEXT NOT NULL,
  uncited_extension         BOOLEAN NOT NULL DEFAULT TRUE,
  formula_version           TEXT NOT NULL,
  computed_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT kala_kota_chakra_natural_key
    UNIQUE (chart_id, ayanamsha_id, graha, window_start),
  CONSTRAINT kala_kota_chakra_window_order CHECK (window_end >= window_start)
);

CREATE INDEX IF NOT EXISTS idx_kala_kota_chakra_lookup
  ON kala_kota_chakra (chart_id, graha, window_start, window_end);

COMMENT ON TABLE kala_kota_chakra IS
  'ṢAḌ-DARŚANA W3 item 16: Kota-Chakra fort chart. One row per (graha, '
  'contiguous same-nakshatra window) over a scanned +-horizon around build '
  'time. kota_ring is the graha''s nakshatra-count-from-janma ring '
  '(stambha/durgantara/prakara/bahya); posture/severity is this writer''s own '
  'template synthesis of ring x classical benefic/malefic nature '
  '(uncited_extension=true) — see ring_table_citation for the ring table''s '
  'own tier-(iii) secondary-source disclosure.';

COMMENT ON COLUMN kala_kota_chakra.start_truncated IS
  'True when window_start lands exactly on the scanned horizon''s start edge '
  '— i.e. the graha''s true entry into this nakshatra is NOT verified to be '
  'window_start; we simply did not scan further back. Honest B.10 disclosure, '
  'never a silently-precise-looking date.';

COMMENT ON COLUMN kala_kota_chakra.end_truncated IS
  'Same discipline as start_truncated, for the horizon''s forward edge.';

-- ── asset_registry seed row for `ka_kota_chakra` (Nirmāṇa contract §2.5.1:
-- seed row lands in the SAME PR as the writer) ───────────────────────────────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status, asset_kind,
    depends_on
) VALUES (
    'ka_kota_chakra',
    'kala',
    120,
    'Koṭa-Cakra',
    'Fort Chart (Transit Fortress)',
    'ṢAḌ-DARŚANA W3 item 16: transiting grahas mapped to the kota''s '
    'stambha/durgantara/prakara/bahya rings relative to the janma nakshatra, '
    'with entry/exit windows and an attack/defence reading. Reads natal Moon '
    'longitude from chart_facts (ga_positions) and transiting positions from '
    'ephemeris_daily (bg_ephemeris); the ring table itself is a disclosed '
    'tier-(iii) secondary-source transcription pending corpus ingestion.',
    'postgres_table', 'kala_kota_chakra',
    'SELECT COUNT(*) FROM kala_kota_chakra WHERE chart_id=$1',
    'SELECT pg_total_relation_size(''kala_kota_chakra'')',
    0, 'per_chart', true, true, false,
    120,
    'Kāla', 'L3', 'CURRENT', 'data',
    ARRAY['ga_positions', 'bg_ephemeris']::text[]
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
--   DELETE FROM asset_registry WHERE asset_id = 'ka_kota_chakra';
--   DROP TABLE IF EXISTS kala_kota_chakra;
--   COMMIT;
-- =============================================================================
