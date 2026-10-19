import { disposableSql } from './disposable_sql.test_support'
import { existsSync, readFileSync } from 'node:fs'
import { expect, it, vi } from 'vitest'
const db = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: db }))

it('K7-4 mapping binds all seven registry and Vidhi identities to their actual stored-tier descriptors', async () => {
  const source = readFileSync(new URL('../../../../../../python-sidecar/services/ka_tulana/__init__.py', import.meta.url), 'utf8')
  const mapping = JSON.parse(source.split("CERTIFICATION_MAPPING = json.loads(r'''")[1].split("''')")[0])
  await import('./index')
  const { getCapability, getCatalog } = await import('../../index')
  const { resolveWebToolBridge } = await import('../../../../../../scripts/manifest/web_tool_bridge_builder')
  for (const entry of Object.values(mapping.views) as Array<{ stage_uri: string; public_uri: string; public_name: string; density_contract: Record<string, unknown> }>) {
    const cap = getCapability(entry.stage_uri)!
    expect(cap).toBeDefined()
    expect(cap.density_contract).toMatchObject(entry.density_contract)
    expect(getCapability(entry.public_uri)?.name).toBe(entry.public_name)
    expect(resolveWebToolBridge([entry.public_name], getCatalog(), {}, {}, { canonical_faces: [], deprecated_aliases: {} }))
      .toEqual([{ name: entry.public_name, uri: entry.public_uri, resolution_kind: 'catalog_name_direct', via: [] }])
  }
})
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
CREATE TEMP TABLE kala_jivana_parva (id bigint, chart_id uuid, start_year int, end_year int,
  high_convergence_count int, avg_effective_score numeric, narrative jsonb);
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
INSERT INTO kala_obstruction SELECT 101, chart_id, generation, 'obstruction', assertion, interval_start, interval_end, window_start, window_end FROM kala_darshana WHERE id = 1;
ALTER TABLE kala_darshana ADD COLUMN verification_pass_status text;
ALTER TABLE kala_obstruction ADD COLUMN verification_pass_status text;
UPDATE kala_obstruction SET verification_pass_status = 'single';
UPDATE kala_darshana SET verification_pass_status = CASE WHEN id = 1 THEN 'two_pass_verified' WHEN id = 4 THEN 'single' ELSE NULL END;
INSERT INTO kala_gochara_contacts VALUES ('${fixtureChart}', '4.1', 'c1', '2026-10-09T00:00:00Z', '2026-10-10T00:00:00Z');
INSERT INTO kala_bhavishya VALUES (1, '${fixtureChart}', '2026-10-09', '2026-10-09');
INSERT INTO kala_convergence VALUES (1, '${fixtureChart}', '2026-10-09', '2026-10-09');
INSERT INTO kala_jivana_parva VALUES (1, '${fixtureChart}', 2026, 2026, 8838, 0.91,
  '{"summary":"8838 high-convergence windows","high_convergence_count":8838,"avg_effective_score":0.91}');
