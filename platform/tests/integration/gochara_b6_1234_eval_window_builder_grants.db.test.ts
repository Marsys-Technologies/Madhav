// @vitest-environment node
/**
 * Pravāha B6.0 / Codex round 8 R8-10 + Stream A relay M20261002T034924-82ce — migration 1234: the builder's EVAL-WINDOW write-path
 * grants (grants only), DERIVED by running the window writer's statements AS data_plane_builder under a deployment-faithful role mirror
 * (objects owned by `amjis_app`, PUBLIC EXECUTE revoked by default — nirmana-evidence-ownership-preflight.ts:259), the 1206-R6 method:
 * apply, run, add one grant per `permission denied …` until it converges; this suite re-proves the convergence and is the detector.
 *
 * Fixtures and writers are the A5.1 suite's (generated helper section; the same one the 1233 suite uses). 1216 + 1220 (the grants
 * production already holds) are applied first; the window write is attempted BEFORE 1234 (it must fail) and AFTER (it must pass),
 * and the matrix of what the builder must NOT be able to do is asserted.
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool, type PoolClient } from 'pg'
import { copyFileSync, mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import path from 'node:path'
import { TRACKER_DDL, TRACKER_IDENTITY_DDL, runMigrations } from '../../scripts/migrate'
import { resolveDisposableA51Config } from './gochara_a5_1_disposable_url'

const TEST_DB_URL = process.env.GOCHARA_A51_TEST_DATABASE_URL

const MIGRATIONS_DIR = path.resolve(process.cwd(), 'migrations')
const PREFLIGHT_DIR = path.resolve(process.cwd(), '../platform/python-sidecar/scripts/kala_gochara_cutover')
const M1216 = '1216_gochara_contract_builder_grants.sql'
const M1220 = '1220_gochara_contract_builder_function_execute.sql'
const M1234 = '1234_gochara_eval_window_builder_grants.sql'
const MIGRATION_FILES = [
  '1153_gochara_sky_event_substrate.sql',
  '1154_gochara_rule_path_registry.sql',
  '1155_gochara_relationship_record.sql',
  '1156_gochara_eval_window.sql',
  '1157_gochara_av_polarity_declaration.sql',
] as const
const PREFLIGHT_FILES = [
  'preflight_1153_sky_event_substrate.sql',
  'preflight_1154_rule_path_registry.sql',
  'preflight_1155_relationship_record.sql',
  'preflight_1156_eval_window.sql',
  'preflight_1157_av_polarity_declaration.sql',
] as const
const PARENT_FILES = [
  '1081_nirmana_l3_gochara_ledger_coverage_publication.sql',
  '1087_nirmana_l3_gochara_contacts_inclusivity_completeness_tier_basis.sql',
  '1152_kala_gochara_contacts_t_exact_nullable_truncated.sql',
] as const
const LEGACY_TABLES = ['charts', 'kala_gochara_convention', 'kala_gochara_publication', 'kala_gochara_coverage', 'kala_gochara_contacts'] as const

// ── Fixture ids ─────────────────────────────────────────────────────────────
const CHART = '482012f1-710e-4a25-994a-93821f5871aa' // the canonical chart (D-SCOPE)
const OTHER_CHART = '00000000-0000-4000-8000-0000000000aa'
const CONV = 'c0'
const CONV2 = 'c1'
const LEGACY_CONV = 'legacy:c0'
const LEGACY_CONV_UNBRIDGED = 'legacy:c9'
const GEN = '5.0'      // published + sealed during the suite (frozen set)
const GEN_C = '5.1'    // candidate: owns CID_OLD_ONLY only
const GEN_R = '5.2'    // concurrency: rebuild first, then publish
const GEN_P = '5.3'    // concurrency: publish first, then rebuild
const GEN_F = '5.4'    // finalisation + negative cases: never published
const GEN_N = '5.5'    // N7: truncated contact + record, sealed, then enriched
const GEN_S = '5.6'    // §N.3 cascade + isolation + lock-behind-orchestrator
const GEN_X = '5.7'    // N6 variations
const GEN_D = '5.8'    // N10 consumer contract: drift classification + seal refusal
const GEN_L = '5.9'    // N12/N13: real runner topology + lock interleavings (two ledger rows)
const GEN_M = '6.0'    // N16: valid membership → parent update → seal refused
const GEN_I = '6.1'    // N17: partition drifts to an infinite horizon → seal refused
const LEGACY_GEN = '4.0'
const OBJ_MARS = '10000000-0000-4000-8000-000000000001'
const OBJ_MOON = '10000000-0000-4000-8000-000000000002'
const OBJ_MARS_ASPECT = '10000000-0000-4000-8000-000000000003'
const OBJ_MARS_C1 = '10000000-0000-4000-8000-000000000004'
const OBJ_MARS_T2 = '10000000-0000-4000-8000-000000000005'
const OBJ_SAT_CONJ = '10000000-0000-4000-8000-000000000006'
const OBJ_SAT_SPAN = '10000000-0000-4000-8000-000000000007'
const OBJ_MARS_SPAN = '10000000-0000-4000-8000-000000000008'
const CID_1 = '10000000-0000-4000-8000-000000000011'         // (OBJ_MARS, 1)
const CID_2 = '10000000-0000-4000-8000-000000000012'         // (OBJ_MARS, 2)
const CID_TRUNC = '10000000-0000-4000-8000-000000000013'     // (OBJ_MARS, 3) truncated
const CID_LATE = '10000000-0000-4000-8000-000000000014'      // (OBJ_MARS, 4) t_in 2025-02-01
const CID_OLD_ONLY = '10000000-0000-4000-8000-000000000015'  // (OBJ_MARS, 5) owned by 5.1 only
const CID_R = '10000000-0000-4000-8000-000000000016'         // (OBJ_MARS, 6) 5.2
const CID_P = '10000000-0000-4000-8000-000000000017'         // (OBJ_MARS, 7) 5.3
const CID_T2 = '10000000-0000-4000-8000-000000000018'        // (OBJ_MARS, 8) truncated, 5.5
const CID_MOON = '10000000-0000-4000-8000-000000000019'      // (OBJ_MOON, 1)
const EVENT_1 = '10000000-0000-4000-8000-000000000021'
const RECORD_1 = '10000000-0000-4000-8000-000000000031'
const WINDOW_1 = '10000000-0000-4000-8000-000000000041'
const COV_KIND = 'body_target'
const COV_KEY = 'mars:karaka'
const HORIZON = "tstzrange('2025-01-01T00:00Z','2026-01-01T00:00Z','[)')"
const SUPPORT = "ARRAY[tstzrange('2025-03-09T00:00Z','2025-03-11T00:00Z')]::tstzrange[]"

let seq = 0
const ANCHOR_COLS = false        // the anchor columns exist only after 1233 is applied
const uuid = (): string => `20000000-0000-4000-8000-${String(++seq).padStart(12, '0')}`

function mig(name: string): string {
  return readFileSync(join(MIGRATIONS_DIR, name), 'utf8')
}
function preflight(name: string): string {
  return readFileSync(join(PREFLIGHT_DIR, name), 'utf8')
}
const sleep = (ms: number) => new Promise(r => setTimeout(r, ms))
/** 'pending' if `p` has not settled within `ms` (either way), else 'settled'. */
async function settledWithin(p: Promise<unknown>, ms = 500): Promise<'settled' | 'pending'> {
  return Promise.race([p.then(() => 'settled' as const, () => 'settled' as const), sleep(ms).then(() => 'pending' as const)])
}

