// @vitest-environment node
/**
 * Packet B2 ("the DAG-derived downstream count") — LIVE-DB proof for the SQL that
 * platform/src/app/api/cockpit/stats/route.ts runs to fill
 * AssetStats.downstream_dependent_count (DOWNSTREAM_DEPENDENTS_SQL in
 * src/lib/cockpit/downstreamDependents.ts — a recursive CTE over
 * asset_registry.asset_id / depends_on / is_active; NO database view, NO
 * migration: the migration login has no CREATE on schema public, so the
 * original CREATE VIEW migration 1202 was dropped and the query moved into the
 * route). This suite imports the SAME exported SQL text the route sends, so a
 * drift in the route's query cannot hide behind a hand-copied stand-in.
 *
 * Before-measurement: 00_ARCHITECTURE/briefs/nirmana/engine/measurements/
 * B2_before_20260926T173944Z.json — a recursive CTE and an independent Python BFS
 * over depends_on agreed exactly on every one of the 129 production assets.
 *
 * C-1 (review B2_review_20260926T202916Z.md) — an UNFILTERED closure counted two
 * inactive leaves (which still themselves depend on active assets) as downstream
 * dependents, inflating 13 real ancestors' counts by 1-2: ga_positions read 80,
 * where plan.ts's computeDownstreamClosure() over the is_active-filtered registry
 * production feeds it says 79. The shipped query is the FILTERED one (79). This
 * suite proves that THREE ways:
 *   (a) a synthetic fixture with an inactive dependent AND an active asset beyond
 *       an inactive one (severance), against exact hand-derived counts;
 *   (b) the query over the REAL 129-row production registry (frozen export,
 *       read-only, 2026-09-27 — fixtures/b2_real_registry_20260927.json) against
 *       a fresh independent JS BFS over that same data, and the headline figure
 *       ga_positions = 79 (the same registry, unfiltered, gives the historical 80,
 *       asserted here too so the 80-vs-79 story is a measured fact, not a claim);
 *   (c) the same real data against the REAL, exported computeDownstreamClosure()
 *       from plan.ts, over the is_active-filtered population.
 *
 * C-3 — `UNION` -> `UNION ALL` in the closure CTE stays green on counts (the outer
 * count(DISTINCT ...) absorbs the duplication) yet exhausts a 512 MB
 * temp_file_limit in ~3 s on the real graph. The detector below runs the
 * ACTUAL exported DOWNSTREAM_CLOSURE_CTE text and asserts at most one closure row
 * per (dependent, upstream) pair — true under UNION, false under UNION ALL on any
 * diamond (the synthetic fixture and the real registry both have one). It fails on
 * SEMANTICS, not on a resource limit.
 *
 * Cycles: `UNION` is also what terminates a cycle in depends_on. A separate
 * fixture (a <-> b, c downstream of a) proves the query terminates, counts each
 * asset once, and never counts an asset as its own dependent.
 *
 * "A test that fails if the query drifts": every assertion compares the query's
 * live output to a same-run independent recomputation or to an exact hand-derived
 * count, never to a number read back from the query itself.
 *
 * Requires a THROWAWAY database (same one-throwaway-db-per-suite pattern as
 * tests/integration/watchdog_failure_attribution.db.test.ts — run this file
 * alone locally). It creates and drops a table named asset_registry, so it
 * refuses to run against any database not named `downstream_dependents_test`.
 * NEVER point it at production.
 *
 *   createdb -h 127.0.0.1 -p 55432 -U postgres downstream_dependents_test
 *   DOWNSTREAM_DEPENDENTS_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/downstream_dependents_test \
 *     npx vitest run tests/integration/downstream_dependents.db.test.ts
 *
 * Skipped unless DOWNSTREAM_DEPENDENTS_TEST_DATABASE_URL is set (CI wiring:
 * job `db-integration-tests`; its two CI steps — create the throwaway database, run
 * this suite — are part of this PR in .github/workflows/ci.yml).
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { Pool } from 'pg'
import { computeDownstreamClosure, type RegistryEntry } from '@/lib/build/plan'
import { DOWNSTREAM_CLOSURE_CTE, DOWNSTREAM_DEPENDENTS_SQL } from '@/lib/cockpit/downstreamDependents'

const HERE = path.dirname(fileURLToPath(import.meta.url))

interface RealRegistryRow { asset_id: string; is_active: boolean; depends_on: string[] }

const REAL_REGISTRY: RealRegistryRow[] = JSON.parse(
  fs.readFileSync(path.join(HERE, 'fixtures/b2_real_registry_20260927.json'), 'utf8')
)

const TEST_DB_URL = process.env.DOWNSTREAM_DEPENDENTS_TEST_DATABASE_URL

let pool: Pool

/**
 * Database-name guard: this suite runs `DROP TABLE asset_registry CASCADE`, so the URL
 * must be unmistakably a disposable local database. A bare substring regex over the whole
 * URL (the original guard) matched anywhere — e.g. `?note=downstream_dependents_test` on a
 * production URL — so this parses the URL and requires BOTH the exact database path and a
 * loopback host.
 */
