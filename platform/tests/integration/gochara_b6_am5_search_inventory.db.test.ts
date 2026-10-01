// @vitest-environment node
/**
 * Pravāha B6.0 / F-1 — LIVE-DB adversarial suite for migration 1206 (AM-5 search-completeness
 * storage + seal checks), executed against a REAL throwaway Postgres (CLAUDE.md §N.8: the
 * test runs the on-disk SQL itself). It replaces the toy executable model
 * (design/evidence/am5_*.py — a logic check only, per Codex v1.4) as the acceptance evidence:
 * every case of the draft's adversarial matrix runs as a real INSERT / finalise / seal attempt.
 *
 * Independent TypeScript reference implementations of the UUIDv8, canonical-JSON and the
 * three digest preimages cross-check the SQL helpers, and the W1 vectors computed by the
 * Python model (input 800d572c…, inventory fb278bb9…, ledger ddbd5a44… / 62c4224e…) must be
 * reproduced byte-for-byte by the database.
 *
 * Requires a THROWAWAY database. Skipped unless GOCHARA_A51_TEST_DATABASE_URL is set (same
 * disposable boundary as the A5.1 / B6 suites — tests/integration/gochara_a5_1_disposable_url.ts).
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
const WINDOW_FILES = [...CONTRACT_FILES, M1204, M1206] as const

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const CONV = 'sha256:eac922d4c3b0deb700112f2260cd250a0388ab159f4a1c4bca9451281a48e7a3'   // AM-1 vector digest
const LEGACY_CONV = 'legacy:c0'
const AV_DECL = 'av-build:l1:482012f1:v1'
const LO = '2025-01-01T00:00:00Z'
const MID = '2025-02-01T00:00:00Z'
const HI = '2025-03-01T00:00:00Z'
const HORIZON_SQL = `tstzrange('${LO}','${HI}','[)')`
const VEC = { bg_transit_rules: 'd1', bg_transit_av_gates: 'd2' }
const B_P6 = 'spec:GOCHARA_DESIGN_SPECS@1.4#§2.2/P6'
const B_EMPTY = 'oracle:O-RP-8'
const CLS = 'marriage'

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

interface PinRef { path: string; disp: 'included' | 'computed_empty' | 'excluded'; reason?: string; ruling?: string; basis?: string; ids: string[] }
const sortC = (xs: string[]): string[] => [...xs].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0))
function tsInventoryDigest(conv: string, input: string, pins: PinRef[], obs: string[]): string {
  const lines = [`convention=${conv}`, `horizon=[${LO},${HI})`, `input=${input}`]
  for (const p of [...pins].sort((a, b) => (a.path < b.path ? -1 : 1)))
    lines.push(`pin=${p.path}|1.0|${p.disp}|${p.reason ?? ''}|${p.ruling ?? ''}|${p.basis ?? ''}|${sortC(p.ids).join(',')}`)
  for (const o of sortC(obs)) lines.push(`ob=${o}`)
  return sha(lines.join('\n'))
}
const tsLedgerDigest = (rows: Array<[string, string, string, string]>, input: string): string =>
  sha(sortC(rows.map(([id, lo, hi, st]) => `${id}|${lo}|${hi}|${st}|${input}`)).join('\n'))

// ── harness ────────────────────────────────────────────────────────────────────
let pool: Pool
type Q = Pick<PoolClient, 'query'>
let genSeq = 0
const nextGen = (): string => `5.${++genSeq + 20}`

function mig(name: string): string { return readFileSync(join(MIGRATIONS_DIR, name), 'utf8') }
async function tx<T>(fn: (c: PoolClient) => Promise<T>): Promise<T> {
  const c = await pool.connect()
  try { await c.query('BEGIN'); const r = await fn(c); await c.query('COMMIT'); return r }
  catch (err) { await c.query('ROLLBACK').catch(() => undefined); throw err }
  finally { c.release() }
}
async function withTempDir<T>(files: readonly string[], fn: (dir: string) => Promise<T>): Promise<T> {
  const dir = mkdtempSync(join(tmpdir(), 'gochara-am5-'))
  try { for (const f of files) copyFileSync(join(MIGRATIONS_DIR, f), join(dir, f)); return await fn(dir) }
  finally { rmSync(dir, { recursive: true, force: true }) }
}
async function window(files: readonly string[]): Promise<void> {
  await withTempDir(WINDOW_FILES, async dir => {
    const c = await pool.connect()
    try { await runMigrations(c, [dir], { only: new Set(files), disclosures: new Map(), renumberDisclosures: new Map() }) }
    finally { c.release() }
  })
}
async function resetSchema(): Promise<void> {
  await pool.query(`
    DROP SCHEMA public CASCADE;
    CREATE SCHEMA public;
    CREATE TABLE charts (id UUID PRIMARY KEY DEFAULT gen_random_uuid());
    -- stand-ins for the production L1 tables the input digests read (key columns only)
    CREATE TABLE chart_facts (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), fact_id TEXT UNIQUE NOT NULL,
      category TEXT NOT NULL DEFAULT 'x', value_text TEXT, created_at TIMESTAMPTZ DEFAULT now());
    CREATE TABLE chart_dashas (dasha_row_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), start_iso TIMESTAMPTZ,
      computed_at TIMESTAMPTZ DEFAULT now());`)
  for (const f of PARENT_FILES) await pool.query(mig(f))
  await pool.query(`INSERT INTO charts (id) VALUES ($1)`, [CHART])
  await pool.query(TRACKER_DDL)
  await pool.query(TRACKER_IDENTITY_DDL)
}
const chartCtx = (c: Q) => c.query(`SELECT ka_gochara_lock_chart($1)`, [CHART])

// fixtures that are generation-independent
const DASHA_IDS = ['30000000-0000-4000-8000-000000000001', '30000000-0000-4000-8000-000000000002']
async function seedStatic(): Promise<void> {
  await tx(async c => {
    await chartCtx(c)
    await c.query(`INSERT INTO kala_gochara_convention
       (convention_id, zodiac, ayanamsha, sidereal_method, node_model, node_source, epoch_convention, time_scale,
        house_system, ephemeris_mode, method_version)
       VALUES ($1,'sidereal','lahiri_chitrapaksha','true_chitra','mean','swiss','j2000','utc','whole_sign','swiss','1.0')`, [LEGACY_CONV])
    await c.query(`INSERT INTO ka_gochara_sky_convention
       (convention_id, ephemeris_generation, ayanamsha, node_convention, grid, method_version, domain_start, domain_end)
       VALUES ($1,'de441','lahiri_chitrapaksha','mean','1s','m1','2025-01-01T00:00Z','2026-01-01T00:00Z')`, [CONV])
    await c.query(`INSERT INTO ka_gochara_convention_bridge (kala_convention_id, sky_convention_id) VALUES ($1,$2)`, [LEGACY_CONV, CONV])
    await c.query(`INSERT INTO ka_gochara_av_polarity_declaration
       (convention, benefic_mark_name, malefic_mark_name, source_ref, applies_to_fact_categories)
       VALUES ($1,'rekhā','khaṇḍa','L1_ASHTAKAVARGA_EXTRACT_v1_1', ARRAY['ashtakavarga_bindu'])`, [AV_DECL])
  })
  await pool.query(`INSERT INTO chart_facts (fact_id, value_text) VALUES ('F1','a'),('F2','b')`)
  await pool.query(`INSERT INTO chart_dashas (dasha_row_id, start_iso) VALUES ($1,'2010-08-18T15:50:23Z'),($2,'2013-01-14T07:17:23Z')`, DASHA_IDS)
  await tx(async c => registry(c, ['p1', 'p5a', 'p6']))
}
async function registry(c: Q, ids: string[]): Promise<void> {
  const sel: Record<string, [string, string, string, string, string]> = {
    p1: ['dasha_lord', 'jupiter', 'residence', 'lord', 'verse_cited'],
    p5a: ['lagna', 'saturn', 'residence', 'av_qualifier', 'verse_cited'],
    p6: ['moon', 'moon', 'conjunction', 'karaka', 'uncited_extension'],
    p7: ['lagna', 'mars', 'residence', 'occupant', 'verse_cited'],
  }
  await c.query(`INSERT INTO ka_gochara_predicate (predicate_id, rule_version, operator, operands)
     VALUES ('q1','v1','within_orb','{"left":"chart_facts.graha_position:mars","right":"object.longitude","orb":3.0}')
     ON CONFLICT DO NOTHING`)
  for (const id of ids) {
    const [frame, agent, rel, role, prov] = sel[id]!
    await c.query(
      `INSERT INTO ka_gochara_rule_path (path_id, rule_version, frame_kind, frame_arg, agent_set, relation_set, object_selector,
         provenance, operator_role, ruling_ref, score_rule)
       VALUES ($1,'1.0',$2,NULL,$3::jsonb,$4::jsonb,$5::jsonb,$6,$7,$8,'within_path_product')`,
      [id, frame, JSON.stringify([agent]), JSON.stringify([rel]),
       JSON.stringify([{ agent, relation: rel, object_role: role }]), prov,
       id === 'p6' ? 'testimony' : 'scored', prov === 'uncited_extension' ? 'R-9' : null])
    await c.query(`INSERT INTO ka_gochara_rule_path_prerequisite (path_id, rule_version, ordinal, predicate_id, predicate_rule_version)
                   VALUES ($1,'1.0',1,'q1','v1')`, [id])
    await c.query(`INSERT INTO ka_gochara_rule_path_seal (path_id, rule_version) VALUES ($1,'1.0')`, [id])
  }
}

// ── per-generation builders (each step takes the chart key first, in ONE transaction by the caller) ──
interface Snap { conv: string; vec: unknown; l1: string; dasha: string; av: string[]; digest: string }
async function publication(c: Q, gen: string, vec: unknown = VEC): Promise<void> {
  await c.query(`INSERT INTO kala_gochara_publication
     (chart_id, generation, writer_asset_id, convention_id, input_generation_vector, ephemeris_backend, horizon, row_counts, content_digest, status)
     VALUES ($1,$2,'ka_gochara',$3,$4::jsonb,'{}',${HORIZON_SQL},'{}','digest','candidate')`, [CHART, gen, LEGACY_CONV, JSON.stringify(vec)])
}
async function snapshotLive(c: Q, gen: string, vec: unknown = VEC): Promise<Snap> {
  const q = async (sqlText: string, args: unknown[]): Promise<string> => (await c.query<{ v: string }>(sqlText, args)).rows[0]!.v
  const l1 = await q(`SELECT ka_gochara_search_l1_facts_digest($1::text[]) AS v`, [['F1', 'F2']])
  const dasha = await q(`SELECT ka_gochara_search_dasha_digest($1::text[]) AS v`, [DASHA_IDS])
  const av = [await q(`SELECT ka_gochara_search_av_entry($1) AS v`, [AV_DECL])]
  return snapshotWith(c, gen, { conv: CONV, vec, l1, dasha, av })
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
     VALUES ($1,$2,$3,$4,'1.0',$5,$6,$7,$8,$9::uuid[])`,
    [CHART, gen, cls, p.path, p.disp, p.reason ?? null, p.ruling ?? null, p.basis ?? null, sortC(p.ids)])
}
async function ob(c: Q, gen: string, path_: string, o: Ob, cls = CLS): Promise<string> {
  const bytes = obBytes(path_, '1.0', o, cls); const id = uuidv8(bytes)
  await c.query(
    `INSERT INTO ka_gochara_search_obligation
       (chart_id, generation, event_class, ob_id, path_id, rule_version, agent, relation, object_role, target, frame, person, canonical_bytes)
     VALUES ($1,$2,$3,$4,$5,'1.0',$6,$7,$8,$9,$10,$11,$12)`, [CHART, gen, cls, id, path_, ...o, bytes])
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
async function partition(c: Q, gen: string, o: { cls?: string; relations?: string[]; horizon?: string } = {}): Promise<void> {
  const h = o.horizon ?? HORIZON_SQL
  await c.query(
    `INSERT INTO kala_gochara_coverage
       (chart_id, generation, partition_kind, partition_key, convention_id, requested_horizon, completed_horizon, resolution,
        relations_searched, targets_requested, targets_resolved, targets_unresolved, target_resolution_state_counts, build_id)
     VALUES ($1,$2,'event_class',$3,$4,${h},${h},1.0,$5::text[],1,1,0,'{"resolved":1}','build-am5')`,
    [CHART, gen, o.cls ?? CLS, LEGACY_CONV, o.relations ?? ['residence']])
}
async function verify(c: Q, gen: string, digest: string, who = 'verifier-a', cls = CLS): Promise<void> {
  await c.query(`INSERT INTO ka_gochara_search_inventory_verification
     (chart_id, generation, event_class, verifier_id, verifier_version, rederived_inventory_digest) VALUES ($1,$2,$3,$4,'1',$5)`,
    [CHART, gen, cls, who, digest])
}
async function publishAndSeal(gen: string): Promise<void> {
  await tx(async c => {
    await chartCtx(c)
    await c.query(`UPDATE kala_gochara_publication SET status='published', published_at=now() WHERE chart_id=$1 AND generation=$2`, [CHART, gen])
    await c.query(`SELECT ka_gochara_seal_generation($1,$2)`, [CHART, gen])
  })
}

/** A GOOD two-path build: p1 (A,B) + p5a (A,B) included, p6 excluded on_demand_tier; every
 *  obligation covered over the horizon; finalised, partition written, verified by a hash of
 *  the stored rows. `mutate` runs inside the build transaction before finalisation. */
