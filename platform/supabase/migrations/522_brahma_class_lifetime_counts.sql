-- Migration 522: N_e structural priors — brahma_class_priors.prior_basis/source_ref,
--                the lifetime-basis CHECK, the `bg_class_lifetime_counts` asset_registry
--                row, and the ka_kshetra ← bg_class_lifetime_counts DAG edge.
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · Wave W2 · lane `l0-ne-priors` (CRITICAL PATH for Gate W2).
-- Governing ruling: 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
--                   SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md § ADJUDICATION-2,
--                   "What the L0 lane concretely builds" items 1, 5, 6.
--
-- ── WHY ──────────────────────────────────────────────────────────────────────
-- KALA_W2_FIELD_DESIGN §5.1 C-1 requires `N_e` — the expected lifetime count of
-- event class `e` over the chart's 100-year horizon — read from
-- `brahma_class_priors` at the reserved coordinate
-- `fact_kind = 'lifetime_count_per_100y'`. No such row exists anywhere today, so
-- `ka_kshetra`'s `load_class_lifetime_count` / `require_baseline`
-- (services/ka_kshetra/stage4_field.py) raise `ClassSkipped(e, 'no_class_prior_row')`
-- for EVERY class and the temporal field is empty.
--
-- ADJUDICATION-2 rules that these values may come ONLY from Tier N-i — a published
-- demographic / actuarial / epidemiological statistic carrying all six of:
-- publisher · edition/survey round · year · indicator/table id · geography+cohort ·
-- retrievable URL or DOI — or from Tier N-ii, a STATED ARITHMETIC IDENTITY over an
-- already-seeded Tier N-i value. Classical-text-derived counts are FORECLOSED
-- (chart-conditional evidence already lives in `P_e`; routing it into λ⁰ double-counts
-- inside a multiplicative hazard and inverts B.1). Cohort-derived counts are
-- FORECLOSED by the CIRCULARITY GUARD (the only real event record is the LEL, and the
-- field never reads the LEL).
--
-- ── WHAT THIS MIGRATION ADDS ─────────────────────────────────────────────────
-- Two nullable TEXT columns and one CHECK constraint that makes the NIGHT_RUN §D
-- DATA-HONESTY RAIL machine-enforced rather than free-text: a row at the reserved
-- lifetime-count coordinate CANNOT be inserted without declaring its basis and
-- naming its source. Existing rows are untouched — all 164 signal-salience priors
-- sit at `fact_kind <> 'lifetime_count_per_100y'` and so satisfy the constraint's
-- left disjunct vacuously.
--
-- ── NON-REGRESSION (verified before authoring) ───────────────────────────────
-- Both existing consumers of `brahma_class_priors` — `bo_laksana._load_class_priors`
-- and `mi_kula._load_registry_priors` — filter `WHERE prior_version='1.0' AND
-- signal_tradition='*' AND fact_kind='*'`. Rows written at
-- `prior_version='ne_v01'`/`fact_kind='lifetime_count_per_100y'` are invisible to
-- both. There is no regression surface.
--
-- ── VERSIONING (ADJUDICATION-2 item 4) ───────────────────────────────────────
-- `prior_version = 'ne_v01'` — ZERO-PADDED, mandatory. `ka_kshetra` selects
-- `ORDER BY prior_version DESC LIMIT 1`, which is a STRING sort: unpadded `ne_v10`
-- would sort below `ne_v2`. A revision is a new `ne_v02` row set, never an in-place
-- edit; retracting a value = seeding `ne_v02` without it, and the class reverts to
-- honest-skip automatically.
--
-- ── IDEMPOTENCY (§N.3) ───────────────────────────────────────────────────────
-- L0 global reference data: `ADD COLUMN IF NOT EXISTS`, constraint guarded by a
-- `pg_constraint` existence check (ADD CONSTRAINT has no IF NOT EXISTS form —
-- same pattern as migration 456), registry row `ON CONFLICT (asset_id) DO UPDATE`,
-- DAG edge appended only when absent. Fully re-runnable.
--
-- ── REVERSIBILITY: HIGH ──────────────────────────────────────────────────────
-- Drop two nullable columns, one constraint, one asset row, one DAG edge. No served
-- value in any existing surface changes. No FROZEN contract touched. See the DOWN
-- block at the foot of this file.
-- =============================================================================

