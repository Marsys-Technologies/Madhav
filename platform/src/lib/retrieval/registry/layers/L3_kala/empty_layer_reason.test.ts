/**
 * SR-EMPTY-REASON (CLAUDE.md §N.6 rule 4, §N.7.6): an empty Kāla convergence / obstruction layer is served with a named,
 * MEASURED empty_reason, never a bare [] that reads as "none".
 *  E1  each route, on an empty layer, names which of the four empties it is, from the counts it reads
 *  E2  a non-empty layer is unchanged (no reason, no extra probe)
 *  E3  a probe that cannot be read is an honest unreadable, never a guessed "none"
 *  E4  composeView names the reason PER SOURCE (one empty source beside a populated one used to be silent)
 *  E5  the SQL viewSql emits measures those counts (real SQL, gated by KALA_VIEW_DB_TESTS like the other real-SQL oracles)
 * Vocabulary and meaning: empty_layer_reason.ts.
 */
import { beforeEach, expect, it, vi } from 'vitest'
import { disposableSql } from './disposable_sql.test_support'

const db = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: db }))
beforeEach(() => { db.mockReset() }) // not `() => db.mockReset()`: a returned mock would be run by vitest as the teardown

type Probe = { any_rows: string; served_rows: string; asset_state: string | null }
/** Page and total queries return nothing; the layer-state probe (the only query naming asset_throughput) answers `probe`. */
function emptyLayer(probe: Probe | 'throw') {
  db.mockImplementation(async (sql: string) => {
    if (sql.includes('asset_throughput')) {
      if (probe === 'throw') throw new Error('probe down')
      return { rows: [probe] }
    }
    return { rows: sql.includes('COUNT(*)::text AS total') ? [{ total: '0' }] : [] }
  })
}

const routes = [
  { name: 'kala_convergence_get', rows: 'convergence_windows', asset: 'ka_sangam',
    load: async () => (await import('./query_convergence_windows')).queryConvergenceWindowsCapability },
  { name: 'kala_obstruction_get', rows: 'obstructions', asset: 'ka_vighnakara',
    load: async () => (await import('./query_obstruction_periods')).queryObstructionPeriodsCapability },
]

const states: [string, Probe, string][] = [
  ['nothing in any partition, asset not built', { any_rows: '0', served_rows: '0', asset_state: null }, 'layer_not_computed'],
  ['nothing in any partition, asset stale (not lit)', { any_rows: '0', served_rows: '0', asset_state: 'stale' }, 'layer_not_computed'],
  ['nothing in any partition, asset lit', { any_rows: '0', served_rows: '0', asset_state: 'lit' }, 'computed_found_none'],
  ['rows only in an unserved partition (a candidate)', { any_rows: '7', served_rows: '0', asset_state: 'lit' }, 'rows_outside_served_generation'],
  ['served rows exist, the filters drop them all', { any_rows: '7', served_rows: '5', asset_state: 'lit' }, 'filters_excluded_all_rows'],
]

for (const route of routes) {
  it.each(states)(`E1 ${route.name} on an empty layer: %s -> %s`, async (_label, probe, reason) => {
    emptyLayer(probe)
    const cap = await route.load()
    const result = await cap.handler!({ chart_id: 'chart-1', ...(route.name === 'kala_convergence_get' ? { domain: 'career' } : { severity: 'severe' }) }, {})
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content[route.rows]).toEqual([])
    expect(content.empty_reason).toBe(reason)
    // the claim is auditable: the measurements behind it are served beside it
    expect(content.layer_state).toMatchObject({ rows_any_partition: Number(probe.any_rows), rows_served_unfiltered: Number(probe.served_rows), asset_state: probe.asset_state })
    const probeCall = db.mock.calls.find(([sql]) => String(sql).includes('asset_throughput'))!
    expect(probeCall[1]).toEqual(['chart-1', route.asset])
  })

  it(`E2 ${route.name} on a non-empty layer is unchanged: no reason, no extra probe`, async () => {
    db.mockImplementation(async (sql: string) =>
      ({ rows: sql.includes('COUNT(*)::text AS total') ? [{ total: '1' }] : [{ id: 1, convergence_id: 1, signal_id: 's1' }] }))
    const cap = await route.load()
    const result = await cap.handler!({ chart_id: 'chart-1' }, {})
    const content = result.content as Record<string, unknown>
    expect(content[route.rows]).toHaveLength(1)
    expect(content.total_matching).toBe(1)
    expect(content.empty_reason).toBeNull()
    expect(content).not.toHaveProperty('layer_state')
    expect(db).toHaveBeenCalledTimes(2)
  })

  it(`E3 ${route.name}: an unreadable layer state is layer_state_unreadable, never computed_found_none`, async () => {
    emptyLayer('throw')
    const cap = await route.load()
    const result = await cap.handler!({ chart_id: 'chart-1' }, {})
    expect(result.is_error).toBe(false)
    expect((result.content as Record<string, unknown>).empty_reason).toBe('layer_state_unreadable')
  })
}

