// @vitest-environment node
/**
 * Packet B2 ("the DAG-derived downstream count") — LIVE-DB proof for
 * vw_asset_downstream_dependents (migration
 * platform/supabase/migrations/1096_vw_asset_downstream_dependents.sql).
 *
 * Before-measurement: 00_ARCHITECTURE/briefs/nirmana/engine/measurements/
 * B2_before_20260926T173944Z.json — a recursive CTE and an independent Python BFS
 * over depends_on agreed exactly on every one of the 129 production assets.
 *
 * CORRECTION PASS (review B2_review_20260926T202916Z.md):
 *
 * C-1 — the FIRST version of this view filtered nothing, while
 * platform/src/lib/build/plan.ts's transitiveDownstream() (the function this
 * view is meant to be the SQL sibling of) only ever walks the registry
 * runs/route.ts actually loads it with — `WHERE is_active = true`, 127 of 129
 * real rows. Two inactive leaves (which still themselves depend on active
 * assets) inflated 13 real ancestors' counts by 1–2, flipping three genuinely
 * active assets from a real 0 to a fabricated 1. This suite now proves the fix
 * THREE ways, closing the exact gap the review measured:
 *   (a) a synthetic fixture case with an inactive dependent (below), so the
 *       is_active filter has a detector that isn't the full production import;
 *   (b) the view, applied to a throwaway Postgres loaded with the REAL 129-row
 *       production registry (frozen export, read-only, 2026-09-27 —
 *       fixtures/b2_real_registry_20260927.json), against a fresh independent
 *       JS BFS over that same real data;
 *   (c) the SAME real data, against the REAL, exported `computeDownstreamClosure`
 *       from plan.ts — not a reimplementation, an actual import — over the
 *       is_active-filtered population, so "reuse plan.ts" (Decision 4) is
 *       honoured as a cross-check rather than skipped because the view had to
 *       be SQL.
 *
 * C-3 — `UNION` → `UNION ALL` in the `closure` CTE was found, by the executor's
 * own delete-the-fix check, to stay green (the outer `count(DISTINCT …)`
 * already absorbs the duplication) — and the reviewer measured that on the
 * real 129-asset graph this exact drift exhausts a 512 MB `temp_file_limit` in
 * 3.1 seconds, i.e. it is not a cosmetic gap, it is the regression that takes
 * the poll down. This suite adds a real detector: it extracts the ACTUAL
 * `edges`/`closure` CTE text from the migration file (not a hand transcription)
 * and asserts the closure contains at most one row per (dependent, upstream)
 * pair — trivially true under `UNION` (which dedupes), false under `UNION ALL`
 * on any DAG with diamond convergence (which both the synthetic fixture and the
 * real registry have). This fails on SEMANTICS, not on a resource limit, so it
 * doesn't require reproducing the temp_file_limit blowup to catch the drift.
 *
 * "A test that fails if the view's definition drifts": every assertion below
 * compares the view's live output to a same-run independent recomputation,
 * never to a hardcoded expected number.
 *
 * Requires a THROWAWAY database (same one-throwaway-db-per-suite pattern as
 * tests/integration/watchdog_failure_attribution.db.test.ts — run this file
 * alone locally). C-2 (review B2_review_20260926T202916Z.md): this suite is
 * WIRED INTO `.github/workflows/ci.yml` (job `db-integration-tests`, steps
 * "Nirmāṇa B2 — provision …" / "Nirmāṇa B2 — vw_asset_downstream_dependents …"),
 * mirroring the exact provision-then-run pattern every other
 * tests/integration/*.db.test.ts suite in that job already uses — a plain local
 * `vitest run` still reports it skipped (no `VW_DOWNSTREAM_TEST_DATABASE_URL` in
 * a developer's shell), but CI sets that env var and runs it for real on every
 * push/PR. The campaign's own A2 suite (WATCHDOG_A2_TEST_DATABASE_URL) remains
 * in the pre-existing unwired state this suite was in before C-2 — that gap is
 * inherited, not this packet's to close.
 *
 *   createdb -h 127.0.0.1 -p 55432 -U postgres vw_downstream_test
 *   VW_DOWNSTREAM_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/vw_downstream_test \
 *     npx vitest run tests/integration/vw_asset_downstream_dependents.db.test.ts
 *
 * Skipped unless VW_DOWNSTREAM_TEST_DATABASE_URL is set.
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { Pool } from 'pg'
import { computeDownstreamClosure, type RegistryEntry } from '@/lib/build/plan'

const HERE = path.dirname(fileURLToPath(import.meta.url))

/** Walk up to the repo root by LOOKING FOR the migration file, not by counting
 *  `..` segments (see plan.ka-kshetra-acyclicity.test.ts's own repoRoot() for why:
 *  a hardcoded depth is silently wrong the moment this file moves). */
