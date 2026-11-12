/** Recalibration uses the shared planner, frozen persistence and dispatch. */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { enqueueLelRecalibration, LEL_DEPENDENT_ASSETS, LEL_RECAL_SCOPE_TARGET } from '../recalibrationEnqueue'
import { manifestDigest } from '../runPreparation'
import { RunSubmissionRejected } from '../jobInvoker'

const { query, transaction, transactionQuery, invokeRunJob } = vi.hoisted(() => ({
  query: vi.fn(),
  transaction: vi.fn(),
  transactionQuery: vi.fn(),
  invokeRunJob: vi.fn(),
}))
vi.mock('@/lib/db/client', () => ({ query, withTransaction: transaction }))
vi.mock('@/lib/build/jobInvoker', async (importOriginal) => ({
  ...await importOriginal<typeof import('../jobInvoker')>(), invokeRunJob,
}))

const CHART = '11111111-2222-4333-8444-555555555555'
const RUN = 'synthetic-recalibration-run'
const UID = 'synthetic-owner'
const activeConflict = Object.assign(new Error('already active'), {
  code: '23505',
  constraint: 'build_runs_one_active_per_chart_idx',
})

const registry = LEL_DEPENDENT_ASSETS.map((asset_id) => ({
  asset_id,
  layer: asset_id.startsWith('mi_') ? 'mimamsa' : 'phala',
  scope: 'per_chart',
  has_writer: true,
  target_table: `${asset_id}_fixture`,
  asset_kind: 'data',
  depends_on: asset_id === 'mi_pramana' ? ['mi_jivanaghatana'] : [],
  estimated_seconds: 10,
}))

function preparation(options: {
  active?: boolean
  protectedIds?: readonly string[]
  registryRows?: Array<Omit<(typeof registry)[number], 'asset_id'> & { asset_id: string }>
  throughput?: Array<{ asset_id: string; state: string }>
  freshness?: Array<{ asset_id: string; state: string; reasons: string[] }>
  insertError?: Error
  assetInsertError?: Error
} = {}) {
  transactionQuery.mockImplementation(async (sql: string) => {
    if (sql.includes('SELECT id FROM build_runs')) return { rows: options.active ? [{ id: 'active' }] : [] }
    if (sql.includes('FROM asset_registry')) return { rows: options.registryRows ?? registry }
    if (sql.includes('FROM asset_throughput')) return { rows: options.throughput ?? [] }
    if (sql.includes('FROM asset_freshness')) return { rows: options.freshness ?? [] }
    if (sql.includes('FROM build_protected_assets')) {
      return { rows: (options.protectedIds ?? []).map((asset_id) => ({ asset_id })) }
    }
    if (sql.includes('INSERT INTO build_runs')) {
      if (options.insertError) throw options.insertError
      return { rows: [{ id: RUN }] }
    }
    if (sql.includes('INSERT INTO build_run_assets')) {
      if (options.assetInsertError) throw options.assetInsertError
      return { rows: [] }
    }
    throw new Error(`Unexpected query inside the preparation transaction: ${sql}`)
  })
}

const phase: string[] = []

beforeEach(() => {
  vi.resetAllMocks()
  phase.length = 0
  transaction.mockImplementation(async (work) => {
    phase.push('begin')
    try {
      const result = await work({ query: transactionQuery })
      phase.push('commit')
      return result
    } catch (error) {
      phase.push('rollback')
      throw error
    }
  })
  query.mockResolvedValueOnce({ rows: [{ value_jsonb: { seconds: 60 } }] })
  query.mockResolvedValueOnce({ rows: [] })
  invokeRunJob.mockImplementation(async () => {
    phase.push('dispatch')
    return { executionName: 'synthetic-operation' }
  })
  preparation()
})