let pool: Pool
type Q = Pick<PoolClient, 'query'>

/** One explicit transaction — the ATOMIC write boundary at which deferred checks run. */
async function tx<T>(fn: (c: PoolClient) => Promise<T>): Promise<T> {
  const c = await pool.connect()
  try {
    await c.query('BEGIN')
    const r = await fn(c)
    await c.query('COMMIT')
    return r
  } catch (err) {
    await c.query('ROLLBACK').catch(() => undefined)
    throw err
  } finally {
    c.release()
  }
}

async function dropRole(): Promise<void> {
  await pool.query(`DO $d$ BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'a51_app') THEN
      EXECUTE 'DROP OWNED BY a51_app CASCADE';
      EXECUTE 'DROP ROLE a51_app';
    END IF;
  END $d$`)
}

async function resetSchema(): Promise<void> {
  await pool.query(`
    DROP TABLE IF EXISTS ka_gochara_eval_window_record CASCADE;
    DROP TABLE IF EXISTS ka_gochara_eval_window CASCADE;
    DROP TABLE IF EXISTS ka_gochara_record_prerequisite CASCADE;
    DROP TABLE IF EXISTS ka_gochara_relationship_record CASCADE;
    DROP TABLE IF EXISTS ka_gochara_rule_path_seal CASCADE;
    DROP TABLE IF EXISTS ka_gochara_rule_path_soft_factor CASCADE;
    DROP TABLE IF EXISTS ka_gochara_rule_path_prerequisite CASCADE;
    DROP TABLE IF EXISTS ka_gochara_rule_path CASCADE;
    DROP TABLE IF EXISTS ka_gochara_factor CASCADE;
    DROP TABLE IF EXISTS ka_gochara_predicate CASCADE;
    DROP TABLE IF EXISTS ka_gochara_contact CASCADE;
    DROP TABLE IF EXISTS ka_gochara_convention_bridge CASCADE;
    DROP TABLE IF EXISTS ka_gochara_generation_seal CASCADE;
    DROP TABLE IF EXISTS ka_gochara_contact_identity CASCADE;
    DROP TABLE IF EXISTS ka_gochara_sky_event CASCADE;
    DROP TABLE IF EXISTS ka_gochara_physical_object CASCADE;
    DROP TABLE IF EXISTS ka_gochara_sky_convention CASCADE;
    DROP TABLE IF EXISTS ka_gochara_av_polarity_declaration CASCADE;
    DROP TABLE IF EXISTS kala_gochara_contacts CASCADE;
    DROP TABLE IF EXISTS kala_gochara_coverage CASCADE;
    DROP TABLE IF EXISTS kala_gochara_publication CASCADE;
    DROP TABLE IF EXISTS kala_gochara_convention CASCADE;
    DROP TABLE IF EXISTS charts CASCADE;
    DROP TABLE IF EXISTS _migrations_applied CASCADE;
    DROP FUNCTION IF EXISTS kala_gochara_convention_no_mutation() CASCADE;
    DROP FUNCTION IF EXISTS a51_block_ledger_insert() CASCADE;
    DO $d$
    DECLARE r record;
    BEGIN
      FOR r IN SELECT p.oid::regprocedure AS sig FROM pg_proc p
               JOIN pg_namespace n ON n.oid = p.pronamespace
               WHERE n.nspname = 'public' AND p.proname LIKE 'ka\\_gochara\\_%'
      LOOP
        EXECUTE 'DROP FUNCTION IF EXISTS ' || r.sig::text || ' CASCADE';
      END LOOP;
    END $d$;
  `)
  await pool.query(`CREATE TABLE charts (id UUID PRIMARY KEY DEFAULT gen_random_uuid())`)
  for (const f of PARENT_FILES) await pool.query(mig(f))
  await pool.query(`INSERT INTO charts (id) VALUES ($1), ($2)`, [CHART, OTHER_CHART])
  await pool.query(TRACKER_DDL)
  await pool.query(TRACKER_IDENTITY_DDL)
}

/** The normalised runtime/migration role: USAGE on public, owner of the application tables, NO CREATE. */
async function createAppRole(): Promise<void> {
  await dropRole()
  await pool.query(`CREATE ROLE a51_app NOLOGIN`)
  await pool.query(`REVOKE CREATE ON SCHEMA public FROM PUBLIC`)
  await pool.query(`GRANT USAGE ON SCHEMA public TO a51_app`)
  for (const t of [...LEGACY_TABLES, '_migrations_applied']) await pool.query(`ALTER TABLE ${t} OWNER TO a51_app`)
}