export function isSafeTestDbUrl(raw: string): boolean {
  let u: URL
  try {
    u = new URL(raw)
  } catch {
    return false
  }
  // WHATWG URL keeps the brackets on an IPv6 literal hostname.
  const loopback = u.hostname === '127.0.0.1' || u.hostname === 'localhost' || u.hostname === '[::1]'
  return loopback && u.pathname === '/downstream_dependents_test'
}

/**
 * Independent recomputation — a THIRD implementation, deliberately not a call into
 * plan.ts's computeDownstreamClosure and not a copy of the route's recursive
 * CTE. A plain reverse-adjacency BFS: for each asset, expand the frontier of
 * everything that lists it (directly or transitively) as an upstream dependency.
 * `is_active` is honoured on BOTH sides, mirroring the shipped query: an
 * inactive asset never seeds/propagates (excluded from `dependents`' source
 * rows) and never receives a result row (excluded from the final iteration).
 */
function independentDownstreamCounts(
  registry: { asset_id: string; depends_on: string[]; is_active: boolean }[]
): Map<string, number> {
  const activeRegistry = registry.filter(r => r.is_active)
  // Reverse adjacency: upstream -> [ACTIVE assets that directly depend on it]
  const dependents = new Map<string, string[]>()
  for (const r of activeRegistry) {
    for (const dep of r.depends_on) {
      if (!dependents.has(dep)) dependents.set(dep, [])
      dependents.get(dep)!.push(r.asset_id)
    }
  }

  const result = new Map<string, number>()
  for (const r of activeRegistry) {
    const seen = new Set<string>()
    const queue = [...(dependents.get(r.asset_id) ?? [])]
    while (queue.length > 0) {
      const next = queue.shift()!
      if (next === r.asset_id || seen.has(next)) continue
      seen.add(next)
      for (const d of dependents.get(next) ?? []) {
        if (!seen.has(d) && d !== r.asset_id) queue.push(d)
      }
    }
    result.set(r.asset_id, seen.size)
  }
  return result
}

// A synthetic DAG, not production's 129-asset registry (this suite proves the
// VIEW'S ALGORITHM on a controlled shape; the real-data cross-check below
// proves it against the actual population). Deliberately includes:
//   - two independent roots (root_a, root_b)
//   - a DIAMOND CONVERGENCE (diamond_join depends on both mid_1 AND mid_2, which
//     both depend on root_a) — the exact shape that (a) blew a naive
//     path-tracking CTE's temp_file_limit in the before-measurement, and (b) is
//     what C-3's UNION-ALL detector below needs to have something to detect.
//   - a leaf with NO dependents at all (leaf_no_deps) — proves the honest-zero
//     path.
//   - a final sink two hops below the diamond AND below a separate branch.
//   - C-1: an INACTIVE dependent (inactive_dependent, is_active=false) that
//     itself depends on root_b — mirroring the real bug exactly (an inactive
//     leaf that depends on an active asset must never inflate that asset's
//     count, and must never receive a count of its own).
const FIXTURE: { asset_id: string; depends_on: string[]; is_active: boolean }[] = [
  { asset_id: 'root_a', depends_on: [], is_active: true },
  { asset_id: 'root_b', depends_on: [], is_active: true },
  { asset_id: 'mid_1', depends_on: ['root_a'], is_active: true },
  { asset_id: 'mid_2', depends_on: ['root_a'], is_active: true },
  { asset_id: 'mid_3', depends_on: ['root_b'], is_active: true },
  { asset_id: 'diamond_join', depends_on: ['mid_1', 'mid_2'], is_active: true },
  { asset_id: 'leaf_no_deps', depends_on: [], is_active: true },
  { asset_id: 'final', depends_on: ['diamond_join', 'mid_3'], is_active: true },
  { asset_id: 'inactive_dependent', depends_on: ['root_b'], is_active: false },
  // B2-R-1 (reviewer-specified, bound to the commit): an ACTIVE asset sitting BEYOND
  // an inactive one. Without this row nothing in the suite distinguishes severance
  // from non-severance — the axis the whole C-1 correction turns on — because both
  // live inactive assets are pure sinks and no such path exists in production. The
  // file's own BFS already severs, so no test logic changes; this row alone makes
  // the non-severing variant fail.
  { asset_id: 'beyond_inactive', depends_on: ['inactive_dependent'], is_active: true },
]

