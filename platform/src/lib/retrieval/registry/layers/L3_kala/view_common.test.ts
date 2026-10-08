import { existsSync, readFileSync } from 'node:fs'
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

it('populated response carries manifest, exact roots and a usable drill', async () => {
  const { composeView } = await common()
  const result = composeView('now', 'chart', { manifest, coverage: [], sources: [
    { table: 'kala_darshana', total: 1, rows: [{ id: '1', generation: '4.1', assertion }] },
  ] })
  expect(result).toMatchObject({ manifest_id: 'build-7', empty_reason: null, rows: [
    { density: 'confirmed', data: { assertion }, drill: { capability: 'marsys://tool/L3/explain_read',
      args: { chart_id: 'chart', assertion_id: 'a1' } } },
  ] })
})
it('flattening testimony/catalog/context into confirmed fails the density oracle', async () => {
  const { composeView } = await common()
  const result = composeView('now', 'chart', { manifest, coverage: [], sources: [
    { table: 'kala_darshana', total: 5, rows: [
      { id: '1', generation: '4.1', assertion },
      { id: '2', generation: '4.1', assertion: { ...assertion, operator_role: 'testimony' } },
      { id: '3', generation: '4.1', assertion: { ...assertion, role: 'selects' } },
      { id: '4', generation: '3.0', assertion }, { id: '5', generation: '4.1' },
    ] },
  ] })
  expect(result.density).toEqual({ scope: 'page', confirmed: 1, testimony: 1, catalog_only: 3, context_only: 1 })
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
