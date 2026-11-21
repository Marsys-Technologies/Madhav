import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'

const h = vi.hoisted(() => ({ query: vi.fn(), getPool: vi.fn(), user: vi.fn(), permission: vi.fn(), probe: vi.fn(), invoke: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: h.query, getPool: h.getPool }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: h.user }))
vi.mock('@/lib/auth/requireChartPermission', () => ({ requireChartPermission: h.permission }))
vi.mock('@/lib/db/columnPresence', () => ({ blockedByAssetIdColumnPresent: h.probe }))
vi.mock('@/lib/build/jobInvoker', () => ({ invokeRunJob: h.invoke }))

import * as activeOwner from '@/lib/build/activeRunData'
import * as controls from '@/lib/build/runControlData'
import { GET, maxDuration as activeDuration } from '@/app/api/cockpit/runs/active/route'
import { POST as pause, maxDuration as pauseDuration } from '@/app/api/cockpit/runs/[id]/pause/route'
import { POST as stop, maxDuration as stopDuration } from '@/app/api/cockpit/runs/[id]/stop/route'
import { POST as resume, maxDuration as resumeDuration } from '@/app/api/cockpit/runs/[id]/resume/route'

const CHART = 'fixture-chart', RUN = 'fixture-run'
const REQUESTED_AT = '2026-11-20 15:00:00.123456+00'
const run = { id: RUN, scope: 'layer', scope_target: 'kala', action: 'build', state: 'running', plan: ['fixture'], current_asset_id: 'fixture', created_at: 'fixture-created', started_at: null, pause_requested_at: null, stop_requested_at: null }
const assets = [{ asset_id: 'fixture', position: 0, state: 'error', started_at: null, ended_at: null, error: 'fixture-error', disposition: 'dependency_blocked', blocked_by_asset_id: 'upstream' }]
const activeRequest = () => new NextRequest(`http://localhost/api/cockpit/runs/active?chart_id=${CHART}`)
const controlRequest = () => new NextRequest('http://localhost/api/cockpit/runs/fixture/control', { method: 'POST' })
const context = () => ({ params: Promise.resolve({ id: RUN }) })
beforeEach(() => {
  vi.restoreAllMocks()
  vi.resetAllMocks()
  vi.spyOn(console, 'error').mockImplementation(() => undefined)
  h.user.mockResolvedValue({ uid: 'fixture-admin' })
  h.permission.mockResolvedValue(null)
  h.probe.mockResolvedValue(true)
  h.invoke.mockResolvedValue(undefined)
  h.getPool.mockImplementation(() => { throw new Error('Unexpected pool acquisition') })
  h.query.mockImplementation((sql: string) => {
    if (sql.includes('FROM profiles')) return Promise.resolve({ rows: [{ role: 'super_admin' }] })
    if (sql.includes('FROM build_run_assets')) return Promise.resolve({ rows: assets })
    if (sql.includes('SELECT id, scope')) return Promise.resolve({ rows: [run] })
    return Promise.resolve({ rows: [{ id: RUN, state: 'planned', action: 'rebuild', resume_requested_at: REQUESTED_AT }] })
  })
})

