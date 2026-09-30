// @vitest-environment node
/**
 * Pravāha A5.1 round 2 — LIVE-DB contract suite for migrations 1153–1157 and
 * their preflights, executed against a REAL throwaway Postgres (CLAUDE.md
 * §N.8: the test runs the on-disk SQL itself, never a hand-copied re-
 * implementation). Sibling of kala_gochara_windows_generation_guard.db.test.ts.
 *
 * Covers ASTRA_REVIEW_A5_1_MIGRATIONS v1_0:
 *   - amendment 8 (a): fresh apply of 1153–1157 IN ORDER through the real
 *     runner (runMigrations from scripts/migrate.ts), then pg_catalog proof
 *     that every contracted constraint and trigger exists;
 *   - amendment 2 (b): a FORCED failure between DDL execution and ledger
 *     recording (a BEFORE INSERT trigger on _migrations_applied) leaves
 *     NOTHING persisted — no ka_gochara table, no ledger row;
 *   - amendment 8 (c): repeat execution is a verified no-op; a deliberately
 *     drifted same-named object fails the apply loudly;
 *   - amendments 1/3/4/5/6/7/9: behavioural fixtures — contact identity and
 *     lifecycle, membership FKs, typed support states, score/valence rules,
 *     correction/supersession, factor calibration discipline.
 *
 * The 1081 parents (charts / kala_gochara_publication / kala_gochara_coverage)
 * are represented by faithful key-shape stubs — the same stub idiom as the
 * sibling suite — because the interactions under test depend only on key
 * shape, and applying the full production chain is out of scope here.
 *
 * Requires a THROWAWAY database. Skipped unless GOCHARA_A51_TEST_DATABASE_URL
 * is set, and it refuses to run against anything not obviously disposable.
 *
 *   initdb -D /tmp/a51/pgdata -U postgres --auth=trust
 *   pg_ctl -D /tmp/a51/pgdata -o "-p 59531 -k /tmp/a51 -c listen_addresses=127.0.0.1" start
 *   createdb -h 127.0.0.1 -p 59531 -U postgres gochara_a51_test
 *   GOCHARA_A51_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:59531/gochara_a51_test \
 *     npx vitest run tests/integration/gochara_a5_1_migrations.db.test.ts
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import { copyFileSync, mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import path from 'node:path'
import { TRACKER_DDL, TRACKER_IDENTITY_DDL, runMigrations } from '../../scripts/migrate'

const TEST_DB_URL = process.env.GOCHARA_A51_TEST_DATABASE_URL

const MIGRATIONS_DIR = path.resolve(process.cwd(), 'migrations')
const PREFLIGHT_DIR = path.resolve(
  process.cwd(), '../platform/python-sidecar/scripts/kala_gochara_cutover',
)
const MIGRATION_FILES = [
  '1153_gochara_sky_event_substrate.sql',
  '1154_gochara_rule_path_registry.sql',
  '1155_gochara_relationship_record.sql',
  '1156_gochara_eval_window.sql',
  '1157_gochara_av_polarity_declaration.sql',
]
const PREFLIGHT_FILES = [
  'preflight_1153_sky_event_substrate.sql',
  'preflight_1154_rule_path_registry.sql',
  'preflight_1155_relationship_record.sql',
  'preflight_1156_eval_window.sql',
  'preflight_1157_av_polarity_declaration.sql',
]

const KA_TABLES = [
  'ka_gochara_sky_convention', 'ka_gochara_physical_object', 'ka_gochara_sky_event',
  'ka_gochara_contact', 'ka_gochara_predicate', 'ka_gochara_factor',
  'ka_gochara_rule_path', 'ka_gochara_rule_path_prerequisite',
  'ka_gochara_rule_path_soft_factor', 'ka_gochara_relationship_record',
  'ka_gochara_record_prerequisite', 'ka_gochara_eval_window',
  'ka_gochara_eval_window_record', 'ka_gochara_av_polarity_declaration',
]

// The constraint set the review contracted (amendment → constraint name).
const EXPECTED_CONSTRAINTS: Array<[string, string]> = [
  ['ka_gochara_sky_convention', 'kgsc_domain_ordered_ck'],
  ['ka_gochara_physical_object', 'kgpo_body_domain_ck'],
  ['ka_gochara_physical_object', 'kgpo_target_form_ck'],
  ['ka_gochara_physical_object', 'kgpo_identity_uq'],
  ['ka_gochara_sky_event', 'ka_gochara_sky_event_object_fk'],
  ['ka_gochara_sky_event', 'kgse_coverage_shape_ck'],
  ['ka_gochara_sky_event', 'kgse_exact_precision_ck'],
  ['ka_gochara_sky_event', 'kgse_station_refined_ck'],
  ['ka_gochara_sky_event', 'kgse_no_self_supersede_ck'],
  ['ka_gochara_sky_event', 'kgse_correction_edge_ck'],
  ['ka_gochara_contact', 'kgc_canonical_chart_ck'],
  ['ka_gochara_contact', 'ka_gochara_contact_ordinal_uq'],
  ['ka_gochara_contact', 'kgc_identity_uq'],
  ['ka_gochara_contact', 'kgc_t_out_unless_truncated_ck'],
  ['ka_gochara_contact', 'kgc_time_order_ck'],
  ['ka_gochara_predicate', 'kgp_unknown_is_false_ck'],
  ['ka_gochara_predicate', 'kgp_operands_typed_ck'],
  ['ka_gochara_factor', 'kgf_range_unit_interval_ck'],
  ['ka_gochara_factor', 'kgf_mapping_discipline_ck'],
  ['ka_gochara_rule_path', 'kgrp_frame_ck'],
  ['ka_gochara_rule_path', 'kgrp_ruling_ck'],
  ['ka_gochara_rule_path_prerequisite', 'kgrpp_predicate_fk'],
  ['ka_gochara_rule_path_soft_factor', 'kgrps_factor_fk'],
  ['ka_gochara_relationship_record', 'kgrr_contact_fk'],
  ['ka_gochara_relationship_record', 'kgrr_coverage_fk'],
  ['ka_gochara_relationship_record', 'kgrr_support_cardinality_ck'],
  ['ka_gochara_relationship_record', 'kgrr_transit_natal_ck'],
  ['ka_gochara_relationship_record', 'kgrr_relative_frame_ck'],
  ['ka_gochara_relationship_record', 'kgrr_citation_ck'],
  ['ka_gochara_relationship_record', 'kgrr_admission_state_ck'],
  ['ka_gochara_relationship_record', 'kgrr_identity_uq'],
  ['ka_gochara_record_prerequisite', 'kgrpr_predicate_fk'],
  ['ka_gochara_eval_window', 'kgew_score_unit_interval_ck'],
  ['ka_gochara_eval_window', 'kgew_interval_nonempty_ck'],
  ['ka_gochara_eval_window', 'kgew_peak_in_interval_ck'],
  ['ka_gochara_eval_window', 'kgew_identity_uq'],
  ['ka_gochara_eval_window_record', 'kgewr_window_fk'],
  ['ka_gochara_eval_window_record', 'kgewr_record_fk'],
  ['ka_gochara_av_polarity_declaration', 'kgav_categories_nonempty_ck'],
]

const EXPECTED_TRIGGERS: Array<[string, string]> = [
  ['ka_gochara_sky_convention', 'ka_gochara_sky_convention_immutable'],
  ['ka_gochara_physical_object', 'ka_gochara_physical_object_immutable'],
  ['ka_gochara_sky_event', 'ka_gochara_sky_event_supersede_check'],
  ['ka_gochara_sky_event', 'ka_gochara_sky_event_mutation_guard'],
  ['ka_gochara_contact', 'ka_gochara_contact_supersede_check'],
  ['ka_gochara_contact', 'ka_gochara_contact_lifecycle_guard'],
  ['ka_gochara_predicate', 'ka_gochara_predicate_immutable'],
  ['ka_gochara_factor', 'ka_gochara_factor_immutable'],
  ['ka_gochara_rule_path', 'ka_gochara_rule_path_immutable'],
  ['ka_gochara_rule_path_prerequisite', 'ka_gochara_rp_prereq_immutable'],
  ['ka_gochara_rule_path_soft_factor', 'ka_gochara_rp_soft_factor_immutable'],
  ['ka_gochara_av_polarity_declaration', 'ka_gochara_av_polarity_immutable'],
]

// ── Fixture ids ─────────────────────────────────────────────────────────────
const CHART = '482012f1-710e-4a25-994a-93821f5871aa' // the canonical chart (D-SCOPE)
const OTHER_CHART = '00000000-0000-4000-8000-0000000000aa'
const CONV = 'c0'
const GEN = '5.0'
const GEN_OLD = '4.1'
const OBJ_MARS = '10000000-0000-4000-8000-000000000001'
const CONTACT_1 = '10000000-0000-4000-8000-000000000011'
const CONTACT_2 = '10000000-0000-4000-8000-000000000012'
const CONTACT_3 = '10000000-0000-4000-8000-000000000013'
const CONTACT_TRUNC = '10000000-0000-4000-8000-000000000014'
const CONTACT_MOON = '10000000-0000-4000-8000-000000000015'
const OBJ_MOON = '10000000-0000-4000-8000-000000000002'
const EVENT_1 = '10000000-0000-4000-8000-000000000021'
const RECORD_1 = '10000000-0000-4000-8000-000000000031'
const RECORD_2 = '10000000-0000-4000-8000-000000000032'
const WINDOW_1 = '10000000-0000-4000-8000-000000000041'
const COV_KIND = 'body_target'
const COV_KEY = 'mars:conjunction'

function mig(name: string): string {
  return readFileSync(join(MIGRATIONS_DIR, name), 'utf8')
}
function preflight(name: string): string {
  return readFileSync(join(PREFLIGHT_DIR, name), 'utf8')
}

let pool: Pool

async function resetSchema(): Promise<void> {
  // Drop every object this suite or the migrations create; keep nothing.
  await pool.query(`
    DROP TABLE IF EXISTS ka_gochara_eval_window_record CASCADE;
    DROP TABLE IF EXISTS ka_gochara_eval_window CASCADE;
    DROP TABLE IF EXISTS ka_gochara_record_prerequisite CASCADE;
    DROP TABLE IF EXISTS ka_gochara_relationship_record CASCADE;
    DROP TABLE IF EXISTS ka_gochara_rule_path_soft_factor CASCADE;
    DROP TABLE IF EXISTS ka_gochara_rule_path_prerequisite CASCADE;
    DROP TABLE IF EXISTS ka_gochara_rule_path CASCADE;
    DROP TABLE IF EXISTS ka_gochara_factor CASCADE;
    DROP TABLE IF EXISTS ka_gochara_predicate CASCADE;
    DROP TABLE IF EXISTS ka_gochara_contact CASCADE;
    DROP TABLE IF EXISTS ka_gochara_sky_event CASCADE;
    DROP TABLE IF EXISTS ka_gochara_physical_object CASCADE;
    DROP TABLE IF EXISTS ka_gochara_sky_convention CASCADE;
    DROP TABLE IF EXISTS ka_gochara_av_polarity_declaration CASCADE;
    DROP TABLE IF EXISTS kala_gochara_coverage CASCADE;
    DROP TABLE IF EXISTS kala_gochara_publication CASCADE;
    DROP TABLE IF EXISTS charts CASCADE;
    DROP TABLE IF EXISTS _migrations_applied CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_sky_convention_no_mutation() CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_physical_object_no_mutation() CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_sky_event_supersede_guard() CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_sky_event_guard() CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_contact_supersede_guard() CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_contact_guard() CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_predicate_no_mutation() CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_factor_no_mutation() CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_rule_path_no_mutation() CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_membership_no_mutation() CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_av_polarity_no_mutation() CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_frame_ok(text, text) CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_string_array_ok(jsonb) CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_vocab_array_ok(jsonb, text[]) CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_object_selector_ok(jsonb) CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_named_operands_ok(jsonb) CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_precision_ok(jsonb) CASCADE;
    DROP FUNCTION IF EXISTS ka_gochara_intervals_ok(tstzrange[]) CASCADE;
    DROP FUNCTION IF EXISTS a51_block_ledger_insert() CASCADE;
  `)
  // Faithful key-shape stubs of the 1081 parents (see header).
  await pool.query(`
    CREATE TABLE charts (id UUID PRIMARY KEY);
    CREATE TABLE kala_gochara_publication (
      manifest_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      chart_id UUID NOT NULL,
      generation TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'candidate',
      UNIQUE (chart_id, generation)
    );
    CREATE TABLE kala_gochara_coverage (
      chart_id UUID NOT NULL,
      generation TEXT NOT NULL,
      partition_kind TEXT NOT NULL,
      partition_key TEXT NOT NULL,
      PRIMARY KEY (chart_id, generation, partition_kind, partition_key)
    );
  `)
  await pool.query(`INSERT INTO charts (id) VALUES ($1), ($2)`, [CHART, OTHER_CHART])
  await pool.query(TRACKER_DDL)
  await pool.query(TRACKER_IDENTITY_DDL)
}

// ── Fixture writers ─────────────────────────────────────────────────────────
async function seedConvention(): Promise<void> {
  await pool.query(
    `INSERT INTO ka_gochara_sky_convention
       (convention_id, ephemeris_generation, ayanamsha, node_convention, grid,
        method_version, domain_start, domain_end)
     VALUES ($1, 'de441', 'lahiri_chitrapaksha', 'mean', '1s', 'm1',
             '2025-01-01T00:00Z', '2026-01-01T00:00Z')`,
    [CONV],
  )
}

async function seedCoverageAndPublication(): Promise<void> {
  await pool.query(
    `INSERT INTO kala_gochara_publication (chart_id, generation, status)
     VALUES ($1, $2, 'candidate'), ($1, $3, 'candidate')`,
    [CHART, GEN, GEN_OLD],
  )
  await pool.query(
    `INSERT INTO kala_gochara_coverage (chart_id, generation, partition_kind, partition_key)
     VALUES ($1, $2, $4, $5), ($1, $3, $4, $5)`,
    [CHART, GEN, GEN_OLD, COV_KIND, COV_KEY],
  )
}

async function seedObject(id: string, body: string, target: string): Promise<void> {
  await pool.query(
    `INSERT INTO ka_gochara_physical_object
       (physical_object_id, body, relation_kind, canonical_target, convention_id)
     VALUES ($1, $2, 'conjunction', $3, $4)`,
    [id, body, target, CONV],
  )
}

const CONTACT_COLS = `contact_id, chart_id, generation, physical_object_id, convention_id,
  body, relation_kind, occurrence_ordinal, correction_seq, t_in, t_out, t_exact,
  solver_method, delta_lambda, delta_t, precision_regime, coverage, supersedes_contact_id`

async function seedContact(id: string, objectId: string, ordinal: number, opts: {
  body?: string, correctionSeq?: number, supersedes?: string | null,
  truncated?: boolean,
} = {}): Promise<void> {
  const truncated = opts.truncated ?? false
  await pool.query(
    `INSERT INTO ka_gochara_contact (${CONTACT_COLS})
     VALUES ($1, $2, $3, $4, $5, $6, 'conjunction', $7, $8,
             '2025-03-09T00:00Z',
             ${truncated ? 'NULL' : `'2025-03-11T00:00Z'`},
             ${truncated ? 'NULL' : `'2025-03-10T00:00Z'`},
             $9,
             ${truncated ? 'NULL' : '0.001'}, ${truncated ? 'NULL' : '60'},
             ${truncated ? 'NULL' : `'standard'`},
             $10::jsonb, $11)`,
    [
      id, CHART, GEN, objectId, CONV, opts.body ?? 'mars', ordinal,
      opts.correctionSeq ?? 0,
      truncated ? 'clipped_truncated' : 'swiss_refined',
      JSON.stringify({ truncated }),
      opts.supersedes ?? null,
    ],
  )
}

async function seedRegistries(): Promise<void> {
  await pool.query(
    `INSERT INTO ka_gochara_predicate (predicate_id, rule_version, operator, operands)
     VALUES ('q1', 'v1', 'eq', '{"left":"agent_longitude","right":"object_longitude"}')`,
  )
  await pool.query(
    `INSERT INTO ka_gochara_factor
       (factor_id, rule_version, operand_selector, direction, function,
        range_lower, range_upper, units, calibration_status, doctrine_ordering,
        category_mapping, null_state, effect)
     VALUES ('f1', 'v1', '{"operand":"dignity_of_transit_sign"}', 'higher_stronger',
             'step', 0, 1, 'unitless', 'uncalibrated_default',
             '["exaltation","own","friendly","neutral","inimical","debility"]',
             NULL, 'omit', 'declared effect text')`,
  )
  await pool.query(
    `INSERT INTO ka_gochara_rule_path
       (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set,
        object_selector, provenance, operator_role, ruling_ref, score_rule)
     VALUES ('P1', 'v1', 'dasha_lord', NULL, '["mars"]', '["conjunction"]',
             '[{"agent":"mars","relation":"conjunction","object_role":"karaka"}]',
             'verse_cited', 'scored', NULL, 'within_path_product')`,
  )
  await pool.query(
    `INSERT INTO ka_gochara_rule_path_prerequisite
       (path_id, rule_version, ordinal, predicate_id, predicate_rule_version)
     VALUES ('P1', 'v1', 1, 'q1', 'v1')`,
  )
}

const RECORD_COLS = `record_id, chart_id, generation, contact_id, event_class,
  affected_person, frame_kind, frame_arg, agent, relation, object_id, object_kind,
  object_role, path_id, rule_version, temporal_support_state, temporal_support_grain,
  temporal_support_intervals, coverage_partition_kind, coverage_partition_key,
  precision, source_text, source_page, source_fact_ids, fixture, provenance,
  operator_role, ruling_ref, admission_state, house_from_frame,
  evidence_for_occurrence, evidence_against_occurrence, outcome_valence_for_native,
  severity`

async function seedRecord(id: string, generation: string = GEN): Promise<void> {
  await pool.query(
    `INSERT INTO ka_gochara_relationship_record (${RECORD_COLS})
     VALUES ($1, $2, $3, $4, 'marriage', 'native', 'lagna', NULL, 'mars', 'conjunction',
             $5, 'degree_point', 'karaka', 'P1', 'v1', 'computed', 'day',
             ARRAY[tstzrange('2025-03-09T00:00Z','2025-03-11T00:00Z')]::tstzrange[],
             $6, $7,
             '{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb,
             'Phaladīpikā', 'PG249-250 (XX.34-38)', '["fact-1"]', false,
             'verse_cited', 'scored', NULL, 'admitted', 7, 0.8, NULL, 'favourable', NULL)`,
    [id, CHART, generation, CONTACT_1, OBJ_MARS, COV_KIND, COV_KEY],
  )
}

async function seedWindowWithMembership(): Promise<void> {
  await pool.query(
    `INSERT INTO ka_gochara_eval_window
       (window_id, chart_id, generation, event_class, path_id, rule_version,
        interval, peak_instant, score, evidence_for, evidence_against,
        outcome_valence_for_native, severity,
        coverage_partition_kind, coverage_partition_key, null_states_used)
     VALUES ($1, $2, $3, 'marriage', 'P1', 'v1',
             tstzrange('2025-03-01T00:00Z','2025-04-01T00:00Z'),
             '2025-03-10T00:00Z', 0.8, 0.8, NULL, 'favourable', NULL, $4, $5, '{}')`,
    [WINDOW_1, CHART, GEN, COV_KIND, COV_KEY],
  )
  await pool.query(
    `INSERT INTO ka_gochara_eval_window_record (window_id, record_id, chart_id, generation)
     VALUES ($1, $2, $3, $4)`,
    [WINDOW_1, RECORD_1, CHART, GEN],
  )
}

/** Full fixture stack, in FK order. */
async function seedFixtures(): Promise<void> {
  await seedConvention()
  await seedCoverageAndPublication()
  await seedObject(OBJ_MARS, 'mars', 'point:198.52')
  await seedObject(OBJ_MOON, 'moon', 'point:327.06')
  // O-RX-1 shape: one tuple, two contacts (direct pass + retrograde re-crossing)
  await seedContact(CONTACT_1, OBJ_MARS, 1)
  await seedContact(CONTACT_2, OBJ_MARS, 2)
  await seedContact(CONTACT_TRUNC, OBJ_MARS, 3, { truncated: true })
  await seedContact(CONTACT_MOON, OBJ_MOON, 1, { body: 'moon' })
  await seedRegistries()
  await seedRecord(RECORD_1)
  await seedWindowWithMembership()
}

