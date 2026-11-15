import { beforeEach, describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'
import { NextRequest } from 'next/server'
import type { Queryable } from '@/lib/build/runPreparation'

const h = vi.hoisted(() => ({
  query: vi.fn(), getPool: vi.fn(), user: vi.fn(), permission: vi.fn(),
  planning: vi.fn(), plan: vi.fn(), freeze: vi.fn(), persist: vi.fn(), active: vi.fn(),
  invalidate: vi.fn(), dispatch: vi.fn(), image: vi.fn(),
}))
vi.mock('@/lib/db/client', () => ({ query: h.query, getPool: h.getPool }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: h.user }))
vi.mock('@/lib/auth/requireChartPermission', () => ({ requireChartPermission: h.permission }))
vi.mock('@/lib/cloud_run/jobs', () => ({ getJobImageTag: h.image }))
vi.mock('@/lib/build/runDispatch', () => ({ dispatchPreparedRun: h.dispatch }))
vi.mock('@/lib/build/runPreparation', async original => ({
  ...await original<typeof import('@/lib/build/runPreparation')>(),
  loadPlanningInputs: h.planning, planRun: h.plan, freezeRunManifest: h.freeze,
  persistPreparedRun: h.persist, findActiveRun: h.active,
}))
vi.mock('@/lib/build/assetInvalidation', async original => ({
  ...await original<typeof import('@/lib/build/assetInvalidation')>(), invalidateAssets: h.invalidate,
}))

import * as owner from '@/lib/build/runRequestData'
import { POST } from '@/app/api/cockpit/runs/route'

const PORTS = {
  readRequestedAssetScope: ['scope_target'],
  readBodhaRunPreconditions: ['chart_id'],
  resetClearedRunAssetState: ['client', 'chart_id', 'clearedAssetIds'],
  markClearedRunDownstreamStale: ['client', 'chart_id', 'downstreamAssets'],
  readClearedRunAssetMarker: ['chart_id', 'plan'],
} as const
const TRANSACTION_SQL = new Set(['BEGIN', 'BEGIN ISOLATION LEVEL SERIALIZABLE', 'COMMIT', 'ROLLBACK'])
const routePath = fileURLToPath(new URL('../../../app/api/cockpit/runs/route.ts', import.meta.url))

