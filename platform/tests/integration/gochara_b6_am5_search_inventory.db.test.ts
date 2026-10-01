// @vitest-environment node
/**
 * Pravāha B6.0 / F-1 — LIVE-DB adversarial suite for migration 1206 (AM-5 search-completeness
 * storage + seal checks), executed against a REAL throwaway Postgres (CLAUDE.md §N.8: the
 * test runs the on-disk SQL itself). Replaces the toy executable model (design/evidence/am5_*.py
 * — a logic check only) as the acceptance evidence: every case of the draft's adversarial matrix
 * runs as a real INSERT / finalise / seal attempt.
 *
 * v1.1 (Codex review of edece78c9, R1–R5): the L1 stand-ins carry the REAL column sets
 * (`computed_at` audit column, float8 / numeric / timestamptz material columns); the builder
 * flow runs `SET ROLE data_plane_builder` with the REAL 1216 grants; sealing runs as a separate
 * principal; the lock protocol is exercised with COMPETING SESSIONS; every table × every
 * operation is attacked after sealing; R1–R4 have regression adversaries.
 *
 * Independent TypeScript reference implementations of the UUIDv8, canonical-JSON and the digest
 * preimages cross-check the SQL helpers; the W1 vectors computed by the Python model must be
 * reproduced byte-for-byte by the database.
 *
 * Requires a THROWAWAY database. Locally the suite skips itself without
 * GOCHARA_A51_TEST_DATABASE_URL; **CI sets GOCHARA_REQUIRE_DB=1, which turns a missing URL into a
 * FAILURE** (no silent skipping). Same disposable boundary as the A5.1 / B6 suites.
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool, type PoolClient } from 'pg'
import { createHash } from 'node:crypto'
import { copyFileSync, mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import path from 'node:path'
import { TRACKER_DDL, TRACKER_IDENTITY_DDL, runMigrations } from '../../scripts/migrate'
import { resolveDisposableA51Config } from './gochara_a5_1_disposable_url'

const TEST_DB_URL = process.env.GOCHARA_A51_TEST_DATABASE_URL
const REQUIRE_DB = process.env.GOCHARA_REQUIRE_DB === '1'

// The suite must never be skipped silently where it is required (CI).
describe.runIf(REQUIRE_DB)('B6.0 F-1 migration 1206 — the live-DB suite is REQUIRED here', () => {
  it('GOCHARA_A51_TEST_DATABASE_URL is set (a missing URL is a failure, not a skip)', () => {
    expect(TEST_DB_URL, 'GOCHARA_REQUIRE_DB=1 but GOCHARA_A51_TEST_DATABASE_URL is unset').toBeTruthy()
  })
})

const MIGRATIONS_DIR = path.resolve(process.cwd(), 'migrations')
const PARENT_FILES = [
  '1081_nirmana_l3_gochara_ledger_coverage_publication.sql',
  '1087_nirmana_l3_gochara_contacts_inclusivity_completeness_tier_basis.sql',
  '1152_kala_gochara_contacts_t_exact_nullable_truncated.sql',
] as const
const CONTRACT_FILES = [
  '1153_gochara_sky_event_substrate.sql', '1154_gochara_rule_path_registry.sql',
  '1155_gochara_relationship_record.sql', '1156_gochara_eval_window.sql',
  '1157_gochara_av_polarity_declaration.sql',
] as const
const M1204 = '1204_gochara_av_qualifier_object_role.sql'
const M1206 = '1206_gochara_search_inventory_completeness.sql'
const M1216 = '1216_gochara_contract_builder_grants.sql'
const WINDOW_FILES = [...CONTRACT_FILES, M1204, M1206, M1216] as const

const BUILDER = 'data_plane_builder'
const SEALER = 'gochara_sealer'
// What migration 1206 §7 grants the builder EXECUTE on (12 own helpers + 5 contract functions its guards call).
const BUILDER_OWN_FUNCTIONS = [
  'ka_gochara_sha256_hex(text)', 'ka_gochara_uuidv8(text)', 'ka_gochara_canonical_json(jsonb)',
  'ka_gochara_utc_ts(timestamptz)', 'ka_gochara_uuid_set_ok(uuid[])',
  'ka_gochara_search_input_digest(text, jsonb, text, text, text[])', 'ka_gochara_search_l1_facts_digest(uuid, text[])',
  'ka_gochara_search_dasha_digest(uuid, uuid[])', 'ka_gochara_search_av_entry(text)',
  'ka_gochara_search_inventory_preimage(uuid, text, text)', 'ka_gochara_search_inventory_digest(uuid, text, text)',
  'ka_gochara_search_ledger_digest(uuid, text, text)',
] as const
const BUILDER_CONTRACT_FUNCTIONS = [
  'ka_gochara_lock_chart(uuid)', 'ka_gochara_lock_global_shared()', 'ka_gochara_generation_is_sealed(uuid, text)',
  'ka_gochara_generation_governed(text)', 'ka_gochara_horizon_finite_ok(tstzrange)',
] as const
// The seal principal's functions (names; unique in the schema).
const SEALER_FUNCTIONS = [
  'ka_gochara_lock_chart', 'ka_gochara_seal_generation', 'ka_gochara_generation_governed', 'ka_gochara_coverage_drift',
  'ka_gochara_horizon_finite_ok', 'ka_gochara_coverage_facts', 'ka_gochara_facts_horizon',
  'ka_gochara_membership_violations', 'ka_gochara_membership_violation', 'ka_gochara_lock_global_shared',
  'ka_gochara_search_completeness_violations', 'ka_gochara_search_l1_facts_digest', 'ka_gochara_sha256_hex',
  'ka_gochara_canonical_json', 'ka_gochara_search_dasha_digest', 'ka_gochara_search_av_entry',
  'ka_gochara_search_inventory_digest', 'ka_gochara_search_ledger_digest', 'ka_gochara_search_inventory_preimage',
  'ka_gochara_utc_ts',
] as const
// The routine/protected migration principal: in production it OWNS every table and function, and the
// governed bootstrap revokes PUBLIC EXECUTE on whatever it creates (platform/scripts/
// nirmana-evidence-ownership-preflight.ts:259). The suite builds the same world so a missing
// function grant fails here, not in production (steward M20261001T224443-bfc4 R6).
const OWNER = 'amjis_app'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const CONV = 'sha256:eac922d4c3b0deb700112f2260cd250a0388ab159f4a1c4bca9451281a48e7a3'   // AM-1 vector digest
const CONV_OTHER = 'sha256:' + 'b'.repeat(64)                                               // a second sky convention
const LEGACY_CONV = 'legacy:c0'            // bridged to CONV
const LEGACY_OTHER = 'legacy:c1'           // bridged to CONV_OTHER (an INCOMPATIBLE bridge)
const LEGACY_NOBRIDGE = 'legacy:c2'        // registered, NEVER bridged
const AV_DECL = 'av-build:l1:482012f1:v1'
const LO = '2025-01-01T00:00:00Z'
const MID = '2025-02-01T00:00:00Z'
const HI = '2025-03-01T00:00:00Z'
const HORIZON_SQL = `tstzrange('${LO}','${HI}','[)')`
const VEC = { bg_transit_rules: 'd1', bg_transit_av_gates: 'd2' }
const B_P6 = 'spec:GOCHARA_DESIGN_SPECS@1.4#§2.2/P6'
const B_EMPTY = 'oracle:O-RP-8'
const B_NA = 'spec:GOCHARA_DESIGN_SPECS@1.4#§2.2/na'
const CLS = 'marriage'

// the sealed registry the suite builds: every (path, version) must be ACCOUNTED for per class
const REGISTRY: Array<[string, string]> = [['p1', '1.0'], ['p1', '1.1'], ['p5a', '1.0'], ['p6', '1.0']]

// ── independent reference implementation (node crypto) ─────────────────────────
const sha = (s: string): string => createHash('sha256').update(s, 'utf8').digest('hex')
function uuidv8(s: string): string {
  const b = createHash('sha256').update(s, 'utf8').digest().subarray(0, 16)
  b[6] = (b[6]! & 0x0f) | 0x80
  b[8] = (b[8]! & 0x3f) | 0x80
  const h = b.toString('hex')
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`
}
function canonJson(v: unknown): string {
  if (v === null || typeof v !== 'object') return JSON.stringify(v)
  if (Array.isArray(v)) return '[' + v.map(canonJson).join(',') + ']'
  const o = v as Record<string, unknown>
  return '{' + Object.keys(o).sort().map(k => JSON.stringify(k) + ':' + canonJson(o[k])).join(',') + '}'
}
const inputDigest = (c: { conv: string; vec: unknown; l1: string; dasha: string; av: string[] }): string =>
  sha([`av_declarations=${[...c.av].sort().join(',')}`, `convention_id=${c.conv}`, `dasha_digest=${c.dasha}`,
       `input_generation_vector=${canonJson(c.vec)}`, `l1_facts_digest=${c.l1}`].join('\n'))

type Ob = readonly [agent: string, relation: string, role: string, target: string, frame: string, person: string]
const obBytes = (path_: string, ver: string, o: Ob, cls = CLS): string => [cls, path_, ver, ...o].join('|')
const obId = (path_: string, ver: string, o: Ob): string => uuidv8(obBytes(path_, ver, o))
const P1A: Ob = ['jupiter', 'residence', 'lord', 'lord_of:7', 'dasha_lord', 'self']
const P1B: Ob = ['jupiter', 'residence', 'occupant', 'occupant_of:7', 'dasha_lord', 'self']
const P5A: Ob = ['saturn', 'residence', 'av_qualifier', 'house_span:7', 'lagna', 'self']
const P5B: Ob = ['saturn', 'residence', 'av_qualifier', 'house_span:8', 'lagna', 'self']

interface PinRef { path: string; ver?: string; disp: 'included' | 'computed_empty' | 'excluded'; reason?: string; ruling?: string; basis?: string; ids: string[] }
const sortC = (xs: string[]): string[] => [...xs].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0))
function tsInventoryDigest(conv: string, input: string, pins: PinRef[], obs: string[]): string {
  const lines = [`convention=${conv}`, `horizon=[${LO},${HI})`, `input=${input}`]
  for (const p of [...pins].sort((a, b) => (`${a.path}|${a.ver ?? '1.0'}` < `${b.path}|${b.ver ?? '1.0'}` ? -1 : 1)))
    lines.push(`pin=${p.path}|${p.ver ?? '1.0'}|${p.disp}|${p.reason ?? ''}|${p.ruling ?? ''}|${p.basis ?? ''}|${sortC(p.ids).join(',')}`)
  for (const o of sortC(obs)) lines.push(`ob=${o}`)
  return sha(lines.join('\n'))
}
// ledger_digest preimage (v1.1): `input=<input_digest>` first, so an EMPTY ledger is input-bound too
const tsLedgerDigest = (rows: Array<[string, string, string, string]>, input: string): string =>
  sha(['input=' + input, ...sortC(rows.map(([id, lo, hi, st]) => `${id}|${lo}|${hi}|${st}|${input}`))].join('\n'))

// ── harness ────────────────────────────────────────────────────────────────────
let pool: Pool
type Q = Pick<PoolClient, 'query'>
let genSeq = 0
const nextGen = (): string => `5.${++genSeq + 20}`

function mig(name: string): string { return readFileSync(join(MIGRATIONS_DIR, name), 'utf8') }
async function tx<T>(fn: (c: PoolClient) => Promise<T>, opts: { tz?: string; role?: string } = {}): Promise<T> {
  const c = await pool.connect()
  try {
    await c.query('BEGIN')
    if (opts.tz) await c.query(`SET LOCAL TIME ZONE '${opts.tz}'`)
    if (opts.role) await c.query(`SET LOCAL ROLE ${opts.role}`)
    const r = await fn(c)
    await c.query('COMMIT')
    return r
  } catch (err) { await c.query('ROLLBACK').catch(() => undefined); throw err }
  finally { c.release() }
}
async function withTempDir<T>(files: readonly string[], fn: (dir: string) => Promise<T>): Promise<T> {
  const dir = mkdtempSync(join(tmpdir(), 'gochara-am5-'))
  try { for (const f of files) copyFileSync(join(MIGRATIONS_DIR, f), join(dir, f)); return await fn(dir) }
  finally { rmSync(dir, { recursive: true, force: true }) }
}
/** Run `fn` on one connection AS the migration principal (production: amjis_app owns everything). */
async function asOwner<T>(fn: (c: PoolClient) => Promise<T>): Promise<T> {
  const c = await pool.connect()
  try { await c.query(`SET ROLE ${OWNER}`); return await fn(c) }
  finally { await c.query('RESET ROLE').catch(() => undefined); c.release() }
}
async function window(files: readonly string[]): Promise<void> {
  await withTempDir(WINDOW_FILES, async dir => {
    await asOwner(c => runMigrations(c, [dir], { only: new Set(files), disclosures: new Map(), renumberDisclosures: new Map() }))
  })
}
// The REAL production column sets of the two L1 tables the input digests read (information_schema,
// read-only, 2026-10-02): audit column `computed_at`; float8 / numeric / timestamptz / date / array
// material columns. Constraints are reduced to the keys (PK fact_id / dasha_row_id).
const L1_STANDINS = `
  CREATE TABLE chart_facts (
    fact_id text PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text NOT NULL, build_id uuid NOT NULL,
    fact_category text NOT NULL, fact_subject text NOT NULL, fact_key text NOT NULL,
    fact_value_text text, fact_value_num numeric, fact_value_jsonb jsonb, unit text,
    citation_ref text NOT NULL DEFAULT '', citation_human text NOT NULL DEFAULT '',
    source_calculation text NOT NULL DEFAULT '', verification_pass_status text NOT NULL DEFAULT 'single_pass',
    engine_version text NOT NULL DEFAULT 'v', salience_formula_ver text,
    computed_at timestamptz NOT NULL DEFAULT now(), tolerance_arcsec double precision,
    near_sign_boundary_flag boolean DEFAULT false, near_nakshatra_boundary_flag boolean DEFAULT false,
    vargottama_flag_at_point boolean DEFAULT false, formula_provenance_text text,
    cross_ayanamsha_divergence_arcsec double precision DEFAULT 0.0, formula_id text);
  CREATE TABLE chart_dashas (
    dasha_row_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, ayanamsha_id text NOT NULL,
    build_id uuid NOT NULL, system_id text NOT NULL, level_n integer NOT NULL, parent_row_id uuid,
    lord_graha text NOT NULL, lord_sign text, start_date date NOT NULL, end_date date NOT NULL,
    start_iso timestamptz NOT NULL, end_iso timestamptz NOT NULL, duration_days numeric NOT NULL,
    sandhi_flag boolean NOT NULL DEFAULT false, karaka_role_at_period text,
    verification_pass_status text NOT NULL DEFAULT 'two_pass_verified', verification_method text NOT NULL DEFAULT '',
    citation_ref text NOT NULL DEFAULT '', citation_human text NOT NULL DEFAULT '',
    computed_at timestamptz NOT NULL DEFAULT now(), engine_version text NOT NULL DEFAULT '',
    lord_natal_shadbala_total numeric, next_dasha_start_iso timestamptz, concurrent_system_lords_jsonb jsonb,
    anchored_solar_return_iso timestamptz, karakas_active_during_period text[]);`