ALTER TABLE kala_gochara_contacts ADD COLUMN verification_pass_status text;
ALTER TABLE kala_gochara_contacts ADD COLUMN build_id uuid;
UPDATE kala_gochara_contacts SET verification_pass_status = 'single', build_id = '22222222-2222-4222-8222-222222222222';
ALTER TABLE kala_bhavishya ADD COLUMN verification_pass_status text;
UPDATE kala_bhavishya SET verification_pass_status = 'single';
ALTER TABLE kala_convergence ADD COLUMN verification_pass_status text;
UPDATE kala_convergence SET verification_pass_status = 'single';
ALTER TABLE kala_jivana_parva ADD COLUMN verification_pass_status text;
UPDATE kala_jivana_parva SET verification_pass_status = 'single';
`
async function postgresQuery(sql: string, params: unknown[], before = '') {
  const literal = (v: unknown) => v == null ? 'NULL' : typeof v === 'number' ? String(v) : `'${String(v).replaceAll("'", "''")}'`
  return { rows: disposableSql(`BEGIN; SET LOCAL timezone = 'UTC'; ${schema} ${before}
    PREPARE ky_view(uuid,timestamptz,timestamptz,timestamptz,text,text,int,int,text,text) AS ${sql};
    EXECUTE ky_view(${params.map(literal).join(',')}); ROLLBACK;`) }

}
it.runIf(process.env.KALA_VIEW_DB_TESTS === '1')('published STORY SQL nulls stale chapter figures even when another chart has convergence rows', async () => {
  const { storyViewCapability } = await import('./view_story')
  db.mockReset().mockImplementation((sql, params) => postgresQuery(sql, params,
    "UPDATE kala_convergence SET chart_id = '33333333-3333-4333-8333-333333333333';"))
  const result = await storyViewCapability.handler!({ chart_id: fixtureChart }, {})
  expect(result).toMatchObject({ is_error: false, content: { rows: expect.arrayContaining([
    expect.objectContaining({ source_table: 'kala_jivana_parva', data: expect.objectContaining({
      high_convergence_count: null, avg_effective_score: null, convergence_null_reason: 'source_table_empty_for_chart',
      narrative: expect.objectContaining({ summary: null, high_convergence_count: null, avg_effective_score: null }),
    }) }),
  ]) } })
})
it.runIf(process.env.KALA_VIEW_DB_TESTS === '1').each([false, true])('all seven actual SQL readers work with stored columns present=%s', async hasTier => {
  expect(existsSync(new URL('./view_common.ts', import.meta.url))).toBe(true)
  await import('./index')
  const { getCapability } = await import('../../index')
  db.mockReset().mockImplementation((sql, params) => postgresQuery(sql, params, hasTier ? '' :
    ['kala_darshana', 'kala_obstruction', 'kala_gochara_contacts', 'kala_bhavishya', 'kala_convergence', 'kala_jivana_parva']
      .map(table => `ALTER TABLE ${table} DROP COLUMN verification_pass_status;`).join('\n')))
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
      generation: '4.1', empty_reason: null, density: { confirmed: hasTier ? 1 : 0 } })
    if (!hasTier) {
      const rows = content.rows as { density: unknown; verification: { status: unknown } }[]
      expect(rows.length).toBeGreaterThan(0)
      expect(rows.every(row => row.density === null && row.verification.status === null)).toBe(true)
      expect(content.density).toMatchObject({ unknown: rows.length })
      expect(content.catalog_only_rows_in_page).toBe(rows.length)
      expect(content.judgment_flags).toEqual(expect.arrayContaining(['catalog_only_rows_present', 'stored_tier_contract_unavailable']))
    }
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
    "ALTER TABLE kala_jivana_parva ADD COLUMN generation text; INSERT INTO kala_jivana_parva (id, chart_id, start_year, end_year, generation) VALUES (99, '" + fixtureChart + "', 2026, 2026, '9.9');"))
  const result = await storyViewCapability.handler!({ chart_id: fixtureChart }, {})
  expect(result.is_error).toBe(false)
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

it.runIf(process.env.KALA_VIEW_DB_TESTS === '1').each(['information_unavailable', 'evaluated_silent'])
  ('real NOW SQL carries %s and null release without substituting the other sentinel', async state => {
    const { nowViewCapability } = await import('./view_now')
    db.mockReset().mockImplementation((sql, params) => postgresQuery(sql, params,
      `UPDATE kala_darshana SET assertion = jsonb_set(assertion, '{payload,effective_state}', '"${state}"'::jsonb) WHERE id = 1;`))
    const result = await nowViewCapability.handler!({ chart_id: fixtureChart, at: '2026-10-09T12:00:00Z' }, {})
    const content = result.content as { rows: { record_id: string; data: unknown }[] }
    expect(content.rows.find(row => row.record_id === '1')).toMatchObject({ data: { assertion: { payload: {
      effective_state: state, release: { kind: 'unknown', instant: null },
    } } } })
  })

it.runIf(process.env.KALA_VIEW_DB_TESTS === '1')('context stays visible when published judge assertions are absent', async () => {
  const { storyViewCapability } = await import('./view_story')
  db.mockReset().mockImplementation((sql, params) => postgresQuery(sql, params,
    'DELETE FROM kala_darshana; DELETE FROM kala_convergence;'))
  expect(await storyViewCapability.handler!({ chart_id: fixtureChart }, {}))
    .toMatchObject({ is_error: false, content: { empty_reason: null, rows: [{
      source_table: 'kala_jivana_parva', qualification: 'context_only', density: null,
      data: { high_convergence_count: null, convergence_null_reason: 'source_table_empty_for_chart' },
    }] } })
})

