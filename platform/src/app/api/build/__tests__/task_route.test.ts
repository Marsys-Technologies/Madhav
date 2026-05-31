/**
 * Route tests for POST /api/build/task — Platform Modernization 4.build_trigger.
 *
 * Acceptance criteria:
 *   - Feature-flag default OFF → 503
 *   - Proper OIDC headers (queue name + matching audience JWT) → authorized
 *   - Missing headers or wrong audience → 401
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

const TEST_AUDIENCE = 'https://amjis-web-test.run.app/api/build/task'

/** Build a minimal fake JWT whose payload contains the given audience. */
function makeFakeJwt(aud: string): string {
  const header  = Buffer.from(JSON.stringify({ alg: 'RS256', typ: 'JWT' })).toString('base64url')
  const payload = Buffer.from(JSON.stringify({ aud, iss: 'test', sub: 'cloud-tasks' })).toString('base64url')
  return `${header}.${payload}.fakesig`
}

function makeReq(body: unknown, headers: Record<string, string> = {}): Request {
  return new Request('http://localhost/api/build/task', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      // Default: proper Cloud Tasks OIDC headers
      'x-cloudtasks-queuename': 'mars-build-queue',
      authorization: `Bearer ${makeFakeJwt(TEST_AUDIENCE)}`,
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
  process.env.BUILD_TASK_AUDIENCE = TEST_AUDIENCE
})

afterEach(() => {
  delete process.env.BUILD_TASK_AUDIENCE
  delete process.env.BUILD_TASK_AUTH_BYPASS
})

describe('POST /api/build/task — kill-switch', () => {
  it('returns 503 when MARSYS_FLAG_BUILD_TRIGGER_ENABLED is false', async () => {
    mockGetFlag.mockReturnValue(false)
    const res = await POST(
      makeReq({
        build_id: 'b1',
        chart_id: 'c1',
        ayanamsha_role: 'jh_true_chitra',
        triggered_by: 'manual:u1',
      }),
    )
    expect(res.status).toBe(503)
    expect(mockInvokeBuildJob).not.toHaveBeenCalled()
  })
})

describe('POST /api/build/task — OIDC gate', () => {
  it('returns 401 when no Cloud Tasks headers and no bearer', async () => {
    const res = await POST(
      makeReq(
        { build_id: 'b1', chart_id: 'c1', ayanamsha_role: 'jh_true_chitra', triggered_by: 'manual:u1' },
        { authorization: '', 'x-cloudtasks-queuename': '' },
      ),
    )
    expect(res.status).toBe(401)
  })

  it('returns 401 when queue header is missing even with valid bearer', async () => {
    const res = await POST(
      makeReq(
        { build_id: 'b1', chart_id: 'c1', ayanamsha_role: 'jh_true_chitra', triggered_by: 'manual:u1' },
        { 'x-cloudtasks-queuename': '' },
      ),
    )
    expect(res.status).toBe(401)
  })

  it('returns 401 when JWT audience does not match BUILD_TASK_AUDIENCE', async () => {
    const res = await POST(
      makeReq(
        { build_id: 'b1', chart_id: 'c1', ayanamsha_role: 'jh_true_chitra', triggered_by: 'manual:u1' },
        { authorization: `Bearer ${makeFakeJwt('https://wrong-audience.run.app')}` },
      ),
    )
    expect(res.status).toBe(401)
  })

  it('returns 401 when BUILD_TASK_AUTH_BYPASS is set but no proper OIDC headers (security regression)', async () => {
    // This env var must have zero effect on auth — setting it cannot bypass OIDC.
    process.env.BUILD_TASK_AUTH_BYPASS = 'test'
    const res = await POST(
      makeReq(
        { build_id: 'b1', chart_id: 'c1', ayanamsha_role: 'jh_true_chitra', triggered_by: 'manual:u1' },
        { authorization: '', 'x-cloudtasks-queuename': '' },
      ),
    )
    expect(res.status).toBe(401)
  })
})

describe('POST /api/build/task — input validation', () => {
  it('returns 400 when any field is missing', async () => {
    const res = await POST(makeReq({ build_id: 'b1', chart_id: 'c1' }))
    expect(res.status).toBe(400)
  })

  it('returns 400 when ayanamsha_role is invalid', async () => {
    const res = await POST(
      makeReq({
        build_id: 'b1',
        chart_id: 'c1',
        ayanamsha_role: 'nope',
        triggered_by: 'manual:u1',
      }),
    )
    expect(res.status).toBe(400)
  })
})

describe('POST /api/build/task — happy path', () => {
  it('invokes the Cloud Run Job and records a dispatch event', async () => {
    mockInvokeBuildJob.mockResolvedValue({
      executionName:
        'projects/p/locations/asia-south1/jobs/marsys-build-pipeline-job/executions/exec-xyz',
    })
    const res = await POST(
      makeReq({
        build_id: 'b1',
        chart_id: 'c1',
        ayanamsha_role: 'jh_true_chitra',
        triggered_by: 'manual:u1',
      }),
    )
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
    const res = await POST(
      makeReq({
        build_id: 'b1',
        chart_id: 'c1',
        ayanamsha_role: 'jh_true_chitra',
        triggered_by: 'manual:u1',
      }),
    )
    expect(res.status).toBe(500)
    expect(mockRecordBuildEvent).toHaveBeenCalled()
    const ev = mockRecordBuildEvent.mock.calls[0][0] as Record<string, string>
    expect(ev.status).toBe('failed')
    expect(ev.stage).toBe('dispatch')
  })
})