async function resetSchema(): Promise<void> {
  await ensureRoles()
  await pool.query(`DROP SCHEMA public CASCADE; CREATE SCHEMA public AUTHORIZATION ${OWNER};`)
  await asOwner(async c => {
    await c.query(`CREATE TABLE charts (id UUID PRIMARY KEY DEFAULT gen_random_uuid());
                   ${L1_STANDINS}`)
    for (const f of PARENT_FILES) await c.query(mig(f))
    await c.query(TRACKER_DDL)
    await c.query(TRACKER_IDENTITY_DDL)
  })
  await pool.query(`INSERT INTO charts (id) VALUES ($1)`, [CHART])
}
/** Roles are cluster-global: create each only if absent, and install the production default-privilege
 *  revocation (per database, idempotent). */
async function ensureRoles(): Promise<void> {
  for (const r of [OWNER, BUILDER, SEALER])
    await pool.query(`DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='${r}') THEN CREATE ROLE ${r} NOLOGIN; END IF; END $$`)
  await pool.query(`ALTER DEFAULT PRIVILEGES FOR ROLE ${OWNER} REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC`)
}
/** Leave a plain superuser-owned schema, then clear this database's role dependencies and drop what no
 *  other database on the cluster still needs. */
async function dropRoles(): Promise<void> {
  await pool.query(`DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;`)
  for (const r of [BUILDER, SEALER, OWNER]) {
    await pool.query(`DROP OWNED BY ${r} CASCADE`).catch(() => undefined)
    await pool.query(`DROP ROLE IF EXISTS ${r}`).catch(() => undefined)
  }
}
const chartCtx = (c: Q) => c.query(`SELECT ka_gochara_lock_chart($1)`, [CHART])

// fixtures that are generation-independent
const BUILD = '40000000-0000-4000-8000-000000000001'
const DASHA_IDS = ['30000000-0000-4000-8000-000000000001', '30000000-0000-4000-8000-000000000002']
async function seedStatic(): Promise<void> {
  await tx(async c => {
    await chartCtx(c)
    for (const lc of [LEGACY_CONV, LEGACY_OTHER, LEGACY_NOBRIDGE])
      await c.query(`INSERT INTO kala_gochara_convention
         (convention_id, zodiac, ayanamsha, sidereal_method, node_model, node_source, epoch_convention, time_scale,
          house_system, ephemeris_mode, method_version)
         VALUES ($1,'sidereal','lahiri_chitrapaksha','true_chitra','mean','swiss','j2000','utc','whole_sign','swiss',$2)`,
        [lc, lc])
    for (const sc of [CONV, CONV_OTHER])
      await c.query(`INSERT INTO ka_gochara_sky_convention
         (convention_id, ephemeris_generation, ayanamsha, node_convention, grid, method_version, domain_start, domain_end)
         VALUES ($1,'de441','lahiri_chitrapaksha','mean','1s','m1','2025-01-01T00:00Z','2026-01-01T00:00Z')`, [sc])
    await c.query(`INSERT INTO ka_gochara_convention_bridge (kala_convention_id, sky_convention_id) VALUES ($1,$2),($3,$4)`,
      [LEGACY_CONV, CONV, LEGACY_OTHER, CONV_OTHER])           // LEGACY_NOBRIDGE deliberately unbridged
    await c.query(`INSERT INTO ka_gochara_av_polarity_declaration
       (convention, benefic_mark_name, malefic_mark_name, source_ref, applies_to_fact_categories)
       VALUES ($1,'rekhā','khaṇḍa','L1_ASHTAKAVARGA_EXTRACT_v1_1', ARRAY['ashtakavarga_bindu'])`, [AV_DECL])
  })
  await pool.query(`INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, build_id, fact_category, fact_subject, fact_key,
                      fact_value_text, fact_value_num, unit, tolerance_arcsec)
                    VALUES ('F1',$1,'lahiri_chitrapaksha',$2,'graha_shadbala_total','SUN','rupa','a', 8.47,'rupa', 0.1),
                           ('F2',$1,'lahiri_chitrapaksha',$2,'graha_shadbala_total','MOON','rupa','b', 5.65,'rupa', 0.2)`, [CHART, BUILD])
  await pool.query(`INSERT INTO chart_dashas (dasha_row_id, chart_id, ayanamsha_id, build_id, system_id, level_n, lord_graha,
                      start_date, end_date, start_iso, end_iso, duration_days, lord_natal_shadbala_total, next_dasha_start_iso)
                    VALUES ($1,$3,'lahiri_chitrapaksha',$4,'vimshottari',1,'Mercury','2010-08-18','2027-08-18','2010-08-18T15:50:23Z','2027-08-18T21:50:23Z',6209,7.55,'2027-08-18T21:50:23Z'),
                           ($2,$3,'lahiri_chitrapaksha',$4,'vimshottari',2,'Ketu','2013-01-14','2014-01-11','2013-01-14T07:17:23Z','2014-01-11T12:14:23Z',362,0.625,'2014-01-11T12:14:23Z')`,
    [DASHA_IDS[0], DASHA_IDS[1], CHART, BUILD])
  await tx(async c => registry(c, REGISTRY))
  // the L1 read grants the builder principal holds in production (stand-ins carry none by default)
  await pool.query(`GRANT SELECT ON chart_facts, chart_dashas TO ${BUILDER}, ${SEALER}`)
}
async function registry(c: Q, ids: Array<[string, string]>): Promise<void> {
  const sel: Record<string, [string, string, string, string, string]> = {
    p1: ['dasha_lord', 'jupiter', 'residence', 'lord', 'verse_cited'],
    p5a: ['lagna', 'saturn', 'residence', 'av_qualifier', 'verse_cited'],
    p6: ['moon', 'moon', 'conjunction', 'karaka', 'uncited_extension'],
    p7: ['lagna', 'mars', 'residence', 'occupant', 'verse_cited'],
  }
  await c.query(`INSERT INTO ka_gochara_predicate (predicate_id, rule_version, operator, operands)
     VALUES ('q1','v1','within_orb','{"left":"chart_facts.graha_position:mars","right":"object.longitude","orb":3.0}')
     ON CONFLICT DO NOTHING`)
  for (const [id, ver] of ids) {
    const [frame, agent, rel, role, prov] = sel[id]!
    await c.query(
      `INSERT INTO ka_gochara_rule_path (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set, object_selector,
         provenance, operator_role, ruling_ref, score_rule)
       VALUES ($1,$9,$2,NULL,$3::jsonb,$4::jsonb,$5::jsonb,$6,$7,$8,'within_path_product')`,
      [id, frame, JSON.stringify([agent]), JSON.stringify([rel]),
       JSON.stringify([{ agent, relation: rel, object_role: role }]), prov,
       id === 'p6' ? 'testimony' : 'scored', prov === 'uncited_extension' ? 'R-9' : null, ver])
    await c.query(`INSERT INTO ka_gochara_rule_path_prerequisite (path_id, rule_version, ordinal, predicate_id, predicate_rule_version)
                   VALUES ($1,$2,1,'q1','v1')`, [id, ver])
    await c.query(`INSERT INTO ka_gochara_rule_path_seal (path_id, rule_version) VALUES ($1,$2)`, [id, ver])
  }
}