type Row = { asset_id: string; is_active?: boolean; depends_on: string[] }

const CYCLE_FIXTURE: { asset_id: string; depends_on: string[]; is_active: boolean }[] = [
  // a <-> b is a 2-cycle; c hangs off a; d joins c and b (a diamond INSIDE the cycle's reach).
  { asset_id: 'a', depends_on: ['b'], is_active: true },
  { asset_id: 'b', depends_on: ['a'], is_active: true },
  { asset_id: 'c', depends_on: ['a'], is_active: true },
  { asset_id: 'd', depends_on: ['c', 'b'], is_active: true },
]

describe('isSafeTestDbUrl — the destructive-test database guard', () => {
  it('accepts the CI URL and the scratch-cluster URL', () => {
    expect(isSafeTestDbUrl('postgresql://postgres:postgres@localhost:5432/downstream_dependents_test')).toBe(true)
    expect(isSafeTestDbUrl('postgresql://postgres@127.0.0.1:55432/downstream_dependents_test')).toBe(true)
    expect(isSafeTestDbUrl('postgresql://postgres@[::1]:5432/downstream_dependents_test')).toBe(true)
  })

  it('refuses a URL carrying the name only in the query string (production URL + ?note=...)', () => {
    expect(isSafeTestDbUrl('postgresql://u:p@127.0.0.1:5432/postgres?application_name=downstream_dependents_test')).toBe(false)
    expect(isSafeTestDbUrl('postgresql://u:p@prod-db.example.com:5432/postgres?options=downstream_dependents_test')).toBe(false)
  })

  it('refuses a non-loopback host even with the right database name', () => {
    expect(isSafeTestDbUrl('postgresql://u:p@prod-db.example.com:5432/downstream_dependents_test')).toBe(false)
    expect(isSafeTestDbUrl('postgresql://u:p@10.0.0.5:5432/downstream_dependents_test')).toBe(false)
    // a hostname that merely CONTAINS a loopback name
    expect(isSafeTestDbUrl('postgresql://u:p@localhost.evil.example.com:5432/downstream_dependents_test')).toBe(false)
  })

  it('refuses a different or longer database path, and unparseable input', () => {
    expect(isSafeTestDbUrl('postgresql://u@127.0.0.1:5432/downstream_dependents_test_prod')).toBe(false)
    expect(isSafeTestDbUrl('postgresql://u@127.0.0.1:5432/x/downstream_dependents_test')).toBe(false)
    expect(isSafeTestDbUrl('postgresql://u@127.0.0.1:5432/downstream_dependents_test/')).toBe(false)
    expect(isSafeTestDbUrl('not a url downstream_dependents_test')).toBe(false)
    expect(isSafeTestDbUrl('')).toBe(false)
  })
})