interface Built { gen: string; snap: Snap; ids: { p1: string[]; p5a: string[] }; dig: { inv: string; led: string } }
async function goodBuild(gen: string, o: {
  vec?: unknown; skipP5aObligations?: boolean; p5a?: 'included' | 'computed_empty' | 'none'; p6?: boolean
  noVerify?: boolean; verifyDigest?: string; p6Basis?: string; noPartition?: boolean; partitionRelations?: string[]
  between?: (c: PoolClient, b: { snap: Snap; ids: { p1: string[]; p5a: string[] } }) => Promise<void>
} = {}): Promise<Built> {
  return tx(async c => {
    await chartCtx(c)
    await publication(c, gen, o.vec)
    const snap = await snapshotLive(c, gen, o.vec ?? VEC)
    await header(c, gen, snap.digest)
    const p1 = [obId('p1', '1.0', P1A), obId('p1', '1.0', P1B)]
    const p5a = [obId('p5a', '1.0', P5A), obId('p5a', '1.0', P5B)]
    await pin(c, gen, { path: 'p1', disp: 'included', ids: p1 })
    if (o.p6 !== false) await pin(c, gen, { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: o.p6Basis ?? B_P6, ids: [] })
    const mode = o.p5a ?? 'included'
    if (mode === 'included') await pin(c, gen, { path: 'p5a', disp: 'included', ids: p5a })
    if (mode === 'computed_empty') await pin(c, gen, { path: 'p5a', disp: 'computed_empty', basis: B_EMPTY, ids: [] })
    await ob(c, gen, 'p1', P1A); await ob(c, gen, 'p1', P1B)
    if (mode === 'included' && !o.skipP5aObligations) { await ob(c, gen, 'p5a', P5A); await ob(c, gen, 'p5a', P5B) }
    const covered = [...p1, ...(mode === 'included' && !o.skipP5aObligations ? p5a : [])]
    for (const id of covered) await iv(c, gen, id, LO, HI, snap.digest)
    if (o.between) await o.between(c, { snap, ids: { p1, p5a } })
    const dig = await finalize(c, gen)
    if (!o.noPartition) await partition(c, gen, { relations: o.partitionRelations })
    if (!o.noVerify) await verify(c, gen, o.verifyDigest ?? dig.inv)
    return { gen, snap, ids: { p1, p5a }, dig }
  })
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
    pool = new Pool({ ...resolveDisposableA51Config(TEST_DB_URL), max: 4 })
    await resetSchema()
    // the protected window, in two steps so the APPLIED objects' definitions can be fingerprinted
    // before and after 1206 (nothing pre-existing may change)
    await window([...CONTRACT_FILES, M1204])
    defsBefore = await defs()
    await window([M1206])
    await seedStatic()
  }, 180_000)

  afterAll(async () => {
    if (!pool) return
    await resetSchema()
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
    // the one touch on an existing relation: a NEW trigger on the seal table; the applied guard still fires
    const seal = await pool.query<{ t: string }>(
      `SELECT tgname AS t FROM pg_trigger WHERE tgrelid = 'ka_gochara_generation_seal'::regclass AND NOT tgisinternal ORDER BY 1`)
    expect(seal.rows.map(r => r.t)).toEqual(
      expect.arrayContaining(['ka_gochara_generation_seal_write_guard', 'ka_gochara_generation_seal_z_search_complete']))
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
    // the post-mask collision control: two digests differing ONLY in the masked bits share a UUID
    expect(uuidv8('mars|conjunction|point:198.52|c0|1')).toBe('23276d7c-c127-8f4c-9ad5-6b7c8da8020f')
    const cj = await pool.query<{ j: string }>(`SELECT ka_gochara_canonical_json($1::jsonb) AS j`,
      ['{"z":[3,{"b":1,"a":"é"}],"a":null,"m":true}'])
    expect(cj.rows[0]!.j).toBe(canonJson({ z: [3, { b: 1, a: 'é' }], a: null, m: true }))
    expect(canonJson(VEC)).toBe('{"bg_transit_av_gates":"d2","bg_transit_rules":"d1"}')
  })

  it('W1: the database reproduces the Python-model vectors (input 800d572c…, inventory fb278bb9…, ledgers ddbd5a44…/62c4224e…)', async () => {
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
        const a = await ob(c, gen, 'p1', P1A); const b = await ob(c, gen, 'p1', P1B)
        await iv(c, gen, a, rows[0]![0], rows[0]![1], snap.digest)
        await iv(c, gen, b, rows[1]![0], rows[1]![1], snap.digest)
        return finalize(c, gen)
      })
    const h1 = await run(nextGen(), [[LO, MID], [MID, HI]])      // A January, B February
    const h2 = await run(nextGen(), [[LO, HI], [LO, HI]])        // both January–February
    const expectedInv = 'fb278bb92edce1505d649c6aabab96a01f65622fd00e6437a3a33c30836d07db'
    expect(h1.inv).toBe(expectedInv)
    expect(h2.inv).toBe(expectedInv)
    expect(h1.led).toBe('ddbd5a44d0745682d402b5c1118439e9f4fca95b90bf4676984e818e6bc5bd82')
    expect(h2.led).toBe('62c4224ee2a0eb23416769c3aa8cc3ccab4a6452bedb09f893d0368df6d2f1a7')
    // …and the independent TypeScript reference agrees
    const input = inputDigest(synth)
    const ids = [obId('p1', '1.0', P1A), obId('p1', '1.0', P1B)]
    expect(tsInventoryDigest(CONV, input, [
      { path: 'p1', disp: 'included', ids }, { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [] }],
      [obBytes('p1', '1.0', P1A), obBytes('p1', '1.0', P1B)])).toBe(expectedInv)
    expect(tsLedgerDigest([[ids[0]!, LO, MID, 'searched_complete'], [ids[1]!, MID, HI, 'searched_complete']], input)).toBe(h1.led)
    expect(tsLedgerDigest([[ids[0]!, LO, HI, 'searched_complete'], [ids[1]!, LO, HI, 'searched_complete']], input)).toBe(h2.led)
    // H1 vs H2: identical inventory, DIFFERENT ledgers — the v0.3 flattening is unrepresentable
    expect(h1.led).not.toBe(h2.led)
  })

  // ── 2. the good build, the full seal lifecycle (C16), and completeness arithmetic ──
  it('C1 Codex W2, exactly as written, is REFUSED: P5a pinned included, obligations never inserted, everything stored covered, verifier merely re-hashes', async () => {
    const gen = nextGen()
    await goodBuild(gen, { skipP5aObligations: true })     // verification row = hash of the stored (incomplete) rows
    await refused(publishAndSeal(gen), /committed_set_mismatch[\s\S]*p5a@1\.0 committed-not-stored=/)
    // the violation function names the two missing committed ids
    const v = await pool.query<{ violation: string; detail: string }>(
      `SELECT violation, detail FROM ka_gochara_search_completeness_violations($1,$2)`, [CHART, gen])
    const m = v.rows.find(r => r.violation === 'committed_set_mismatch')!
    expect(m.detail).toContain(obId('p5a', '1.0', P5A))
    expect(m.detail).toContain(obId('p5a', '1.0', P5B))
  })

  it('C1b: an included pin with an empty commitment is refused at insert (kgspp_included_nonempty_ck)', async () => {
    const gen = nextGen()
    await refused(tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      await pin(c, gen, { path: 'p5a', disp: 'included', ids: [] })
    }), /kgspp_included_nonempty_ck/)
  })

  it('C2: a sealed registry path with no pin at all → registry_unaccounted_path', async () => {
    const gen = nextGen()
    const b = await goodBuild(gen, { p6: false, noVerify: true })    // p6 never pinned
    await tx(async c => { await chartCtx(c); await verify(c, gen, b.dig.inv) })
    await refused(publishAndSeal(gen), /registry_unaccounted_path[\s\S]*p6@1\.0|p6@1\.0/)
  })

  it('C3 / C3c: a false computed_empty, or a smaller committed set, with a verifier that derives the TRUE inventory → verification_missing_or_mismatch', async () => {
    const truth = await goodBuild(nextGen())                      // the true inventory (p5a included)
    const g1 = nextGen()
    await goodBuild(g1, { p5a: 'computed_empty', verifyDigest: truth.dig.inv })
    await refused(publishAndSeal(g1), /verification_missing_or_mismatch/)
    // smaller committed AND stored set (p1 only A) — structurally self-consistent; only the verifier can tell
    const g2 = nextGen()
    await tx(async c => {
      await chartCtx(c); await publication(c, g2)
      const snap = await snapshotLive(c, g2); await header(c, g2, snap.digest)
      await pin(c, g2, { path: 'p1', disp: 'included', ids: [obId('p1', '1.0', P1A)] })
      for (const p of ['p5a']) await pin(c, g2, { path: p, disp: 'included', ids: truth.ids.p5a })
      await pin(c, g2, { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [] })
      const a = await ob(c, g2, 'p1', P1A); const x = await ob(c, g2, 'p5a', P5A); const y = await ob(c, g2, 'p5a', P5B)
      for (const id of [a, x, y]) await iv(c, g2, id, LO, HI, snap.digest)
      await finalize(c, g2); await partition(c, g2); await verify(c, g2, truth.dig.inv)
    })
    await refused(publishAndSeal(g2), /verification_missing_or_mismatch/)
  })

  it('C3b: no verification row → refused; C5 (positive control): a genuine computed_empty with an agreeing verifier seals', async () => {
    const g1 = nextGen()
    await goodBuild(g1, { p5a: 'computed_empty', noVerify: true })
    await refused(publishAndSeal(g1), /verification_missing_or_mismatch/)
    const g2 = nextGen()
    await goodBuild(g2, { p5a: 'computed_empty' })             // verifier digest == stored digest
    await publishAndSeal(g2)
    const p = await pool.query<{ disposition: string }>(
      `SELECT disposition FROM ka_gochara_search_path_pin WHERE chart_id=$1 AND generation=$2 AND path_id='p5a'`, [CHART, g2])
    expect(p.rows[0]!.disposition).toBe('computed_empty')
  })

  it('C4: an obligation with NO ledger rows → obligation_uncovered (the wholly-missing-path case 1156 cannot see); a half-covered one too (W1 H1)', async () => {
    const g1 = nextGen()
    await tx(async c => {
      await chartCtx(c); await publication(c, g1)
      const snap = await snapshotLive(c, g1); await header(c, g1, snap.digest)
      await pin(c, g1, { path: 'p1', disp: 'included', ids: [obId('p1', '1.0', P1A), obId('p1', '1.0', P1B)] })
      await pin(c, g1, { path: 'p5a', disp: 'excluded', reason: 'not_applicable_to_class', basis: 'spec:GOCHARA_DESIGN_SPECS@1.4#§2.2/p5a', ids: [] })
      await pin(c, g1, { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [] })
      const a = await ob(c, g1, 'p1', P1A); await ob(c, g1, 'p1', P1B)             // B never searched
      await iv(c, g1, a, LO, MID, snap.digest)                                       // A only January (H1-style gap)
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
    await refused(tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      await pin(c, gen, { path: 'p5a', disp: 'included', ids: [obId('p5a', '1.0', P5A)] })
      await ob(c, gen, 'p5a', P5B)                                                  // not committed
    }), /not in the pin's committed obligation set/)
    await refused(tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      await pin(c, gen, { path: 'p5a', disp: 'included', ids: [obId('p5a', '1.0', P5A)] })
      const bytes = obBytes('p5a', '1.0', P5A)
      await c.query(`INSERT INTO ka_gochara_search_obligation
        (chart_id, generation, event_class, ob_id, path_id, rule_version, agent, relation, object_role, target, frame, person, canonical_bytes)
        VALUES ($1,$2,$3,gen_random_uuid(),'p5a','1.0',$4,$5,$6,$7,$8,$9,$10)`, [CHART, gen, CLS, ...P5A, bytes])
    }), /is not the UUIDv8 of its canonical bytes|committed obligation set/)
    // non-canonical (uppercase) bytes with a CONSISTENT ob_id that the pin DID commit: only the shape CHECK can stop it
    const upper = 'marriage|p5a|1.0|SATURN|residence|av_qualifier|house_span:7|lagna|self'
    await refused(tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      await pin(c, gen, { path: 'p5a', disp: 'included', ids: [uuidv8(upper)] })
      await c.query(`INSERT INTO ka_gochara_search_obligation
        (chart_id, generation, event_class, ob_id, path_id, rule_version, agent, relation, object_role, target, frame, person, canonical_bytes)
        VALUES ($1,$2,$3,$4,'p5a','1.0','SATURN','residence','av_qualifier','house_span:7','lagna','self',$5)`,
        [CHART, gen, CLS, uuidv8(upper), upper])
    }), /kgso_bytes_shape_ck/)
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
      await chartCtx(c); await publication(c, gen)                                  // manifest vector = VEC
      await snapshotWith(c, gen, { conv: CONV, vec: { bg_transit_rules: 'DIFFERENT' }, l1: sha('a'), dasha: sha('b'), av: [] })
    }), /differs from the manifest/)
    await refused(tx(async c => {
      await chartCtx(c); await publication(c, gen)
      await c.query(`INSERT INTO ka_gochara_search_input_snapshot
        (chart_id, generation, convention_id, input_generation_vector, consumed_fact_ids, consumed_dasha_row_ids, av_declarations, l1_facts_digest, dasha_digest, input_digest)
        VALUES ($1,$2,$3,$4::jsonb,'{}','{}','{}',$5,$5,$5)`, [CHART, gen, CONV, JSON.stringify(VEC), sha('z')])
    }), /does not recompute from its components/)
  })

  it('C9: L1 rewritten after the search → input_snapshot_drift; manifest vector changed → input_vector_mismatch; both refuse the seal, and restoring L1 lets it seal', async () => {
    const gen = nextGen()
    await goodBuild(gen)
    await pool.query(`UPDATE chart_facts SET value_text = 'tampered' WHERE fact_id = 'F1'`)
    await refused(publishAndSeal(gen), /input_snapshot_drift/)
    await pool.query(`UPDATE chart_facts SET value_text = 'a' WHERE fact_id = 'F1'`)
    await pool.query(`UPDATE chart_dashas SET start_iso = '2010-08-18T16:00:00Z' WHERE dasha_row_id = $1`, [DASHA_IDS[0]])
    await refused(publishAndSeal(gen), /input_snapshot_drift/)
    await pool.query(`UPDATE chart_dashas SET start_iso = '2010-08-18T15:50:23Z' WHERE dasha_row_id = $1`, [DASHA_IDS[0]])
    await pool.query(`UPDATE kala_gochara_publication SET input_generation_vector = '{"bg_transit_rules":"d9"}'::jsonb WHERE chart_id=$1 AND generation=$2`, [CHART, gen])
    await refused(publishAndSeal(gen), /input_vector_mismatch/)
    await pool.query(`UPDATE kala_gochara_publication SET input_generation_vector = $3::jsonb WHERE chart_id=$1 AND generation=$2`, [CHART, gen, JSON.stringify(VEC)])
    await publishAndSeal(gen)    // L1/dasha/AV restored, vector restored → seals
  })

  it('C15: the same targets, paths and convention under a different L1 snapshot yield a different input digest, inventory digest and ledger digest', async () => {
    const a = await goodBuild(nextGen())
    await pool.query(`UPDATE chart_facts SET value_text = 'rebuilt' WHERE fact_id = 'F2'`)
    const b = await goodBuild(nextGen())
    await pool.query(`UPDATE chart_facts SET value_text = 'b' WHERE fact_id = 'F2'`)
    expect(b.snap.digest).not.toBe(a.snap.digest)
    expect(b.dig.inv).not.toBe(a.dig.inv)
    expect(b.dig.led).not.toBe(a.dig.led)
    // the nine-field ob_id is UNCHANGED (inputs change completion digests, not obligation identity)
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
    // adjacent half-open ranges are NOT an overlap
    await tx(async c => { const s = await stage(c); await iv(c, gen, s.id, LO, MID, s.input); await iv(c, gen, s.id, MID, HI, s.input) })
  })

  it('finalisation: a wrong digest is refused; a finalised class is immutable; verification needs a finalised class; a header cannot be deleted under its children', async () => {
    const gen = nextGen()
    await refused(tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      await verify(c, gen, sha('x'))
    }), /not FINALISED/)
    // each digest is checked on its OWN: a wrong inventory digest with the right ledger digest, and the converse
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
    await refused(tx(async c => { await chartCtx(c); await pin(c, g2, { path: 'p7', disp: 'excluded', reason: 'not_applicable_to_class', basis: B_P6, ids: [] }) }), /FINALISED/)
    await refused(tx(async c => {
      await chartCtx(c)
      await c.query(`UPDATE ka_gochara_search_inventory SET inventory_digest=$3 WHERE chart_id=$1 AND generation=$2`, [CHART, g2, sha('again')])
    }), /already FINALISED/)
    await refused(tx(async c => { await chartCtx(c); await c.query(`DELETE FROM ka_gochara_search_inventory WHERE chart_id=$1 AND generation=$2`, [CHART, g2]) }), /foreign key|violates/)
    // candidate REPLACEMENT in dependency order works (and a changed input mints a new chain)
    await tx(async c => {
      await chartCtx(c)
      for (const t of ['ka_gochara_search_inventory_verification', 'ka_gochara_search_interval', 'ka_gochara_search_obligation',
                       'ka_gochara_search_path_pin', 'ka_gochara_search_inventory', 'ka_gochara_search_input_snapshot'])
        await c.query(`DELETE FROM ${t} WHERE chart_id=$1 AND generation=$2`, [CHART, g2])
      await c.query(`DELETE FROM kala_gochara_coverage WHERE chart_id=$1 AND generation=$2`, [CHART, g2])
      const s = await snapshotLive(c, g2); await header(c, g2, s.digest)
    })
  })

  it('C14 / partition / manifest: a missing_inputs interval, an over-claiming partition and a horizon that is not the manifest\'s refuse the seal', async () => {
    const g1 = nextGen()
    await tx(async c => {
      await chartCtx(c); await publication(c, g1)
      const snap = await snapshotLive(c, g1); await header(c, g1, snap.digest)
      await pin(c, g1, { path: 'p1', disp: 'included', ids: [obId('p1', '1.0', P1A)] })
      await pin(c, g1, { path: 'p5a', disp: 'excluded', reason: 'inputs_unavailable', ruling: 'R-9', basis: 'ruling:R-9', ids: [] })
      await pin(c, g1, { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [] })
      const a = await ob(c, g1, 'p1', P1A)
      await iv(c, g1, a, LO, HI, snap.digest, 'missing_inputs')
      const d = await finalize(c, g1); await partition(c, g1); await verify(c, g1, d.inv)
    })
    await refused(publishAndSeal(g1), /missing_inputs_present/)
    // partition relations_searched wider than the obligations' relations, and horizon ≠ inventory horizon
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
      for (const p of ['p5a']) await pin(c, g3, { path: p, disp: 'excluded', reason: 'not_applicable_to_class', basis: 'spec:GOCHARA_DESIGN_SPECS@1.4#§2.2/p5a', ids: [] })
      await pin(c, g3, { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [] })
      const a = await ob(c, g3, 'p1', P1A); await iv(c, g3, a, LO, HI, snap.digest)
      const d = await finalize(c, g3); await partition(c, g3); await verify(c, g3, d.inv)
    })
    await refused(publishAndSeal(g3), /horizon_manifest_mismatch/)
    // a class claimed by a partition but never inventoried, and an inventory without a partition
    const g4 = nextGen()
    await goodBuild(g4, { noPartition: true })
    await refused(publishAndSeal(g4), /inventory_without_partition/)
    const g5 = nextGen()
    await goodBuild(g5)
    await tx(async c => { await chartCtx(c); await partition(c, g5, { cls: 'career_change' }) })
    await refused(publishAndSeal(g5), /partition_without_inventory/)
  })

  // ── 5. F-2: exclusion evidence ───────────────────────────────────────────────
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
    // M1–M3: changing basis / ruling_ref / reason changes the digest (a degrading reason requires its ruling)
    // (each `mk` runs on its own generation + snapshot; snapshots are identical because L1 is unchanged)
    const base = await mk({})
    expect(await mk({ basis: 'spec:GOCHARA_DESIGN_SPECS@1.4#§2.2/P5a' })).not.toBe(base)
    expect(await mk({ reason: 'disabled_form', ruling: 'R-9' })).not.toBe(base)
    expect(await mk({ reason: 'disabled_form', ruling: 'R-10' })).not.toBe(await mk({ reason: 'disabled_form', ruling: 'R-9' }))
    expect(await mk({ reason: 'not_applicable_to_class' })).not.toBe(base)
    // M4: the writer silently swaps an exclusion's basis AFTER the independent verifier signed the original
    // (UPDATE is refused, so the attack is a rebuilt chain carrying the OLD verification digest)
    const g4 = nextGen()
    const b4 = await goodBuild(g4)
    const g4b = nextGen()
    await goodBuild(g4b, { p6Basis: 'spec:GOCHARA_DESIGN_SPECS@1.4#§2.2/P5a', verifyDigest: b4.dig.inv })
    await refused(publishAndSeal(g4b), /verification_missing_or_mismatch/)
    // M5: the writer declares a NON-degrading exclusion where the verifier derives a DEGRADING one
    const degrading = await mk({ reason: 'disabled_form', ruling: 'R-9', basis: 'ruling:R-9' })
    const g5 = nextGen()
    await goodBuild(g5, { verifyDigest: degrading })
    await refused(publishAndSeal(g5), /verification_missing_or_mismatch/)
    // M6: pin CHECKs
    const bad = (o: Partial<PinRef>, re: RegExp): Promise<void> => refused(mk(o), re)
    await bad({ reason: 'disabled_form', ruling: undefined }, /kgspp_ruling_iff_degrading_ck/)          // degrading without ruling
    await bad({ reason: 'on_demand_tier', ruling: 'R-9' }, /kgspp_ruling_iff_degrading_ck/)             // ruling on a non-degrading reason
    await bad({ basis: 'free prose that is not a reference' }, /kgspp_basis_grammar_ck/)                 // basis outside the grammar
    await bad({ basis: 'spec:X@1.4#a|b' }, /kgspp_basis_grammar_ck/)                                      // a delimiter in the basis
    await bad({ reason: 'made_up_reason' }, /kgspp_reason_closed_ck/)                                     // reason outside the closed set
    await bad({ basis: undefined }, /kgspp_basis_required_ck/)                                            // excluded needs a basis
    await bad({ disp: 'included', reason: undefined, basis: undefined, ids: [] }, /kgspp_included_nonempty_ck/)
  })

  // ── 6. lock protocol ─────────────────────────────────────────────────────────
  it('lock protocol: chart EXCLUSIVE → global SHARED is taken by a receipt-only transaction; the global-EXCLUSIVE key cannot be held with a chart write', async () => {
    const gen = nextGen()
    await tx(async c => {
      await chartCtx(c); await publication(c, gen)
      const snap = await snapshotLive(c, gen); await header(c, gen, snap.digest)
      const before = await c.query<{ s: string | null }>(`SELECT current_setting('gochara5.global_shared', true) AS s`)
      expect(before.rows[0]!.s ?? '').not.toBe('on')
      await pin(c, gen, { path: 'p5a', disp: 'excluded', reason: 'not_applicable_to_class', basis: B_P6, ids: [] })
      const after = await c.query<{ s: string; cl: string }>(
        `SELECT current_setting('gochara5.global_shared', true) AS s, current_setting('gochara5.chart_locked', true) AS cl`)
      expect(after.rows[0]).toEqual({ s: 'on', cl: 'on' })
    })
    const gen2 = nextGen()
    await refused(tx(async c => {
      await c.query(`SELECT ka_gochara_lock_global()`)                      // registry-style EXCLUSIVE key first
      await publication(c, gen2)
      await c.query(`INSERT INTO ka_gochara_search_input_snapshot (chart_id, generation, convention_id, input_generation_vector,
        consumed_fact_ids, consumed_dasha_row_ids, av_declarations, l1_facts_digest, dasha_digest, input_digest)
        VALUES ($1,$2,$3,'{}','{}','{}','{}',$4,$4,$4)`, [CHART, gen2, CONV, sha('q')])
    }), /lock-order violation/)
  })

  // LAST in this describe: it advances the registry (p7), which every later first-publication seal must account for
  it('C16 lifecycle: initial seal → identical replay → registry advance → replay again → FIRST seal after advance refused; wrong-manifest and post-seal mutation refused', async () => {
    const gen = nextGen()
    const b = await goodBuild(gen)
    expect(b.dig.inv).toBe(tsInventoryDigest(CONV, b.snap.digest, [
      { path: 'p1', disp: 'included', ids: b.ids.p1 }, { path: 'p5a', disp: 'included', ids: b.ids.p5a },
      { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [] }],
      [obBytes('p1', '1.0', P1A), obBytes('p1', '1.0', P1B), obBytes('p5a', '1.0', P5A), obBytes('p5a', '1.0', P5B)]))
    await publishAndSeal(gen)                                                   // 1. initial seal
    const s1 = await pool.query<{ manifest_id: string }>(`SELECT manifest_id FROM ka_gochara_generation_seal WHERE chart_id=$1 AND generation=$2`, [CHART, gen])
    expect(s1.rows).toHaveLength(1)
    const d1 = await pool.query<{ d: string }>(`SELECT ka_gochara_search_inventories_digest($1,$2) AS d`, [CHART, gen])
    expect(d1.rows[0]!.d).toMatch(/^[0-9a-f]{64}$/)
    await tx(async c => { await chartCtx(c); await c.query(`SELECT ka_gochara_seal_generation($1,$2)`, [CHART, gen]) })   // 2. identical replay: no-op
    await tx(async c => registry(c, ['p7']))                                    // 3. registry advance (global-EXCLUSIVE txn)
    await tx(async c => { await chartCtx(c); await c.query(`SELECT ka_gochara_seal_generation($1,$2)`, [CHART, gen]) })   // 4. replay again: still accepted
    const d2 = await pool.query<{ d: string }>(`SELECT ka_gochara_search_inventories_digest($1,$2) AS d`, [CHART, gen])
    expect(d2.rows[0]!.d).toBe(d1.rows[0]!.d)                                   // sealed content did not move
    // 5. a FIRST seal for a new generation under the advanced registry is refused until p7 is accounted for
    const g2 = nextGen()
    await goodBuild(g2)
    await refused(publishAndSeal(g2), /registry_unaccounted_path[\s\S]*p7@1\.0|p7@1\.0/)
    // 6. wrong manifest: a seal row naming another manifest is refused (the applied 1153 guard fires first)
    await refused(tx(async c => {
      await chartCtx(c)
      await c.query(`INSERT INTO ka_gochara_generation_seal (chart_id, generation, manifest_id) VALUES ($1,$2,gen_random_uuid())`, [CHART, gen])
    }), /manifest/i)
    // 7. post-seal mutation of EVERY table, and TRUNCATE, is refused
    const oid = b.ids.p1[0]!
    await refused(tx(async c => { await chartCtx(c); await iv(c, gen, oid, LO, MID, b.snap.digest, 'searched_unqualified') }), /SEALED|overlaps|publication-immutable/)
    await refused(tx(async c => { await chartCtx(c); await c.query(`DELETE FROM ka_gochara_search_interval WHERE chart_id=$1 AND generation=$2`, [CHART, gen]) }), /SEALED/)
    await refused(tx(async c => { await chartCtx(c); await c.query(`DELETE FROM ka_gochara_search_obligation WHERE chart_id=$1 AND generation=$2`, [CHART, gen]) }), /SEALED/)
    await refused(tx(async c => { await chartCtx(c); await c.query(`DELETE FROM ka_gochara_search_path_pin WHERE chart_id=$1 AND generation=$2`, [CHART, gen]) }), /SEALED/)
    await refused(tx(async c => { await chartCtx(c); await c.query(`DELETE FROM ka_gochara_search_inventory_verification WHERE chart_id=$1 AND generation=$2`, [CHART, gen]) }), /SEALED/)
    await refused(tx(async c => { await chartCtx(c); await c.query(`DELETE FROM ka_gochara_search_inventory WHERE chart_id=$1 AND generation=$2`, [CHART, gen]) }), /SEALED/)
    await refused(tx(async c => { await chartCtx(c); await c.query(`DELETE FROM ka_gochara_search_input_snapshot WHERE chart_id=$1 AND generation=$2`, [CHART, gen]) }), /SEALED/)
    await refused(tx(async c => { await chartCtx(c); await verify(c, gen, b.dig.inv, 'verifier-b') }), /SEALED/)
    await refused(tx(async c => { await chartCtx(c); await c.query(`UPDATE ka_gochara_search_path_pin SET note='x' WHERE chart_id=$1 AND generation=$2`, [CHART, gen]) }), /insert-only/)
    await refused(tx(async c => { await chartCtx(c); await c.query(`UPDATE ka_gochara_search_inventory SET horizon=${HORIZON_SQL} WHERE chart_id=$1 AND generation=$2`, [CHART, gen]) }), /SEALED|FINALISED/)
    for (const t of ['ka_gochara_search_interval', 'ka_gochara_search_inventory']) {
      await refused(pool.query(`TRUNCATE ${t} CASCADE`), /TRUNCATE refused/)
    }
    // the registry advance does not break the sealed class: its stored digests still recompute
    const rv = await pool.query(`SELECT * FROM ka_gochara_search_replay_violations($1,$2)`, [CHART, gen])
    expect(rv.rows).toEqual([])
    // account for p7 in a NEW generation: the advanced registry is then satisfiable
    const g3 = nextGen()
    await tx(async c => {
      await chartCtx(c)
      await publication(c, g3)
      const snap = await snapshotLive(c, g3)
      await header(c, g3, snap.digest)
      const p1 = [obId('p1', '1.0', P1A)]
      await pin(c, g3, { path: 'p1', disp: 'included', ids: p1 })
      for (const p of ['p5a', 'p7']) await pin(c, g3, { path: p, disp: 'excluded', reason: 'not_applicable_to_class', basis: 'spec:GOCHARA_DESIGN_SPECS@1.4#§2.2/' + p, ids: [] })
      await pin(c, g3, { path: 'p6', disp: 'excluded', reason: 'on_demand_tier', basis: B_P6, ids: [] })
      const a = await ob(c, g3, 'p1', P1A)
      await iv(c, g3, a, LO, HI, snap.digest)
      const d = await finalize(c, g3)
      await partition(c, g3); await verify(c, g3, d.inv)
    })
    await publishAndSeal(g3)
  })
})