// ── per-generation builders (each step takes the chart key first, in ONE transaction by the caller) ──
interface Snap { conv: string; vec: unknown; l1: string; dasha: string; av: string[]; digest: string }
async function publication(c: Q, gen: string, vec: unknown = VEC, legacy = LEGACY_CONV): Promise<void> {
  await c.query(`INSERT INTO kala_gochara_publication
     (chart_id, generation, writer_asset_id, convention_id, input_generation_vector, ephemeris_backend, horizon, row_counts, content_digest, status)
     VALUES ($1,$2,'ka_gochara',$3,$4::jsonb,'{}',${HORIZON_SQL},'{}','digest','candidate')`, [CHART, gen, legacy, JSON.stringify(vec)])
}
async function snapshotLive(c: Q, gen: string, vec: unknown = VEC, conv = CONV): Promise<Snap> {
  const q = async (sqlText: string, args: unknown[]): Promise<string> => (await c.query<{ v: string }>(sqlText, args)).rows[0]!.v
  const l1 = await q(`SELECT ka_gochara_search_l1_facts_digest($1,$2::text[]) AS v`, [CHART, ['F1', 'F2']])
  const dasha = await q(`SELECT ka_gochara_search_dasha_digest($1,$2::uuid[]) AS v`, [CHART, DASHA_IDS])
  const av = [await q(`SELECT ka_gochara_search_av_entry($1) AS v`, [AV_DECL])]
  return snapshotWith(c, gen, { conv, vec, l1, dasha, av })
}
async function snapshotWith(c: Q, gen: string, s: Omit<Snap, 'digest'>): Promise<Snap> {
  const digest = inputDigest(s)
  await c.query(
    `INSERT INTO ka_gochara_search_input_snapshot
       (chart_id, generation, convention_id, input_generation_vector, consumed_fact_ids, consumed_dasha_row_ids,
        av_declarations, l1_facts_digest, dasha_digest, input_digest)
     VALUES ($1,$2,$3,$4::jsonb,$5,$6,$7,$8,$9,$10)`,
    [CHART, gen, s.conv, JSON.stringify(s.vec), ['F1', 'F2'], DASHA_IDS, s.av, s.l1, s.dasha, digest])
  return { ...s, digest }
}
async function header(c: Q, gen: string, input: string, cls = CLS, horizon = HORIZON_SQL): Promise<void> {
  await c.query(`INSERT INTO ka_gochara_search_inventory (chart_id, generation, event_class, horizon, input_digest)
                 VALUES ($1,$2,$3,${horizon},$4)`, [CHART, gen, cls, input])
}
async function pin(c: Q, gen: string, p: PinRef, cls = CLS): Promise<void> {
  await c.query(
    `INSERT INTO ka_gochara_search_path_pin
       (chart_id, generation, event_class, path_id, rule_version, disposition, exclusion_reason, ruling_ref, basis, committed_ob_ids)
     VALUES ($1,$2,$3,$4,$10,$5,$6,$7,$8,$9::uuid[])`,
    [CHART, gen, cls, p.path, p.disp, p.reason ?? null, p.ruling ?? null, p.basis ?? null, sortC(p.ids), p.ver ?? '1.0'])
}
/** Pin every registry version NOT in `handled` as an explicit exclusion (the total partition). */
async function pinRest(c: Q, gen: string, handled: Array<[string, string]>, cls = CLS): Promise<void> {
  for (const [path_, ver] of REGISTRY) {
    if (handled.some(([p, v]) => p === path_ && v === ver)) continue
    if (path_ === 'p6') await pin(c, gen, { path: 'p6', ver, disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [] }, cls)
    else await pin(c, gen, { path: path_, ver, disp: 'excluded', reason: 'not_applicable_to_class', basis: B_NA, ids: [] }, cls)
  }
}
async function ob(c: Q, gen: string, path_: string, o: Ob, cls = CLS, ver = '1.0'): Promise<string> {
  const bytes = obBytes(path_, ver, o, cls); const id = uuidv8(bytes)
  await c.query(
    `INSERT INTO ka_gochara_search_obligation
       (chart_id, generation, event_class, ob_id, path_id, rule_version, agent, relation, object_role, target, frame, person, canonical_bytes)
     VALUES ($1,$2,$3,$4,$5,$13,$6,$7,$8,$9,$10,$11,$12)`, [CHART, gen, cls, id, path_, ...o, bytes, ver])
  return id
}
async function iv(c: Q, gen: string, id: string, lo: string, hi: string, input: string, state = 'searched_complete', cls = CLS): Promise<void> {
  await c.query(
    `INSERT INTO ka_gochara_search_interval (chart_id, generation, event_class, ob_id, search_range, state, input_digest)
     VALUES ($1,$2,$3,$4,tstzrange($5::timestamptz,$6::timestamptz,'[)'),$7,$8)`, [CHART, gen, cls, id, lo, hi, state, input])
}
async function finalize(c: Q, gen: string, cls = CLS): Promise<{ inv: string; led: string }> {
  const r = await c.query<{ inv: string; led: string }>(
    `SELECT ka_gochara_search_inventory_digest($1,$2,$3) AS inv, ka_gochara_search_ledger_digest($1,$2,$3) AS led`, [CHART, gen, cls])
  const d = r.rows[0]!
  await c.query(`UPDATE ka_gochara_search_inventory SET inventory_digest=$4, ledger_digest=$5
                 WHERE chart_id=$1 AND generation=$2 AND event_class=$3`, [CHART, gen, cls, d.inv, d.led])
  return d
}
async function partition(c: Q, gen: string, o: { cls?: string; relations?: string[]; horizon?: string; legacy?: string } = {}): Promise<void> {
  const h = o.horizon ?? HORIZON_SQL
  await c.query(
    `INSERT INTO kala_gochara_coverage
       (chart_id, generation, partition_kind, partition_key, convention_id, requested_horizon, completed_horizon, resolution,
        relations_searched, targets_requested, targets_resolved, targets_unresolved, target_resolution_state_counts, build_id)
     VALUES ($1,$2,'event_class',$3,$4,${h},${h},1.0,$5::text[],1,1,0,'{"resolved":1}','build-am5')`,
    [CHART, gen, o.cls ?? CLS, o.legacy ?? LEGACY_CONV, o.relations ?? ['residence']])
}
async function verify(c: Q, gen: string, digest: string, who = 'verifier-a', cls = CLS): Promise<void> {
  await c.query(`INSERT INTO ka_gochara_search_inventory_verification
     (chart_id, generation, event_class, verifier_id, verifier_version, rederived_inventory_digest) VALUES ($1,$2,$3,$4,'1',$5)`,
    [CHART, gen, cls, who, digest])
}
async function publishAndSeal(gen: string, opts: { role?: string; tz?: string } = {}): Promise<void> {
  if (!opts.role) opts = { ...opts, role: SEALER }   // every seal runs as the separately authorised principal
  await tx(async c => {
    await chartCtx(c)
    await c.query(`UPDATE kala_gochara_publication SET status='published', published_at=now() WHERE chart_id=$1 AND generation=$2`, [CHART, gen])
    await c.query(`SELECT ka_gochara_seal_generation($1,$2)`, [CHART, gen])
  }, opts)
}

/** A GOOD two-path build: p1@1.0 (A,B) + p5a@1.0 (A,B) included; every other registry version excluded;
 *  every obligation covered over the horizon; finalised; partition written; verified by a hash of the
 *  stored rows. `between` runs inside the build transaction before finalisation. */
interface Built { gen: string; snap: Snap; ids: { p1: string[]; p5a: string[] }; dig: { inv: string; led: string } }
async function goodBuild(gen: string, o: {
  vec?: unknown; skipP5aObligations?: boolean; p5a?: 'included' | 'computed_empty' | 'none'
  noVerify?: boolean; verifyDigest?: string; noPartition?: boolean; partitionRelations?: string[]
  tz?: string; role?: string
  between?: (c: PoolClient, b: { snap: Snap; ids: { p1: string[]; p5a: string[] } }) => Promise<void>
} = {}): Promise<Built> {
  return tx(async c => {
    await chartCtx(c)
    await publication(c, gen, o.vec)
    const snap = await snapshotLive(c, gen, o.vec ?? VEC)
    await header(c, gen, snap.digest)
    const p1 = [obId('p1', '1.0', P1A), obId('p1', '1.0', P1B)]
    const p5a = [obId('p5a', '1.0', P5A), obId('p5a', '1.0', P5B)]
    const mode = o.p5a ?? 'included'
    await pin(c, gen, { path: 'p1', disp: 'included', ids: p1 })
    if (mode === 'included') await pin(c, gen, { path: 'p5a', disp: 'included', ids: p5a })
    if (mode === 'computed_empty') await pin(c, gen, { path: 'p5a', disp: 'computed_empty', basis: B_EMPTY, ids: [] })
    await pinRest(c, gen, [['p1', '1.0'], ...(mode === 'none' ? [] : [['p5a', '1.0'] as [string, string]])])
    await ob(c, gen, 'p1', P1A); await ob(c, gen, 'p1', P1B)
    if (mode === 'included' && !o.skipP5aObligations) { await ob(c, gen, 'p5a', P5A); await ob(c, gen, 'p5a', P5B) }
    const covered = [...p1, ...(mode === 'included' && !o.skipP5aObligations ? p5a : [])]
    for (const id of covered) await iv(c, gen, id, LO, HI, snap.digest)
    if (o.between) await o.between(c, { snap, ids: { p1, p5a } })
    const dig = await finalize(c, gen)
    if (!o.noPartition) await partition(c, gen, { relations: o.partitionRelations })
    if (!o.noVerify) await verify(c, gen, o.verifyDigest ?? dig.inv)
    return { gen, snap, ids: { p1, p5a }, dig }
  }, { tz: o.tz, role: o.role })
}
const refused = async (p: Promise<unknown>, re: RegExp): Promise<void> => { await expect(p).rejects.toThrow(re) }

