-- Migration 528: bg_vedha_malefic_scale + bg_phaladeepika_latta — cited L0 vedha rules
-- from Phaladeepika Adh. XXVI (ADJUDICATION-11 Part 4, mandatory for R-19 closure)
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · ANTARYĀMIN supplemental ruling ADJUDICATION-11
-- (00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
--  SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md) Part 4: "item 5 also seeds +
-- serves at least the two cited vedha rows the corpus holds today, transcribed
-- exactly: Phaladeepika PG353 (vedha scale) and PG339 (Lattā,
-- vedha_kind='latta', uncited_extension=false), as versioned cited L0 rows."
--
-- ── VERIFICATION (mandatory precondition, discharged before this file was
-- authored) ────────────────────────────────────────────────────────────────
-- Both chunks were read READ-ONLY via the postgres MCP (SELECT only) against
-- `classical_text_chunks` this session, BEFORE any row below was written.
-- Exact quoted text (transcribed from the OCR'd content_en column, cleaned of
-- OCR line-break noise only — no wording changed) is reproduced in this PR's
-- description and in brahmagyan/l0_phaladeepika_vedha.py's module docstring.
--
-- ── TABLE 1: bg_vedha_malefic_scale (PG353) ───────────────────────────────────
-- Verbatim (chunk phaladeepika_pg0353_c01): "When at the time of a battle,
-- there is a (Vedha) caused by one, two, three, four or five malefics, the
-- corresponding effects will be fear, failure, killing (blood-shed), death
-- and ignominy respectively." A genuine classical malefic-count -> effect-
-- grade scale, REAL and cited (school='parashari', Phaladeepika Adh. XXVI).
-- SCOPE DISCLOSURE: the source verse is stated in a muhurta/nimitta "time of
-- battle" context, not generalized in the text itself to any-and-every vedha
-- situation. This table stores the verse's scale VERBATIM and CITED; whether
-- a specific consuming computation's APPLICATION of the scale outside a
-- battle-muhurta context is itself an extension is that consumer's own
-- disclosure to make (see ka_vedha_gochara's own `uncited_extension` flag on
-- rows that apply this table to ordinary transit vedha) — the table's own
-- rows are the verbatim cited scale, not an extension.
--
-- ── TABLE 2: bg_phaladeepika_latta (PG338-339, Sloka 42-44 + effects) ─────────
-- Verbatim (chunks phaladeepika_pg0338_c01 + phaladeepika_pg0339_c01, joined
-- across the OCR page break): "The 12th asterism counted from that occupied
-- by the Sun at the time, the 3rd from that of Mars, the 6th from that of
-- Jupiter, and the 8th from that of Saturn are termed ... forward Lattas.
-- The 5th star reckoned from that of Venus, the 7th from that of Mercury;
-- the 9th from that of Rahu and the 22nd from that of the Moon are called
-- ... rear Latta. If, when thus counting, the Janma-nakshatra (natal star)
-- happens to come as the Latta star, there will be sickness and anguish."
-- Per-graha effects, also verbatim: "During the Sun's Latta there will be
-- ruin of every business. Misery will result during the Latta of Rahu and
-- Ketu. In the Latta of Jupiter, death, ruin of relations and a sort of
-- general fear or insecurity may occur. There will be quarrel in the Latta
-- of Venus. In Mercury's Latta will occur loss of position or similar
-- untoward event. A great loss will mark the Moon's Latta."
--
-- HONEST GAPS (disclosed, not silently filled):
--   - Mars and Saturn ARE given a counting rule (3rd, 8th forward) but NO
--     distinct per-graha effect text was found in the retrieved passage
--     (`effect_description` is NULL for these two rows — the general
--     sickness/anguish affliction from the shared condition still applies).
--   - Ketu is named in the EFFECTS text ("Misery will result during the
--     Latta of Rahu and Ketu") but its own counting rule (which asterism
--     counts as Ketu's Latta point) was NOT found in the retrieved passage —
--     Ketu is NOT seeded here rather than guessed (B.10). Filed as a
--     follow-on extraction item alongside the other 13 unretrieved
--     Phaladeepika vedha hits (ADJUDICATION-11 Part 6).
--   - Sloka 47 (multi-Latta synchronisation multiplies severity 2x-3x) and
--     Sloka 48 (a general SBC-vedha auspicious/evil note) are cited in
--     source material but NOT implemented as computed logic here — disclosed
--     as a documented follow-on refinement, not attempted under time
--     pressure (mirrors ADJUDICATION-11 Part 6's own framing).
--
-- ── CITATION ──────────────────────────────────────────────────────────────────
-- '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950
--  (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG353' / '| PG339'
-- text_id='phaladeepika' in classical_texts (author Mantreswara, school
-- 'parashari'). Both `[HIGH]` provenance per the corpus's own tagging.
--
-- ── VERSIONING (§N.3 / §B.8) ───────────────────────────────────────────────────
-- table_version zero-padded (phaladeepika_vedha_v01) per the ne_vNN /
-- kota_chakra_rings_vNN precedent. A revision (e.g. adding Ketu once sourced)
-- is a new _v02 row set landed by INSERT, never an in-place edit.
--
-- ── IDEMPOTENCY ────────────────────────────────────────────────────────────────
-- L0 = ON CONFLICT DO UPDATE (global, not per-chart), per §N.3.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS bg_vedha_malefic_scale (
  table_version       TEXT        NOT NULL,
  malefic_count       SMALLINT    NOT NULL CHECK (malefic_count BETWEEN 1 AND 5),
  effect_grade        TEXT        NOT NULL,
  effect_description  TEXT        NOT NULL,
  source_citation     TEXT        NOT NULL,
  verse_ref           TEXT        NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT bg_vedha_malefic_scale_pk PRIMARY KEY (table_version, malefic_count)
);

COMMENT ON TABLE bg_vedha_malefic_scale IS
  'ADJUDICATION-11 Part 4 (mandatory for R-19 closure): Phaladeepika Adh. XXVI '
  'PG353''s malefic-count -> effect-grade vedha scale, REAL and cited, '
  'transcribed verbatim. malefic_count is the number of malefics (1-5) '
  'simultaneously causing vedha; effect_grade/effect_description are the '
  'verse''s own graded outcomes (fear/failure/killing/death/ignominy). Source '
  'verse context is "at the time of a battle" — see this migration''s header '
  'for the scope-generalization disclosure. Consumed by ka_vedha_gochara.';

CREATE TABLE IF NOT EXISTS bg_phaladeepika_latta (
  table_version         TEXT        NOT NULL,
  graha                 TEXT        NOT NULL,
  count_from_graha      SMALLINT    NOT NULL,
  direction             TEXT        NOT NULL CHECK (direction IN ('forward', 'backward')),
  effect_description    TEXT,
  affliction_condition  TEXT        NOT NULL,
  source_citation       TEXT        NOT NULL,
  verse_ref             TEXT        NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT bg_phaladeepika_latta_pk PRIMARY KEY (table_version, graha)
);

COMMENT ON TABLE bg_phaladeepika_latta IS
  'ADJUDICATION-11 Part 4 (mandatory for R-19 closure): Phaladeepika Adh. XXVI '
  'PG338-339 Sloka 42-44''s Lattā rule, REAL and cited, transcribed verbatim. '
  'For each graha, the Lattā nakshatra is count_from_graha nakshatras forward '
  '(direction=''forward'') or backward (''backward'') from that graha''s '
  'current transiting nakshatra. affliction_condition (identical on every '
  'row, the verse''s own shared rule) fires when the native''s janma '
  'nakshatra coincides with the Lattā nakshatra. effect_description is the '
  'verse''s own per-graha elaboration where the retrieved passage states one '
  '(NULL for Mars/Saturn — disclosed gap, see migration header; the shared '
  'affliction_condition still applies). Ketu is deliberately ABSENT (its own '
  'counting rule was not found in the retrieved passage — not guessed, '
  'B.10). Consumed by ka_vedha_gochara as vedha_kind=''latta'' rows, '
  'uncited_extension=false.';

COMMENT ON COLUMN bg_phaladeepika_latta.affliction_condition IS
  'Verbatim, shared across every row: "If, when thus counting, the '
  'Janma-nakshatra (natal star) happens to come as the Latta star, there '
  'will be sickness and anguish." (PG339).';

-- ── bg_vedha_malefic_scale seed (5 rows, verbatim from PG353) ────────────────

INSERT INTO bg_vedha_malefic_scale
  (table_version, malefic_count, effect_grade, effect_description, source_citation, verse_ref)
VALUES
  ('phaladeepika_vedha_v01', 1, 'fear',     'Vedha caused by one malefic: fear.',                          '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG353', 'Adh.XXVI PG353'),
  ('phaladeepika_vedha_v01', 2, 'failure',  'Vedha caused by two malefics: failure.',                      '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG353', 'Adh.XXVI PG353'),
  ('phaladeepika_vedha_v01', 3, 'killing',  'Vedha caused by three malefics: killing (blood-shed).',       '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG353', 'Adh.XXVI PG353'),
  ('phaladeepika_vedha_v01', 4, 'death',    'Vedha caused by four malefics: death.',                       '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG353', 'Adh.XXVI PG353'),
  ('phaladeepika_vedha_v01', 5, 'ignominy', 'Vedha caused by five malefics: ignominy.',                    '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG353', 'Adh.XXVI PG353')
ON CONFLICT (table_version, malefic_count) DO UPDATE SET
  effect_grade       = EXCLUDED.effect_grade,
  effect_description = EXCLUDED.effect_description,
  source_citation    = EXCLUDED.source_citation,
  verse_ref          = EXCLUDED.verse_ref;

-- ── bg_phaladeepika_latta seed (8 rows, verbatim from PG338-339 Sloka 42-44) ──

INSERT INTO bg_phaladeepika_latta
  (table_version, graha, count_from_graha, direction, effect_description, affliction_condition, source_citation, verse_ref)
VALUES
  ('phaladeepika_vedha_v01', 'Sun',     12, 'forward',  'Ruin of every business.',
   'If, when thus counting, the Janma-nakshatra (natal star) happens to come as the Latta star, there will be sickness and anguish.',
   '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG339', 'Adh.XXVI PG338-339 Sloka 42-44'),
  ('phaladeepika_vedha_v01', 'Mars',     3, 'forward',  NULL,
   'If, when thus counting, the Janma-nakshatra (natal star) happens to come as the Latta star, there will be sickness and anguish.',
   '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG339', 'Adh.XXVI PG338-339 Sloka 42-44'),
  ('phaladeepika_vedha_v01', 'Jupiter',  6, 'forward',  'Death, ruin of relations and a sort of general fear or insecurity may occur.',
   'If, when thus counting, the Janma-nakshatra (natal star) happens to come as the Latta star, there will be sickness and anguish.',
   '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG339', 'Adh.XXVI PG338-339 Sloka 42-44'),
  ('phaladeepika_vedha_v01', 'Saturn',   8, 'forward',  NULL,
   'If, when thus counting, the Janma-nakshatra (natal star) happens to come as the Latta star, there will be sickness and anguish.',
   '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG339', 'Adh.XXVI PG338-339 Sloka 42-44'),
  ('phaladeepika_vedha_v01', 'Venus',    5, 'backward', 'Quarrel.',
   'If, when thus counting, the Janma-nakshatra (natal star) happens to come as the Latta star, there will be sickness and anguish.',
   '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG339', 'Adh.XXVI PG338-339 Sloka 42-44'),
  ('phaladeepika_vedha_v01', 'Mercury',  7, 'backward', 'Loss of position or similar untoward event.',
   'If, when thus counting, the Janma-nakshatra (natal star) happens to come as the Latta star, there will be sickness and anguish.',
   '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG339', 'Adh.XXVI PG338-339 Sloka 42-44'),
  ('phaladeepika_vedha_v01', 'Rahu',     9, 'backward', 'Misery.',
   'If, when thus counting, the Janma-nakshatra (natal star) happens to come as the Latta star, there will be sickness and anguish.',
   '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG339', 'Adh.XXVI PG338-339 Sloka 42-44'),
  ('phaladeepika_vedha_v01', 'Moon',    22, 'backward', 'A great loss.',
   'If, when thus counting, the Janma-nakshatra (natal star) happens to come as the Latta star, there will be sickness and anguish.',
   '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG339', 'Adh.XXVI PG338-339 Sloka 42-44')
ON CONFLICT (table_version, graha) DO UPDATE SET
  count_from_graha      = EXCLUDED.count_from_graha,
  direction             = EXCLUDED.direction,
  effect_description    = EXCLUDED.effect_description,
  affliction_condition  = EXCLUDED.affliction_condition,
  source_citation       = EXCLUDED.source_citation,
  verse_ref             = EXCLUDED.verse_ref;

-- ── asset_registry seed rows (Nirmāṇa contract §2.5.1) ───────────────────────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status, asset_kind,
    depends_on
) VALUES
(
    'bg_vedha_malefic_scale',
    'brahmagyan',
    74,
    'Vedha-Pāpa-Saṅkhyā Sāraṇī',
    'Vedha Malefic-Count Scale (Phaladeepika PG353)',
    'ADJUDICATION-11 Part 4: Phaladeepika Adh. XXVI PG353''s malefic-count '
    '(1-5) -> effect-grade (fear/failure/killing/death/ignominy) vedha scale, '
    'REAL and cited, transcribed verbatim. Consumed by ka_vedha_gochara for '
    'the house_vedha malefic-count grading.',
    'postgres_table', 'bg_vedha_malefic_scale',
    'SELECT COUNT(*) FROM bg_vedha_malefic_scale',
    'SELECT pg_total_relation_size(''bg_vedha_malefic_scale'')',
    5, 'global', true, true, false,
    60,
    'Brahmagyan', 'L0', 'CURRENT', 'data',
    ARRAY[]::text[]
),
(
    'bg_phaladeepika_latta',
    'brahmagyan',
    75,
    'Lattā Sāraṇī (Phaladeepikā)',
    'Lattā Vedha Rule Table (Phaladeepika PG338-339)',
    'ADJUDICATION-11 Part 4: Phaladeepika Adh. XXVI PG338-339 Sloka 42-44''s '
    'Lattā (obstruction-point) rule, REAL and cited, transcribed verbatim, 8 '
    'grahas (Ketu deliberately absent — its counting rule was not found in '
    'the retrieved passage). Consumed by ka_vedha_gochara as vedha_kind='
    '''latta'' rows, uncited_extension=false.',
    'postgres_table', 'bg_phaladeepika_latta',
    'SELECT COUNT(*) FROM bg_phaladeepika_latta',
    'SELECT pg_total_relation_size(''bg_phaladeepika_latta'')',
    8, 'global', true, true, false,
    60,
    'Brahmagyan', 'L0', 'CURRENT', 'data',
    ARRAY[]::text[]
)
ON CONFLICT (asset_id) DO UPDATE SET
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

-- ── ka_vedha_gochara gains the two new dependency edges (Nirmāṇa contract) ────

UPDATE asset_registry
   SET depends_on = ARRAY['ga_positions', 'bg_ephemeris', 'bg_transit_rules',
                           'bg_sarvatobhadra_grid', 'bg_vedha_malefic_scale', 'bg_phaladeepika_latta']::text[]
 WHERE asset_id = 'ka_vedha_gochara';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   UPDATE asset_registry SET depends_on = ARRAY['ga_positions', 'bg_ephemeris', 'bg_transit_rules']::text[]
--     WHERE asset_id = 'ka_vedha_gochara';
--   DELETE FROM asset_registry WHERE asset_id IN ('bg_vedha_malefic_scale', 'bg_phaladeepika_latta');
--   DROP TABLE IF EXISTS bg_vedha_malefic_scale;
--   DROP TABLE IF EXISTS bg_phaladeepika_latta;
--   COMMIT;
-- =============================================================================
