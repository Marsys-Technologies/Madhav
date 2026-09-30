// @vitest-environment node
/**
 * Pravāha A5.1 round 7 — LIVE-DB contract suite for migrations 1153–1157 and
 * their preflights, executed against a REAL throwaway Postgres (CLAUDE.md
 * §N.8: the test runs the on-disk SQL itself, never a hand-copied
 * re-implementation). Sibling of kala_gochara_windows_generation_guard.db.test.ts.
 *
 * Closes ASTRA_REVIEW_A5_1_MIGRATIONS v1_2 (N1–N11), v1_3 (N12–N15, P2),
 * v1_4 (residual N13 substrate order, N16, N17) and v1_5 (N18 one chart per
 * transaction, N19 timestamp era) under the steward's rulings —
 * including the CORRECTED lock ruling (family keys, never the orchestrator's)
 * — at runtime:
 *   - N3   the deploy route: the routine runner REFUSES 1153–1157; a role with
 *          USAGE but not CREATE is blocked by each gate; with the temporary
 *          CREATE grant (the window) the same role applies all five through
 *          the exact `--only` route, interleaved with the preflights, and the
 *          objects it created are its own after the revoke;
 *   - N1/P2 legacy '4.0' is untouched: no trigger of ours on any legacy table;
 *          our FKs' RI triggers sit on charts / convention / coverage ONLY
 *          (disclosed) and never on publication / contacts; the legacy publish
 *          / re-publish / rollback SQL completes as the runtime role while
 *          another session HOLDS the orchestrator's chart lock (no lock
 *          dependency), writes no seal, and the seal function refuses
 *          'v1'/'3.0'/'4.0'/'4.1';
 *   - N12  the REAL runner topology: a main connection holds the
 *          orchestrator's session locks (chart + global) while a WORKER
 *          connection writes governed rows and COMPLETES; an unrelated second
 *          writer and the seal function are excluded until the worker commits;
 *          governed writes never wait on the orchestrator's keys;
 *   - N13  the fixed order is ENFORCED: global-EXCLUSIVE→chart and
 *          chart→global-EXCLUSIVE are refused in-transaction;
 *          chart→global-SHARED is the legal mix; a registry mutation never
 *          waits for a chart-only holder (only for a SHARED reader); the
 *          family key precedes tuple locks — the concurrent UPDATE/DELETE
 *          inversion (A locks X, B wants Y then X, A wants Y) cannot deadlock
 *          and B is observed waiting on the ADVISORY lock, not a tuple;
 *          SUBSTRATE ORDER (v1_4): a substrate/identity/bridge/declaration
 *          write without a chart context is refused; with one it takes the
 *          chart key FIRST, so the reviewer's unique-entry and sky-event
 *          tuple schedules are serialised (B waits on the advisory key
 *          before touching any substrate lock), never deadlocked — with the
 *          main connection holding its session locks throughout;
 *          ONE CHART PER TRANSACTION (v1_5, N18): the transaction is bound to
 *          the first chart it locks; a different chart is refused BEFORE any
 *          other family key is requested; a non-canonical chart is refused at
 *          the lock boundary (D-SCOPE); a substrate write whose declared
 *          context disagrees with the binding is refused — the reviewer's
 *          mixed-context unique-entry and sky-event tuple schedules are
 *          refused outright, never waited on, never deadlocked;
 *   - N16  the seal boundary carries the complete membership invariant: a
 *          VALID membership, then a parent update (relations dropped,
 *          convention changed, window horizon narrowed, contributor support
 *          moved) → the seal is REFUSED; ka_gochara_membership_violations
 *          names the row and reason; after restoration the seal succeeds;
 *   - N17/N19 finite AD-era horizons only (every bound within 1000-01-01 ≤ t
 *          < 3000-01-01 UTC): a partition with ±infinity / omitted / BC /
 *          out-of-range bounds is refused by the record and window coverage
 *          guards; such window intervals and support intervals fail their
 *          CHECKs; the encoder RAISES on any of them (the reviewer's H_BC
 *          included) and round-trips AD horizons exactly at the era edges; a
 *          validated AD consumer whose partition is replaced by H_BC (or an
 *          infinite / out-of-range horizon) is `incompatible` and the seal is
 *          refused;
 *   - N2/N5 rebuild ⇄ publication serialise in BOTH orders; the reviewer's
 *          lock-inversion schedule cannot deadlock (the publication path locks
 *          the chart first); membership ⇄ seal serialise in BOTH orders and
 *          record production waits for an in-flight construction; REPEATABLE
 *          READ is refused;
 *   - N4   plain re-run is BLOCKED (no replay mode); presence checks pass;
 *   - N6   a changed solved reading under the same contact id in another
 *          generation is refused (INSERT and enrichment UPDATE);
 *   - N7/N15 contact enrichment re-states dependent record precision, sealed
 *          generation included, EVEN AFTER the partition's horizon was
 *          extended after validation (extend-then-enrich); a diverging direct
 *          update is refused;
 *   - N8   prerequisite reparenting is refused; only `result` may change;
 *   - N9   a published generation's records / windows / membership are a
 *          frozen set (INSERT refused);
 *   - N10  NULL relations_searched is inapplicable; body_target full key;
 *          windows carry event_class coverage; consumers bind to the coverage
 *          facts; the CONSUMER CONTRACT: ka_gochara_coverage_drift classifies
 *          identical / extended / incompatible, the seal REFUSES incompatible
 *          drift, and window CONTRIBUTORS are checked against the window's
 *          coverage (convention, relations, horizon); isolated negative cases;
 *   - N14  the facts encoding distinguishes empty from unbounded horizons,
 *          NULL elements and element boundaries (the reviewer's collisions);
 *   - N11  the URL guard validates the driver's effective configuration and
 *          the suite connects with THAT resolved config;
 *   - amendment 2 (kept): a forced ledger failure after EACH migration leaves
 *          none of its tables or standalone functions.
 *
 * The 1081/1087/1152 parents are built by applying the REAL migration files;
 * only `charts` is a key-shape stub.
 *
 * Requires a THROWAWAY database. Skipped unless GOCHARA_A51_TEST_DATABASE_URL
 * is set; the URL is validated through pg-connection-string (the driver's
 * view) and must name an explicit loopback host:port and a database called
 * exactly `gochara_a51_test`.
 *
 *   initdb -D /tmp/a51/pgdata -U postgres --auth=trust
 *   pg_ctl -D /tmp/a51/pgdata -o "-p 59531 -c unix_socket_directories='' -c listen_addresses=127.0.0.1" start
 *   createdb -h 127.0.0.1 -p 59531 -U postgres gochara_a51_test
 *   GOCHARA_A51_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:59531/gochara_a51_test \
 *     npx vitest run tests/integration/gochara_a5_1_migrations.db.test.ts
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

/** Objects each migration OWNS (tables + standalone functions), for rollback proofs. */
const OWNED: Record<string, { tables: string[]; functions: string[] }> = {
  '1153_gochara_sky_event_substrate.sql': {
    tables: ['ka_gochara_sky_convention', 'ka_gochara_physical_object', 'ka_gochara_sky_event',
      'ka_gochara_contact_identity', 'ka_gochara_generation_seal', 'ka_gochara_convention_bridge',
      'ka_gochara_contact'],
    functions: ['ka_gochara_refuse_truncate()', 'ka_gochara_text_array_ok(text[],integer)',
      'ka_gochara_finite_ok(double precision)', 'ka_gochara_finite_nonneg_ok(double precision)',
      'ka_gochara_generation_governed(text)', 'ka_gochara_horizon_finite_ok(tstzrange)',
      'ka_gochara_lock_chart(uuid)', 'ka_gochara_lock_global()',
      'ka_gochara_lock_global_shared()', 'ka_gochara_insert_only()', 'ka_gochara_chart_statement_lock()',
      'ka_gochara_substrate_chart_lock()',
      'ka_gochara_global_write_guard()', 'ka_gochara_generation_is_sealed(uuid,text)',
      'ka_gochara_seal_generation(uuid,text)', 'ka_gochara_generation_seal_guard()',
      'ka_gochara_sky_event_supersede_guard()', 'ka_gochara_sky_event_guard()',
      'ka_gochara_contact_identity_supersede_guard()', 'ka_gochara_contact_guard()'],
  },
  '1154_gochara_rule_path_registry.sql': {
    tables: ['ka_gochara_predicate', 'ka_gochara_factor', 'ka_gochara_rule_path',
      'ka_gochara_rule_path_prerequisite', 'ka_gochara_rule_path_soft_factor', 'ka_gochara_rule_path_seal'],
    functions: ['ka_gochara_frame_ok(text,text)', 'ka_gochara_selector_token_ok(text)',
      'ka_gochara_string_array_ok(jsonb)', 'ka_gochara_vocab_array_ok(jsonb,text[])',
      'ka_gochara_named_operands_ok(jsonb)', 'ka_gochara_object_selector_ok(jsonb)',
      'ka_gochara_object_selector_consistent_ok(jsonb,jsonb,jsonb)', 'ka_gochara_membership_guard()',
      'ka_gochara_require_sealed_rule_path()'],
  },
  '1155_gochara_relationship_record.sql': {
    tables: ['ka_gochara_relationship_record', 'ka_gochara_record_prerequisite'],
    functions: ['ka_gochara_precision_ok(jsonb)', 'ka_gochara_intervals_ok(tstzrange[])',
      'ka_gochara_coverage_facts(text,tstzrange,text[])', 'ka_gochara_facts_horizon(jsonb)', 'ka_gochara_chart_write_guard()',
      'ka_gochara_record_coverage_guard()', 'ka_gochara_record_finalize_check()',
      'ka_gochara_contact_propagate_precision()'],
  },
  '1156_gochara_eval_window.sql': {
    tables: ['ka_gochara_eval_window', 'ka_gochara_eval_window_record'],
    functions: ['ka_gochara_window_coverage_guard()', 'ka_gochara_membership_violation(jsonb,uuid,text,jsonb,tstzrange[])',
      'ka_gochara_window_membership_guard()', 'ka_gochara_membership_violations(uuid,text)', 'ka_gochara_coverage_drift(uuid,text)'],
  },
  '1157_gochara_av_polarity_declaration.sql': {
    tables: ['ka_gochara_av_polarity_declaration'],
    functions: [],
  },
}
const KA_TABLES = Object.values(OWNED).flatMap(o => o.tables)

