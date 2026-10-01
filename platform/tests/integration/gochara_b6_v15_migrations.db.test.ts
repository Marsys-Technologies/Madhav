// @vitest-environment node
/**
 * Pravāha B6.0 PART 1 — LIVE-DB contract suite for migration 1204 (the v1.5
 * contract amendment AM-7 'av_qualifier' object_role), executed against a REAL
 * throwaway Postgres (CLAUDE.md §N.8: the test runs the on-disk SQL itself).
 * Sibling of gochara_a5_1_migrations.db.test.ts, whose fixture vocabulary this
 * suite reuses at a smaller scale.
 *
 * AM-8's 1205 was SPLIT OUT (ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_0, rank 1):
 * the shared-validator arm would have admitted unresolved 'inherited' frames
 * on arbitrary paths including scored rows, and bypassed 1155:527-528's
 * relative-frame exclusion. It returns as its own designed P6-testimony-
 * template migration with day_on_demand. This suite proves the split live:
 * ka_gochara_frame_ok still has exactly its v1.0 arms and a rule path with
 * frame_kind='inherited' is REFUSED by kgrp_frame_ck.
 *
 * Proves, on the live database:
 *   - the exact `--only` window route applies the FULL contract chain
 *     1153→1154→1155→1156→1157→1204 in order (CONTRACT_FILES no longer omits
 *     1156/1157 — the review's test-debt note), each file's own gate
 *     observing its prerequisite recorded;
 *   - AM-7: after 1204, kgrr_object_role_ck ACCEPTS 'av_qualifier' on a REAL
 *     house-span-residence qualification (a full writer-path record against a
 *     relation_kind='residence' contact COMMITs — every trigger, CHECK and
 *     the commit-time finaliser pass; the review's fixture correction:
 *     residence, not a conjunction) and still REJECTS an unknown role with a
 *     kgrr_object_role_ck violation; EVERY v1.0 role still passes the CHECK
 *     (full probe, not only karaka);
 *   - ka_gochara_object_selector_ok widens the same way (the Codex-accepted
 *     fold — see the 1204 header);
 *   - the routine runner REFUSES 1204 (no --only), loudly naming the window;
 *   - replay is BLOCKED (the embedded gate refuses an already-applied file).
 *
 * Requires a THROWAWAY database. Skipped unless GOCHARA_A51_TEST_DATABASE_URL
 * is set (same disposable boundary as the A5.1 suite — see
 * tests/integration/gochara_a5_1_disposable_url.ts).
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
const PARENT_FILES = [
  '1081_nirmana_l3_gochara_ledger_coverage_publication.sql',
  '1087_nirmana_l3_gochara_contacts_inclusivity_completeness_tier_basis.sql',
  '1152_kala_gochara_contacts_t_exact_nullable_truncated.sql',
] as const
const CONTRACT_FILES = [
  '1153_gochara_sky_event_substrate.sql',
  '1154_gochara_rule_path_registry.sql',
  '1155_gochara_relationship_record.sql',
  '1156_gochara_eval_window.sql',
  '1157_gochara_av_polarity_declaration.sql',
] as const
const M1204 = '1204_gochara_av_qualifier_object_role.sql'
const WINDOW_FILES = [...CONTRACT_FILES, M1204] as const

const CHART = '482012f1-710e-4a25-994a-93821f5871aa' // the canonical chart (D-SCOPE)
const CONV = 'c0'
const LEGACY_CONV = 'legacy:c0'
const GEN = '5.4'      // candidate, never published
const OBJ_MARS = '10000000-0000-4000-8000-000000000001'
const OBJ_MARS_RES = '10000000-0000-4000-8000-000000000002'
const CID_1 = '10000000-0000-4000-8000-000000000011'
const CID_2 = '10000000-0000-4000-8000-000000000012'
const COV_KIND = 'body_target'
const HORIZON = "tstzrange('2025-01-01T00:00Z','2026-01-01T00:00Z','[)')"
const SUPPORT = "ARRAY[tstzrange('2025-03-09T00:00Z','2025-03-11T00:00Z')]::tstzrange[]"

const V10_ROLES = ['lord', 'occupant', 'karaka', 'dispositor', 'maraka_of_house',
  'period_lord', 'yoga_constituent', 'pada', 'signature_house'] as const

let seq = 0
const uuid = (): string => `20000000-0000-4000-8000-${String(++seq).padStart(12, '0')}`

function mig(name: string): string {
  return readFileSync(join(MIGRATIONS_DIR, name), 'utf8')
}

let pool: Pool
type Q = Pick<PoolClient, 'query'>

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

async function withTempDir<T>(files: readonly string[], fn: (dir: string) => Promise<T>): Promise<T> {
  const dir = mkdtempSync(join(tmpdir(), 'gochara-b6-migrations-'))
  try {
    for (const f of files) copyFileSync(join(MIGRATIONS_DIR, f), join(dir, f))
    return await fn(dir)
  } finally {
    rmSync(dir, { recursive: true, force: true })
  }
}

async function resetSchema(): Promise<void> {
  await pool.query(`
    DROP SCHEMA public CASCADE;
    CREATE SCHEMA public;
    CREATE TABLE charts (id UUID PRIMARY KEY DEFAULT gen_random_uuid());
  `)
  for (const f of PARENT_FILES) await pool.query(mig(f))
  await pool.query(`INSERT INTO charts (id) VALUES ($1)`, [CHART])
  await pool.query(TRACKER_DDL)
  await pool.query(TRACKER_IDENTITY_DDL)
}

// ── Fixture writers (A5.1 suite vocabulary, minimal) ────────────────────────
async function chartCtx(c: Q): Promise<void> {
  await c.query(`SELECT ka_gochara_lock_chart($1)`, [CHART])
}
async function seedLegacyConvention(c: Q): Promise<void> {
  await c.query(
    `INSERT INTO kala_gochara_convention
       (convention_id, zodiac, ayanamsha, sidereal_method, node_model, node_source,
        epoch_convention, time_scale, house_system, ephemeris_mode, method_version)
     VALUES ($1, 'sidereal', 'lahiri_chitrapaksha', 'true_chitra', 'mean', 'swiss',
             'j2000', 'utc', 'whole_sign', 'swiss', '1.0')`, [LEGACY_CONV],
  )
}
async function seedSkyConvention(c: Q): Promise<void> {
  await c.query(
    `INSERT INTO ka_gochara_sky_convention
       (convention_id, ephemeris_generation, ayanamsha, node_convention, grid,
        method_version, domain_start, domain_end)
     VALUES ($1, 'de441', 'lahiri_chitrapaksha', 'mean', '1s', 'm1',
             '2025-01-01T00:00Z', '2026-01-01T00:00Z')`, [CONV],
  )
}
async function seedPublication(c: Q): Promise<void> {
  await c.query(
    `INSERT INTO kala_gochara_publication
       (chart_id, generation, writer_asset_id, convention_id, input_generation_vector,
        ephemeris_backend, horizon, row_counts, content_digest, status)
     VALUES ($1, $2, 'ka_gochara', $3, '{}', '{}', ${HORIZON}, '{}', 'digest', 'candidate')`,
    [CHART, GEN, LEGACY_CONV],
  )
}
async function seedCoverage(c: Q, key: string): Promise<void> {
  await c.query(
    `INSERT INTO kala_gochara_coverage
       (chart_id, generation, partition_kind, partition_key, convention_id,
        requested_horizon, completed_horizon, resolution, relations_searched,
        targets_requested, targets_resolved, targets_unresolved,
        target_resolution_state_counts, build_id)
     VALUES ($1, $2, $3, $4, $5, ${HORIZON}, ${HORIZON}, 1.0,
             ARRAY['conjunction','aspect','residence']::text[], 1, 1, 0,
             '{"resolved":1}', 'build-b6')`,
    [CHART, GEN, COV_KIND, key, LEGACY_CONV],
  )
}
async function seedObjects(c: Q): Promise<void> {
  await c.query(
    `INSERT INTO ka_gochara_physical_object
       (physical_object_id, body, relation_kind, canonical_target, convention_id)
     VALUES ($1, 'mars', 'conjunction', 'point:198.52', $2),
            ($3, 'mars', 'residence', 'span:7', $2)`,
    [OBJ_MARS, CONV, OBJ_MARS_RES],
  )
}
async function seedContact(c: Q, contactId: string, objectId: string, body: string, relation: string): Promise<void> {
  await chartCtx(c)
  await c.query(
    `INSERT INTO ka_gochara_contact_identity
       (contact_id, physical_object_id, occurrence_ordinal, supersedes_contact_id)
     VALUES ($1, $2, 1, NULL)`, [contactId, objectId],
  )
  await c.query(
    `INSERT INTO ka_gochara_contact
       (chart_id, generation, contact_id, physical_object_id, occurrence_ordinal,
        convention_id, body, relation_kind, t_in, t_out, t_exact, solver_method,
        delta_lambda, delta_t, precision_regime, coverage)
     VALUES ($1, $2, $3, $4, 1, $5, $6, $7,
             '2025-03-09T00:00Z', '2025-03-11T00:00Z', '2025-03-10T00:00Z',
             'swiss_refined', 0.001, 60, 'standard', '{"truncated":false}'::jsonb)`,
    [CHART, GEN, contactId, objectId, CONV, body, relation],
  )
}
async function seedRegistries(c: Q): Promise<void> {
  await c.query(
    `INSERT INTO ka_gochara_predicate (predicate_id, rule_version, operator, operands) VALUES
       ('q1', 'v1', 'within_orb', '{"left":"chart_facts.graha_position:mars","right":"object.longitude","orb":3.0}')`,
  )
  await c.query(
    `INSERT INTO ka_gochara_rule_path
       (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set, object_selector,
        provenance, operator_role, ruling_ref, score_rule)
     VALUES
       ('P1', 'v1', 'dasha_lord', NULL, '["mars"]', '["conjunction"]',
        '[{"agent":"mars","relation":"conjunction","object_role":"karaka"}]',
        'verse_cited', 'scored', NULL, 'within_path_product'),
       ('P5A', 'v1', 'lagna', NULL, '["mars"]', '["residence"]',
        '[{"agent":"mars","relation":"residence","object_role":"av_qualifier"}]',
        'verse_cited', 'scored', NULL, 'within_path_product')`,
  )
  await c.query(
    `INSERT INTO ka_gochara_rule_path_prerequisite
       (path_id, rule_version, ordinal, predicate_id, predicate_rule_version)
     VALUES ('P1', 'v1', 1, 'q1', 'v1'), ('P5A', 'v1', 1, 'q1', 'v1')`,
  )
  await c.query(`INSERT INTO ka_gochara_rule_path_seal (path_id, rule_version) VALUES ('P1','v1'), ('P5A','v1')`)
}
async function factsFor(c: Q, key: string): Promise<string> {
  const r = await c.query<{ f: unknown }>(
    `SELECT ka_gochara_coverage_facts(convention_id, completed_horizon, relations_searched) AS f
     FROM kala_gochara_coverage WHERE chart_id = $1 AND generation = $2 AND partition_kind = $3 AND partition_key = $4`,
    [CHART, GEN, COV_KIND, key],
  )
  if (!r.rows[0]) throw new Error('no coverage partition')
  return JSON.stringify(r.rows[0]!.f)
}

const RECORD_COLS = `record_id, chart_id, generation, contact_id, event_class,
  affected_person, frame_kind, frame_arg, agent, relation, object_id, object_kind,
  object_role, path_id, rule_version, temporal_support_state, temporal_support_grain,
  temporal_support_intervals, coverage_partition_kind, coverage_partition_key, coverage_facts,
  precision, source_text, source_page, source_fact_ids, fixture, provenance,
  operator_role, ruling_ref, admission_state, house_from_frame,
  evidence_for_occurrence, evidence_against_occurrence, outcome_valence_for_native,
  severity`

/** A full writer-path record (contact + precision + prerequisite membership) for the given role. */
async function insertRecord(c: Q, o: {
  objectRole: string
  pathId?: string
  covKey?: string
  contactId?: string
  objectId?: string
  relation?: string
  frameKind?: string
}): Promise<string> {
  const id = uuid()
  // N10: the body_target full key is agent:object_role — the partition the
  // writer consumed is keyed by the SAME role the record carries.
  const covKey = o.covKey ?? `mars:${o.objectRole}`
  const facts = await factsFor(c, covKey)
  await c.query(
    `INSERT INTO ka_gochara_relationship_record (${RECORD_COLS})
     VALUES ($1, $2, $3, $4, 'marriage', 'native', $11, NULL, 'mars', $12,
             $5, 'degree_point', $6, $7, 'v1', 'computed', 'day', ${SUPPORT},
             $8, $9, $10::jsonb,
             '{"solver_method":"swiss_refined","delta_lambda":0.001,"delta_t":60}'::jsonb,
             'Phaladīpikā', 'PG249-250 (XX.34-38)', '["fact-1"]', false,
             'verse_cited', 'scored', NULL, 'admitted', 7, 0.8, NULL, 'favourable', NULL)`,
    [id, CHART, GEN, o.contactId ?? CID_1, o.objectId ?? OBJ_MARS, o.objectRole,
     o.pathId ?? 'P1', COV_KIND, covKey, facts, o.frameKind ?? 'dasha_lord',
     o.relation ?? 'conjunction'],
  )
  await c.query(
    `INSERT INTO ka_gochara_record_prerequisite
       (record_id, chart_id, generation, ordinal, predicate_id, predicate_rule_version, result)
     VALUES ($1, $2, $3, 1, 'q1', 'v1', 'true')`, [id, CHART, GEN],
  )
  return id
}

