/**
 * End-to-end smoke test for the autonomous build trigger spine — Stream B 3/3.
 *
 * Chains the two API surfaces that Cloud Tasks fronts:
 *
 *   1. POST /api/build/start  → enqueueBuild() (Cloud Tasks createTask)
 *   2. POST /api/build/task   → invokeBuildJob() (Cloud Run JobsClient.RunJob)
 *
 * Assertions:
 *   - Happy path:    /start (owner) → enqueueBuild called → /task → invokeBuildJob
 *                    called → recordBuildEvent records a `started` dispatch row.
 *   - Failure path:  /task with invokeBuildJob throwing → recordBuildEvent records
 *                    a `failed` dispatch row (auto-rollback signal).
 *   - Authz path:    /start with permission=deny (no chart row) → 404; the chain
 *                    never reaches the Cloud Tasks transport. (The brief calls
 *                    this 403; with authorizeChartAccess the deny case is 404,
 *                    view-grantee is 403 — we exercise the 404 deny path and
 *                    additionally assert view-grantee → 403 below.)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const {
  mockQuery,
  mockGetServerUser,
  mockEnqueueBuild,
  mockInvokeBuildJob,
  mockRecordBuildEvent,
  mockGetFlag,
} = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
  mockEnqueueBuild: vi.fn(),
  mockInvokeBuildJob: vi.fn(),
  mockRecordBuildEvent: vi.fn(),
  mockGetFlag: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/build/trigger', () => ({ enqueueBuild: mockEnqueueBuild }))
vi.mock('@/lib/build/jobInvoker', () => ({ invokeBuildJob: mockInvokeBuildJob }))
vi.mock('@/lib/build/events', () => ({ recordBuildEvent: mockRecordBuildEvent }))
vi.mock('@/lib/config', () => ({ getFlag: mockGetFlag }))

// Use the real authorizeChartAccess so we exercise the actual permission
// resolver against mockQuery rows.
vi.mock('@/lib/auth/authorizeChartAccess', async () => {
  const actual = await vi.importActual<
    typeof import('@/lib/auth/authorizeChartAccess')
  >('@/lib/auth/authorizeChartAccess')
  return actual
})

// Imported AFTER mocks so the route picks up the mocked modules.
import { POST as POST_START } from '../start/route'
import { POST as POST_TASK } from '../task/route'

function makeReq(url: string, body: unknown, headers: Record<string, string> = {}): Request {
  return new Request(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json', ...headers },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  mockQuery.mockReset()
  mockGetServerUser.mockReset()
  mockEnqueueBuild.mockReset()
  mockInvokeBuildJob.mockReset()
  mockRecordBuildEvent.mockReset()
  mockGetFlag.mockReset()
  mockGetFlag.mockImplementation((name: string) => name === 'BUILD_TRIGGER_ENABLED')
  process.env.BUILD_TASK_AUTH_BYPASS = 'test'
})

afterEach(() => {
  delete process.env.BUILD_TASK_AUTH_BYPASS
})

describe('build-trigger E2E: happy path (start → task → event)', () => {
  it('chains the two routes end-to-end with all writes recorded', async () => {
    // ── Stage 1: /api/build/start as the chart owner ────────────────────
    mockGetServerUser.mockResolvedValue({ uid: 'owner-7' })
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) {
        return Promise.resolve({ rows: [{ role: 'guest' }] })
      }
      if (/FROM charts WHERE id/.test(sql)) {
        return Promise.resolve({ rows: [{ owner_id: 'owner-7' }] })
      }
      return Promise.resolve({ rows: [] })
    })
    mockEnqueueBuild.mockResolvedValue({
      buildId: 'build-e2e-1',
      taskName: 'projects/p/locations/asia-south1/queues/amjis-build-queue/tasks/t-1',
    })

    const startRes = await POST_START(
      makeReq('http://localhost/api/build/start', {
        chart_id: 'chart-77',
        ayanamsha_role: 'jh_true_chitra',
      }),
    )
    expect(startRes.status).toBe(200)
    const startBody = (await startRes.json()) as { build_id: string; task_name: string }
    expect(startBody.build_id).toBe('build-e2e-1')

    // Cloud Tasks enqueue must have happened with the planner-validated payload.
    expect(mockEnqueueBuild).toHaveBeenCalledTimes(1)
    const enqueueArg = mockEnqueueBuild.mock.calls[0][0] as {
      chartId: string
      ayanamshaRole: string
      triggeredBy: string
    }
    expect(enqueueArg.chartId).toBe('chart-77')
    expect(enqueueArg.ayanamshaRole).toBe('jh_true_chitra')
    expect(enqueueArg.triggeredBy).toBe('manual:owner-7')

    // ── Stage 2: /api/build/task — Cloud Tasks calls us back ──────────
    mockInvokeBuildJob.mockResolvedValue({
      executionName:
        'projects/p/locations/asia-south1/jobs/marsys-build-pipeline-job/executions/exec-e2e-1',
    })
    const taskRes = await POST_TASK(
      makeReq('http://localhost/api/build/task', {
        build_id: startBody.build_id,
        chart_id: 'chart-77',
        ayanamsha_role: 'jh_true_chitra',
        triggered_by: 'manual:owner-7',
      }),
    )
    expect(taskRes.status).toBe(200)

    // Cloud Run Job invocation must have been made.
    expect(mockInvokeBuildJob).toHaveBeenCalledTimes(1)
    const invokeArg = mockInvokeBuildJob.mock.calls[0][0] as {
      buildId: string
      chartId: string
      ayanamshaRole: string
      triggeredBy: string
    }
    expect(invokeArg.buildId).toBe('build-e2e-1')
    expect(invokeArg.chartId).toBe('chart-77')
    expect(invokeArg.ayanamshaRole).toBe('jh_true_chitra')

    // A `started` dispatch event must have been recorded.
    expect(mockRecordBuildEvent).toHaveBeenCalledTimes(1)
    const eventArg = mockRecordBuildEvent.mock.calls[0][0] as {
      buildId: string
      asset: string
      stage: string
      status: string
    }
    expect(eventArg.buildId).toBe('build-e2e-1')
    expect(eventArg.asset).toBe('orchestrator')
    expect(eventArg.stage).toBe('dispatch')
    expect(eventArg.status).toBe('started')
  })
})

describe('build-trigger E2E: failure path (rollback signal)', () => {
  it('records a failed dispatch event when the Cloud Run Job invocation throws', async () => {
    mockInvokeBuildJob.mockRejectedValue(new Error('PermissionDenied: jobs.run'))

    const res = await POST_TASK(
      makeReq('http://localhost/api/build/task', {
        build_id: 'build-e2e-fail',
        chart_id: 'chart-77',
        ayanamsha_role: 'jh_true_chitra',
        triggered_by: 'manual:owner-7',
      }),
    )

    expect(res.status).toBe(500)
    const body = (await res.json()) as { error: string }
    expect(body.error).toBe('job_dispatch_failed')

    // Auto-rollback: a `failed` event row must have been written so the
    // cockpit reverts its progress visualization.
    expect(mockRecordBuildEvent).toHaveBeenCalledTimes(1)
    const arg = mockRecordBuildEvent.mock.calls[0][0] as {
      stage: string
      status: string
      metadata: Record<string, unknown>
    }
    expect(arg.stage).toBe('dispatch')
    expect(arg.status).toBe('failed')
    expect(arg.metadata.error).toBe('job_dispatch_failed')
  })
})

describe('build-trigger E2E: authz path (denied principal)', () => {
  it('returns 403 for a view-only grantee and never touches the enqueue transport', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'view-grantee' })
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) {
        return Promise.resolve({ rows: [{ role: 'guest' }] })
      }
      if (/FROM charts WHERE id/.test(sql)) {
        return Promise.resolve({ rows: [{ owner_id: 'someone-else' }] })
      }
      if (/FROM chart_grants/.test(sql)) {
        return Promise.resolve({ rows: [{ permission: 'view' }] })
      }
      return Promise.resolve({ rows: [] })
    })

    const res = await POST_START(
      makeReq('http://localhost/api/build/start', {
        chart_id: 'chart-77',
        ayanamsha_role: 'jh_true_chitra',
      }),
    )
    expect(res.status).toBe(403)
    expect(mockEnqueueBuild).not.toHaveBeenCalled()
  })

  it('returns 404 for a fully denied principal (no chart row, no grant)', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'stranger' })
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM profiles/.test(sql)) {
        return Promise.resolve({ rows: [{ role: 'guest' }] })
      }
      return Promise.resolve({ rows: [] })
    })

    const res = await POST_START(
      makeReq('http://localhost/api/build/start', {
        chart_id: 'chart-99',
        ayanamsha_role: 'jh_true_chitra',
      }),
    )
    expect(res.status).toBe(404)
    expect(mockEnqueueBuild).not.toHaveBeenCalled()
  })
})