describe.skipIf(!TEST_DB_URL)('B6.0 F-1 migration 1206 — AM-5 search completeness (live disposable DB)', () => {
  let defsBefore: Map<string, string>

  async function defs(): Promise<Map<string, string>> {
    const fns = await pool.query<{ k: string; d: string }>(
      `SELECT 'fn:' || p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')' AS k, md5(pg_get_functiondef(p.oid)) AS d
       FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
       WHERE n.nspname = 'public' AND p.proname LIKE 'ka_gochara%'`)
    const cons = await pool.query<{ k: string; d: string }>(
      `SELECT 'con:' || c.conrelid::regclass::text || '.' || c.conname AS k, md5(pg_get_constraintdef(c.oid)) AS d
       FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace
       WHERE n.nspname = 'public' AND c.conrelid::regclass::text LIKE '%ka_gochara%'`)
    const trg = await pool.query<{ k: string; d: string }>(
      `SELECT 'trg:' || c.relname || '.' || t.tgname AS k, md5(pg_get_triggerdef(t.oid)) AS d
       FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
       WHERE NOT t.tgisinternal AND c.relname LIKE 'ka_gochara%'`)
    return new Map([...fns.rows, ...cons.rows, ...trg.rows].map(r => [r.k, r.d]))
  }

  beforeAll(async () => {
    pool = new Pool({ ...resolveDisposableA51Config(TEST_DB_URL), max: 8 })
    await resetSchema()
    await window([...CONTRACT_FILES, M1204])
    defsBefore = await defs()
    await window([M1206])
    await window([M1216])            // the REAL builder grants (1216) on top, as production routine deploys will
    await seedStatic()
    await pool.query(`GRANT USAGE ON SCHEMA public TO ${BUILDER}, ${SEALER}`)
    // the seal principal: INSERT on the seal table + UPDATE on the publication + the reads the seal functions perform
    await pool.query(`
      GRANT SELECT, INSERT ON ka_gochara_generation_seal TO ${SEALER};
      GRANT SELECT, UPDATE ON kala_gochara_publication TO ${SEALER};
      GRANT SELECT ON kala_gochara_coverage, ka_gochara_rule_path_seal, ka_gochara_convention_bridge,
        ka_gochara_av_polarity_declaration, ka_gochara_relationship_record, ka_gochara_eval_window,
        ka_gochara_eval_window_record, ka_gochara_search_input_snapshot, ka_gochara_search_inventory,
        ka_gochara_search_path_pin, ka_gochara_search_obligation, ka_gochara_search_interval,
        ka_gochara_search_inventory_verification TO ${SEALER}`)
    // The seal principal's EXECUTE: not granted by any migration (the sealing principal is the native's to
    // authorise — D-FLIP); this is the exact set the seal path reaches, derived by adding one EXECUTE per
    // 'permission denied for function X' until publishAndSeal-as-sealer converged, and proven sufficient by
    // every seal in this suite running as SEALER (publishAndSeal defaults to it).
    await pool.query(`GRANT EXECUTE ON FUNCTION ${SEALER_FUNCTIONS.map(f => `public.${f}`).join(', ')} TO ${SEALER}`)
  }, 180_000)

  afterAll(async () => {
    if (!pool) return
    await dropRoles()
    await pool.end()
  })

  // ── 0. additive proof ──────────────────────────────────────────────────────────
  it('1206 applies through the exact --only window AFTER 1204, creates the six tables, and changes NO applied object', async () => {
    const t = await pool.query<{ n: string }>(
      `SELECT relname AS n FROM pg_class WHERE relname LIKE 'ka_gochara_search_%' AND relkind = 'r' ORDER BY 1`)
    expect(t.rows.map(r => r.n)).toEqual([
      'ka_gochara_search_input_snapshot', 'ka_gochara_search_interval', 'ka_gochara_search_inventory',
      'ka_gochara_search_inventory_verification', 'ka_gochara_search_obligation', 'ka_gochara_search_path_pin'])
    const after = await defs()
    const changed = [...defsBefore].filter(([k, d]) => after.get(k) !== d).map(([k]) => k)
    expect(changed, 'pre-1206 functions/constraints/triggers whose definition changed').toEqual([])
    const seal = await pool.query<{ t: string }>(
      `SELECT tgname AS t FROM pg_trigger WHERE tgrelid = 'ka_gochara_generation_seal'::regclass AND NOT tgisinternal ORDER BY 1`)
    expect(seal.rows.map(r => r.t)).toEqual(
      expect.arrayContaining(['ka_gochara_generation_seal_write_guard', 'ka_gochara_generation_seal_z_search_complete']))
    // every new function pins search_path (Codex §4: not "some")
    const unpinned = await pool.query<{ n: string }>(
      `SELECT p.proname AS n FROM pg_proc p JOIN pg_namespace ns ON ns.oid = p.pronamespace
       WHERE ns.nspname='public' AND (p.proname LIKE 'ka_gochara_search_%' OR p.proname IN
         ('ka_gochara_sha256_hex','ka_gochara_uuidv8','ka_gochara_canonical_json','ka_gochara_utc_ts','ka_gochara_uuid_set_ok','ka_gochara_generation_seal_search_guard'))
         AND NOT EXISTS (SELECT 1 FROM unnest(coalesce(p.proconfig, ARRAY[]::text[])) c WHERE c LIKE 'search_path=%')`)
    expect(unpinned.rows.map(r => r.n)).toEqual([])
  })

  // ── 1. identity / digest vectors: SQL == TypeScript reference == the Python model ──
  it('AM-2/AM-5 helpers reproduce the pinned vectors byte-for-byte (SQL, TypeScript, Python model)', async () => {
    const vectors: Array<[string, string]> = [
      ['mars|conjunction|point:198.52|c0|1', '23276d7c-c127-8f4c-9ad5-6b7c8da8020f'],
      ['mars|conjunction|point:198.52|c0|2', 'b6cd1a15-4820-859f-b6e4-d7e144e59416'],
      ['mars|conjunction|point:198.52|c0|3', 'c523b443-fcc4-8665-8bfc-52b6e3e831d9'],
      ['mars|conjunction|point:198.52|c0|4', '8e423fdf-6ab5-842a-ab1f-b31d4720d319'],
      ['Mars|conjunction|point:198.52|c0|1', '87b023cc-c9f3-8979-9b37-96701f285356'],
      ['mars|conjunction|point:198.52|c1|1', 'eec1d008-2a69-8857-9164-786f5c8e96e8'],
    ]
    for (const [bytes, want] of vectors) {
      const r = await pool.query<{ u: string }>(`SELECT ka_gochara_uuidv8($1)::text AS u`, [bytes])
      expect(r.rows[0]!.u, bytes).toBe(want)
      expect(uuidv8(bytes), `TS ${bytes}`).toBe(want)
    }
    const cj = await pool.query<{ j: string }>(`SELECT ka_gochara_canonical_json($1::jsonb) AS j`,
      ['{"z":[3,{"b":1,"a":"é"}],"a":null,"m":true}'])
    expect(cj.rows[0]!.j).toBe(canonJson({ z: [3, { b: 1, a: 'é' }], a: null, m: true }))
    expect(canonJson(VEC)).toBe('{"bg_transit_av_gates":"d2","bg_transit_rules":"d1"}')
  })

  it('W1: the database reproduces the Python-model vectors (input 800d572c…, inventory fb278bb9…, input-bound ledgers bfab9224…/b43e3157…)', async () => {
    const synth = {
      conv: CONV, vec: VEC, l1: sha('l1-demo'), dasha: sha('dasha-demo'),
      av: ['1157:lahiri_av_v1:' + sha('decl-row').slice(0, 12)],
    }
    expect(inputDigest(synth)).toBe('800d572c7db35d0e05f2c41bec3c6c9420b72b42619aaa4602de9596c7a2a0da')
    const run = async (gen: string, rows: Array<[string, string]>): Promise<{ inv: string; led: string }> =>
      tx(async c => {
        await chartCtx(c)
        await publication(c, gen)
        const snap = await snapshotWith(c, gen, synth)
        await header(c, gen, snap.digest)
        const ids = [obId('p1', '1.0', P1A), obId('p1', '1.0', P1B)]
        await pin(c, gen, { path: 'p1', disp: 'included', ids })
        await pin(c, gen, { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [] })
        await pin(c, gen, { path: 'p1', ver: '1.1', disp: 'excluded', reason: 'not_applicable_to_class', basis: B_NA, ids: [] })
        const a = await ob(c, gen, 'p1', P1A); const b = await ob(c, gen, 'p1', P1B)
        await iv(c, gen, a, rows[0]![0], rows[0]![1], snap.digest)
        await iv(c, gen, b, rows[1]![0], rows[1]![1], snap.digest)
        return finalize(c, gen)
      })
    const h1 = await run(nextGen(), [[LO, MID], [MID, HI]])
    const h2 = await run(nextGen(), [[LO, HI], [LO, HI]])
    const input = inputDigest(synth)
    const ids = [obId('p1', '1.0', P1A), obId('p1', '1.0', P1B)]
    // the suite's registry carries an extra p1@1.1 version, so the DB digest is the TS reference over THAT pin set …
    const expectedInv = tsInventoryDigest(CONV, input, [
      { path: 'p1', disp: 'included', ids }, { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [] },
      { path: 'p1', ver: '1.1', disp: 'excluded', reason: 'not_applicable_to_class', basis: B_NA, ids: [] }],
      [obBytes('p1', '1.0', P1A), obBytes('p1', '1.0', P1B)])
    expect(h1.inv).toBe(expectedInv)
    expect(h2.inv).toBe(expectedInv)
    // … and the published two-pin W1 vector is reproduced by the same TS reference
    expect(tsInventoryDigest(CONV, input, [
      { path: 'p1', disp: 'included', ids }, { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [] }],
      [obBytes('p1', '1.0', P1A), obBytes('p1', '1.0', P1B)])).toBe('fb278bb92edce1505d649c6aabab96a01f65622fd00e6437a3a33c30836d07db')
    expect(h1.led).toBe('bfab922403c857b66ff2eef99f63a45b6882cba31f61f8e7d448c6099fee01ce')
    expect(h2.led).toBe('b43e3157f320d15b19074b21d35bdd0546cc4901087632eb313faed1421d82a6')
    expect(tsLedgerDigest([[ids[0]!, LO, MID, 'searched_complete'], [ids[1]!, MID, HI, 'searched_complete']], input)).toBe(h1.led)
    expect(tsLedgerDigest([[ids[0]!, LO, HI, 'searched_complete'], [ids[1]!, LO, HI, 'searched_complete']], input)).toBe(h2.led)
    expect(h1.led).not.toBe(h2.led)
  })

  it('an EMPTY ledger is input-bound: two snapshots with no intervals have different ledger digests (v1.0 follow-up)', async () => {
    const empty = async (gen: string, l1: string): Promise<{ inv: string; led: string; input: string }> => tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotWith(c, gen, { conv: CONV, vec: VEC, l1, dasha: sha('d'), av: [] })
      await header(c, gen, snap.digest)
      await pin(c, gen, { path: 'p1', disp: 'computed_empty', basis: B_EMPTY, ids: [] })
      return { ...(await finalize(c, gen)), input: snap.digest }
    })
    const a = await empty(nextGen(), sha('l1-a')); const b = await empty(nextGen(), sha('l1-b'))
    expect(a.led).not.toBe(b.led)
    expect(a.led).toBe(tsLedgerDigest([], a.input))
    expect(a.inv).not.toBe(b.inv)
  })

  // ── R4: live-input digests are session-independent and ignore ONLY the audit column ──
  it('R4: the L1/dasha digests do not depend on the session timezone or float output settings, ignore audit-only changes, and see material ones', async () => {
    const digestIn = async (tz: string, extra?: string): Promise<[string, string]> => tx(async c => {
      if (extra) await c.query(extra)
      const l1 = (await c.query<{ v: string }>(`SELECT ka_gochara_search_l1_facts_digest($1,$2::text[]) AS v`, [CHART, ['F1', 'F2']])).rows[0]!.v
      const d = (await c.query<{ v: string }>(`SELECT ka_gochara_search_dasha_digest($1,$2::uuid[]) AS v`, [CHART, DASHA_IDS])).rows[0]!.v
      return [l1, d]
    }, { tz })
    const utc = await digestIn('UTC')
    expect(await digestIn('Asia/Kolkata')).toEqual(utc)
    expect(await digestIn('America/New_York')).toEqual(utc)
    expect(await digestIn('Pacific/Kiritimati', 'SET LOCAL extra_float_digits = -3')).toEqual(utc)
    const baseline = utc
    const change = async (sqlText: string, args: unknown[], undo: string, undoArgs: unknown[]): Promise<[string, string]> => {
      await pool.query(sqlText, args)
      try { return await digestIn('UTC') } finally { await pool.query(undo, undoArgs) }
    }
    // audit-only change: computed_at — NO change
    expect(await change(`UPDATE chart_facts SET computed_at = computed_at + interval '3 days' WHERE fact_id='F1'`, [], `UPDATE chart_facts SET computed_at = computed_at - interval '3 days' WHERE fact_id='F1'`, [])).toEqual(baseline)
    expect(await change(`UPDATE chart_dashas SET computed_at = computed_at + interval '3 days' WHERE dasha_row_id=$1`, [DASHA_IDS[0]], `UPDATE chart_dashas SET computed_at = computed_at - interval '3 days' WHERE dasha_row_id=$1`, [DASHA_IDS[0]])).toEqual(baseline)
    // material changes — each one changes the digest it feeds
    const m1 = await change(`UPDATE chart_facts SET fact_value_num = 8.48 WHERE fact_id='F1'`, [], `UPDATE chart_facts SET fact_value_num = 8.47 WHERE fact_id='F1'`, [])
    expect(m1[0]).not.toBe(baseline[0]); expect(m1[1]).toBe(baseline[1])
    const m2 = await change(`UPDATE chart_facts SET tolerance_arcsec = 0.1000001 WHERE fact_id='F1'`, [], `UPDATE chart_facts SET tolerance_arcsec = 0.1 WHERE fact_id='F1'`, [])
    expect(m2[0]).not.toBe(baseline[0])
    const m3 = await change(`UPDATE chart_dashas SET start_iso = start_iso + interval '1 second' WHERE dasha_row_id=$1`, [DASHA_IDS[0]], `UPDATE chart_dashas SET start_iso = start_iso - interval '1 second' WHERE dasha_row_id=$1`, [DASHA_IDS[0]])
    expect(m3[1]).not.toBe(baseline[1]); expect(m3[0]).toBe(baseline[0])
    const m4 = await change(`UPDATE chart_dashas SET next_dasha_start_iso = NULL WHERE dasha_row_id=$1`, [DASHA_IDS[0]], `UPDATE chart_dashas SET next_dasha_start_iso = '2027-08-18T21:50:23Z' WHERE dasha_row_id=$1`, [DASHA_IDS[0]])
    expect(m4[1]).not.toBe(baseline[1])
    expect(await digestIn('UTC')).toEqual(baseline)
  })

  it('R4: a snapshot built under one session timezone seals under another (no false input_snapshot_drift)', async () => {
    const gen = nextGen()
    await goodBuild(gen, { tz: 'Asia/Kolkata' })
    await publishAndSeal(gen, { tz: 'America/New_York' })
    const s = await pool.query(`SELECT 1 FROM ka_gochara_generation_seal WHERE chart_id=$1 AND generation=$2`, [CHART, gen])
    expect(s.rows).toHaveLength(1)
  })

  // ── the good build under the REAL builder / sealer principals ─────────────────
  it('R5 principals: the builder constructs and finalises the inventory under its REAL grants but CANNOT seal; a separate seal principal can', async () => {
    const gen = nextGen()
    await goodBuild(gen, { role: BUILDER })
    // Two independent walls: the builder holds no EXECUTE on the seal function, and no write on the seal table.
    await refused(publishAndSeal(gen, { role: BUILDER }), /permission denied for function ka_gochara_seal_generation/)
    await refused(tx(async c => {
      await c.query(`INSERT INTO ka_gochara_generation_seal (chart_id, generation, manifest_id) VALUES ($1, $2, gen_random_uuid())`, [CHART, gen])
    }, { role: BUILDER }), /permission denied for table ka_gochara_generation_seal/)
    await refused(tx(async c => { await c.query('CREATE TABLE public.x_builder_probe (a int)') }, { role: BUILDER }), /permission denied for schema public/)
    await refused(tx(async c => { await c.query('TRUNCATE ka_gochara_search_interval') }, { role: BUILDER }), /permission denied/)
    await publishAndSeal(gen, { role: SEALER })
    const s = await pool.query(`SELECT 1 FROM ka_gochara_generation_seal WHERE chart_id=$1 AND generation=$2`, [CHART, gen])
    expect(s.rows).toHaveLength(1)
  })

  // ── adversaries ──────────────────────────────────────────────────────────────
  it('C1 Codex W2, exactly as written, is REFUSED: P5a pinned included, obligations never inserted, everything stored covered, verifier merely re-hashes', async () => {
    const gen = nextGen()
    await goodBuild(gen, { skipP5aObligations: true })
    await refused(publishAndSeal(gen), /committed_set_mismatch[\s\S]*p5a@1\.0 committed-not-stored=/)
    const v = await pool.query<{ violation: string; detail: string }>(
      `SELECT violation, detail FROM ka_gochara_search_completeness_violations($1,$2)`, [CHART, gen])
    const m = v.rows.find(r => r.violation === 'committed_set_mismatch')!
    expect(m.detail).toContain(obId('p5a', '1.0', P5A))
    expect(m.detail).toContain(obId('p5a', '1.0', P5B))
  })

  it('R1 cross-path borrowing: P5a commits P1\'s obligation ids, stores none, and P1\'s obligations must NOT satisfy it', async () => {
    const gen = nextGen()
    const p1 = [obId('p1', '1.0', P1A), obId('p1', '1.0', P1B)]
    await tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      await pin(c, gen, { path: 'p1', disp: 'included', ids: p1 })
      await pin(c, gen, { path: 'p5a', disp: 'included', ids: p1 })                  // BORROWED commitment
      await pinRest(c, gen, [['p1', '1.0'], ['p5a', '1.0']])
      for (const o of [P1A, P1B]) { const id = await ob(c, gen, 'p1', o); await iv(c, gen, id, LO, HI, snap.digest) }
      const d = await finalize(c, gen); await partition(c, gen); await verify(c, gen, d.inv)   // verifier re-hashes the adversarial rows
    })
    await refused(publishAndSeal(gen), /committed_set_mismatch[\s\S]*p5a@1\.0 committed-not-stored=[^\n]*\(stored-under-p1@1\.0\)/)
    const v = await pool.query<{ detail: string }>(
      `SELECT detail FROM ka_gochara_search_completeness_violations($1,$2) WHERE violation='committed_set_mismatch'`, [CHART, gen])
    expect(v.rows).toHaveLength(1)
    expect(v.rows[0]!.detail.startsWith('p5a@1.0')).toBe(true)
  })

  it('R1 cross-version borrowing: p1@1.1 commits p1@1.0\'s ids and stores nothing', async () => {
    const gen = nextGen()
    const p1 = [obId('p1', '1.0', P1A), obId('p1', '1.0', P1B)]
    await tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      await pin(c, gen, { path: 'p1', ver: '1.0', disp: 'included', ids: p1 })
      await pin(c, gen, { path: 'p1', ver: '1.1', disp: 'included', ids: p1 })       // other VERSION, same ids
      await pinRest(c, gen, [['p1', '1.0'], ['p1', '1.1']])
      for (const o of [P1A, P1B]) { const id = await ob(c, gen, 'p1', o); await iv(c, gen, id, LO, HI, snap.digest) }
      const d = await finalize(c, gen); await partition(c, gen); await verify(c, gen, d.inv)
    })
    await refused(publishAndSeal(gen), /committed_set_mismatch[\s\S]*p1@1\.1 committed-not-stored=[^\n]*\(stored-under-p1@1\.0\)/)
  })

  it('C1b: an included pin with an empty commitment is refused at insert (kgspp_included_nonempty_ck)', async () => {
    const gen = nextGen()
    await refused(tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      await pin(c, gen, { path: 'p5a', disp: 'included', ids: [] })
    }), /kgspp_included_nonempty_ck/)
  })

  it('C2: a sealed registry version with no pin at all → registry_unaccounted_path (a second VERSION of a pinned path counts)', async () => {
    const gen = nextGen()
    await tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      await pin(c, gen, { path: 'p1', disp: 'included', ids: [obId('p1', '1.0', P1A)] })
      await pin(c, gen, { path: 'p5a', disp: 'excluded', reason: 'not_applicable_to_class', basis: B_NA, ids: [] })
      await pin(c, gen, { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [] })   // p1@1.1 never pinned
      const id = await ob(c, gen, 'p1', P1A); await iv(c, gen, id, LO, HI, snap.digest)
      const d = await finalize(c, gen); await partition(c, gen); await verify(c, gen, d.inv)
    })
    await refused(publishAndSeal(gen), /registry_unaccounted_path[\s\S]*p1@1\.1/)
  })

  it('C3 / C3c: a false computed_empty, or a smaller committed set, with a verifier that derives the TRUE inventory → verification_missing_or_mismatch', async () => {
    const truth = await goodBuild(nextGen())
    const g1 = nextGen()
    await goodBuild(g1, { p5a: 'computed_empty', verifyDigest: truth.dig.inv })
    await refused(publishAndSeal(g1), /verification_missing_or_mismatch/)
    const g2 = nextGen()
    await tx(async c => {
      await chartCtx(c); await publication(c, g2)
      const snap = await snapshotLive(c, g2); await header(c, g2, snap.digest)
      await pin(c, g2, { path: 'p1', disp: 'included', ids: [obId('p1', '1.0', P1A)] })
      await pin(c, g2, { path: 'p5a', disp: 'included', ids: truth.ids.p5a })
      await pinRest(c, g2, [['p1', '1.0'], ['p5a', '1.0']])
      const a = await ob(c, g2, 'p1', P1A); const x = await ob(c, g2, 'p5a', P5A); const y = await ob(c, g2, 'p5a', P5B)
      for (const id of [a, x, y]) await iv(c, g2, id, LO, HI, snap.digest)
      await finalize(c, g2); await partition(c, g2); await verify(c, g2, truth.dig.inv)
    })
    await refused(publishAndSeal(g2), /verification_missing_or_mismatch/)
  })

  it('C3b: no verification row → refused; v1.1: ONE stale disagreeing verification row vetoes the seal until it is deleted; C5 genuine computed_empty seals', async () => {
    const g1 = nextGen()
    await goodBuild(g1, { p5a: 'computed_empty', noVerify: true })
    await refused(publishAndSeal(g1), /verification_missing_or_mismatch/)
    const g3 = nextGen()
    const b = await goodBuild(g3)
    await tx(async c => { await chartCtx(c); await verify(c, g3, sha('stale-negative'), 'verifier-b') })
    await refused(publishAndSeal(g3), /verification_missing_or_mismatch/)         // every row must equal (stricter than 'at least one')
    await tx(async c => { await chartCtx(c); await c.query(`DELETE FROM ka_gochara_search_inventory_verification WHERE chart_id=$1 AND generation=$2 AND verifier_id='verifier-b'`, [CHART, g3]) })
    await publishAndSeal(g3)
    expect(b.dig.inv).toMatch(/^[0-9a-f]{64}$/)
    const g2 = nextGen()
    await goodBuild(g2, { p5a: 'computed_empty' })
    await publishAndSeal(g2)
  })

  it('C4: an obligation with NO ledger rows → obligation_uncovered; a half-covered one too (W1 H1)', async () => {
    const g1 = nextGen()
    await tx(async c => {
      await chartCtx(c); await publication(c, g1)
      const snap = await snapshotLive(c, g1); await header(c, g1, snap.digest)
      await pin(c, g1, { path: 'p1', disp: 'included', ids: [obId('p1', '1.0', P1A), obId('p1', '1.0', P1B)] })
      await pinRest(c, g1, [['p1', '1.0']])
      const a = await ob(c, g1, 'p1', P1A); await ob(c, g1, 'p1', P1B)
      await iv(c, g1, a, LO, MID, snap.digest)
      const d = await finalize(c, g1); await partition(c, g1); await verify(c, g1, d.inv)
    })
    await refused(publishAndSeal(g1), /obligation_uncovered/)
    const v = await pool.query<{ detail: string }>(
      `SELECT detail FROM ka_gochara_search_completeness_violations($1,$2) WHERE violation='obligation_uncovered' ORDER BY detail`, [CHART, g1])
    expect(v.rows).toHaveLength(2)
    expect(v.rows.some(r => r.detail.includes(obId('p1', '1.0', P1B)))).toBe(true)
    expect(v.rows.some(r => r.detail.includes(obId('p1', '1.0', P1A)) && r.detail.includes('2025-02-01'))).toBe(true)
  })

  it('C7: an obligation outside its pin\'s committed set, a wrong ob_id, or non-canonical bytes is refused at insert', async () => {
    const gen = nextGen()
    const stage = async (c: PoolClient, ids: string[]): Promise<void> => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      await pin(c, gen, { path: 'p5a', disp: 'included', ids })
    }
    await refused(tx(async c => { await stage(c, [obId('p5a', '1.0', P5A)]); await ob(c, gen, 'p5a', P5B) }), /not in the pin's committed obligation set/)
    await refused(tx(async c => {
      await stage(c, [obId('p5a', '1.0', P5A)])
      await c.query(`INSERT INTO ka_gochara_search_obligation
        (chart_id, generation, event_class, ob_id, path_id, rule_version, agent, relation, object_role, target, frame, person, canonical_bytes)
        VALUES ($1,$2,$3,gen_random_uuid(),'p5a','1.0',$4,$5,$6,$7,$8,$9,$10)`, [CHART, gen, CLS, ...P5A, obBytes('p5a', '1.0', P5A)])
    }), /is not the UUIDv8 of its canonical bytes|committed obligation set/)
    const upper = 'marriage|p5a|1.0|SATURN|residence|av_qualifier|house_span:7|lagna|self'
    await refused(tx(async c => {
      await stage(c, [uuidv8(upper)])
      await c.query(`INSERT INTO ka_gochara_search_obligation
        (chart_id, generation, event_class, ob_id, path_id, rule_version, agent, relation, object_role, target, frame, person, canonical_bytes)
        VALUES ($1,$2,$3,$4,'p5a','1.0','SATURN','residence','av_qualifier','house_span:7','lagna','self',$5)`,
        [CHART, gen, CLS, uuidv8(upper), upper])
    }), /kgso_bytes_shape_ck/)
  })

  // ── R2: the snapshot convention is bound to the publication AND coverage conventions ──
  it('R2: an incompatible or missing bridge is refused at the snapshot, and at the seal for the partition — with no records or windows', async () => {
    const mkPub = (legacy: string) => async (c: PoolClient, gen: string): Promise<void> => { await chartCtx(c); await publication(c, gen, VEC, legacy) }
    const g1 = nextGen()
    await refused(tx(async c => { await mkPub(LEGACY_OTHER)(c, g1); await snapshotLive(c, g1, VEC, CONV) }), /R2[\s\S]*is not the one the publication's legacy convention legacy:c1 is bridged to/)
    const g2 = nextGen()
    await refused(tx(async c => { await mkPub(LEGACY_NOBRIDGE)(c, g2); await snapshotLive(c, g2, VEC, CONV) }), /R2[\s\S]*has no ka_gochara_convention_bridge row/)
    const g3 = nextGen()
    await tx(async c => {
      await chartCtx(c); await publication(c, g3)
      const snap = await snapshotLive(c, g3); await header(c, g3, snap.digest)
      await pin(c, g3, { path: 'p1', disp: 'included', ids: [obId('p1', '1.0', P1A)] })
      await pinRest(c, g3, [['p1', '1.0']])
      const id = await ob(c, g3, 'p1', P1A); await iv(c, g3, id, LO, HI, snap.digest)
      const d = await finalize(c, g3); await partition(c, g3, { legacy: LEGACY_OTHER }); await verify(c, g3, d.inv)
    })
    await refused(publishAndSeal(g3), /convention_mismatch[\s\S]*partition legacy convention legacy:c1 is bridged to sha256:b+ but the snapshot is bound to sha256:eac922d4/)
    const g4 = nextGen()
    await tx(async c => {
      await chartCtx(c); await publication(c, g4)
      const snap = await snapshotLive(c, g4); await header(c, g4, snap.digest)
      await pin(c, g4, { path: 'p1', disp: 'included', ids: [obId('p1', '1.0', P1A)] })
      await pinRest(c, g4, [['p1', '1.0']])
      const id = await ob(c, g4, 'p1', P1A); await iv(c, g4, id, LO, HI, snap.digest)
      const d = await finalize(c, g4); await partition(c, g4, { legacy: LEGACY_NOBRIDGE }); await verify(c, g4, d.inv)
    })
    await refused(publishAndSeal(g4), /convention_bridge_missing[\s\S]*partition legacy convention legacy:c2/)
    const recs = await pool.query(`SELECT (SELECT count(*) FROM ka_gochara_relationship_record) + (SELECT count(*) FROM ka_gochara_eval_window) AS n`)
    expect(Number(recs.rows[0]!.n)).toBe(0)           // the existing consumer guards had nothing to inspect — only 1206 stops it
    const g5 = nextGen(); await goodBuild(g5); await publishAndSeal(g5)
  })

  // ── R3: excluded pins need a non-NULL reason; total booleans ──────────────────
  it('F-3 version scope: superseded_by_version lets an older version yield to the included one; two included versions of one path and a supersession with no included superseder are refused at the seal', async () => {
    // the build skeleton: header + the caller's pins + obligations/intervals for the included ones
    const scoped = (gen: string, pins: PinRef[], covered: Array<{ ver: string; o: Ob }>) => tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      for (const pn of pins) await pin(c, gen, pn)
      for (const { ver, o } of covered) { const id = await ob(c, gen, 'p1', o, CLS, ver); await iv(c, gen, id, LO, HI, snap.digest) }
      const d = await finalize(c, gen); await partition(c, gen); await verify(c, gen, d.inv)
    })
    const rest = (handled: Array<[string, string]>): PinRef[] => REGISTRY
      .filter(([pa, ve]) => !handled.some(([hp, hv]) => hp === pa && hv === ve))
      .map(([pa, ve]) => pa === 'p6'
        ? { path: pa, ver: ve, disp: 'excluded' as const, reason: 'on_demand_tier', basis: B_P6, ids: [] }
        : { path: pa, ver: ve, disp: 'excluded' as const, reason: 'not_applicable_to_class', basis: B_NA, ids: [] })
    // (1) p1@1.1 included, p1@1.0 superseded_by_version (NON-degrading: no ruling_ref) → seals
    const ok = nextGen()
    await scoped(ok, [
      { path: 'p1', ver: '1.1', disp: 'included', ids: [obId('p1', '1.1', P1A)] },
      { path: 'p1', ver: '1.0', disp: 'excluded', reason: 'superseded_by_version', basis: B_NA, ids: [] },
      ...rest([['p1', '1.0'], ['p1', '1.1']])], [{ ver: '1.1', o: P1A }])
    await publishAndSeal(ok)
    // (2) two included versions of ONE path in one class → multiple_included_versions (names the path and both versions)
    const two = nextGen()
    await scoped(two, [
      { path: 'p1', ver: '1.0', disp: 'included', ids: [obId('p1', '1.0', P1A)] },
      { path: 'p1', ver: '1.1', disp: 'included', ids: [obId('p1', '1.1', P1A)] },
      ...rest([['p1', '1.0'], ['p1', '1.1']])], [{ ver: '1.0', o: P1A }, { ver: '1.1', o: P1A }])
    await refused(publishAndSeal(two), /multiple_included_versions[\s\S]*p1@1\.0,1\.1/)
    // (3) a supersession claim whose superseder is not included → superseded_without_included_version
    const hole = nextGen()
    await scoped(hole, [
      { path: 'p1', ver: '1.0', disp: 'excluded', reason: 'superseded_by_version', basis: B_NA, ids: [] },
      { path: 'p1', ver: '1.1', disp: 'excluded', reason: 'not_applicable_to_class', basis: B_NA, ids: [] },
      ...rest([['p1', '1.0'], ['p1', '1.1']])], [])
    await refused(publishAndSeal(hole), /superseded_without_included_version[\s\S]*p1@1\.0/)
    // (4) superseded_by_version is non-degrading: a ruling_ref on it is refused by the pin CHECK, and it needs a basis
    const bad = (ruling: string | null, basis: string | null) => tx(async c => {
      const g = nextGen()
      await chartCtx(c); await publication(c, g)
      const snap = await snapshotLive(c, g); await header(c, g, snap.digest)
      await c.query(`INSERT INTO ka_gochara_search_path_pin
        (chart_id, generation, event_class, path_id, rule_version, disposition, exclusion_reason, ruling_ref, basis, committed_ob_ids)
        VALUES ($1,$2,$3,'p1','1.0','excluded','superseded_by_version',$4,$5,'{}')`, [CHART, g, CLS, ruling, basis])
    })
    await refused(bad('R-9', B_NA), /kgspp_ruling_iff_degrading_ck/)
    await refused(bad(null, null), /kgspp_basis_required_ck/)
  })

  it('R6: with PUBLIC execute revoked (deployment mirror) the builder holds EXECUTE on exactly the 12 own helpers + 5 contract functions, and nothing seal-side', async () => {
    const r = await pool.query<{ sig: string; owner: string; builder: boolean; pub: boolean }>(
      `SELECT p.oid::regprocedure::text AS sig, pg_get_userbyid(p.proowner) AS owner,
              has_function_privilege('${BUILDER}', p.oid, 'EXECUTE') AS builder, has_function_privilege('public', p.oid, 'EXECUTE') AS pub
         FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public' AND p.proname LIKE 'ka\\_gochara\\_%'`)
    expect(r.rows.filter(x => x.owner !== OWNER)).toEqual([])      // control: the mirror is faithful
    expect(r.rows.filter(x => x.pub)).toEqual([])                  // control: PUBLIC executes none
    const got = r.rows.filter(x => x.builder).map(x => x.sig).sort()
    // expected signatures normalised through the catalog itself (regprocedure spelling), not by string-munging
    const want = (await Promise.all([...BUILDER_OWN_FUNCTIONS, ...BUILDER_CONTRACT_FUNCTIONS].map(async sg => {
      const q = await pool.query<{ t: string | null }>(`SELECT to_regprocedure($1)::text AS t`, [`public.${sg}`])
      expect(q.rows[0]!.t, sg).not.toBeNull()
      return q.rows[0]!.t!
    }))).sort()
    expect(got).toEqual(want)
    for (const name of ['ka_gochara_seal_generation', 'ka_gochara_search_completeness_violations', 'ka_gochara_search_replay_violations',
      'ka_gochara_search_inventories_digest', 'ka_gochara_search_write_guard', 'ka_gochara_generation_seal_search_guard'])
      expect(r.rows.filter(x => x.sig.startsWith(name + '(') || x.sig.startsWith('public.' + name + '(')).every(x => !x.builder), name).toBe(true)
  })

  it('R6: each of the 17 builder EXECUTE grants is necessary — revoking any one breaks construct-and-finalise, naming that function', async () => {
    for (const sig of [...BUILDER_OWN_FUNCTIONS, ...BUILDER_CONTRACT_FUNCTIONS]) {
      const name = sig.slice(0, sig.indexOf('('))
      await asOwner(c => c.query(`REVOKE EXECUTE ON FUNCTION public.${sig} FROM ${BUILDER}`))
      try {
        await refused(goodBuild(nextGen(), { role: BUILDER }), new RegExp(`permission denied for function ${name}\\b`))
      } finally {
        await asOwner(c => c.query(`GRANT EXECUTE ON FUNCTION public.${sig} TO ${BUILDER}`))
      }
    }
    await goodBuild(nextGen(), { role: BUILDER })   // restored: the builder works again
  })

  it('R3: an excluded pin with a NULL reason is refused in BOTH variants (with and without a ruling_ref); other dispositions carry no reason', async () => {
    const raw = (gen: string, disp: string, reason: string | null, ruling: string | null) => tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      await c.query(`INSERT INTO ka_gochara_search_path_pin
        (chart_id, generation, event_class, path_id, rule_version, disposition, exclusion_reason, ruling_ref, basis, committed_ob_ids)
        VALUES ($1,$2,$3,'p6','1.0',$4,$5,$6,$7,'{}')`, [CHART, gen, CLS, disp, reason, ruling, B_P6])
    })
    await refused(raw(nextGen(), 'excluded', null, null), /kgspp_reason_closed_ck/)
    await refused(raw(nextGen(), 'excluded', null, 'R-9'), /kgspp_reason_closed_ck|kgspp_ruling_iff_degrading_ck/)
    await refused(raw(nextGen(), 'computed_empty', 'on_demand_tier', null), /kgspp_reason_closed_ck|kgspp_computed_empty_bare_ck/)
    await refused(raw(nextGen(), 'excluded', 'made_up_reason', null), /kgspp_reason_closed_ck/)
    await refused(raw(nextGen(), 'excluded', 'disabled_form', null), /kgspp_ruling_iff_degrading_ck/)
    await refused(raw(nextGen(), 'excluded', 'on_demand_tier', 'R-9'), /kgspp_ruling_iff_degrading_ck/)
  })

  // ── 3. search-input binding ──────────────────────────────────────────────────
  it('C8: an interval stamped with another input_digest, a second snapshot for one generation, and a snapshot whose vector differs from the manifest are all refused', async () => {
    const gen = nextGen()
    await refused(tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      await pin(c, gen, { path: 'p1', disp: 'included', ids: [obId('p1', '1.0', P1A)] })
      const a = await ob(c, gen, 'p1', P1A)
      await iv(c, gen, a, LO, MID, sha('another-snapshot'))
    }), /kgsiv_input_fk/)
    await refused(tx(async c => {
      await chartCtx(c); await publication(c, gen)
      await snapshotLive(c, gen)
      await snapshotWith(c, gen, { conv: CONV, vec: VEC, l1: sha('other'), dasha: sha('x'), av: [] })
    }), /ka_gochara_search_input_snapshot_pkey|duplicate key/)
    await refused(tx(async c => {
      await chartCtx(c); await publication(c, gen)
      await snapshotWith(c, gen, { conv: CONV, vec: { bg_transit_rules: 'DIFFERENT' }, l1: sha('a'), dasha: sha('b'), av: [] })
    }), /differs from the manifest/)
    await refused(tx(async c => {
      await chartCtx(c); await publication(c, gen)
      await c.query(`INSERT INTO ka_gochara_search_input_snapshot
        (chart_id, generation, convention_id, input_generation_vector, consumed_fact_ids, consumed_dasha_row_ids, av_declarations, l1_facts_digest, dasha_digest, input_digest)
        VALUES ($1,$2,$3,$4::jsonb,'{}','{}','{}',$5,$5,$5)`, [CHART, gen, CONV, JSON.stringify(VEC), sha('z')])
    }), /does not recompute from its components/)
  })

  it('C9: L1 rewritten after the search → input_snapshot_drift; manifest vector changed → input_vector_mismatch; both refuse the seal, and restoring lets it seal', async () => {
    const gen = nextGen()
    await goodBuild(gen)
    await pool.query(`UPDATE chart_facts SET fact_value_text = 'tampered' WHERE fact_id = 'F1'`)
    await refused(publishAndSeal(gen), /input_snapshot_drift/)
    await pool.query(`UPDATE chart_facts SET fact_value_text = 'a' WHERE fact_id = 'F1'`)
    await pool.query(`UPDATE chart_dashas SET start_iso = '2010-08-18T16:00:00Z' WHERE dasha_row_id = $1`, [DASHA_IDS[0]])
    await refused(publishAndSeal(gen), /input_snapshot_drift/)
    await pool.query(`UPDATE chart_dashas SET start_iso = '2010-08-18T15:50:23Z' WHERE dasha_row_id = $1`, [DASHA_IDS[0]])
    await pool.query(`UPDATE kala_gochara_publication SET input_generation_vector = '{"bg_transit_rules":"d9"}'::jsonb WHERE chart_id=$1 AND generation=$2`, [CHART, gen])
    await refused(publishAndSeal(gen), /input_vector_mismatch/)
    await pool.query(`UPDATE kala_gochara_publication SET input_generation_vector = $3::jsonb WHERE chart_id=$1 AND generation=$2`, [CHART, gen, JSON.stringify(VEC)])
    await publishAndSeal(gen)
  })

  it('C15: the same targets, paths and convention under a different L1 snapshot yield a different input digest, inventory digest and ledger digest', async () => {
    const a = await goodBuild(nextGen())
    await pool.query(`UPDATE chart_facts SET fact_value_text = 'rebuilt' WHERE fact_id = 'F2'`)
    const b = await goodBuild(nextGen())
    await pool.query(`UPDATE chart_facts SET fact_value_text = 'b' WHERE fact_id = 'F2'`)
    expect(b.snap.digest).not.toBe(a.snap.digest)
    expect(b.dig.inv).not.toBe(a.dig.inv)
    expect(b.dig.led).not.toBe(a.dig.led)
    expect(b.ids.p1).toEqual(a.ids.p1)
  })

  // ── 4. interval + finalisation guards ────────────────────────────────────────
  it('C11/C12: overlapping, out-of-horizon, sub-second and non-half-open intervals are refused', async () => {
    const gen = nextGen()
    const stage = async (c: PoolClient): Promise<{ id: string; input: string }> => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      await pin(c, gen, { path: 'p1', disp: 'included', ids: [obId('p1', '1.0', P1A)] })
      return { id: await ob(c, gen, 'p1', P1A), input: snap.digest }
    }
    await refused(tx(async c => { const s = await stage(c); await iv(c, gen, s.id, LO, MID, s.input); await iv(c, gen, s.id, '2025-01-15T00:00:00Z', HI, s.input, 'searched_unqualified') }), /overlaps an existing interval/)
    await refused(tx(async c => { const s = await stage(c); await iv(c, gen, s.id, HI, '2025-03-02T00:00:00Z', s.input) }), /outside the inventory horizon/)
    await refused(tx(async c => { const s = await stage(c); await iv(c, gen, s.id, '2024-12-31T00:00:00Z', MID, s.input) }), /outside the inventory horizon/)
    await refused(tx(async c => { const s = await stage(c); await iv(c, gen, s.id, '2025-01-01T00:00:00.5Z', MID, s.input) }), /kgsiv_range_ck/)
    await refused(tx(async c => {
      const s = await stage(c)
      await c.query(`INSERT INTO ka_gochara_search_interval (chart_id, generation, event_class, ob_id, search_range, state, input_digest)
        VALUES ($1,$2,$3,$4,tstzrange('${LO}','${MID}','(]'),'searched_complete',$5)`, [CHART, gen, CLS, s.id, s.input])
    }), /kgsiv_range_ck/)
    await tx(async c => { const s = await stage(c); await iv(c, gen, s.id, LO, MID, s.input); await iv(c, gen, s.id, MID, HI, s.input) })
  })

  it('finalisation: each digest is checked on its own; a finalised class is immutable; verification needs a finalised class; replacement works in dependency order', async () => {
    const gen = nextGen()
    await refused(tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      await verify(c, gen, sha('x'))
    }), /not FINALISED/)
    for (const wrong of ['inventory', 'ledger'] as const) {
      await refused(tx(async c => {
        await chartCtx(c); await publication(c, gen)
        const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
        await pin(c, gen, { path: 'p1', disp: 'included', ids: [obId('p1', '1.0', P1A)] })
        const d = (await c.query<{ inv: string; led: string }>(
          `SELECT ka_gochara_search_inventory_digest($1,$2,$3) AS inv, ka_gochara_search_ledger_digest($1,$2,$3) AS led`, [CHART, gen, CLS])).rows[0]!
        await c.query(`UPDATE ka_gochara_search_inventory SET inventory_digest=$4, ledger_digest=$5 WHERE chart_id=$1 AND generation=$2 AND event_class=$3`,
          [CHART, gen, CLS, wrong === 'inventory' ? sha('wrong') : d.inv, wrong === 'ledger' ? sha('wrong') : d.led])
      }), /do not equal the recomputation/)
    }
    const g2 = nextGen()
    await goodBuild(g2)
    await refused(tx(async c => { await chartCtx(c); await pin(c, g2, { path: 'p5a', ver: '9.9', disp: 'excluded', reason: 'not_applicable_to_class', basis: B_P6, ids: [] }) }), /FINALISED/)
    await refused(tx(async c => {
      await chartCtx(c)
      await c.query(`UPDATE ka_gochara_search_inventory SET inventory_digest=$3 WHERE chart_id=$1 AND generation=$2`, [CHART, g2, sha('again')])
    }), /already FINALISED/)
    await refused(tx(async c => { await chartCtx(c); await c.query(`DELETE FROM ka_gochara_search_inventory WHERE chart_id=$1 AND generation=$2`, [CHART, g2]) }), /foreign key|violates/)
    await tx(async c => {
      await chartCtx(c)
      for (const t of ['ka_gochara_search_inventory_verification', 'ka_gochara_search_interval', 'ka_gochara_search_obligation',
                       'ka_gochara_search_path_pin', 'ka_gochara_search_inventory', 'ka_gochara_search_input_snapshot'])
        await c.query(`DELETE FROM ${t} WHERE chart_id=$1 AND generation=$2`, [CHART, g2])
      await c.query(`DELETE FROM kala_gochara_coverage WHERE chart_id=$1 AND generation=$2`, [CHART, g2])
      const s = await snapshotLive(c, g2); await header(c, g2, s.digest)
    })
  })

  it('C14 / partition / manifest / class census: missing_inputs, an over-claiming partition, a horizon that is not the manifest\'s, a class without inventory and an inventory without partition refuse the seal', async () => {
    const g1 = nextGen()
    await tx(async c => {
      await chartCtx(c); await publication(c, g1)
      const snap = await snapshotLive(c, g1); await header(c, g1, snap.digest)
      await pin(c, g1, { path: 'p1', disp: 'included', ids: [obId('p1', '1.0', P1A)] })
      await pin(c, g1, { path: 'p5a', disp: 'excluded', reason: 'inputs_unavailable', ruling: 'R-9', basis: 'ruling:R-9', ids: [] })
      await pinRest(c, g1, [['p1', '1.0'], ['p5a', '1.0']])
      const a = await ob(c, g1, 'p1', P1A)
      await iv(c, g1, a, LO, HI, snap.digest, 'missing_inputs')
      const d = await finalize(c, g1); await partition(c, g1); await verify(c, g1, d.inv)
    })
    await refused(publishAndSeal(g1), /missing_inputs_present/)
    const g2 = nextGen()
    await goodBuild(g2, { partitionRelations: ['residence', 'aspect'] })
    await refused(publishAndSeal(g2), /partition_overclaims/)
    const g3 = nextGen()
    await tx(async c => {
      await chartCtx(c); await publication(c, g3)
      const snap = await snapshotLive(c, g3)
      await c.query(`UPDATE kala_gochara_publication SET horizon = tstzrange('${LO}','2025-04-01T00:00:00Z','[)') WHERE chart_id=$1 AND generation=$2`, [CHART, g3])
      await header(c, g3, snap.digest)
      await pin(c, g3, { path: 'p1', disp: 'included', ids: [obId('p1', '1.0', P1A)] })
      await pinRest(c, g3, [['p1', '1.0']])
      const a = await ob(c, g3, 'p1', P1A); await iv(c, g3, a, LO, HI, snap.digest)
      const d = await finalize(c, g3); await partition(c, g3); await verify(c, g3, d.inv)
    })
    await refused(publishAndSeal(g3), /horizon_manifest_mismatch/)
    const g4 = nextGen()
    await goodBuild(g4, { noPartition: true })
    await refused(publishAndSeal(g4), /inventory_without_partition/)
    const g5 = nextGen()
    await goodBuild(g5)
    await tx(async c => { await chartCtx(c); await partition(c, g5, { cls: 'career_change' }) })
    await refused(publishAndSeal(g5), /partition_without_inventory/)
    // a class absent from BOTH coverage and inventory is NOT a violation: the generation simply does not claim it —
    // serving must report it `not_searched` (a seal is not proof that every possible class was searched)
    const g6 = nextGen(); await goodBuild(g6); await publishAndSeal(g6)
    const claimed = await pool.query<{ event_class: string }>(`SELECT event_class FROM ka_gochara_search_inventory WHERE chart_id=$1 AND generation=$2`, [CHART, g6])
    expect(claimed.rows.map(r => r.event_class)).toEqual([CLS])
  })

  // ── F-2 ───────────────────────────────────────────────────────────────────────
  it('F-2 / M1–M6: basis, ruling_ref and reason are in the verified preimage; the pin CHECKs enforce the closed grammar', async () => {
    const mk = async (o: Partial<PinRef>): Promise<string> => {
      const gen = nextGen()
      return tx(async c => {
        await chartCtx(c); await publication(c, gen)
        const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
        await pin(c, gen, { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [], ...o })
        return (await finalize(c, gen)).inv
      })
    }
    const base = await mk({})
    expect(await mk({ basis: 'spec:GOCHARA_DESIGN_SPECS@1.4#§2.2/P5a' })).not.toBe(base)
    expect(await mk({ reason: 'disabled_form', ruling: 'R-9' })).not.toBe(base)
    expect(await mk({ reason: 'disabled_form', ruling: 'R-10' })).not.toBe(await mk({ reason: 'disabled_form', ruling: 'R-9' }))
    expect(await mk({ reason: 'not_applicable_to_class' })).not.toBe(base)
    const b4 = await goodBuild(nextGen())
    const g4b = nextGen()
    await tx(async c => {   // the writer rebuilds the chain with a DIFFERENT p6 basis but keeps the old verification digest
      await chartCtx(c); await publication(c, g4b)
      const snap = await snapshotLive(c, g4b); await header(c, g4b, snap.digest)
      await pin(c, g4b, { path: 'p1', disp: 'included', ids: b4.ids.p1 })
      await pin(c, g4b, { path: 'p5a', disp: 'included', ids: b4.ids.p5a })
      await pin(c, g4b, { path: 'p1', ver: '1.1', disp: 'excluded', reason: 'not_applicable_to_class', basis: B_NA, ids: [] })
      await pin(c, g4b, { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: 'spec:GOCHARA_DESIGN_SPECS@1.4#§2.2/P5a', ids: [] })
      for (const [p, o] of [['p1', P1A], ['p1', P1B], ['p5a', P5A], ['p5a', P5B]] as Array<[string, Ob]>) {
        const id = await ob(c, g4b, p, o); await iv(c, g4b, id, LO, HI, snap.digest)
      }
      await finalize(c, g4b); await partition(c, g4b); await verify(c, g4b, b4.dig.inv)
    })
    await refused(publishAndSeal(g4b), /verification_missing_or_mismatch/)
    const degrading = await mk({ reason: 'disabled_form', ruling: 'R-9', basis: 'ruling:R-9' })
    const g5 = nextGen()
    await goodBuild(g5, { verifyDigest: degrading })
    await refused(publishAndSeal(g5), /verification_missing_or_mismatch/)
    const bad = (o: Partial<PinRef>, re: RegExp): Promise<void> => refused(mk(o), re)
    await bad({ reason: 'disabled_form', ruling: undefined }, /kgspp_ruling_iff_degrading_ck/)
    await bad({ reason: 'on_demand_tier', ruling: 'R-9' }, /kgspp_ruling_iff_degrading_ck/)
    await bad({ basis: 'free prose that is not a reference' }, /kgspp_basis_grammar_ck/)
    await bad({ basis: 'spec:X@1.4#a|b' }, /kgspp_basis_grammar_ck/)
    await bad({ reason: 'made_up_reason' }, /kgspp_reason_closed_ck/)
    await bad({ basis: undefined }, /kgspp_basis_required_ck/)
    await bad({ disp: 'included', reason: undefined, basis: undefined, ids: [] }, /kgspp_included_nonempty_ck/)
  })

  // ── 6. lock protocol with COMPETING SESSIONS ─────────────────────────────────
  it('lock protocol (competing sessions): a chart writer blocks another chart writer AND a registry writer; a sealing transaction blocks a registry advance; the orchestrator\'s main-connection lock does not block the worker', async () => {
    const lockTimeout = async (fn: (c: PoolClient) => Promise<unknown>): Promise<string | null> => {
      const c = await pool.connect()
      try {
        await c.query('BEGIN'); await c.query(`SET LOCAL lock_timeout = '400ms'`)
        try { await fn(c); await c.query('COMMIT'); return null } catch (e) { await c.query('ROLLBACK'); return (e as Error).message }
      } finally { c.release() }
    }
    const A = await pool.connect()
    const gen = nextGen()
    try {
      await A.query('BEGIN')
      await chartCtx(A); await publication(A, gen)
      const snap = await snapshotLive(A, gen); await header(A, gen, snap.digest)
      await pin(A, gen, { path: 'p5a', disp: 'excluded', reason: 'not_applicable_to_class', basis: B_P6, ids: [] })   // chart EXCLUSIVE then global SHARED
      expect(await lockTimeout(c => c.query(`SELECT ka_gochara_lock_chart($1)`, [CHART]))).toMatch(/lock timeout/)
      expect(await lockTimeout(c => c.query(`SELECT ka_gochara_lock_global()`))).toMatch(/lock timeout/)
      await A.query('COMMIT')
    } finally { A.release() }
    expect(await lockTimeout(c => c.query(`SELECT ka_gochara_lock_chart($1)`, [CHART]))).toBeNull()
    expect(await lockTimeout(c => c.query(`SELECT ka_gochara_lock_global()`))).toBeNull()

    // a SEALING transaction holds chart EXCLUSIVE + global SHARED: a registry advance (global EXCLUSIVE) waits for it
    const g = nextGen()
    await goodBuild(g)
    const S = await pool.connect()
    try {
      await S.query('BEGIN'); await chartCtx(S)
      await S.query(`UPDATE kala_gochara_publication SET status='published', published_at=now() WHERE chart_id=$1 AND generation=$2`, [CHART, g])
      await S.query(`SELECT ka_gochara_seal_generation($1,$2)`, [CHART, g])
      expect(await lockTimeout(c => c.query(`SELECT ka_gochara_lock_global()`))).toMatch(/lock timeout/)
      await S.query('COMMIT')
    } finally { S.release() }
    expect(await lockTimeout(c => c.query(`SELECT ka_gochara_lock_global()`))).toBeNull()

    // the orchestrator's MAIN-connection session lock (hashtext(chart_id), locks.py) is a DIFFERENT key from the
    // contract's `gochara5:chart:` family key: the worker is not blocked by it
    const M = await pool.connect()
    try {
      await M.query(`SELECT pg_advisory_lock(hashtext($1))`, [CHART])
      expect(await lockTimeout(c => c.query(`SELECT ka_gochara_lock_chart($1)`, [CHART]))).toBeNull()
      await M.query(`SELECT pg_advisory_unlock(hashtext($1))`, [CHART])
    } finally { M.release() }

    const gen2 = nextGen()
    await refused(tx(async c => {
      await c.query(`SELECT ka_gochara_lock_global()`)
      await publication(c, gen2)
      await snapshotWith(c, gen2, { conv: CONV, vec: VEC, l1: sha('q'), dasha: sha('r'), av: [] })
    }), /lock-order violation/)
  })

  // ── 7. post-seal immutability: every table × every operation ──────────────────
  it('post-seal: INSERT, UPDATE, DELETE and TRUNCATE are refused on EVERY new table once the generation is sealed', async () => {
    const gen = nextGen()
    await goodBuild(gen)
    await publishAndSeal(gen)
    const tables = ['ka_gochara_search_input_snapshot', 'ka_gochara_search_inventory', 'ka_gochara_search_path_pin',
                    'ka_gochara_search_obligation', 'ka_gochara_search_interval', 'ka_gochara_search_inventory_verification']
    for (const t of tables) {
      const where = `chart_id = '${CHART}' AND generation = '${gen}'`
      await refused(tx(async c => { await chartCtx(c); await c.query(`INSERT INTO ${t} SELECT * FROM ${t} WHERE ${where} LIMIT 1`) }), /SEALED|publication-immutable/)
      await refused(tx(async c => { await chartCtx(c); await c.query(`UPDATE ${t} SET chart_id = chart_id WHERE ${where}`) }), /SEALED|insert-only|publication-immutable/)
      await refused(tx(async c => { await chartCtx(c); await c.query(`DELETE FROM ${t} WHERE ${where}`) }), /SEALED|publication-immutable/)
      await refused(pool.query(`TRUNCATE ${t} CASCADE`), /TRUNCATE refused/)
    }
    const d = await pool.query<{ d: string }>(`SELECT ka_gochara_search_inventories_digest($1,$2) AS d`, [CHART, gen])
    expect(d.rows[0]!.d).toMatch(/^[0-9a-f]{64}$/)
  })

  // ── 8. seal cost (informational: realistic data volume, no wall-clock assertion) ──
  it('seal cost: the first-publication check over a full 27-class generation completes (timing recorded, not asserted)', async () => {
    const gen = nextGen()
    const classes = ['achievement_recognition','bereavement','business_launch','career_advancement','career_change','career_entry','career_setback',
      'childbirth','chronic_onset','education_milestone','exam_outcome','financial_deception','foreign_settlement','illness_acute','major_gain',
      'major_loss','marriage','parental_event','property_acquisition','psychological_arc','relocation','romantic_start','separation',
      'spiritual_turn','surgery','travel_event','birth_anchor']
    const N = 40   // obligations per class
    await tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen)
      for (const cls of classes) await header(c, gen, snap.digest, cls)
      for (const cls of classes) {
        await c.query(`
          WITH g AS (SELECT n, '${cls}|p1|1.0|jupiter|residence|lord|t' || n || '|dasha_lord|self' AS bytes FROM generate_series(1,${N}) n)
          INSERT INTO ka_gochara_search_path_pin (chart_id, generation, event_class, path_id, rule_version, disposition, committed_ob_ids)
          SELECT $1,$2,'${cls}','p1','1.0','included', (SELECT array_agg(ka_gochara_uuidv8(bytes) ORDER BY ka_gochara_uuidv8(bytes)) FROM g)`, [CHART, gen])
        for (const [p, v] of REGISTRY.filter(([p, v]) => !(p === 'p1' && v === '1.0')))
          await pin(c, gen, p === 'p6'
            ? { path: p, ver: v, disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [] }
            : { path: p, ver: v, disp: 'excluded', reason: 'not_applicable_to_class', basis: B_NA, ids: [] }, cls)
        await c.query(`
          INSERT INTO ka_gochara_search_obligation (chart_id, generation, event_class, ob_id, path_id, rule_version, agent, relation, object_role, target, frame, person, canonical_bytes)
          SELECT $1,$2,'${cls}', ka_gochara_uuidv8('${cls}|p1|1.0|jupiter|residence|lord|t' || n || '|dasha_lord|self'), 'p1','1.0','jupiter','residence','lord','t' || n,'dasha_lord','self',
                 '${cls}|p1|1.0|jupiter|residence|lord|t' || n || '|dasha_lord|self' FROM generate_series(1,${N}) n`, [CHART, gen])
        await c.query(`
          INSERT INTO ka_gochara_search_interval (chart_id, generation, event_class, ob_id, search_range, state, input_digest)
          SELECT $1,$2,'${cls}', o.ob_id, r.rng, 'searched_complete', $3
          FROM ka_gochara_search_obligation o,
               (VALUES (tstzrange('${LO}','${MID}','[)')), (tstzrange('${MID}','${HI}','[)'))) r(rng)
          WHERE o.chart_id=$1 AND o.generation=$2 AND o.event_class='${cls}'`, [CHART, gen, snap.digest])
        const d = await finalize(c, gen, cls)
        await partition(c, gen, { cls })
        await verify(c, gen, d.inv, 'verifier-a', cls)
      }
    })
    await pool.query(`UPDATE kala_gochara_publication SET status='published', published_at=now() WHERE chart_id=$1 AND generation=$2`, [CHART, gen])
    const t0 = Date.now()
    const v = await pool.query(`SELECT * FROM ka_gochara_search_completeness_violations($1,$2)`, [CHART, gen])
    const ms = Date.now() - t0
    console.info(`[1206 seal cost] 27 classes × ${N} obligations × 2 intervals: violations=${v.rows.length} in ${ms} ms`)
    expect(v.rows).toEqual([])
    await tx(async c => { await chartCtx(c); await c.query(`SELECT ka_gochara_seal_generation($1,$2)`, [CHART, gen]) })
  })

  // ── 9. the full seal lifecycle (LAST in this describe: it advances the registry) ──
  it('C16 lifecycle: initial seal → identical replay → registry advance → replay again → FIRST seal after advance refused; wrong-manifest refused', async () => {
    const gen = nextGen()
    const b = await goodBuild(gen)
    expect(b.dig.inv).toBe(tsInventoryDigest(CONV, b.snap.digest, [
      { path: 'p1', disp: 'included', ids: b.ids.p1 }, { path: 'p5a', disp: 'included', ids: b.ids.p5a },
      { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [] },
      { path: 'p1', ver: '1.1', disp: 'excluded', reason: 'not_applicable_to_class', basis: B_NA, ids: [] }],
      [obBytes('p1', '1.0', P1A), obBytes('p1', '1.0', P1B), obBytes('p5a', '1.0', P5A), obBytes('p5a', '1.0', P5B)]))
    await publishAndSeal(gen)
    const d1 = await pool.query<{ d: string }>(`SELECT ka_gochara_search_inventories_digest($1,$2) AS d`, [CHART, gen])
    await tx(async c => { await chartCtx(c); await c.query(`SELECT ka_gochara_seal_generation($1,$2)`, [CHART, gen]) })
    await tx(async c => registry(c, [['p7', '1.0']]))
    await tx(async c => { await chartCtx(c); await c.query(`SELECT ka_gochara_seal_generation($1,$2)`, [CHART, gen]) })
    const d2 = await pool.query<{ d: string }>(`SELECT ka_gochara_search_inventories_digest($1,$2) AS d`, [CHART, gen])
    expect(d2.rows[0]!.d).toBe(d1.rows[0]!.d)
    const g2 = nextGen()
    await goodBuild(g2)
    await refused(publishAndSeal(g2), /registry_unaccounted_path[\s\S]*p7@1\.0|p7@1\.0/)
    await refused(tx(async c => {
      await chartCtx(c)
      await c.query(`INSERT INTO ka_gochara_generation_seal (chart_id, generation, manifest_id) VALUES ($1,$2,gen_random_uuid())`, [CHART, gen])
    }), /manifest/i)
    const rv = await pool.query(`SELECT * FROM ka_gochara_search_replay_violations($1,$2)`, [CHART, gen])
    expect(rv.rows).toEqual([])
    REGISTRY.push(['p7', '1.0'])
    const g3 = nextGen()
    await goodBuild(g3)
    await publishAndSeal(g3)
  })
})

