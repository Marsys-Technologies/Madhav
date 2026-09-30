// @vitest-environment node
/**
 * Pravāha A5.1 round 3 — LIVE-DB contract suite for migrations 1153–1157 and
 * their preflights, executed against a REAL throwaway Postgres (CLAUDE.md
 * §N.8: the test runs the on-disk SQL itself, never a hand-copied
 * re-implementation). Sibling of kala_gochara_windows_generation_guard.db.test.ts.
 *
 * Closes ASTRA_REVIEW_A5_1_MIGRATIONS v1_1 (F1–F11) at runtime:
 *   - F8/F9  the effective ORDERED gate: preflight N passes → migration N
 *            applies through the real runner → preflight N+1 …; after apply
 *            every preflight blocks with the SPECIFIC `migration_already_applied`
 *            token; a plain re-run is BLOCKED by the embedded gate; a
 *            deliberate replay (GUC) is a verified no-op; a drifted same-named
 *            object (no PK, `CHECK (true)`, missing column) fails loudly; a
 *            same-argument-type function with NAMED parameters is caught; the
 *            privilege checks fire for a role without CREATE/REFERENCES; schema
 *            resolution is pinned to public under a shadow search_path;
 *   - amendment 2  a forced ledger failure after EACH migration in turn
 *            leaves none of that migration's tables OR standalone functions
 *            while the earlier ones stay committed;
 *   - F1     one contact identity coexists in a retained generation and a
 *            candidate; references are ownership-bound;
 *   - F2     permanent seal (auto-recorded on publish; survives superseded /
 *            rolled_back), refused deletes, TRUNCATE refusal, and the
 *            rebuild ⇄ publication serialization in BOTH orders on two
 *            concurrent connections;
 *   - F3     sealed rule versions: no later membership; unsealed versions
 *            produce nothing;
 *   - F4     the frozen identity recipe: same-tuple rewrites refused, target-
 *            and convention-changing corrections supersede, wrong-body /
 *            double / self supersession refused, the solver-method loophole
 *            closed;
 *   - F5     total validators (NULL payloads refused) and the commit-time
 *            finalisation of admission vs prerequisite results;
 *   - F6     C2 exactly: uncalibrated rows may carry a mapping; calibrated
 *            rows must;
 *   - F7     relation-exact lineage, class/path-bound window membership, and
 *            coverage APPLICABILITY (class, body, Moon, relation, convention
 *            bridge, horizon, restated precision);
 *   - F11    selector encoding, finite domains, non-empty AV categories.
 *
 * The 1081/1087/1152 parents (kala_gochara_convention / _publication /
 * _coverage / _contacts) are built by applying the REAL migration files; only
 * `charts` is a key-shape stub (001_baseline's charts needs the whole profile
 * chain and only its `id uuid PRIMARY KEY` is referenced here).
 *
 * Requires a THROWAWAY database. Skipped unless GOCHARA_A51_TEST_DATABASE_URL
 * is set; the URL is PARSED and must name a loopback database called exactly
 * `gochara_a51_test` (F10 — see gochara_a5_1_disposable_url.ts).
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
import { assertDisposableA51DatabaseUrl } from './gochara_a5_1_disposable_url'

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

/** Objects each migration OWNS (tables + standalone functions), for rollback proofs. */
const OWNED: Record<string, { tables: string[]; functions: string[] }> = {
  '1153_gochara_sky_event_substrate.sql': {
    tables: ['ka_gochara_sky_convention', 'ka_gochara_physical_object', 'ka_gochara_sky_event',
      'ka_gochara_contact_identity', 'ka_gochara_generation_seal', 'ka_gochara_convention_bridge',
      'ka_gochara_contact'],
    functions: ['ka_gochara_refuse_truncate()', 'ka_gochara_insert_only()',
      'ka_gochara_text_array_ok(text[],integer)', 'ka_gochara_finite_ok(double precision)',
      'ka_gochara_finite_nonneg_ok(double precision)', 'ka_gochara_norm_def(text)',
      'ka_gochara_describe_definitions(text[],text[])', 'ka_gochara_jsonb_diff(text,jsonb,jsonb)',
      'ka_gochara_verify_definitions(text,jsonb)', 'ka_gochara_sky_event_supersede_guard()',
      'ka_gochara_sky_event_guard()', 'ka_gochara_contact_identity_supersede_guard()',
      'ka_gochara_record_generation_seal()', 'ka_gochara_generation_seal_guard()',
      'ka_gochara_generation_is_sealed(uuid,text)', 'ka_gochara_contact_guard()'],
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
      'ka_gochara_sealed_generation_guard()', 'ka_gochara_record_coverage_guard()',
      'ka_gochara_record_finalize_check()'],
  },
  '1156_gochara_eval_window.sql': {
    tables: ['ka_gochara_eval_window', 'ka_gochara_eval_window_record'],
    functions: ['ka_gochara_window_coverage_guard()'],
  },
  '1157_gochara_av_polarity_declaration.sql': {
    tables: ['ka_gochara_av_polarity_declaration'],
    functions: [],
  },
}
const KA_TABLES = Object.values(OWNED).flatMap(o => o.tables)

// The constraint set the review contracted (finding → constraint name).
const EXPECTED_CONSTRAINTS: Array<[string, string]> = [
  ['ka_gochara_sky_convention', 'kgsc_domain_ordered_ck'],
  ['ka_gochara_physical_object', 'kgpo_relation_kind_ck'],
  ['ka_gochara_physical_object', 'kgpo_target_form_ck'],
  ['ka_gochara_physical_object', 'kgpo_identity_uq'],
  ['ka_gochara_sky_event', 'ka_gochara_sky_event_object_fk'],
  ['ka_gochara_sky_event', 'ka_gochara_sky_event_ordinal_uq'],
  ['ka_gochara_sky_event', 'kgse_truncated_method_ck'],
  ['ka_gochara_sky_event', 'kgse_uncertainty_finite_ck'],
  ['ka_gochara_sky_event', 'kgse_longitude_range_ck'],
  ['ka_gochara_sky_event', 'kgse_supersedes_uq'],
  ['ka_gochara_contact_identity', 'ka_gochara_contact_identity_ordinal_uq'],
  ['ka_gochara_contact_identity', 'kgci_supersedes_uq'],
  ['ka_gochara_contact_identity', 'kgci_tuple_uq'],
  ['ka_gochara_generation_seal', 'ka_gochara_generation_seal_pkey'],
  ['ka_gochara_convention_bridge', 'ka_gochara_convention_bridge_pkey'],
  ['ka_gochara_contact', 'ka_gochara_contact_pkey'],
  ['ka_gochara_contact', 'ka_gochara_contact_identity_fk'],
  ['ka_gochara_contact', 'ka_gochara_contact_object_fk'],
  ['ka_gochara_contact', 'kgc_reference_uq'],
  ['ka_gochara_contact', 'kgc_canonical_chart_ck'],
  ['ka_gochara_contact', 'kgc_truncated_method_ck'],
  ['ka_gochara_predicate', 'kgp_unknown_is_false_ck'],
  ['ka_gochara_predicate', 'kgp_operands_typed_ck'],
  ['ka_gochara_factor', 'kgf_range_unit_interval_ck'],
  ['ka_gochara_factor', 'kgf_calibrated_requires_mapping_ck'],
  ['ka_gochara_rule_path', 'kgrp_frame_ck'],
  ['ka_gochara_rule_path', 'kgrp_object_selector_ck'],
  ['ka_gochara_rule_path', 'kgrp_ruling_ck'],
  ['ka_gochara_rule_path_prerequisite', 'kgrpp_predicate_fk'],
  ['ka_gochara_rule_path_soft_factor', 'kgrps_factor_fk'],
  ['ka_gochara_rule_path_seal', 'kgrpseal_path_fk'],
  ['ka_gochara_relationship_record', 'kgrr_contact_fk'],
  ['ka_gochara_relationship_record', 'kgrr_coverage_fk'],
  ['ka_gochara_relationship_record', 'kgrr_support_cardinality_ck'],
  ['ka_gochara_relationship_record', 'kgrr_transit_natal_ck'],
  ['ka_gochara_relationship_record', 'kgrr_relative_frame_ck'],
  ['ka_gochara_relationship_record', 'kgrr_citation_ck'],
  ['ka_gochara_relationship_record', 'kgrr_evidence_finite_ck'],
  ['ka_gochara_relationship_record', 'kgrr_membership_uq'],
  ['ka_gochara_record_prerequisite', 'kgrpr_record_fk'],
  ['ka_gochara_record_prerequisite', 'kgrpr_predicate_fk'],
  ['ka_gochara_eval_window', 'kgew_score_unit_interval_ck'],
  ['ka_gochara_eval_window', 'kgew_interval_nonempty_ck'],
  ['ka_gochara_eval_window', 'kgew_peak_in_interval_ck'],
  ['ka_gochara_eval_window', 'kgew_evidence_finite_ck'],
  ['ka_gochara_eval_window', 'kgew_membership_uq'],
  ['ka_gochara_eval_window_record', 'kgewr_window_fk'],
  ['ka_gochara_eval_window_record', 'kgewr_record_fk'],
  ['ka_gochara_av_polarity_declaration', 'ka_gochara_av_polarity_declaration_pkey'],
  ['ka_gochara_av_polarity_declaration', 'kgav_categories_nonempty_ck'],
]

