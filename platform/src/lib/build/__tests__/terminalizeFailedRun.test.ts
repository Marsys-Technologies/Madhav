/**
 * terminalizeFailedRun.test.ts — Packet A2 ("Always record why it failed").
 *
 * Unit-level (mocked query) coverage for the shared helper that replaced the
 * copy-pasted "fail the run, then abort its queued assets with no error text"
 * idiom at three call sites (runs/route.ts x2, recalibrationEnqueue.ts).
 *
 * These tests FAIL against the pre-fix idiom (two separate UPDATEs, the second
 * with no `error` clause at all): they assert the SAME message parameter is
 * bound into BOTH the build_runs.last_error position and the build_run_assets.
 * error position of a single statement.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { terminalizeFailedRun, TERMINALIZE_EMPTY_MESSAGE_FALLBACK } from '@/lib/build/terminalizeFailedRun'

beforeEach(() => {
  vi.clearAllMocks()
  mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })
})

describe('terminalizeFailedRun', () => {
  it('issues exactly one statement carrying the message + runId', async () => {
    await terminalizeFailedRun('run-123', 'invokeRunJob failed: missing GCP_PROJECT env var')

    expect(mockQuery).toHaveBeenCalledOnce()
    const [sql, params] = mockQuery.mock.calls[0]!
    expect(params).toEqual(['invokeRunJob failed: missing GCP_PROJECT env var', 'run-123'])
    // Both tables written from the same statement (proof the value reaches both,
    // not just build_runs as the pre-fix idiom did).
    expect(sql).toMatch(/UPDATE build_runs/)
    expect(sql).toMatch(/last_error\s*=\s*\$1/)
    expect(sql).toMatch(/UPDATE build_run_assets/)
    expect(sql).toMatch(/error\s*=\s*\$1/)
  })

  it('never emits an empty-string error — falls back to a distinguishable, labeled message', async () => {
    await terminalizeFailedRun('run-456', '')
    const [, params] = mockQuery.mock.calls[0]!
    expect(params[0]).toBe(TERMINALIZE_EMPTY_MESSAGE_FALLBACK)
    expect(params[0]).not.toBe('')
    // The fallback names the case that produced it — distinguishable from a real
    // diagnosis, never a vague "unknown error".
    expect(params[0]).toMatch(/caller supplied no error message/)
  })

  it('treats whitespace-only text the same as empty (still not stored verbatim)', async () => {
    await terminalizeFailedRun('run-789', '   \n\t  ')
    const [, params] = mockQuery.mock.calls[0]!
    expect(params[0]).toBe(TERMINALIZE_EMPTY_MESSAGE_FALLBACK)
  })

  it('passes non-empty text through unmodified — the honest, common case', async () => {
    await terminalizeFailedRun('run-abc', 'ECONNREFUSED 127.0.0.1:8080')
    const [, params] = mockQuery.mock.calls[0]!
    expect(params[0]).toBe('ECONNREFUSED 127.0.0.1:8080')
  })

  it('only aborts still-queued assets and only for a run not already terminal', async () => {
    await terminalizeFailedRun('run-xyz', 'boom')
    const [sql] = mockQuery.mock.calls[0]!
    expect(sql).toMatch(/state\s*=\s*'queued'/)
    expect(sql).toMatch(/NOT IN \('completed', 'failed', 'stopped'\)/)
  })
})