describe('enqueueLelRecalibration', () => {
  it('keeps the documented four-asset scope and its debounce signature', () => {
    expect(LEL_DEPENDENT_ASSETS).toEqual(['mi_jivanaghatana', 'mi_pramana', 'ph_rectification', 'ph_pramana'])
    expect(LEL_RECAL_SCOPE_TARGET).toBe('mi_jivanaghatana,mi_pramana,ph_rectification,ph_pramana')
  })

  it('commits the frozen manifest and ordered queued assets before invoking the job', async () => {
    const result = await enqueueLelRecalibration({ chartId: CHART, triggeredBy: UID })
    expect(result.enqueued).toBe(true)
    if (!result.enqueued) throw new Error('Expected the fixture to enqueue a run')
    expect(result.run_id).toBe(RUN)
    expect(new Set(result.plan)).toEqual(new Set(LEL_DEPENDENT_ASSETS))
    expect(phase).toEqual(['begin', 'commit', 'dispatch'])
    expect(invokeRunJob).toHaveBeenCalledExactlyOnceWith(RUN, { reportDefiniteRejection: true })

    const runInsert = transactionQuery.mock.calls.find(([sql]) => sql.includes('INSERT INTO build_runs'))
    expect(runInsert).toBeDefined()
    const [runSql, params] = runInsert!
    expect(runSql).toContain('plan_manifest, plan_manifest_digest')
    expect(params.slice(0, 5)).toEqual([CHART, 'asset_set', LEL_RECAL_SCOPE_TARGET, 'rebuild', JSON.stringify(result.plan)])
    const manifest = JSON.parse(params[5])
    expect(manifest.chart_id).toBe(CHART)
    expect(manifest.waves.flat()).toEqual(result.plan)
    expect(manifest.assets.map((asset: { asset_id: string }) => asset.asset_id)).toEqual(result.plan)
    expect(params.slice(6)).toEqual([manifestDigest(manifest), UID])

    const assets = transactionQuery.mock.calls.find(([sql]) => sql.includes('INSERT INTO build_run_assets'))
    expect(assets?.[1]).toEqual([RUN, ...result.plan.flatMap((asset, index) => [asset, index, 'queued'])])
    expect(transactionQuery.mock.calls.some(([sql]) => /\bDELETE\b/.test(sql))).toBe(false)
  })

  it('reports debounce before checking active state and does not start a transaction', async () => {
    query.mockReset().mockResolvedValueOnce({ rows: [{ value_jsonb: { seconds: 90 } }] })
      .mockResolvedValueOnce({ rows: [{ id: 'recent-run' }] })
    preparation({ active: true })
    await expect(enqueueLelRecalibration({ chartId: CHART })).resolves.toEqual({
      enqueued: false, reason: 'debounced', debounce_seconds: 90,
    })
    expect(query.mock.calls[1][1]).toEqual([CHART, 'asset_set', LEL_RECAL_SCOPE_TARGET, '90'])
    expect(transaction).not.toHaveBeenCalled()
    expect(invokeRunJob).not.toHaveBeenCalled()
  })

  it('uses the default quiet window if the formula lookup fails', async () => {
    query.mockReset().mockRejectedValueOnce(new Error('constant unavailable')).mockResolvedValueOnce({ rows: [{ id: 'recent' }] })
    await expect(enqueueLelRecalibration({ chartId: CHART })).resolves.toEqual({
      enqueued: false, reason: 'debounced', debounce_seconds: 600,
    })
    expect(transaction).not.toHaveBeenCalled()
  })

  it('force skips only the quiet-window queries and does not force job execution', async () => {
    await expect(enqueueLelRecalibration({ chartId: CHART, force: true })).resolves.toMatchObject({ enqueued: true })
    expect(query).not.toHaveBeenCalled()
    expect(invokeRunJob).toHaveBeenCalledExactlyOnceWith(RUN, { reportDefiniteRejection: true })
  })

  it.each([false, true])('coalesces an active run (force=%s)', async (force) => {
    preparation({ active: true })
    await expect(enqueueLelRecalibration({ chartId: CHART, force })).resolves.toEqual({
      enqueued: false, reason: 'run_active', existing_run_id: 'active',
    })
    expect(invokeRunJob).not.toHaveBeenCalled()
    expect(transactionQuery).toHaveBeenCalledOnce()
  })

  it.each([true, false])('coalesces the exact uniqueness race after rollback (winner still active=%s)', async (active) => {
    preparation({ insertError: activeConflict })
    query.mockReset().mockImplementation(async () => {
      expect(phase).toEqual(['begin', 'rollback'])
      return { rows: active ? [{ id: 'winner' }] : [] }
    })
    await expect(enqueueLelRecalibration({ chartId: CHART, force: true })).resolves.toEqual({
      enqueued: false, reason: 'run_active', ...(active ? { existing_run_id: 'winner' } : {}),
    })
    expect(query).toHaveBeenCalledOnce()
    expect(query.mock.calls[0][1]).toEqual([CHART])
    expect(invokeRunJob).not.toHaveBeenCalled()
  })

  it('does not classify an unrelated unique violation as a coalesced run', async () => {
    const failure = Object.assign(new Error('different unique failure'), { code: '23505', constraint: 'another_index' })
    preparation({ insertError: failure })
    await expect(enqueueLelRecalibration({ chartId: CHART, force: true })).rejects.toBe(failure)
    expect(query).not.toHaveBeenCalled()
    expect(invokeRunJob).not.toHaveBeenCalled()
  })

  it('reports protection when all requested assets are withheld or a dependent is blocked', async () => {
    for (const protectedIds of [LEL_DEPENDENT_ASSETS, ['mi_jivanaghatana']]) {
      preparation({ protectedIds })
      await expect(enqueueLelRecalibration({ chartId: CHART, force: true })).resolves.toEqual({
        enqueued: false, reason: 'protected',
      })
    }
    expect(transactionQuery.mock.calls.some(([sql]) => sql.includes('INSERT'))).toBe(false)
    expect(invokeRunJob).not.toHaveBeenCalled()
  })

  it('can prepare the planner-eligible subset without adding or writing protected assets', async () => {
    preparation({ protectedIds: ['mi_pramana'] })
    const result = await enqueueLelRecalibration({ chartId: CHART, force: true })
    expect(result.enqueued).toBe(true)
    if (!result.enqueued) throw new Error('Expected an eligible subset')
    expect(new Set(result.plan)).toEqual(new Set(LEL_DEPENDENT_ASSETS.filter((asset) => asset !== 'mi_pramana')))
  })

  it('keeps the fixed scope target and admits only the registered requested subset when one identity is missing', async () => {
    const remaining = registry.filter((asset) => asset.asset_id !== 'mi_pramana')
    preparation({ registryRows: [...remaining, { ...registry[0], asset_id: 'synthetic_unrelated_writer' }] })
    const result = await enqueueLelRecalibration({ chartId: CHART, force: true })
    expect(result.enqueued).toBe(true)
    if (!result.enqueued) throw new Error('Expected a registered subset')
    expect(new Set(result.plan)).toEqual(new Set(remaining.map((asset) => asset.asset_id)))
    const params = transactionQuery.mock.calls.find(([sql]) => sql.includes('INSERT INTO build_runs'))?.[1]
    expect(params?.[2]).toBe(LEL_RECAL_SCOPE_TARGET)
  })

  it('returns nothing_to_build for a registered prerequisite without earned readiness', async () => {
    const required = { ...registry[0], asset_id: 'synthetic_upstream' }
    preparation({ registryRows: [...registry.map((asset) => asset.asset_id === 'ph_pramana'
      ? { ...asset, depends_on: [required.asset_id] }
      : asset), required] })
    await expect(enqueueLelRecalibration({ chartId: CHART })).resolves.toEqual({ enqueued: false, reason: 'nothing_to_build' })
    expect(transactionQuery.mock.calls.some(([sql]) => sql.includes('INSERT'))).toBe(false)
    expect(invokeRunJob).not.toHaveBeenCalled()
  })

  it('accepts an out-of-plan prerequisite only with an earned ready state and fresh receipt', async () => {
    const required = { ...registry[0], asset_id: 'synthetic_upstream' }
    const registryRows = [...registry.map((asset) => asset.asset_id === 'ph_pramana'
      ? { ...asset, depends_on: [required.asset_id] }
      : asset), required]
    const throughput = [{ asset_id: required.asset_id, state: 'lit' }]
    preparation({ registryRows, throughput, protectedIds: ['mi_pramana'],
      freshness: [{ asset_id: required.asset_id, state: 'stale', reasons: [] }] })
    await expect(enqueueLelRecalibration({ chartId: CHART, force: true })).resolves.toEqual({ enqueued: false, reason: 'nothing_to_build' })
    expect(invokeRunJob).not.toHaveBeenCalled()
    preparation({ registryRows, throughput, freshness: [{ asset_id: required.asset_id, state: 'fresh', reasons: [] }] })
    const result = await enqueueLelRecalibration({ chartId: CHART, force: true })
    expect(result.enqueued).toBe(true)
    if (!result.enqueued) throw new Error('Expected the earned prerequisite to admit the plan')
    expect(new Set(result.plan)).toEqual(new Set(LEL_DEPENDENT_ASSETS))
    expect(invokeRunJob).toHaveBeenCalledExactlyOnceWith(RUN, { reportDefiniteRejection: true })
  })

  it('propagates an absent target configuration before writes or dispatch', async () => {
    preparation({ registryRows: [] })
    await expect(enqueueLelRecalibration({ chartId: CHART })).rejects.toThrow('valid asset_ids')
    expect(transactionQuery.mock.calls.some(([sql]) => sql.includes('INSERT'))).toBe(false)
    expect(invokeRunJob).not.toHaveBeenCalled()
  })

  it('does not dispatch if queued asset persistence fails and rolls back', async () => {
    const failure = new Error('synthetic asset insert refusal')
    preparation({ assetInsertError: failure })
    await expect(enqueueLelRecalibration({ chartId: CHART })).rejects.toBe(failure)
    expect(phase).toEqual(['begin', 'rollback'])
    expect(invokeRunJob).not.toHaveBeenCalled()
  })

  it('reports an uncertain submission with the committed run ID and no state change or retry', async () => {
    invokeRunJob.mockRejectedValueOnce(Object.assign(new Error('synthetic response loss'), { code: 4 }))
    await expect(enqueueLelRecalibration({ chartId: CHART, force: true })).resolves.toEqual({
      enqueued: false, reason: 'dispatch_unknown', run_id: RUN,
    })
    expect(query).not.toHaveBeenCalled()
    expect(phase).toEqual(['begin', 'commit'])
    expect(invokeRunJob).toHaveBeenCalledOnce()
  })

  it('reports unknown if transport resolves without an operation identity', async () => {
    invokeRunJob.mockResolvedValueOnce({ executionName: '' })
    await expect(enqueueLelRecalibration({ chartId: CHART, force: true })).resolves.toEqual({
      enqueued: false, reason: 'dispatch_unknown', run_id: RUN,
    })
    expect(query).not.toHaveBeenCalled()
    expect(invokeRunJob).toHaveBeenCalledOnce()
  })

  it('propagates the dispatch failure message to both run and asset state after commit', async () => {
    invokeRunJob.mockRejectedValueOnce(new RunSubmissionRejected(new Error('synthetic transport refusal')))
    query.mockResolvedValueOnce({ rows: [] })
    await expect(enqueueLelRecalibration({ chartId: CHART, triggeredBy: UID })).rejects.toThrow('synthetic transport refusal')
    expect(phase).toEqual(['begin', 'commit'])
    const [sql, params] = query.mock.calls[2]
    expect(sql).toMatch(/last_error\s*=\s*\$1/)
    expect(sql).toMatch(/state = 'planned' AND started_at IS NULL/)
    expect(sql).toMatch(/WHERE run_id IN \(SELECT id FROM failed_run\)/)
    expect(sql).toMatch(/UPDATE build_run_assets/)
    expect(sql).toMatch(/error\s*=\s*\$1/)
    expect(params).toEqual(['synthetic transport refusal', RUN])
  })
})