describe('active-run owner and actual route', () => {
  it('keeps the actual delegate and exact run/asset response', async () => {
    const delegate = vi.spyOn(activeOwner, 'readActiveBuildRun')
    const response = await GET(activeRequest())
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ data: { run, assets } })
    expect(delegate).toHaveBeenCalledExactlyOnceWith(CHART)
    expect(h.permission).toHaveBeenCalledExactlyOnceWith({ uid: 'fixture-admin', chartId: CHART, access: 'read' })
    expect(h.query).toHaveBeenCalledTimes(2)
  })
  it('returns early for no run without probing the column or reading assets', async () => {
    h.query.mockResolvedValue({ rows: [] })
    expect(await activeOwner.readActiveBuildRun(CHART)).toBeNull()
    expect(h.query).toHaveBeenCalledExactlyOnceWith(expect.stringContaining("state IN ('planned','running','paused')"), [CHART])
    expect(h.probe).not.toHaveBeenCalled()
  })
  it.each([true, false])('preserves conditional blocked-by projection when presence is %s', async present => {
    h.probe.mockResolvedValue(present)
    const order: string[] = []
    h.query.mockImplementation((sql: string) => {
      order.push(sql.includes('FROM build_run_assets') ? 'assets' : 'run')
      return Promise.resolve({ rows: sql.includes('FROM build_run_assets') ? assets : [run] })
    })
    h.probe.mockImplementation(async () => { order.push('probe'); return present })
    expect(await activeOwner.readActiveBuildRun(CHART)).toEqual({ run, assets })
    expect(order).toEqual(['run', 'probe', 'assets'])
    expect(h.query).toHaveBeenCalledTimes(2)
    expect(h.query.mock.calls[0][0]).toContain('ORDER BY created_at DESC LIMIT 1')
    expect(h.query.mock.calls[0][1]).toEqual([CHART])
    const query = String(h.query.mock.calls[1][0])
    expect(query).toContain('error, disposition,')
    expect(query).toContain(present ? 'disposition, blocked_by_asset_id' : 'NULL::text AS blocked_by_asset_id')
    expect(h.query.mock.calls[1][1]).toEqual([RUN])
    expect(h.getPool).not.toHaveBeenCalled()
  })
  it('preserves the existing HTTP200 null/error envelope on DB failure', async () => {
    h.query.mockRejectedValue(new Error('fixture read failure'))
    const response = await GET(activeRequest())
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ data: null, _error: 'fixture read failure' })
    expect(h.probe).not.toHaveBeenCalled()
  })
  it('reports unavailable status to the preparation poll when the read fails', async () => {
    h.query.mockRejectedValue(new Error('fixture read failure'))
    const request = new NextRequest(`http://localhost/api/cockpit/runs/active?chart_id=${CHART}&preparation=true`)
    const response = await GET(request)
    expect(response.status).toBe(503)
    expect(await response.json()).toEqual({ error: 'Run status is temporarily unavailable.' })
  })
  it('does not touch the data owner on denied or absent authentication', async () => {
    const delegate = vi.spyOn(activeOwner, 'readActiveBuildRun')
    h.permission.mockResolvedValue(new Response(null, { status: 403 }))
    expect((await GET(activeRequest())).status).toBe(403)
    h.user.mockResolvedValue(null)
    expect((await GET(activeRequest())).status).toBe(403)
    expect(delegate).not.toHaveBeenCalled()
    expect(h.query).not.toHaveBeenCalled()
  })
})

describe('actual run control delegates', () => {
  it('delegates pause and retains one Identity read, one write and its HTTP shape', async () => {
    const delegate = vi.spyOn(controls, 'requestBuildRunPause')
    const response = await pause(controlRequest(), context())
    expect(await response.json()).toEqual({ data: { run_id: RUN, pause_requested: true } })
    expect(delegate).toHaveBeenCalledExactlyOnceWith(RUN)
    expect(h.query).toHaveBeenCalledTimes(2)
    expect(h.query.mock.calls[0]).toEqual(['SELECT role FROM profiles WHERE id=$1', ['fixture-admin']])
    expect(h.invoke).not.toHaveBeenCalled()
  })
  it('delegates stop and keeps planned/running/paused semantics', async () => {
    const delegate = vi.spyOn(controls, 'requestBuildRunStop')
    const response = await stop(controlRequest(), context())
    expect(await response.json()).toEqual({ data: { run_id: RUN, stop_requested: true } })
    expect(delegate).toHaveBeenCalledExactlyOnceWith(RUN)
    expect(h.query).toHaveBeenCalledTimes(2)
    expect(h.invoke).not.toHaveBeenCalled()
  })
  it('delegates the paused claim and forces the existing rebuild dispatch', async () => {
    const claim = vi.spyOn(controls, 'claimPausedBuildRun')
    expect((await resume(controlRequest(), context())).status).toBe(200)
    expect(claim).toHaveBeenCalledExactlyOnceWith(RUN)
    expect(h.query).toHaveBeenCalledTimes(2)
    expect(h.invoke).toHaveBeenCalledExactlyOnceWith(RUN, { forceExecute: true })
  })
  it('forces even a paused single-asset build', async () => {
    h.query.mockResolvedValueOnce({ rows: [{ role: 'super_admin' }] })
      .mockResolvedValueOnce({ rows: [{ id: RUN, action: 'build', resume_requested_at: REQUESTED_AT }] })
    expect((await resume(controlRequest(), context())).status).toBe(200)
    expect(h.invoke).toHaveBeenCalledExactlyOnceWith(RUN, { forceExecute: true })
  })
  it('delegates the legacy-state read after an empty atomic claim and refuses dispatch', async () => {
    const read = vi.spyOn(controls, 'readBuildRunResumeState')
    h.query.mockResolvedValueOnce({ rows: [{ role: 'super_admin' }] }).mockResolvedValueOnce({ rows: [] }).mockResolvedValueOnce({ rows: [{ state: 'paused', has_manifest: false }] })
    const response = await resume(controlRequest(), context())
    expect(response.status).toBe(409)
    expect((await response.json()).code).toBe('LEGACY_RUN_MANIFEST_MISSING')
    expect(read).toHaveBeenCalledExactlyOnceWith(RUN)
    expect(h.query).toHaveBeenCalledTimes(3)
    expect(h.invoke).not.toHaveBeenCalled()
  })
  it('delegates planned-only compensation after failed dispatch and keeps the503', async () => {
    const restore = vi.spyOn(controls, 'restorePausedBuildRunAfterDispatchFailure')
    h.invoke.mockRejectedValue(new Error('fixture dispatch failure'))
    const response = await resume(controlRequest(), context())
    expect(response.status).toBe(503)
    expect((await response.json()).code).toBe('JOB_DISPATCH_FAILED')
    expect(restore).toHaveBeenCalledExactlyOnceWith('fixture dispatch failure', RUN, REQUESTED_AT)
    expect(h.query).toHaveBeenCalledTimes(3)
  })
  it.each([pause, stop, resume])('requires the same super-admin gate before control writes', async handler => {
    h.query.mockResolvedValue({ rows: [{ role: 'guest' }] })
    expect((await handler(controlRequest(), context())).status).toBe(403)
    expect(h.query).toHaveBeenCalledExactlyOnceWith('SELECT role FROM profiles WHERE id=$1', ['fixture-admin'])
    expect(h.invoke).not.toHaveBeenCalled()
  })
  it('keeps all four existing duration declarations', () => {
    expect([activeDuration, pauseDuration, stopDuration, resumeDuration]).toEqual([8, 8, 8, 8])
  })
})