/** Exact existing caller seam, not a universal SQL or lexical-analysis policy. */
function inspectRoute(text: string): string[] {
  const file = ts.createSourceFile('route.ts', text, ts.ScriptTarget.Latest, true)
  const errors: string[] = []
  const post = file.statements.find((n): n is ts.FunctionDeclaration => ts.isFunctionDeclaration(n) && n.name?.text === 'POST')
  if (!post?.body || (file as ts.SourceFile & { readonly parseDiagnostics: readonly ts.Diagnostic[] }).parseDiagnostics.length) return ['POST parse/body']
  const imports = file.statements.filter(ts.isImportDeclaration)
  const declared = imports.flatMap(n => ts.isStringLiteral(n.moduleSpecifier) && n.moduleSpecifier.text === '@/lib/build/runRequestData'
    && n.importClause?.namedBindings && ts.isNamedImports(n.importClause.namedBindings)
    ? [...n.importClause.namedBindings.elements] : [])
  if (declared.length !== 5 || declared.some(n => !Object.hasOwn(PORTS, n.name.text) || (n.propertyName && n.propertyName.text !== n.name.text))) errors.push('owner imports')
  const enclosing = (node: ts.Node): ts.Node | undefined => {
    let p = node.parent
    while (p && !ts.isFunctionLike(p)) p = p.parent
    return p
  }
  const binds = (node: ts.Node, name: string): boolean => {
    if (ts.isVariableDeclaration(node) || ts.isParameter(node) || ts.isFunctionDeclaration(node) || ts.isClassDeclaration(node)) {
      return Boolean(node.name && ts.isIdentifier(node.name) && node.name.text === name)
    }
    return false
  }
  const shadowed = (call: ts.Node, name: string): boolean => {
    for (let scope: ts.Node | undefined = call.parent; scope && scope !== file; scope = scope.parent) {
      if (ts.isBlock(scope)) {
        for (const statement of scope.statements) {
          if (binds(statement, name)) return true
          if (ts.isVariableStatement(statement) && statement.declarationList.declarations.some(n => binds(n, name))) return true
        }
      }
      if (ts.isFunctionLike(scope) && scope.parameters.some(n => binds(n, name))) return true
    }
    return false
  }
  const seen = new Map<string, number>()
  let role = 0, transactions = 0
  function visit(node: ts.Node) {
    if (ts.isCallExpression(node)) {
      const callee = node.expression
      if (ts.isIdentifier(callee) && Object.hasOwn(PORTS, callee.text) && enclosing(node) === post) {
        const name = callee.text as keyof typeof PORTS
        seen.set(name, (seen.get(name) ?? 0) + 1)
        if (JSON.stringify(node.arguments.map(n => n.getText(file))) !== JSON.stringify(PORTS[name]) || shadowed(node, name)) errors.push(`binding:${name}`)
      }
      if ((ts.isIdentifier(callee) && callee.text === 'query') || (ts.isPropertyAccessExpression(callee) && callee.name.text === 'query')) {
        const sql = node.arguments[0]
        if (!sql || !(ts.isStringLiteral(sql) || ts.isNoSubstitutionTemplateLiteral(sql))) errors.push('nonliteral caller query')
        else if (ts.isIdentifier(callee) && callee.text === 'query'
          && ts.isFunctionDeclaration(enclosing(node)!) && (enclosing(node) as ts.FunctionDeclaration).name?.text === 'getUserRole'
          && sql.text === 'SELECT role FROM profiles WHERE id=$1' && node.arguments[1]?.getText(file) === '[uid]') role++
        else if (enclosing(node) === post && ts.isPropertyAccessExpression(callee)
          && ['client', 'checkClient'].includes(callee.expression.getText(file)) && TRANSACTION_SQL.has(sql.text)) transactions++
        else errors.push('caller-owned domain query')
      }
    }
    ts.forEachChild(node, visit)
  }
  visit(file)
  if (role !== 1 || transactions !== 9) errors.push('Identity/transaction shape')
  for (const name of Object.keys(PORTS)) if (seen.get(name) !== 1) errors.push(`delegate:${name}`)
  return errors
}

const CHART = 'fixture-chart', ASSET = 'bo_fixture'
const registry = [
  { asset_id: ASSET, layer: 'bodha', scope: 'per_chart', has_writer: true, depends_on: [], target_table: 'fixture_a', asset_kind: 'data', asset_type: 'data' },
  { asset_id: 'ph_downstream', layer: 'phala', scope: 'per_chart', has_writer: true, depends_on: [ASSET], target_table: 'fixture_b', asset_kind: 'data', asset_type: 'data' },
]
let client: { query: ReturnType<typeof vi.fn>; release: ReturnType<typeof vi.fn> }
beforeEach(() => {
  vi.restoreAllMocks()
  vi.resetAllMocks()
  client = { query: vi.fn().mockResolvedValue({ rows: [], rowCount: 0 }), release: vi.fn() }
  h.getPool.mockResolvedValue({ connect: vi.fn().mockResolvedValue(client) })
  h.user.mockResolvedValue({ uid: 'fixture-owner' })
  h.permission.mockResolvedValue(null)
  h.active.mockResolvedValue(null)
  h.planning.mockResolvedValue({ registry, protectedAssetIds: new Set(), throughput: new Map(), freshness: new Map() })
  h.plan.mockReturnValue({ plan: [ASSET], buildPlan: { plan_waves: [[ASSET]], protected_assets: [] } })
  h.freeze.mockReturnValue({ manifest: { fixture: true }, digest: 'fixture-digest' })
  h.persist.mockResolvedValue('fixture-run')
  h.invalidate.mockResolvedValue({ clearedAssetIds: [ASSET], failedAssetIds: [], notices: [] })
  h.dispatch.mockResolvedValue({ ok: true })
  h.image.mockResolvedValue('fixture-image')
  h.query.mockImplementation((sql: string) => {
    if (sql.includes('FROM profiles')) return Promise.resolve({ rows: [{ role: 'guest' }] })
    if (sql.includes('SELECT scope')) return Promise.resolve({ rows: [{ scope: 'per_chart' }] })
    if (sql.includes("asset_id='ga_structural'")) return Promise.resolve({ rows: [{ state: 'lit' }] })
    if (sql.includes('count(*)')) return Promise.resolve({ rows: [{ count: '1' }] })
    return Promise.resolve({ rows: [] })
  })
})
const request = (clear = false) => new NextRequest('http://localhost/api/cockpit/runs', {
  method: 'POST', body: JSON.stringify({ chart_id: CHART, scope: 'asset', scope_target: ASSET, action: clear ? 'rebuild' : 'build', clear_before: clear }),
})