it.each([
  ['now', ['kala_darshana', 'kala_obstruction']],
  ['ahead', ['kala_darshana', 'kala_bhavishya', 'kala_gochara_contacts']],
  ['priority', ['kala_darshana', 'kala_convergence']],
  ['elect', ['kala_darshana', 'kala_obstruction', 'kala_gochara_contacts']],
  ['story', ['kala_darshana', 'kala_jivana_parva']],
  ['ritual', ['kala_darshana', 'kala_obstruction']],
  ['explain', ['kala_darshana', 'kala_obstruction', 'kala_gochara_contacts', 'kala_bhavishya', 'kala_convergence', 'kala_jivana_parva']],
])('%s actual entry discloses its no-tier sources and retains unknown counts, order, pages and drills', async (name, tables) => {
  await import('./index')
  const { getCapability } = await import('../../index')
  const cap = getCapability(`marsys://tool/L3/${name}_read`)!
  expect(cap.density_contract).toMatchObject({ stored_tier_columns: tables.map(table => `${table}.verification_pass_status`), unavailable_sources: [] })
  db.mockReset().mockResolvedValue({ rows: [{ manifest: { manifest_id: 'test-build', generation: '4.1' },
    coverage: [], sources: [{ table: 'kala_darshana', total: 100, rows: [
      { id: '2', generation: '4.1', tier: 'confirmed', assertion_id: 'a2', source_citation: 'fixture:2' },
      { id: '10', generation: '4.1', tier: 'testimony', assertion_id: 'a10', source_citation: 'fixture:10' },
      { id: '0', generation: null, source_citation: 'fixture:legacy' },
    ] }] }] })
  const result = await cap.handler!({ chart_id: fixtureChart, at: '2026-10-09T12:00:00Z',
    date_from: '2026-10-09T00:00:00Z', date_to: '2026-10-10T00:00:00Z',
    event_class: 'travel', assertion_id: 'a2', limit: 3, offset: 3 }, {})
  expect(result.content).toMatchObject({ density: { confirmed: 0, testimony: 0, unknown: 3, context_only: 1 },
    catalog_only_rows_in_page: 3,
    judgment_flags: ['catalog_only_rows_present', 'stored_tier_contract_unavailable',
      'context_only_rows_present', 'coverage_unavailable'],
    pagination: { total_matching: 100, returned: 3, more_available: true, limit_per_source: 3, offset_per_source: 3 },
    rows: [
      { record_id: '0', density: null, qualification: 'context_only', data: { source_citation: 'fixture:legacy' },
        drill: { args: { chart_id: fixtureChart, source_table: 'kala_darshana', record_id: '0' } } },
      { record_id: '10', density: null, data: { tier: 'testimony', source_citation: 'fixture:10' },
        drill: { args: { chart_id: fixtureChart, assertion_id: 'a10' } } },
      { record_id: '2', density: null, data: { tier: 'confirmed', source_citation: 'fixture:2' },
        drill: { args: { chart_id: fixtureChart, assertion_id: 'a2' } } },
    ],
  })
  const sql = db.mock.calls[0][0]
  expect(sql).toContain('ORDER BY tier_order, record_id LIMIT $7 OFFSET $8')
  expect(sql).not.toContain('kala_darshana_candidate')
  expect(sql).not.toContain('kala_jivana_parva_candidate')
})

it.runIf(process.env.KALA_VIEW_DB_TESTS === '1').each(['kala_obstruction','kala_gochara_contacts','kala_bhavishya','kala_convergence','kala_jivana_parva'])(
  'real EXPLAIN SELECT carries %s own stored single and provenance without inheriting verdicts', async source_table => {
    const { explainViewCapability } = await import('./view_explain')
    db.mockReset().mockImplementation(postgresQuery)
    const record_id = source_table === 'kala_gochara_contacts' ? 'c1' : source_table === 'kala_obstruction' ? '101' : '1'
    const result = await explainViewCapability.handler!({ chart_id: fixtureChart, source_table, record_id }, {})
    expect(result).toMatchObject({ is_error: false, content: { rows: [{ source_table,
      data: { verification_pass_status: 'single' }, verification: { column: `${source_table}.verification_pass_status`, status: 'single' },
      density: ['kala_obstruction','kala_gochara_contacts'].includes(source_table) ? 'catalog_only' : null,
    }] } })
  },
)
it.runIf(process.env.KALA_VIEW_DB_TESTS === '1')('real SQL does not give contact verification credit to a different build sharing the generation label', async () => {
  const { explainViewCapability } = await import('./view_explain')
  db.mockReset().mockImplementation((sql,params) => postgresQuery(sql,params,
    "UPDATE kala_gochara_contacts SET build_id = '99999999-9999-4999-8999-999999999999', verification_pass_status = 'two_pass_verified';"))
  expect(await explainViewCapability.handler!({ chart_id: fixtureChart, source_table: 'kala_gochara_contacts', record_id: 'c1' }, {}))
    .toMatchObject({ is_error: false, content: { rows: [{ density: null, qualification: 'context_only',
      verification: { status: 'two_pass_verified', manifest_id: null },
    }] } })
})

