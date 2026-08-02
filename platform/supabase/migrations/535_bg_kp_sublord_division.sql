-- Migration 535: bg_kp_sublord_division — the canonical 249-fold KP sub-lord
-- division of the sidereal zodiac (L0), + the KP row on brahma_dasha_systems,
-- + the ga_nakshatra KP-significator extension, + two cockpit-truth count_sql fixes.
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · W3K Lane 1 · ANTARYĀMIN ADJUDICATION-7
-- (00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
--  SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md), discharging inventory §6 Lane-1
-- steps 1–4 (00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
--  W3K_SUBSTRATE_INVENTORY_v1_0.md).
--
-- MIGRATION NUMBER: checked against the live max in BOTH directories immediately
-- before authoring — platform/migrations max = 474, platform/supabase/migrations
-- max = 534 (534_kala_paddhati_native_confirmed.sql, on shad-darshana/integration).
-- 535 is free in both. (MIGRATION_AND_MERGE_PROTOCOL §MIG-1; the two-directory
-- trap has hit this campaign twice.)
--
-- ── PART 1: bg_kp_sublord_division (ADJUDICATION-7 Part 1) ────────────────────
-- "The 249-fold division itself: nakṣatra → pāda → sub → sub-sub boundary spans
--  in sidereal longitude, by Vimśottarī proportional subdivision. This is pure
--  chart-independent reference geometry — §N.1's exact definition of bg_*."
--
-- BINDING SUB-RULING HONOURED: the table is stored in SIDEREAL-longitude space
-- and carries NO ayanamsha_key. The division of the sidereal circle is
-- ayanāṃśa-invariant; the ayanāṃśa enters only at the projection of a tropical
-- longitude into it (an L1 concern). Stamping an ayanāṃśa here would fabricate a
-- dependency that does not exist and 5× the row count for no information.
--
-- WHY 249, DERIVED NOT ASSERTED (full derivation in
-- platform/python-sidecar/brahmagyan/l0_kp_sublord_division.py's docstring):
--   R1  each nakṣatra (13°20') is divided into 9 subs in Vimśottarī order
--       starting from its own lord, sub arc = years/120 × 13°20' = years/9 deg.
--       27 × 9 = 243 sub segments.
--   R2  the 12 rāśi boundaries are applied as cuts (a KP division never straddles
--       a sign, because the sign lord is one of the four KP lordship limbs and
--       must be single-valued inside a division). Of the 12: three (0°/120°/240°)
--       start a nakṣatra and cut nothing; three more (60°/180°/300°) land EXACTLY
--       on an interior sub boundary (cumulative 60 Vimśottarī years inside the
--       Mars-lorded Mṛgaśira/Citrā/Dhaniṣṭhā) and also cut nothing; the remaining
--       SIX split one sub segment each.
--   243 + 6 = 249.
-- The Python builder computes this in exact rational arithmetic and the row count
-- FALLS OUT; the test asserts 249 rather than the code hard-coding it, so a wrong
-- derivation fails to reproduce the classical figure instead of assuming it.
--
-- SCOPE DISCLOSURE (not silently omitted): this table holds the SUB level cut by
-- rāśi — the canonical 249. It does NOT tabulate the sub-sub/prāṇa grain (~2,200
-- rows at the same treatment; a different object from "the 249"), and it carries
-- pāda as an ATTRIBUTE (pada_at_start/pada_at_end) rather than as a further cut,
-- because cutting at pāda would move the row count off 249. Sub-sub/prāṇa remain
-- available from the identical proportional rule at call time
-- (ga_writers.ga_nakshatra_compute.compute_kp_lords). A sub-sub reference table is
-- PARKED and named, not dropped.
--
-- ── CITATION (honest tiering, per the ruling's own instruction) ───────────────
-- Tier (i): the Vimśottarī year table + fixed order — BPHS Ch.46, ingested, and
--   already seeded at L0 (brahma_dasha_systems.canonical_id='vimshottari').
-- Tier (iii): the KP-specific conventions (applying the proportion to ARC rather
--   than time; cutting at rāśi) — K. S. Krishnamurti, KP Reader I–III / Stellar
--   Astrology. ADJUDICATION-7 records that NO KP text is ingested in this corpus
--   ("3 chunks ... all three are false positives"), so tier (i) is empty for these
--   two conventions and tier (iii) applies. Per the ruling ("File that gap"), the
--   corpus-ingestion gap for KP source texts is FILED as a work item and named in
--   05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md §8.
-- The tier-(iii) conventions are VERIFIED, not asserted: the committed fixture in
-- CROSSCHECK_v1_0.md §2 (FORENSIC §4.2's nine natal KP lords) is reproduced 9/9 on
-- star lord AND 9/9 on sub lord by this table — see CROSSCHECK §6.
--
-- ── PART 2: brahma_dasha_systems gains canonical_id='kp' (ADJUDICATION-7 Part 4)
-- The field design's own designated extension seam. IMPORTANT HONESTY CONSTRAINT
-- carried in the row itself: KP is NOT a fifth independent timing GENERATOR — its
-- sub/sub-sub periods are proportional subdivisions of the SAME Vimśottarī
-- mahādaśā/antardaśā windows every Parāśarī reading already uses, which is why
-- services/gochara_intensity/permission.py deliberately excludes
-- system_id='vimshottari_kp' from DR-14's PERMISSION plurality count. KP's
-- independence is a JUDGMENT-METHOD independence (a verdict rule with no Parāśarī
-- analogue), not a clock independence — W3K_SUBSTRATE_INVENTORY §4. The row's
-- conditions_for_use states this so no consumer double-counts it.
--
-- ── PART 3: ga_nakshatra extension (ADJUDICATION-7 Part 2 — NO NEW ga_* ASSET) ─
-- The 4-limbed KP significator ladder (gap G-1) lands as ADDITIVE emitters on the
-- standing ga_nakshatra asset, with bg_kp_sublord_division as boundary authority.
-- Two new fact_categories: kp_house_significators, kp_planet_significations.
-- ga_nakshatra.depends_on gains bg_kp_sublord_division (L0→L1, acyclic).
--
-- ── PART 4: cockpit truth (§N.4) — gap G-3 ───────────────────────────────────
-- `bhava_cusps` (12 houses × {sripati,placidus} × {start,madhya,end} = 72 rows per
-- chart per ayanāṃśa) is emitted by ga_positions_writer.py and was counted by NO
-- asset's count_sql. The inventory §2 G-3 attributed it to ga_sensitive; the live
-- emitter is ga_positions (ga_writers/ga_positions_writer.py:450) — corrected here
-- and the fix applied to the writer that actually emits it.
-- DISCLOSED ADJACENT GAP (not fixed here, named so it is not rediscovered as a
-- surprise): `house_chalit` and `sandhi_flag`, emitted by the same ga_positions
-- pass, are ALSO uncounted. They are outside the W3K Lane-1 scope statement
-- (which names bhava_cusps only) and are filed rather than silently swept in.
--
-- ── IDEMPOTENCY ──────────────────────────────────────────────────────────────
-- L0 = ON CONFLICT DO UPDATE (global, no chart_id), per CLAUDE.md §N.3.
-- Rows are seeded by the bg_kp_sublord_division WRITER (deterministic Python,
-- §N.4 deterministic-first), not by this migration — the migration creates the
-- table and the registry contract; it does not hand-transcribe 249 rows.
-- =============================================================================

BEGIN;

-- ── PART 1: the table ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bg_kp_sublord_division (
  table_version           TEXT        NOT NULL,
  division_index          SMALLINT    NOT NULL CHECK (division_index BETWEEN 1 AND 400),
  start_longitude_deg     NUMERIC(18,15) NOT NULL CHECK (start_longitude_deg >= 0   AND start_longitude_deg <  360),
  end_longitude_deg       NUMERIC(18,15) NOT NULL CHECK (end_longitude_deg   >  0   AND end_longitude_deg   <= 360),
  span_arcmin             NUMERIC(18,12) NOT NULL CHECK (span_arcmin > 0),
  nakshatra_number        SMALLINT    NOT NULL CHECK (nakshatra_number BETWEEN 1 AND 27),
  star_lord               TEXT        NOT NULL,
  sub_lord                TEXT        NOT NULL,
  sign_number             SMALLINT    NOT NULL CHECK (sign_number BETWEEN 1 AND 12),
  pada_at_start           SMALLINT    NOT NULL CHECK (pada_at_start BETWEEN 1 AND 4),
  pada_at_end             SMALLINT    NOT NULL CHECK (pada_at_end   BETWEEN 1 AND 4),
  split_by_sign_boundary  BOOLEAN     NOT NULL DEFAULT false,
  source_citation         TEXT        NOT NULL,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT bg_kp_sublord_division_pk PRIMARY KEY (table_version, division_index),
  CONSTRAINT bg_kp_sublord_division_ordered CHECK (end_longitude_deg > start_longitude_deg),
  CONSTRAINT bg_kp_sublord_division_start_uniq UNIQUE (table_version, start_longitude_deg)
);

CREATE INDEX IF NOT EXISTS idx_bg_kp_sublord_division_arc
  ON bg_kp_sublord_division (table_version, start_longitude_deg, end_longitude_deg);

COMMENT ON TABLE bg_kp_sublord_division IS
  'ADJUDICATION-7 Part 1 (SHAD_DARSHANA W3K): the canonical 249-fold Krishnamurti '
  'Paddhati sub-lord division of the SIDEREAL zodiac. 243 Vimshottari-proportional '
  'sub segments (27 nakshatras x 9, sub arc = lord_years/9 degrees, sequence starting '
  'from the nakshatra lord) further cut at the 12 rashi boundaries; six of those '
  'boundaries fall strictly inside a sub segment and split it, giving 243 + 6 = 249. '
  'Chart-independent reference geometry: NO ayanamsha_key by binding sub-ruling — the '
  'division of the sidereal circle is ayanamsha-invariant; the ayanamsha enters only '
  'when a chart longitude is projected into it (L1 ga_nakshatra). Sub-sub/prana grain '
  'is deliberately NOT tabulated (see migration 535 header, SCOPE DISCLOSURE). '
  'Authority for every KP sub-lord boundary in this instrument: L1 REFERENCES this '
  'table (§N.5), it does not re-derive the geometry.';

COMMENT ON COLUMN bg_kp_sublord_division.split_by_sign_boundary IS
  'true when this row is one fragment of a sub segment that a rashi boundary cut in '
  'two (12 such rows = the 6 split segments x 2 fragments). Kept as data so a '
  'consumer can tell a fragment from a whole sub without re-deriving the cut.';

COMMENT ON COLUMN bg_kp_sublord_division.pada_at_start IS
  'The pada (1-4) at this division''s start / end longitude. Pada is carried as an '
  'ATTRIBUTE, not as a further cut: cutting at pada boundaries would move the row '
  'count off the canonical 249. A division whose pada_at_start <> pada_at_end spans '
  'a pada boundary.';

-- ── PART 2: brahma_dasha_systems gains the KP row ────────────────────────────

INSERT INTO brahma_dasha_systems (
    canonical_id, name_sa, name_en, total_cycle_years, base_unit,
    sequence_jsonb, computation_method, computation_pseudocode,
    conditions_for_use, school, classical_citations, python_impl_module
) VALUES (
    'kp',
    'Kṛṣṇamūrti Paddhati',
    'KP (Krishnamurti Paddhati) Sub-Period System',
    120,
    'nakshatra_lord',
    '[{"ruler":"ketu","years":7},{"ruler":"venus","years":20},{"ruler":"sun","years":6},
      {"ruler":"moon","years":10},{"ruler":"mars","years":7},{"ruler":"rahu","years":18},
      {"ruler":"jupiter","years":16},{"ruler":"saturn","years":19},{"ruler":"mercury","years":17}]'::JSONB,
    'vimshottari_proportional_subdivision',
    '1. KP uses the SAME Vimshottari mahadasha/antardasha windows as the Parashari '
    'default — it does not compute a different clock. '
    '2. Each classical window is subdivided further in the same fixed Vimshottari '
    'order and proportion (sub, sub-sub), giving chart_dashas rows under '
    'system_id=''vimshottari_kp'' with kp_sub_lord / kp_sub_sub_lord populated '
    '(ga_dashas_writer.py, KP_SYSTEM_ID). '
    '3. The same proportional rule applied to ARC instead of TIME gives the 249-fold '
    'sub-lord division of the zodiac (bg_kp_sublord_division). '
    '4. KP''s VERDICT rule — "does the running dasha lord match this house''s KP '
    'significator?" (chart_facts.kp_house_significators / kp_planet_significations) — '
    'is the part with no Parashari analogue.',
    'NOT AN INDEPENDENT TIMING GENERATOR. KP''s sub/sub-sub periods are proportional '
    'subdivisions of the SAME Vimshottari windows already counted once, which is why '
    'services/gochara_intensity/permission.py deliberately EXCLUDES '
    'system_id=''vimshottari_kp'' from DR-14''s timing-system-plurality PERMISSION '
    'count — counting it there would double-count one clock. KP''s independence is a '
    'JUDGMENT-METHOD independence (a significator-matching verdict rule Parashari does '
    'not use), and it must earn concurrence through Law-1 applicability like every '
    'other system, never be privileged (SHAD_DARSHANA brief §3 W3K; '
    'W3K_SUBSTRATE_INVENTORY_v1_0.md §4). House frame is Placidus cusps, not '
    'whole-sign — the divergence from the project default is served as data '
    '(chart_facts.kp_planet_significations.house_system_divergence), never reconciled.',
    'kp',
    '[{"text_id": "bphs", "chapter": 46, "note": "proportional constants (Vimshottari year table + fixed order) — TIER-I, ingested"},
      {"text_id": null, "source": "K. S. Krishnamurti, KP Reader I-III (Stellar Astrology)", "note": "the KP-specific conventions — TIER-III, NOT ingested in this corpus (ADJUDICATION-7); corpus gap FILED, see 05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md §8"}]'::JSONB,
    'brahmagyan.l0_kp_sublord_division'
)
ON CONFLICT (canonical_id) DO UPDATE SET
    name_sa                = EXCLUDED.name_sa,
    name_en                = EXCLUDED.name_en,
    total_cycle_years      = EXCLUDED.total_cycle_years,
    base_unit              = EXCLUDED.base_unit,
    sequence_jsonb         = EXCLUDED.sequence_jsonb,
    computation_method     = EXCLUDED.computation_method,
    computation_pseudocode = EXCLUDED.computation_pseudocode,
    conditions_for_use     = EXCLUDED.conditions_for_use,
    school                 = EXCLUDED.school,
    classical_citations    = EXCLUDED.classical_citations,
    python_impl_module     = EXCLUDED.python_impl_module;

-- ── PART 1b: asset_registry seed row (Nirmāṇa contract §2.5.1, SAME PR) ───────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status, asset_kind,
    depends_on
) VALUES (
    'bg_kp_sublord_division',
    'brahmagyan',
    76,
    'Kṛṣṇamūrti Upa-Svāmī Vibhāga',
    'KP Sub-Lord Division (249-fold)',
    'ADJUDICATION-7 Part 1: the canonical 249-fold Krishnamurti Paddhati sub-lord '
    'division of the sidereal zodiac. 243 Vimshottari-proportional sub segments '
    '(sub arc = lord_years/9 degrees, sequence starting from the nakshatra lord) '
    'cut at the 12 rashi boundaries; 6 boundaries fall strictly inside a sub and '
    'split it, so 243 + 6 = 249 — derived by exact rational arithmetic, not '
    'hard-coded. Stored in sidereal longitude with NO ayanamsha key (the sidereal '
    'division is ayanamsha-invariant). AUTHORITY for every KP sub-lord boundary: '
    'ga_nakshatra REFERENCES it (§N.5) rather than re-deriving. Verified 9/9 star '
    'lord + 9/9 sub lord against the committed FORENSIC §4.2 fixture in '
    '05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md §2.',
    'postgres_table', 'bg_kp_sublord_division',
    'SELECT COUNT(*) FROM bg_kp_sublord_division',
    'SELECT pg_total_relation_size(''bg_kp_sublord_division'')',
    249, 'global', true, true, false,
    120,
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
    target_floor            = EXCLUDED.target_floor,
    depends_on              = EXCLUDED.depends_on;

-- ── PART 3: ga_nakshatra — new dependency edge + the two new fact_categories ──

UPDATE asset_registry
   SET depends_on = ARRAY['bg_nakshatra', 'ga_positions', 'bg_kp_sublord_division']::text[],
       count_sql  = 'SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category IN ('
                    || '''graha_nakshatra_join'',''graha_pada_join'',''nakshatra_lord_placement'','
                    || '''graha_kp_lords'',''cusp_kp_lords'',''graha_gandanta'',''graha_degree_flags'','
                    || '''nakshatra_dispositor'',''nakshatra_exchange'',''nakshatra_conjunction'','
                    || '''nakshatra_cogravity'',''graha_tara_bala'',''nakshatra_statistics'','
                    || '''nakshatra_cross_ayanamsha'',''kp_house_significators'',''kp_planet_significations'')',
       english_description = 'Per-chart parallel nakshatra chart: placement+attribute JOIN from '
                    || 'bg_nakshatra, KP sub-lords (star/sub/sub-sub/prana) per body and house cusp, '
                    || 'the 4-limbed KP significator ladder per house AND per planet (W3K, referencing '
                    || 'bg_kp_sublord_division as boundary authority), nakshatra dispositor graph, '
                    || 'gaṇḍānta severity flags, tara bala, per-chart statistics. Into chart_facts. '
                    || 'Authoritative L1 nakshatra grain.'
 WHERE asset_id = 'ga_nakshatra';

-- ── PART 4: cockpit truth — bhava_cusps joins ga_positions' count_sql (G-3) ───
-- ga_positions_writer.py emits bhava_cusps (72 rows/chart/ayanamsha) and no
-- asset counted them. See the header for the disclosed adjacent gap
-- (house_chalit / sandhi_flag, also uncounted, deliberately out of Lane-1 scope).

UPDATE asset_registry
   SET count_sql = 'SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category IN '
                   || '(''graha_position'', ''graha_sign_attributes'', ''bhava_cusps'')'
 WHERE asset_id = 'ga_positions';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   UPDATE asset_registry
--      SET count_sql = 'SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category IN (''graha_position'', ''graha_sign_attributes'')'
--    WHERE asset_id = 'ga_positions';
--   UPDATE asset_registry
--      SET depends_on = ARRAY['bg_nakshatra', 'ga_positions']::text[],
--          count_sql  = 'SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category IN (''graha_nakshatra_join'',''graha_pada_join'',''nakshatra_lord_placement'',''graha_kp_lords'',''cusp_kp_lords'',''graha_gandanta'',''graha_degree_flags'',''nakshatra_dispositor'',''nakshatra_exchange'',''nakshatra_conjunction'',''nakshatra_cogravity'',''graha_tara_bala'',''nakshatra_statistics'',''nakshatra_cross_ayanamsha'')'
--    WHERE asset_id = 'ga_nakshatra';
--   DELETE FROM asset_registry WHERE asset_id = 'bg_kp_sublord_division';
--   DELETE FROM brahma_dasha_systems WHERE canonical_id = 'kp';
--   DROP TABLE IF EXISTS bg_kp_sublord_division;
--   COMMIT;
-- (chart_facts rows in the two new KP categories are per-chart data and are left
--  in place by this DOWN — legacy data is never destroyed by a rollback; a
--  rebuild replaces them per §N.3.)
-- =============================================================================
