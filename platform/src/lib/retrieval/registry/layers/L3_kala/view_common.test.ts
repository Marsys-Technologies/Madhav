import { existsSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { build } from 'esbuild'
import { beforeEach, expect, it, vi } from 'vitest'
const db = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: db }))
beforeEach(() => db.mockReset())
async function common() {
  expect(existsSync(new URL('./view_common.ts', import.meta.url))).toBe(true)
  return import('./view_common')
}
const manifest = { manifest_id: 'build-7', generation: '4.1', model_digest: 'digest',
  rule_registry_version: 'rules-2', conventions: { ayanamsha: 'lahiri' } }
const assertion = { assertion_id: 'a1', generation: '4.1', operator_role: 'scored',
  role: 'corroborates', roots: { contact_ids: ['contact-1'], fact_ids: ['fact-1'], record_ids: [] },
  coverage_ref: 'coverage-1', payload: { effective_state: 'obstruction_cancelled' } }

it('the web view bundles entirely inside its Docker build context', async () => {
  const result = await build({
    absWorkingDir: fileURLToPath(new URL('../../../../../../', import.meta.url)),
    entryPoints: ['src/lib/retrieval/registry/layers/L3_kala/view_common.ts'],
    bundle: true, platform: 'node', write: false, metafile: true,
    external: ['@/lib/db/client'],
  })
  expect(Object.keys(result.metafile!.inputs).every(path => path.startsWith('src/'))).toBe(true)
})

it('ELECT preserves the canonical MCP undertaking vocabulary and order', async () => {
  const { MUHURTA_UNDERTAKINGS } = await import('../../../../../../../platform-mcp/src/lib/muhurta_undertakings')
  const { legacyViewContract } = await common()
  expect(legacyViewContract('elect').input_schema.undertaking.enum).toEqual([...MUHURTA_UNDERTAKINGS])
})

it.each(['now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain'] as const)(
  '%s density facets select stored subject/source rows rather than naming output tiers', async name => {
    const { makeView } = await common()
    const capability = makeView({ name, description: 'Stored-stage fixture', sources: ['kala_darshana'], required: [] })
    expect(capability.density_contract?.facets).toEqual(['event_class', 'source_table'])
    db.mockResolvedValue({ rows: [{ manifest, coverage: [], sources: [] }] })
    await capability.handler!({ chart_id: 'chart', event_class: 'travel', source_table: 'kala_darshana', record_id: '1' }, {})
    expect(db.mock.calls[0][1]).toEqual(['chart', null, null, null, 'travel', null, 25, 0, 'kala_darshana', '1'])
  },
)

it.each([
  ['now', { as_of: '2026-10-09', ayanamsha_id: 'lahiri_chitrapaksha' }],
  ['ahead', { horizon_years: 5, max_items: 20 }],
  ['priority', { date_from: '2026-10-09', date_to: '2027-01-07', top_k: 20, domain: 'career' }],
  ['elect', { undertaking: 'travel', date_range: { start: '2026-10-09', end: '2026-10-10' }, limit: 5 }],
  ['story', { top_k: 739 }],
  ['ritual', { undertaking: 'travel', horizon: '90d' }],
  ['explain', { domain: 'career', as_of_date: '2026-10-09', max_signals: 15 }],
])('the %s adapter preserves legacy arguments and response/error envelope after authorization', async (name, selectors) => {
  const { makeLegacyViewHandler } = await import('./view_common')
  const args = { chart_id: '11111111-1111-4111-8111-111111111111', ...selectors,
    question_frame: { domain: 'career', stakes: 'high' } }
  const response = { content: { tool: `kala_${name}_get`, question_frame: args.question_frame,
    reading: { thesis: 'Stored legacy fixture' }, field_snapshot_id: null }, metadata: { receipt: 'legacy' } }
  const events: unknown[] = []
  const handler = makeLegacyViewHandler(name as import('./view_common').ViewName, {
    async authorize(chart) { events.push(['authorize', chart]); return true },
    async invoke(tool, request, context) { events.push(['invoke', tool, request, context]); return response },
  })
  expect(await handler(args, { request_id: 'request-7' })).toEqual(response)
  expect(events).toEqual([['authorize', args.chart_id], ['invoke', `kala_${name}_get`, args, { request_id: 'request-7' }]])
})
it('denied charts never reach a legacy adapter or stage SQL', async () => {
  const { makeLegacyViewHandler } = await import('./view_common')
  const handler = makeLegacyViewHandler('now', { authorize: async () => false,
    invoke: async () => { throw new Error('must not execute') } })
  expect(await handler({ chart_id: '11111111-1111-4111-8111-111111111111' }))
    .toMatchObject({ is_error: true, content: { empty_reason: 'authorization_denied', manifest_id: null } })
  expect(db).not.toHaveBeenCalled()
})
it('legacy refusal and Mode-3 envelopes are forwarded without converting them into a stage answer', async () => {
  const { makeLegacyViewHandler } = await import('./view_common')
  const response = { is_error: false, content: { tool: 'kala_ritual_get', wrong_view: true,
    correct_view: 'kala_elect_get', undertaking: 'travel' } }
  const handler = makeLegacyViewHandler('ritual', { authorize: async () => true,
    invoke: async () => response })
  expect(await handler({ chart_id: '11111111-1111-4111-8111-111111111111', undertaking: 'travel' })).toBe(response)
  const error = { is_error: true, content: { tool: 'kala_explain_get', error: 'domain or bhava required' } }
  expect(await makeLegacyViewHandler('explain', { authorize: async () => true, invoke: async () => error })
    ({ chart_id: '11111111-1111-4111-8111-111111111111' })).toBe(error)
})
it('authorization exceptions fail closed before invoking legacy code', async () => {
  const { makeLegacyViewHandler } = await import('./view_common')
  expect(await makeLegacyViewHandler('now', { authorize: async () => { throw new Error('private authority detail') },
    invoke: async () => { throw new Error('must not execute') } })
    ({ chart_id: '11111111-1111-4111-8111-111111111111' }))
    .toMatchObject({ is_error: true, content: { empty_reason: 'authorization_unavailable' } })
})
it('absent legacy clock/horizon/identity fields stay absent for the established handler defaults', async () => {
  const { makeLegacyViewHandler } = await import('./view_common')
  const args = { chart_id: '11111111-1111-4111-8111-111111111111' }
  const handler = makeLegacyViewHandler('now', { authorize: async () => true,
    invoke: async (_tool, request) => ({ content: request }) })
  expect((await handler(args)).content).toEqual(args)
})
it('adapter exceptions cannot expose infrastructure details or claim a successful answer', async () => {
  const { makeLegacyViewHandler } = await import('./view_common')
  const handler = makeLegacyViewHandler('elect', { authorize: async () => true,
    invoke: async () => { throw new Error('private infrastructure detail') } })
  const result = await handler({ chart_id: '11111111-1111-4111-8111-111111111111' })
  expect(result).toMatchObject({ is_error: true, content: { empty_reason: 'legacy_query_failed', manifest_id: null } })
  expect(JSON.stringify(result)).not.toContain('private infrastructure')
})