describe('control statement boundaries', () => {
  it('uses exactly five original statements and preserves ID/detail binding order', async () => {
    await controls.requestBuildRunPause(RUN)
    await controls.requestBuildRunStop(RUN)
    await controls.claimPausedBuildRun(RUN)
    await controls.readBuildRunResumeState(RUN)
    await controls.restorePausedBuildRunAfterDispatchFailure('fixture detail', RUN, REQUESTED_AT)
    expect(h.query).toHaveBeenCalledTimes(5)
    expect(h.query.mock.calls.map(([, args]) => args)).toEqual([[RUN], [RUN], [RUN], [RUN], ['fixture detail', RUN, REQUESTED_AT]])
    expect(h.query.mock.calls[0][0]).toContain("WHERE id=$1 AND state = 'running'")
    const stopSql = String(h.query.mock.calls[1][0])
    expect(stopSql).toContain("pg_try_advisory_xact_lock(hashtext(COALESCE(chart_id::text, 'nirmana-global-assets')))")
    expect(stopSql).not.toContain('hashtextextended')
    expect(stopSql).not.toMatch(/pg_try_advisory_lock\s*\(/)
    expect(stopSql).toContain("WHEN t.prev_state IN ('planned','paused') OR t.dead_worker_lock THEN 'stopped'")
    expect(stopSql).toContain("r.state = 'stopped' AND b.state = 'queued'")
    expect(stopSql).toContain("r.state = 'stopped' AND b.state = 'building'")
    expect(stopSql).toContain("COALESCE(b.error, 'Stopped after worker exit')")
    expect(stopSql).toContain('UPDATE asset_throughput at')
    expect(stopSql).toContain("AND at.state = 'building'")
    expect(h.query.mock.calls[2][0]).toContain("WHERE id=$1 AND state = 'paused'")
    expect(h.query.mock.calls[2][0]).toContain('plan_manifest IS NOT NULL AND plan_manifest_digest IS NOT NULL')
    expect(h.query.mock.calls[3][0]).toContain('AS has_manifest')
    expect(h.query.mock.calls[4][0]).toContain("WHERE id=$2 AND state = 'planned'")
    expect(h.query.mock.calls[4][0]).toContain('resume_requested_at = $3::timestamptz')
    expect(h.getPool).not.toHaveBeenCalled()
    expect(h.invoke).not.toHaveBeenCalled()
  })
  it.each([
    () => controls.requestBuildRunPause(RUN), () => controls.requestBuildRunStop(RUN),
    () => controls.claimPausedBuildRun(RUN), () => controls.readBuildRunResumeState(RUN),
    () => controls.restorePausedBuildRunAfterDispatchFailure('fixture detail', RUN, REQUESTED_AT),
  ])('passes each original statement failure through without another query or dispatch', async operation => {
    const error = new Error('fixture SQL failure'); h.query.mockRejectedValue(error)
    await expect(operation()).rejects.toBe(error)
    expect(h.query).toHaveBeenCalledTimes(1)
    expect(h.getPool).not.toHaveBeenCalled()
    expect(h.invoke).not.toHaveBeenCalled()
  })
})

const contracts = [
  { relative: '../../../app/api/cockpit/runs/active/route.ts', handler: 'GET', module: '@/lib/build/activeRunData', calls: { readActiveBuildRun: ['chart_id'] }, roleQueries: 0 },
  { relative: '../../../app/api/cockpit/runs/[id]/pause/route.ts', handler: 'POST', module: '@/lib/build/runControlData', calls: { requestBuildRunPause: ['id'] }, roleQueries: 1 },
  { relative: '../../../app/api/cockpit/runs/[id]/stop/route.ts', handler: 'POST', module: '@/lib/build/runControlData', calls: { requestBuildRunStop: ['id'] }, roleQueries: 1 },
  { relative: '../../../app/api/cockpit/runs/[id]/resume/route.ts', handler: 'POST', module: '@/lib/build/runControlData', calls: { claimPausedBuildRun: ['id'], readBuildRunResumeState: ['id'], restorePausedBuildRunAfterDispatchFailure: ['detail', 'id', 'requestedAt'] }, roleQueries: 1 },
] as const
type Contract = typeof contracts[number]
/** Checks only the exact existing handler/owner/Identity seam, not arbitrary data flow. */
function inspect(text: string, contract: Contract): string[] {
  const file = ts.createSourceFile('route.ts', text, ts.ScriptTarget.Latest, true)
  const errors: string[] = []
  const handler = file.statements.find((n): n is ts.FunctionDeclaration => ts.isFunctionDeclaration(n) && n.name?.text === contract.handler)
  if (!handler?.body || (file as ts.SourceFile & { parseDiagnostics: readonly ts.Diagnostic[] }).parseDiagnostics.length) return ['parse/handler']
  const imports = new Map<string, string>()
  for (const n of file.statements.filter(ts.isImportDeclaration)) {
    if (!ts.isStringLiteral(n.moduleSpecifier) || n.moduleSpecifier.text !== contract.module || n.importClause?.isTypeOnly) continue
    const names = n.importClause?.namedBindings
    if (names && ts.isNamedImports(names)) for (const x of names.elements) if (!x.isTypeOnly) imports.set(x.name.text, x.propertyName?.text ?? x.name.text)
  }
  if (imports.size !== Object.keys(contract.calls).length || [...imports.values()].some(x => !Object.hasOwn(contract.calls, x))) errors.push('owner imports')
  const enclosing = (n: ts.Node) => { let p = n.parent; while (p && !ts.isFunctionLike(p)) p = p.parent; return p }
  const binds = (n: ts.Node, name: string) => (ts.isVariableDeclaration(n) || ts.isFunctionDeclaration(n) || ts.isParameter(n) || ts.isClassDeclaration(n)) && n.name && ts.isIdentifier(n.name) && n.name.text === name
  const shadowed = (n: ts.Node, name: string) => {
    for (let p: ts.Node | undefined = n.parent; p && p !== file; p = p.parent) {
      if (ts.isBlock(p) && p.statements.some(s => binds(s, name) || (ts.isVariableStatement(s) && s.declarationList.declarations.some(x => binds(x, name))))) return true
      if (ts.isFunctionLike(p) && p.parameters.some(x => binds(x, name))) return true
    }
    return false
  }
  const seen = new Map<string, number>(); let roles = 0
  function visit(n: ts.Node) {
    if (ts.isCallExpression(n)) {
      const target = n.expression
      if (ts.isIdentifier(target) && imports.has(target.text) && enclosing(n) === handler) {
        const name = imports.get(target.text)!
        const args = (contract.calls as Readonly<Record<string, readonly string[]>>)[name]
        seen.set(name, (seen.get(name) ?? 0) + 1)
        if (JSON.stringify(n.arguments.map(x => x.getText(file))) !== JSON.stringify(args) || shadowed(n, target.text)) errors.push('binding:' + name)
      }
      if ((ts.isIdentifier(target) && target.text === 'query') || (ts.isPropertyAccessExpression(target) && target.name.text === 'query')) {
        const f = enclosing(n), sql = n.arguments[0]
        if (ts.isIdentifier(target) && f && ts.isFunctionDeclaration(f) && f.name?.text === 'requireSuperAdmin'
          && sql && ts.isStringLiteral(sql) && sql.text === 'SELECT role FROM profiles WHERE id=$1' && n.arguments[1]?.getText(file) === '[user.uid]') roles++
        else errors.push('local domain query')
      }
    }
    ts.forEachChild(n, visit)
  }
  visit(file)
  if (roles !== contract.roleQueries) errors.push('Identity shape')
  for (const name of Object.keys(contract.calls)) if (seen.get(name) !== 1) errors.push('delegate:' + name)
  return errors
}
describe('four exact source seams', () => {
  it.each(contracts)('delegates the declared $handler interface in $relative', contract => {
    expect(inspect(readFileSync(fileURLToPath(new URL(contract.relative, import.meta.url)), 'utf8'), contract)).toEqual([])
  })
  it('rejects actual inline SQL, disconnected delegates, wrong IDs and lexical shadows', () => {
    const c = contracts[3], text = readFileSync(fileURLToPath(new URL(c.relative, import.meta.url)), 'utf8')
    expect(inspect(text.replace('const result = await', "await query('UPDATE build_runs SET state=state')\n    const result = await"), c)).toContain('local domain query')
    expect(inspect(text.replace('claimPausedBuildRun(id)', "Promise.resolve({rows:[]}) /* claimPausedBuildRun(id) */"), c)).toContain('delegate:claimPausedBuildRun')
    expect(inspect(text.replace('claimPausedBuildRun(id)', "claimPausedBuildRun('foreign')"), c)).toContain('binding:claimPausedBuildRun')
    expect(inspect(text.replace('const result = await', 'const claimPausedBuildRun = async () => ({rows:[]})\n    const result = await'), c)).toContain('binding:claimPausedBuildRun')
  })
  it('accepts comments, formatting and an unrelated local presentation scope', () => {
    const c = contracts[3], text = readFileSync(fileURLToPath(new URL(c.relative, import.meta.url)), 'utf8')
    expect(inspect(text + '\n// query("not executable")\nfunction presentation(rows: string[]) { const claimPausedBuildRun = rows.find(x => x); return claimPausedBuildRun }\n', c)).toEqual([])
  })
})

describe('NIR-04 requestBuildRunStop live vs dead vs global reconciliation', () => {
  interface SimState {
    run: { id: string; chart_id: string | null; state: string; stop_requested_at: string | null; ended_at: string | null }
    assets: Array<{ run_id: string; asset_id: string; state: string; ended_at: string | null; error: string | null }>
    throughput: Array<{ chart_id: string | null; asset_id: string; state: string; last_error: string | null }>
    heldLocks: Set<string>
  }

  function installStopHarness(sim: SimState) {
    h.query.mockImplementation((sql: string, params?: unknown[]) => {
      if (sql.includes('FROM profiles')) return Promise.resolve({ rows: [{ role: 'super_admin' }] })
      const runId = params?.[0]
      if (runId !== sim.run.id || !['planned', 'running', 'paused'].includes(sim.run.state)) {
        return Promise.resolve({ rows: [] })
      }
      expect(sql).toContain("pg_try_advisory_xact_lock(hashtext(COALESCE(chart_id::text, 'nirmana-global-assets')))")
      const lockKey = sim.run.chart_id ?? 'nirmana-global-assets'
      const prevState = sim.run.state
      const deadWorkerLock = prevState === 'running' ? !sim.heldLocks.has(lockKey) : false
      const now = '2026-11-21T18:40:00Z'
      sim.run.stop_requested_at = now
      if (prevState === 'planned' || prevState === 'paused' || deadWorkerLock) {
        sim.run.state = 'stopped'
        sim.run.ended_at = now
        for (const b of sim.assets) {
          if (b.run_id !== sim.run.id) continue
          if (b.state === 'queued') {
            b.state = 'aborted'
            b.ended_at = now
            b.error = prevState === 'running' ? (b.error ?? 'Stopped after worker exit') : 'Stopped before this asset started.'
          } else if (b.state === 'building') {
            b.state = 'aborted'
            b.ended_at = now
            b.error = b.error ?? 'Stopped after worker exit'
            for (const at of sim.throughput) {
              if ((at.chart_id === sim.run.chart_id || at.chart_id === null) && at.asset_id === b.asset_id && at.state === 'building') {
                at.state = 'error'
                at.last_error = at.last_error ?? 'Stopped after worker exit'
              }
            }
          }
        }
      }
      return Promise.resolve({ rows: [{ id: sim.run.id }] })
    })
  }

  it('preserves running state for cooperative stop when a live worker holds the chart advisory lock', async () => {
    const sim: SimState = {
      run: { id: RUN, chart_id: CHART, state: 'running', stop_requested_at: null, ended_at: null },
      assets: [
        { run_id: RUN, asset_id: 'ga_structural', state: 'building', ended_at: null, error: null },
        { run_id: RUN, asset_id: 'ga_yoga', state: 'queued', ended_at: null, error: null },
      ],
      throughput: [{ chart_id: CHART, asset_id: 'ga_structural', state: 'building', last_error: null }],
      heldLocks: new Set([CHART]),
    }
    installStopHarness(sim)
    const response = await stop(controlRequest(), context())
    expect(response.status).toBe(200)
    expect(sim.run.state).toBe('running')
    expect(sim.run.stop_requested_at).not.toBeNull()
    expect(sim.run.ended_at).toBeNull()
    expect(sim.assets.map(a => a.state)).toEqual(['building', 'queued'])
    expect(sim.throughput[0].state).toBe('building')
  })

  it('immediately reconciles running -> stopped when worker advisory lock is unheld (dead worker)', async () => {
    const sim: SimState = {
      run: { id: RUN, chart_id: CHART, state: 'running', stop_requested_at: null, ended_at: null },
      assets: [
        { run_id: RUN, asset_id: 'ga_positions', state: 'complete', ended_at: '2026-11-21T18:00:00Z', error: null },
        { run_id: RUN, asset_id: 'ga_structural', state: 'building', ended_at: null, error: null },
        { run_id: RUN, asset_id: 'ga_yoga', state: 'queued', ended_at: null, error: null },
      ],
      throughput: [{ chart_id: CHART, asset_id: 'ga_structural', state: 'building', last_error: null }],
      heldLocks: new Set(),
    }
    installStopHarness(sim)
    const response = await stop(controlRequest(), context())
    expect(response.status).toBe(200)
    expect(sim.run.state).toBe('stopped')
    expect(sim.run.ended_at).not.toBeNull()
    expect(sim.run.stop_requested_at).not.toBeNull()
    expect(sim.assets).toEqual([
      { run_id: RUN, asset_id: 'ga_positions', state: 'complete', ended_at: '2026-11-21T18:00:00Z', error: null },
      { run_id: RUN, asset_id: 'ga_structural', state: 'aborted', ended_at: '2026-11-21T18:40:00Z', error: 'Stopped after worker exit' },
      { run_id: RUN, asset_id: 'ga_yoga', state: 'aborted', ended_at: '2026-11-21T18:40:00Z', error: 'Stopped after worker exit' },
    ])
    expect(sim.throughput[0]).toEqual({
      chart_id: CHART, asset_id: 'ga_structural', state: 'error', last_error: 'Stopped after worker exit',
    })
  })

  it('uses the nirmana-global-assets lock key for global runs (chart_id IS NULL) on both live and dead paths', async () => {
    const liveGlobal: SimState = {
      run: { id: RUN, chart_id: null, state: 'running', stop_requested_at: null, ended_at: null },
      assets: [{ run_id: RUN, asset_id: 'bg_ephemeris', state: 'building', ended_at: null, error: null }],
      throughput: [{ chart_id: null, asset_id: 'bg_ephemeris', state: 'building', last_error: null }],
      heldLocks: new Set(['nirmana-global-assets']),
    }
    installStopHarness(liveGlobal)
    expect((await stop(controlRequest(), context())).status).toBe(200)
    expect(liveGlobal.run.state).toBe('running')
    expect(liveGlobal.throughput[0].state).toBe('building')

    liveGlobal.heldLocks.clear()
    expect((await stop(controlRequest(), context())).status).toBe(200)
    expect(liveGlobal.run.state).toBe('stopped')
    expect(liveGlobal.assets[0].state).toBe('aborted')
    expect(liveGlobal.throughput[0].state).toBe('error')
  })
})
