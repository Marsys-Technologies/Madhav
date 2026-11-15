import { beforeEach, describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { createSourceFile, forEachChild, isCallExpression, isIdentifier, isPropertyAccessExpression, isStringLiteralLike, isVariableDeclaration, ScriptTarget } from 'typescript'

const m = vi.hoisted(() => ({ query: vi.fn(), access: vi.fn(), list: vi.fn(), order: [] as string[] }))
vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: m.query }))
vi.mock('@/lib/auth/chart-page-guard', () => ({ resolveChartPageAccess: m.access }))
vi.mock('@/lib/conversations', () => ({ listConversations: m.list }))
vi.mock('@/lib/config/index', () => ({ configService: { getFlag: () => false } }))
vi.mock('@/components/consume/ConsumeChat', () => ({ ConsumeChat: () => null }))
vi.mock('next/navigation', () => ({ redirect: (to: string) => { throw new Error(`redirect(${to})`) } }))

import ConsultPage from '@/app/clients/[id]/consult/page'
import { readChartPyramidLayers, legacyL1AvailabilityFromPyramid } from '../pyramidLayers'

const SQL = `SELECT layer AS layer_key, status FROM pyramid_layers WHERE chart_id = $1`
const CHART = 'chart'
const renderPage = () => ConsultPage({ params: Promise.resolve({ id: CHART }), searchParams: Promise.resolve({}) })

beforeEach(() => {
  vi.resetAllMocks()
  m.order.length = 0
  m.access.mockImplementation(async () => { m.order.push('access'); return { user: { uid: 'owner' }, permission: 'all', role: 'guest', canBuild: true } })
  m.list.mockImplementation(async () => { m.order.push('list'); return [] })
  m.query.mockImplementation(async (sql: string) => {
    if (sql === SQL) { m.order.push('layers'); return { rows: [{ layer_key: 'L1', status: 'built' }] } }
    m.order.push('chart')
    return { rows: [{ name: 'Chart', birth_date: 'date', birth_place: 'place', client_id: 'owner' }] }
  })
})

describe('Consult Build-layer read contract', () => {
  it.each([null, { permission: 'deny' }])('retains access redirects before either data read (%s)', async access => {
    m.access.mockResolvedValue(access)
    await expect(renderPage()).rejects.toThrow(access ? 'redirect(/dashboard)' : 'redirect(/login)')
    expect(m.query).not.toHaveBeenCalled()
    expect(m.list).not.toHaveBeenCalled()
  })

  it('retains the missing-chart redirect before conversations and layers', async () => {
    m.query.mockResolvedValue({ rows: [] })
    await expect(renderPage()).rejects.toThrow('redirect(/dashboard)')
    expect(m.query).toHaveBeenCalledExactlyOnceWith('SELECT name, birth_date, birth_place, client_id FROM charts WHERE id=$1', [CHART])
    expect(m.list).not.toHaveBeenCalled()
  })

  it('preserves access/chart/list/layer invocation order, exact SQL/binds and first-L1 cardinality', async () => {
    m.query.mockImplementation(async (sql: string) => {
      m.order.push(sql === SQL ? 'layers' : 'chart')
      return { rows: sql === SQL ? [{ layer_key: 'L1', status: 'building' }, { layer_key: 'L1', status: 'built' }] : [{ name: 'Chart', birth_date: 'date', birth_place: 'place', client_id: 'owner' }] }
    })
    const page = await renderPage()
    expect(m.order).toEqual(['access', 'chart', 'list', 'layers'])
    expect(m.query.mock.calls).toEqual([
      ['SELECT name, birth_date, birth_place, client_id FROM charts WHERE id=$1', [CHART]], [SQL, [CHART]],
    ])
    expect(m.list).toHaveBeenCalledExactlyOnceWith({ chartId: CHART, userId: 'owner', module: 'consume' })
    expect(page.props.children.props.capabilityGateState).toEqual({ state: 'l1-building', cockpitHref: '/clients/chart/nirmana' })
    expect(page.props.children.props.chartMeta).toBe('date · place')
    expect(page.props.children.props.reports).toEqual([])
  })

  it('retains the page-owned empty-layer fallback when the Build read fails', async () => {
    m.query.mockImplementation(async (sql: string) => {
      if (sql === SQL) throw new Error('layer read failed')
      return { rows: [{ name: 'Chart', client_id: 'owner' }] }
    })
    const page = await renderPage()
    expect(page.props.children.props.capabilityGateState).toEqual({ state: 'no-build', cockpitHref: '/clients/chart/nirmana' })
  })

  it('does not absorb the parallel conversation read failure', async () => {
    const error = new Error('conversation read failed')
    m.list.mockRejectedValue(error)
    await expect(renderPage()).rejects.toBe(error)
    expect(m.query).toHaveBeenCalledWith(SQL, [CHART])
  })
})