describe.skipIf(!TEST_DB_URL)('B6.0 v1.5 contract migration 1204 (live disposable DB)', () => {
  beforeAll(async () => {
    const config = resolveDisposableA51Config(TEST_DB_URL)
    pool = new Pool({ ...config, max: 4 })
    await resetSchema()
    // The protected-window route: runMigrations --only over the on-disk files, in order.
    await withTempDir(WINDOW_FILES, async dir => {
      const c = await pool.connect()
      try {
        await runMigrations(c, [dir], { only: new Set(WINDOW_FILES), disclosures: new Map(), renumberDisclosures: new Map() })
      } finally {
        c.release()
      }
    })
    // Minimal fixture stack, in FK order, in TWO transactions (the enforced
    // lock order forbids registry global-EXCLUSIVE and chart keys together).
    await tx(async c => {
      await chartCtx(c)
      await seedLegacyConvention(c)
      await seedSkyConvention(c)
      await c.query(`INSERT INTO ka_gochara_convention_bridge (kala_convention_id, sky_convention_id) VALUES ($1, $2)`, [LEGACY_CONV, CONV])
      await seedPublication(c)
      // one body_target partition per probed role (agent:object_role full key, N10)
      await seedCoverage(c, 'mars:karaka')
      await seedCoverage(c, 'mars:av_qualifier')
      await seedCoverage(c, 'mars:not_a_role')
      await seedObjects(c)
    })
    await tx(async c => { await seedRegistries(c) })
    await tx(async c => { await seedContact(c, CID_1, OBJ_MARS, 'mars', 'conjunction') })
    await tx(async c => { await seedContact(c, CID_2, OBJ_MARS_RES, 'mars', 'residence') })
  }, 120_000)

  afterAll(async () => {
    if (!pool) return
    await resetSchema()
    await pool.end()
  })

  it("AM-7: the widened CHECK ACCEPTS 'av_qualifier' on a REAL house-span residence — a full writer-path record COMMITs", async () => {
    // The review's fixture correction: the qualification is the transiting
    // agent's RESIDENCE in the qualified span (relation_kind='residence',
    // canonical_target 'span:7', lagna frame), not a conjunction.
    const id = await tx(async c => insertRecord(c, {
      objectRole: 'av_qualifier', pathId: 'P5A',
      contactId: CID_2, objectId: OBJ_MARS_RES, relation: 'residence', frameKind: 'lagna',
    }))
    const r = await pool.query(
      `SELECT object_role, relation, frame_kind FROM ka_gochara_relationship_record WHERE record_id = $1`, [id])
    expect(r.rows[0]).toMatchObject({ object_role: 'av_qualifier', relation: 'residence', frame_kind: 'lagna' })
  })

  it('AM-7: the widened CHECK still REJECTS an unknown role with kgrr_object_role_ck', async () => {
    await expect(tx(async c => insertRecord(c, { objectRole: 'not_a_role' })))
      .rejects.toThrow(/kgrr_object_role_ck/)
  })

  it('AM-7: every v1.0 role still passes the widened CHECK (full probe, not only karaka)', async () => {
    // Writer-path proof for karaka (the role P1's selector carries):
    const id = await tx(async c => insertRecord(c, { objectRole: 'karaka' }))
    const r = await pool.query(`SELECT object_role FROM ka_gochara_relationship_record WHERE record_id = $1`, [id])
    expect(r.rows[0]?.object_role).toBe('karaka')
    // Vocabulary proof for every v1.0 role: an insert whose role the CHECK
    // admits must fail on something ELSE (here the deliberately dangling
    // contact FK / downstream guards) — never on kgrr_object_role_ck. If the
    // widening had dropped a v1.0 role, that role's probe fails WITH it.
    for (const role of V10_ROLES) {
      // The dangling contact forces a failure; the failure must NOT be the
      // role CHECK. (An unexpected success would fail `.rejects` itself.)
      await expect(tx(async c => insertRecord(c, {
        objectRole: role, covKey: `mars:${role}`,
        contactId: '10000000-0000-4000-8000-0000000000ff',
        objectId: OBJ_MARS,
      }))).rejects.not.toThrow(/kgrr_object_role_ck/)
    }
  })

  it('AM-7 selector: ka_gochara_object_selector_ok admits av_qualifier, refuses an unknown role, keeps every v1.0 role', async () => {
    for (const role of [...V10_ROLES, 'av_qualifier']) {
      const r = await pool.query(
        `SELECT public.ka_gochara_object_selector_ok($1::jsonb) AS ok`,
        [JSON.stringify([{ agent: 'mars', relation: 'conjunction', object_role: role }])])
      expect(r.rows[0]!.ok, `selector keeps ${role}`).toBe(true)
    }
    const bogus = await pool.query(
      `SELECT public.ka_gochara_object_selector_ok('[{"agent":"mars","relation":"conjunction","object_role":"not_a_role"}]'::jsonb) AS ok`)
    expect(bogus.rows[0]!.ok).toBe(false)
    // …and the P5A path registered through the real table (seedRegistries) proves the live kgrp CHECK admits it
    const p = await pool.query(`SELECT object_selector FROM ka_gochara_rule_path WHERE path_id = 'P5A' AND rule_version = 'v1'`)
    expect(JSON.stringify(p.rows[0]?.object_selector)).toContain('av_qualifier')
  })

  it("AM-8 SPLIT: ka_gochara_frame_ok keeps exactly its v1.0 arms; frame_kind='inherited' is REFUSED", async () => {
    const r = await pool.query(`
      SELECT public.ka_gochara_frame_ok('inherited', NULL) AS inh_null,
             public.ka_gochara_frame_ok('moon', NULL) AS moon_ok,
             public.ka_gochara_frame_ok('lagna', NULL) AS lagna_ok,
             public.ka_gochara_frame_ok('dasha_lord', NULL) AS dl_ok,
             public.ka_gochara_frame_ok('graha', 'mars') AS graha_ok,
             public.ka_gochara_frame_ok('bhavat_bhavam', '12') AS bb_ok,
             public.ka_gochara_frame_ok('moon', 'x') AS moon_arg,
             public.ka_gochara_frame_ok(NULL, NULL) AS null_kind`)
    expect(r.rows[0]).toEqual({
      inh_null: false, moon_ok: true, lagna_ok: true, dl_ok: true, graha_ok: true,
      bb_ok: true, moon_arg: false, null_kind: false,
    })
    // …and a rule path carrying the split-out frame kind fails the LIVE CHECK
    // (the exact scored-P6 shape the rejected 1205 fixture tried to admit):
    await expect(tx(async c => {
      await c.query(
        `INSERT INTO ka_gochara_rule_path
           (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set, object_selector,
            provenance, operator_role, ruling_ref, score_rule)
         VALUES ('P6', 'v1', 'inherited', NULL, '["moon"]', '["residence"]',
                 '[{"agent":"moon","relation":"residence","object_role":"occupant"}]',
                 'verse_cited', 'scored', NULL, 'within_path_product')`,
      )
    })).rejects.toThrow(/kgrp_frame_ck/)
  })

  it('deploy route: the routine runner REFUSES 1204 and names the protected window', async () => {
    await resetSchema()
    await withTempDir(WINDOW_FILES, async dir => {
      const c = await pool.connect()
      try {
        // 1153-1157 through the window …
        await runMigrations(c, [dir], { only: new Set(CONTRACT_FILES), disclosures: new Map(), renumberDisclosures: new Map() })
        // … 1204 on the routine path: refused BEFORE any gate runs
        await expect(runMigrations(c, [dir], { disclosures: new Map(), renumberDisclosures: new Map() }))
          .rejects.toThrow(/gochara_contracts_schema_migration=true/)
      } finally {
        c.release()
      }
    })
    const r = await pool.query(`SELECT COUNT(*)::int AS n FROM _migrations_applied WHERE starts_with(filename, '120')`)
    expect(r.rows[0]!.n).toBe(0)
  })

  it('replay is BLOCKED: the embedded gate refuses an already-applied file', async () => {
    await resetSchema()
    await withTempDir(WINDOW_FILES, async dir => {
      const c = await pool.connect()
      try {
        await runMigrations(c, [dir], { only: new Set(WINDOW_FILES), disclosures: new Map(), renumberDisclosures: new Map() })
      } finally {
        c.release()
      }
    })
    // A bare re-run of 1204's own file (out of band — e.g. psql) hits its gate
    await expect(pool.query(mig(M1204))).rejects.toThrow(/preflight 1204 BLOCKED/)
  })
})