describe('actual run request delegates', () => {
  it('calls the actual read ports with the authorized chart and uses the marker result', async () => {
    const scope = vi.spyOn(owner, 'readRequestedAssetScope'), prerequisites = vi.spyOn(owner, 'readBodhaRunPreconditions'), marker = vi.spyOn(owner, 'readClearedRunAssetMarker')
    const res = await POST(request())
    expect(res.status).toBe(201)
    expect(scope).toHaveBeenCalledExactlyOnceWith(ASSET)
    expect(prerequisites).toHaveBeenCalledExactlyOnceWith(CHART)
    expect(marker).toHaveBeenCalledExactlyOnceWith(CHART, [ASSET])
    expect(h.dispatch).toHaveBeenCalledExactlyOnceWith('fixture-run', {})
  })
  it('calls the actual borrowed-client write ports inside the existing clear transaction', async () => {
    const reset = vi.spyOn(owner, 'resetClearedRunAssetState'), stale = vi.spyOn(owner, 'markClearedRunDownstreamStale')
    const res = await POST(request(true))
    expect(res.status).toBe(201)
    expect(reset).toHaveBeenCalledExactlyOnceWith(client, CHART, [ASSET])
    expect(stale).toHaveBeenCalledExactlyOnceWith(client, CHART, ['ph_downstream'])
    expect(client.query.mock.calls.map(([sql]) => sql)).toEqual(expect.arrayContaining(['BEGIN', 'COMMIT']))
    expect(h.dispatch).toHaveBeenCalledExactlyOnceWith('fixture-run', { forceExecute: true })
  })
  it('denies before any Build data port, pool acquisition or dispatch', async () => {
    const scope = vi.spyOn(owner, 'readRequestedAssetScope'), prerequisites = vi.spyOn(owner, 'readBodhaRunPreconditions')
    h.permission.mockResolvedValue(new Response(null, { status: 403 }))
    expect((await POST(request(true))).status).toBe(403)
    expect(scope).not.toHaveBeenCalled()
    expect(prerequisites).not.toHaveBeenCalled()
    expect(h.getPool).not.toHaveBeenCalled()
    expect(h.dispatch).not.toHaveBeenCalled()
  })
})