// K9-6: the installed MCP public name -> public registry -> actual SQL path.
// No HTTP server or production endpoint is used; fetch is the local wire harness.
vi.mock('../../../../../../../platform-mcp/src/lib/authz.js', () => ({ remoteAuthorize: async () => true }))
it.runIf(process.env.KALA_VIEW_DB_TESTS === '1').each(['now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain'])
  ('K9-6 installed public %s carries the SQL-published manifest through the Vidhi identity', async view => {
    const { registerAllKalaViews } = await import('../../../../../../../platform-mcp/src/tools/kala_views/register_all')
    const { getCapability, getCatalog } = await import('../../index')
    const { resolveWebToolBridge } = await import('../../../../../../scripts/manifest/web_tool_bridge_builder')
    const name = `kala_${view}_get`, uri = `marsys://tool/L3/${name}`
    await import('./index')
    expect(resolveWebToolBridge([name], getCatalog(), {}, {}, { canonical_faces: [], deprecated_aliases: {} }))
      .toEqual([{ name, uri, resolution_kind: 'catalog_name_direct', via: [] }])
    db.mockReset().mockImplementation(postgresQuery)
    const fetcher = vi.fn(async (_url: unknown, init: RequestInit) => {
      const request = JSON.parse(String(init.body))
      expect(request.uri).toBe(uri)
      return { ok: true, json: async () => ({ ok: true, content: await getCapability(uri)!.handler!(request.args, {}) }) }
    })
    vi.stubGlobal('fetch', fetcher)
    const tools = new Map<string, (args: Record<string, unknown>) => Promise<unknown>>()
    registerAllKalaViews({ tool(tool: string, _description: unknown, _shape: unknown,
      callback: (args: Record<string, unknown>) => Promise<unknown>) { tools.set(tool, callback) },
    } as unknown as Parameters<typeof registerAllKalaViews>[0], { user_uid: 'fixture', key_id: 'fixture', role: 'guest' })
    try {
      const response = await tools.get(name)!({ chart_id: fixtureChart, published_request: {
        at: '2026-10-09T12:00:00Z', date_from: '2026-10-09T00:00:00Z', date_to: '2026-10-10T00:00:00Z',
        event_class: 'travel', assertion_id: 'a1',
      } }) as { structuredContent: { object: Record<string, unknown> } }
      const content = response.structuredContent.object
      expect(content).toMatchObject({ view, chart_id: fixtureChart, manifest_id: '22222222-2222-4222-8222-222222222222',
        generation: '4.1', empty_reason: null })
      expect(fetcher).toHaveBeenCalledTimes(1)
      expect(JSON.stringify(content)).not.toContain('9.9')
      if (process.env.K9_CAPTURE_DIR) {
        const { writeFileSync } = await import('node:fs')
        writeFileSync(`${process.env.K9_CAPTURE_DIR}/${view}.json`, JSON.stringify({ source: 'local_guarded_fixture', name, uri, content }, null, 2))
      }
    } finally { vi.unstubAllGlobals() }
  })
it.runIf(process.env.KALA_VIEW_DB_TESTS === '1').each(['information_unavailable', 'evaluated_silent'])
  ('K9-6 public NOW preserves planted %s with its null release', async state => {
    await import('./index')
    const { getCapability } = await import('../../index')
    db.mockReset().mockImplementation((sql, params) => postgresQuery(sql, params,
      `UPDATE kala_obstruction SET assertion = jsonb_set(assertion, '{payload,effective_state}', '"${state}"'::jsonb);`))
    const result = await getCapability('marsys://tool/L3/kala_now_get')!.handler!({ chart_id: fixtureChart,
      published_request: { at: '2026-10-09T12:00:00Z' } }, {})
    expect(result.is_error).toBe(false)
    expect(result.content).toMatchObject({ rows: expect.arrayContaining([expect.objectContaining({ source_table: 'kala_obstruction',
      data: expect.objectContaining({ assertion: expect.objectContaining({ payload: expect.objectContaining({
        effective_state: state, release: { kind: 'unknown', instant: null },
      }) }) }),
    })]) })
    const { arrivalFromPublishedNow } = await import('./arrival_state')
    const { ArrivalLine } = await import('@/components/pariprashna/ArrivalLine')
    const { createElement } = await import('react')
    const { renderToStaticMarkup } = await import('react-dom/server')
    const arrival = arrivalFromPublishedNow(fixtureChart, result.content)
    expect(arrival?.effective_states).toContain(state)
    const html = renderToStaticMarkup(createElement(ArrivalLine, { arrival }))
    expect(html).toContain(state === 'information_unavailable' ? 'information unavailable' : 'evaluated silence')
    if (process.env.K9_CAPTURE_DIR) {
      const { writeFileSync } = await import('node:fs')
      writeFileSync(`${process.env.K9_CAPTURE_DIR}/now-${state}.json`, JSON.stringify({
        source: 'local_guarded_fixture', content: result.content, arrival, rendered_html: html,
      }, null, 2))
    }
  })