// ── Fixture writers ─────────────────────────────────────────────────────────
async function seedLegacyConvention(c: Q, id: string): Promise<void> {
  await c.query(
    `INSERT INTO kala_gochara_convention
       (convention_id, zodiac, ayanamsha, sidereal_method, node_model, node_source,
        epoch_convention, time_scale, house_system, ephemeris_mode, method_version)
     VALUES ($1, 'sidereal', 'lahiri_chitrapaksha', 'true_chitra', 'mean', 'swiss',
             'j2000', 'utc', 'whole_sign', 'swiss', '1.0')`, [id],
  )
}
async function seedSkyConvention(c: Q, id: string, method = 'm1'): Promise<void> {
  await c.query(
    `INSERT INTO ka_gochara_sky_convention
       (convention_id, ephemeris_generation, ayanamsha, node_convention, grid,
        method_version, domain_start, domain_end)
     VALUES ($1, 'de441', 'lahiri_chitrapaksha', 'mean', '1s', $2,
             '2025-01-01T00:00Z', '2026-01-01T00:00Z')`, [id, method],
  )
}
async function seedPublication(c: Q, generation: string, status = 'candidate'): Promise<string> {
  const r = await c.query<{ manifest_id: string }>(
    `INSERT INTO kala_gochara_publication
       (chart_id, generation, writer_asset_id, convention_id, input_generation_vector,
        ephemeris_backend, horizon, row_counts, content_digest, status)
     VALUES ($1, $2, 'ka_gochara', $3, '{}', '{}', ${HORIZON}, '{}', 'digest', $4)
     RETURNING manifest_id`,
    [CHART, generation, LEGACY_CONV, status],
  )
  return r.rows[0]!.manifest_id
}
async function seedCoverage(c: Q, o: {
  generation: string; kind: string; key: string; conv?: string;
  relationsSql?: string; completed?: string;
}): Promise<void> {
  await c.query(
    `INSERT INTO kala_gochara_coverage
       (chart_id, generation, partition_kind, partition_key, convention_id,
        requested_horizon, completed_horizon, resolution, relations_searched,
        targets_requested, targets_resolved, targets_unresolved,
        target_resolution_state_counts, build_id)
     VALUES ($1, $2, $3, $4, $5, ${HORIZON}, ${o.completed ?? HORIZON}, 1.0,
             ${o.relationsSql ?? `ARRAY['conjunction','aspect','residence']::text[]`}, 1, 1, 0,
             '{"resolved":1}', 'build-a51')`,
    [CHART, o.generation, o.kind, o.key, o.conv ?? LEGACY_CONV],
  )
}
async function seedLegacyContact(c: Q, manifestId: string): Promise<void> {
  await c.query(
    `INSERT INTO kala_gochara_contacts
       (chart_id, generation, contact_id, independence_group, body, relation, aspect_deg,
        target_type, target_ref, target_fact_id, target_resolution_state, target_longitude_deg,
        t_in, t_exact, t_out, bracket_seconds, tolerance_arcsec, branch, station_flag,
        exact_crossing, orb_max_deg, orb_source, epistemic_class, completeness_state,
        operator_role, precision_regime, time_basis, comparable_with, convention_id,
        ephemeris_backend, evidence_fact_ids, input_generation_vector_id, build_id, computed_at)
     VALUES ($1, $2, 'sha256:legacy', 'g1', 'Mars', 'conjunction', 0, 'graha', 'natal:mars', NULL,
             'resolved', 198.52, '2025-03-09T00:00Z', '2025-03-10T00:00Z', '2025-03-11T00:00Z',
             60, 1, 'direct', false, true, 3, 'orb-1', 'observed', 'applied', 'scored',
             'standard', 'event_time_utc', 'self', $3, '{}', '[]', $4, 'build-legacy', now())`,
    [CHART, LEGACY_GEN, LEGACY_CONV, manifestId],
  )
}
async function seedObject(c: Q, id: string, body: string, relation: string, target: string, conv = CONV): Promise<void> {
  await c.query(
    `INSERT INTO ka_gochara_physical_object
       (physical_object_id, body, relation_kind, canonical_target, convention_id)
     VALUES ($1, $2, $3, $4, $5)`, [id, body, relation, target, conv],
  )
}
/** The chart context every substrate/identity/bridge/declaration write needs FIRST (ruling B, substrate order). */
async function chartCtx(c: Q, chart = CHART): Promise<void> {
  await c.query(`SELECT ka_gochara_lock_chart($1)`, [chart])
}
async function seedIdentity(c: Q, id: string, objectId: string, ordinal: number, supersedes: string | null = null): Promise<void> {
  await chartCtx(c)
  await c.query(
    `INSERT INTO ka_gochara_contact_identity
       (contact_id, physical_object_id, occurrence_ordinal, supersedes_contact_id)
     VALUES ($1, $2, $3, $4)`, [id, objectId, ordinal, supersedes],
  )
}
const CONTACT_COLS = `chart_id, generation, contact_id, physical_object_id, occurrence_ordinal,
  convention_id, body, relation_kind, t_in, t_out, t_exact, solver_method, delta_lambda,
  delta_t, precision_regime, coverage`

async function seedLedger(c: Q, o: {
  id: string; objectId: string; ordinal: number; generation?: string; chart?: string;
  body?: string; relation?: string; conv?: string; truncated?: boolean; tIn?: string;
  tExact?: string; solver?: string;
}): Promise<void> {
  const truncated = o.truncated ?? false
  await c.query(
    `INSERT INTO ka_gochara_contact (${CONTACT_COLS})
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9,
             ${truncated ? 'NULL' : `'2025-03-11T00:00Z'`},
             ${truncated ? 'NULL' : `'${o.tExact ?? '2025-03-10T00:00Z'}'`},
             $10,
             ${truncated ? 'NULL' : '0.001'}, ${truncated ? 'NULL' : '60'},
             ${truncated ? 'NULL' : `'standard'`},
             $11::jsonb)`,
    [o.chart ?? CHART, o.generation ?? GEN, o.id, o.objectId, o.ordinal, o.conv ?? CONV,
      o.body ?? 'mars', o.relation ?? 'conjunction', o.tIn ?? '2025-03-09T00:00Z',
      o.solver ?? (truncated ? 'clipped_truncated' : 'swiss_refined'),
      JSON.stringify({ truncated })],
  )
}
async function seedContact(c: Q, o: Parameters<typeof seedLedger>[1]): Promise<void> {
  await seedIdentity(c, o.id, o.objectId, o.ordinal)
  await seedLedger(c, o)
}