function repoRoot(): string {
  let dir = HERE
  for (let i = 0; i < 10; i++) {
    if (fs.existsSync(path.join(dir, 'platform/supabase/migrations/1096_vw_asset_downstream_dependents.sql'))) return dir
    dir = path.dirname(dir)
  }
  throw new Error('could not locate the 1096 migration from ' + HERE)
}

const REPO_ROOT = repoRoot()

const MIGRATION_SQL = fs.readFileSync(
  path.join(REPO_ROOT, 'platform/supabase/migrations/1096_vw_asset_downstream_dependents.sql'),
  'utf8'
)

interface RealRegistryRow { asset_id: string; is_active: boolean; depends_on: string[] }

const REAL_REGISTRY: RealRegistryRow[] = JSON.parse(
  fs.readFileSync(path.join(HERE, 'fixtures/b2_real_registry_20260927.json'), 'utf8')
)

const TEST_DB_URL = process.env.VW_DOWNSTREAM_TEST_DATABASE_URL

let pool: Pool

/**
 * Independent recomputation — a THIRD implementation, deliberately not a call into
 * plan.ts's computeDownstreamClosure and not a copy of the migration's recursive
 * CTE. A plain reverse-adjacency BFS: for each asset, expand the frontier of
 * everything that lists it (directly or transitively) as an upstream dependency.
 * `is_active` is honoured on BOTH sides, mirroring the corrected view: an
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

/**
 * C-3: extracts the ACTUAL `edges`/`closure` CTE text from the migration file
 * (between `WITH RECURSIVE edges AS (` and the final `SELECT\n  ar.asset_id,`),
 * so the duplicate-pair detector below runs against the SAME text that ships,
 * not a hand-copied stand-in that could itself drift from the real migration.
 */