it('E3 a probe row with no counts is unreadable, not "none"', async () => {
  db.mockImplementation(async (sql: string) => sql.includes('asset_throughput') ? { rows: [{}] } : { rows: sql.includes('COUNT(*)::text AS total') ? [{ total: '0' }] : [] })
  const { queryObstructionPeriodsCapability } = await import('./query_obstruction_periods')
  const result = await queryObstructionPeriodsCapability.handler!({ chart_id: 'chart-1' }, {})
  expect((result.content as Record<string, unknown>).empty_reason).toBe('layer_state_unreadable')
})

const manifest = { manifest_id: 'build-7', generation: '4.1' }
const darshanaRow = { id: '1', generation: '4.1', verification_pass_status: null, assertion: { assertion_id: 'a1' } }

it('E4 composeView names the reason for the empty source even when another source is populated', async () => {
  const { composeView } = await import('./view_common')
  const content = composeView('now', 'chart', { manifest, coverage: [], sources: [
    { table: 'kala_darshana', total: 1, rows: [darshanaRow], layer: { rows_in_published_generation: 1, rows_any_partition: 1, asset_state: 'lit' } },
    { table: 'kala_obstruction', total: 0, rows: [], layer: { rows_in_published_generation: 0, rows_any_partition: 0, asset_state: null } },
  ] })
  // the page is NOT empty, so the page-level reason stays null; the empty source still says why
  expect(content.empty_reason).toBeNull()
  const [populated, empty] = content.sources as Record<string, unknown>[]
  expect(populated).not.toHaveProperty('empty_reason')
  expect(empty).toMatchObject({ table: 'kala_obstruction', total_matching: 0, empty_reason: 'layer_not_computed',
    layer_state: { rows_any_partition: 0, rows_served_unfiltered: 0, asset_state: null } })
})

it.each([
  ['lit and empty', { rows_in_published_generation: 0, rows_any_partition: 0, asset_state: 'lit' }, 'computed_found_none'],
  ['rows only outside the published generation', { rows_in_published_generation: 0, rows_any_partition: 4, asset_state: 'lit' }, 'rows_outside_served_generation'],
  ['published rows dropped by the selectors', { rows_in_published_generation: 3, rows_any_partition: 3, asset_state: 'lit' }, 'filters_excluded_all_rows'],
  ['counts delivered as strings (bigint)', { rows_in_published_generation: '3', rows_any_partition: '3', asset_state: null }, 'filters_excluded_all_rows'],
  ['counts not measured', undefined, 'layer_state_unreadable'],
])('E4 composeView per-source reason: %s -> %s', async (_label, layer, reason) => {
  const { composeView } = await import('./view_common')
  const content = composeView('now', 'chart', { manifest, coverage: [], sources: [
    { table: 'kala_obstruction', total: 0, rows: [], ...(layer ? { layer } : {}) },
  ] })
  expect(content.empty_reason).toBe('no_matching_rows')
  expect(content.sources[0]).toMatchObject({ empty_reason: reason })
})

it('E4 a source with no single writer asset never claims "computed and found none"', async () => {
  const { composeView } = await import('./view_common')
  const content = composeView('now', 'chart', { manifest, coverage: [], sources: [
    { table: 'kala_gochara_contacts', total: 0, rows: [], layer: { rows_in_published_generation: 0, rows_any_partition: 0, asset_state: 'lit' } },
  ] })
  expect(content.sources[0]).toMatchObject({ empty_reason: 'layer_state_unreadable' })
})