describe('Build pyramid-layer read owner', () => {
  it('returns the original query promise/result, with exact SQL/binds and no row transformation', async () => {
    const result = { rows: [{ layer_key: 'L1', status: 'complete' }], rowCount: 1 }
    const promise = Promise.resolve(result)
    m.query.mockReturnValue(promise)
    expect(readChartPyramidLayers(CHART)).toBe(promise)
    expect(await promise).toBe(result)
    expect(m.query).toHaveBeenCalledExactlyOnceWith(SQL, [CHART])
  })

  it('propagates the original error, leaving fallback policy to the page', async () => {
    const error = new Error('layer read failed')
    m.query.mockRejectedValue(error)
    await expect(readChartPyramidLayers(CHART)).rejects.toBe(error)
  })
})

function layerReadBoundary(source: string) {
  const file = createSourceFile('page.tsx', source, ScriptTarget.Latest, true)
  let ownerCalls = 0
  const inlineLayerReads: string[] = []
  function visit(node: Parameters<typeof forEachChild>[0]) {
    if (isCallExpression(node)) {
      if (isIdentifier(node.expression) && node.expression.text === 'readChartPyramidLayers') ownerCalls++
      if (node.arguments.some(arg => isStringLiteralLike(arg) && /\bpyramid_layers\b/.test(arg.text))) inlineLayerReads.push(node.expression.getText(file))
    }
    forEachChild(node, visit)
  }
  visit(file)
  return { ownerCalls, inlineLayerReads }
}

function l1AvailabilityBoundary(source: string) {
  const file = createSourceFile('page.tsx', source, ScriptTarget.Latest, true)
  let delegated = false
  const inlineDerivations: string[] = []
  function isPyramidRows(node: Parameters<typeof forEachChild>[0]) {
    return (isIdentifier(node) && node.text === 'pyramidRows')
      || (isPropertyAccessExpression(node) && isIdentifier(node.expression)
        && node.expression.text === 'pyramidResult' && node.name.text === 'rows')
  }
  function visit(node: Parameters<typeof forEachChild>[0]) {
    if (isVariableDeclaration(node) && isIdentifier(node.name) && node.name.text === 'l1Availability') {
      const value = node.initializer
      delegated = !!value && isCallExpression(value) && isIdentifier(value.expression)
        && value.expression.text === 'legacyL1AvailabilityFromPyramid' && value.arguments.length === 1
        && isPropertyAccessExpression(value.arguments[0]) && isIdentifier(value.arguments[0].expression)
        && value.arguments[0].expression.text === 'pyramidResult' && value.arguments[0].name.text === 'rows'
    }
    if (isCallExpression(node) && isPropertyAccessExpression(node.expression)
      && ['find', 'findIndex'].includes(node.expression.name.text) && isPyramidRows(node.expression.expression)) {
      inlineDerivations.push('pyramid row selection')
    }
    if (isPropertyAccessExpression(node) && node.name.text === 'status'
      && isIdentifier(node.expression) && node.expression.text === 'l1Row') {
      inlineDerivations.push('L1 status derivation')
    }
    forEachChild(node, visit)
  }
  visit(file)
  return { delegated, inlineDerivations }
}

