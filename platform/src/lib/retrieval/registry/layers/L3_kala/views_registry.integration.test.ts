import { existsSync } from 'node:fs'
import { expect, it, vi } from 'vitest'
const db = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: db }))
it('the unchanged bridge resolves all seven public names directly without replacing internal readers', async () => {
  await import('./index')
  const { getCatalog, getCapability } = await import('../../index')
  const { resolveWebToolBridge } = await import('../../../../../../scripts/manifest/web_tool_bridge_builder')
  const names = ['now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain']
  const entries = resolveWebToolBridge(names.map(name => `kala_${name}_get`), getCatalog(), {}, {},
    { canonical_faces: [], deprecated_aliases: {} })
  expect(entries).toEqual([...names].sort().map(name => ({ name: `kala_${name}_get`,
    uri: `marsys://tool/L3/kala_${name}_get`, resolution_kind: 'catalog_name_direct', via: [] })))
  for (const name of names) expect(getCapability(`marsys://tool/L3/${name}_read`)).toBeDefined()
})
it.each([
  ['now', { as_of: '2026-10-09' }, ['at']],
  ['elect', { undertaking: 'travel', date_range: { start: '2026-10-09', end: '2026-10-10' } }, ['event_class', 'date_from', 'date_to']],
  ['explain', { domain: 'career' }, ['assertion_id_or_record_drill']],
])('public %s discloses an unavailable adapter instead of inventing stage selectors or a successful legacy envelope', async (name, args, bindings) => {
  await import('./index')
  const { getCapability } = await import('../../index')
  db.mockReset()
  expect(await getCapability(`marsys://tool/L3/kala_${name}_get`)!.handler!({ chart_id: fixtureChart, ...args }, {}))
    .toMatchObject({ is_error: true, content: { tool: `kala_${name}_get`, manifest_id: null,
      empty_reason: 'legacy_adapter_unavailable', unavailable_stage_bindings: bindings } })
  expect(db).not.toHaveBeenCalled()
})
it('seven composites resolve additively and require their own explicit request context', async () => {
  expect(existsSync(new URL('./view_common.ts', import.meta.url))).toBe(true)
  await import('./index')
  const { getCapability } = await import('../../index')
  for (const name of ['now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain']) {
    const cap = getCapability(`marsys://tool/L3/${name}_read`)!
    expect(cap).toBeDefined()
    expect((await cap.handler!({}, {})).is_error).toBe(true)
  }
  expect(db).not.toHaveBeenCalled()
})
it('refuses invalid time bounds, nonfinite limits and missing view-specific selectors before SQL', async () => {
  expect(existsSync(new URL('./view_common.ts', import.meta.url))).toBe(true)
  await import('./index')
  const { getCapability } = await import('../../index')
  for (const [name, args] of [
    ['now', { chart_id: 'chart' }], ['ahead', { chart_id: 'chart', date_from: 'junk', date_to: '2026-10-09' }],
    ['ahead', { chart_id: 'chart', date_from: '2026-10-10T00:00:00Z', date_to: '2026-10-09T00:00:00Z' }],
    ['elect', { chart_id: 'chart' }], ['ritual', { chart_id: 'chart' }], ['explain', { chart_id: 'chart' }],
    ['priority', { chart_id: 'chart', limit: NaN }], ['story', { chart_id: 'chart', offset: -1 }],
  ] as const) expect((await getCapability(`marsys://tool/L3/${name}_read`)!.handler!({ ...args }, {})).is_error).toBe(true)
})
it('query failure is an error with no invented manifest or successful empty-result claim', async () => {
  expect(existsSync(new URL('./view_common.ts', import.meta.url))).toBe(true)
  const { nowViewCapability } = await import('./view_now')
  db.mockRejectedValueOnce(new Error('db unavailable'))
  expect(await nowViewCapability.handler!({ chart_id: 'chart', at: '2026-10-09T10:00:00Z' }, {}))
    .toMatchObject({ is_error: true, content: { manifest_id: null, empty_reason: 'query_failed' } })
})
it('old temporal tools still return their golden shapes and isolate private candidate rows', async () => {
  db.mockReset().mockImplementation((sql: string) => Promise.resolve({ rows: sql.includes('COUNT(*)')
    ? [{ total: '1' }] : [{ id: 'legacy-1', net_label: 'favorable', effective_score: 0.7 }] }))
  await import('./index')
  const { getCapability } = await import('../../index')
  for (const [name, field] of [['query_temporal_view', 'rows'], ['query_obstruction_periods', 'obstructions']]) {
    expect((await getCapability(`marsys://tool/L3/${name}`)!.handler!({ chart_id: 'chart' }, {})).content)
      .toMatchObject({ chart_id: 'chart', [field]: [{ id: 'legacy-1' }], count: 1, total_matching: 1, more_available: false })
  }
  for (const [sql] of db.mock.calls) expect(sql).toContain('generation IS NULL')
})