async function seedRegistries(c: Q): Promise<void> {
  await c.query(
    `INSERT INTO ka_gochara_predicate (predicate_id, rule_version, operator, operands) VALUES
       ('q1', 'v1', 'within_orb', '{"left":"chart_facts.graha_position:mars","right":"object.longitude","orb":3.0}'),
       ('q2', 'v1', 'period_running_at', '{"lord":"dasha.md_lord","at":"eval.instant"}')`,
  )
  await c.query(
    `INSERT INTO ka_gochara_factor
       (factor_id, rule_version, operand_selector, direction, function, range_lower, range_upper,
        units, calibration_status, doctrine_ordering, category_mapping, null_state, effect)
     VALUES ('f1', 'v1', '{"operand":"dignity.transit_sign"}', 'higher_stronger', 'step', 0, 1,
             'unitless', 'uncalibrated_default',
             '["exaltation","own","friendly","neutral","inimical","debility"]', NULL, 'omit',
             'declared effect text')`,
  )
  const marsSel = '[{"agent":"mars","relation":"conjunction","object_role":"karaka"}]'
  await c.query(
    `INSERT INTO ka_gochara_rule_path
       (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set, object_selector,
        provenance, operator_role, ruling_ref, score_rule)
     VALUES
       ('P1', 'v1', 'dasha_lord', NULL, '["mars","moon"]', '["conjunction","occupancy"]',
        '[{"agent":"mars","relation":"conjunction","object_role":"karaka"},
          {"agent":"moon","relation":"conjunction","object_role":"karaka"},
          {"agent":"mars","relation":"occupancy","object_role":"occupant"}]',
        'verse_cited', 'scored', NULL, 'within_path_product'),
       ('P2', 'v1', 'moon', NULL, '["saturn"]', '["residence"]',
        '[{"agent":"saturn","relation":"residence","object_role":"occupant"}]',
        'verse_cited', 'scored', 'M-8', 'within_path_product'),
       ('P3', 'v1', 'lagna', NULL, '["mars"]', '["conjunction"]', '${marsSel}', 'verse_cited', 'scored', NULL, 'within_path_product'),
       ('P4', 'v1', 'lagna', NULL, '["jupiter","saturn","mars"]', '["residence","aspect","conjunction"]',
        '[{"agent":"jupiter","relation":"residence","object_role":"signature_house"},
          {"agent":"mars","relation":"conjunction","object_role":"karaka"}]',
        'uncited_extension', 'scored', 'D-P4', 'within_path_product'),
       ('P5', 'v1', 'lagna', NULL, '["mars"]', '["conjunction"]', '${marsSel}', 'verse_cited', 'scored', NULL, 'within_path_product'),
       ('P6', 'v1', 'lagna', NULL, '["mars"]', '["conjunction"]', '${marsSel}', 'verse_cited', 'scored', NULL, 'within_path_product')`,
  )
  await c.query(
    `INSERT INTO ka_gochara_rule_path_prerequisite
       (path_id, rule_version, ordinal, predicate_id, predicate_rule_version)
     VALUES ('P1', 'v1', 1, 'q1', 'v1'), ('P4', 'v1', 1, 'q1', 'v1')`,
  )
  await c.query(
    `INSERT INTO ka_gochara_rule_path_soft_factor
       (path_id, rule_version, factor_id, factor_rule_version) VALUES ('P1', 'v1', 'f1', 'v1')`,
  )
  // P1/v1 and P4/v1 sealed (complete); P2, P3, P5, P6 left UNSEALED for the seal/membership cases.
  await c.query(`INSERT INTO ka_gochara_rule_path_seal (path_id, rule_version) VALUES ('P1','v1'), ('P4','v1')`)
}

/** The writer's side of N10/N14: the facts snapshot of the partition it consumed, as JSON text. */
async function factsFor(c: Q, generation: string, kind: string, key: string): Promise<string> {
  const r = await c.query<{ f: unknown }>(
    `SELECT ka_gochara_coverage_facts(convention_id, completed_horizon, relations_searched) AS f
     FROM kala_gochara_coverage WHERE chart_id = $1 AND generation = $2 AND partition_kind = $3 AND partition_key = $4`,
    [CHART, generation, kind, key],
  )
  if (!r.rows[0]) throw new Error(`no coverage partition (${generation}, ${kind}, ${key})`)
  return JSON.stringify(r.rows[0].f)
}

const RECORD_COLS = `record_id, chart_id, generation, contact_id, event_class,
  affected_person, frame_kind, frame_arg, agent, relation, object_id, object_kind,
  object_role, path_id, rule_version, temporal_support_state, temporal_support_grain,
  temporal_support_intervals, coverage_partition_kind, coverage_partition_key, coverage_facts,
  precision, source_text, source_page, source_fact_ids, fixture, provenance,
  operator_role, ruling_ref, admission_state, house_from_frame,
  evidence_for_occurrence, evidence_against_occurrence, outcome_valence_for_native,
  severity, period_anchor_lord, period_anchor_level`