const EXPECTED_CONSTRAINTS: Array<[string, string]> = [
  ['ka_gochara_physical_object', 'kgpo_identity_uq'],
  ['ka_gochara_sky_event', 'ka_gochara_sky_event_object_fk'],
  ['ka_gochara_sky_event', 'kgse_truncated_method_ck'],
  ['ka_gochara_sky_event', 'kgse_supersedes_uq'],
  ['ka_gochara_contact_identity', 'ka_gochara_contact_identity_ordinal_uq'],
  ['ka_gochara_contact_identity', 'kgci_supersedes_uq'],
  ['ka_gochara_generation_seal', 'ka_gochara_generation_seal_pkey'],
  ['ka_gochara_generation_seal', 'kgseal_generation_governed_ck'],
  ['ka_gochara_contact', 'ka_gochara_contact_pkey'],
  ['ka_gochara_contact', 'ka_gochara_contact_identity_fk'],
  ['ka_gochara_contact', 'kgc_reference_uq'],
  ['ka_gochara_contact', 'kgc_generation_governed_ck'],
  ['ka_gochara_factor', 'kgf_calibrated_requires_mapping_ck'],
  ['ka_gochara_rule_path', 'kgrp_frame_ck'],
  ['ka_gochara_rule_path_seal', 'kgrpseal_path_fk'],
  ['ka_gochara_relationship_record', 'kgrr_contact_fk'],
  ['ka_gochara_relationship_record', 'kgrr_coverage_fk'],
  ['ka_gochara_relationship_record', 'kgrr_coverage_facts_shape_ck'],
  ['ka_gochara_relationship_record', 'kgrr_generation_governed_ck'],
  ['ka_gochara_relationship_record', 'kgrr_membership_uq'],
  ['ka_gochara_record_prerequisite', 'kgrpr_record_fk'],
  ['ka_gochara_eval_window', 'kgew_coverage_kind_ck'],
  ['ka_gochara_eval_window', 'kgew_interval_finite_ck'],
  ['ka_gochara_eval_window', 'kgew_coverage_facts_shape_ck'],
  ['ka_gochara_eval_window', 'kgew_membership_uq'],
  ['ka_gochara_eval_window_record', 'kgewr_window_fk'],
  ['ka_gochara_eval_window_record', 'kgewr_record_fk'],
  ['ka_gochara_av_polarity_declaration', 'ka_gochara_av_polarity_declaration_pkey'],
  ['ka_gochara_av_polarity_declaration', 'kgav_categories_nonempty_ck'],
]
const EXPECTED_TRIGGERS: Array<[string, string]> = [
  ['ka_gochara_sky_convention', 'ka_gochara_sky_convention_0_chart_context'],
  ['ka_gochara_sky_convention', 'ka_gochara_sky_convention_immutable'],
  ['ka_gochara_sky_event', 'ka_gochara_sky_event_0_chart_context'],
  ['ka_gochara_contact_identity', 'ka_gochara_contact_identity_0_chart_context'],
  ['ka_gochara_contact_identity', 'ka_gochara_contact_identity_immutable'],
  ['ka_gochara_convention_bridge', 'ka_gochara_convention_bridge_0_chart_context'],
  ['ka_gochara_av_polarity_declaration', 'ka_gochara_av_polarity_0_chart_context'],
  ['ka_gochara_sky_event', 'ka_gochara_sky_event_mutation_guard'],
  ['ka_gochara_contact_identity', 'ka_gochara_contact_identity_supersede_check'],
  ['ka_gochara_generation_seal', 'ka_gochara_generation_seal_write_guard'],
  ['ka_gochara_contact', 'ka_gochara_contact_0_statement_lock'],
  ['ka_gochara_contact', 'ka_gochara_contact_1_write_guard'],
  ['ka_gochara_contact', 'ka_gochara_contact_2_propagate_precision'],
  ['ka_gochara_contact', 'ka_gochara_contact_no_truncate'],
  ['ka_gochara_rule_path_prerequisite', 'ka_gochara_rp_prereq_sealed_check'],
  ['ka_gochara_rule_path_seal', 'ka_gochara_rule_path_seal_write_guard'],
  ['ka_gochara_relationship_record', 'ka_gochara_rr_0_statement_lock'],
  ['ka_gochara_relationship_record', 'ka_gochara_rr_1_write_guard'],
  ['ka_gochara_relationship_record', 'ka_gochara_rr_2_coverage_guard'],
  ['ka_gochara_relationship_record', 'ka_gochara_rr_3_sealed_path_check'],
  ['ka_gochara_relationship_record', 'ka_gochara_rr_finalize'],
  ['ka_gochara_record_prerequisite', 'ka_gochara_rpr_0_statement_lock'],
  ['ka_gochara_record_prerequisite', 'ka_gochara_rpr_1_write_guard'],
  ['ka_gochara_eval_window', 'ka_gochara_ew_0_statement_lock'],
  ['ka_gochara_eval_window', 'ka_gochara_ew_1_write_guard'],
  ['ka_gochara_eval_window_record', 'ka_gochara_ewr_0_statement_lock'],
  ['ka_gochara_eval_window_record', 'ka_gochara_ewr_1_write_guard'],
  ['ka_gochara_eval_window_record', 'ka_gochara_ewr_2_membership_guard'],
  ['ka_gochara_av_polarity_declaration', 'ka_gochara_av_polarity_write_guard'],
]

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
  severity`

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
  await c.query(
    `INSERT INTO ka_gochara_relationship_record (${RECORD_COLS})
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17,
             ${o.intervalsSql ?? SUPPORT}, $18, $19, $20::jsonb,
             ${o.precisionSql ?? (transit ? `'{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb` : 'NULL')},
             $21, $22, ${o.factIdsSql ?? `'["fact-1"]'`}, $23, $24, $25, $26, $27, $28,
             ${o.evidenceForSql ?? '0.8'}, ${o.evidenceAgainstSql ?? 'NULL'}, $29,
             ${o.severitySql ?? 'NULL'})`,
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
      o.house === undefined ? 7 : o.house, o.valence ?? 'favourable'],
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
    await insertRecord(c, { id: RECORD_1, generation: GEN })
    await insertWindow(c, { id: WINDOW_1, generation: GEN })
    await addMembership(c, WINDOW_1, RECORD_1, { generation: GEN })
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

describe.skipIf(!TEST_DB_URL)('A5.1 migrations 1153–1157 (live disposable DB, round 7)', () => {
  beforeAll(async () => {
    // N11: validate the DRIVER's view of the target and connect with the resolved config only
    const config = resolveDisposableA51Config(TEST_DB_URL)
    pool = new Pool({ ...config, max: 8 })
    await resetSchema()
    await createAppRole()
  })

  afterAll(async () => {
    if (!pool) return
    await resetSchema()
    await dropRole()
    await pool.end()
  })

  // ── Preflight gate semantics before any apply (F8/F9, kept) ─────────────
  describe('preflights fail closed and open', () => {
    it('PF1153 passes on a clean, correctly-privileged target with the REAL 1081 parents', async () => {
      await expect(pool.query(preflight(PREFLIGHT_FILES[0]))).resolves.toBeDefined()
    })

    it('PF1153 ledger lookup is wildcard-safe; blocks with the SPECIFIC token when 1153 is recorded', async () => {
      await pool.query(`INSERT INTO _migrations_applied (filename, sha256) VALUES ('1153Z_decoy.sql', 'x')`)
      await expect(pool.query(preflight(PREFLIGHT_FILES[0]))).resolves.toBeDefined()
      await pool.query(`DELETE FROM _migrations_applied WHERE filename = '1153Z_decoy.sql'`)
      await pool.query(`INSERT INTO _migrations_applied (filename, sha256) VALUES ($1, 'x')`, [MIGRATION_FILES[0]])
      await expect(pool.query(preflight(PREFLIGHT_FILES[0]))).rejects.toThrow(/migration_already_applied :: 1153_gochara_sky_event_substrate\.sql/)
      await pool.query(`DELETE FROM _migrations_applied WHERE filename = $1`, [MIGRATION_FILES[0]])
    })

    it('PF1153 blocks on a colliding table name AND on a colliding index name (relation namespace)', async () => {
      await pool.query(`CREATE TABLE ka_gochara_contact (id int)`)
      await expect(pool.query(preflight(PREFLIGHT_FILES[0]))).rejects.toThrow(/relation_already_exists :: public\.ka_gochara_contact\b/)
      await pool.query(`DROP TABLE ka_gochara_contact`)
      await pool.query(`CREATE TABLE idx_kgc_object (id int)`)
      await expect(pool.query(preflight(PREFLIGHT_FILES[0]))).rejects.toThrow(/relation_already_exists :: public\.idx_kgc_object/)
      await pool.query(`DROP TABLE idx_kgc_object`)
    })

    it('F8: PF1154 catches a same-ARGUMENT-TYPE function whose parameters are NAMED', async () => {
      await pool.query(`CREATE FUNCTION ka_gochara_frame_ok(a text, b text) RETURNS boolean LANGUAGE sql AS 'select true'`)
      await expect(pool.query(preflight(PREFLIGHT_FILES[1]))).rejects.toThrow(/function_already_exists :: public\.ka_gochara_frame_ok\(text,text\)/)
      await pool.query(`DROP FUNCTION ka_gochara_frame_ok(text, text)`)
    })

    it('F9: PF1155/PF1156 refuse to run before their prerequisite migrations (ordered gate)', async () => {
      await expect(pool.query(preflight(PREFLIGHT_FILES[2]))).rejects.toThrow(/prerequisite_migration_not_applied :: 1153_/)
      await expect(pool.query(preflight(PREFLIGHT_FILES[3]))).rejects.toThrow(/prerequisite_migration_not_applied :: 1155_/)
    })
  })

  // ── N3: the deploy route, rehearsed with the normalised role model ───────
  describe('(a) deploy route: routine refusal, USAGE-only block, the CREATE window, ordered apply', () => {
    it('the routine runner REFUSES pending 1153 with the dispatch instruction and touches nothing', async () => {
      const client = await pool.connect()
      try {
        await expect(withTempDir(MIGRATION_FILES, dir => runMigrations(client, [dir], { disclosures: new Map(), renumberDisclosures: new Map() })))
          .rejects.toThrow(/Protected public-schema migration "1153_gochara_sky_event_substrate\.sql" is pending[\s\S]*gochara_contracts_schema_migration=true/)
      } finally {
        client.release()
      }
      expect(await tableExists('ka_gochara_sky_convention')).toBe(false)
      expect(await ledgerFiles()).toEqual([])
    })

    it('a role with USAGE but not CREATE is blocked by the gate through the --only route; nothing persists', async () => {
      const client = await pool.connect()
      try {
        await client.query(`SET ROLE a51_app`)
        await expect(client.query(preflight(PREFLIGHT_FILES[0]))).rejects.toThrow(/no_create_privilege_on_public :: a51_app/)
        await expect(withTempDir(MIGRATION_FILES, dir => runMigrations(client, [dir], { only: new Set([MIGRATION_FILES[0]]), disclosures: new Map(), renumberDisclosures: new Map() })))
          .rejects.toThrow(/no_create_privilege_on_public :: a51_app/)
      } finally {
        await client.query(`RESET ROLE`).catch(() => undefined)
        client.release()
      }
      expect(await tableExists('ka_gochara_sky_convention')).toBe(false)
      expect(await ledgerFiles()).toEqual([])
    })

    it('inside the temporary CREATE window the same role applies 1153…1157 via --only, each preflight passing just before its file', async () => {
      await pool.query(`GRANT CREATE ON SCHEMA public TO a51_app`)   // the window opens
      const client = await pool.connect()
      try {
        await client.query(`SET ROLE a51_app`)
        for (let i = 0; i < MIGRATION_FILES.length; i++) {
          await expect(client.query(preflight(PREFLIGHT_FILES[i]!))).resolves.toBeDefined()
          const ran = await withTempDir(MIGRATION_FILES, dir =>
            runMigrations(client, [dir], { only: new Set([MIGRATION_FILES[i]!]), disclosures: new Map(), renumberDisclosures: new Map() }))
          expect(ran).toEqual([MIGRATION_FILES[i]])
        }
      } finally {
        await client.query(`RESET ROLE`).catch(() => undefined)
        client.release()
        await pool.query(`REVOKE CREATE ON SCHEMA public FROM a51_app`)   // the window closes on every exit
      }
      expect(await ledgerFiles()).toEqual([...MIGRATION_FILES])
      const owner = await pool.query<{ n: number }>(
        `SELECT COUNT(*)::int AS n FROM pg_class c JOIN pg_roles r ON r.oid = c.relowner
         WHERE c.relkind = 'r' AND c.relname = ANY($1) AND r.rolname = 'a51_app'`, [KA_TABLES])
      expect(owner.rows[0]!.n).toBe(KA_TABLES.length)
      const canCreate = await pool.query<{ ok: boolean }>(`SELECT has_schema_privilege('a51_app', 'public', 'CREATE') AS ok`)
      expect(canCreate.rows[0]!.ok).toBe(false)
    })

    it('every contracted constraint exists validated and every contracted trigger is enabled (pg_catalog proof)', async () => {
      const cons = await pool.query<{ conrelid: string; conname: string; convalidated: boolean }>(
        `SELECT conrelid::regclass::text AS conrelid, conname, convalidated FROM pg_constraint WHERE conname = ANY($1)`,
        [EXPECTED_CONSTRAINTS.map(c => c[1])])
      const present = new Map(cons.rows.map(r => [`${r.conrelid}.${r.conname}`, r.convalidated]))
      expect(EXPECTED_CONSTRAINTS.filter(([t, c]) => present.get(`${t}.${c}`) !== true)).toEqual([])
      const trg = await pool.query<{ relname: string; tgname: string }>(
        `SELECT c.relname, t.tgname FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
         WHERE NOT t.tgisinternal AND t.tgenabled = 'O' AND t.tgname = ANY($1)`, [EXPECTED_TRIGGERS.map(t => t[1])])
      const have = new Set(trg.rows.map(r => `${r.relname}.${r.tgname}`))
      expect(EXPECTED_TRIGGERS.filter(([t, g]) => !have.has(`${t}.${g}`))).toEqual([])
    })

    it('N4: after apply every preflight blocks with its SPECIFIC token, and a plain re-run is BLOCKED (no replay mode)', async () => {
      for (let i = 0; i < PREFLIGHT_FILES.length; i++) {
        await expect(pool.query(preflight(PREFLIGHT_FILES[i]!)))
          .rejects.toThrow(new RegExp(`migration_already_applied :: ${MIGRATION_FILES[i]!.replace('.', '\\.')}`))
      }
      await expect(pool.query(mig(MIGRATION_FILES[4]))).rejects.toThrow(/preflight 1157 BLOCKED[\s\S]*relation_already_exists :: public\.ka_gochara_av_polarity_declaration\b/)
      await expect(pool.query(`SET LOCAL ka_gochara.deliberate_replay = 'on'; ${mig(MIGRATION_FILES[4])}`)).rejects.toThrow(/BLOCKED/)
    })
  })

  // ── N1: legacy '4.0' is untouched ─────────────────────────────────────────
  describe('(b) N1: legacy 4.0 isolation', () => {
    beforeAll(async () => {
      await seedFixtures()
    })

    it('P2/N1: no trigger of ours on any legacy table; our FKs\' RI triggers sit on charts / convention / coverage ONLY (disclosed), never on publication or contacts', async () => {
      const r = await pool.query<{ relname: string; tgname: string; internal: boolean }>(
        `SELECT c.relname, t.tgname, t.tgisinternal AS internal FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
         WHERE c.relname = ANY($1) AND (t.tgname LIKE 'ka\\_gochara\\_%' OR
               (t.tgisinternal AND t.tgconstraint IN (SELECT oid FROM pg_constraint WHERE conrelid::regclass::text LIKE 'ka\\_gochara\\_%' AND confrelid = c.oid)))`,
        [[...LEGACY_TABLES]])
      // nothing of ours on the two tables the legacy publish/rollback path writes
      expect(r.rows.filter(x => x.relname === 'kala_gochara_publication' || x.relname === 'kala_gochara_contacts')).toEqual([])
      // no USER trigger of ours anywhere legacy
      expect(r.rows.filter(x => x.tgname.startsWith('ka_gochara_'))).toEqual([])
      // the disclosed FK surface (P2): PostgreSQL's internal RI triggers exist on exactly these three
      const riTargets = [...new Set(r.rows.filter(x => x.internal).map(x => x.relname))].sort()
      expect(riTargets).toEqual(['charts', 'kala_gochara_convention', 'kala_gochara_coverage'])
    })

    it('legacy publish / re-publish / rollback complete as the runtime role while another session HOLDS the orchestrator chart lock, and write no seal', async () => {
      const holder = await pool.connect()
      const app = await pool.connect()
      try {
        await holder.query(`SELECT pg_advisory_lock(hashtext($1))`, [CHART])   // the orchestrator's own key, held
        await app.query(`SET ROLE a51_app`)
        const ops = [
          `UPDATE kala_gochara_publication SET status = 'published', published_at = now() WHERE chart_id = $1 AND generation = $2`,
          `UPDATE kala_gochara_publication SET status = 'published' WHERE chart_id = $1 AND generation = $2`,
          `DELETE FROM kala_gochara_coverage WHERE chart_id = $1 AND generation = $2`,
          `DELETE FROM kala_gochara_contacts WHERE chart_id = $1 AND generation = $2`,
          `UPDATE kala_gochara_publication SET status = 'rolled_back' WHERE chart_id = $1 AND generation = $2`,
        ]
        for (const sql of ops) {
          const p = app.query(sql, [CHART, LEGACY_GEN])
          expect(await settledWithin(p), sql).toBe('settled')
          await p
        }
      } finally {
        await app.query(`RESET ROLE`).catch(() => undefined)
        await holder.query(`SELECT pg_advisory_unlock(hashtext($1))`, [CHART]).catch(() => undefined)
        app.release(); holder.release()
      }
      expect(await sealCount(LEGACY_GEN)).toBe(0)
      const status = await pool.query<{ status: string }>(`SELECT status FROM kala_gochara_publication WHERE chart_id = $1 AND generation = $2`, [CHART, LEGACY_GEN])
      expect(status.rows[0]!.status).toBe('rolled_back')
    })

    it('the seal function and every governed table refuse legacy generations v1 / 3.0 / 4.0 / 4.1', async () => {
      for (const g of ['v1', '3.0', '4.0', '4.1']) {
        await expect(pool.query(`SELECT ka_gochara_seal_generation($1, $2)`, [CHART, g])).rejects.toThrow(/not governed by the A5\.1 contract/)
      }
      await expect(seedLedger(pool, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: '4.1' })).rejects.toThrow(/kgc_generation_governed_ck/)
      await expect(pool.query(
        `INSERT INTO ka_gochara_generation_seal (chart_id, generation, manifest_id) VALUES ($1, '4.0', gen_random_uuid())`, [CHART]))
        .rejects.toThrow(/not governed by the A5\.1 contract/)
    })
  })

  // ── Rulings A/B: the family keys, the enforced order, the real topology ──
  describe('(c) N12/N13/N2/N5: the Gochara-5 family keys', () => {
    const ORCH_CHART_KEY = `SELECT pg_advisory_lock(hashtext($1))`            // pipeline/orchestrator/locks.py acquire_chart_lock
    const ORCH_GLOBAL_KEY = `SELECT pg_advisory_lock(hashtext('nirmana-global-assets'))`
    const ORCH_UNLOCK_ALL = `SELECT pg_advisory_unlock_all()`
    const predicateInsert = (id: string) =>
      `INSERT INTO ka_gochara_predicate (predicate_id, rule_version, operator, operands) VALUES ('${id}', 'v1', 'eq', '{"left":"a","right":"b"}')`
    async function waitState(pid: number): Promise<{ wait_event_type: string | null; wait_event: string | null }> {
      const r = await pool.query<{ wait_event_type: string | null; wait_event: string | null }>(
        `SELECT wait_event_type, wait_event FROM pg_stat_activity WHERE pid = $1`, [pid])
      return r.rows[0]!
    }
    async function pidOf(c: Q): Promise<number> {
      return (await c.query<{ pid: number }>(`SELECT pg_backend_pid() AS pid`)).rows[0]!.pid
    }
    const base_sky_event = () => `INSERT INTO ka_gochara_sky_event (event_id, physical_object_id, convention_id, body, event_kind, occurrence_ordinal,
         t_exact, longitude, solver_method, delta_lambda, delta_t, precision_regime, coverage)`

    it('N12: the REAL runner topology — the main connection holds the orchestrator\'s session locks while a WORKER connection writes and COMPLETES; an unrelated writer and the seal are excluded until the worker commits', async () => {
      const main = await pool.connect()     // runner.py: the scheduler's MAIN connection
      const worker = await pool.connect()   // runner.py: an in-flight asset's OWN connection (asset_runner → writer)
      const other = await pool.connect()    // another session's worker, or the publication path
      try {
        await main.query(ORCH_CHART_KEY, [CHART])   // held for the whole run (runner.py ~1092–1212)
        await main.query(ORCH_GLOBAL_KEY)
        const held = await main.query<{ n: number }>(
          `SELECT COUNT(*)::int AS n FROM pg_locks WHERE locktype = 'advisory' AND pid = pg_backend_pid() AND granted`)
        expect(held.rows[0]!.n).toBe(2)

        await worker.query('BEGIN')
        // the writer's per-chart delete-then-insert (§N.3) on its worker connection
        const del = worker.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_2])
        expect(await settledWithin(del), 'worker DELETE must not wait on the orchestrator\'s keys').toBe('settled')
        await del
        const ins = seedLedger(worker, { id: CID_2, objectId: OBJ_MARS, ordinal: 2, generation: GEN_L })
        expect(await settledWithin(ins), 'worker INSERT must not wait on the orchestrator\'s keys').toBe('settled')
        await ins
        const rec = insertRecord(worker, { generation: GEN_L, contactId: CID_2 })   // chart → global SHARED
        expect(await settledWithin(rec), 'worker record INSERT must not wait on the orchestrator\'s keys').toBe('settled')
        await rec

        // an unrelated second writer (another session's worker) is excluded by the FAMILY key …
        await other.query('BEGIN')
        const otherPid = await pidOf(other)
        const otherWrite = other.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_1])
        expect(await settledWithin(otherWrite)).toBe('pending')
        expect(await waitState(otherPid)).toEqual({ wait_event_type: 'Lock', wait_event: 'advisory' })
        // … until the worker commits; the main connection never released anything
        await worker.query('COMMIT')
        await otherWrite
        await other.query('ROLLBACK')
        // the seal function is excluded the same way (it takes the chart family key)
        await worker.query('BEGIN')
        await worker.query(`SELECT ka_gochara_lock_chart($1)`, [CHART])
        await other.query('BEGIN')
        const seal = other.query(`SELECT ka_gochara_seal_generation($1, $2)`, [CHART, GEN_L])
        expect(await settledWithin(seal)).toBe('pending')
        await worker.query('COMMIT')
        await expect(seal).rejects.toThrow(/no published manifest/)   // proceeds, then honestly refuses (candidate)
        await other.query('ROLLBACK')
        const stillHeld = await main.query<{ n: number }>(
          `SELECT COUNT(*)::int AS n FROM pg_locks WHERE locktype = 'advisory' AND pid = pg_backend_pid() AND granted`)
        expect(stillHeld.rows[0]!.n).toBe(2)
        // candidate-generation cleanup of the worker's record (the later N13 cases delete its contact)
        await pool.query(`DELETE FROM ka_gochara_relationship_record WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_L])
      } finally {
        await main.query(ORCH_UNLOCK_ALL).catch(() => undefined)
        await worker.query('ROLLBACK').catch(() => undefined)
        await other.query('ROLLBACK').catch(() => undefined)
        main.release(); worker.release(); other.release()
      }
      const rows = await pool.query<{ n: number }>(`SELECT COUNT(*)::int AS n FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_L])
      expect(rows.rows[0]!.n).toBe(2)
    })

    it('N12: governed writes never wait on the orchestrator\'s session keys (the round-4 defect, inverted)', async () => {
      const holder = await pool.connect()
      try {
        await holder.query(ORCH_CHART_KEY, [CHART])
        await holder.query(ORCH_GLOBAL_KEY)
        const del = pool.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_S, CID_1])
        expect(await settledWithin(del)).toBe('settled')
        await del
        await seedLedger(pool, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: GEN_S })
        const ins = pool.query(predicateInsert('q9'))
        expect(await settledWithin(ins)).toBe('settled')
        await ins
      } finally {
        await holder.query(ORCH_UNLOCK_ALL).catch(() => undefined)
        holder.release()
      }
    })

    it('N13: the fixed order is ENFORCED in-transaction — global-EXCLUSIVE→chart and chart→global-EXCLUSIVE are refused; chart→global-SHARED is the legal mix', async () => {
      // a registry mutation followed by a chart-scoped mutation in ONE transaction
      await expect(tx(async c => {
        await c.query(predicateInsert('q_order_1'))
        await c.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_2])
      })).rejects.toThrow(/lock-order violation[\s\S]*already holds the gochara5 GLOBAL family key EXCLUSIVE/)
      await expect(tx(async c => {
        await c.query(predicateInsert('q_order_2'))
        await seedLedger(c, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: GEN_X })   // INSERT path (row guard)
      })).rejects.toThrow(/lock-order violation/)
      // a chart-scoped mutation followed by a registry mutation in ONE transaction
      await expect(tx(async c => {
        await c.query(`UPDATE ka_gochara_contact SET created_at = created_at WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_L])
        await c.query(predicateInsert('q_order_3'))
      })).rejects.toThrow(/lock-order violation[\s\S]*already holds a chart family key/)
      // a chart-scoped mutation that reads rule-path seal state (chart → global SHARED) is fine, and
      // a registry mutation after it is still refused (SHARED holder may not upgrade)
      await expect(tx(async c => {
        const r = await insertRecord(c, { generation: GEN_L, contactId: CID_1 })
        const gs = await c.query<{ v: string }>(`SELECT current_setting('gochara5.global_shared', true) AS v`)
        expect(gs.rows[0]!.v).toBe('on')
        await c.query(`DELETE FROM ka_gochara_relationship_record WHERE record_id = $1`, [r])   // candidate cleanup, same tx
      })).resolves.toBeUndefined()
      await expect(tx(async c => {
        await insertRecord(c, { generation: GEN_L, contactId: CID_1 })
        await c.query(predicateInsert('q_order_4'))
      })).rejects.toThrow(/lock-order violation/)
      // the seal function is chart-first too: it refuses inside a registry transaction
      await expect(tx(async c => {
        await c.query(predicateInsert('q_order_5'))
        await c.query(`SELECT ka_gochara_seal_generation($1, $2)`, [CHART, GEN_L])
      })).rejects.toThrow(/lock-order violation/)
      const none = await pool.query(`SELECT 1 FROM ka_gochara_predicate WHERE predicate_id LIKE 'q\\_order\\_%'`)
      expect(none.rowCount).toBe(0)
    })

    it('N13: a registry mutation never waits for a chart-only holder; it waits only for a SHARED reader (a record writer)', async () => {
      const a = await pool.connect()
      try {
        await a.query('BEGIN')
        await a.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_2])   // chart key held
        const reg = pool.query(predicateInsert('q_free'))
        expect(await settledWithin(reg), 'registry mutation must not wait for a chart key').toBe('settled')
        await reg
        await a.query('ROLLBACK')

        await a.query('BEGIN')
        await insertRecord(a, { generation: GEN_L, contactId: CID_1 })   // chart key + global SHARED held
        const reg2 = pool.query(predicateInsert('q_waits'))
        expect(await settledWithin(reg2), 'registry mutation waits for a SHARED reader').toBe('pending')
        await a.query('ROLLBACK')
        await reg2
      } finally {
        await a.query('ROLLBACK').catch(() => undefined)
        a.release()
      }
    })

    it('N13: the family key precedes the tuple lock — the reviewer\'s UPDATE/DELETE inversion cannot deadlock (B waits on the ADVISORY lock, never a tuple)', async () => {
      const a = await pool.connect()
      const b = await pool.connect()
      try {
        // DELETE/DELETE: A takes the chart key + X's tuple; B wants Y (then would want X); A then wants Y
        await a.query('BEGIN')
        await a.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_1])   // X
        await b.query('BEGIN')
        const bPid = await pidOf(b)
        const bDel = b.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_2])   // Y
        expect(await settledWithin(bDel)).toBe('pending')
        expect(await waitState(bPid)).toEqual({ wait_event_type: 'Lock', wait_event: 'advisory' })   // at the STATEMENT trigger, before any tuple
        const aDel = a.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_2])   // A wants Y: no deadlock
        expect(await settledWithin(aDel)).toBe('settled')
        expect((await aDel).rowCount).toBe(1)
        await a.query('COMMIT')
        expect((await bDel).rowCount).toBe(0)   // Y was gone when B finally read it
        await b.query('COMMIT')
        await seedLedger(pool, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: GEN_L })
        await seedLedger(pool, { id: CID_2, objectId: OBJ_MARS, ordinal: 2, generation: GEN_L })

        // UPDATE/DELETE: A updates X (tuple lock), B deletes Y, A deletes Y
        await a.query('BEGIN')
        await a.query(`UPDATE ka_gochara_contact SET created_at = created_at WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_1])
        await b.query('BEGIN')
        const bDel2 = b.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_2])
        expect(await settledWithin(bDel2)).toBe('pending')
        expect(await waitState(bPid)).toEqual({ wait_event_type: 'Lock', wait_event: 'advisory' })
        const aDel2 = a.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_2])
        expect(await settledWithin(aDel2)).toBe('settled')
        await a.query('ROLLBACK')   // A gives up: B proceeds and deletes Y itself
        expect((await bDel2).rowCount).toBe(1)
        await b.query('ROLLBACK')

        // the same on the record/window tables (statement lock on every chart-scoped table)
        const r1 = await tx(c => insertRecord(c, { generation: GEN_L, contactId: CID_1 }))
        const r2 = await tx(c => insertRecord(c, { generation: GEN_L, contactId: CID_2 }))
        await a.query('BEGIN')
        await a.query(`UPDATE ka_gochara_relationship_record SET severity = 0.5 WHERE record_id = $1`, [r1])
        await b.query('BEGIN')
        const bUpd = b.query(`UPDATE ka_gochara_relationship_record SET severity = 0.5 WHERE record_id = $1`, [r2])
        expect(await settledWithin(bUpd)).toBe('pending')
        expect(await waitState(bPid)).toEqual({ wait_event_type: 'Lock', wait_event: 'advisory' })
        const aUpd = a.query(`UPDATE ka_gochara_relationship_record SET severity = 0.5 WHERE record_id = $1`, [r2])
        expect(await settledWithin(aUpd)).toBe('settled')
        await a.query('COMMIT')
        await bUpd
        await b.query('COMMIT')
      } finally {
        await a.query('ROLLBACK').catch(() => undefined)
        await b.query('ROLLBACK').catch(() => undefined)
        a.release(); b.release()
      }
    })

    it('N13 substrate order: substrate/identity/bridge/declaration writes need the chart key FIRST — no context is refused; the reviewer\'s unique-entry and sky-event tuple schedules are serialised, never deadlocked (main connection holding its session locks)', async () => {
      const EVENT_L = '10000000-0000-4000-8000-000000000022'
      const CID_Y = '10000000-0000-4000-8000-00000000001a'   // (OBJ_SAT_CONJ, 1) — a new identity under a committed object
      const identityInsert = `INSERT INTO ka_gochara_contact_identity (contact_id, physical_object_id, occurrence_ordinal) VALUES ($1, $2, 1) ON CONFLICT DO NOTHING`
      const main = await pool.connect()
      const a = await pool.connect()
      const b = await pool.connect()
      try {
        await main.query(ORCH_CHART_KEY, [CHART])
        await main.query(ORCH_GLOBAL_KEY)

        // no chart context → refused before any lock, on every substrate table
        await expect(pool.query(identityInsert, [CID_Y, OBJ_SAT_CONJ])).rejects.toThrow(/ka_gochara_contact_identity write refused .* no chart context/)
        await expect(pool.query(`INSERT INTO ka_gochara_sky_convention (convention_id, ephemeris_generation, ayanamsha, node_convention, grid, method_version, domain_start, domain_end) VALUES ('c-noctx','de441','lahiri','mean','1s','m1','2025-01-01T00:00Z','2026-01-01T00:00Z')`)).rejects.toThrow(/no chart context/)
        await expect(pool.query(`INSERT INTO ka_gochara_convention_bridge (kala_convention_id, sky_convention_id) VALUES ($1, $2)`, [LEGACY_CONV_UNBRIDGED, CONV])).rejects.toThrow(/no chart context/)
        await expect(pool.query(`INSERT INTO ka_gochara_av_polarity_declaration (convention, benefic_mark_name, malefic_mark_name, source_ref, applies_to_fact_categories) VALUES ('c-noctx','a','b','x', ARRAY['y'])`)).rejects.toThrow(/no chart context/)
        // a registry transaction cannot write substrate either: without a context it is refused, with a declared
        // context it would need the chart key, which the registry marker forbids (lock-order violation)
        await expect(tx(async c => {
          await c.query(predicateInsert('q_substrate'))
          await c.query(identityInsert, [CID_Y, OBJ_SAT_CONJ])
        })).rejects.toThrow(/no chart context/)
        await expect(tx(async c => {
          await c.query(`SELECT set_config('gochara5.chart', $1, true)`, [CHART])
          await c.query(predicateInsert('q_substrate'))
          await c.query(identityInsert, [CID_Y, OBJ_SAT_CONJ])
        })).rejects.toThrow(/lock-order violation/)
        // with a declared context the write takes the chart family key first
        await tx(async c => {
          await c.query(`SELECT set_config('gochara5.chart', $1, true)`, [CHART])
          await c.query(`${base_sky_event()} VALUES ($1, $2, $3, 'saturn', 'sign_ingress', 2, '2025-04-10T00:00Z', 180.0, 'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}')`, [EVENT_L, OBJ_SAT_SPAN, CONV])
          const held = await c.query<{ n: number; locked: string }>(
            `SELECT COUNT(*)::int AS n, current_setting('gochara5.chart_locked', true) AS locked FROM pg_locks
             WHERE locktype = 'advisory' AND pid = pg_backend_pid() AND granted AND mode = 'ExclusiveLock'`)
          expect(held.rows[0]).toEqual({ n: 1, locked: 'on' })   // exactly the chart family key, taken by the statement trigger
        })

        // schedule 1 (unique entry): A holds C; B inserts identity Y — B must take C first, so it waits on the ADVISORY key
        await a.query('BEGIN')
        await a.query(`UPDATE ka_gochara_contact SET created_at = created_at WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_1])
        await b.query('BEGIN')
        const bPid = await pidOf(b)
        await b.query(`SELECT set_config('gochara5.chart', $1, true)`, [CHART])
        const bIns = b.query(identityInsert, [CID_Y, OBJ_SAT_CONJ])
        expect(await settledWithin(bIns)).toBe('pending')
        expect(await waitState(bPid)).toEqual({ wait_event_type: 'Lock', wait_event: 'advisory' })   // before any unique-index entry
        const aIns = a.query(identityInsert, [CID_Y, OBJ_SAT_CONJ])   // A inserts the same Y: no wait on B (B holds nothing)
        expect(await settledWithin(aIns)).toBe('settled')
        expect((await aIns).rowCount).toBe(1)
        await a.query('COMMIT')
        expect((await bIns).rowCount).toBe(0)   // B proceeds after A: Y already exists (ON CONFLICT DO NOTHING)
        await seedLedger(b, { id: CID_Y, objectId: OBJ_SAT_CONJ, ordinal: 1, generation: GEN_L, body: 'saturn' })   // B's ledger row: C already held
        await b.query('COMMIT')

        // schedule 2 (tuple): A holds C; B updates a sky event (allowed no-op) — B must take C first; A's update of the same row does not wait
        await a.query('BEGIN')
        await a.query(`UPDATE ka_gochara_contact SET created_at = created_at WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_1])
        await b.query('BEGIN')
        await b.query(`SELECT set_config('gochara5.chart', $1, true)`, [CHART])
        const bUpd = b.query(`UPDATE ka_gochara_sky_event SET longitude = longitude WHERE event_id = $1`, [EVENT_L])
        expect(await settledWithin(bUpd)).toBe('pending')
        expect(await waitState(bPid)).toEqual({ wait_event_type: 'Lock', wait_event: 'advisory' })   // before any tuple lock
        const aUpd = a.query(`UPDATE ka_gochara_sky_event SET longitude = longitude WHERE event_id = $1`, [EVENT_L])
        expect(await settledWithin(aUpd)).toBe('settled')
        await a.query('COMMIT')
        expect((await bUpd).rowCount).toBe(1)
        await b.query(`UPDATE ka_gochara_contact SET created_at = created_at WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_1])   // B's chart write: C already held
        await b.query('COMMIT')
        const stillHeld = await main.query<{ n: number }>(`SELECT COUNT(*)::int AS n FROM pg_locks WHERE locktype = 'advisory' AND pid = pg_backend_pid() AND granted`)
        expect(stillHeld.rows[0]!.n).toBe(2)
      } finally {
        await main.query(ORCH_UNLOCK_ALL).catch(() => undefined)
        await a.query('ROLLBACK').catch(() => undefined)
        await b.query('ROLLBACK').catch(() => undefined)
        main.release(); a.release(); b.release()
      }
      await pool.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_Y])   // candidate cleanup
    })

    it('N18 one chart per transaction: bound at the lock boundary before any substrate acquisition; a different chart is refused before another key; non-canonical charts are refused (D-SCOPE); the reviewer\'s mixed-context schedules are refused outright (main connection holding its session locks)', async () => {
      const D = OTHER_CHART
      const CID_Z = '10000000-0000-4000-8000-00000000001b'   // (OBJ_SAT_CONJ, 2)
      const identityInsert = `INSERT INTO ka_gochara_contact_identity (contact_id, physical_object_id, occurrence_ordinal) VALUES ($1, $2, 2) ON CONFLICT DO NOTHING`
      const EVENT_L = '10000000-0000-4000-8000-000000000022'   // inserted by the substrate-order case above
      const advisoryHeld = async (c: Q) => (await c.query<{ n: number }>(`SELECT COUNT(*)::int AS n FROM pg_locks WHERE locktype = 'advisory' AND pid = pg_backend_pid() AND granted`)).rows[0]!.n
      const main = await pool.connect()
      const a = await pool.connect()
      const b = await pool.connect()
      try {
        await main.query(ORCH_CHART_KEY, [CHART])
        await main.query(ORCH_GLOBAL_KEY)

        // the seal function and the lock helper refuse a non-canonical chart before any key
        await expect(pool.query(`SELECT ka_gochara_seal_generation($1, $2)`, [D, GEN])).rejects.toThrow(/not governed by the Gochara-5 contract \(D-SCOPE/)
        await b.query('BEGIN')
        await b.query('SAVEPOINT s')
        await expect(b.query(`SELECT ka_gochara_lock_chart($1)`, [D])).rejects.toThrow(/not governed by the Gochara-5 contract/)
        await b.query('ROLLBACK TO SAVEPOINT s')
        expect(await advisoryHeld(b)).toBe(0)
        // a declared non-canonical context is refused at the substrate write, before any key
        await b.query(`SELECT set_config('gochara5.chart', $1, true)`, [D])
        await b.query('SAVEPOINT s2')
        await expect(b.query(identityInsert, [CID_Z, OBJ_SAT_CONJ])).rejects.toThrow(/not governed by the Gochara-5 contract/)
        await b.query('ROLLBACK TO SAVEPOINT s2')
        expect(await advisoryHeld(b)).toBe(0)
        await b.query('ROLLBACK')
        // bound to C: a different chart is refused BEFORE another family key is requested (binding precedes scope)
        await b.query('BEGIN')
        await b.query(`SELECT ka_gochara_lock_chart($1)`, [CHART])
        expect(await advisoryHeld(b)).toBe(1)
        await b.query('SAVEPOINT s3')
        await expect(b.query(`SELECT ka_gochara_lock_chart($1)`, [D])).rejects.toThrow(/bound to chart 482012f1-710e-4a25-994a-93821f5871aa and may not take the family key of chart 00000000-0000-4000-8000-0000000000aa/)
        await b.query('ROLLBACK TO SAVEPOINT s3')
        expect(await advisoryHeld(b)).toBe(1)   // still exactly C
        // bound to C but declaring context D: the substrate write is refused (it would run under C's key while claiming D)
        await b.query(`SELECT set_config('gochara5.chart', $1, true)`, [D])
        await b.query('SAVEPOINT s4')
        await expect(b.query(identityInsert, [CID_Z, OBJ_SAT_CONJ])).rejects.toThrow(/bound to chart 482012f1-710e-4a25-994a-93821f5871aa but declares context 00000000-0000-4000-8000-0000000000aa/)
        await b.query('ROLLBACK TO SAVEPOINT s4')
        await b.query('ROLLBACK')

        // the reviewer's mixed-context schedule 1: A holds C; B declares D and inserts Y — refused at once, so A's
        // insert of the same identity never waits and B never comes to wait for C while holding a unique entry
        await a.query('BEGIN')
        await a.query(`UPDATE ka_gochara_contact SET created_at = created_at WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_1])
        await b.query('BEGIN')
        await b.query(`SELECT set_config('gochara5.chart', $1, true)`, [D])
        await expect(b.query(identityInsert, [CID_Z, OBJ_SAT_CONJ])).rejects.toThrow(/not governed by the Gochara-5 contract/)
        const aIns = a.query(identityInsert, [CID_Z, OBJ_SAT_CONJ])
        expect(await settledWithin(aIns)).toBe('settled')
        expect((await aIns).rowCount).toBe(1)
        await b.query('ROLLBACK')
        await a.query('COMMIT')
        // the sky-event tuple variant: B declares D and updates the event — refused before any tuple lock; A's update settles
        await a.query('BEGIN')
        await a.query(`UPDATE ka_gochara_contact SET created_at = created_at WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_L, CID_1])
        await b.query('BEGIN')
        await b.query(`SELECT set_config('gochara5.chart', $1, true)`, [D])
        await expect(b.query(`UPDATE ka_gochara_sky_event SET longitude = longitude WHERE event_id = $1`, [EVENT_L])).rejects.toThrow(/not governed by the Gochara-5 contract/)
        const aUpd = a.query(`UPDATE ka_gochara_sky_event SET longitude = longitude WHERE event_id = $1`, [EVENT_L])
        expect(await settledWithin(aUpd)).toBe('settled')
        await b.query('ROLLBACK')
        await a.query('COMMIT')
        const stillHeld = await main.query<{ n: number }>(`SELECT COUNT(*)::int AS n FROM pg_locks WHERE locktype = 'advisory' AND pid = pg_backend_pid() AND granted`)
        expect(stillHeld.rows[0]!.n).toBe(2)
      } finally {
        await main.query(ORCH_UNLOCK_ALL).catch(() => undefined)
        await a.query('ROLLBACK').catch(() => undefined)
        await b.query('ROLLBACK').catch(() => undefined)
        main.release(); a.release(); b.release()
      }
    })

    it('REPEATABLE READ (and SERIALIZABLE) writes are refused explicitly', async () => {
      for (const level of ['REPEATABLE READ', 'SERIALIZABLE']) {
        const c = await pool.connect()
        try {
          await c.query(`BEGIN ISOLATION LEVEL ${level}`)
          await expect(c.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_S, CID_1]))
            .rejects.toThrow(/require READ COMMITTED/)
          await c.query('ROLLBACK')
        } finally {
          c.release()
        }
      }
    })

    it('N2 rebuild-first: the publication path waits behind the rebuild, then seals what remains', async () => {
      const a = await pool.connect()
      const b = await pool.connect()
      try {
        await a.query('BEGIN')
        await a.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_R, CID_R])
        // the reviewer's inversion: the rebuild now touches manifest metadata too — no deadlock,
        // because the publication path takes the chart lock BEFORE touching the manifest row
        await a.query(`UPDATE kala_gochara_publication SET row_counts = '{"contacts":0}' WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_R])
        await b.query('BEGIN')
        const publish = publishAndSeal(b, GEN_R)
        expect(await settledWithin(publish)).toBe('pending')
        await a.query('COMMIT')
        await publish
        await b.query('COMMIT')
      } finally {
        a.release(); b.release()
      }
      expect(await sealCount(GEN_R)).toBe(1)
      const gone = await pool.query(`SELECT 1 FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_R])
      expect(gone.rowCount).toBe(0)
      await expect(seedLedger(pool, { id: CID_R, objectId: OBJ_MARS, ordinal: 6, generation: GEN_R })).resolves.toBeUndefined() // append stays permitted
      await expect(pool.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_R])).rejects.toThrow(/SEALED/)
    })

    it('N2 publish-first: the rebuild waits behind the publication, then is refused', async () => {
      const a = await pool.connect()
      const b = await pool.connect()
      try {
        await b.query('BEGIN')
        await publishAndSeal(b, GEN_P)
        const del = a.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_P, CID_P])
        expect(await settledWithin(del)).toBe('pending')
        await b.query('COMMIT')
        await expect(del).rejects.toThrow(/SEALED/)
      } finally {
        a.release(); b.release()
      }
      const kept = await pool.query(`SELECT 1 FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_P, CID_P])
      expect(kept.rowCount).toBe(1)
    })

    it('N5 membership-first: sealing waits for the in-flight membership and includes it', async () => {
      const a = await pool.connect()
      const b = await pool.connect()
      try {
        await a.query('BEGIN')
        await a.query(`INSERT INTO ka_gochara_rule_path_prerequisite (path_id, rule_version, ordinal, predicate_id, predicate_rule_version) VALUES ('P3','v1',1,'q2','v1')`)
        const seal = b.query(`INSERT INTO ka_gochara_rule_path_seal (path_id, rule_version) VALUES ('P3','v1')`)
        expect(await settledWithin(seal)).toBe('pending')
        await a.query('COMMIT')
        await seal
      } finally {
        a.release(); b.release()
      }
      const members = await pool.query<{ n: number }>(`SELECT COUNT(*)::int AS n FROM ka_gochara_rule_path_prerequisite WHERE path_id = 'P3' AND rule_version = 'v1'`)
      expect(members.rows[0]!.n).toBe(1)
      await expect(pool.query(`INSERT INTO ka_gochara_rule_path_prerequisite (path_id, rule_version, ordinal, predicate_id, predicate_rule_version) VALUES ('P3','v1',2,'q1','v1')`)).rejects.toThrow(/SEALED/)
    })

    it('N5 seal-first: a membership insert waits for the in-flight seal, then is refused', async () => {
      const a = await pool.connect()
      const b = await pool.connect()
      try {
        await b.query('BEGIN')
        await b.query(`INSERT INTO ka_gochara_rule_path_seal (path_id, rule_version) VALUES ('P5','v1')`)
        const member = a.query(`INSERT INTO ka_gochara_rule_path_prerequisite (path_id, rule_version, ordinal, predicate_id, predicate_rule_version) VALUES ('P5','v1',1,'q1','v1')`)
        expect(await settledWithin(member)).toBe('pending')
        await b.query('COMMIT')
        await expect(member).rejects.toThrow(/SEALED/)
      } finally {
        a.release(); b.release()
      }
    })

    it('N5: record production waits for an in-flight membership construction, then is refused until the version is sealed', async () => {
      const a = await pool.connect()
      try {
        await a.query('BEGIN')
        await a.query(`INSERT INTO ka_gochara_rule_path_prerequisite (path_id, rule_version, ordinal, predicate_id, predicate_rule_version) VALUES ('P6','v1',1,'q1','v1')`)
        const produce = tx(c => insertRecord(c, { pathId: 'P6' }))
        expect(await settledWithin(produce)).toBe('pending')
        await a.query('COMMIT')
        await expect(produce).rejects.toThrow(/not sealed/)
      } finally {
        a.release()
      }
      await pool.query(`INSERT INTO ka_gochara_rule_path_seal (path_id, rule_version) VALUES ('P6','v1')`)
      await expect(tx(c => insertRecord(c, { pathId: 'P6' }))).resolves.toBeDefined()
    })
  })

  // ── Behavioural contract (F1–F7, F11, N6–N10) ─────────────────────────────
  describe('(d) behavioural contract', () => {
    it('F1/O-RX-1: one identity per (object, ordinal); the SAME contact id is owned by several generations; ownership-bound references', async () => {
      const ordinals = await pool.query(`SELECT occurrence_ordinal FROM ka_gochara_contact_identity WHERE physical_object_id = $1 ORDER BY 1`, [OBJ_MARS])
      expect(ordinals.rows.map(r => r.occurrence_ordinal)).toEqual([1, 2, 3, 4, 5, 6, 7, 8])
      const owners = await pool.query(`SELECT generation FROM ka_gochara_contact WHERE contact_id = $1 ORDER BY 1`, [CID_1])
      expect(owners.rows.map(r => r.generation)).toEqual([GEN, GEN_F, GEN_S, GEN_L])
      await expect(tx(c => seedIdentity(c, uuid(), OBJ_MARS, 1))).rejects.toThrow(/ka_gochara_contact_identity_ordinal_uq/)
      await expect(seedLedger(pool, { id: CID_1, objectId: OBJ_MARS, ordinal: 2, generation: GEN_X })).rejects.toThrow(/ka_gochara_contact_identity_fk/)
      await expect(tx(c => insertRecord(c, { contactId: CID_OLD_ONLY }))).rejects.toThrow(/is not owned by \(chart 482012f1-710e-4a25-994a-93821f5871aa, generation 5\.4\) \(F1\)/)
      await pool.query(`ALTER TABLE ka_gochara_relationship_record DISABLE TRIGGER ka_gochara_rr_2_coverage_guard`)
      try {
        await expect(tx(c => insertRecord(c, { contactId: CID_OLD_ONLY }))).rejects.toThrow(/kgrr_contact_fk/)
      } finally {
        await pool.query(`ALTER TABLE ka_gochara_relationship_record ENABLE TRIGGER ka_gochara_rr_2_coverage_guard`)
      }
      await expect(tx(c => insertRecord(c, { contactId: CID_OLD_ONLY, generation: GEN_C }))).resolves.toBeDefined()
    })

    it('N6: a changed solved reading under the same contact id in another generation is refused; NULL enrichment coexists', async () => {
      await expect(seedLedger(pool, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: GEN_X, tExact: '2025-03-12T00:00Z' }))
        .rejects.toThrow(/already carries a different solved reading in another generation/)
      await expect(seedLedger(pool, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: GEN_X, truncated: true })).resolves.toBeUndefined()
      const enrich = (tExact: string) => pool.query(
        `UPDATE ka_gochara_contact SET t_out = '2025-03-21T00:00Z', t_exact = $3, solver_method = 'swiss_refined',
           delta_lambda = 0.001, delta_t = 60, precision_regime = 'standard', coverage = '{"truncated":false}'::jsonb
         WHERE chart_id = $1 AND generation = $2 AND contact_id = $4`, [CHART, GEN_X, tExact, CID_1])
      await expect(enrich('2025-03-12T00:00Z')).rejects.toThrow(/different solved reading/)
      await expect(enrich('2025-03-10T00:00Z')).resolves.toBeDefined()
    })

    it('F7: physical relation is exact along the whole chain (object → contact → record; object → sky event)', async () => {
      await expect(tx(c => insertRecord(c, { relation: 'aspect' }))).rejects.toThrow(/kgrr_contact_fk/)
      await expect(tx(c => insertRecord(c, { objectId: OBJ_MARS_ASPECT }))).rejects.toThrow(/kgrr_contact_fk/)
      await expect(tx(c => seedContact(c, { id: uuid(), objectId: OBJ_MARS, ordinal: 9, generation: GEN_F, relation: 'aspect' }))).rejects.toThrow(/ka_gochara_contact_object_fk/)
      await expect(tx(async c => {
        await chartCtx(c)
        await c.query(
          `INSERT INTO ka_gochara_sky_event (event_id, physical_object_id, convention_id, body, event_kind, occurrence_ordinal,
              t_exact, longitude, solver_method, delta_lambda, delta_t, precision_regime, coverage)
           VALUES ($1, $2, $3, 'saturn', 'station', 1, '2025-03-10T00:00Z', 180.0, 'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}')`,
          [uuid(), OBJ_SAT_SPAN, CONV])
      })).rejects.toThrow(/ka_gochara_sky_event_object_fk/)
    })

    it('F2/N9: sealing freezes the record set; contacts may still append; the seal outlives superseded/rolled_back', async () => {
      await pool.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN, CID_2])
      await seedLedger(pool, { id: CID_2, objectId: OBJ_MARS, ordinal: 2, generation: GEN })
      await tx(c => publishAndSeal(c, GEN))
      expect(await sealCount(GEN)).toBe(1)
      const refused = /SEALED/
      await expect(pool.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN, CID_2])).rejects.toThrow(refused)
      for (const later of ['superseded', 'rolled_back']) {
        await pool.query(`UPDATE kala_gochara_publication SET status = $3 WHERE chart_id = $1 AND generation = $2`, [CHART, GEN, later])
        await expect(pool.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN, CID_2])).rejects.toThrow(refused)
        await expect(pool.query(`DELETE FROM ka_gochara_relationship_record WHERE record_id = $1`, [RECORD_1])).rejects.toThrow(refused)
        await expect(pool.query(`UPDATE ka_gochara_relationship_record SET severity = 1 WHERE record_id = $1`, [RECORD_1])).rejects.toThrow(refused)
        await expect(pool.query(`DELETE FROM ka_gochara_eval_window WHERE window_id = $1`, [WINDOW_1])).rejects.toThrow(refused)
        await expect(pool.query(`DELETE FROM ka_gochara_eval_window_record WHERE window_id = $1`, [WINDOW_1])).rejects.toThrow(refused)
        await expect(pool.query(`DELETE FROM ka_gochara_record_prerequisite WHERE record_id = $1`, [RECORD_1])).rejects.toThrow(refused)
      }
      // N9: the published set is frozen — no new record, window, prerequisite or membership row
      await expect(tx(c => insertRecord(c, { generation: GEN }))).rejects.toThrow(/SEALED[\s\S]*INSERT refused/)
      await expect(tx(c => insertWindow(c, { generation: GEN }))).rejects.toThrow(/SEALED[\s\S]*INSERT refused/)
      const other = await tx(c => insertRecord(c, { generation: GEN_F }))
      await expect(addMembership(pool, WINDOW_1, other, { generation: GEN })).rejects.toThrow(/SEALED[\s\S]*INSERT refused|kgewr_record_fk/)
      // contacts keep their spec-explicit append (partition extension, O-RX-1 ordinal 4)
      await expect(tx(c => seedContact(c, { id: uuid(), objectId: OBJ_MARS, ordinal: 9, generation: GEN }))).resolves.toBeUndefined()
      // the seal itself is permanent and honest
      await expect(pool.query(`DELETE FROM ka_gochara_generation_seal WHERE chart_id = $1`, [CHART])).rejects.toThrow(/permanent/)
      await expect(pool.query(`UPDATE ka_gochara_generation_seal SET sealed_at = now()`)).rejects.toThrow(/permanent/)
      await expect(pool.query(`SELECT ka_gochara_seal_generation($1, $2)`, [CHART, GEN_C])).rejects.toThrow(/no published manifest/)
      await expect(pool.query(`INSERT INTO ka_gochara_generation_seal (chart_id, generation, manifest_id) SELECT chart_id, generation, manifest_id FROM kala_gochara_publication WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_C]))
        .rejects.toThrow(/not a published manifest/)
    })

    it('F2: TRUNCATE is refused on every owned table', async () => {
      for (const t of KA_TABLES) await expect(pool.query(`TRUNCATE ${t} CASCADE`)).rejects.toThrow(/TRUNCATE refused/)
    })

    it('F3: a sealed rule version accepts no further membership; a new version is constructed then sealed', async () => {
      await expect(pool.query(`INSERT INTO ka_gochara_rule_path_prerequisite (path_id, rule_version, ordinal, predicate_id, predicate_rule_version) VALUES ('P1','v1',2,'q2','v1')`)).rejects.toThrow(/SEALED/)
      await expect(pool.query(`INSERT INTO ka_gochara_rule_path_soft_factor (path_id, rule_version, factor_id, factor_rule_version) VALUES ('P1','v1','f1','v1')`)).rejects.toThrow(/SEALED/)
      await expect(tx(c => insertRecord(c, { pathId: 'P2', agent: 'saturn', relation: 'occupancy', contactId: null, objectId: OBJ_SAT_CONJ, objectRole: 'occupant', covKind: 'event_class', covKey: 'marriage', results: [] }))).rejects.toThrow(/not sealed/)
      await tx(async c => {
        await c.query(`INSERT INTO ka_gochara_rule_path (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set, object_selector, provenance, operator_role, ruling_ref, score_rule)
                       VALUES ('P1', 'v2', 'dasha_lord', NULL, '["mars"]', '["conjunction"]', '[{"agent":"mars","relation":"conjunction","object_role":"karaka"}]', 'verse_cited', 'scored', NULL, 'within_path_product')`)
        await c.query(`INSERT INTO ka_gochara_rule_path_prerequisite (path_id, rule_version, ordinal, predicate_id, predicate_rule_version) VALUES ('P1','v2',1,'q1','v1'), ('P1','v2',2,'q2','v1')`)
        await c.query(`INSERT INTO ka_gochara_rule_path_seal (path_id, rule_version) VALUES ('P1','v2')`)
      })
      await expect(pool.query(`DELETE FROM ka_gochara_rule_path_seal WHERE path_id = 'P1'`)).rejects.toThrow(/insert-only/)
    })

    it('F4: published non-NULL values never rewritten; enrichment fills NULL/truncated fields; corrections supersede', async () => {
      const refused = /published non-NULL values are immutable/
      await expect(pool.query(`UPDATE ka_gochara_contact SET t_exact = '2025-03-22T00:00Z' WHERE contact_id = $1 AND generation = $2`, [CID_1, GEN_F])).rejects.toThrow(refused)
      await expect(pool.query(`UPDATE ka_gochara_contact SET occurrence_ordinal = 4 WHERE contact_id = $1 AND generation = $2`, [CID_1, GEN_F])).rejects.toThrow(/identity fields are immutable/)
      await expect(pool.query(`UPDATE ka_gochara_contact SET solver_method = 'arc_index_bracket' WHERE contact_id = $1 AND generation = $2`, [CID_1, GEN_F])).rejects.toThrow(/clipped_truncated placeholder/)
      await expect(seedLedger(pool, { id: CID_TRUNC, objectId: OBJ_MARS, ordinal: 3, generation: GEN_X, truncated: true, solver: 'swiss_refined' })).rejects.toThrow(/kgc_truncated_method_ck/)
      await pool.query(
        `UPDATE ka_gochara_contact SET t_out = '2025-03-21T00:00Z', t_exact = '2025-03-20T00:00Z', solver_method = 'swiss_refined',
           delta_lambda = 0.001, delta_t = 60, precision_regime = 'standard', coverage = '{"truncated":false}'::jsonb
         WHERE contact_id = $1 AND generation = $2`, [CID_TRUNC, GEN_F])
      const enriched = await pool.query(`SELECT t_exact, occurrence_ordinal FROM ka_gochara_contact WHERE contact_id = $1 AND generation = $2`, [CID_TRUNC, GEN_F])
      expect(enriched.rows[0]!.t_exact).toBeTruthy()
      expect(enriched.rows[0]!.occurrence_ordinal).toBe(3)
      const CID_C1 = uuid(); const CID_T2X = uuid()
      await expect(tx(c => seedIdentity(c, CID_C1, OBJ_MARS_C1, 1, CID_1))).resolves.toBeUndefined()      // convention-changing correction
      await expect(tx(c => seedIdentity(c, CID_T2X, OBJ_MARS_T2, 1, CID_2))).resolves.toBeUndefined()     // target-changing correction
      await expect(tx(c => seedIdentity(c, uuid(), OBJ_SAT_CONJ, 1, CID_TRUNC))).rejects.toThrow(/SAME body and relation/)
      await expect(tx(c => seedIdentity(c, uuid(), OBJ_MARS_T2, 2, CID_1))).rejects.toThrow(/already superseded/)
      await expect(pool.query(`UPDATE ka_gochara_contact_identity SET occurrence_ordinal = 9 WHERE contact_id = $1`, [CID_1])).rejects.toThrow(/insert-only/)
      await expect(pool.query(`DELETE FROM ka_gochara_contact_identity WHERE contact_id = $1`, [CID_1])).rejects.toThrow(/insert-only/)
    })

    it('N7/N15: extend-then-enrich — the partition horizon is extended AFTER validation, then the contact is enriched; the sealed record\'s precision re-syncs and its facts snapshot is classified `extended`', async () => {
      const rec = await tx(c => insertRecord(c, { generation: GEN_N, contactId: CID_T2, precisionSql: `'{"solver_method":"clipped_truncated","delta_lambda":null,"delta_t":null}'::jsonb` }))
      await tx(c => publishAndSeal(c, GEN_N))
      // the ledger's own sequence (reviewer N15): the coverage horizon grows after the record was validated …
      await pool.query(
        `UPDATE kala_gochara_coverage SET completed_horizon = tstzrange('2025-01-01T00:00Z','2027-01-01T00:00Z','[)')
         WHERE chart_id = $1 AND generation = $2 AND partition_kind = $3 AND partition_key = $4`, [CHART, GEN_N, COV_KIND, COV_KEY])
      // … and only then is the truncated contact solved. The propagation must NOT trip on coverage.
      await expect(pool.query(
        `UPDATE ka_gochara_contact SET t_out = '2025-03-21T00:00Z', t_exact = '2025-03-20T00:00Z', solver_method = 'swiss_refined',
           delta_lambda = 0.001, delta_t = 60, precision_regime = 'standard', coverage = '{"truncated":false}'::jsonb
         WHERE contact_id = $1 AND generation = $2`, [CID_T2, GEN_N])).resolves.toBeDefined()
      const after = await pool.query<{ precision: { solver_method: string; delta_lambda: number; delta_t: number }; coverage_facts: { horizon: { upper: string } } }>(
        `SELECT precision, coverage_facts FROM ka_gochara_relationship_record WHERE record_id = $1`, [rec])
      expect(after.rows[0]!.precision).toEqual({ solver_method: 'swiss_refined', delta_lambda: 0.001, delta_t: 60 })
      expect(after.rows[0]!.coverage_facts.horizon.upper).toBe('2026-01-01T00:00:00.000000Z')   // the validation-time snapshot is retained
      const drift = await pool.query<{ consumer: string; drift: string }>(`SELECT consumer, drift FROM ka_gochara_coverage_drift($1, $2) ORDER BY consumer`, [CHART, GEN_N])
      expect(drift.rows).toEqual([{ consumer: 'relationship_record', drift: 'extended' }])
      // a diverging direct update is still refused; nothing else on the sealed row may change
      await expect(pool.query(`UPDATE ka_gochara_relationship_record SET precision = '{"solver_method":"swiss_refined","delta_lambda":0.002,"delta_t":60}' WHERE record_id = $1`, [rec]))
        .rejects.toThrow(/restates the contact's solved precision/)
      await expect(pool.query(`UPDATE ka_gochara_relationship_record SET severity = 1 WHERE record_id = $1`, [rec])).rejects.toThrow(/SEALED/)
    })

    it('N14/N17/N19: the coverage-facts encoding is a lossless bijection over the accepted domain (AD, years 1000–2999) — NULL elements and element boundaries distinguished; empty, unbounded, ±infinity, BC and out-of-range horizons REFUSED', async () => {
      const H = `tstzrange('2025-01-01T00:00Z','2026-01-01T00:00:00.5Z','[)')`
      const facts = async (h: string, rel: string) =>
        (await pool.query<{ f: Record<string, unknown> }>(`SELECT ka_gochara_coverage_facts('c', ${h}, ${rel}) AS f`)).rows[0]!.f
      // the reviewer's collisions on the array side
      const one = await facts(H, `ARRAY['conjunction']::text[]`)
      const oneAndNull = await facts(H, `ARRAY['conjunction', NULL]::text[]`)
      expect(one.relations_searched).toEqual(['conjunction'])
      expect(oneAndNull.relations_searched).toEqual([null, 'conjunction'])
      const two = await facts(H, `ARRAY['aspect','conjunction']::text[]`)
      const joined = await facts(H, `ARRAY['aspect,conjunction']::text[]`)
      expect(two.relations_searched).toEqual(['aspect', 'conjunction'])
      expect(joined.relations_searched).toEqual(['aspect,conjunction'])
      const bounded = await facts(H, `ARRAY['b','a']::text[]`)
      expect(bounded).toEqual({
        convention_id: 'c',
        horizon: { lower: '2025-01-01T00:00:00.000000Z', lower_inc: true, upper: '2026-01-01T00:00:00.500000Z', upper_inc: false },
        relations_searched: ['a', 'b'],
      })
      const rt = await pool.query<{ ok: boolean }>(
        `SELECT ka_gochara_facts_horizon(ka_gochara_coverage_facts('c', ${H}, ARRAY['a'])) = ${H} AS ok`)
      expect(rt.rows[0]!.ok).toBe(true)
      // N17/N19: the reviewer's infinity collision, the reviewer's H_BC, and every other horizon outside the accepted
      // domain are REFUSED, not encoded — the encoding never meets infinity or a BC/out-of-range year
      for (const h of [`tstzrange('-infinity','infinity','[]')`, `tstzrange('infinity','infinity','[]')`,
        `'empty'::tstzrange`, `'(,)'::tstzrange`, `tstzrange('2025-01-01T00:00Z', NULL, '[)')`,
        `tstzrange('2025-01-01T00:00Z', 'infinity', '[)')`, `NULL::tstzrange`,
        `tstzrange('2025-03-01 00:00:00+00 BC','2025-04-01 00:00:00+00 BC','[)')`,
        `tstzrange('0999-12-31 23:59:59+00','2025-04-01 00:00:00+00','[)')`,
        `tstzrange('2025-03-01 00:00:00+00','3000-01-01 00:00:00+00','[)')`]) {
        await expect(facts(h, `ARRAY['a']::text[]`), h).rejects.toThrow(/unsupported horizon .*\(N17\/N19\)/)
      }
      // N19: within the domain the encoding is a lossless bijection — exact at the era edges, and H_AD ≠ anything else
      const edges = `tstzrange('1000-01-01 00:00:00+00','2999-12-31 23:59:59.999999+00','[]')`
      const edgeFacts = await facts(edges, `ARRAY['a']::text[]`)
      expect(edgeFacts.horizon).toEqual({ lower: '1000-01-01T00:00:00.000000Z', lower_inc: true, upper: '2999-12-31T23:59:59.999999Z', upper_inc: true })
      const rtEdges = await pool.query<{ ok: boolean }>(`SELECT ka_gochara_facts_horizon(ka_gochara_coverage_facts('c', ${edges}, ARRAY['a'])) = ${edges} AS ok`)
      expect(rtEdges.rows[0]!.ok).toBe(true)
      const fin = await pool.query<{ h: string; ok: boolean }>(
        `SELECT h::text AS h, ka_gochara_horizon_finite_ok(h) AS ok FROM unnest(ARRAY[
           tstzrange('2025-03-01 00:00:00+00','2025-04-01 00:00:00+00','[)'),
           tstzrange('2025-03-01 00:00:00+00 BC','2025-04-01 00:00:00+00 BC','[)'),
           tstzrange('1000-01-01 00:00:00+00','1000-01-02 00:00:00+00','[)'),
           tstzrange('0999-12-31 00:00:00+00','1000-01-02 00:00:00+00','[)'),
           tstzrange('2999-12-31 00:00:00+00','2999-12-31 23:59:59.999999+00','[]'),
           tstzrange('2999-12-31 00:00:00+00','3000-01-01 00:00:00+00','[]')]) h`)
      expect(fin.rows.map(r => r.ok)).toEqual([true, false, true, false, true, false])
    })

    it('N17/N19: horizons outside the accepted domain are refused at every consumer boundary — partition, window interval, support interval — and a validated AD consumer whose partition is replaced by an infinite / BC / out-of-range horizon is `incompatible` and unsealable', async () => {
      // a partition whose completed_horizon is the full horizon / the positive-infinity singleton / an omitted bound:
      // the writer cannot even compute its facts (the encoder refuses), and a consumer that brings its own facts is
      // refused by the guard BEFORE any comparison
      const anyFacts = '{"convention_id":"legacy:c0","horizon":{"lower":"2025-01-01T00:00:00.000000Z","lower_inc":true,"upper":"2026-01-01T00:00:00.000000Z","upper_inc":false},"relations_searched":["aspect","conjunction","residence"]}'
      for (const cls of ['travel_event', 'relocation', 'major_gain']) {
        await expect(factsFor(pool, GEN_F, 'event_class', cls), cls).rejects.toThrow(/unsupported horizon .*\(N17\/N19\)/)
        await expect(tx(c => insertRecord(c, { eventClass: cls, covKind: 'event_class', covKey: cls, factsOverride: anyFacts })), cls).rejects.toThrow(/\(N17\/N19\): partition \(event_class, .*\) completed_horizon .* is not a finite, bounded, non-empty range within 1000-01-01 <= t < 3000-01-01 UTC \(AD\)/)
        await expect(tx(c => insertWindow(c, { eventClass: cls, intervalSql: `tstzrange('2025-03-01T00:00Z','2025-04-01T00:00Z')`, factsOverride: anyFacts })), cls).rejects.toThrow(/\(N17\/N19\): partition \(event_class, .*\) completed_horizon .* is not a finite, bounded, non-empty range within 1000-01-01 <= t < 3000-01-01 UTC \(AD\)/)
      }
      // window interval and record support intervals CHECK the same predicate (the guards defer to the CHECK)
      await expect(tx(c => insertWindow(c, { intervalSql: `tstzrange('2025-03-01T00:00Z','infinity','[)')`, peakSql: 'NULL' }))).rejects.toThrow(/kgew_interval_finite_ck/)
      await expect(tx(c => insertWindow(c, { intervalSql: `'(,)'::tstzrange`, peakSql: 'NULL' }))).rejects.toThrow(/kgew_interval_finite_ck/)
      await expect(tx(c => insertWindow(c, { intervalSql: `tstzrange('2025-03-01 00:00:00+00 BC','2025-04-01 00:00:00+00 BC','[)')`, peakSql: 'NULL' }))).rejects.toThrow(/kgew_interval_finite_ck/)
      await expect(tx(c => insertRecord(c, { intervalsSql: `ARRAY[tstzrange('-infinity','2025-03-11T00:00Z','(]')]::tstzrange[]` }))).rejects.toThrow(/kgrr_support_intervals_ck/)
      await expect(tx(c => insertRecord(c, { intervalsSql: `ARRAY[tstzrange('2025-03-09T00:00Z', NULL, '[)')]::tstzrange[]` }))).rejects.toThrow(/kgrr_support_intervals_ck/)
      await expect(tx(c => insertRecord(c, { intervalsSql: `ARRAY[tstzrange('2025-03-09 00:00:00+00 BC','2025-03-11 00:00:00+00 BC')]::tstzrange[]` }))).rejects.toThrow(/kgrr_support_intervals_ck/)
      // the reviewer's drift (N17 and N19's complete sealing counterexample): a valid AD record, AD window and membership;
      // then ONLY the class partition's completed_horizon is replaced by an infinite horizon / the reviewer's H_BC / an out-of-range year
      const { r, w } = await tx(async c => {
        await seedLedger(c, { id: CID_2, objectId: OBJ_MARS, ordinal: 2, generation: GEN_I })
        const r = await insertRecord(c, { generation: GEN_I, contactId: CID_2 })
        const w = await insertWindow(c, { generation: GEN_I })
        await addMembership(c, w, r, { generation: GEN_I })
        return { r, w }
      })
      const drift = async () => (await pool.query<{ consumer: string; consumer_id: string; drift: string; current_facts: unknown }>(
        `SELECT consumer, consumer_id, drift, current_facts FROM ka_gochara_coverage_drift($1, $2) ORDER BY consumer`, [CHART, GEN_I])).rows
      expect((await drift()).map(x => x.drift)).toEqual(['identical', 'identical'])
      // pin the class partition to the reviewer's H_AD and re-bind the candidate window to it, so the H_BC replacement
      // below carries EXACTLY the same digits as the stored AD facts (the era is the only difference)
      const H_AD = `tstzrange('2025-03-01 00:00:00+00','2025-04-01 00:00:00+00','[)')`
      const H_BC = `tstzrange('2025-03-01 00:00:00+00 BC','2025-04-01 00:00:00+00 BC','[)')`
      const setClass = (h: string) => pool.query(`UPDATE kala_gochara_coverage SET completed_horizon = ${h} WHERE chart_id = $1 AND generation = $2 AND partition_kind = 'event_class' AND partition_key = 'marriage'`, [CHART, GEN_I])
      await setClass(H_AD)
      await pool.query(
        `UPDATE ka_gochara_eval_window SET coverage_facts = (
           SELECT ka_gochara_coverage_facts(convention_id, completed_horizon, relations_searched) FROM kala_gochara_coverage
           WHERE chart_id = $2 AND generation = $3 AND partition_kind = 'event_class' AND partition_key = 'marriage')
         WHERE window_id = $1`, [w, CHART, GEN_I])
      expect((await drift()).map(x => x.drift)).toEqual(['identical', 'identical'])
      expect((await pool.query(`SELECT 1 FROM ka_gochara_membership_violations($1, $2)`, [CHART, GEN_I])).rowCount).toBe(0)
      for (const h of [`tstzrange('-infinity','infinity','[]')`, `tstzrange('infinity','infinity','[]')`, `'(,)'::tstzrange`,
        H_BC,   // the reviewer's N19 counterexample: identical digits, BC era — previously encoded identically to H_AD
        `tstzrange('0999-03-01 00:00:00+00','2025-04-01 00:00:00+00','[)')`,
        `tstzrange('2025-03-01 00:00:00+00','3000-01-01 00:00:00+00','[)')`]) {
        await setClass(h)
        const rows = await drift()
        expect(rows.find(x => x.consumer === 'eval_window')!, h).toMatchObject({ consumer_id: w, drift: 'incompatible', current_facts: null })
        expect(rows.find(x => x.consumer === 'relationship_record')!, h).toMatchObject({ consumer_id: r, drift: 'identical' })
        await expect(tx(c => publishAndSeal(c, GEN_I)), h).rejects.toThrow(/INCOMPATIBLE/)
        expect(await sealCount(GEN_I)).toBe(0)
      }
      await setClass(H_AD)
      expect((await drift()).map(x => x.drift)).toEqual(['identical', 'identical'])
      await tx(c => publishAndSeal(c, GEN_I))
      expect(await sealCount(GEN_I)).toBe(1)
    })

    it('N16: the seal boundary carries the complete membership invariant — a VALID membership, then a parent update (relations / convention / window horizon / contributor support), then the seal is REFUSED', async () => {
      const { r, w } = await tx(async c => {
        await seedLedger(c, { id: CID_2, objectId: OBJ_MARS, ordinal: 2, generation: GEN_M })
        const r = await insertRecord(c, { generation: GEN_M, contactId: CID_2 })
        const w = await insertWindow(c, { generation: GEN_M })
        await addMembership(c, w, r, { generation: GEN_M })   // valid at insert
        return { r, w }
      })
      const classCov = (set: string) => pool.query(
        `UPDATE kala_gochara_coverage SET ${set} WHERE chart_id = $1 AND generation = $2 AND partition_kind = 'event_class' AND partition_key = 'marriage'`, [CHART, GEN_M])
      // the candidate window is re-bound to the partition's fresh facts (the reviewer's step 4) — a legal candidate update
      const rebind = (extra = '') => pool.query(
        `UPDATE ka_gochara_eval_window SET coverage_facts = (
           SELECT ka_gochara_coverage_facts(convention_id, completed_horizon, relations_searched) FROM kala_gochara_coverage
           WHERE chart_id = $2 AND generation = $3 AND partition_kind = 'event_class' AND partition_key = 'marriage')${extra}
         WHERE window_id = $1`, [w, CHART, GEN_M])
      const violations = async () => (await pool.query<{ window_id: string; record_id: string; violation: string }>(
        `SELECT window_id, record_id, violation FROM ka_gochara_membership_violations($1, $2)`, [CHART, GEN_M])).rows
      const driftKinds = async () => (await pool.query<{ drift: string }>(`SELECT drift FROM ka_gochara_coverage_drift($1, $2)`, [CHART, GEN_M])).rows.map(x => x.drift)
      expect(await violations()).toEqual([])

      // 1. relations dropped: the class was re-searched for aspect only; the conjunction contributor no longer applies
      await classCov(`relations_searched = ARRAY['aspect']`)
      await expect(rebind()).resolves.toBeDefined()
      expect(await driftKinds()).toEqual(['identical', 'identical'])   // the drift classifier alone would let this through
      expect(await violations()).toEqual([{ window_id: w, record_id: r, violation: expect.stringMatching(/relation 'conjunction' was not searched by the window/) }])
      await expect(tx(c => publishAndSeal(c, GEN_M))).rejects.toThrow(/\(N16 membership invariant\): 1 window membership row/)
      expect(await sealCount(GEN_M)).toBe(0)
      await classCov(`relations_searched = ARRAY['conjunction','aspect','residence']`)
      await rebind()
      expect(await violations()).toEqual([])

      // 2. convention changed on the class partition
      await classCov(`convention_id = '${LEGACY_CONV_UNBRIDGED}'`)
      await rebind()
      expect(await violations()).toEqual([{ window_id: w, record_id: r, violation: expect.stringMatching(/validated under convention 'legacy:c0' but the window was searched under convention 'legacy:c9'/) }])
      await expect(tx(c => publishAndSeal(c, GEN_M))).rejects.toThrow(/N16 membership invariant/)
      await classCov(`convention_id = '${LEGACY_CONV}'`)
      await rebind()
      expect(await violations()).toEqual([])

      // 3. window horizon narrowed past the contributor's support (window interval moved inside the new horizon)
      await classCov(`completed_horizon = tstzrange('2025-03-15T00:00Z','2026-01-01T00:00Z','[)')`)
      await rebind(`, interval = tstzrange('2025-03-15T00:00Z','2025-04-01T00:00Z'), peak_instant = '2025-03-20T00:00Z'`)
      expect(await violations()).toEqual([{ window_id: w, record_id: r, violation: expect.stringMatching(/support interval .* lies outside the window's coverage horizon/) }])
      await expect(tx(c => publishAndSeal(c, GEN_M))).rejects.toThrow(/N16 membership invariant/)
      await classCov(`completed_horizon = ${HORIZON}`)
      await rebind(`, interval = tstzrange('2025-03-01T00:00Z','2025-04-01T00:00Z'), peak_instant = '2025-03-10T00:00Z'`)
      expect(await violations()).toEqual([])

      // 4. the CONTRIBUTOR moves: its support is updated (still covered by its own body_target partition) outside a narrowed window horizon
      await classCov(`completed_horizon = tstzrange('2025-01-01T00:00Z','2025-06-01T00:00Z','[)')`)
      await rebind()
      expect(await violations()).toEqual([])
      await expect(pool.query(`UPDATE ka_gochara_relationship_record SET temporal_support_intervals = ARRAY[tstzrange('2025-08-09T00:00Z','2025-08-11T00:00Z')]::tstzrange[] WHERE record_id = $1`, [r])).resolves.toBeDefined()
      expect(await violations()).toEqual([{ window_id: w, record_id: r, violation: expect.stringMatching(/support interval .* lies outside the window's coverage horizon/) }])
      await expect(tx(c => publishAndSeal(c, GEN_M))).rejects.toThrow(/N16 membership invariant/)
      expect(await sealCount(GEN_M)).toBe(0)
      await pool.query(`UPDATE ka_gochara_relationship_record SET temporal_support_intervals = ${SUPPORT} WHERE record_id = $1`, [r])
      expect(await violations()).toEqual([])

      // restored: the invariant holds and the seal succeeds
      await tx(c => publishAndSeal(c, GEN_M))
      expect(await sealCount(GEN_M)).toBe(1)
    })

    it('N10 consumer contract: drift is classified identical / extended / incompatible; the seal REFUSES incompatible drift and the manifest flip rolls back with it', async () => {
      const { r, w } = await tx(async c => {
        await seedLedger(c, { id: CID_2, objectId: OBJ_MARS, ordinal: 2, generation: GEN_D })
        const r = await insertRecord(c, { generation: GEN_D, contactId: CID_2 })
        const w = await insertWindow(c, { generation: GEN_D })
        await addMembership(c, w, r, { generation: GEN_D })
        return { r, w }
      })
      const drift = async () => (await pool.query<{ consumer: string; consumer_id: string; drift: string }>(
        `SELECT consumer, consumer_id, drift FROM ka_gochara_coverage_drift($1, $2) ORDER BY consumer`, [CHART, GEN_D])).rows
      expect(await drift()).toEqual([{ consumer: 'eval_window', consumer_id: w, drift: 'identical' }, { consumer: 'relationship_record', consumer_id: r, drift: 'identical' }])
      // extension (superset horizon + an added relation) is still valid
      await pool.query(
        `UPDATE kala_gochara_coverage SET completed_horizon = tstzrange('2024-06-01T00:00Z','2026-06-01T00:00Z','[)'),
                relations_searched = ARRAY['conjunction','aspect','residence','dispositorship']
         WHERE chart_id = $1 AND generation = $2 AND partition_kind = $3 AND partition_key = $4`, [CHART, GEN_D, COV_KIND, COV_KEY])
      expect((await drift()).map(x => x.drift)).toEqual(['identical', 'extended'])
      // a shrunk class partition makes the window INCOMPATIBLE: the seal refuses, atomically with the manifest flip
      await pool.query(
        `UPDATE kala_gochara_coverage SET completed_horizon = tstzrange('2025-02-01T00:00Z','2026-01-01T00:00Z','[)')
         WHERE chart_id = $1 AND generation = $2 AND partition_kind = 'event_class' AND partition_key = 'marriage'`, [CHART, GEN_D])
      expect((await drift()).map(x => x.drift)).toEqual(['incompatible', 'extended'])
      await expect(tx(c => publishAndSeal(c, GEN_D))).rejects.toThrow(/ka_gochara_generation_seal refused \(N10 consumer contract\): 1 record\/window row/)
      expect(await sealCount(GEN_D)).toBe(0)
      const status = await pool.query<{ status: string }>(`SELECT status FROM kala_gochara_publication WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_D])
      expect(status.rows[0]!.status).toBe('candidate')
      // a dropped relation on the record's partition is incompatible too
      await pool.query(
        `UPDATE kala_gochara_coverage SET completed_horizon = ${HORIZON} WHERE chart_id = $1 AND generation = $2 AND partition_kind = 'event_class' AND partition_key = 'marriage'`, [CHART, GEN_D])
      await pool.query(
        `UPDATE kala_gochara_coverage SET relations_searched = ARRAY['aspect','residence']
         WHERE chart_id = $1 AND generation = $2 AND partition_kind = $3 AND partition_key = $4`, [CHART, GEN_D, COV_KIND, COV_KEY])
      expect((await drift()).map(x => x.drift)).toEqual(['identical', 'incompatible'])
      await expect(tx(c => publishAndSeal(c, GEN_D))).rejects.toThrow(/INCOMPATIBLE/)
      // a NULL introduced later is incompatible (never 'extended')
      await pool.query(
        `UPDATE kala_gochara_coverage SET relations_searched = ARRAY['conjunction','aspect','residence',NULL]
         WHERE chart_id = $1 AND generation = $2 AND partition_kind = $3 AND partition_key = $4`, [CHART, GEN_D, COV_KIND, COV_KEY])
      expect((await drift()).map(x => x.drift)).toEqual(['identical', 'incompatible'])
      // restored (a superset again) → sealable; after the seal the detector keeps reporting for serve-time consumers
      await pool.query(
        `UPDATE kala_gochara_coverage SET relations_searched = ARRAY['conjunction','aspect','residence','dispositorship']
         WHERE chart_id = $1 AND generation = $2 AND partition_kind = $3 AND partition_key = $4`, [CHART, GEN_D, COV_KIND, COV_KEY])
      await tx(c => publishAndSeal(c, GEN_D))
      expect(await sealCount(GEN_D)).toBe(1)
      await pool.query(
        `UPDATE kala_gochara_coverage SET convention_id = $5
         WHERE chart_id = $1 AND generation = $2 AND partition_kind = $3 AND partition_key = $4`, [CHART, GEN_D, COV_KIND, COV_KEY, LEGACY_CONV_UNBRIDGED])
      expect((await drift()).map(x => x.drift)).toEqual(['identical', 'incompatible'])
      await expect(pool.query(`SELECT * FROM ka_gochara_coverage_drift($1, $2)`, [CHART, '4.0'])).resolves.toMatchObject({ rowCount: 0 })
    })

    it('N10: window CONTRIBUTORS are checked against the window\'s coverage — convention, relations searched, horizon — with isolated negative cases', async () => {
      // relations: the class search for romantic_start covered 'aspect' only; a conjunction record cannot contribute
      const wr = await tx(c => insertWindow(c, { eventClass: 'romantic_start' }))
      const rr = await tx(c => insertRecord(c, { eventClass: 'romantic_start' }))   // validated on the mars:karaka body_target partition
      await expect(addMembership(pool, wr, rr, { eventClass: 'romantic_start' })).rejects.toThrow(/relation 'conjunction' was not searched by the window/)
      // convention: the separation class was searched under the unbridged legacy convention; the record under legacy:c0
      const ws = await tx(c => insertWindow(c, { eventClass: 'separation' }))
      const rs = await tx(c => insertRecord(c, { eventClass: 'separation' }))
      await expect(addMembership(pool, ws, rs, { eventClass: 'separation' })).rejects.toThrow(/validated under convention 'legacy:c0' but the window was searched under convention 'legacy:c9'/)
      // horizon: the career_entry class search starts 2025-06-01; a March support interval lies outside it
      const wc = await tx(c => insertWindow(c, { eventClass: 'career_entry', intervalSql: `tstzrange('2025-07-01T00:00Z','2025-08-01T00:00Z')`, peakSql: `'2025-07-10T00:00Z'` }))
      const rc = await tx(c => insertRecord(c, { eventClass: 'career_entry' }))
      await expect(addMembership(pool, wc, rc, { eventClass: 'career_entry' })).rejects.toThrow(/support interval .* lies outside the window's coverage horizon/)
      const rc2 = await tx(c => insertRecord(c, { eventClass: 'career_entry', intervalsSql: `ARRAY[tstzrange('2025-07-09T00:00Z','2025-07-11T00:00Z')]::tstzrange[]` }))
      await expect(addMembership(pool, wc, rc2, { eventClass: 'career_entry' })).resolves.toBeUndefined()
    })

    it('F4/amendment 5: sky events — precision required, station Swiss-refined, no Moon rows, DELETE forbidden, supersession rules', async () => {
      const base = `INSERT INTO ka_gochara_sky_event (event_id, physical_object_id, convention_id, body, event_kind, occurrence_ordinal,
         t_exact, longitude, solver_method, delta_lambda, delta_t, precision_regime, coverage)`
      const ev = (sql: string, params: unknown[]) => tx(async c => { await chartCtx(c); return c.query(sql, params) })
      await expect(ev(`${base} VALUES ($1, $2, $3, 'saturn', 'sign_ingress', 1, '2025-03-10T00:00Z', 180.0, 'swiss_refined', NULL, NULL, NULL, '{"truncated":false}')`, [uuid(), OBJ_SAT_SPAN, CONV])).rejects.toThrow(/kgse_exact_precision_ck/)
      await expect(ev(`${base} VALUES ($1, $2, $3, 'saturn', 'sign_ingress', 1, '2025-03-10T00:00Z', 360.0, 'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}')`, [uuid(), OBJ_SAT_SPAN, CONV])).rejects.toThrow(/kgse_longitude_range_ck/)
      await expect(ev(`${base} VALUES ($1, $2, $3, 'saturn', 'sign_ingress', 1, '2025-03-10T00:00Z', 180.0, 'swiss_refined', -0.001, 60, 'standard', '{"truncated":false}')`, [uuid(), OBJ_SAT_SPAN, CONV])).rejects.toThrow(/kgse_uncertainty_finite_ck/)
      await expect(ev(`${base} VALUES ($1, $2, $3, 'moon', 'sign_ingress', 1, '2025-03-10T00:00Z', 100.0, 'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}')`, [uuid(), OBJ_MOON, CONV])).rejects.toThrow(/kgse_body_domain_ck/)
      await ev(`${base} VALUES ($1, $2, $3, 'saturn', 'sign_ingress', 1, '2025-03-10T00:00Z', 180.0, 'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}')`, [EVENT_1, OBJ_SAT_SPAN, CONV])
      await expect(pool.query(`DELETE FROM ka_gochara_sky_event WHERE event_id = $1`, [EVENT_1])).rejects.toThrow(/publication-immutable/)
      await expect(ev(`UPDATE ka_gochara_sky_event SET longitude = 181 WHERE event_id = $1`, [EVENT_1])).rejects.toThrow(/published non-NULL values are immutable/)
      await expect(ev(`${base.replace('coverage)', 'coverage, supersedes_event_id)')} VALUES ($1, $2, $3, 'mars', 'sign_ingress', 1, '2025-03-10T00:00Z', 180.0, 'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}', $4)`, [uuid(), OBJ_MARS_SPAN, CONV, EVENT_1]))
        .rejects.toThrow(/SAME body and kind/)
    })

    it('F5: validators are total; qualification is finalised at commit; N8: membership reparenting is prohibited', async () => {
      await expect(pool.query(`INSERT INTO ka_gochara_rule_path (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set, object_selector, provenance, operator_role, score_rule)
        VALUES ('P9', 'v1', 'graha', NULL, '["mars"]', '["conjunction"]', '[{"agent":"mars","relation":"conjunction","object_role":"karaka"}]', 'verse_cited', 'scored', 'x')`)).rejects.toThrow(/kgrp_frame_ck/)
      await expect(tx(c => insertRecord(c, { precisionSql: `'{"solver_method":null,"delta_lambda":0.001,"delta_t":60}'::jsonb` }))).rejects.toThrow(/kgrr_precision_typed_ck/)
      await expect(tx(c => insertRecord(c, { precisionSql: `'{"solver_method":"swiss_refined","delta_lambda":-0.001,"delta_t":60}'::jsonb` }))).rejects.toThrow(/kgrr_precision_typed_ck/)
      await expect(tx(c => insertRecord(c, { results: [['q1', 'v1', 'unknown']] }))).rejects.toThrow(/admission_state 'admitted' contradicts[\s\S]*derived 'unqualified'/)
      await expect(tx(c => insertRecord(c, { results: [['q1', 'v1', null]] }))).rejects.toThrow(/derived 'unqualified'/)
      await expect(tx(c => insertRecord(c, { admission: 'unqualified', valence: 'unqualified' }))).rejects.toThrow(/derived 'admitted'/)
      await expect(tx(c => insertRecord(c, { admission: 'unqualified', valence: 'unqualified', results: [['q1', 'v1', 'false']] }))).rejects.toThrow(/derived 'not_admitted'/)
      await expect(tx(c => insertRecord(c, { results: [] }))).rejects.toThrow(/prerequisite membership does not equal/)
      await expect(tx(c => insertRecord(c, { results: [['q1', 'v1', 'true'], ['q2', 'v1', 'true']] }))).rejects.toThrow(/prerequisite membership does not equal/)
      const r1 = await tx(c => insertRecord(c, { admission: 'unqualified', valence: 'unqualified', results: [['q1', 'v1', 'unknown']] }))
      const r2 = await tx(c => insertRecord(c, { generation: GEN_F }))
      await expect(pool.query(`UPDATE ka_gochara_record_prerequisite SET result = 'true' WHERE record_id = $1`, [r1])).rejects.toThrow(/derived 'admitted'/)
      await expect(pool.query(`DELETE FROM ka_gochara_record_prerequisite WHERE record_id = $1`, [r1])).rejects.toThrow(/prerequisite membership does not equal/)
      // N8: the reviewer's reparenting schedule — moving R1's rows to R2 — is refused at the row, not merely re-checked
      await expect(pool.query(`UPDATE ka_gochara_record_prerequisite SET record_id = $2 WHERE record_id = $1`, [r1, r2])).rejects.toThrow(/may change only `result`/)
      await expect(pool.query(`UPDATE ka_gochara_record_prerequisite SET ordinal = 2 WHERE record_id = $1`, [r1])).rejects.toThrow(/may change only `result`/)
      await expect(pool.query(`UPDATE ka_gochara_relationship_record SET generation = $2 WHERE record_id = $1`, [r1, GEN_X])).rejects.toThrow(/scope \(chart_id, generation\) is immutable/)
      await expect(tx(c => insertRecord(c, { results: [['q_missing', 'v1', 'true']] }))).rejects.toThrow(/kgrpr_predicate_fk/)
      await expect(tx(c => insertRecord(c, { house: null }))).rejects.toThrow(/kgrr_evaluated_has_house_ck/)
    })

    it('F6: factor discipline is exactly C2', async () => {
      const ins = `INSERT INTO ka_gochara_factor (factor_id, rule_version, operand_selector, direction, function, range_lower, range_upper, units, calibration_status, doctrine_ordering, category_mapping, null_state, effect)`
      await expect(pool.query(`${ins} VALUES ('f2','v1','{"operand":"x"}','higher_stronger','step',0,1,'unitless','uncalibrated_default',NULL,'{"exaltation":1.0,"debility":0.0}','omit','e')`)).resolves.toBeDefined()
      await expect(pool.query(`${ins} VALUES ('f3','v1','{"operand":"x"}','higher_stronger','linear',0,1,'degrees','uncalibrated_default',NULL,NULL,'omit','e')`)).resolves.toBeDefined()
      await expect(pool.query(`${ins} VALUES ('f4','v1','{"operand":"x"}','higher_stronger','linear',0,1,'degrees','calibrated',NULL,NULL,'omit','e')`)).rejects.toThrow(/kgf_calibrated_requires_mapping_ck/)
      await expect(pool.query(`${ins} VALUES ('f4','v1','{"operand":"x"}','higher_stronger','linear',0,1.5,'degrees','uncalibrated_default',NULL,NULL,'omit','e')`)).rejects.toThrow(/kgf_range_unit_interval_ck/)
    })

    it('N10/F7: coverage must APPLY — each rule with an isolated negative case', async () => {
      await expect(tx(c => insertRecord(c, { eventClass: 'childbirth', covKind: 'event_class', covKey: 'marriage' }))).rejects.toThrow(/does not cover class 'childbirth'/)
      await expect(tx(c => insertRecord(c, { objectRole: 'occupant' }))).rejects.toThrow(/does not cover \(agent 'mars', object_role 'occupant'\)/)
      await expect(tx(c => insertRecord(c, { contactId: null, agent: 'venus', relation: 'occupancy' }))).rejects.toThrow(/does not cover \(agent 'venus'/)
      await expect(tx(c => insertRecord(c, { contactId: CID_MOON, agent: 'moon', objectId: OBJ_MOON, covKind: 'event_class', covKey: 'marriage' }))).rejects.toThrow(/Moon contact is covered only by a moon_on_demand partition/)
      await expect(tx(c => insertRecord(c, { covKind: 'moon_on_demand', covKey: 'moon:interval:2025-03-01/2025-03-31' }))).rejects.toThrow(/Moon contact is covered only by a moon_on_demand partition/)
      await expect(tx(c => insertRecord(c, { contactId: null, agent: 'mars', relation: 'occupancy', objectRole: 'occupant', covKind: 'moon_on_demand', covKey: 'moon:interval:2025-03-01/2025-03-31' }))).rejects.toThrow(/natal-fact row never references a moon_on_demand/)
      // isolated relation case: class matches, body_target not involved, only relations_searched differs
      await expect(tx(c => insertRecord(c, { eventClass: 'romantic_start', covKind: 'event_class', covKey: 'romantic_start' }))).rejects.toThrow(/relation 'conjunction' is not among the partition's relations_searched/)
      await expect(tx(c => insertRecord(c, { eventClass: 'separation', covKind: 'event_class', covKey: 'separation' }))).rejects.toThrow(/not bridged to the contact's sky convention/)
      await expect(tx(c => insertRecord(c, { eventClass: 'career_entry', covKind: 'event_class', covKey: 'career_entry' }))).rejects.toThrow(/outside the partition's completed_horizon/)
      // N10: a NULL element in relations_searched is inapplicable outright (no SQL-NULL escape)
      await expect(tx(c => insertRecord(c, { eventClass: 'surgery', covKind: 'event_class', covKey: 'surgery' }))).rejects.toThrow(/NULL relations_searched element/)
      // N10: the consumer binds to the coverage facts — a stale/foreign digest is refused
      await expect(tx(c => insertRecord(c, { factsOverride: '{"convention_id":"legacy:c0","horizon":null,"relations_searched":["conjunction"]}' }))).rejects.toThrow(/does not equal the partition's current facts/)
      await expect(tx(c => insertRecord(c, { precisionSql: `'{"solver_method":"arc_index_bracket","delta_lambda":0.001,"delta_t":60}'::jsonb` }))).rejects.toThrow(/restates the contact's solved precision/)
      await expect(tx(c => insertRecord(c, { intervalsSql: `ARRAY[tstzrange('2026-03-09T00:00Z','2026-03-11T00:00Z')]::tstzrange[]` }))).rejects.toThrow(/support interval .* lies outside/)
      await expect(tx(c => insertRecord(c, { contactId: CID_MOON, agent: 'moon', objectId: OBJ_MOON, covKind: 'moon_on_demand', covKey: 'moon:interval:2025-03-01/2025-03-31' }))).resolves.toBeDefined()
    })

    it('N10/F7: windows carry event_class coverage bound by the facts snapshot; membership is class/path-bound and immutable', async () => {
      const w = await tx(c => insertWindow(c))
      await expect(tx(c => insertWindow(c, { covKind: 'body_target', covKey: COV_KEY }))).rejects.toThrow(/kgew_coverage_kind_ck/)
      await expect(tx(c => insertWindow(c, { eventClass: 'childbirth', covKey: 'marriage' }))).rejects.toThrow(/does not cover class 'childbirth'/)
      await expect(tx(c => insertWindow(c, { eventClass: 'surgery' }))).rejects.toThrow(/NULL relations_searched element/)
      await expect(tx(c => insertWindow(c, { eventClass: 'career_entry', intervalSql: `tstzrange('2025-03-01T00:00Z','2025-04-01T00:00Z')`, peakSql: 'NULL' }))).rejects.toThrow(/outside the partition's completed_horizon/)
      await expect(tx(c => insertWindow(c, { factsOverride: '{"convention_id":"legacy:c0","horizon":{"empty":true},"relations_searched":["aspect","conjunction","residence"]}' }))).rejects.toThrow(/does not equal the partition's current facts/)
      const childbirth = await tx(c => insertRecord(c, { eventClass: 'childbirth', covKind: 'event_class', covKey: 'childbirth' }))
      await expect(addMembership(pool, w, childbirth)).rejects.toThrow(/kgewr_record_fk/)
      const p4 = await tx(c => insertRecord(c, { pathId: 'P4' }))
      await expect(addMembership(pool, w, p4)).rejects.toThrow(/kgewr_record_fk/)
      const ok = await tx(c => insertRecord(c))
      await addMembership(pool, w, ok)
      await expect(pool.query(`UPDATE ka_gochara_eval_window_record SET record_id = $2 WHERE window_id = $1`, [w, p4])).rejects.toThrow(/rows are immutable/)
      await expect(pool.query(`UPDATE ka_gochara_eval_window SET generation = $2 WHERE window_id = $1`, [w, GEN_X])).rejects.toThrow(/scope \(chart_id, generation\) is immutable/)
    })

    it('amendment 7 / F11 (kept): score, evidence, intervals, peaks, selectors, fact ids, AV categories', async () => {
      await expect(tx(c => insertWindow(c, { scoreSql: '1.5' }))).rejects.toThrow(/kgew_score_unit_interval_ck/)
      await expect(tx(c => insertWindow(c, { evidenceForSql: `'NaN'::real` }))).rejects.toThrow(/kgew_evidence_finite_ck/)
      // an empty interval fails both the non-empty and the finite CHECK; PostgreSQL reports them in name order
      await expect(tx(c => insertWindow(c, { intervalSql: `'empty'::tstzrange`, peakSql: 'NULL' }))).rejects.toThrow(/kgew_interval_(finite|nonempty)_ck/)
      await expect(tx(c => insertWindow(c, { peakSql: `'2025-05-01T00:00Z'` }))).rejects.toThrow(/kgew_peak_in_interval_ck/)
      await expect(tx(c => insertWindow(c, { scoreSql: 'NULL', valence: 'unqualified', nullStatesSql: `'{unqualified}'` }))).resolves.toBeDefined()
      const pred = `INSERT INTO ka_gochara_predicate (predicate_id, rule_version, operator, operands)`
      await expect(pool.query(`${pred} VALUES ('q8','v1','eq','{"left":"some free prose here"}')`)).rejects.toThrow(/kgp_operands_typed_ck/)
      await expect(tx(c => insertRecord(c, { evidenceForSql: `'infinity'::real` }))).rejects.toThrow(/kgrr_evidence_finite_ck/)
      await expect(tx(c => insertRecord(c, { factIdsSql: `'["fact 1"]'` }))).rejects.toThrow(/kgrr_source_fact_ids_ck/)
      await expect(tx(c => insertRecord(c, { factIdsSql: `'[]'`, fixture: true }))).resolves.toBeDefined()
      const av = `INSERT INTO ka_gochara_av_polarity_declaration (convention, benefic_mark_name, malefic_mark_name, source_ref, applies_to_fact_categories)`
      await expect(tx(async c => { await chartCtx(c); await c.query(`${av} VALUES ('c-av','rekhā','bindu','BPHS2:35666-35684', ARRAY[NULL]::text[])`) })).rejects.toThrow(/kgav_categories_nonempty_ck/)
      await expect(tx(async c => { await chartCtx(c); await c.query(`${av} VALUES ('c-av','rekhā','bindu','BPHS2:35666-35684', ARRAY['ashtakavarga_bindu'])`) })).resolves.toBeUndefined()
      await expect(pool.query(`UPDATE ka_gochara_av_polarity_declaration SET source_ref = 'x'`)).rejects.toThrow(/insert-only/)
      await expect(tx(c => insertRecord(c, { eventClass: 'bereavement', affected: 'father', frameKind: 'moon', valence: 'adverse' }))).rejects.toThrow(/kgrr_relative_frame_ck/)
      // D-SCOPE: a non-canonical chart is refused at the lock boundary (N18) — kgc_canonical_chart_ck is the structural backstop behind it
      await expect(seedLedger(pool, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: GEN_X, chart: OTHER_CHART })).rejects.toThrow(/chart 00000000-0000-4000-8000-0000000000aa is not governed by the Gochara-5 contract \(D-SCOPE/)
      await pool.query(`ALTER TABLE ka_gochara_contact DISABLE TRIGGER ka_gochara_contact_1_write_guard`)
      try {
        await expect(seedLedger(pool, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: GEN_X, chart: OTHER_CHART })).rejects.toThrow(/kgc_canonical_chart_ck/)
      } finally {
        await pool.query(`ALTER TABLE ka_gochara_contact ENABLE TRIGGER ka_gochara_contact_1_write_guard`)
      }
    })

    it('§N.3 rebuild ordering on a CANDIDATE generation: deletes cascade membership, never block', async () => {
      await tx(async c => {
        const r = await insertRecord(c, { generation: GEN_S })
        const w = await insertWindow(c, { generation: GEN_S })
        await addMembership(c, w, r, { generation: GEN_S })
      })
      await pool.query(`DELETE FROM ka_gochara_eval_window WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_S])
      await pool.query(`DELETE FROM ka_gochara_relationship_record WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_S])
      await pool.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_S])
      const left = await pool.query<{ n: string }>(
        `SELECT (SELECT COUNT(*) FROM ka_gochara_eval_window_record WHERE generation = $1)
              + (SELECT COUNT(*) FROM ka_gochara_record_prerequisite WHERE generation = $1) AS n`, [GEN_S])
      expect(left.rows[0]!.n).toBe('0')
    })
  })

  // ── Forced failure between DDL and ledger, per migration (amendment 2) ───
  describe('(e) atomicity: a ledger failure after EACH migration persists nothing of it', () => {
    beforeAll(async () => {
      await resetSchema()
      await pool.query(`
        CREATE FUNCTION a51_block_ledger_insert() RETURNS trigger LANGUAGE plpgsql AS $f$
        BEGIN
          IF NEW.filename = current_setting('a51.block_file', true) THEN
            RAISE EXCEPTION 'a51 forced ledger failure (amendment 2 test): %', NEW.filename;
          END IF;
          RETURN NEW;
        END;
        $f$;
        CREATE TRIGGER a51_block_ledger BEFORE INSERT ON _migrations_applied
          FOR EACH ROW EXECUTE FUNCTION a51_block_ledger_insert();
      `)
    })

    it.each(MIGRATION_FILES.map((f, i) => [f, i] as const))(
      'blocking the ledger insert of %s rolls back exactly that migration (tables AND functions)',
      async (blocked, i) => {
        await pool.query(`DELETE FROM _migrations_applied`)
        for (const t of KA_TABLES) await pool.query(`DROP TABLE IF EXISTS ${t} CASCADE`)
        await pool.query(`DO $d$ DECLARE r record; BEGIN
          FOR r IN SELECT p.oid::regprocedure AS sig FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
                   WHERE n.nspname = 'public' AND p.proname LIKE 'ka\\_gochara\\_%' LOOP
            EXECUTE 'DROP FUNCTION IF EXISTS ' || r.sig::text || ' CASCADE';
          END LOOP; END $d$`)
        const client = await pool.connect()
        try {
          await client.query(`SET a51.block_file = '${blocked}'`)
          await expect(withTempDir(MIGRATION_FILES, dir =>
            runMigrations(client, [dir], { only: new Set(MIGRATION_FILES), disclosures: new Map(), renumberDisclosures: new Map() })))
            .rejects.toThrow(new RegExp(`a51 forced ledger failure \\(amendment 2 test\\): ${blocked.replace('.', '\\.')}`))
          await client.query(`RESET a51.block_file`)
        } finally {
          client.release()
        }
        expect(await ledgerFiles()).toEqual([...MIGRATION_FILES.slice(0, i)])
        for (const f of MIGRATION_FILES.slice(0, i)) for (const t of OWNED[f]!.tables) expect(await tableExists(t), `${t} should exist`).toBe(true)
        for (const t of OWNED[blocked]!.tables) expect(await tableExists(t), `${t} should be rolled back`).toBe(false)
        for (const fn of OWNED[blocked]!.functions) expect(await functionExists(fn), `${fn} should be rolled back`).toBe(false)
        for (const f of MIGRATION_FILES.slice(i + 1)) for (const t of OWNED[f]!.tables) expect(await tableExists(t), `${t} should not exist`).toBe(false)
      },
    )
  })
})