// Real SQL oracle, explicitly enabled by the item's precheck. All writes are
// transaction-local TEMP fixtures in the disposable lane DB; production is unreachable.
const fixtureChart = '11111111-1111-4111-8111-111111111111'
const schema = `
CREATE TEMP TABLE kala_layer_head (chart_id uuid, generation text, published_at timestamptz);
CREATE TEMP TABLE kala_layer_candidate (chart_id uuid, generation text, build_id uuid, model_digest text, rule_registry_version text, conventions jsonb, state text);
CREATE TEMP TABLE kala_layer_candidate_grain (chart_id uuid, generation text, grain_key text, result_state text, input_vector text);
CREATE TEMP TABLE kala_gochara_coverage (chart_id uuid, generation text, partition_kind text, partition_key text, unsearched_reason text);
CREATE TEMP TABLE kala_darshana (id bigint, chart_id uuid, generation text, assertion_id text, assertion jsonb, interval_start timestamptz, interval_end timestamptz, window_start date, window_end date);
CREATE TEMP TABLE kala_obstruction (LIKE kala_darshana);
CREATE TEMP TABLE kala_gochara_contacts (chart_id uuid, generation text, contact_id text, t_in timestamptz, t_out timestamptz);
CREATE TEMP TABLE kala_bhavishya (id bigint, chart_id uuid, window_start date, window_end date);
CREATE TEMP TABLE kala_convergence (convergence_id bigint, chart_id uuid, window_start date, window_end date);
CREATE TEMP TABLE kala_jivana_parva (id bigint, chart_id uuid, start_year int, end_year int);
INSERT INTO kala_layer_head VALUES ('${fixtureChart}', '4.1', '2026-10-09T00:00:00Z');
INSERT INTO kala_layer_candidate VALUES ('${fixtureChart}', '4.1', '22222222-2222-4222-8222-222222222222', 'digest', 'r2', '{}', 'published');
INSERT INTO kala_layer_candidate VALUES ('${fixtureChart}', '9.9', '99999999-9999-4999-8999-999999999999', 'private', 'r9', '{}', 'building');
INSERT INTO kala_layer_candidate_grain VALUES ('${fixtureChart}', '4.1', 'negative_space/day', 'rows', 'vector');
INSERT INTO kala_gochara_coverage VALUES ('${fixtureChart}', '4.1', 'moon', 'on_demand', 'not_searched');
INSERT INTO kala_darshana
SELECT id, '${fixtureChart}'::uuid, generation, 'a'||id, jsonb_build_object(
  'assertion_id', 'a'||id, 'operator_role', operator_role, 'role', role,
  'subject', jsonb_build_object('event_class', 'travel'),
  'roots', jsonb_build_object('contact_ids', jsonb_build_array('c1'), 'fact_ids', jsonb_build_array('f1'), 'record_ids', '[]'::jsonb),
  'payload', jsonb_build_object('effective_state', 'obstruction_cancelled', 'release', jsonb_build_object('kind', 'unknown', 'instant', NULL))),
  '2026-10-09T00:00:00Z'::timestamptz, '2026-10-10T00:00:00Z'::timestamptz, '2026-10-09'::date, '2026-10-09'::date
FROM (VALUES (1, '4.1', 'scored', 'corroborates'), (2, '9.9', 'scored', 'corroborates'),
             (3, NULL, 'scored', 'corroborates'), (4, '4.1', 'testimony', 'corroborates'),
             (5, '4.1', 'scored', 'selects')) fixture(id, generation, operator_role, role);
INSERT INTO kala_gochara_contacts VALUES ('${fixtureChart}', '4.1', 'c1', '2026-10-09T00:00:00Z', '2026-10-10T00:00:00Z');
INSERT INTO kala_bhavishya VALUES (1, '${fixtureChart}', '2026-10-09', '2026-10-09');
INSERT INTO kala_convergence VALUES (1, '${fixtureChart}', '2026-10-09', '2026-10-09');
INSERT INTO kala_jivana_parva VALUES (1, '${fixtureChart}', 2026, 2026);
`
async function postgresQuery(sql: string, params: unknown[], before = '') {
  const { execFileSync } = await import('node:child_process')
  const lane = process.env.KY_LANE
  if (!lane || !/^k[1-8]$|^v[1-4]$/.test(lane)) throw new Error('an explicit disposable campaign lane is required')
  const literal = (v: unknown) => v == null ? 'NULL' : typeof v === 'number' ? String(v) : `'${String(v).replaceAll("'", "''")}'`
  const output = execFileSync('docker', ['exec', '-i', 'ky-pg', 'psql', '-U', 'postgres', '-d', `ky_${lane}`, '-qAt', '-v', 'ON_ERROR_STOP=1'], {
    input: `BEGIN; SET LOCAL timezone = 'UTC'; ${schema} ${before}\nPREPARE ky_view(uuid,timestamptz,timestamptz,timestamptz,text,text,int,int,text,text) AS ${sql};\nEXECUTE ky_view(${params.map(literal).join(',')}); ROLLBACK;`,
    encoding: 'utf8', timeout: 15000,
  }).trim().split('\n').at(-1)!
  const [manifest, coverage, sources] = output.split('|').map(x => x ? JSON.parse(x) : null)
  return { rows: [{ manifest, coverage, sources }] }
}
it.runIf(process.env.KALA_VIEW_DB_TESTS === '1')('all seven actual SQL readers preserve published binding, source tiers, references and coverage', async () => {
  expect(existsSync(new URL('./view_common.ts', import.meta.url))).toBe(true)
  await import('./index')
  const { getCapability } = await import('../../index')
  db.mockReset().mockImplementation(postgresQuery)
  for (const name of ['now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain']) {
    const result = await getCapability(`marsys://tool/L3/${name}_read`)!.handler!({ chart_id: fixtureChart,
      at: name === 'now' ? '2026-10-09T12:00:00Z' : undefined,
      date_from: '2026-10-09T00:00:00Z', date_to: '2026-10-10T00:00:00Z',
      event_class: ['elect', 'ritual'].includes(name) ? 'travel' : undefined,
      assertion_id: name === 'explain' ? 'a1' : undefined,
    }, {})
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content).toMatchObject({ manifest_id: '22222222-2222-4222-8222-222222222222',
      generation: '4.1', empty_reason: null, density: { confirmed: 1 } })
    expect(content.coverage).toEqual(expect.arrayContaining([expect.objectContaining({ unsearched_reason: 'not_searched' })]))
    expect(JSON.stringify(content.rows)).not.toContain('9.9')
  }
})
it.runIf(process.env.KALA_VIEW_DB_TESTS === '1')('actual SQL uses half-open intervals, rejects private head and prevents selector injection', async () => {
  const { nowViewCapability } = await import('./view_now')
  const { explainViewCapability } = await import('./view_explain')
  db.mockReset().mockImplementation(postgresQuery)
  const boundary = await nowViewCapability.handler!({ chart_id: fixtureChart, at: '2026-10-10T00:00:00Z' }, {})
  expect(boundary.content).toMatchObject({ empty_reason: 'no_matching_rows', rows: [] })
  const injection = await explainViewCapability.handler!({ chart_id: fixtureChart, assertion_id: "a1' OR true --" }, {})
  expect(injection.content).toMatchObject({ empty_reason: 'no_matching_rows', rows: [] })
  db.mockImplementation((sql, params) => postgresQuery(sql, params, "UPDATE kala_layer_head SET generation = '9.9';"))
  expect((await nowViewCapability.handler!({ chart_id: fixtureChart, at: '2026-10-09T12:00:00Z' }, {})).content)
    .toMatchObject({ empty_reason: 'unpublished', manifest_id: null, rows: [] })
})
it.runIf(process.env.KALA_VIEW_DB_TESTS === '1')('a context row drill resolves the exact stored record through EXPLAIN', async () => {
  const { storyViewCapability } = await import('./view_story')
  const { explainViewCapability } = await import('./view_explain')
  db.mockReset().mockImplementation(postgresQuery)
  const story = (await storyViewCapability.handler!({ chart_id: fixtureChart }, {})).content as { rows: { source_table: string; drill: { args: Record<string, unknown> } }[] }
  const pointer = story.rows.find(row => row.source_table === 'kala_jivana_parva')!.drill
  expect((await explainViewCapability.handler!(pointer.args, {})).content)
    .toMatchObject({ rows: [{ source_table: 'kala_jivana_parva', record_id: '1', qualification: 'context_only' }] })
})
it.runIf(process.env.KALA_VIEW_DB_TESTS === '1')('pages protect confirmed findings and disclose exhaustion accurately', async () => {
  const { priorityViewCapability } = await import('./view_priority')
  db.mockReset().mockImplementation(postgresQuery)
  const first = await priorityViewCapability.handler!({ chart_id: fixtureChart, limit: 1 }, {})
  expect(first.content).toMatchObject({ density: { confirmed: 1 }, rows: [
    { density: 'confirmed', record_id: '1' }, { source_table: 'kala_convergence', qualification: 'context_only' },
  ], pagination: { more_available: true } })
  const exhausted = await priorityViewCapability.handler!({ chart_id: fixtureChart, limit: 1, offset: 4 }, {})
  expect(exhausted.content).toMatchObject({ rows: [], pagination: { total_matching: 5, more_available: false } })
})
it('rejects nonexistent calendar dates instead of allowing Date.parse rollover', async () => {
  const { nowViewCapability } = await import('./view_now')
  db.mockReset().mockResolvedValue({ rows: [{ manifest: null, coverage: [], sources: [] }] })
  expect((await nowViewCapability.handler!({ chart_id: fixtureChart, at: '2026-02-30T10:00:00Z' }, {})).is_error).toBe(true)
})
it.runIf(process.env.KALA_VIEW_DB_TESTS === '1')('an additive generation column on a legacy source cannot expose private future rows', async () => {
  const { storyViewCapability } = await import('./view_story')
  db.mockReset().mockImplementation((sql, params) => postgresQuery(sql, params,
    "ALTER TABLE kala_jivana_parva ADD COLUMN generation text; INSERT INTO kala_jivana_parva VALUES (99, '" + fixtureChart + "', 2026, 2026, '9.9');"))
  const result = await storyViewCapability.handler!({ chart_id: fixtureChart }, {})
  expect(JSON.stringify(result.content)).not.toContain('9.9')
})
it.runIf(process.env.KALA_VIEW_DB_TESTS === '1')('published readers follow a head cutover and rollback while ignoring other candidates', async () => {
  const { nowViewCapability } = await import('./view_now')
  db.mockReset().mockImplementation((sql, params) => postgresQuery(sql, params,
    "UPDATE kala_layer_candidate SET state = 'published' WHERE generation = '9.9'; UPDATE kala_layer_head SET generation = '9.9';"))
  expect((await nowViewCapability.handler!({ chart_id: fixtureChart, at: '2026-10-09T12:00:00Z' }, {})).content)
    .toMatchObject({ generation: '9.9', manifest_id: '99999999-9999-4999-8999-999999999999',
      rows: [{ record_id: '2', qualification: 'published' }, { record_id: '3', qualification: 'context_only' }] })
  db.mockImplementation(postgresQuery)
  expect((await nowViewCapability.handler!({ chart_id: fixtureChart, at: '2026-10-09T12:00:00Z' }, {})).content)
    .toMatchObject({ generation: '4.1', manifest_id: '22222222-2222-4222-8222-222222222222', density: { confirmed: 1 } })
})