const EXPECTED_TRIGGERS: Array<[string, string]> = [
  ['ka_gochara_sky_convention', 'ka_gochara_sky_convention_immutable'],
  ['ka_gochara_sky_convention', 'ka_gochara_sky_convention_no_truncate'],
  ['ka_gochara_physical_object', 'ka_gochara_physical_object_immutable'],
  ['ka_gochara_sky_event', 'ka_gochara_sky_event_supersede_check'],
  ['ka_gochara_sky_event', 'ka_gochara_sky_event_mutation_guard'],
  ['ka_gochara_contact_identity', 'ka_gochara_contact_identity_supersede_check'],
  ['ka_gochara_contact_identity', 'ka_gochara_contact_identity_immutable'],
  ['ka_gochara_generation_seal', 'ka_gochara_generation_seal_check'],
  ['ka_gochara_generation_seal', 'ka_gochara_generation_seal_immutable'],
  ['kala_gochara_publication', 'ka_gochara_publication_seal_record'],
  ['ka_gochara_contact', 'ka_gochara_contact_lifecycle_guard'],
  ['ka_gochara_contact', 'ka_gochara_contact_no_truncate'],
  ['ka_gochara_predicate', 'ka_gochara_predicate_immutable'],
  ['ka_gochara_factor', 'ka_gochara_factor_immutable'],
  ['ka_gochara_rule_path', 'ka_gochara_rule_path_immutable'],
  ['ka_gochara_rule_path_prerequisite', 'ka_gochara_rp_prereq_sealed_check'],
  ['ka_gochara_rule_path_soft_factor', 'ka_gochara_rp_soft_factor_sealed_check'],
  ['ka_gochara_rule_path_seal', 'ka_gochara_rule_path_seal_immutable'],
  ['ka_gochara_relationship_record', 'ka_gochara_rr_sealed_path_check'],
  ['ka_gochara_relationship_record', 'ka_gochara_rr_coverage_guard'],
  ['ka_gochara_relationship_record', 'ka_gochara_rr_sealed_generation_guard'],
  ['ka_gochara_relationship_record', 'ka_gochara_rr_finalize'],
  ['ka_gochara_record_prerequisite', 'ka_gochara_rpr_finalize'],
  ['ka_gochara_eval_window', 'ka_gochara_ew_coverage_guard'],
  ['ka_gochara_eval_window', 'ka_gochara_ew_sealed_generation_guard'],
  ['ka_gochara_eval_window_record', 'ka_gochara_ewr_sealed_generation_guard'],
  ['ka_gochara_av_polarity_declaration', 'ka_gochara_av_polarity_immutable'],
  ['ka_gochara_av_polarity_declaration', 'ka_gochara_av_polarity_no_truncate'],
]

// ── Fixture ids ─────────────────────────────────────────────────────────────
const CHART = '482012f1-710e-4a25-994a-93821f5871aa' // the canonical chart (D-SCOPE)
const OTHER_CHART = '00000000-0000-4000-8000-0000000000aa'
const CONV = 'c0'                 // sky convention (§6.1)
const CONV2 = 'c1'                // a second sky convention (method change — §7.2 inv 4)
const LEGACY_CONV = 'legacy:c0'   // 1081 convention vector, bridged to c0
const LEGACY_CONV_UNBRIDGED = 'legacy:c9'
const GEN = '5.0'
const GEN_OLD = '4.1'
const GEN_C = '5.1'               // concurrency: rebuild first, then publish
const GEN_C2 = '5.2'              // concurrency: publish first, then rebuild
const GEN_F = '5.4'               // finalisation cases: a candidate that is never published
const OBJ_MARS = '10000000-0000-4000-8000-000000000001'      // mars conjunction point:198.52 c0
const OBJ_MOON = '10000000-0000-4000-8000-000000000002'      // moon conjunction point:327.06 c0
const OBJ_MARS_ASPECT = '10000000-0000-4000-8000-000000000003' // mars aspect point:198.52 c0
const OBJ_MARS_C1 = '10000000-0000-4000-8000-000000000004'   // mars conjunction point:198.52 c1
const OBJ_MARS_T2 = '10000000-0000-4000-8000-000000000005'   // mars conjunction point:198.53 c0
const OBJ_SAT_CONJ = '10000000-0000-4000-8000-000000000006'  // saturn conjunction point:202.43 c0
const OBJ_SAT_SPAN = '10000000-0000-4000-8000-000000000007'  // saturn sign_ingress span:libra c0
const OBJ_MARS_SPAN = '10000000-0000-4000-8000-000000000008' // mars sign_ingress span:libra c0
const CID_1 = '10000000-0000-4000-8000-000000000011'
const CID_2 = '10000000-0000-4000-8000-000000000012'
const CID_TRUNC = '10000000-0000-4000-8000-000000000013'
const CID_MOON = '10000000-0000-4000-8000-000000000014'
const CID_OLD_ONLY = '10000000-0000-4000-8000-000000000015'
const CID_LATE = '10000000-0000-4000-8000-000000000016'
const CID_C = '10000000-0000-4000-8000-000000000017'
const CID_C2 = '10000000-0000-4000-8000-000000000018'
const EVENT_1 = '10000000-0000-4000-8000-000000000021'
const RECORD_1 = '10000000-0000-4000-8000-000000000031'
const RECORD_OLD = '10000000-0000-4000-8000-000000000032'
const WINDOW_1 = '10000000-0000-4000-8000-000000000041'
const COV_KIND = 'body_target'
const COV_KEY = 'mars:conjunction'
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
    DROP SCHEMA IF EXISTS a51_shadow CASCADE;
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
  // `charts` key-shape stub; the gochara parents are the REAL 1081/1087/1152 files.
  await pool.query(`CREATE TABLE charts (id UUID PRIMARY KEY DEFAULT gen_random_uuid())`)
  for (const f of PARENT_FILES) await pool.query(mig(f))
  await pool.query(`INSERT INTO charts (id) VALUES ($1), ($2)`, [CHART, OTHER_CHART])
  await pool.query(TRACKER_DDL)
  await pool.query(TRACKER_IDENTITY_DDL)
}