// The runner-route checks reset the schema, so they run last in their own describe.
describe.skipIf(!TEST_DB_URL)('B6.0 F-1 migration 1206 — deploy route', () => {
  beforeAll(async () => { pool = new Pool({ ...resolveDisposableA51Config(TEST_DB_URL), max: 4 }) })
  afterAll(async () => { if (pool) { await dropRoles(); await pool.end() } })

  it('the routine runner REFUSES 1206 and names the protected window; replay of the applied file is BLOCKED by its gate', async () => {
    await resetSchema()
    await withTempDir(WINDOW_FILES, async dir => {
      await asOwner(async c => {
        await runMigrations(c, [dir], { only: new Set([...CONTRACT_FILES, M1204]), disclosures: new Map(), renumberDisclosures: new Map() })
        await expect(runMigrations(c, [dir], { disclosures: new Map(), renumberDisclosures: new Map() }))
          .rejects.toThrow(/gochara_contracts_schema_migration=true/)
        await runMigrations(c, [dir], { only: new Set([M1206]), disclosures: new Map(), renumberDisclosures: new Map() })
      })
    })
    await expect(pool.query(mig(M1206))).rejects.toThrow(/preflight 1206 BLOCKED/)
    await resetSchema()
    await withTempDir(WINDOW_FILES, async dir => {
      await asOwner(async c => {
        await expect(runMigrations(c, [dir], { only: new Set([M1206]), disclosures: new Map(), renumberDisclosures: new Map() }))
          .rejects.toThrow()
      })
    })
  })
})