it('populated response carries manifest, exact roots and a usable drill', async () => {
  const { composeView } = await common()
  const result = composeView('now', 'chart', { manifest, coverage: [], sources: [
    { table: 'kala_darshana', total: 1, rows: [{ id: '1', generation: '4.1', assertion }] },
  ] })
  expect(result).toMatchObject({ manifest_id: 'build-7', empty_reason: null, rows: [
    { density: null, data: { assertion }, drill: { capability: 'marsys://tool/L3/explain_read',
      args: { chart_id: 'chart', assertion_id: 'a1' } } },
  ] })
})
it('roles cannot classify missing-tier rows; context remains separately counted', async () => {
  const { composeView } = await common()
  const result = composeView('now', 'chart', { manifest, coverage: [], sources: [
    { table: 'kala_darshana', total: 5, rows: [
      { id: '1', generation: '4.1', assertion },
      { id: '2', generation: '4.1', assertion: { ...assertion, operator_role: 'testimony' } },
      { id: '3', generation: '4.1', assertion: { ...assertion, role: 'selects' } },
      { id: '4', generation: '3.0', assertion }, { id: '5', generation: '4.1' },
    ] },
  ] })
  expect(result.density).toEqual({ scope: 'page', confirmed: 0, testimony: 0, catalog_only: 0, context_only: 1, unknown: 5 })
})
it.each(['information_unavailable', 'method_inapplicable', 'outside_risk_set'])('does not confirm unavailable negative-space state %s', async state => {
  const { composeView } = await common()
  const result = composeView('now', 'chart', { manifest, coverage: [], sources: [
    { table: 'kala_darshana', total: 1, rows: [{ id: '1', generation: '4.1', assertion: {
      ...assertion, payload: { effective_state: state },
    } }] },
  ] })
  expect(result.density.confirmed).toBe(0)
})
it('unpublished response names an empty reason and never serves private/context rows', async () => {
  const { composeView } = await common()
  expect(composeView('now', 'chart', { manifest: null, coverage: [], sources: [
    { table: 'kala_darshana', total: 1, rows: [{ id: '1', assertion }] },
  ] })).toMatchObject({ manifest_id: null, empty_reason: 'unpublished', rows: [] })
})
it('published empty page preserves coverage and names no_matching_rows', async () => {
  const { composeView } = await common()
  expect(composeView('now', 'chart', { manifest, coverage: [{ unsearched_reason: 'moon_on_demand' }], sources: [] }))
    .toMatchObject({ manifest_id: 'build-7', empty_reason: 'no_matching_rows', coverage: [{ unsearched_reason: 'moon_on_demand' }] })
})
it('reports bounded page totals without claiming full-result density', async () => {
  const { composeView } = await common()
  expect(composeView('now', 'chart', { manifest, coverage: [], sources: [
    { table: 'kala_darshana', total: 12, rows: [{ id: '1', generation: '4.1', assertion }] },
  ] })).toMatchObject({ pagination: { total_matching: 12, returned: 1, more_available: true } })
})
it('source lint rejects local primitive computations and external engines in every view', async () => {
  await common()
  const ts = await import('typescript')
  const inspect = (source: string) => {
    const found: string[] = []
    const visit = (n: import('typescript').Node) => {
      if (ts.isImportDeclaration(n) && /panchang|ephemeris|swisseph|transit_search|calendar/.test(n.moduleSpecifier.getText())) found.push('engine')
      if (ts.isBinaryExpression(n) && n.operatorToken.kind === ts.SyntaxKind.PercentToken) found.push('primitive')
      ts.forEachChild(n, visit)
    }
    visit(ts.createSourceFile('view.ts', source, ts.ScriptTarget.Latest, true))
    return found
  }
  for (const name of ['common', 'now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain']) {
    expect(inspect(readFileSync(new URL(`./view_${name}.ts`, import.meta.url), 'utf8'))).toEqual([])
  }
  expect(inspect('const tithi = elongation % 360')).toEqual(['primitive'])
  expect(inspect('import engine from "calendar/primitive"')).toEqual(['engine'])
})
it.each([
  { operator_role: 'scored', role: 'invented' },
  { operator_role: 'scored', role: undefined },
  { operator_role: 'scored', role: 'corroborates', roots: {} },
])('unqualified operator/role/roots cannot earn confirmation: %j', async changes => {
  const { composeView } = await common()
  expect(composeView('now', 'chart', { manifest, coverage: [], sources: [
    { table: 'kala_darshana', total: 1, rows: [{ id: '1', generation: '4.1', assertion: { ...assertion, ...changes } }] },
  ] }).density.confirmed).toBe(0)
})