BEGIN;

-- ── 1. Additive columns (ADJUDICATION-2 item 1, verbatim) ────────────────────

ALTER TABLE brahma_class_priors
  ADD COLUMN IF NOT EXISTS prior_basis TEXT,
  ADD COLUMN IF NOT EXISTS source_ref  TEXT;

COMMENT ON COLUMN brahma_class_priors.prior_basis IS
  'Epistemic basis of the row''s value. NULL for the 164 legacy signal-salience '
  'priors (prior_version=''1.0''). For rows at fact_kind=''lifetime_count_per_100y'' '
  'this is CONSTRAINED to ''demographic_structural'' (Tier N-i: a published '
  'demographic/actuarial/epidemiological statistic carrying all six citation '
  'elements) or ''derived_identity'' (Tier N-ii: obtained from an already-seeded '
  'Tier N-i value by a STATED ARITHMETIC IDENTITY, never by judgement — "a '
  'reasonable proportion of" is not an identity and is forbidden). '
  'ADJUDICATION-2 source hierarchy.';

COMMENT ON COLUMN brahma_class_priors.source_ref IS
  'The retrievable source handle: publisher · edition/survey round · year · '
  'indicator/table id · geography+cohort · URL or DOI, plus the arithmetic '
  'converting the published figure to a per-100-year count. NOT NULL is enforced '
  'for lifetime-count rows by brahma_class_priors_lifetime_basis_ck — this is what '
  'makes the NIGHT_RUN §D DATA-HONESTY RAIL machine-enforced rather than free-text.';

-- ── 2. The lifetime-basis CHECK (ADJUDICATION-2 item 1, verbatim) ────────────
-- ADD CONSTRAINT has no IF NOT EXISTS form in Postgres; guard with an existence
-- check so this file is safely re-runnable (same discipline as migration 456).

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'brahma_class_priors_lifetime_basis_ck'
  ) THEN
    ALTER TABLE brahma_class_priors
      ADD CONSTRAINT brahma_class_priors_lifetime_basis_ck
      CHECK (fact_kind <> 'lifetime_count_per_100y'
             OR (prior_basis IN ('demographic_structural','derived_identity')
                 AND source_ref IS NOT NULL));
  END IF;
END $$;

COMMENT ON CONSTRAINT brahma_class_priors_lifetime_basis_ck ON brahma_class_priors IS
  'ADJUDICATION-2: a value at the reserved N_e coordinate cannot exist without '
  'declaring its tier and naming its source. Note what this constraint does NOT '
  'claim (CLAUDE.md §N.8 — a signal must measure what it asserts): it enforces that '
  'a basis and a source string are PRESENT and well-typed. It cannot verify that the '
  'cited source says what the row claims, nor that the conversion arithmetic is '
  'correct. Those are the Verifier''s two-pass independent re-derivation (item 7), '
  'and the seed module''s citation-completeness test. The constraint closes the '
  '"number with no source at all" hole; it does not close the "wrong number" hole.';