async function tableExists(name: string): Promise<boolean> {
  const res = await pool.query<{ present: boolean }>(
    `SELECT to_regclass($1) IS NOT NULL AS present`, [`public.${name}`],
  )
  return res.rows[0]!.present
}

describe.skipIf(!TEST_DB_URL)('A5.1 migrations 1153–1157 (live disposable DB)', () => {
  beforeAll(async () => {
    if (!/gochara_a51_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'GOCHARA_A51_TEST_DATABASE_URL must point at a disposable database named ' +
        '`gochara_a51_test`. This suite creates and drops schema objects and must ' +
        'never run against production.',
      )
    }
    pool = new Pool({ connectionString: TEST_DB_URL })
    await resetSchema()
  })

  afterAll(async () => {
    if (!pool) return
    await resetSchema()
    await pool.end()
  })

  // ── Preflight gate semantics (amendment 8) ──────────────────────────────
  describe('preflights fail closed and open', () => {
    it('PF1153 passes on a clean, correctly-privileged target', async () => {
      await expect(pool.query(preflight(PREFLIGHT_FILES[0]!))).resolves.toBeDefined()
    })

    it('PF1153 ledger lookup is wildcard-safe: a 1153Z_ row does NOT block', async () => {
      await pool.query(
        `INSERT INTO _migrations_applied (filename, sha256) VALUES ('1153Z_decoy.sql', 'x')`,
      )
      await expect(pool.query(preflight(PREFLIGHT_FILES[0]!))).resolves.toBeDefined()
      await pool.query(`DELETE FROM _migrations_applied WHERE filename = '1153Z_decoy.sql'`)
    })

    it('PF1153 blocks when 1153 IS recorded in the ledger', async () => {
      await pool.query(
        `INSERT INTO _migrations_applied (filename, sha256)
         VALUES ('1153_gochara_sky_event_substrate.sql', 'x')`,
      )
      await expect(pool.query(preflight(PREFLIGHT_FILES[0])))
        .rejects.toThrow(/migration_already_applied/)
      await pool.query(
        `DELETE FROM _migrations_applied WHERE filename = '1153_gochara_sky_event_substrate.sql'`,
      )
    })

    it('PF1153 blocks on a colliding table name', async () => {
      await pool.query(`CREATE TABLE ka_gochara_contact (id int)`)
      await expect(pool.query(preflight(PREFLIGHT_FILES[0])))
        .rejects.toThrow(/table_already_exists/)
      await pool.query(`DROP TABLE ka_gochara_contact`)
    })

    it('PF1155 refuses to run before its prerequisite migrations are applied (ordered gate)', async () => {
      await expect(pool.query(preflight(PREFLIGHT_FILES[2])))
        .rejects.toThrow(/prerequisite_migration_not_applied|parent_table_missing/)
    })
  })

  // ── (a) Fresh apply through the real runner (amendment 8) ───────────────
  describe('(a) fresh apply of 1153–1157 in order via runMigrations', () => {
    it('applies all five and records them in the ledger', async () => {
      const dir = mkdtempSync(join(tmpdir(), 'gochara-a51-migrations-'))
      const client = await pool.connect()
      try {
        for (const f of MIGRATION_FILES) copyFileSync(join(MIGRATIONS_DIR, f), join(dir, f))
        const ran = await runMigrations(client, [dir], {
          disclosures: new Map(), renumberDisclosures: new Map(),
        })
        expect(ran).toEqual(MIGRATION_FILES)
      } finally {
        client.release()
        rmSync(dir, { recursive: true, force: true })
      }
      const ledger = await pool.query<{ filename: string }>(
        `SELECT filename FROM _migrations_applied ORDER BY filename`,
      )
      expect(ledger.rows.map(r => r.filename)).toEqual([...MIGRATION_FILES].sort())
    })

    it('every contracted constraint exists (pg_catalog proof)', async () => {
      const res = await pool.query<{ conrelid: string; conname: string }>(
        `SELECT conrelid::regclass::text AS conrelid, conname FROM pg_constraint
         WHERE conname = ANY($1)`, [EXPECTED_CONSTRAINTS.map(c => c[1])],
      )
      const present = new Set(res.rows.map(r => `${r.conrelid}.${r.conname}`))
      const missing = EXPECTED_CONSTRAINTS.filter(([t, c]) => !present.has(`${t}.${c}`))
      expect(missing).toEqual([])
    })

    it('every contracted trigger exists on its table', async () => {
      const res = await pool.query<{ relname: string; tgname: string }>(
        `SELECT c.relname, t.tgname FROM pg_trigger t
         JOIN pg_class c ON c.oid = t.tgrelid
         WHERE NOT t.tgisinternal AND t.tgname = ANY($1)`,
        [EXPECTED_TRIGGERS.map(t => t[1])],
      )
      const present = new Set(res.rows.map(r => `${r.relname}.${r.tgname}`))
      const missing = EXPECTED_TRIGGERS.filter(([t, g]) => !present.has(`${t}.${g}`))
      expect(missing).toEqual([])
    })

    it('after apply, every preflight blocks on migration_already_applied', async () => {
      for (const pf of PREFLIGHT_FILES) {
        await expect(pool.query(preflight(pf))).rejects.toThrow(/BLOCKED/)
      }
    })
  })

  // ── Behavioural fixtures (amendments 1/3/4/5/6/7/9) ─────────────────────
  describe('behavioural contract', () => {
    beforeAll(async () => {
      await seedFixtures()
    })

    it('amendment 1/O-RX-1: one physical object holds ordinals 1 and 2; a duplicate (object, ordinal, seq 0) is refused', async () => {
      const res = await pool.query(
        `SELECT occurrence_ordinal FROM ka_gochara_contact
         WHERE physical_object_id = $1 AND correction_seq = 0 ORDER BY 1`, [OBJ_MARS],
      )
      expect(res.rows.map(r => r.occurrence_ordinal)).toEqual([1, 2, 3])
      await expect(seedContact('10000000-0000-4000-8000-000000000019', OBJ_MARS, 1))
        .rejects.toThrow(/ka_gochara_contact_ordinal_uq/)
    })

    it('amendment 6: a correction supersedes the same tuple with seq+1; wrong-target, self- and double-supersession are refused', async () => {
      await seedContact(CONTACT_3, OBJ_MARS, 1, { correctionSeq: 1, supersedes: CONTACT_1 })
      await expect(
        seedContact('10000000-0000-4000-8000-00000000001a', OBJ_MARS, 2,
          { correctionSeq: 1, supersedes: CONTACT_1 }),
      ).rejects.toThrow(/supersede edge invalid|already superseded/)
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_contact (${CONTACT_COLS})
           VALUES ($1, $2, $3, $4, $5, 'mars', 'conjunction', 9, 1,
                   '2025-03-09T00:00Z', '2025-03-11T00:00Z', '2025-03-10T00:00Z',
                   'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}'::jsonb, $1)`,
          ['10000000-0000-4000-8000-00000000001b', CHART, GEN, OBJ_MARS, CONV],
        ),
      ).rejects.toThrow(/supersede edge invalid|kgc_no_self_supersede_ck/)
      await expect(
        seedContact('10000000-0000-4000-8000-00000000001c', OBJ_MARS, 1,
          { correctionSeq: 2, supersedes: CONTACT_1 }),
      ).rejects.toThrow(/supersede edge invalid/)
    })

    it('amendment 1/§N.3: candidate-generation DELETE is allowed (delete-then-insert); published is refused', async () => {
      await pool.query(`DELETE FROM ka_gochara_contact WHERE contact_id = $1`, [CONTACT_2])
      await seedContact(CONTACT_2, OBJ_MARS, 2) // re-inserted by the rebuild
      await pool.query(
        `UPDATE kala_gochara_publication SET status = 'published'
         WHERE chart_id = $1 AND generation = $2`, [CHART, GEN],
      )
      await expect(
        pool.query(`DELETE FROM ka_gochara_contact WHERE contact_id = $1`, [CONTACT_2]),
      ).rejects.toThrow(/publication-immutable/)
      await pool.query(
        `UPDATE kala_gochara_publication SET status = 'candidate'
         WHERE chart_id = $1 AND generation = $2`, [CHART, GEN],
      )
    })

    it('amendments 5/6: enrichment fills NULL/truncated fields in place; changing a published value is refused', async () => {
      // truncated → exact enrichment (same id, same ordinal — §6.1)
      await pool.query(
        `UPDATE ka_gochara_contact
         SET t_out = '2025-03-21T00:00Z', t_exact = '2025-03-20T00:00Z',
             solver_method = 'swiss_refined', delta_lambda = 0.001, delta_t = 60,
             precision_regime = 'standard', coverage = '{"truncated":false}'::jsonb
         WHERE contact_id = $1`, [CONTACT_TRUNC],
      )
      const enriched = await pool.query(
        `SELECT t_exact FROM ka_gochara_contact WHERE contact_id = $1`, [CONTACT_TRUNC],
      )
      expect(enriched.rows[0]!.t_exact).toBeTruthy()
      // ...but now that t_exact is published, changing it is a correction, not an UPDATE
      await expect(
        pool.query(
          `UPDATE ka_gochara_contact SET t_exact = '2025-03-22T00:00Z' WHERE contact_id = $1`,
          [CONTACT_TRUNC],
        ),
      ).rejects.toThrow(/published non-NULL values are immutable/)
      // identity fields are never mutable
      await expect(
        pool.query(
          `UPDATE ka_gochara_contact SET occurrence_ordinal = 4 WHERE contact_id = $1`,
          [CONTACT_TRUNC],
        ),
      ).rejects.toThrow(/identity fields are immutable/)
    })

    it('amendment 4: a transit record whose agent disagrees with its contact is refused', async () => {
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_relationship_record (${RECORD_COLS})
           VALUES ($1, $2, $3, $4, 'marriage', 'native', 'lagna', NULL, 'venus', 'conjunction',
                   $5, 'degree_point', 'karaka', 'P1', 'v1', 'computed', 'day',
                   ARRAY[tstzrange('2025-03-09T00:00Z','2025-03-11T00:00Z')]::tstzrange[],
                   $6, $7,
                   '{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb,
                   'Phaladīpikā', 'PG249-250 (XX.34-38)', '["fact-1"]', false,
                   'verse_cited', 'scored', NULL, 'admitted', 7, NULL, NULL, 'favourable', NULL)`,
          ['10000000-0000-4000-8000-000000000033', CHART, GEN, CONTACT_1, OBJ_MARS, COV_KIND, COV_KEY],
        ),
      ).rejects.toThrow(/kgrr_contact_fk/)
    })

    it('amendment 4: coverage is scope-bound — a record cannot point at another generation’s partition', async () => {
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_relationship_record (${RECORD_COLS})
           VALUES ($1, $2, $3, $4, 'marriage', 'native', 'lagna', NULL, 'mars', 'conjunction',
                   $5, 'degree_point', 'karaka', 'P1', 'v1', 'computed', 'day',
                   ARRAY[tstzrange('2025-03-09T00:00Z','2025-03-11T00:00Z')]::tstzrange[],
                   'event_class', 'marriage',
                   '{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb,
                   'Phaladīpikā', 'PG249-250 (XX.34-38)', '["fact-1"]', false,
                   'verse_cited', 'scored', NULL, 'admitted', 7, NULL, NULL, 'favourable', NULL)`,
          ['10000000-0000-4000-8000-000000000034', CHART, GEN, CONTACT_1, OBJ_MARS],
        ),
      ).rejects.toThrow(/kgrr_coverage_fk/)
    })

    it('amendment 5: transit rows require precision; natal rows forbid contact and precision', async () => {
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_relationship_record (${RECORD_COLS})
           VALUES ($1, $2, $3, $4, 'marriage', 'native', 'lagna', NULL, 'mars', 'conjunction',
                   $5, 'degree_point', 'karaka', 'P1', 'v1', 'computed', 'day',
                   ARRAY[tstzrange('2025-03-09T00:00Z','2025-03-11T00:00Z')]::tstzrange[],
                   $6, $7, NULL,
                   'Phaladīpikā', 'PG249-250 (XX.34-38)', '["fact-1"]', false,
                   'verse_cited', 'scored', NULL, 'admitted', 7, NULL, NULL, 'favourable', NULL)`,
          ['10000000-0000-4000-8000-000000000035', CHART, GEN, CONTACT_1, OBJ_MARS, COV_KIND, COV_KEY],
        ),
      ).rejects.toThrow(/kgrr_transit_natal_ck/)
    })

    it('amendment 5: temporal_support state/interval cardinality is enforced', async () => {
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_relationship_record (${RECORD_COLS})
           VALUES ($1, $2, $3, $4, 'marriage', 'native', 'lagna', NULL, 'mars', 'conjunction',
                   $5, 'degree_point', 'karaka', 'P1', 'v1', 'computed', 'day', '{}',
                   $6, $7,
                   '{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb,
                   'Phaladīpikā', 'PG249-250 (XX.34-38)', '["fact-1"]', false,
                   'verse_cited', 'scored', NULL, 'admitted', 7, NULL, NULL, 'favourable', NULL)`,
          ['10000000-0000-4000-8000-000000000036', CHART, GEN, CONTACT_1, OBJ_MARS, COV_KIND, COV_KEY],
        ),
      ).rejects.toThrow(/kgrr_support_cardinality_ck/)
    })

    it('amendment 5: valence is NOT NULL — unqualified is the declared honest state', async () => {
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_relationship_record (${RECORD_COLS})
           VALUES ($1, $2, $3, $4, 'marriage', 'native', 'lagna', NULL, 'mars', 'conjunction',
                   $5, 'degree_point', 'karaka', 'P1', 'v1', 'uncomputed', NULL, '{}',
                   $6, $7,
                   '{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb,
                   'Phaladīpikā', 'PG249-250 (XX.34-38)', '["fact-1"]', false,
                   'verse_cited', 'scored', NULL, 'unqualified', NULL, NULL, NULL, NULL, NULL)`,
          ['10000000-0000-4000-8000-000000000037', CHART, GEN, CONTACT_1, OBJ_MARS, COV_KIND, COV_KEY],
        ),
      ).rejects.toThrow(/null value in column "outcome_valence_for_native"/)
      // the same row WITH 'unqualified' persisted is accepted (S:103 recorded)
      await pool.query(
        `INSERT INTO ka_gochara_relationship_record (${RECORD_COLS})
         VALUES ($1, $2, $3, $4, 'marriage', 'native', 'lagna', NULL, 'mars', 'conjunction',
                 $5, 'degree_point', 'karaka', 'P1', 'v1', 'uncomputed', NULL, '{}',
                 $6, $7,
                 '{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb,
                 'Phaladīpikā', 'PG249-250 (XX.34-38)', '["fact-1"]', false,
                 'verse_cited', 'scored', NULL, 'unqualified', NULL, NULL, NULL,
                 'unqualified', NULL)`,
        ['10000000-0000-4000-8000-000000000037', CHART, GEN, CONTACT_1, OBJ_MARS, COV_KIND, COV_KEY],
      )
    })

    it('amendment 3: dangling predicate references are refused; evaluated results persist', async () => {
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_record_prerequisite
             (record_id, ordinal, predicate_id, predicate_rule_version, result)
           VALUES ($1, 1, 'q_missing', 'v1', NULL)`,
          [RECORD_1],
        ),
      ).rejects.toThrow(/kgrpr_predicate_fk/)
      await pool.query(
        `INSERT INTO ka_gochara_record_prerequisite
           (record_id, ordinal, predicate_id, predicate_rule_version, result)
         VALUES ($1, 1, 'q1', 'v1', 'unknown')`,
        [RECORD_1],
      )
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_record_prerequisite
             (record_id, ordinal, predicate_id, predicate_rule_version, result)
           VALUES ($1, 2, 'q1', 'v1', 'maybe')`,
          [RECORD_1],
        ),
      ).rejects.toThrow(/kgrpr_result_ck/)
    })

    it('amendment 3: window membership cannot cross chart or generation', async () => {
      await seedRecord(RECORD_2, GEN_OLD) // same shape, older generation
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_eval_window_record (window_id, record_id, chart_id, generation)
           VALUES ($1, $2, $3, $4)`,
          [WINDOW_1, RECORD_2, CHART, GEN],
        ),
      ).rejects.toThrow(/kgewr_record_fk/)
    })

    it('amendment 7: score is bounded [0,1] with NULL preserved; evidence is nonnegative', async () => {
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_eval_window
             (window_id, chart_id, generation, event_class, path_id, rule_version,
              interval, score, outcome_valence_for_native,
              coverage_partition_kind, coverage_partition_key, null_states_used)
           VALUES ($1, $2, $3, 'marriage', 'P1', 'v1',
                   tstzrange('2025-05-01','2025-06-01'), 1.5, 'favourable', $4, $5, '{}')`,
          ['10000000-0000-4000-8000-000000000042', CHART, GEN, COV_KIND, COV_KEY],
        ),
      ).rejects.toThrow(/kgew_score_unit_interval_ck/)
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_eval_window
             (window_id, chart_id, generation, event_class, path_id, rule_version,
              interval, score, evidence_for, outcome_valence_for_native,
              coverage_partition_kind, coverage_partition_key, null_states_used)
           VALUES ($1, $2, $3, 'marriage', 'P1', 'v1',
                   tstzrange('2025-05-01','2025-06-01'), 0.5, -1, 'favourable', $4, $5, '{}')`,
          ['10000000-0000-4000-8000-000000000042', CHART, GEN, COV_KIND, COV_KEY],
        ),
      ).rejects.toThrow(/kgew_evidence_for_nn_ck/)
      // NULL score with the unqualified valence is the honest state — accepted
      await pool.query(
        `INSERT INTO ka_gochara_eval_window
           (window_id, chart_id, generation, event_class, path_id, rule_version,
            interval, score, outcome_valence_for_native,
            coverage_partition_kind, coverage_partition_key, null_states_used)
         VALUES ($1, $2, $3, 'marriage', 'P1', 'v1',
                 tstzrange('2025-05-01','2025-06-01'), NULL, 'unqualified', $4, $5, '{unqualified}')`,
        ['10000000-0000-4000-8000-000000000042', CHART, GEN, COV_KIND, COV_KEY],
      )
    })

    it('amendment 7: empty intervals and out-of-interval peaks are refused', async () => {
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_eval_window
             (window_id, chart_id, generation, event_class, path_id, rule_version,
              interval, outcome_valence_for_native,
              coverage_partition_kind, coverage_partition_key, null_states_used)
           VALUES ($1, $2, $3, 'marriage', 'P1', 'v1', 'empty'::tstzrange,
                   'favourable', $4, $5, '{}')`,
          ['10000000-0000-4000-8000-000000000043', CHART, GEN, COV_KIND, COV_KEY],
        ),
      ).rejects.toThrow(/kgew_interval_nonempty_ck/)
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_eval_window
             (window_id, chart_id, generation, event_class, path_id, rule_version,
              interval, peak_instant, outcome_valence_for_native,
              coverage_partition_kind, coverage_partition_key, null_states_used)
           VALUES ($1, $2, $3, 'marriage', 'P1', 'v1',
                   tstzrange('2025-03-01','2025-04-01'), '2025-05-01T00:00Z',
                   'favourable', $4, $5, '{}')`,
          ['10000000-0000-4000-8000-000000000043', CHART, GEN, COV_KIND, COV_KEY],
        ),
      ).rejects.toThrow(/kgew_peak_in_interval_ck/)
    })

    it('amendment 9: typed frame args; a relative never reads the native Moon frame', async () => {
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_rule_path
             (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set,
              object_selector, provenance, operator_role, score_rule)
           VALUES ('P2', 'v1', 'graha', 'pluto', '["mars"]', '["conjunction"]',
                   '[{"agent":"mars","relation":"conjunction","object_role":"karaka"}]',
                   'verse_cited', 'scored', 'within_path_product')`,
        ),
      ).rejects.toThrow(/kgrp_frame_ck/)
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_relationship_record (${RECORD_COLS})
           VALUES ($1, $2, $3, $4, 'bereavement', 'father', 'moon', NULL, 'mars', 'conjunction',
                   $5, 'degree_point', 'karaka', 'P1', 'v1', 'computed', 'day',
                   ARRAY[tstzrange('2025-03-09T00:00Z','2025-03-11T00:00Z')]::tstzrange[],
                   $6, $7,
                   '{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb,
                   'Phaladīpikā', 'PG249-250 (XX.34-38)', '["fact-1"]', false,
                   'verse_cited', 'scored', NULL, 'admitted', NULL, NULL, NULL, 'adverse', NULL)`,
          ['10000000-0000-4000-8000-000000000038', CHART, GEN, CONTACT_1, OBJ_MARS, COV_KIND, COV_KEY],
        ),
      ).rejects.toThrow(/kgrr_relative_frame_ck/)
    })

    it('amendment 9: ruling rule matches the frozen wording; verse_cited requires its citation', async () => {
      // uncited_extension without a ruling is refused…
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_rule_path
             (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set,
              object_selector, provenance, operator_role, ruling_ref, score_rule)
           VALUES ('P4', 'v1', 'lagna', NULL, '["jupiter","saturn"]',
                   '["residence","aspect","conjunction"]',
                   '[{"agent":"jupiter","relation":"residence","object_role":"signature_house"}]',
                   'uncited_extension', 'scored', NULL, 'within_path_product')`,
        ),
      ).rejects.toThrow(/kgrp_ruling_ck/)
      // …with a ruling it is accepted…
      await pool.query(
        `INSERT INTO ka_gochara_rule_path
           (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set,
            object_selector, provenance, operator_role, ruling_ref, score_rule)
         VALUES ('P4', 'v1', 'lagna', NULL, '["jupiter","saturn"]',
                 '["residence","aspect","conjunction"]',
                 '[{"agent":"jupiter","relation":"residence","object_role":"signature_house"}]',
                 'uncited_extension', 'scored', 'D-P4', 'within_path_product')`,
      )
      // …and a verse_cited SCORED row carrying a ruling ref is NOT forbidden
      // (the frozen wording never forbids it — the round-1 biconditional did)
      await pool.query(
        `INSERT INTO ka_gochara_rule_path
           (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set,
            object_selector, provenance, operator_role, ruling_ref, score_rule)
         VALUES ('P2', 'v1', 'moon', NULL, '["saturn"]', '["residence"]',
                 '[{"agent":"saturn","relation":"residence","object_role":"occupant"}]',
                 'verse_cited', 'scored', 'M-8', 'within_path_product')`,
      )
    })

    it('amendment 7 (steward ruling): factor mapping discipline — calibrated needs a mapping; uncalibrated carries ordering only', async () => {
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_factor
             (factor_id, rule_version, operand_selector, direction, function,
              range_lower, range_upper, units, calibration_status, null_state, effect)
           VALUES ('f2', 'v1', '{"operand":"x"}', 'higher_stronger', 'linear',
                   0, 1, 'degrees', 'calibrated', 'omit', 'e')`,
        ),
      ).rejects.toThrow(/kgf_mapping_discipline_ck/)
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_factor
             (factor_id, rule_version, operand_selector, direction, function,
              range_lower, range_upper, units, calibration_status, doctrine_ordering,
              category_mapping, null_state, effect)
           VALUES ('f2', 'v1', '{"operand":"x"}', 'higher_stronger', 'linear',
                   0, 1, 'degrees', 'uncalibrated_default', '["a","b"]',
                   '{"a":1.0}'::jsonb, 'omit', 'e')`,
        ),
      ).rejects.toThrow(/kgf_mapping_discipline_ck/)
      // range beyond [0,1] refused
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_factor
             (factor_id, rule_version, operand_selector, direction, function,
              range_lower, range_upper, units, calibration_status, doctrine_ordering,
              null_state, effect)
           VALUES ('f2', 'v1', '{"operand":"x"}', 'higher_stronger', 'linear',
                   0, 1.5, 'degrees', 'uncalibrated_default', '["a","b"]', 'omit', 'e')`,
        ),
      ).rejects.toThrow(/kgf_range_unit_interval_ck/)
    })

    it('amendment 9/D-SCOPE: the canonical-chart CHECK binds every per-chart table', async () => {
      await expect(seedContact('10000000-0000-4000-8000-00000000001d', OBJ_MARS, 4)
        // seedContact always uses CHART; write the wrong-chart insert explicitly
      ).resolves.toBeUndefined()
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_contact (${CONTACT_COLS})
           VALUES ($1, $2, $3, $4, $5, 'mars', 'conjunction', 5, 0,
                   '2025-03-09T00:00Z', '2025-03-11T00:00Z', '2025-03-10T00:00Z',
                   'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}'::jsonb, NULL)`,
          ['10000000-0000-4000-8000-00000000001e', OTHER_CHART, GEN, OBJ_MARS, CONV],
        ),
      ).rejects.toThrow(/kgc_canonical_chart_ck/)
    })

    it('amendment 9: source_fact_ids element types; [] only on fixtures', async () => {
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_relationship_record (${RECORD_COLS})
           VALUES ($1, $2, $3, $4, 'marriage', 'native', 'lagna', NULL, 'mars', 'conjunction',
                   $5, 'degree_point', 'karaka', 'P1', 'v1', 'computed', 'day',
                   ARRAY[tstzrange('2025-03-09T00:00Z','2025-03-11T00:00Z')]::tstzrange[],
                   $6, $7,
                   '{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb,
                   'Phaladīpikā', 'PG249-250 (XX.34-38)', '[null]', false,
                   'verse_cited', 'scored', NULL, 'admitted', 7, NULL, NULL, 'favourable', NULL)`,
          ['10000000-0000-4000-8000-000000000039', CHART, GEN, CONTACT_1, OBJ_MARS, COV_KIND, COV_KEY],
        ),
      ).rejects.toThrow(/kgrr_source_fact_ids_ck/)
    })

    it('O-SS-4 disposition: no materialised Moon rows in the sky-event substrate; per-chart Moon contacts allowed', async () => {
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_sky_event
             (event_id, physical_object_id, convention_id, body, event_kind,
              occurrence_ordinal, t_exact, longitude, solver_method,
              delta_lambda, delta_t, precision_regime, coverage)
           VALUES ($1, $2, $3, 'moon', 'sign_ingress', 1, '2025-03-10T00:00Z', 100.0,
                   'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}'::jsonb)`,
          ['10000000-0000-4000-8000-000000000022', OBJ_MOON, CONV],
        ),
      ).rejects.toThrow(/kgse_body_domain_ck/)
      const moon = await pool.query(
        `SELECT COUNT(*)::int AS n FROM ka_gochara_contact WHERE body = 'moon'`,
      )
      expect(moon.rows[0]!.n).toBe(1) // the per-chart Moon-on-demand fixture stands
    })

    it('amendment 5: an exact sky event carries its uncertainties; a station is Swiss-refined', async () => {
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_sky_event
             (event_id, physical_object_id, convention_id, body, event_kind,
              occurrence_ordinal, t_exact, longitude, solver_method, coverage)
           VALUES ($1, $2, $3, 'mars', 'sign_ingress', 1, '2025-03-10T00:00Z', 198.52,
                   'swiss_refined', '{"truncated":false}'::jsonb)`,
          ['10000000-0000-4000-8000-000000000023', OBJ_MARS, CONV],
        ),
      ).rejects.toThrow(/kgse_exact_precision_ck/)
      await expect(
        pool.query(
          `INSERT INTO ka_gochara_sky_event
             (event_id, physical_object_id, convention_id, body, event_kind,
              occurrence_ordinal, t_exact, longitude, solver_method,
              delta_lambda, delta_t, precision_regime, coverage)
           VALUES ($1, $2, $3, 'mars', 'station', 1, '2025-06-15T00:00Z', 198.52,
                   'arc_index_bracket', 0.001, 60, 'standard', '{"truncated":false}'::jsonb)`,
          ['10000000-0000-4000-8000-000000000024', OBJ_MARS, CONV],
        ),
      ).rejects.toThrow(/kgse_station_refined_ck/)
      // a conforming event inserts, and DELETE is forbidden outright
      await pool.query(
        `INSERT INTO ka_gochara_sky_event
           (event_id, physical_object_id, convention_id, body, event_kind,
            occurrence_ordinal, t_exact, longitude, solver_method,
            delta_lambda, delta_t, precision_regime, coverage)
         VALUES ($1, $2, $3, 'mars', 'sign_ingress', 1, '2025-03-10T00:00Z', 198.52,
                 'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}'::jsonb)`,
        [EVENT_1, OBJ_MARS, CONV],
      )
      await expect(
        pool.query(`DELETE FROM ka_gochara_sky_event WHERE event_id = $1`, [EVENT_1]),
      ).rejects.toThrow(/publication-immutable/)
    })

    it('registries are insert-only (§2.1 amendment 1)', async () => {
      await expect(
        pool.query(`UPDATE ka_gochara_rule_path SET score_rule = 'x' WHERE path_id = 'P1'`),
      ).rejects.toThrow(/insert-only/)
      await expect(
        pool.query(`DELETE FROM ka_gochara_predicate WHERE predicate_id = 'q1'`),
      ).rejects.toThrow(/insert-only/)
    })

    it('§N.3 rebuild ordering: deleting records/windows cascades membership, never blocks', async () => {
      await pool.query(`DELETE FROM ka_gochara_eval_window WHERE window_id = $1`, [WINDOW_1])
      const membership = await pool.query(
        `SELECT COUNT(*)::int AS n FROM ka_gochara_eval_window_record WHERE record_id = $1`,
        [RECORD_1],
      )
      expect(membership.rows[0]!.n).toBe(0)
      // and a record delete cascades its prerequisite membership
      await pool.query(`DELETE FROM ka_gochara_relationship_record WHERE record_id = $1`, [RECORD_1])
      const prereqs = await pool.query(
        `SELECT COUNT(*)::int AS n FROM ka_gochara_record_prerequisite WHERE record_id = $1`,
        [RECORD_1],
      )
      expect(prereqs.rows[0]!.n).toBe(0)
    })
  })

  // ── (c) Repeat execution and drifted objects (amendment 8) ──────────────
  describe('(c) repeat execution and drifted-object outcomes', () => {
    it('re-applying migration 1153 is a verified no-op; guards stay armed', async () => {
      await expect(pool.query(mig('1153_gochara_sky_event_substrate.sql'))).resolves.toBeDefined()
      const res = await pool.query<{ n: string }>(
        `SELECT COUNT(*)::text AS n FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
         WHERE c.relname = 'ka_gochara_contact' AND NOT t.tgisinternal`,
      )
      expect(res.rows[0]!.n).toBe('2')
      await expect(
        pool.query(`UPDATE ka_gochara_sky_convention SET grid = 'x' WHERE convention_id = $1`, [CONV]),
      ).rejects.toThrow(/insert-only/)
    })

    it('a drifted same-named table fails the apply loudly (never silently adopted)', async () => {
      await pool.query(`DROP TABLE ka_gochara_av_polarity_declaration CASCADE`)
      await pool.query(
        `CREATE TABLE ka_gochara_av_polarity_declaration (
           convention TEXT PRIMARY KEY,
           benefic_mark_name TEXT NOT NULL,
           malefic_mark_name TEXT NOT NULL,
           applies_to_fact_categories TEXT[] NOT NULL
         )`,
      ) // drifted: source_ref missing
      await expect(pool.query(mig('1157_gochara_av_polarity_declaration.sql')))
        .rejects.toThrow(/post-DDL verification failed/)
      // recover: drop the drift and apply cleanly
      await pool.query(`DROP TABLE ka_gochara_av_polarity_declaration`)
      await pool.query(mig('1157_gochara_av_polarity_declaration.sql'))
    })
  })

  // ── (b) Forced failure between DDL and ledger (amendment 2) ─────────────
  describe('(b) atomicity: failure between DDL and ledger recording persists nothing', () => {
    beforeAll(async () => {
      await resetSchema()
      // A ledger that refuses the tracking insert — the failure the review
      // named (committed DDL without its tracking row).
      await pool.query(`
        CREATE FUNCTION a51_block_ledger_insert() RETURNS trigger LANGUAGE plpgsql AS $f$
        BEGIN
          RAISE EXCEPTION 'a51 forced ledger failure (amendment 2 test)';
        END;
        $f$;
        CREATE TRIGGER a51_block_ledger
          BEFORE INSERT ON _migrations_applied
          FOR EACH ROW EXECUTE FUNCTION a51_block_ledger_insert();
      `)
    })

    it('runMigrations throws and NO ka_gochara object or ledger row survives', async () => {
      const dir = mkdtempSync(join(tmpdir(), 'gochara-a51-migrations-'))
      try {
        for (const f of MIGRATION_FILES) copyFileSync(join(MIGRATIONS_DIR, f), join(dir, f))
        const client = await pool.connect()
        try {
          await expect(
            runMigrations(client, [dir], {
              disclosures: new Map(), renumberDisclosures: new Map(),
            }),
          ).rejects.toThrow(/a51 forced ledger failure/)
        } finally {
          client.release()
        }
      } finally {
        rmSync(dir, { recursive: true, force: true })
      }
      for (const table of KA_TABLES) {
        expect(await tableExists(table)).toBe(false)
      }
      const ledger = await pool.query<{ n: string }>(
        `SELECT COUNT(*)::text AS n FROM _migrations_applied`,
      )
      expect(ledger.rows[0]!.n).toBe('0')
    })
  })
})
