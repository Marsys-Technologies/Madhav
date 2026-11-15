import { beforeEach, describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { createSourceFile, forEachChild, isCallExpression, isFunctionDeclaration, isIdentifier, isStringLiteralLike, ScriptTarget } from 'typescript'
import { NextRequest, NextResponse } from 'next/server'

const m = vi.hoisted(() => ({ query: vi.fn(), user: vi.fn(), permission: vi.fn(), order: [] as string[] }))
vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: m.query, getPool: vi.fn() }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: m.user }))
vi.mock('@/lib/auth/requireChartPermission', () => ({ requireChartPermission: m.permission }))
vi.mock('@/lib/build/plan', () => ({}))
vi.mock('@/lib/cloud_run/jobs', () => ({}))
vi.mock('@/lib/cockpit/clearScopeFilter', () => ({}))
vi.mock('@/lib/cockpit/serviceProbeContract', () => ({}))
vi.mock('@/lib/build/runPreparation', () => ({}))
vi.mock('@/lib/build/assetInvalidation', () => ({}))
vi.mock('@/lib/build/runDispatch', () => ({}))

import { GET } from '@/app/api/cockpit/runs/route'
import { readBuildRunHistory } from '../runHistory'

const SQL = `SELECT id, scope, scope_target, action, state, created_at, ended_at, last_error
         FROM build_runs
        WHERE chart_id = $1
        ORDER BY created_at DESC
        LIMIT 20`
const req = (params = 'chart_id=chart&limit=1') => new NextRequest(`http://localhost/api/cockpit/runs?${params}`)

beforeEach(() => {
  vi.resetAllMocks()
  m.order.length = 0
  m.user.mockImplementation(async () => { m.order.push('user'); return { uid: 'owner' } })
  m.permission.mockImplementation(async () => { m.order.push('permission'); return null })
  m.query.mockImplementation(async () => { m.order.push('history'); return { rows: [] } })
})

describe('GET run-history contract', () => {
  it('rejects an unsigned caller before params, permission, or history', async () => {
    m.user.mockResolvedValue(null)
    const response = await GET(req(''))
    expect(response.status).toBe(403)
    expect(await response.json()).toEqual({ error: 'Forbidden' })
    expect(m.permission).not.toHaveBeenCalled()
    expect(m.query).not.toHaveBeenCalled()
  })

  it('rejects a missing chart before permission or history', async () => {
    const response = await GET(req('limit=1'))
    expect(response.status).toBe(400)
    expect(await response.json()).toEqual({ error: 'chart_id query param required' })
    expect(m.permission).not.toHaveBeenCalled()
    expect(m.query).not.toHaveBeenCalled()
  })

  it('returns the original permission denial without reading history', async () => {
    const denied = NextResponse.json({ error: 'Forbidden', code: 'FORBIDDEN_CHART' }, { status: 403 })
    m.permission.mockResolvedValue(denied)
    expect(await GET(req())).toBe(denied)
    expect(m.permission).toHaveBeenCalledExactlyOnceWith({ uid: 'owner', chartId: 'chart', access: 'read' })
    expect(m.query).not.toHaveBeenCalled()
  })

  it('keeps permission failures outside the history fallback', async () => {
    const error = new Error('permission lookup failed')
    m.permission.mockRejectedValue(error)
    await expect(GET(req())).rejects.toBe(error)
    expect(m.query).not.toHaveBeenCalled()
  })

  it('authorizes before the exact chart-bound latest-20 read and preserves the JSON projection', async () => {
    const rows = [{ id: 'run-1', scope: 'chart', scope_target: null, action: 'build', state: 'failed', created_at: 'date', ended_at: null, last_error: 'original error' }]
    m.query.mockImplementation(async () => { m.order.push('history'); return { rows } })
    const response = await GET(req())
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ data: rows })
    expect(m.query).toHaveBeenCalledExactlyOnceWith(SQL, ['chart'])
    expect(m.order).toEqual(['user', 'permission', 'history'])
  })

  it('keeps the existing logged HTTP-200 empty-data fallback for a history error', async () => {
    const error = new Error('history lookup failed')
    m.query.mockRejectedValue(error)
    const log = vi.spyOn(console, 'error').mockImplementation(() => {})
    try {
      const response = await GET(req())
      expect(response.status).toBe(200)
      expect(await response.json()).toEqual({ data: [] })
      expect(log).toHaveBeenCalledExactlyOnceWith('[cockpit/runs GET]', error)
    } finally { log.mockRestore() }
  })
})

describe('Build run-history read owner', () => {
  it('returns the original row array, including empty results, without a second query', async () => {
    const rows: never[] = []
    m.query.mockResolvedValue({ rows })
    expect(await readBuildRunHistory('empty-chart')).toBe(rows)
    expect(m.query).toHaveBeenCalledExactlyOnceWith(SQL, ['empty-chart'])
  })

  it('propagates the original query failure to its caller', async () => {
    const error = new Error('history lookup failed')
    m.query.mockRejectedValue(error)
    await expect(readBuildRunHistory('chart')).rejects.toBe(error)
  })
})

function getDataBoundary(source: string) {
  const file = createSourceFile('route.ts', source, ScriptTarget.Latest, true)
  const get = file.statements.find(node => isFunctionDeclaration(node) && node.name?.text === 'GET')
  const bypasses: string[] = []
  let ownerCalls = 0
  function visit(node: Parameters<typeof forEachChild>[0]) {
    if (isCallExpression(node)) {
      const callee = node.expression.getText(file)
      if (isIdentifier(node.expression) && callee === 'readBuildRunHistory') ownerCalls++
      if (!['requireUser', 'NextResponse.json', 'req.nextUrl.searchParams.get', 'requireChartPermission', 'readBuildRunHistory', 'console.error'].includes(callee)) bypasses.push(callee)
    }
    if (isStringLiteralLike(node) && /\b(?:SELECT|FROM|build_runs)\b/.test(node.text)) bypasses.push('inline SQL')
    forEachChild(node, visit)
  }
  if (get) visit(get)
  return { ownerCalls, bypasses }
}

describe('GET delegates data while retaining the other handlers', () => {
  it('keeps the actual GET free of raw/namespace data calls and the owner server-only', () => {
    const source = readFileSync(new URL('../../../app/api/cockpit/runs/route.ts', import.meta.url), 'utf8')
    expect(getDataBoundary(source)).toEqual({ ownerCalls: 1, bypasses: [] })
    const owner = readFileSync(new URL('../runHistory.ts', import.meta.url), 'utf8')
    expect(owner).toMatch(/^import 'server-only'/)
  })

  it.each(["query('SELECT 1')", "database.query('SELECT 1')"])('detects a reintroduced GET data bypass: %s', call => {
    expect(getDataBoundary(`export async function GET() { await readBuildRunHistory('chart'); await ${call} }`).bypasses).not.toHaveLength(0)
  })
})