describe.skipIf(!TEST_DB_URL)('downstream-dependents query (stats route SQL) — B2 live-DB proof', () => {
  /** Runs the route's exact SQL (optionally wrapped for ordering/filtering by the test). */
  async function runRouteSql(suffix = '', sql: string = DOWNSTREAM_DEPENDENTS_SQL) {
    const { rows } = await pool.query<{ asset_id: string; downstream_dependent_count: string }>(
      `SELECT asset_id, downstream_dependent_count FROM (${sql}) t ${suffix}`
    )
    return new Map(rows.map(r => [r.asset_id, Number(r.downstream_dependent_count)]))
  }

  async function load(rows: Row[]) {
    await pool.query('TRUNCATE asset_registry')
    for (const r of rows) {
      await pool.query(
        'INSERT INTO asset_registry (asset_id, depends_on, is_active) VALUES ($1, $2, $3)',
        [r.asset_id, r.depends_on, r.is_active ?? true]
      )
    }
  }

  beforeAll(async () => {
    if (!isSafeTestDbUrl(TEST_DB_URL!)) {
      throw new Error(
        'DOWNSTREAM_DEPENDENTS_TEST_DATABASE_URL must point at a disposable LOOPBACK database named ' +
          '`downstream_dependents_test` (host 127.0.0.1/localhost/::1, path exactly ' +
          '/downstream_dependents_test). This suite creates and drops an asset_registry table and ' +
          'must never run against production.'
      )
    }

    // statement_timeout: a regression that makes the closure CTE non-terminating (UNION ALL
    // over the a <-> b cycle) must be STOPPED BY POSTGRES and surface as a fast query error,
    // not as a vitest timeout that abandons a runaway recursion still running in the backend
    // (which then blocks every later TRUNCATE in this suite). Healthy queries here take ms.
    pool = new Pool({ connectionString: TEST_DB_URL, statement_timeout: 3000 })

    // Only the three asset_registry columns the query reads. No view, no role, no GRANT:
    // the query is plain SELECT text sent by the route, so there is no DDL to prove.
    await pool.query(`
      DROP TABLE IF EXISTS asset_registry CASCADE;

      CREATE TABLE asset_registry (
        asset_id     text PRIMARY KEY,
        depends_on   text[] NOT NULL DEFAULT ARRAY[]::text[],
        is_active    boolean NOT NULL DEFAULT true
      );
    `)
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query('DROP TABLE IF EXISTS asset_registry CASCADE')
    await pool.end()
  })

  it('synthetic DAG: exact hand-derived counts (diamond counted once, leaf a real 0, inactive severed)', async () => {
    await load(FIXTURE)
    const got = await runRouteSql()
    expect(Object.fromEntries(got)).toEqual({
      root_a: 4, // mid_1, mid_2, diamond_join, final — NOT 5 (diamond_join is reachable two ways)
      root_b: 2, // mid_3, final — inactive_dependent and the active asset beyond it (beyond_inactive) excluded
      mid_1: 2, // diamond_join, final
      mid_2: 2,
      mid_3: 1, // final
      diamond_join: 1, // final
      final: 0,
      leaf_no_deps: 0, // a real, present 0 — never a missing row
      beyond_inactive: 0,
      // inactive_dependent: deliberately absent — never a rebuild target
    })
  })

  it('agrees exactly with an independent JS BFS over the same DAG, for every ACTIVE asset', async () => {
    await load(FIXTURE)
    const got = await runRouteSql()
    const bfsMap = independentDownstreamCounts(FIXTURE)
    const activeFixture = FIXTURE.filter(r => r.is_active)
    expect(got.size).toBe(activeFixture.length)
    for (const r of activeFixture) {
      expect(got.get(r.asset_id), `mismatch for ${r.asset_id}`).toBe(bfsMap.get(r.asset_id))
    }
  })

  it('C-1: an inactive dependent never inflates its active ancestor\'s count, never gets a row of its own, and severs the chain beyond it', async () => {
    await load(FIXTURE)
    const got = await runRouteSql()
    expect(got.get('root_b')).toBe(2)
    expect(got.has('inactive_dependent')).toBe(false)
    expect(got.get('beyond_inactive')).toBe(0)
  })

  it('every ACTIVE registry row has a result row, and no INACTIVE row does', async () => {
    await load(FIXTURE)
    const got = await runRouteSql()
    expect(new Set(got.keys())).toEqual(new Set(FIXTURE.filter(r => r.is_active).map(r => r.asset_id)))
  })

  it('an empty registry yields no rows (the route then reads null for every asset, never a fabricated 0)', async () => {
    await load([])
    expect((await runRouteSql()).size).toBe(0)
  })

  it('CYCLE: a <-> b terminates (UNION), counts each asset once, and never counts an asset as its own dependent', async () => {
    await load(CYCLE_FIXTURE)
    const got = await runRouteSql()
    expect(Object.fromEntries(got)).toEqual({
      a: 3, // b, c, d — NOT a itself, though a is reachable from itself via b
      b: 3, // a, c (via a), d
      c: 1, // d
      d: 0,
    })
    // And it agrees with the independent BFS (which excludes the seed by construction).
    const bfs = independentDownstreamCounts(CYCLE_FIXTURE)
    for (const r of CYCLE_FIXTURE) expect(got.get(r.asset_id)).toBe(bfs.get(r.asset_id))
  })

  it('C-3: the closure has at most one row per (dependent, upstream) pair — the UNION-ALL detector', async () => {
    await load(FIXTURE)
    // Each detector query runs in its own transaction under SET LOCAL statement_timeout so a
    // non-terminating CTE is cancelled by the backend itself (2 s), never by the test timeout.
    const runTimed = async <T extends Record<string, unknown>>(sql: string) => {
      const client = await pool.connect()
      try {
        await client.query('BEGIN')
        await client.query("SET LOCAL statement_timeout = '2s'")
        const res = await client.query<T>(sql)
        await client.query('COMMIT')
        return res.rows
      } catch (err) {
        await client.query('ROLLBACK').catch(() => {})
        throw err
      } finally {
        client.release()
      }
    }
    const detector = () =>
      runTimed<{ dependent: string; upstream: string; n: string }>(
        `${DOWNSTREAM_CLOSURE_CTE}
         SELECT dependent, upstream, count(*) AS n
         FROM closure
         GROUP BY dependent, upstream
         HAVING count(*) > 1`
      )
    const rows = await detector()
    expect(rows, `duplicate (dependent, upstream) pairs found: ${JSON.stringify(rows)}`).toEqual([])

    // Prove the detector CAN fail: the same CTE with UNION ALL over a diamond must
    // report duplicates (otherwise this test would be a green light with no detector
    // behind it, the exact §N.8 defect this suite exists to prevent).
    expect(DOWNSTREAM_CLOSURE_CTE).toMatch(/\bUNION\b(?!\s+ALL)/)
    const dup = await runTimed(
      `${DOWNSTREAM_CLOSURE_CTE.replace(/\bUNION\b/, 'UNION ALL')}
       SELECT dependent, upstream FROM closure GROUP BY dependent, upstream HAVING count(*) > 1`
    )
    expect(dup.length).toBeGreaterThan(0)
  })

  it('C-1 + reuse: over the REAL 129-row production registry, agrees on every one of the 127 active assets with the REAL computeDownstreamClosure() from plan.ts and the independent BFS', async () => {
    await load(REAL_REGISTRY)
    const got = await runRouteSql()

    const activeRows = REAL_REGISTRY.filter(r => r.is_active)
    expect(REAL_REGISTRY.length).toBe(129)
    expect(activeRows.length).toBe(127)
    expect(got.size).toBe(127)

    // The REAL, imported plan.ts function — not a reimplementation — given EXACTLY
    // the population runs/route.ts feeds it (is_active=true only).
    const planRegistry: RegistryEntry[] = activeRows.map(r => ({
      asset_id: r.asset_id, layer: 'test', depends_on: r.depends_on, estimated_seconds: null,
    }))
    const bfs = independentDownstreamCounts(REAL_REGISTRY)

    const mismatches: string[] = []
    for (const r of activeRows) {
      const planCount = computeDownstreamClosure([r.asset_id], planRegistry).size
      const sqlCount = got.get(r.asset_id)
      if (planCount !== sqlCount || bfs.get(r.asset_id) !== sqlCount) {
        mismatches.push(`${r.asset_id}: plan=${planCount} bfs=${bfs.get(r.asset_id)} sql=${sqlCount}`)
      }
    }
    expect(mismatches, `disagreements: ${mismatches.join(', ')}`).toEqual([])
  })

  it('C-1: the three named category flips (0 -> fabricated 1) read a real 0 — "no downstream impact", not a phantom rebuild target', async () => {
    await load(REAL_REGISTRY)
    const got = await runRouteSql("WHERE asset_id IN ('bg_sky_calendar', 'ka_kota_chakra', 'ka_tithi_pravesha')")
    expect(Object.fromEntries(got)).toEqual({ bg_sky_calendar: 0, ka_kota_chakra: 0, ka_tithi_pravesha: 0 })
  })

  it('the top-5 over the real production registry: ga_positions = 79 (the historical "80" is the UNFILTERED figure, reproduced below), the other four unchanged', async () => {
    await load(REAL_REGISTRY)
    const { rows } = await pool.query<{ asset_id: string; downstream_dependent_count: string }>(
      `SELECT asset_id, downstream_dependent_count FROM (${DOWNSTREAM_DEPENDENTS_SQL}) t
        ORDER BY downstream_dependent_count DESC, asset_id ASC LIMIT 5`
    )
    expect(rows.map(r => [r.asset_id, Number(r.downstream_dependent_count)])).toEqual([
      ['ga_positions', 79],
      ['bg_ontology', 69],
      ['bg_reference', 62],
      ['ga_dashas', 61],
      ['ga_vargas', 61],
    ])
  })

  it('reproduces the historical 80 for ga_positions with the is_active filters REMOVED — proving the 80-vs-79 gap is exactly the C-1 inactive-leaf inflation, not a different algorithm', async () => {
    await load(REAL_REGISTRY)
    const unfiltered = DOWNSTREAM_DEPENDENTS_SQL
      .replace('WHERE is_active = true', 'WHERE true')
      .replace('WHERE ar.is_active = true', 'WHERE true')
    expect(unfiltered).not.toBe(DOWNSTREAM_DEPENDENTS_SQL)
    expect(unfiltered).not.toMatch(/is_active/)
    const got = await runRouteSql("WHERE asset_id = 'ga_positions'", unfiltered)
    expect(got.get('ga_positions')).toBe(80)
  })
})