// ── Fixture writers (all take a Queryable so they can run inside tx()) ──────
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
async function seedPublication(c: Q, generation: string, status = 'candidate'): Promise<void> {
  await c.query(
    `INSERT INTO kala_gochara_publication
       (chart_id, generation, writer_asset_id, convention_id, input_generation_vector,
        ephemeris_backend, horizon, row_counts, content_digest, status)
     VALUES ($1, $2, 'ka_gochara', $3, '{}', '{}', ${HORIZON}, '{}', 'digest', $4)`,
    [CHART, generation, LEGACY_CONV, status],
  )
}
async function seedCoverage(c: Q, o: {
  generation: string; kind: string; key: string; conv?: string;
  relations?: string[]; completed?: string;
}): Promise<void> {
  await c.query(
    `INSERT INTO kala_gochara_coverage
       (chart_id, generation, partition_kind, partition_key, convention_id,
        requested_horizon, completed_horizon, resolution, relations_searched,
        targets_requested, targets_resolved, targets_unresolved,
        target_resolution_state_counts, build_id)
     VALUES ($1, $2, $3, $4, $5, ${HORIZON}, ${o.completed ?? HORIZON}, 1.0, $6, 1, 1, 0,
             '{"resolved":1}', 'build-a51')`,
    [CHART, o.generation, o.kind, o.key, o.conv ?? LEGACY_CONV,
      o.relations ?? ['conjunction', 'aspect', 'residence']],
  )
}
async function seedObject(c: Q, id: string, body: string, relation: string, target: string, conv = CONV): Promise<void> {
  await c.query(
    `INSERT INTO ka_gochara_physical_object
       (physical_object_id, body, relation_kind, canonical_target, convention_id)
     VALUES ($1, $2, $3, $4, $5)`, [id, body, relation, target, conv],
  )
}
async function seedIdentity(c: Q, id: string, objectId: string, ordinal: number, supersedes: string | null = null): Promise<void> {
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
  solver?: string;
}): Promise<void> {
  const truncated = o.truncated ?? false
  await c.query(
    `INSERT INTO ka_gochara_contact (${CONTACT_COLS})
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9,
             ${truncated ? 'NULL' : `'2025-03-11T00:00Z'`},
             ${truncated ? 'NULL' : `'2025-03-10T00:00Z'`},
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
/** identity + ledger in one go (the writer's normal shape). */
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
       ('P4', 'v1', 'lagna', NULL, '["jupiter","saturn","mars"]', '["residence","aspect","conjunction"]',
        '[{"agent":"jupiter","relation":"residence","object_role":"signature_house"},
          {"agent":"mars","relation":"conjunction","object_role":"karaka"}]',
        'uncited_extension', 'scored', 'D-P4', 'within_path_product')`,
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
  // P1/v1 and P4/v1 are sealed (complete); P2/v1 is left UNSEALED on purpose.
  await c.query(`INSERT INTO ka_gochara_rule_path_seal (path_id, rule_version) VALUES ('P1','v1'), ('P4','v1')`)
}

const RECORD_COLS = `record_id, chart_id, generation, contact_id, event_class,
  affected_person, frame_kind, frame_arg, agent, relation, object_id, object_kind,
  object_role, path_id, rule_version, temporal_support_state, temporal_support_grain,
  temporal_support_intervals, coverage_partition_kind, coverage_partition_key,
  precision, source_text, source_page, source_fact_ids, fixture, provenance,
  operator_role, ruling_ref, admission_state, house_from_frame,
  evidence_for_occurrence, evidence_against_occurrence, outcome_valence_for_native,
  severity`

interface RecordOpts {
  id?: string; chart?: string; generation?: string; contactId?: string | null;
  eventClass?: string; affected?: string; frameKind?: string; frameArg?: string | null;
  agent?: string; relation?: string; objectId?: string; objectKind?: string; objectRole?: string;
  pathId?: string; ruleVersion?: string; supportState?: string; grain?: string | null;
  intervalsSql?: string; covKind?: string; covKey?: string; precisionSql?: string;
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
  const generation = o.generation ?? GEN
  const chart = o.chart ?? CHART
  const transit = o.contactId !== null
  await c.query(
    `INSERT INTO ka_gochara_relationship_record (${RECORD_COLS})
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17,
             ${o.intervalsSql ?? SUPPORT}, $18, $19,
             ${o.precisionSql ?? (transit ? `'{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb` : 'NULL')},
             $20, $21, ${o.factIdsSql ?? `'["fact-1"]'`}, $22, $23, $24, $25, $26, $27,
             ${o.evidenceForSql ?? '0.8'}, ${o.evidenceAgainstSql ?? 'NULL'}, $28,
             ${o.severitySql ?? 'NULL'})`,
    [id, chart, generation,
      transit ? (o.contactId ?? CID_1) : null,
      o.eventClass ?? 'marriage', o.affected ?? 'native', o.frameKind ?? 'lagna', o.frameArg ?? null,
      o.agent ?? 'mars', o.relation ?? (transit ? 'conjunction' : 'occupancy'),
      o.objectId ?? OBJ_MARS, o.objectKind ?? 'degree_point', o.objectRole ?? 'karaka',
      o.pathId ?? 'P1', o.ruleVersion ?? 'v1', o.supportState ?? 'computed',
      o.grain === undefined ? 'day' : o.grain,
      o.covKind ?? COV_KIND, o.covKey ?? COV_KEY,
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
  evidenceAgainstSql?: string; valence?: string; covKind?: string; covKey?: string;
  nullStatesSql?: string; severitySql?: string;
} = {}): Promise<string> {
  const id = o.id ?? uuid()
  await c.query(
    `INSERT INTO ka_gochara_eval_window
       (window_id, chart_id, generation, event_class, path_id, rule_version, interval,
        peak_instant, score, evidence_for, evidence_against, outcome_valence_for_native,
        severity, coverage_partition_kind, coverage_partition_key, null_states_used)
     VALUES ($1, $2, $3, $4, $5, $6,
             ${o.intervalSql ?? `tstzrange('2025-03-01T00:00Z','2025-04-01T00:00Z')`},
             ${o.peakSql ?? `'2025-03-10T00:00Z'`}, ${o.scoreSql ?? '0.8'},
             ${o.evidenceForSql ?? '0.8'}, ${o.evidenceAgainstSql ?? 'NULL'}, $7,
             ${o.severitySql ?? 'NULL'}, $8, $9, ${o.nullStatesSql ?? `'{}'`})`,
    [id, CHART, o.generation ?? GEN, o.eventClass ?? 'marriage', o.pathId ?? 'P1',
      o.ruleVersion ?? 'v1', o.valence ?? 'favourable', o.covKind ?? 'event_class',
      o.covKey ?? 'marriage'],
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
    [windowId, recordId, CHART, o.generation ?? GEN, o.eventClass ?? 'marriage',
      o.pathId ?? 'P1', o.ruleVersion ?? 'v1'],
  )
}

/** Full fixture stack, in FK order, in ONE transaction. */
async function seedFixtures(): Promise<void> {
  await tx(async c => {
    await seedLegacyConvention(c, LEGACY_CONV)
    await seedLegacyConvention(c, LEGACY_CONV_UNBRIDGED)
    await seedSkyConvention(c, CONV)
    await seedSkyConvention(c, CONV2, 'm2')
    await c.query(`INSERT INTO ka_gochara_convention_bridge (kala_convention_id, sky_convention_id) VALUES ($1, $2)`, [LEGACY_CONV, CONV])
    for (const g of [GEN, GEN_OLD, GEN_C, GEN_C2, GEN_F]) {
      await seedPublication(c, g)
      await seedCoverage(c, { generation: g, kind: 'body_target', key: 'mars:conjunction' })
      await seedCoverage(c, { generation: g, kind: 'event_class', key: 'marriage' })
    }
    await seedCoverage(c, { generation: GEN, kind: 'event_class', key: 'childbirth' })
    await seedCoverage(c, { generation: GEN, kind: 'moon_on_demand', key: 'moon:interval:2025-03-01/2025-03-31', relations: ['conjunction'] })
    await seedCoverage(c, { generation: GEN, kind: 'body_target', key: 'saturn:aspect', relations: ['aspect'] })
    await seedCoverage(c, { generation: GEN, kind: 'body_target', key: 'mars:late', completed: "tstzrange('2025-06-01T00:00Z','2026-01-01T00:00Z','[)')" })
    await seedCoverage(c, { generation: GEN, kind: 'body_target', key: 'mars:unbridged', conv: LEGACY_CONV_UNBRIDGED })
    await seedObject(c, OBJ_MARS, 'mars', 'conjunction', 'point:198.52')
    await seedObject(c, OBJ_MOON, 'moon', 'conjunction', 'point:327.06')
    await seedObject(c, OBJ_MARS_ASPECT, 'mars', 'aspect', 'point:198.52')
    await seedObject(c, OBJ_MARS_C1, 'mars', 'conjunction', 'point:198.52', CONV2)
    await seedObject(c, OBJ_MARS_T2, 'mars', 'conjunction', 'point:198.53')
    await seedObject(c, OBJ_SAT_CONJ, 'saturn', 'conjunction', 'point:202.43')
    await seedObject(c, OBJ_SAT_SPAN, 'saturn', 'sign_ingress', 'span:libra')
    await seedObject(c, OBJ_MARS_SPAN, 'mars', 'sign_ingress', 'span:libra')
    // O-RX-1 shape: one tuple, three contacts (direct pass, retrograde re-crossing, truncated)
    await seedContact(c, { id: CID_1, objectId: OBJ_MARS, ordinal: 1 })
    await seedContact(c, { id: CID_2, objectId: OBJ_MARS, ordinal: 2 })
    await seedContact(c, { id: CID_TRUNC, objectId: OBJ_MARS, ordinal: 3, truncated: true })
    await seedContact(c, { id: CID_MOON, objectId: OBJ_MOON, ordinal: 1, body: 'moon' })
    await seedContact(c, { id: CID_LATE, objectId: OBJ_MARS, ordinal: 4, tIn: '2025-02-01T00:00Z' })
    // F1: the SAME identity CID_1 also owned by the retained generation 4.1 …
    await seedLedger(c, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: GEN_OLD })
    // … and one identity owned ONLY by 4.1
    await seedContact(c, { id: CID_OLD_ONLY, objectId: OBJ_MARS, ordinal: 5, generation: GEN_OLD })
    // concurrency fixtures
    await seedContact(c, { id: CID_C, objectId: OBJ_MARS, ordinal: 6, generation: GEN_C })
    await seedContact(c, { id: CID_C2, objectId: OBJ_MARS, ordinal: 7, generation: GEN_C2 })
    // the never-published candidate used by the finalisation cases owns CID_1 too
    await seedLedger(c, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: GEN_F })
    await seedRegistries(c)
    await insertRecord(c, { id: RECORD_1 })
    await insertRecord(c, { id: RECORD_OLD, generation: GEN_OLD })
    await insertWindow(c, { id: WINDOW_1 })
    await addMembership(c, WINDOW_1, RECORD_1)
  })
}

/** Roles are cluster-wide: drop the under-privileged role and everything granted to it. */
async function dropNoprivRole(): Promise<void> {
  await pool.query(`DO $d$ BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'a51_nopriv') THEN
      EXECUTE 'DROP OWNED BY a51_nopriv';
      EXECUTE 'DROP ROLE a51_nopriv';
    END IF;
  END $d$`)
}

async function tableExists(name: string, schema = 'public'): Promise<boolean> {
  const res = await pool.query<{ present: boolean }>(
    `SELECT to_regclass($1) IS NOT NULL AS present`, [`${schema}.${name}`],
  )
  return res.rows[0]!.present
}
async function functionExists(sig: string): Promise<boolean> {
  const res = await pool.query<{ present: boolean }>(
    `SELECT to_regprocedure($1) IS NOT NULL AS present`, [`public.${sig}`],
  )
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
/** Replay one migration file directly, with the deliberate-replay GUC on. */
function replaySql(name: string): string {
  return `SET LOCAL ka_gochara.deliberate_replay = 'on';\n${mig(name)}`
}

describe.skipIf(!TEST_DB_URL)('A5.1 migrations 1153–1157 (live disposable DB, round 3)', () => {
  beforeAll(async () => {
    assertDisposableA51DatabaseUrl(TEST_DB_URL)   // F10: parsed, loopback, exact db name
    pool = new Pool({ connectionString: TEST_DB_URL })
    await resetSchema()
  })

  afterAll(async () => {
    if (!pool) return
    await resetSchema()
    await dropNoprivRole()
    await pool.end()
  })

  // ── Preflight gate semantics before any apply (F8/F9) ────────────────────
  describe('preflights fail closed and open', () => {
    it('PF1153 passes on a clean, correctly-privileged target with the REAL 1081 parents', async () => {
      await expect(pool.query(preflight(PREFLIGHT_FILES[0]))).resolves.toBeDefined()
    })

    it('PF1153 ledger lookup is wildcard-safe: a 1153Z_ row does NOT block', async () => {
      await pool.query(`INSERT INTO _migrations_applied (filename, sha256) VALUES ('1153Z_decoy.sql', 'x')`)
      await expect(pool.query(preflight(PREFLIGHT_FILES[0]))).resolves.toBeDefined()
      await pool.query(`DELETE FROM _migrations_applied WHERE filename = '1153Z_decoy.sql'`)
    })

    it('PF1153 blocks with the SPECIFIC token when 1153 is recorded', async () => {
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

    it('F9: PF1153 reports missing CREATE / REFERENCES privileges for an under-privileged role', async () => {
      await dropNoprivRole()
      // a role that can READ the ledger and catalog but holds neither CREATE on public nor REFERENCES on the parents
      await pool.query(`CREATE ROLE a51_nopriv NOLOGIN;
                        REVOKE CREATE ON SCHEMA public FROM PUBLIC; GRANT USAGE ON SCHEMA public TO a51_nopriv;
                        GRANT SELECT ON _migrations_applied TO a51_nopriv;`)
      const c = await pool.connect()
      try {
        await c.query(`SET ROLE a51_nopriv`)
        await expect(c.query(preflight(PREFLIGHT_FILES[0]))).rejects.toThrow(/no_create_privilege_on_public :: a51_nopriv[\s\S]*no_references_privilege :: public\.charts/)
      } finally {
        await c.query(`RESET ROLE`).catch(() => undefined)
        c.release()
        await pool.query(`GRANT CREATE ON SCHEMA public TO PUBLIC`)
        await dropNoprivRole()
      }
    })
  })

  // ── The effective ordered gate through the real runner (F9) ─────────────
  describe('(a) interleaved preflight → apply → verify through runMigrations', () => {
    it('each preflight passes right before its migration; each migration applies and is recorded', async () => {
      const client = await pool.connect()
      try {
        for (let i = 0; i < MIGRATION_FILES.length; i++) {
          await expect(client.query(preflight(PREFLIGHT_FILES[i]!))).resolves.toBeDefined()
          const ran = await withTempDir(MIGRATION_FILES.slice(0, i + 1), dir =>
            runMigrations(client, [dir], { disclosures: new Map(), renumberDisclosures: new Map() }))
          expect(ran).toEqual([MIGRATION_FILES[i]])
        }
      } finally {
        client.release()
      }
      expect(await ledgerFiles()).toEqual([...MIGRATION_FILES])
    })

    it('every contracted constraint exists, validated (pg_catalog proof)', async () => {
      const res = await pool.query<{ conrelid: string; conname: string; convalidated: boolean }>(
        `SELECT conrelid::regclass::text AS conrelid, conname, convalidated FROM pg_constraint
         WHERE conname = ANY($1)`, [EXPECTED_CONSTRAINTS.map(c => c[1])],
      )
      const present = new Map(res.rows.map(r => [`${r.conrelid}.${r.conname}`, r.convalidated]))
      const missing = EXPECTED_CONSTRAINTS.filter(([t, c]) => present.get(`${t}.${c}`) !== true)
      expect(missing).toEqual([])
    })

    it('every contracted trigger exists on its table (including the seal recorder on kala_gochara_publication)', async () => {
      const res = await pool.query<{ relname: string; tgname: string }>(
        `SELECT c.relname, t.tgname FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
         WHERE NOT t.tgisinternal AND t.tgname = ANY($1)`, [EXPECTED_TRIGGERS.map(t => t[1])],
      )
      const present = new Set(res.rows.map(r => `${r.relname}.${r.tgname}`))
      const missing = EXPECTED_TRIGGERS.filter(([t, g]) => !present.has(`${t}.${g}`))
      expect(missing).toEqual([])
    })

    it('after apply, every preflight blocks with its SPECIFIC migration_already_applied token', async () => {
      for (let i = 0; i < PREFLIGHT_FILES.length; i++) {
        await expect(pool.query(preflight(PREFLIGHT_FILES[i]!)))
          .rejects.toThrow(new RegExp(`migration_already_applied :: ${MIGRATION_FILES[i]!.replace('.', '\\.')}`))
      }
    })

    it('a plain re-run of a migration is BLOCKED by its embedded gate (untracked collision path)', async () => {
      await expect(pool.query(mig(MIGRATION_FILES[0]))).rejects.toThrow(/preflight 1153 BLOCKED[\s\S]*relation_already_exists :: public\.ka_gochara_contact\b/)
    })

    it('a deliberate replay (GUC) is a verified no-op for all five; guards stay armed', async () => {
      for (const f of MIGRATION_FILES) await expect(pool.query(replaySql(f))).resolves.toBeDefined()
      const res = await pool.query<{ n: string }>(
        `SELECT COUNT(*)::text AS n FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
         WHERE c.relname = 'ka_gochara_contact' AND NOT t.tgisinternal`)
      expect(res.rows[0]!.n).toBe('2')
      await expect(pool.query(`TRUNCATE ka_gochara_av_polarity_declaration`)).rejects.toThrow(/TRUNCATE refused/)
      await expect(pool.query(`TRUNCATE ka_gochara_sky_convention CASCADE`)).rejects.toThrow(/TRUNCATE refused/)
    })

    it('F9: schema resolution is pinned — a replay under a shadow search_path lands nothing outside public', async () => {
      await pool.query(`CREATE SCHEMA a51_shadow`)
      const c = await pool.connect()
      try {
        await c.query(`SET search_path TO a51_shadow, public`)
        await expect(c.query(replaySql(MIGRATION_FILES[4]))).resolves.toBeDefined()
        await c.query(`RESET search_path`)
      } finally {
        c.release()
      }
      const shadow = await pool.query<{ n: string }>(
        `SELECT COUNT(*)::text AS n FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'a51_shadow'`)
      expect(shadow.rows[0]!.n).toBe('0')
      expect(await tableExists('ka_gochara_av_polarity_declaration')).toBe(true)
    })

    it('F9: a same-named table with NO primary key and CHECK (true) fails the replay verification loudly', async () => {
      await pool.query(`DROP TABLE ka_gochara_av_polarity_declaration CASCADE`)
      await pool.query(
        `CREATE TABLE ka_gochara_av_polarity_declaration (
           convention TEXT NOT NULL, benefic_mark_name TEXT NOT NULL, malefic_mark_name TEXT NOT NULL,
           source_ref TEXT NOT NULL, applies_to_fact_categories TEXT[] NOT NULL,
           created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
           CONSTRAINT kgav_convention_nonblank_ck CHECK (btrim(convention) <> ''),
           CONSTRAINT kgav_mark_names_ck CHECK (btrim(benefic_mark_name) <> '' AND btrim(malefic_mark_name) <> '' AND benefic_mark_name <> malefic_mark_name),
           CONSTRAINT kgav_source_ref_nonblank_ck CHECK (btrim(source_ref) <> ''),
           CONSTRAINT kgav_categories_nonempty_ck CHECK (true))`)
      await expect(pool.query(replaySql(MIGRATION_FILES[4])))
        .rejects.toThrow(/definition drift[\s\S]*ka_gochara_av_polarity_declaration_pkey: MISSING[\s\S]*kgav_categories_nonempty_ck: expected/)
      await pool.query(`DROP TABLE ka_gochara_av_polarity_declaration`)
      await expect(pool.query(replaySql(MIGRATION_FILES[4]))).resolves.toBeDefined()
    })

    it('F9: a same-named table with a missing column fails the replay verification loudly', async () => {
      await pool.query(`DROP TABLE ka_gochara_av_polarity_declaration CASCADE`)
      await pool.query(
        `CREATE TABLE ka_gochara_av_polarity_declaration (
           convention TEXT PRIMARY KEY, benefic_mark_name TEXT NOT NULL, malefic_mark_name TEXT NOT NULL,
           applies_to_fact_categories TEXT[] NOT NULL)`)
      await expect(pool.query(replaySql(MIGRATION_FILES[4])))
        .rejects.toThrow(/definition drift[\s\S]*columns\.source_ref: MISSING/)
      await pool.query(`DROP TABLE ka_gochara_av_polarity_declaration`)
      await expect(pool.query(replaySql(MIGRATION_FILES[4]))).resolves.toBeDefined()
    })
  })

  // ── Behavioural contract (F1–F7, F11) ────────────────────────────────────
  describe('behavioural contract', () => {
    beforeAll(async () => {
      await seedFixtures()
    })

    it('F1/O-RX-1: one identity per (object, ordinal); the SAME contact id is owned by 4.1 and 5.0', async () => {
      const ordinals = await pool.query(
        `SELECT occurrence_ordinal FROM ka_gochara_contact_identity WHERE physical_object_id = $1 ORDER BY 1`, [OBJ_MARS])
      expect(ordinals.rows.map(r => r.occurrence_ordinal)).toEqual([1, 2, 3, 4, 5, 6, 7])
      const owners = await pool.query(
        `SELECT generation FROM ka_gochara_contact WHERE contact_id = $1 ORDER BY 1`, [CID_1])
      expect(owners.rows.map(r => r.generation)).toEqual([GEN_OLD, GEN, GEN_F])
      // a second identity for the same (object, ordinal) is refused
      await expect(seedIdentity(pool, uuid(), OBJ_MARS, 1)).rejects.toThrow(/ka_gochara_contact_identity_ordinal_uq/)
      // a ledger row disagreeing with its identity's tuple is refused
      await expect(seedLedger(pool, { id: CID_1, objectId: OBJ_MARS, ordinal: 2, generation: GEN_C }))
        .rejects.toThrow(/ka_gochara_contact_identity_fk/)
    })

    it('F1: a record cannot reference a contact owned only by another generation', async () => {
      // the applicability guard names the ownership violation first; the FK (kgrr_contact_fk) stands behind it
      await expect(tx(c => insertRecord(c, { contactId: CID_OLD_ONLY })))
        .rejects.toThrow(/is not owned by \(chart 482012f1-710e-4a25-994a-93821f5871aa, generation 5\.0\) \(F1\)/)
      await pool.query(`ALTER TABLE ka_gochara_relationship_record DISABLE TRIGGER ka_gochara_rr_coverage_guard`)
      try {
        await expect(tx(c => insertRecord(c, { contactId: CID_OLD_ONLY }))).rejects.toThrow(/kgrr_contact_fk/)
      } finally {
        await pool.query(`ALTER TABLE ka_gochara_relationship_record ENABLE TRIGGER ka_gochara_rr_coverage_guard`)
      }
      // the same identity IS usable from the generation that owns it
      await expect(tx(c => insertRecord(c, { contactId: CID_OLD_ONLY, generation: GEN_OLD }))).resolves.toBeDefined()
    })

    it('F7: physical relation is exact along the whole chain (object → contact → record; object → sky event)', async () => {
      await expect(tx(c => insertRecord(c, { relation: 'aspect' }))).rejects.toThrow(/kgrr_contact_fk/)
      await expect(tx(c => insertRecord(c, { objectId: OBJ_MARS_ASPECT }))).rejects.toThrow(/kgrr_contact_fk/)
      await expect(seedContact(pool, { id: uuid(), objectId: OBJ_MARS, ordinal: 8, relation: 'aspect' }))
        .rejects.toThrow(/ka_gochara_contact_object_fk/)
      await expect(pool.query(
        `INSERT INTO ka_gochara_sky_event
           (event_id, physical_object_id, convention_id, body, event_kind, occurrence_ordinal,
            t_exact, longitude, solver_method, delta_lambda, delta_t, precision_regime, coverage)
         VALUES ($1, $2, $3, 'saturn', 'station', 1, '2025-03-10T00:00Z', 180.0,
                 'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}')`,
        [uuid(), OBJ_SAT_SPAN, CONV])).rejects.toThrow(/ka_gochara_sky_event_object_fk/)
    })

    it('F2: candidate DELETE is allowed; publishing auto-seals; the seal outlives superseded/rolled_back', async () => {
      await pool.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN, CID_2])
      await seedLedger(pool, { id: CID_2, objectId: OBJ_MARS, ordinal: 2 }) // rebuilt: same identity, no re-mint
      await pool.query(`UPDATE kala_gochara_publication SET status = 'published', published_at = now() WHERE chart_id = $1 AND generation = $2`, [CHART, GEN])
      const seal = await pool.query(`SELECT manifest_id FROM ka_gochara_generation_seal WHERE chart_id = $1 AND generation = $2`, [CHART, GEN])
      expect(seal.rowCount).toBe(1)
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
      // the seal itself is permanent and honest
      await expect(pool.query(`DELETE FROM ka_gochara_generation_seal WHERE chart_id = $1`, [CHART])).rejects.toThrow(/insert-only/)
      await expect(pool.query(`UPDATE ka_gochara_generation_seal SET sealed_at = now()`)).rejects.toThrow(/insert-only/)
      await expect(pool.query(`DELETE FROM kala_gochara_publication WHERE chart_id = $1 AND generation = $2`, [CHART, GEN])).rejects.toThrow(/violates foreign key constraint/)
      await expect(pool.query(
        `INSERT INTO ka_gochara_generation_seal (chart_id, generation, manifest_id)
         SELECT chart_id, generation, manifest_id FROM kala_gochara_publication WHERE chart_id = $1 AND generation = $2`,
        [CHART, GEN_OLD])).rejects.toThrow(/not a published manifest/)
      // append (INSERT) into a sealed generation stays permitted — partition extension (O-RX-1 ordinal 4)
      await expect(seedContact(pool, { id: uuid(), objectId: OBJ_MARS, ordinal: 9 })).resolves.toBeUndefined()
      // a 4.1-style legacy-published generation with no seal row is protected by the manifest status
      await pool.query(`UPDATE kala_gochara_publication SET status = 'published' WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_OLD])
      await pool.query(`DELETE FROM ka_gochara_generation_seal WHERE false`) // no-op; the trigger wrote a seal — remove nothing
      await expect(pool.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_OLD, CID_OLD_ONLY])).rejects.toThrow(refused)
    })

    it('F2: TRUNCATE is refused on every owned table (row guards cannot be bypassed)', async () => {
      for (const t of KA_TABLES) {
        await expect(pool.query(`TRUNCATE ${t} CASCADE`)).rejects.toThrow(/TRUNCATE refused/)
      }
    })

    it('F2: rebuild ⇄ publication serialize — rebuild first: the publish waits, then seals what remains', async () => {
      const a = await pool.connect()
      const b = await pool.connect()
      try {
        await a.query('BEGIN')
        await a.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_C, CID_C])
        const publish = b.query(`UPDATE kala_gochara_publication SET status = 'published', published_at = now() WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_C])
        const state = await Promise.race([publish.then(() => 'settled'), sleep(500).then(() => 'pending')])
        expect(state).toBe('pending') // blocked on the per-generation lock the rebuild holds
        await a.query('COMMIT')
        await publish
      } finally {
        a.release(); b.release()
      }
      const seal = await pool.query(`SELECT 1 FROM ka_gochara_generation_seal WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_C])
      expect(seal.rowCount).toBe(1)
      const gone = await pool.query(`SELECT 1 FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_C, CID_C])
      expect(gone.rowCount).toBe(0)
    })

    it('F2: rebuild ⇄ publication serialize — publish first: the rebuild waits, then is refused', async () => {
      const a = await pool.connect()
      const b = await pool.connect()
      try {
        await b.query('BEGIN')
        await b.query(`UPDATE kala_gochara_publication SET status = 'published', published_at = now() WHERE chart_id = $1 AND generation = $2`, [CHART, GEN_C2])
        const del = a.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_C2, CID_C2])
        const state = await Promise.race([del.then(() => 'settled', () => 'settled'), sleep(500).then(() => 'pending')])
        expect(state).toBe('pending') // blocked on the lock the seal writer holds
        await b.query('COMMIT')
        await expect(del).rejects.toThrow(/SEALED/)
      } finally {
        a.release(); b.release()
      }
      const kept = await pool.query(`SELECT 1 FROM ka_gochara_contact WHERE chart_id = $1 AND generation = $2 AND contact_id = $3`, [CHART, GEN_C2, CID_C2])
      expect(kept.rowCount).toBe(1)
    })

    it('F3: a sealed rule version accepts no further membership; an unsealed version produces nothing', async () => {
      await expect(pool.query(
        `INSERT INTO ka_gochara_rule_path_prerequisite (path_id, rule_version, ordinal, predicate_id, predicate_rule_version)
         VALUES ('P1', 'v1', 2, 'q2', 'v1')`)).rejects.toThrow(/SEALED/)
      await expect(pool.query(
        `INSERT INTO ka_gochara_rule_path_soft_factor (path_id, rule_version, factor_id, factor_rule_version)
         VALUES ('P1', 'v1', 'f1', 'v1')`)).rejects.toThrow(/SEALED/)
      await expect(tx(c => insertRecord(c, { pathId: 'P2', agent: 'saturn', relation: 'occupancy', contactId: null, objectId: OBJ_SAT_CONJ, covKind: 'event_class', covKey: 'marriage', results: [] })))
        .rejects.toThrow(/not sealed/)
      await expect(tx(c => insertWindow(c, { pathId: 'P2' }))).rejects.toThrow(/not sealed/)
      // a NEW version is constructed then sealed; the old version is untouched
      await tx(async c => {
        await c.query(
          `INSERT INTO ka_gochara_rule_path (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set, object_selector, provenance, operator_role, ruling_ref, score_rule)
           VALUES ('P1', 'v2', 'dasha_lord', NULL, '["mars"]', '["conjunction"]', '[{"agent":"mars","relation":"conjunction","object_role":"karaka"}]', 'verse_cited', 'scored', NULL, 'within_path_product')`)
        await c.query(`INSERT INTO ka_gochara_rule_path_prerequisite (path_id, rule_version, ordinal, predicate_id, predicate_rule_version) VALUES ('P1','v2',1,'q1','v1'), ('P1','v2',2,'q2','v1')`)
        await c.query(`INSERT INTO ka_gochara_rule_path_seal (path_id, rule_version) VALUES ('P1','v2')`)
      })
      await expect(pool.query(`DELETE FROM ka_gochara_rule_path_seal WHERE path_id = 'P1'`)).rejects.toThrow(/insert-only/)
    })

    it('F4: a published non-NULL value is never rewritten in place; enrichment fills only NULL/truncated fields', async () => {
      const refused = /published non-NULL values are immutable/
      await expect(pool.query(`UPDATE ka_gochara_contact SET t_exact = '2025-03-22T00:00Z' WHERE contact_id = $1 AND generation = $2`, [CID_1, GEN])).rejects.toThrow(refused)
      await expect(pool.query(`UPDATE ka_gochara_contact SET t_in = '2025-03-08T00:00Z' WHERE contact_id = $1 AND generation = $2`, [CID_1, GEN])).rejects.toThrow(refused)
      await expect(pool.query(`UPDATE ka_gochara_contact SET occurrence_ordinal = 4 WHERE contact_id = $1 AND generation = $2`, [CID_1, GEN])).rejects.toThrow(/identity fields are immutable/)
      // the F4 loophole: a non-placeholder method never changes in place
      await expect(pool.query(`UPDATE ka_gochara_contact SET solver_method = 'arc_index_bracket' WHERE contact_id = $1 AND generation = $2`, [CID_1, GEN])).rejects.toThrow(/clipped_truncated placeholder/)
      // truncated ⇔ clipped_truncated is structural on both tables
      await expect(seedLedger(pool, { id: CID_TRUNC, objectId: OBJ_MARS, ordinal: 3, generation: GEN_C, truncated: true, solver: 'swiss_refined' })).rejects.toThrow(/kgc_truncated_method_ck/)
      // enrichment: the truncated row's centre is solved in place — same id, same ordinal
      await pool.query(
        `UPDATE ka_gochara_contact
         SET t_out = '2025-03-21T00:00Z', t_exact = '2025-03-20T00:00Z', solver_method = 'swiss_refined',
             delta_lambda = 0.001, delta_t = 60, precision_regime = 'standard', coverage = '{"truncated":false}'::jsonb
         WHERE contact_id = $1 AND generation = $2`, [CID_TRUNC, GEN])
      const enriched = await pool.query(`SELECT t_exact, occurrence_ordinal FROM ka_gochara_contact WHERE contact_id = $1 AND generation = $2`, [CID_TRUNC, GEN])
      expect(enriched.rows[0]!.t_exact).toBeTruthy()
      expect(enriched.rows[0]!.occurrence_ordinal).toBe(3)
      await expect(pool.query(`UPDATE ka_gochara_contact SET t_exact = '2025-03-22T00:00Z' WHERE contact_id = $1 AND generation = $2`, [CID_TRUNC, GEN])).rejects.toThrow(refused)
    })

    it('F4: corrections follow the frozen recipe — new tuple (target or convention), same body+relation, chain, never self/double', async () => {
      const CID_C1 = uuid(); const CID_T2 = uuid()
      // convention-changing correction (§7.2 inv 4): same target, new convention ⇒ new object ⇒ new id
      await expect(seedIdentity(pool, CID_C1, OBJ_MARS_C1, 1, CID_1)).resolves.toBeUndefined()
      // target-changing correction: same convention, corrected target ⇒ new object ⇒ new id
      await expect(seedIdentity(pool, CID_T2, OBJ_MARS_T2, 1, CID_2)).resolves.toBeUndefined()
      // a predecessor of a different body/relation is refused
      await expect(seedIdentity(pool, uuid(), OBJ_SAT_CONJ, 1, CID_TRUNC)).rejects.toThrow(/SAME body and relation/)
      // double supersession is refused (chain, never a tree)
      await expect(seedIdentity(pool, uuid(), OBJ_MARS_T2, 2, CID_1)).rejects.toThrow(/already superseded/)
      // self-supersession is refused
      const self = uuid()
      await expect(seedIdentity(pool, self, OBJ_MARS_T2, 3, self)).rejects.toThrow(/kgci_no_self_supersede_ck|does not exist/)
      // identities are never renumbered, reused or deleted
      await expect(pool.query(`UPDATE ka_gochara_contact_identity SET occurrence_ordinal = 9 WHERE contact_id = $1`, [CID_1])).rejects.toThrow(/insert-only/)
      await expect(pool.query(`DELETE FROM ka_gochara_contact_identity WHERE contact_id = $1`, [CID_1])).rejects.toThrow(/insert-only/)
      // retirement is derivable
      const retired = await pool.query(`SELECT COUNT(*)::int AS n FROM ka_gochara_contact_identity s WHERE s.supersedes_contact_id = $1`, [CID_1])
      expect(retired.rows[0]!.n).toBe(1)
    })

    it('F4/amendment 5: sky events — precision required, station Swiss-refined, no Moon rows, DELETE forbidden, supersession rules', async () => {
      const base = `INSERT INTO ka_gochara_sky_event
        (event_id, physical_object_id, convention_id, body, event_kind, occurrence_ordinal,
         t_exact, longitude, solver_method, delta_lambda, delta_t, precision_regime, coverage)`
      await expect(pool.query(`${base} VALUES ($1, $2, $3, 'saturn', 'sign_ingress', 1, '2025-03-10T00:00Z', 180.0, 'swiss_refined', NULL, NULL, NULL, '{"truncated":false}')`, [uuid(), OBJ_SAT_SPAN, CONV]))
        .rejects.toThrow(/kgse_exact_precision_ck/)
      await expect(pool.query(`${base} VALUES ($1, $2, $3, 'saturn', 'sign_ingress', 1, '2025-03-10T00:00Z', 360.0, 'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}')`, [uuid(), OBJ_SAT_SPAN, CONV]))
        .rejects.toThrow(/kgse_longitude_range_ck/)
      await expect(pool.query(`${base} VALUES ($1, $2, $3, 'saturn', 'sign_ingress', 1, '2025-03-10T00:00Z', 180.0, 'swiss_refined', -0.001, 60, 'standard', '{"truncated":false}')`, [uuid(), OBJ_SAT_SPAN, CONV]))
        .rejects.toThrow(/kgse_uncertainty_finite_ck/)
      await expect(pool.query(`${base} VALUES ($1, $2, $3, 'saturn', 'sign_ingress', 1, '2025-03-10T00:00Z', 180.0, 'clipped_truncated', 0.001, 60, 'standard', '{"truncated":false}')`, [uuid(), OBJ_SAT_SPAN, CONV]))
        .rejects.toThrow(/kgse_truncated_method_ck/)
      await expect(pool.query(`${base} VALUES ($1, $2, $3, 'moon', 'sign_ingress', 1, '2025-03-10T00:00Z', 100.0, 'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}')`, [uuid(), OBJ_MOON, CONV]))
        .rejects.toThrow(/kgse_body_domain_ck/)
      await pool.query(`${base} VALUES ($1, $2, $3, 'saturn', 'sign_ingress', 1, '2025-03-10T00:00Z', 180.0, 'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}')`, [EVENT_1, OBJ_SAT_SPAN, CONV])
      await expect(pool.query(`DELETE FROM ka_gochara_sky_event WHERE event_id = $1`, [EVENT_1])).rejects.toThrow(/publication-immutable/)
      await expect(pool.query(`UPDATE ka_gochara_sky_event SET longitude = 181 WHERE event_id = $1`, [EVENT_1])).rejects.toThrow(/published non-NULL values are immutable/)
      // supersession: a mars ingress cannot supersede a saturn ingress
      await expect(pool.query(`${base.replace('coverage)', 'coverage, supersedes_event_id)')} VALUES ($1, $2, $3, 'mars', 'sign_ingress', 1, '2025-03-10T00:00Z', 180.0, 'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}', $4)`, [uuid(), OBJ_MARS_SPAN, CONV, EVENT_1]))
        .rejects.toThrow(/SAME body and kind/)
    })

    it('F5: validators are total — NULL frame args and NULL/negative precision payloads are refused', async () => {
      await expect(pool.query(
        `INSERT INTO ka_gochara_rule_path (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set, object_selector, provenance, operator_role, score_rule)
         VALUES ('P9', 'v1', 'graha', NULL, '["mars"]', '["conjunction"]', '[{"agent":"mars","relation":"conjunction","object_role":"karaka"}]', 'verse_cited', 'scored', 'x')`))
        .rejects.toThrow(/kgrp_frame_ck/)
      await expect(pool.query(
        `INSERT INTO ka_gochara_rule_path (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set, object_selector, provenance, operator_role, score_rule)
         VALUES ('P9', 'v1', 'bhavat_bhavam', NULL, '["mars"]', '["conjunction"]', '[{"agent":"mars","relation":"conjunction","object_role":"karaka"}]', 'verse_cited', 'scored', 'x')`))
        .rejects.toThrow(/kgrp_frame_ck/)
      await expect(tx(c => insertRecord(c, { precisionSql: `'{"solver_method":null,"delta_lambda":0.001,"delta_t":60}'::jsonb` })))
        .rejects.toThrow(/kgrr_precision_typed_ck/)
      await expect(tx(c => insertRecord(c, { precisionSql: `'{"solver_method":"swiss_refined","delta_lambda":-0.001,"delta_t":60}'::jsonb` })))
        .rejects.toThrow(/kgrr_precision_typed_ck/)
      await expect(tx(c => insertRecord(c, { precisionSql: `'{}'::jsonb` }))).rejects.toThrow(/kgrr_precision_typed_ck/)
    })

    it('F5: qualification is finalised at commit — contradictory admission/prerequisite states are rejected', async () => {
      // admitted with an unknown prerequisite (the reviewer's counterexample)
      await expect(tx(c => insertRecord(c, { generation: GEN_F, results: [['q1', 'v1', 'unknown']] })))
        .rejects.toThrow(/admission_state 'admitted' contradicts[\s\S]*derived 'unqualified'/)
      // admitted with an unevaluated prerequisite
      await expect(tx(c => insertRecord(c, { generation: GEN_F, results: [['q1', 'v1', null]] })))
        .rejects.toThrow(/derived 'unqualified'/)
      // unqualified while every prerequisite is true
      await expect(tx(c => insertRecord(c, { generation: GEN_F, admission: 'unqualified', valence: 'unqualified' })))
        .rejects.toThrow(/derived 'admitted'/)
      // a false prerequisite must be recorded as not_admitted, never unqualified
      await expect(tx(c => insertRecord(c, { generation: GEN_F, admission: 'unqualified', valence: 'unqualified', results: [['q1', 'v1', 'false']] })))
        .rejects.toThrow(/derived 'not_admitted'/)
      // membership must equal the path's declared list: missing, extra, or wrong order all fail
      await expect(tx(c => insertRecord(c, { generation: GEN_F, results: [] }))).rejects.toThrow(/prerequisite membership does not equal/)
      await expect(tx(c => insertRecord(c, { generation: GEN_F, results: [['q1', 'v1', 'true'], ['q2', 'v1', 'true']] }))).rejects.toThrow(/prerequisite membership does not equal/)
      await expect(tx(c => insertRecord(c, { generation: GEN_F, pathId: 'P1', ruleVersion: 'v2', results: [['q2', 'v1', 'true'], ['q1', 'v1', 'true']] }))).rejects.toThrow(/prerequisite membership does not equal/)
      // the honest states are accepted …
      const unq = await tx(c => insertRecord(c, { generation: GEN_F, admission: 'unqualified', valence: 'unqualified', results: [['q1', 'v1', 'unknown']] }))
      await tx(c => insertRecord(c, { generation: GEN_F, admission: 'not_admitted', valence: 'unqualified', results: [['q1', 'v1', 'false']] }))
      await tx(c => insertRecord(c, { generation: GEN_F, pathId: 'P1', ruleVersion: 'v2', results: [['q1', 'v1', 'true'], ['q2', 'v1', 'true']] }))
      // … and a later mutation that would contradict the record is refused at ITS commit
      await expect(pool.query(`UPDATE ka_gochara_record_prerequisite SET result = 'true' WHERE record_id = $1`, [unq])).rejects.toThrow(/derived 'admitted'/)
      await expect(pool.query(`DELETE FROM ka_gochara_record_prerequisite WHERE record_id = $1`, [unq])).rejects.toThrow(/prerequisite membership does not equal/)
      await expect(pool.query(
        `INSERT INTO ka_gochara_record_prerequisite (record_id, chart_id, generation, ordinal, predicate_id, predicate_rule_version, result)
         VALUES ($1, $2, $3, 2, 'q2', 'v1', 'unknown')`, [RECORD_1, CHART, GEN])).rejects.toThrow(/SEALED|prerequisite membership does not equal/)
      // dangling predicate references are still refused by FK
      await expect(tx(c => insertRecord(c, { generation: GEN_F, results: [['q_missing', 'v1', 'true']] }))).rejects.toThrow(/kgrpr_predicate_fk/)
      // an evaluated row must carry its frame arithmetic (§1.2 inv 5)
      await expect(tx(c => insertRecord(c, { generation: GEN_F, house: null }))).rejects.toThrow(/kgrr_evaluated_has_house_ck/)
    })

    it('F6: factor discipline is exactly C2 — uncalibrated rows MAY carry a mapping; calibrated rows MUST', async () => {
      const ins = `INSERT INTO ka_gochara_factor (factor_id, rule_version, operand_selector, direction, function, range_lower, range_upper, units, calibration_status, doctrine_ordering, category_mapping, null_state, effect)`
      await expect(pool.query(`${ins} VALUES ('f2','v1','{"operand":"x"}','higher_stronger','step',0,1,'unitless','uncalibrated_default',NULL,'{"exaltation":1.0,"debility":0.0}','omit','e')`)).resolves.toBeDefined()
      await expect(pool.query(`${ins} VALUES ('f3','v1','{"operand":"x"}','higher_stronger','linear',0,1,'degrees','uncalibrated_default',NULL,NULL,'omit','e')`)).resolves.toBeDefined()
      await expect(pool.query(`${ins} VALUES ('f4','v1','{"operand":"x"}','higher_stronger','linear',0,1,'degrees','calibrated',NULL,NULL,'omit','e')`)).rejects.toThrow(/kgf_calibrated_requires_mapping_ck/)
      await expect(pool.query(`${ins} VALUES ('f4','v1','{"operand":"x"}','higher_stronger','linear',0,1,'degrees','calibrated',NULL,'{}','omit','e')`)).rejects.toThrow(/kgf_category_mapping_shape_ck/)
      await expect(pool.query(`${ins} VALUES ('f4','v1','{"operand":"x"}','higher_stronger','linear',0,1,'degrees','partially','["a"]',NULL,'omit','e')`)).rejects.toThrow(/kgf_calibration_status_ck/)
      await expect(pool.query(`${ins} VALUES ('f4','v1','{"operand":"x"}','higher_stronger','linear',0,1.5,'degrees','uncalibrated_default',NULL,NULL,'omit','e')`)).rejects.toThrow(/kgf_range_unit_interval_ck/)
      await expect(pool.query(`${ins} VALUES ('f4','v1','{"operand":"x"}','higher_stronger','linear',0,'NaN','degrees','uncalibrated_default',NULL,NULL,'omit','e')`)).rejects.toThrow(/kgf_range_unit_interval_ck/)
      await expect(pool.query(`${ins} VALUES ('f4','v1','{"operand":"x"}','higher_stronger','linear',0,1,'degrees','uncalibrated_default','[]',NULL,'omit','e')`)).rejects.toThrow(/kgf_doctrine_ordering_shape_ck/)
    })

    it('F7: coverage must APPLY — class, body, Moon, relation, convention bridge, horizon, restated precision, support intervals', async () => {
      await expect(tx(c => insertRecord(c, { eventClass: 'childbirth', covKind: 'event_class', covKey: 'marriage' }))).rejects.toThrow(/does not cover class 'childbirth'/)
      await expect(tx(c => insertRecord(c, { contactId: null, agent: 'venus', relation: 'occupancy', objectId: OBJ_MARS, results: [['q1', 'v1', 'true']] }))).rejects.toThrow(/does not cover agent 'venus'/)
      await expect(tx(c => insertRecord(c, { contactId: CID_MOON, agent: 'moon', objectId: OBJ_MOON, covKind: 'event_class', covKey: 'marriage' }))).rejects.toThrow(/Moon contact is covered only by a moon_on_demand partition/)
      await expect(tx(c => insertRecord(c, { contactId: CID_MOON, agent: 'moon', objectId: OBJ_MOON }))).rejects.toThrow(/does not cover agent 'moon'/)
      await expect(tx(c => insertRecord(c, { covKind: 'moon_on_demand', covKey: 'moon:interval:2025-03-01/2025-03-31' }))).rejects.toThrow(/Moon contact is covered only by a moon_on_demand partition/)
      await expect(tx(c => insertRecord(c, { contactId: null, agent: 'mars', relation: 'occupancy', covKind: 'moon_on_demand', covKey: 'moon:interval:2025-03-01/2025-03-31' }))).rejects.toThrow(/natal-fact row never references a moon_on_demand/)
      await expect(tx(c => insertRecord(c, { covKey: 'saturn:aspect', agent: 'mars' }))).rejects.toThrow(/does not cover agent 'mars'|relations_searched/)
      await expect(tx(c => insertRecord(c, { covKey: 'mars:unbridged' }))).rejects.toThrow(/not bridged to the contact's sky convention/)
      await expect(tx(c => insertRecord(c, { covKey: 'mars:late' }))).rejects.toThrow(/outside the partition's completed_horizon/)
      await expect(tx(c => insertRecord(c, { precisionSql: `'{"solver_method":"arc_index_bracket","delta_lambda":0.001,"delta_t":60}'::jsonb` }))).rejects.toThrow(/restates the contact's solved precision/)
      await expect(tx(c => insertRecord(c, { intervalsSql: `ARRAY[tstzrange('2026-03-09T00:00Z','2026-03-11T00:00Z')]::tstzrange[]` }))).rejects.toThrow(/support interval .* lies outside/)
      // a Moon record with Moon coverage, and the relation-searched partition with an aspect contact, are accepted
      await expect(tx(c => insertRecord(c, { contactId: CID_MOON, agent: 'moon', objectId: OBJ_MOON, covKind: 'moon_on_demand', covKey: 'moon:interval:2025-03-01/2025-03-31' }))).resolves.toBeDefined()
    })

    it('F7: window membership cannot cross generation, class or rule version; window coverage must apply', async () => {
      const w = await tx(c => insertWindow(c))
      await expect(addMembership(pool, w, RECORD_OLD, { generation: GEN_OLD })).rejects.toThrow(/kgewr_window_fk/)
      await expect(addMembership(pool, w, RECORD_OLD)).rejects.toThrow(/kgewr_record_fk/)
      const childbirth = await tx(c => insertRecord(c, { eventClass: 'childbirth', covKind: 'event_class', covKey: 'childbirth' }))
      await expect(addMembership(pool, w, childbirth)).rejects.toThrow(/kgewr_record_fk/)
      const p4 = await tx(c => insertRecord(c, { pathId: 'P4' }))
      await expect(addMembership(pool, w, p4)).rejects.toThrow(/kgewr_record_fk/)
      await expect(addMembership(pool, w, p4, { pathId: 'P4' })).rejects.toThrow(/kgewr_window_fk/)
      await expect(tx(c => insertWindow(c, { eventClass: 'childbirth', covKind: 'event_class', covKey: 'marriage' }))).rejects.toThrow(/does not cover class 'childbirth'/)
      await expect(tx(c => insertWindow(c, { intervalSql: `tstzrange('2025-12-01T00:00Z','2026-02-01T00:00Z')`, peakSql: 'NULL' }))).rejects.toThrow(/outside the partition's completed_horizon/)
    })

    it('amendment 7 (kept): score bounded [0,1] with NULL preserved; empty intervals and out-of-interval peaks refused', async () => {
      await expect(tx(c => insertWindow(c, { scoreSql: '1.5' }))).rejects.toThrow(/kgew_score_unit_interval_ck/)
      await expect(tx(c => insertWindow(c, { evidenceForSql: '-1' }))).rejects.toThrow(/kgew_evidence_finite_ck/)
      await expect(tx(c => insertWindow(c, { intervalSql: `'empty'::tstzrange`, peakSql: 'NULL' }))).rejects.toThrow(/kgew_interval_nonempty_ck/)
      await expect(tx(c => insertWindow(c, { peakSql: `'2025-05-01T00:00Z'` }))).rejects.toThrow(/kgew_peak_in_interval_ck/)
      await expect(tx(c => insertWindow(c, { scoreSql: 'NULL', valence: 'unqualified', nullStatesSql: `'{unqualified}'` }))).resolves.toBeDefined()
      await expect(tx(c => insertWindow(c, { nullStatesSql: `ARRAY[NULL]::text[]` }))).rejects.toThrow(/kgew_null_states_ck/)
    })

    it('F11: selector encoding, finite domains, non-empty AV category elements', async () => {
      const pred = `INSERT INTO ka_gochara_predicate (predicate_id, rule_version, operator, operands)`
      await expect(pool.query(`${pred} VALUES ('q9','v1','eq','{"left":"some free prose here"}')`)).rejects.toThrow(/kgp_operands_typed_ck/)
      await expect(pool.query(`${pred} VALUES ('q9','v1','eq','{"left":""}')`)).rejects.toThrow(/kgp_operands_typed_ck/)
      await expect(pool.query(`${pred} VALUES ('q9','v1','eq','{"left":null}')`)).rejects.toThrow(/kgp_operands_typed_ck/)
      await expect(pool.query(`${pred} VALUES ('q9','v1','eq','"just a string"')`)).rejects.toThrow(/kgp_operands_typed_ck/)
      await expect(pool.query(`${pred} VALUES ('q9','v1','eq','{"left":"chart_facts.graha_position:mars","orb":3}')`)).resolves.toBeDefined()
      await expect(tx(c => insertRecord(c, { evidenceForSql: `'NaN'::real` }))).rejects.toThrow(/kgrr_evidence_finite_ck/)
      await expect(tx(c => insertRecord(c, { evidenceForSql: `'infinity'::real` }))).rejects.toThrow(/kgrr_evidence_finite_ck/)
      await expect(tx(c => insertRecord(c, { severitySql: `'NaN'::real` }))).rejects.toThrow(/kgrr_severity_finite_ck/)
      await expect(tx(c => insertWindow(c, { evidenceForSql: `'NaN'::real` }))).rejects.toThrow(/kgew_evidence_finite_ck/)
      await expect(tx(c => insertRecord(c, { factIdsSql: `'[null]'` }))).rejects.toThrow(/kgrr_source_fact_ids_ck/)
      await expect(tx(c => insertRecord(c, { factIdsSql: `'["fact 1"]'` }))).rejects.toThrow(/kgrr_source_fact_ids_ck/)
      await expect(tx(c => insertRecord(c, { factIdsSql: `'[]'` }))).rejects.toThrow(/kgrr_source_fact_ids_ck/)
      await expect(tx(c => insertRecord(c, { factIdsSql: `'[]'`, fixture: true }))).resolves.toBeDefined()
      const av = `INSERT INTO ka_gochara_av_polarity_declaration (convention, benefic_mark_name, malefic_mark_name, source_ref, applies_to_fact_categories)`
      await expect(pool.query(`${av} VALUES ('c-av','rekhā','bindu','BPHS2:35666-35684', ARRAY[NULL]::text[])`)).rejects.toThrow(/kgav_categories_nonempty_ck/)
      await expect(pool.query(`${av} VALUES ('c-av','rekhā','bindu','BPHS2:35666-35684', ARRAY['']::text[])`)).rejects.toThrow(/kgav_categories_nonempty_ck/)
      await expect(pool.query(`${av} VALUES ('c-av','rekhā','bindu','BPHS2:35666-35684', '{}')`)).rejects.toThrow(/kgav_categories_nonempty_ck/)
      await expect(pool.query(`${av} VALUES ('c-av','rekhā','rekhā','BPHS2:35666-35684', ARRAY['ashtakavarga_bindu'])`)).rejects.toThrow(/kgav_mark_names_ck/)
      await expect(pool.query(`${av} VALUES ('c-av','rekhā','bindu','BPHS2:35666-35684', ARRAY['ashtakavarga_bindu'])`)).resolves.toBeDefined()
      await expect(pool.query(`UPDATE ka_gochara_av_polarity_declaration SET source_ref = 'x'`)).rejects.toThrow(/insert-only/)
    })

    it('amendments 5/9 (kept): support cardinality, NOT NULL valence, relative frame, citation, ruling rule, D-SCOPE', async () => {
      await expect(tx(c => insertRecord(c, { supportState: 'computed', intervalsSql: `'{}'::tstzrange[]` }))).rejects.toThrow(/kgrr_support_cardinality_ck/)
      await expect(tx(c => insertRecord(c, { supportState: 'computed_empty', intervalsSql: `'{}'::tstzrange[]` }))).resolves.toBeDefined()
      await expect(tx(c => c.query(
        `INSERT INTO ka_gochara_relationship_record (${RECORD_COLS})
         VALUES ($1, $2, $3, $4, 'marriage', 'native', 'lagna', NULL, 'mars', 'conjunction', $5, 'degree_point', 'karaka',
                 'P1', 'v1', 'uncomputed', NULL, '{}', $6, $7,
                 '{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb,
                 'Phaladīpikā', 'PG249-250 (XX.34-38)', '["fact-1"]', false, 'verse_cited', 'scored', NULL,
                 'unqualified', NULL, NULL, NULL, NULL, NULL)`,
        [uuid(), CHART, GEN, CID_1, OBJ_MARS, COV_KIND, COV_KEY]))).rejects.toThrow(/null value in column "outcome_valence_for_native"/)
      await expect(tx(c => insertRecord(c, { eventClass: 'bereavement', affected: 'father', frameKind: 'moon', valence: 'adverse' }))).rejects.toThrow(/kgrr_relative_frame_ck/)
      await expect(tx(c => insertRecord(c, { sourcePage: null }))).rejects.toThrow(/kgrr_citation_ck/)
      await expect(tx(c => insertRecord(c, { provenance: 'uncited_extension', rulingRef: null }))).rejects.toThrow(/kgrr_ruling_ck/)
      await expect(tx(c => insertRecord(c, { rulingRef: 'M-8' }))).resolves.toBeDefined() // a ruling on a verse_cited scored row is not forbidden
      await expect(seedLedger(pool, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: GEN, chart: OTHER_CHART })).rejects.toThrow(/kgc_canonical_chart_ck/)
    })

    it('registries and the convention bridge are insert-only (§2.1 amendment 1; §7.2 inv 4)', async () => {
      await expect(pool.query(`UPDATE ka_gochara_rule_path SET score_rule = 'x' WHERE path_id = 'P1'`)).rejects.toThrow(/insert-only/)
      await expect(pool.query(`DELETE FROM ka_gochara_predicate WHERE predicate_id = 'q1'`)).rejects.toThrow(/insert-only/)
      await expect(pool.query(`UPDATE ka_gochara_convention_bridge SET sky_convention_id = $1`, [CONV2])).rejects.toThrow(/insert-only/)
      await expect(pool.query(`UPDATE ka_gochara_sky_convention SET grid = 'x' WHERE convention_id = $1`, [CONV])).rejects.toThrow(/insert-only/)
    })

    it('§N.3 rebuild ordering on a CANDIDATE generation: deleting records/windows cascades membership, never blocks', async () => {
      await tx(async c => {
        await seedPublication(c, '5.3')
        await seedCoverage(c, { generation: '5.3', kind: 'body_target', key: 'mars:conjunction' })
        await seedCoverage(c, { generation: '5.3', kind: 'event_class', key: 'marriage' })
        await seedLedger(c, { id: CID_1, objectId: OBJ_MARS, ordinal: 1, generation: '5.3' })
        const r = await insertRecord(c, { generation: '5.3' })
        const w2 = await insertWindow(c, { generation: '5.3' })
        await addMembership(c, w2, r, { generation: '5.3' })
      })
      await pool.query(`DELETE FROM ka_gochara_eval_window WHERE chart_id = $1 AND generation = '5.3'`, [CHART])
      await pool.query(`DELETE FROM ka_gochara_relationship_record WHERE chart_id = $1 AND generation = '5.3'`, [CHART])
      await pool.query(`DELETE FROM ka_gochara_contact WHERE chart_id = $1 AND generation = '5.3'`, [CHART])
      const left = await pool.query<{ n: string }>(
        `SELECT (SELECT COUNT(*) FROM ka_gochara_eval_window_record WHERE generation = '5.3')
              + (SELECT COUNT(*) FROM ka_gochara_record_prerequisite WHERE generation = '5.3') AS n`)
      expect(left.rows[0]!.n).toBe('0')
    })
  })

  // ── Forced failure between DDL and ledger, per migration (amendment 2) ───
  describe('(b) atomicity: a ledger failure after EACH migration persists nothing of it', () => {
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
        await pool.query(`DROP TRIGGER IF EXISTS ka_gochara_publication_seal_record ON kala_gochara_publication`)
        await pool.query(`DO $d$ DECLARE r record; BEGIN
          FOR r IN SELECT p.oid::regprocedure AS sig FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
                   WHERE n.nspname = 'public' AND p.proname LIKE 'ka\\_gochara\\_%' LOOP
            EXECUTE 'DROP FUNCTION IF EXISTS ' || r.sig::text || ' CASCADE';
          END LOOP; END $d$`)
        const client = await pool.connect()
        try {
          await client.query(`SET a51.block_file = '${blocked}'`)
          await expect(
            withTempDir(MIGRATION_FILES, dir =>
              runMigrations(client, [dir], { disclosures: new Map(), renumberDisclosures: new Map() })),
          ).rejects.toThrow(new RegExp(`a51 forced ledger failure \\(amendment 2 test\\): ${blocked.replace('.', '\\.')}`))
          await client.query(`RESET a51.block_file`)
        } finally {
          client.release()
        }
        // earlier migrations committed with their ledger rows …
        expect(await ledgerFiles()).toEqual([...MIGRATION_FILES.slice(0, i)])
        for (const f of MIGRATION_FILES.slice(0, i)) {
          for (const t of OWNED[f]!.tables) expect(await tableExists(t), `${t} should exist`).toBe(true)
        }
        // … the blocked one left NO table and NO standalone function …
        for (const t of OWNED[blocked]!.tables) expect(await tableExists(t), `${t} should be rolled back`).toBe(false)
        for (const fn of OWNED[blocked]!.functions) expect(await functionExists(fn), `${fn} should be rolled back`).toBe(false)
        if (i === 0) {
          const trg = await pool.query(`SELECT 1 FROM pg_trigger WHERE tgname = 'ka_gochara_publication_seal_record'`)
          expect(trg.rowCount).toBe(0)
        }
        // … and nothing after it ran at all.
        for (const f of MIGRATION_FILES.slice(i + 1)) {
          for (const t of OWNED[f]!.tables) expect(await tableExists(t), `${t} should not exist`).toBe(false)
        }
      },
    )
  })
})