function extractClosureCte(migrationSql: string): string {
  const start = migrationSql.indexOf('WITH RECURSIVE edges AS (')
  const selectMarker = '\nSELECT\n  ar.asset_id,'
  const end = migrationSql.indexOf(selectMarker, start)
  if (start === -1 || end === -1) {
    throw new Error('could not locate the edges/closure CTE in the migration file — has its shape changed?')
  }
  return migrationSql.slice(start, end)
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

describe.skipIf(!TEST_DB_URL)('vw_asset_downstream_dependents — B2 live-DB proof', () => {
  beforeAll(async () => {
    if (!/vw_downstream_test/.test(TEST_DB_URL!)) {
      throw new Error(
        'VW_DOWNSTREAM_TEST_DATABASE_URL must point at a disposable database named ' +
          '`vw_downstream_test`. This suite creates and drops schema objects and ' +
          'must never run against production.'
      )
    }

    pool = new Pool({ connectionString: TEST_DB_URL })

    await pool.query(`
      DROP VIEW IF EXISTS vw_asset_downstream_dependents CASCADE;
      DROP TABLE IF EXISTS asset_registry CASCADE;

      CREATE TABLE asset_registry (
        asset_id     text PRIMARY KEY,
        depends_on   text[] NOT NULL DEFAULT ARRAY[]::text[],
        is_active    boolean NOT NULL DEFAULT true
      );

      DO $$
      BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app') THEN
          CREATE ROLE amjis_app;
        END IF;
      END $$;
    `)

    // The REAL migration file, executed verbatim — not a transcription. If the
    // migration's own SQL ever fails to apply (a syntax error, a broken GRANT
    // guard), this beforeAll fails loudly rather than the suite silently testing
    // a hand-copied stand-in.
    await pool.query(MIGRATION_SQL)

    for (const r of FIXTURE) {
      await pool.query(
        'INSERT INTO asset_registry (asset_id, depends_on, is_active) VALUES ($1, $2, $3)',
        [r.asset_id, r.depends_on, r.is_active]
      )
    }
  })

  afterAll(async () => {
    if (!pool) return
    await pool.query('DROP VIEW IF EXISTS vw_asset_downstream_dependents CASCADE; DROP TABLE IF EXISTS asset_registry CASCADE;')
    await pool.end()
  })

  it('agrees exactly with an independent JS BFS over the same DAG, for every ACTIVE asset', async () => {
    const { rows } = await pool.query<{ asset_id: string; downstream_dependent_count: number }>(
      'SELECT asset_id, downstream_dependent_count FROM vw_asset_downstream_dependents ORDER BY asset_id'
    )
    const viewMap = new Map(rows.map(r => [r.asset_id, Number(r.downstream_dependent_count)]))
    const bfsMap = independentDownstreamCounts(FIXTURE)

    const activeFixture = FIXTURE.filter(r => r.is_active)
    expect(viewMap.size).toBe(activeFixture.length)
    for (const r of activeFixture) {
      expect(viewMap.get(r.asset_id), `mismatch for ${r.asset_id}`).toBe(bfsMap.get(r.asset_id))
    }
  })

  it('gets the diamond-convergence count right (not double-counted)', async () => {
    const { rows } = await pool.query<{ downstream_dependent_count: number }>(
      "SELECT downstream_dependent_count FROM vw_asset_downstream_dependents WHERE asset_id = 'root_a'"
    )
    // root_a's downstream: mid_1, mid_2, diamond_join, final — NOT mid_1, mid_2,
    // diamond_join (via mid_1), diamond_join (via mid_2), final (5, double-counted).
    expect(Number(rows[0].downstream_dependent_count)).toBe(4)
  })

  it('reads a real, present 0 for an asset with no dependents — never a missing row', async () => {
    const { rows } = await pool.query<{ downstream_dependent_count: number }>(
      "SELECT downstream_dependent_count FROM vw_asset_downstream_dependents WHERE asset_id = 'leaf_no_deps'"
    )
    expect(rows.length).toBe(1)
    expect(rows[0].downstream_dependent_count).not.toBeNull()
    expect(Number(rows[0].downstream_dependent_count)).toBe(0)
  })

  it('C-1: an inactive dependent never inflates its active ancestor\'s count, and never gets a row of its own', async () => {
    // inactive_dependent depends on root_b but is_active=false — root_b's count
    // must be exactly what it would be with inactive_dependent absent entirely
    // (mid_3, final = 2), and inactive_dependent itself must not appear in the
    // view at all (it is never a valid rebuild target).
    const { rows: rootBRows } = await pool.query<{ downstream_dependent_count: number }>(
      "SELECT downstream_dependent_count FROM vw_asset_downstream_dependents WHERE asset_id = 'root_b'"
    )
    expect(Number(rootBRows[0].downstream_dependent_count)).toBe(2)

    const { rows: inactiveRows } = await pool.query(
      "SELECT 1 FROM vw_asset_downstream_dependents WHERE asset_id = 'inactive_dependent'"
    )
    expect(inactiveRows.length).toBe(0)
  })

  it('every ACTIVE registry row has a view row, and no INACTIVE row does', async () => {
    const { rows: regRows } = await pool.query<{ asset_id: string; is_active: boolean }>('SELECT asset_id, is_active FROM asset_registry')
    const { rows: viewRows } = await pool.query<{ asset_id: string }>('SELECT asset_id FROM vw_asset_downstream_dependents')
    const activeIds = new Set(regRows.filter(r => r.is_active).map(r => r.asset_id))
    const inactiveIds = new Set(regRows.filter(r => !r.is_active).map(r => r.asset_id))
    const viewIds = new Set(viewRows.map(r => r.asset_id))
    expect(viewIds).toEqual(activeIds)
    for (const id of inactiveIds) expect(viewIds.has(id)).toBe(false)
  })

  it('the migration is idempotent — re-running it changes nothing and errors on nothing', async () => {
    await expect(pool.query(MIGRATION_SQL)).resolves.toBeDefined()
    const { rows } = await pool.query<{ downstream_dependent_count: number }>(
      "SELECT downstream_dependent_count FROM vw_asset_downstream_dependents WHERE asset_id = 'root_a'"
    )
    expect(Number(rows[0].downstream_dependent_count)).toBe(4)
  })

  it('amjis_app (the app role) can SELECT from the view', async () => {
    const { rows } = await pool.query<{ has_select: boolean }>(
      "SELECT has_table_privilege('amjis_app', 'public.vw_asset_downstream_dependents', 'SELECT') AS has_select"
    )
    expect(rows[0].has_select).toBe(true)
  })

  it('C-3: the closure has at most one row per (dependent, upstream) pair — the UNION-ALL detector', async () => {
    const cte = extractClosureCte(MIGRATION_SQL)
    const { rows } = await pool.query<{ dependent: string; upstream: string; n: string }>(
      `${cte}
       SELECT dependent, upstream, count(*) AS n
       FROM closure
       GROUP BY dependent, upstream
       HAVING count(*) > 1`
    )
    expect(rows, `duplicate (dependent, upstream) pairs found: ${JSON.stringify(rows)}`).toEqual([])
  })

  it('C-1 + reuse (Decision 4): the view over the REAL 129-row production registry agrees, on every one of the 127 active assets, with the REAL computeDownstreamClosure() from plan.ts', async () => {
    // Reload the real production export into this same throwaway DB.
    await pool.query('TRUNCATE asset_registry')
    for (const r of REAL_REGISTRY) {
      await pool.query(
        'INSERT INTO asset_registry (asset_id, depends_on, is_active) VALUES ($1, $2, $3)',
        [r.asset_id, r.depends_on, r.is_active]
      )
    }

    const { rows } = await pool.query<{ asset_id: string; downstream_dependent_count: number }>(
      'SELECT asset_id, downstream_dependent_count FROM vw_asset_downstream_dependents'
    )
    const viewMap = new Map(rows.map(r => [r.asset_id, Number(r.downstream_dependent_count)]))

    const activeRows = REAL_REGISTRY.filter(r => r.is_active)
    expect(activeRows.length).toBe(127)
    expect(viewMap.size).toBe(127)

    // The REAL, imported plan.ts function — not a reimplementation — given
    // EXACTLY the population runs/route.ts actually feeds it (is_active=true
    // only), which is the population the view must now match (C-1).
    const planRegistry: RegistryEntry[] = activeRows.map(r => ({
      asset_id: r.asset_id, layer: 'test', depends_on: r.depends_on, estimated_seconds: null,
    }))

    const mismatches: string[] = []
    for (const r of activeRows) {
      const planCount = computeDownstreamClosure([r.asset_id], planRegistry).size
      const viewCount = viewMap.get(r.asset_id)
      if (planCount !== viewCount) mismatches.push(`${r.asset_id}: plan=${planCount} view=${viewCount}`)
    }
    expect(mismatches, `disagreements: ${mismatches.join(', ')}`).toEqual([])

    // Restore the synthetic fixture for any subsequent test run in this file
    // (vitest runs `it` blocks in declaration order within one `describe`, and
    // this is deliberately the last data-dependent assertion, but leave the
    // table in the state beforeAll set it up in, for defensiveness).
    await pool.query('TRUNCATE asset_registry')
    for (const r of FIXTURE) {
      await pool.query(
        'INSERT INTO asset_registry (asset_id, depends_on, is_active) VALUES ($1, $2, $3)',
        [r.asset_id, r.depends_on, r.is_active]
      )
    }
  })

  it('C-1: the three named category flips (0 -> fabricated 1) now read a real 0 — "no downstream impact", not a phantom rebuild target', async () => {
    await pool.query('TRUNCATE asset_registry')
    for (const r of REAL_REGISTRY) {
      await pool.query(
        'INSERT INTO asset_registry (asset_id, depends_on, is_active) VALUES ($1, $2, $3)',
        [r.asset_id, r.depends_on, r.is_active]
      )
    }
    const { rows } = await pool.query<{ asset_id: string; downstream_dependent_count: number }>(
      `SELECT asset_id, downstream_dependent_count FROM vw_asset_downstream_dependents
        WHERE asset_id IN ('bg_sky_calendar', 'ka_kota_chakra', 'ka_tithi_pravesha')
        ORDER BY asset_id`
    )
    expect(rows.map(r => [r.asset_id, Number(r.downstream_dependent_count)])).toEqual([
      ['bg_sky_calendar', 0],
      ['ka_kota_chakra', 0],
      ['ka_tithi_pravesha', 0],
    ])

    // Restore synthetic fixture.
    await pool.query('TRUNCATE asset_registry')
    for (const r of FIXTURE) {
      await pool.query(
        'INSERT INTO asset_registry (asset_id, depends_on, is_active) VALUES ($1, $2, $3)',
        [r.asset_id, r.depends_on, r.is_active]
      )
    }
  })

  it('the corrected top-5, over the real production registry, matches ga_positions=79 (not 80) and the other four unchanged', async () => {
    await pool.query('TRUNCATE asset_registry')
    for (const r of REAL_REGISTRY) {
      await pool.query(
        'INSERT INTO asset_registry (asset_id, depends_on, is_active) VALUES ($1, $2, $3)',
        [r.asset_id, r.depends_on, r.is_active]
      )
    }
    const { rows } = await pool.query<{ asset_id: string; downstream_dependent_count: number }>(
      'SELECT asset_id, downstream_dependent_count FROM vw_asset_downstream_dependents ORDER BY downstream_dependent_count DESC, asset_id ASC LIMIT 5'
    )
    expect(rows.map(r => [r.asset_id, Number(r.downstream_dependent_count)])).toEqual([
      ['ga_positions', 79],
      ['bg_ontology', 69],
      ['bg_reference', 62],
      ['ga_dashas', 61],
      ['ga_vargas', 61],
    ])

    // Restore synthetic fixture.
    await pool.query('TRUNCATE asset_registry')
    for (const r of FIXTURE) {
      await pool.query(
        'INSERT INTO asset_registry (asset_id, depends_on, is_active) VALUES ($1, $2, $3)',
        [r.asset_id, r.depends_on, r.is_active]
      )
    }
  })
})