interface RecordOpts {
  id?: string; chart?: string; generation?: string; contactId?: string | null;
  eventClass?: string; affected?: string; frameKind?: string; frameArg?: string | null;
  agent?: string; relation?: string; objectId?: string; objectKind?: string; objectRole?: string;
  pathId?: string; ruleVersion?: string; supportState?: string; grain?: string | null;
  intervalsSql?: string; covKind?: string; covKey?: string; factsOverride?: string; precisionSql?: string;
  sourceText?: string | null; sourcePage?: string | null; factIdsSql?: string; fixture?: boolean;
  provenance?: string; operatorRole?: string; rulingRef?: string | null; admission?: string;
  house?: number | null; evidenceForSql?: string; evidenceAgainstSql?: string; valence?: string;
  severitySql?: string;
  anchorLord?: string | null; anchorLevel?: string | null;
  /** prerequisite membership rows (ordinal = position + 1); null = no membership */
  results?: Array<[string, string, string | null]> | null;
}

/** Record + its prerequisite membership (the writer's atomic unit) on the given client. */
async function insertRecord(c: Q, o: RecordOpts = {}): Promise<string> {
  const id = o.id ?? uuid()
  const generation = o.generation ?? GEN_F
  const chart = o.chart ?? CHART
  const transit = o.contactId !== null
  const covKind = o.covKind ?? COV_KIND
  const covKey = o.covKey ?? COV_KEY
  const facts = o.factsOverride ?? await factsFor(c, generation, covKind, covKey)
  const cols = ANCHOR_COLS ? RECORD_COLS : RECORD_COLS.replace(', period_anchor_lord, period_anchor_level', '')
  const anchorParams = ANCHOR_COLS ? [o.anchorLord === undefined ? null : o.anchorLord, o.anchorLevel === undefined ? null : o.anchorLevel] : []
  await c.query(
    `INSERT INTO ka_gochara_relationship_record (${cols})
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17,
             ${o.intervalsSql ?? SUPPORT}, $18, $19, $20::jsonb,
             ${o.precisionSql ?? (transit ? `'{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb` : 'NULL')},
             $21, $22, ${o.factIdsSql ?? `'["fact-1"]'`}, $23, $24, $25, $26, $27, $28,
             ${o.evidenceForSql ?? '0.8'}, ${o.evidenceAgainstSql ?? 'NULL'}, $29,
             ${o.severitySql ?? 'NULL'}${ANCHOR_COLS ? ', $30, $31' : ''})`,
    [id, chart, generation,
      transit ? (o.contactId ?? CID_1) : null,
      o.eventClass ?? 'marriage', o.affected ?? 'native', o.frameKind ?? 'lagna', o.frameArg ?? null,
      o.agent ?? 'mars', o.relation ?? (transit ? 'conjunction' : 'occupancy'),
      o.objectId ?? OBJ_MARS, o.objectKind ?? 'degree_point', o.objectRole ?? 'karaka',
      o.pathId ?? 'P1', o.ruleVersion ?? 'v1', o.supportState ?? 'computed',
      o.grain === undefined ? 'day' : o.grain,
      covKind, covKey, facts,
      o.sourceText === undefined ? 'Phaladīpikā' : o.sourceText,
      o.sourcePage === undefined ? 'PG249-250 (XX.34-38)' : o.sourcePage,
      o.fixture ?? false, o.provenance ?? 'verse_cited', o.operatorRole ?? 'scored',
      o.rulingRef ?? null, o.admission ?? 'admitted',
      o.house === undefined ? 7 : o.house, o.valence ?? 'favourable', ...anchorParams],
  )
  const results = o.results === undefined ? [['q1', 'v1', 'true'] as [string, string, string | null]] : o.results
  if (results) {
    let ordinal = 0
    for (const [pid, pver, result] of results) {
      await c.query(
        `INSERT INTO ka_gochara_record_prerequisite
           (record_id, chart_id, generation, ordinal, predicate_id, predicate_rule_version, result)
         VALUES ($1, $2, $3, $4, $5, $6, $7)`,
        [id, chart, generation, ++ordinal, pid, pver, result],
      )
    }
  }
  return id
}

async function insertWindow(c: Q, o: {
  id?: string; generation?: string; eventClass?: string; pathId?: string; ruleVersion?: string;
  intervalSql?: string; peakSql?: string; scoreSql?: string; evidenceForSql?: string;
  evidenceAgainstSql?: string; valence?: string; covKind?: string; covKey?: string; factsOverride?: string;
  nullStatesSql?: string; severitySql?: string;
} = {}): Promise<string> {
  const id = o.id ?? uuid()
  const generation = o.generation ?? GEN_F
  const eventClass = o.eventClass ?? 'marriage'
  const covKind = o.covKind ?? 'event_class'
  const covKey = o.covKey ?? eventClass
  const facts = o.factsOverride ?? await factsFor(c, generation, covKind, covKey)
  await c.query(
    `INSERT INTO ka_gochara_eval_window
       (window_id, chart_id, generation, event_class, path_id, rule_version, interval,
        peak_instant, score, evidence_for, evidence_against, outcome_valence_for_native,
        severity, coverage_partition_kind, coverage_partition_key, coverage_facts, null_states_used)
     VALUES ($1, $2, $3, $4, $5, $6,
             ${o.intervalSql ?? `tstzrange('2025-03-01T00:00Z','2025-04-01T00:00Z')`},
             ${o.peakSql ?? `'2025-03-10T00:00Z'`}, ${o.scoreSql ?? '0.8'},
             ${o.evidenceForSql ?? '0.8'}, ${o.evidenceAgainstSql ?? 'NULL'}, $7,
             ${o.severitySql ?? 'NULL'}, $8, $9, $10::jsonb, ${o.nullStatesSql ?? `'{}'`})`,
    [id, CHART, generation, eventClass, o.pathId ?? 'P1', o.ruleVersion ?? 'v1',
      o.valence ?? 'favourable', covKind, covKey, facts],
  )
  return id
}

async function addMembership(c: Q, windowId: string, recordId: string, o: {
  generation?: string; eventClass?: string; pathId?: string; ruleVersion?: string;
} = {}): Promise<void> {
  await c.query(
    `INSERT INTO ka_gochara_eval_window_record
       (window_id, record_id, chart_id, generation, event_class, path_id, rule_version)
     VALUES ($1, $2, $3, $4, $5, $6, $7)`,
    [windowId, recordId, CHART, o.generation ?? GEN_F, o.eventClass ?? 'marriage',
      o.pathId ?? 'P1', o.ruleVersion ?? 'v1'],
  )
}

/** The governed publication protocol: chart lock FIRST, then the manifest flip, then the seal. */
async function publishAndSeal(c: Q, generation: string): Promise<void> {
  await c.query(`SELECT ka_gochara_lock_chart($1)`, [CHART])
  await c.query(`UPDATE kala_gochara_publication SET status = 'published', published_at = now()
                 WHERE chart_id = $1 AND generation = $2`, [CHART, generation])
  await c.query(`SELECT ka_gochara_seal_generation($1, $2)`, [CHART, generation])
}

/**
 * Full fixture stack, in FK order, in TWO transactions — the enforced lock
 * order (ruling B) forbids a rule-path registry mutation (global EXCLUSIVE)
 * and a chart-scoped mutation (chart key) in one transaction. Substrate rows
 * (conventions, objects, identities, bridge) take no family key and may ride
 * with either.
 */
async function seedFixtures(): Promise<void> {
  await tx(async c => {
    await chartCtx(c)   // substrate order: the chart key precedes every substrate write
    await seedLegacyConvention(c, LEGACY_CONV)
    await seedLegacyConvention(c, LEGACY_CONV_UNBRIDGED)
    await seedSkyConvention(c, CONV)
    await seedSkyConvention(c, CONV2, 'm2')
    await c.query(`INSERT INTO ka_gochara_convention_bridge (kala_convention_id, sky_convention_id) VALUES ($1, $2)`, [LEGACY_CONV, CONV])
    for (const g of [GEN, GEN_C, GEN_R, GEN_P, GEN_F, GEN_N, GEN_S, GEN_X, GEN_D, GEN_L, GEN_M, GEN_I]) {
      await seedPublication(c, g)
      await seedCoverage(c, { generation: g, kind: 'body_target', key: COV_KEY })
      await seedCoverage(c, { generation: g, kind: 'event_class', key: 'marriage' })
    }
    // legacy '4.0' — candidate manifest, coverage and one legacy contact (legacy tables only)
    const legacyManifest = await seedPublication(c, LEGACY_GEN)
    await seedCoverage(c, { generation: LEGACY_GEN, kind: 'body_target', key: 'saturn:karaka' })
    await seedLegacyContact(c, legacyManifest)
    // negative-case partitions on the never-published generation
    await seedCoverage(c, { generation: GEN_F, kind: 'event_class', key: 'childbirth' })
    await seedCoverage(c, { generation: GEN_F, kind: 'moon_on_demand', key: 'moon:interval:2025-03-01/2025-03-31', relationsSql: `ARRAY['conjunction']::text[]` })
    await seedCoverage(c, { generation: GEN_F, kind: 'event_class', key: 'romantic_start', relationsSql: `ARRAY['aspect']::text[]` })
    await seedCoverage(c, { generation: GEN_F, kind: 'event_class', key: 'separation', conv: LEGACY_CONV_UNBRIDGED })
    await seedCoverage(c, { generation: GEN_F, kind: 'event_class', key: 'career_entry', completed: "tstzrange('2025-06-01T00:00Z','2026-01-01T00:00Z','[)')" })
    await seedCoverage(c, { generation: GEN_F, kind: 'event_class', key: 'surgery', relationsSql: `ARRAY['conjunction', NULL]::text[]` })
    // N17: partitions the contract does not admit (full horizon; positive-infinity singleton; omitted bound)
    await seedCoverage(c, { generation: GEN_F, kind: 'event_class', key: 'travel_event', completed: "tstzrange('-infinity','infinity','[]')" })
    await seedCoverage(c, { generation: GEN_F, kind: 'event_class', key: 'relocation', completed: "tstzrange('infinity','infinity','[]')" })
    await seedCoverage(c, { generation: GEN_F, kind: 'event_class', key: 'major_gain', completed: "tstzrange('2025-01-01T00:00Z', NULL, '[)')" })
    await seedObject(c, OBJ_MARS, 'mars', 'conjunction', 'point:198.52')
    await seedObject(c, OBJ_MOON, 'moon', 'conjunction', 'point:327.06')
    await seedObject(c, OBJ_MARS_ASPECT, 'mars', 'aspect', 'point:198.52')
    await seedObject(c, OBJ_MARS_C1, 'mars', 'conjunction', 'point:198.52', CONV2)
    await seedObject(c, OBJ_MARS_T2, 'mars', 'conjunction', 'point:198.53')
    await seedObject(c, OBJ_SAT_CONJ, 'saturn', 'conjunction', 'point:202.43')
    await seedObject(c, OBJ_SAT_SPAN, 'saturn', 'sign_ingress', 'span:libra')
    await seedObject(c, OBJ_MARS_SPAN, 'mars', 'sign_ingress', 'span:libra')
  })
  await tx(async c => {
    await seedRegistries(c)   // global EXCLUSIVE — registry construction, its own transaction
  })
  await tx(async c => {
    // O-RX-1 shape: one tuple, many contacts
    await seedContact(c, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: GEN })
    await seedContact(c, { id: CID_2, objectId: OBJ_MARS, ordinal: 2, generation: GEN })
    await seedContact(c, { id: CID_TRUNC, objectId: OBJ_MARS, ordinal: 3, generation: GEN_F, truncated: true })
    await seedContact(c, { id: CID_LATE, objectId: OBJ_MARS, ordinal: 4, generation: GEN_F, tIn: '2025-02-01T00:00Z' })
    await seedContact(c, { id: CID_OLD_ONLY, objectId: OBJ_MARS, ordinal: 5, generation: GEN_C })
    await seedContact(c, { id: CID_R, objectId: OBJ_MARS, ordinal: 6, generation: GEN_R })
    await seedContact(c, { id: CID_P, objectId: OBJ_MARS, ordinal: 7, generation: GEN_P })
    await seedContact(c, { id: CID_T2, objectId: OBJ_MARS, ordinal: 8, generation: GEN_N, truncated: true })
    await seedContact(c, { id: CID_MOON, objectId: OBJ_MOON, ordinal: 1, generation: GEN_F, body: 'moon' })
    // F1: the SAME identity CID_1 is also owned by the never-published and the cascade generations
    await seedLedger(c, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: GEN_F })
    await seedLedger(c, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: GEN_S })
    // N12/N13 topology fixtures: two rows of one candidate generation (same readings — N6)
    await seedLedger(c, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: GEN_L })
    await seedLedger(c, { id: CID_2, objectId: OBJ_MARS, ordinal: 2, generation: GEN_L })
  })
}

async function tableExists(name: string): Promise<boolean> {
  const res = await pool.query<{ present: boolean }>(`SELECT to_regclass($1) IS NOT NULL AS present`, [`public.${name}`])
  return res.rows[0]!.present
}
async function functionExists(sig: string): Promise<boolean> {
  const res = await pool.query<{ present: boolean }>(`SELECT to_regprocedure($1) IS NOT NULL AS present`, [`public.${sig}`])
  return res.rows[0]!.present
}
async function ledgerFiles(): Promise<string[]> {
  const res = await pool.query<{ filename: string }>(`SELECT filename FROM _migrations_applied ORDER BY filename`)
  return res.rows.map(r => r.filename)
}
async function withTempDir<T>(files: readonly string[], fn: (dir: string) => Promise<T>): Promise<T> {
  const dir = mkdtempSync(join(tmpdir(), 'gochara-a51-migrations-'))
  try {
    for (const f of files) copyFileSync(join(MIGRATIONS_DIR, f), join(dir, f))
    return await fn(dir)
  } finally {
    rmSync(dir, { recursive: true, force: true })
  }
}
async function sealCount(generation: string): Promise<number> {
  const r = await pool.query<{ n: number }>(`SELECT COUNT(*)::int AS n FROM ka_gochara_generation_seal WHERE chart_id = $1 AND generation = $2`, [CHART, generation])
  return r.rows[0]!.n
}



const OWNER = 'amjis_app'
const BUILDER = 'data_plane_builder'
const refused = async (p: Promise<unknown>, re: RegExp): Promise<void> => { await expect(p).rejects.toThrow(re) }

/** Deployment-faithful mirror: the migration principal owns every object; PUBLIC EXECUTE is revoked on whatever it creates. */
async function mirror(): Promise<void> {
  for (const r of [OWNER, BUILDER])
    await pool.query(`DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='${r}') THEN CREATE ROLE ${r} NOLOGIN; END IF; END $$`)
  await pool.query(`ALTER DEFAULT PRIVILEGES FOR ROLE ${OWNER} REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC`)
  await pool.query(`GRANT USAGE, CREATE ON SCHEMA public TO ${OWNER}; GRANT USAGE ON SCHEMA public TO ${BUILDER}`)
  for (const t of [...LEGACY_TABLES, '_migrations_applied']) await pool.query(`ALTER TABLE ${t} OWNER TO ${OWNER}`)
}
async function asOwner<T>(fn: (c: PoolClient) => Promise<T>): Promise<T> {
  const c = await pool.connect()
  try { await c.query(`SET ROLE ${OWNER}`); return await fn(c) } finally { await c.query('RESET ROLE').catch(() => undefined); c.release() }
}
async function asBuilder<T>(fn: (c: PoolClient) => Promise<T>): Promise<T> {
  const c = await pool.connect()
  try {
    await c.query('BEGIN'); await c.query(`SET LOCAL ROLE ${BUILDER}`)
    const r = await fn(c); await c.query('COMMIT'); return r
  } catch (err) { await c.query('ROLLBACK').catch(() => undefined); throw err } finally { c.release() }
}
async function dropMirror(): Promise<void> {
  await pool.query(`DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;`)
  for (const r of [BUILDER, OWNER]) { await pool.query(`DROP OWNED BY ${r} CASCADE`).catch(() => undefined); await pool.query(`DROP ROLE IF EXISTS ${r}`).catch(() => undefined) }
}

describe.skipIf(!TEST_DB_URL)('B6.0 migration 1234 — eval-window builder grants, derived under the deployment-faithful mirror (live disposable DB)', () => {
  let rid = ''
  beforeAll(async () => {
    pool = new Pool({ ...resolveDisposableA51Config(TEST_DB_URL), max: 4 })
    await resetSchema()
    await mirror()
    await asOwner(async c => {
      await withTempDir(MIGRATION_FILES, dir => runMigrations(c, [dir], { only: new Set(MIGRATION_FILES), disclosures: new Map(), renumberDisclosures: new Map() }))
      await c.query(mig(M1216)); await c.query(mig(M1220))        // what production already holds
    })
    await seedFixtures()
    rid = await tx(async c => { await chartCtx(c); return insertRecord(c, { generation: GEN_F }) })
  }, 120_000)
  afterAll(async () => { if (!pool) return; await resetSchema(); await dropMirror(); await pool.end() })

  const write = (wid: string) => asBuilder(async c => { await chartCtx(c); await insertWindow(c, { id: wid, generation: GEN_F }); await addMembership(c, wid, rid, { generation: GEN_F }) })

  it('BEFORE 1234 the builder cannot write a window (the gap 1216 deferred and 1220 does not cover)', async () => {
    await refused(write(uuid()), /permission denied for table ka_gochara_eval_window/)
  })

  it('applies as the owner', async () => { await asOwner(c => c.query(mig(M1234))) })

  it('AFTER 1234 the builder writes a window with its membership through the real guards, replaces it by DELETE (membership rides the cascade) and re-writes it', async () => {
    const w1 = uuid()
    await write(w1)
    const n = async (): Promise<number> => (await pool.query(`SELECT count(*)::int AS n FROM ka_gochara_eval_window_record WHERE window_id = $1`, [w1])).rows[0].n
    expect(await n()).toBe(1)
    await asBuilder(async c => { await chartCtx(c)
      await c.query(`DELETE FROM ka_gochara_eval_window WHERE chart_id=$1 AND generation=$2 AND event_class='marriage' AND path_id='P1' AND rule_version='v1'`, [CHART, GEN_F]) })
    expect(await n()).toBe(0)                                                    // the membership row left with the window — no DELETE grant on it was needed
    await write(uuid())
  })

  it('least privilege: the builder cannot UPDATE a window, DELETE a membership row directly, TRUNCATE, or touch the seal', async () => {
    const w = uuid(); await write(w)
    await refused(asBuilder(async c => { await chartCtx(c); await c.query(`UPDATE ka_gochara_eval_window SET score = 0.1 WHERE window_id = $1`, [w]) }), /permission denied for table ka_gochara_eval_window/)
    await refused(asBuilder(async c => { await chartCtx(c); await c.query(`DELETE FROM ka_gochara_eval_window_record WHERE window_id = $1`, [w]) }), /permission denied for table ka_gochara_eval_window_record/)
    await refused(asBuilder(c => c.query(`TRUNCATE ka_gochara_eval_window`)), /permission denied for table ka_gochara_eval_window/)
    await refused(asBuilder(async c => { await chartCtx(c); await c.query(`UPDATE ka_gochara_eval_window_record SET path_id = path_id WHERE window_id = $1`, [w]) }), /permission denied for table ka_gochara_eval_window_record/)
    await refused(asBuilder(c => c.query(`INSERT INTO ka_gochara_generation_seal (chart_id, generation, manifest_id) VALUES ($1,$2,gen_random_uuid())`, [CHART, GEN_F])), /permission denied for table ka_gochara_generation_seal/)
  })

  it('each grant is individually necessary: revoking any one breaks the writer path (the converged set is minimal)', async () => {
    // the writer's two statements: INSERT window + membership; and the grain REPLACE (DELETE ... WHERE, membership rides the cascade)
    const replace = () => asBuilder(async c => { await chartCtx(c)
      await c.query(`DELETE FROM ka_gochara_eval_window WHERE chart_id=$1 AND generation=$2 AND event_class='marriage' AND path_id='P1' AND rule_version='v1'`, [CHART, GEN_F]) })
    const REVOKES: Array<[string, string, () => Promise<unknown>, RegExp]> = [
      [`REVOKE INSERT ON ka_gochara_eval_window FROM ${BUILDER}`, `GRANT INSERT ON ka_gochara_eval_window TO ${BUILDER}`, () => write(uuid()), /permission denied for table ka_gochara_eval_window/],
      [`REVOKE DELETE ON ka_gochara_eval_window FROM ${BUILDER}`, `GRANT DELETE ON ka_gochara_eval_window TO ${BUILDER}`, replace, /permission denied for table ka_gochara_eval_window/],
      [`REVOKE SELECT ON ka_gochara_eval_window FROM ${BUILDER}`, `GRANT SELECT ON ka_gochara_eval_window TO ${BUILDER}`, replace, /permission denied for table ka_gochara_eval_window/],
      [`REVOKE INSERT ON ka_gochara_eval_window_record FROM ${BUILDER}`, `GRANT INSERT ON ka_gochara_eval_window_record TO ${BUILDER}`, () => write(uuid()), /permission denied for table ka_gochara_eval_window_record/],
      [`REVOKE EXECUTE ON FUNCTION ka_gochara_text_array_ok(text[],integer) FROM ${BUILDER}`, `GRANT EXECUTE ON FUNCTION ka_gochara_text_array_ok(text[],integer) TO ${BUILDER}`, () => write(uuid()), /permission denied for function ka_gochara_text_array_ok/],
      [`REVOKE EXECUTE ON FUNCTION ka_gochara_membership_violation(jsonb,uuid,text,jsonb,tstzrange[]) FROM ${BUILDER}`, `GRANT EXECUTE ON FUNCTION ka_gochara_membership_violation(jsonb,uuid,text,jsonb,tstzrange[]) TO ${BUILDER}`, () => write(uuid()), /permission denied for function ka_gochara_membership_violation/],
      [`REVOKE EXECUTE ON FUNCTION ka_gochara_facts_horizon(jsonb) FROM ${BUILDER}`, `GRANT EXECUTE ON FUNCTION ka_gochara_facts_horizon(jsonb) TO ${BUILDER}`, () => write(uuid()), /permission denied for function ka_gochara_facts_horizon/],
    ]
    await write(uuid())                                                         // a window exists for the replace cases
    for (const [rev, grant, action, re] of REVOKES) {
      await pool.query(rev)
      try { await refused(action(), re) } finally { await pool.query(grant) }
    }
    await write(uuid()); await replace()                                         // restored: both statements work again
  })

  it('SELECT on the membership table is NOT needed by the database guards (measured); it is granted for the WRITER\'s read-back of the pairs it wrote (window_store.py:212/224)', async () => {
    await pool.query(`REVOKE SELECT ON ka_gochara_eval_window_record FROM ${BUILDER}`)
    let needed = false
    try { await write(uuid()) } catch (e) { needed = /permission denied for table ka_gochara_eval_window_record/.test(String(e)) }
    await pool.query(`GRANT SELECT ON ka_gochara_eval_window_record TO ${BUILDER}`)
    expect(needed).toBe(false)
  })

  it('the builder is NOT granted the seal-side window functions (membership_violations / coverage_drift) or the trigger functions', async () => {
    const r = await pool.query<{ f: string; ok: boolean }>(
      `SELECT f, has_function_privilege($1, ('public.' || f)::regprocedure, 'EXECUTE') AS ok FROM unnest($2::text[]) f`,
      [BUILDER, ['ka_gochara_membership_violations(uuid,text)', 'ka_gochara_coverage_drift(uuid,text)', 'ka_gochara_window_coverage_guard()', 'ka_gochara_window_membership_guard()']])
    expect(r.rows.every(x => x.ok === false)).toBe(true)
  })
})