// B1: independent review's missing/contrary-tier fixtures, using the shared roots.
it.each(['now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain'] as const)(
  '%s must not confirm a row without producer tier proof', async view => {
    const { composeView } = await common()
    const result = composeView(view, 'review-chart', { manifest, coverage: [], sources: [
      { table: 'kala_darshana', total: 1, rows: [{ id: '1', generation: '4.1', assertion }] },
    ] })
    expect(result.rows[0].density).toBeNull()
  },
)
it.each(['now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain'] as const)(
  '%s must not promote a contextual stored tier from role/roots', async view => {
    const { composeView } = await common()
    const result = composeView(view, 'review-chart', { manifest, coverage: [], sources: [
      { table: 'kala_darshana', total: 1, rows: [{ id: '1', generation: '4.1', tier: 'contextual', assertion }] },
    ] })
    expect(result.rows[0].density).not.toBe('confirmed')
  },
)

it.each(['now', 'ahead', 'priority', 'elect', 'story', 'ritual', 'explain'] as const)(
  '%s declares its stored tier binding on the reader entry and cannot rank roles as verification', async name => {
    const { makeView } = await common()
    const capability = makeView({ name, description: 'B1 fixture', sources: ['kala_darshana'], required: [] })
    expect(capability.density_contract).toMatchObject({ stored_tier_columns: ['kala_darshana.verification_pass_status'],
      unavailable_sources: [] })
    db.mockResolvedValue({ rows: [{ manifest, coverage: [], sources: [] }] })
    await capability.handler!({ chart_id: 'chart' }, {})
    const sql = db.mock.calls[0][0]
    expect(sql).not.toContain("s.assertion->>'operator_role'")
    expect(sql).not.toContain('jsonb_array_length')
    expect(sql).toContain("to_jsonb(s)->>'verification_pass_status'")
  },
)

it.each(['kala_darshana', 'kala_obstruction', 'kala_gochara_contacts', 'kala_bhavishya',
  'kala_convergence', 'kala_jivana_parva'])(
  '%s cannot infer density from tier_basis, geometry, confidence or an unbound label', async table => {
    const { composeView } = await common()
    const stored = { id: '1', generation: '4.1', assertion, tier: 'confirmed',
      tier_basis: 'two_pass_verified', confidence_score: 1, source_citation: 'fixture:source',
      upstream_refs: { build_id: 'fixture:build' } }
    const result = composeView('explain', 'chart', { manifest, coverage: [], sources: [
      { table, total: 1, rows: [stored] },
    ] })
    expect(result.rows[0]).toMatchObject({ density: null, density_reason: 'stored_tier_contract_unavailable',
      data: { tier: 'confirmed', tier_basis: 'two_pass_verified', source_citation: 'fixture:source',
        upstream_refs: { build_id: 'fixture:build' } } })
    expect(result.density).toMatchObject({ confirmed: 0, testimony: 0, unknown: 1 })
    expect(result.catalog_only_rows_in_page).toBe(1)
  },
)

it('K7-4 PRIORITY public adapter keeps preference with the established name', async () => {
  const { makeLegacyViewHandler } = await common()
  const invoke = vi.fn(async (_tool, args) => ({ content: args }))
  const handler = makeLegacyViewHandler('priority', { authorize: async () => true, invoke })
  const args = { chart_id: '11111111-1111-4111-8111-111111111111', question_frame: { domain: 'career' }, preference: ['nearest'] }
  expect((await handler(args)).content).toEqual(args)
  expect(invoke.mock.calls[0][0]).toBe('kala_priority_get')
})