describe('Build run data port SQL and chart binds', () => {
  it('preserves the asset scope query and raw result', async () => {
    const result = { rows: [{ scope: 'global' }] }; h.query.mockResolvedValue(result)
    expect(await owner.readRequestedAssetScope('fixture-global')).toBe(result)
    expect(h.query).toHaveBeenCalledExactlyOnceWith('SELECT scope FROM asset_registry WHERE asset_id=$1', ['fixture-global'])
    expect(h.getPool).not.toHaveBeenCalled()
  })
  it('keeps all three upstream reads, argument order, and their raw results', async () => {
    const results = [{ rows: [{ count: '7' }] }, { rows: [{ state: 'error' }] }, { rows: [{ count: '0' }] }]
    h.query.mockResolvedValueOnce(results[0]).mockResolvedValueOnce(results[1]).mockResolvedValueOnce(results[2])
    expect(await owner.readBodhaRunPreconditions(CHART)).toEqual(results)
    expect(h.query.mock.calls).toEqual([
      ['SELECT count(*)::text AS count FROM chart_facts WHERE chart_id=$1', [CHART]],
      ["SELECT state FROM asset_throughput WHERE chart_id=$1 AND asset_id='ga_structural'", [CHART]],
      ['SELECT count(*)::text AS count FROM brahma_remedy_corpus'],
    ])
  })
  it('passes upstream SQL errors through without changing the request policy', async () => {
    const error = new Error('fixture read failure'); h.query.mockRejectedValueOnce(error)
    await expect(owner.readBodhaRunPreconditions(CHART)).rejects.toBe(error)
  })
  it('keeps guarded successful-clear and downstream writes on the supplied client', async () => {
    await owner.resetClearedRunAssetState(client as unknown as Queryable, CHART, ['cleared'])
    await owner.markClearedRunDownstreamStale(client as unknown as Queryable, CHART, ['downstream'])
    expect(client.query).toHaveBeenCalledTimes(2)
    expect(client.query.mock.calls[0][0]).toContain("SET state='dormant', last_built_at=NULL, rows_written=NULL")
    expect(client.query.mock.calls[0][0]).toContain('WHERE chart_id=$1 AND asset_id = ANY($2::text[])')
    expect(client.query.mock.calls[0][1]).toEqual([CHART, ['cleared']])
    expect(client.query.mock.calls[1]).toEqual([expect.stringContaining("AND state IN ('lit','building','error')"), [CHART, ['downstream']]])
    expect(h.query).not.toHaveBeenCalled()
    expect(h.getPool).not.toHaveBeenCalled()
    expect(client.release).not.toHaveBeenCalled()
  })
  it.each([
    ['resetClearedRunAssetState', owner.resetClearedRunAssetState],
    ['markClearedRunDownstreamStale', owner.markClearedRunDownstreamStale],
  ] as const)('passes %s errors through without commit, rollback or release', async (_name, write) => {
    const error = new Error('fixture write failure'); client.query.mockRejectedValue(error)
    await expect(write(client as unknown as Queryable, CHART, ['cleared'])).rejects.toBe(error)
    expect(client.query).toHaveBeenCalledTimes(1)
    expect(client.release).not.toHaveBeenCalled()
  })
  it('keeps the clear marker filter, chart/plan binds and raw result', async () => {
    const result = { rows: [{ asset_id: ASSET }] }; h.query.mockResolvedValue(result)
    expect(await owner.readClearedRunAssetMarker(CHART, [ASSET])).toBe(result)
    expect(h.query.mock.calls[0][0]).toContain("AND state='dormant' AND last_built_at IS NULL")
    expect(h.query.mock.calls[0][0]).toContain('LIMIT 1')
    expect(h.query.mock.calls[0][1]).toEqual([CHART, [ASSET]])
  })
})

describe('run request source boundary', () => {
  it('keeps Identity and transaction control locally and delegates seven domain statements', () => {
    expect(inspectRoute(readFileSync(routePath, 'utf8'))).toEqual([])
  })
  it('rejects an actual additional inline domain statement', () => {
    const text = readFileSync(routePath, 'utf8').replace('const inputs = await loadPlanningInputs', "await query('SELECT count(*) FROM chart_facts')\n  const inputs = await loadPlanningInputs")
    expect(inspectRoute(text)).toContain('caller-owned domain query')
  })
  it('rejects a disconnected actual delegate despite an imported name or comment decoy', () => {
    const text = readFileSync(routePath, 'utf8').replace('await readBodhaRunPreconditions(chart_id)', "await Promise.resolve([{rows:[]},{rows:[]},{rows:[]}]) /* readBodhaRunPreconditions(chart_id) */")
    expect(inspectRoute(text)).toContain('delegate:readBodhaRunPreconditions')
  })
  it('rejects an actual delegate shadow and a foreign-chart bind', () => {
    const text = readFileSync(routePath, 'utf8')
    expect(inspectRoute(text.replace('const inputs = await loadPlanningInputs', 'const readBodhaRunPreconditions = async () => []\n  const inputs = await loadPlanningInputs'))).toContain('binding:readBodhaRunPreconditions')
    expect(inspectRoute(text.replace('readBodhaRunPreconditions(chart_id)', "readBodhaRunPreconditions('foreign')"))).toContain('binding:readBodhaRunPreconditions')
  })
  it('ignores harmless comments and unrelated presentation scope', () => {
    const text = readFileSync(routePath, 'utf8') + '\n// query("not executable")\nfunction presentation(rows: string[]) { const readBodhaRunPreconditions = rows.find(x => x); return readBodhaRunPreconditions }\n'
    expect(inspectRoute(text)).toEqual([])
  })
})
