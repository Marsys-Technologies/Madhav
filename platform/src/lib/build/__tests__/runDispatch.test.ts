/**
 * Post-commit run dispatch (Jātaka chart workspace, Task 5).
 *
 * Dispatch can never be part of the preparation transaction. On failure the
 * run is marked failed and its queued assets aborted; the chart-correction path
 * tags last_error with JOB_DISPATCH_FAILED so shared readiness reads the chart
 * as Needs rebuild, while the cockpit keeps its raw error text.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
const { mockQuery, mockInvokeRunJob } = vi.hoisted(() => ({ mockQuery: vi.fn(), mockInvokeRunJob: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/build/jobInvoker', () => ({ invokeRunJob: mockInvokeRunJob }))

import { dispatchPreparedRun } from '../runDispatch'

beforeEach(() => {
  mockQuery.mockReset()
  mockQuery.mockResolvedValue({ rows: [], rowCount: 1 })
  mockInvokeRunJob.mockReset()
})

describe('dispatchPreparedRun', () => {
  it('returns the execution name and writes nothing on success', async () => {
    mockInvokeRunJob.mockResolvedValue({ executionName: 'exec-9' })
    expect(await dispatchPreparedRun('run-1')).toEqual({ ok: true, executionName: 'exec-9' })
    expect(mockInvokeRunJob).toHaveBeenCalledWith('run-1')
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('marks the run failed and aborts queued assets, keeping the raw error by default', async () => {
    mockInvokeRunJob.mockRejectedValue(new Error('cloud run down'))
    const result = await dispatchPreparedRun('run-1')
    expect(result).toEqual({ ok: false, code: 'JOB_DISPATCH_FAILED', message: 'cloud run down' })
    // A2: one shared statement (terminalizeFailedRun) carries the same text to both tables.
    expect(mockQuery).toHaveBeenCalledTimes(1)
    const [sql, params] = mockQuery.mock.calls[0]
    expect(sql).toContain('UPDATE build_runs')
    expect(sql).toContain('UPDATE build_run_assets')
    expect(sql).toContain("state = 'aborted'")
    expect(sql).toMatch(/SET state = 'aborted', ended_at = NOW\(\), error = \$1/)
    expect(params).toEqual(['cloud run down', 'run-1'])
  })

  it('tags last_error with the JOB_DISPATCH_FAILED prefix when asked (chart correction)', async () => {
    mockInvokeRunJob.mockRejectedValue(new Error('spawn ENOENT'))
    await dispatchPreparedRun('run-2', { failurePrefix: 'JOB_DISPATCH_FAILED' })
    expect(mockQuery.mock.calls[0][1]).toEqual(['JOB_DISPATCH_FAILED: spawn ENOENT', 'run-2'])
  })

  it('still reports the failure honestly if recording it also fails', async () => {
    mockInvokeRunJob.mockRejectedValue(new Error('down'))
    mockQuery.mockRejectedValue(new Error('db gone'))
    expect(await dispatchPreparedRun('run-3')).toEqual({ ok: false, code: 'JOB_DISPATCH_FAILED', message: 'down' })
  })
})