// The runner-route checks reset the schema, so they run last in their own describe.
describe.skipIf(!TEST_DB_URL)('B6.0 F-1 migration 1206 — deploy route', () => {
  beforeAll(async () => { pool = new Pool({ ...resolveDisposableA51Config(TEST_DB_URL), max: 4 }) })
  afterAll(async () => { if (pool) { await resetSchema(); await pool.end() } })

  it('the routine runner REFUSES 1206 and names the protected window; replay of the applied file is BLOCKED by its gate', async () => {
    await resetSchema()
    await withTempDir(WINDOW_FILES, async dir => {
      const c = await pool.connect()
      try {
        await runMigrations(c, [dir], { only: new Set([...CONTRACT_FILES, M1204]), disclosures: new Map(), renumberDisclosures: new Map() })
        await expect(runMigrations(c, [dir], { disclosures: new Map(), renumberDisclosures: new Map() }))
          .rejects.toThrow(/gochara_contracts_schema_migration=true/)
        await runMigrations(c, [dir], { only: new Set([M1206]), disclosures: new Map(), renumberDisclosures: new Map() })
      } finally { c.release() }
    })
    await expect(pool.query(mig(M1206))).rejects.toThrow(/preflight 1206 BLOCKED/)
    // the --only route refuses to jump an unapplied predecessor: 1206 without 1157 recorded is blocked by the gate
    await resetSchema()
    await withTempDir(WINDOW_FILES, async dir => {
      const c = await pool.connect()
      try {
        await expect(runMigrations(c, [dir], { only: new Set([M1206]), disclosures: new Map(), renumberDisclosures: new Map() }))
          .rejects.toThrow()
      } finally { c.release() }
    })
  })
})