-- ── 3. asset_registry row for `bg_class_lifetime_counts` (item 5, verbatim) ──
-- Mirrors platform/scripts/seed/asset_registry_seed.ts exactly — a clean reseed
-- must not silently drop this asset (the ga_vichara / bo_pratijna defect class).
-- Global L0, `depends_on=[]`, `scope='global'`. Per brief §2.5.2 it is
-- super-admin-triggered and never auto-pulled into a per-chart build.

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, depends_on, scope, is_active, has_writer, has_substeps,
    layer_name, layer_index, catalog_status, asset_kind
) VALUES (
    'bg_class_lifetime_counts',
    'brahmagyan',
    21,
    'Jīvana-Ghaṭanā-Saṅkhyā',
    'Event-Class Lifetime Counts',
    'ṢAḌ-DARŚANA W2 (ADJUDICATION-2): N_e — the expected lifetime count of each '
    'brahma_event_ontology event class over a 100-year modelled timeline from birth, '
    'assuming survival. The chart-INDEPENDENT structural baseline λ⁰_e of the Kāla '
    'Kṣetra hazard field. Every value is Tier N-i: a published demographic / '
    'actuarial / epidemiological statistic carrying publisher, edition, year, '
    'indicator id, geography+cohort and a retrievable URL/DOI, together with the '
    'arithmetic converting it to a per-100-year count — or Tier N-ii, a stated '
    'arithmetic identity over such a value. Classical-text counts are FORECLOSED '
    '(chart-conditional; already carried by P_e) and cohort/LEL-derived counts are '
    'FORECLOSED by the circularity guard. A class with no defensible source is NOT '
    'seeded and is honestly skipped by ka_kshetra with no_class_prior_row — '
    'honest-empty per class, never a fabricated baseline.',
    'postgres_table', 'brahma_class_priors',
    'SELECT COUNT(*) FROM brahma_class_priors WHERE fact_kind=''lifetime_count_per_100y''',
    NULL,
    0, ARRAY[]::text[], 'global', true, true, false,
    'Brahmagyan', 'L0', 'CURRENT', 'data'
) ON CONFLICT (asset_id) DO UPDATE SET
    layer                   = EXCLUDED.layer,
    sort_order              = EXCLUDED.sort_order,
    sanskrit_name           = EXCLUDED.sanskrit_name,
    english_name            = EXCLUDED.english_name,
    english_description     = EXCLUDED.english_description,
    storage_type            = EXCLUDED.storage_type,
    target_table            = EXCLUDED.target_table,
    count_sql               = EXCLUDED.count_sql,
    scope                   = EXCLUDED.scope,
    is_active               = EXCLUDED.is_active,
    has_writer              = EXCLUDED.has_writer,
    has_substeps            = EXCLUDED.has_substeps,
    layer_name              = EXCLUDED.layer_name,
    layer_index             = EXCLUDED.layer_index,
    catalog_status          = EXCLUDED.catalog_status,
    asset_kind              = EXCLUDED.asset_kind;

-- `target_floor` is left at 0 deliberately (§N.4 — floors are aspirational, never
-- gates, and are set to the ACHIEVED count after a build). Seeding a floor of 6 or
-- 27 here would be exactly the "fabricate rows to hit a number" pressure the rail
-- forbids, on the one asset where fabricating a row is the specific failure mode
-- ADJUDICATION-2 exists to prevent.

-- ── 4. DAG edge: ka_kshetra ← bg_class_lifetime_counts (item 6) ──────────────
-- Mirrors the `bg_cohort` precedent exactly: `bg_cohort` is an L0 global asset that
-- appears in `ka_kshetra.depends_on` via migration 494's `UPDATE ... SET depends_on
-- = ARRAY[...]`, NOT via the TS seed's `ka_kshetra` row (which carries `[]` for the
-- reasons documented in asset_registry_seed.ts). This edge is added the same way.
--
-- Acyclic: L0 → L3, one direction only. §2.5.2's "L0 dependency not built" BLOCKED
-- state is the correct behaviour — the L0 asset must be built in production BEFORE
-- the first per-chart `ka_kshetra` build, exactly as for `bg_cohort`.
--
-- Appended (not replaced) so this migration cannot silently narrow the eight edges
-- migration 494 established, and guarded so a re-run does not duplicate the entry.

UPDATE asset_registry
   SET depends_on = COALESCE(depends_on, ARRAY[]::text[]) || ARRAY['bg_class_lifetime_counts']::text[]
 WHERE asset_id = 'ka_kshetra'
   AND NOT ('bg_class_lifetime_counts' = ANY(COALESCE(depends_on, ARRAY[]::text[])));

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   UPDATE asset_registry
--      SET depends_on = ARRAY(
--            SELECT e FROM unnest(depends_on) AS e WHERE e <> 'bg_class_lifetime_counts')
--    WHERE asset_id = 'ka_kshetra';
--   DELETE FROM asset_registry WHERE asset_id = 'bg_class_lifetime_counts';
--   DELETE FROM brahma_class_priors WHERE fact_kind = 'lifetime_count_per_100y';
--   ALTER TABLE brahma_class_priors DROP CONSTRAINT IF EXISTS brahma_class_priors_lifetime_basis_ck;
--   ALTER TABLE brahma_class_priors DROP COLUMN IF EXISTS source_ref;
--   ALTER TABLE brahma_class_priors DROP COLUMN IF EXISTS prior_basis;
--   COMMIT;
-- =============================================================================
