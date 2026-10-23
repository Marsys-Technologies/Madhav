/**
 * SR-EMPTY-REASON real-SQL oracles (CLAUDE.md §N.6 rule 4, §N.7.6, §N.8). Run by the db-integration-tests-10-0 profile
 * (ci_test_suites.json glob `views_registry.integration*.test.ts`) with KALA_VIEW_DB_TESTS=1 on a disposable database;
 * a skip is not a pass. The unit twin, with the database mocked, is empty_layer_reason.test.ts.
 *  E5   viewSql (composeView's per-source layer) measures the counts from the table and the asset state
 *  E5b  the layer-state probe of kala_obstruction_get / kala_convergence_get (readEmptyLayer) runs on real SQL: rows only in
 *       an unpublished K9 candidate partition are "rows_outside_served_generation", never "computed_found_none" ("no obstacles
 *       were found" would be the dangerous reading); a lit asset with no rows is computed_found_none; a never-lit or stale asset
 *       with no rows is layer_not_computed. The mocked unit test answers the probe with canned counts, so it cannot read false
 *       for the probe's own SQL: this is the detector for that SQL.
 */
import { expect, it, vi } from 'vitest'
import { disposableSql } from './disposable_sql.test_support'

// The routes' own `query` is routed to the disposable database: each statement runs against freshly seeded temp tables.
let seed = ''
const lit = (v: unknown) => v === null || v === undefined ? 'NULL' : typeof v === 'number' ? String(v) : `'${String(v).replace(/'/g, "''")}'`
vi.mock('@/lib/db/client', () => ({ query: async (sql: string, params: unknown[] = []) => {
  const rows = disposableSql(`BEGIN;
    CREATE TEMP TABLE kala_layer_head (chart_id uuid, generation text);
    CREATE TEMP TABLE asset_throughput (chart_id uuid, asset_id text, state text);
    CREATE TEMP TABLE kala_obstruction (id bigint, chart_id uuid, generation text, convergence_id bigint, signal_id text, obstruction_type text,
      severity text, severity_score numeric, override_score numeric, obstruction_detail jsonb, source_citation text);
    CREATE TEMP TABLE kala_convergence (convergence_id bigint, chart_id uuid, generation text, signal_id text, window_start date, window_end date,
      peak_date date, mode text, convergence_score numeric, orb_strength numeric, rarity_years numeric, confidence_score numeric,
      confidence_label text, independent_current_count int, is_off_dasha_discovery bool, horizon_tier text, domain text,
      constituent_factors jsonb, source_citation text);
    INSERT INTO kala_layer_head VALUES ('${chart}', '${head}');
    ${seed}
    PREPARE q AS ${sql};
    EXECUTE q(${params.map(lit).join(', ')}); ROLLBACK;`)
  return { rows }
} }))

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

// ---- E5b: the routes' layer-state probe on real SQL ----
const obs = (g: string) => `INSERT INTO kala_obstruction VALUES (1, '${chart}', '${g}', 1, 's', 'graha', 'mild', 0.2, NULL, NULL, NULL);`
const conv = (g: string) => `INSERT INTO kala_convergence VALUES (1, '${chart}', '${g}', 's', '2031-01-01', '2031-01-09', '2031-01-05', 'C', 0.5, 0.5, 1, 0.5, 'high', 3, false, 'near', 'career', '{}', NULL);`
const asset = (a: string, s: string) => `INSERT INTO asset_throughput VALUES ('${chart}', '${a}', '${s}');`
it.runIf(process.env.KALA_VIEW_DB_TESTS === '1').each([
  ['obstruction', 'no asset row, no rows', 'layer_not_computed', '', {}],
  ['obstruction', 'lit asset, no rows', 'computed_found_none', asset('ka_vighnakara', 'lit'), {}],
  ['obstruction', 'stale asset, no rows', 'layer_not_computed', asset('ka_vighnakara', 'stale'), {}],
  ['obstruction', 'rows only in a K9 candidate partition', 'rows_outside_served_generation', asset('ka_vighnakara', 'lit') + obs('candidate:x'), {}],
  ['obstruction', 'served rows, the filter drops them', 'filters_excluded_all_rows', asset('ka_vighnakara', 'lit') + obs(head), { severity: 'severe' }],
  ['convergence', 'no asset row, no rows', 'layer_not_computed', '', {}],
  ['convergence', 'lit asset, no rows', 'computed_found_none', asset('ka_sangam', 'lit'), {}],
  ['convergence', 'stale asset, no rows', 'layer_not_computed', asset('ka_sangam', 'stale'), {}],
  ['convergence', 'rows only in a K9 candidate partition', 'rows_outside_served_generation', asset('ka_sangam', 'lit') + conv('candidate:x'), {}],
  ['convergence', 'served rows, the filter drops them', 'filters_excluded_all_rows', asset('ka_sangam', 'lit') + conv(head), { domain: 'wealth' }],
] as const)('E5b real SQL: kala_%s_get, %s -> %s', async (route, _label, reason, s, args) => {
  seed = s
  const cap = route === 'obstruction' ? (await import('./query_obstruction_periods')).queryObstructionPeriodsCapability
    : (await import('./query_convergence_windows')).queryConvergenceWindowsCapability
  const res = await cap.handler!({ chart_id: chart, ...args }, {})
  expect(res.is_error).toBe(false)
  expect((res.content as Record<string, unknown>).empty_reason).toBe(reason)
})