it('E4 an unpublished view keeps its page-level reason and invents no per-source one', async () => {
  const { composeView } = await import('./view_common')
  const content = composeView('now', 'chart', { manifest: null, coverage: [], sources: [] })
  expect(content).toMatchObject({ empty_reason: 'unpublished', sources: [] })
})

// ---- E5: real SQL ----
const chart = '11111111-1111-4111-8111-111111111111'
const head = 'CODEX-head'
function measured(opts: { obstruction: (string | null)[]; asset?: string; selector?: string }) {
  const rows = opts.obstruction.map((generation, i) =>
    `INSERT INTO kala_obstruction VALUES (${i + 1}, '${chart}', ${generation === null ? 'NULL' : `'${generation}'`}, 'a${i + 1}', NULL, NULL, NULL, NULL, NULL);`).join('\n')
  return import('./view_common').then(({ viewSql }) => disposableSql(`BEGIN;
    CREATE TEMP TABLE kala_layer_head (chart_id uuid, generation text, published_at timestamptz);
    CREATE TEMP TABLE asset_throughput (chart_id uuid, asset_id text, state text);
    CREATE TEMP TABLE kala_layer_candidate (chart_id uuid, generation text, build_id uuid, model_digest text, rule_registry_version text, conventions jsonb, state text);
    CREATE TEMP TABLE kala_layer_candidate_grain (chart_id uuid, generation text, grain_key text, result_state text);
    CREATE TEMP TABLE kala_gochara_coverage (chart_id uuid, generation text, partition_kind text, partition_key text);
    CREATE TEMP TABLE kala_obstruction (id bigint, chart_id uuid, generation text, assertion_id text, assertion jsonb,
      interval_start timestamptz, interval_end timestamptz, window_start date, window_end date);
    INSERT INTO kala_layer_head VALUES ('${chart}', '${head}', now());
    INSERT INTO kala_layer_candidate VALUES ('${chart}', '${head}', '22222222-2222-4222-8222-222222222222', 'd', 'r', '{}', 'published');
    ${opts.asset ? `INSERT INTO asset_throughput VALUES ('${chart}', 'ka_vighnakara', '${opts.asset}');` : ''}
    ${rows}
    PREPARE ky_view(uuid,timestamptz,timestamptz,timestamptz,text,text,int,int,text,text)
      AS ${viewSql({ name: 'now', description: 'fixture', sources: ['kala_obstruction'], required: [] })};
    EXECUTE ky_view('${chart}', NULL, NULL, NULL, ${opts.selector ? `'${opts.selector}'` : 'NULL'}, NULL, 50, 0, NULL, NULL); ROLLBACK;`)[0].sources as Parameters<typeof import('./view_common').composeView>[2]['sources'])
}
const dbLane = it.runIf(process.env.KALA_VIEW_DB_TESTS === '1')

dbLane('E5 real SQL: the three empty states are measured from the table and the asset state', async () => {
  const { composeView } = await import('./view_common')
  const reasonOf = async (opts: Parameters<typeof measured>[0]) => {
    const sources = await measured(opts)
    return composeView('now', chart, { manifest: { manifest_id: 'b', generation: head }, coverage: [], sources }).sources[0] as Record<string, unknown>
  }
  expect(await reasonOf({ obstruction: [] })).toMatchObject({ empty_reason: 'layer_not_computed', layer_state: { rows_any_partition: 0, asset_state: null } })
  expect(await reasonOf({ obstruction: [], asset: 'lit' })).toMatchObject({ empty_reason: 'computed_found_none', layer_state: { asset_state: 'lit' } })
  // a private candidate's rows are rows in the table, but not the published generation's
  expect(await reasonOf({ obstruction: ['candidate:x'], asset: 'lit' })).toMatchObject({ empty_reason: 'rows_outside_served_generation', layer_state: { rows_any_partition: 1, rows_served_unfiltered: 0 } })
  // the head holds a row, the selector (event_class) excludes it
  expect(await reasonOf({ obstruction: [head], asset: 'lit', selector: 'travel' })).toMatchObject({ empty_reason: 'filters_excluded_all_rows', layer_state: { rows_served_unfiltered: 1 } })
  // a populated source is unchanged: no reason key
  const populated = (await reasonOf({ obstruction: [head], asset: 'lit' }))
  expect(populated).not.toHaveProperty('empty_reason')
  expect(populated).toMatchObject({ total_matching: 1, returned: 1 })
})