describe('Consult delegates its Build read', () => {
  it('keeps the actual page Build read behind a server-only owner while retaining its chart gate', () => {
    const page = readFileSync(new URL('../../../app/clients/[id]/consult/page.tsx', import.meta.url), 'utf8')
    expect(layerReadBoundary(page)).toEqual({ ownerCalls: 1, inlineLayerReads: [] })
    expect(l1AvailabilityBoundary(page)).toEqual({ delegated: true, inlineDerivations: [] })
    expect(page).toContain('SELECT name, birth_date, birth_place, client_id FROM charts WHERE id=$1')
    expect(readFileSync(new URL('../pyramidLayers.ts', import.meta.url), 'utf8')).toMatch(/^import 'server-only'/)
  })

  it('allows unrelated presentation selection and comparisons beside the L1 owner call', () => {
    expect(l1AvailabilityBoundary(`
      const l1Availability = legacyL1AvailabilityFromPyramid(pyramidResult.rows)
      const item = presentationRows.find(row => row.status === 'visible')
      const active = item?.status === 'active'
      // pyramidRows.find(row => row.layer_key === 'L1') is only a comment
    `)).toEqual({ delegated: true, inlineDerivations: [] })
  })

  it.each(['pyramidRows', 'pyramidResult.rows'])('rejects the old inline %s L1 derivation', rows => {
    const boundary = l1AvailabilityBoundary(`
      const l1Row = ${rows}.find(row => row.layer_key === 'L1')
      const isL1Built = l1Row?.status === 'built' || l1Row?.status === 'complete'
      const l1Availability = isL1Built ? 'ready' : 'no-build'
    `)
    expect(boundary.delegated).toBe(false)
    expect(boundary.inlineDerivations).toContain('pyramid row selection')
    expect(boundary.inlineDerivations).toContain('L1 status derivation')
  })

  it.each(['query', 'database.query'])('detects an inline %s bypass of the Build owner', callee => {
    expect(layerReadBoundary(`${callee}('SELECT layer AS layer_key, status FROM pyramid_layers WHERE chart_id = $1', [id])`).inlineLayerReads).toEqual([callee])
  })
})


describe('legacy Consult L1 availability selection', () => {
  it.each([
    { name: 'empty', rows: [], state: 'no-build' },
    { name: 'no L1', rows: [{ layer_key: 'L2', status: 'built' }], state: 'no-build' },
    { name: 'built', rows: [{ layer_key: 'L1', status: 'built' }], state: 'ready' },
    { name: 'complete', rows: [{ layer_key: 'L1', status: 'complete' }], state: 'ready' },
    { name: 'building', rows: [{ layer_key: 'L1', status: 'building' }], state: 'l1-building' },
    { name: 'in progress', rows: [{ layer_key: 'L1', status: 'in_progress' }], state: 'l1-building' },
    { name: 'unrecognized', rows: [{ layer_key: 'L1', status: 'not_started' }], state: 'no-build' },
    { name: 'first L1 building', rows: [{ layer_key: 'L1', status: 'building' }, { layer_key: 'L1', status: 'built' }], state: 'l1-building' },
    { name: 'first L1 built', rows: [{ layer_key: 'L2', status: 'building' }, { layer_key: 'L1', status: 'built' }, { layer_key: 'L1', status: 'building' }], state: 'ready' },
  ])('preserves $name without mutating or deduplicating its input', ({ rows, state }) => {
    const before = rows.map(row => ({ ...row }))
    expect(legacyL1AvailabilityFromPyramid(rows)).toBe(state)
    expect(rows).toEqual(before)
  })
})
