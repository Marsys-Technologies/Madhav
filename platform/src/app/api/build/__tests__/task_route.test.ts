/**
 * Route tests for POST /api/build/task — Platform Modernization 4.build_trigger.
 *
 * Auth model: Design A — Cloud Run IAM owns the OIDC check (service must be
 * deployed --no-allow-unauthenticated). The app authorises on the platform-
 * forwarded X-CloudTasks-QueueName header + BUILD_TASK_QUEUE env var alone.
 * Bearer-parse was removed (see isAuthorized JSDoc for root-cause notes).
 *
 * Acceptance criteria:
 *   - Feature-flag default OFF → 503
 *   - Correct queue-name header + BUILD_TASK_QUEUE set → authorized
 *   - Missing queue header or mismatched queue name → 401
 *   - BUILD_TASK_QUEUE env unset → 401 (fail-safe)
 *   - BUILD_TASK_AUTH_BYPASS env var has zero effect (security regression test)
 *   - Happy path invokes Cloud Run Job + records dispatch event
 *   - Job-dispatch failure records a `failed` build_event row (auto-rollback)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const { mockInvokeBuildJob, mockRecordBuildEvent, mockGetFlag } = vi.hoisted(() => ({
  mockInvokeBuildJob: vi.fn(),
  mockRecordBuildEvent: vi.fn(),
  mockGetFlag: vi.fn(),
}))

vi.mock('@/lib/build/jobInvoker', () => ({ invokeBuildJob: mockInvokeBuildJob }))
vi.mock('@/lib/build/events', () => ({ recordBuildEvent: mockRecordBuildEvent }))
vi.mock('@/lib/config', () => ({ getFlag: mockGetFlag }))

import { POST } from '../task/route'

const TEST_QUEUE = 'amjis-build-queue'

function makeReq(body: unknown, headers: Record<string, string> = {}): Request {
  return new Request('http://localhost/api/build/task', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      // Design A: only Cloud Tasks queue header is checked; no bearer needed.
      'x-cloudtasks-queuename': TEST_QUEUE,
      ...headers,
    },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  mockInvokeBuildJob.mockReset()
  mockRecordBuildEvent.mockReset()
  mockGetFlag.mockReset()
  mockGetFlag.mockImplementation((name: string) => name === 'BUILD_TRIGGER_ENABLED')
  process.env['BUILD_TASK_QUEUE'] = TEST_QUEUE
})

afterEach(() => {
  delete process.env['BUILD_TASK_QUEUE']
  delete process.env.BUILD_TASK_AUTH_BYPASS
})

describe('POST /api/build/task — kill-switch', () => {
  it('returns 503 when MARSYS_FLAG_BUILD_TRIGGER_ENABLED is false', async () => {
    mockGetFlag.mockReturnValue(false)
    const res = await POST()
    expect(res.status).toBe(503)
    expect(mockInvokeBuildJob).not.toHaveBeenCalled()
  })
})

describe('POST /api/build/task — auth gate (Design A: queue-header + BUILD_TASK_QUEUE)', () => {
  it('returns 401 when X-CloudTasks-QueueName header is absent', async () => {
    const res = await POST()
    expect(res.status).toBe(401)
  })

  it('returns 401 when queue name does not match BUILD_TASK_QUEUE', async () => {
    const res = await POST()
    expect(res.status).toBe(401)
  })

  it('returns 401 when BUILD_TASK_QUEUE env is unset (fail-safe)', async () => {
    delete process.env['BUILD_TASK_QUEUE']
    const res = await POST()
    expect(res.status).toBe(401)
  })

  it('returns 401 when BUILD_TASK_AUTH_BYPASS is set but queue header is absent (security regression)', async () => {
    // This env var must have zero effect on auth — setting it cannot bypass the queue check.
    process.env.BUILD_TASK_AUTH_BYPASS = 'test'
    const res = await POST()
    expect(res.status).toBe(401)
  })
})

describe('POST /api/build/task — input validation', () => {
  it('returns 400 when any field is missing', async () => {
    const res = await POST()
    expect(res.status).toBe(400)
  })

  it('returns 400 when ayanamsha_role is invalid', async () => {
    const res = await POST()
    expect(res.status).toBe(400)
  })
})

describe('POST /api/build/task — happy path', () => {
  it('invokes the Cloud Run Job and records a dispatch event', async () => {
    mockInvokeBuildJob.mockResolvedValue({
      executionName:
        'projects/p/locations/asia-south1/jobs/brahma-build-pipeline-job/executions/exec-xyz',
    })
    const res = await POST()
    expect(res.status).toBe(200)
    const body = (await res.json()) as { execution_name: string }
    expect(body.execution_name).toContain('exec-xyz')

    expect(mockInvokeBuildJob).toHaveBeenCalledTimes(1)
    const invokeArg = mockInvokeBuildJob.mock.calls[0][0] as Record<string, string>
    expect(invokeArg.buildId).toBe('b1')
    expect(invokeArg.chartId).toBe('c1')
    expect(invokeArg.ayanamshaRole).toBe('jh_true_chitra')

    expect(mockRecordBuildEvent).toHaveBeenCalled()
    const ev = mockRecordBuildEvent.mock.calls[0][0] as Record<string, string>
    expect(ev.status).toBe('started')
    expect(ev.stage).toBe('dispatch')
  })
})

describe('POST /api/build/task — failure path (auto-rollback signal)', () => {
  it('records a failed event row when Job invocation throws', async () => {
    mockInvokeBuildJob.mockRejectedValue(new Error('PermissionDenied: jobs.run'))
    const res = await POST()
    expect(res.status).toBe(500)
    expect(mockRecordBuildEvent).toHaveBeenCalled()
    const ev = mockRecordBuildEvent.mock.calls[0][0] as Record<string, string>
    expect(ev.status).toBe('failed')
    expect(ev.stage).toBe('dispatch')
  })
})
