/**
 * Unit tests for lib/build/trigger.ts — Platform Modernization 4.build_trigger.
 *
 * Validates:
 *   - readBuildTriggerEnv throws when required env vars are missing
 *   - queuePath formats the Cloud Tasks parent correctly
 *   - enqueueBuild calls the transport with the right OIDC + URL + payload,
 *     and persists a build_events:enqueued row
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query } from '@/lib/db/client'
import {
  readBuildTriggerEnv,
  queuePath,
  enqueueBuild,
  type BuildTriggerEnv,
  type TaskTransport,
} from '../trigger'

const ENV: BuildTriggerEnv = {
  gcpProject: 'madhav-astrology',
  queueLocation: 'asia-south1',
  queueId: 'amjis-build-queue',
  invokerSaEmail: 'amjis-build-invoker@madhav-astrology.iam.gserviceaccount.com',
  taskAudience: 'https://amjis-web-938361928218.asia-south1.run.app',
}

function makeTransport(): { transport: TaskTransport; calls: unknown[] } {
  const calls: unknown[] = []
  return {
    calls,
    transport: {
      async createTask(args) {
        calls.push(args)
        return { name: 'projects/p/locations/asia-south1/queues/q/tasks/t-1' }
      },
    },
  }
}

beforeEach(() => {
  vi.mocked(query).mockClear()
  vi.mocked(query).mockResolvedValue({ rows: [] })
})

describe('readBuildTriggerEnv', () => {
  it('returns the env block when all vars are present', () => {
    const out = readBuildTriggerEnv({
      GCP_PROJECT: 'p',
      BUILD_TASK_QUEUE_LOCATION: 'asia-south1',
      BUILD_TASK_QUEUE: 'q',
      BUILD_TASK_INVOKER_SA: 'sa@x',
      BUILD_TASK_AUDIENCE: 'https://x',
    } as NodeJS.ProcessEnv)
    expect(out.gcpProject).toBe('p')
    expect(out.queueId).toBe('q')
  })

  it('throws when any required var is missing', () => {
    expect(() => readBuildTriggerEnv({} as NodeJS.ProcessEnv)).toThrow(
      /missing env vars/,
    )
  })
})

describe('queuePath', () => {
  it('formats as projects/.../locations/.../queues/...', () => {
    expect(queuePath(ENV)).toBe(
      'projects/madhav-astrology/locations/asia-south1/queues/amjis-build-queue',
    )
  })
})

describe('enqueueBuild', () => {
  it('creates a Cloud Task pointing at /api/build/task with OIDC + JSON payload, and persists an enqueue row', async () => {
    const { transport, calls } = makeTransport()
    const result = await enqueueBuild(
      {
        chartId: 'chart-abc',
        ayanamshaRole: 'jh_true_chitra',
        triggeredBy: 'manual:uid-1',
      },
      { env: ENV, transport, buildId: 'build-fixed-1' },
    )

    expect(result.buildId).toBe('build-fixed-1')
    expect(result.taskName).toMatch(/^projects\//)

    // Transport got the right args.
    expect(calls.length).toBe(1)
    const arg = calls[0] as {
      parent: string
      task: {
        httpRequest: {
          httpMethod: string
          url: string
          headers: Record<string, string>
          body: string
          oidcToken: { serviceAccountEmail: string; audience: string }
        }
      }
    }
    expect(arg.parent).toBe(queuePath(ENV))
    expect(arg.task.httpRequest.httpMethod).toBe('POST')
    expect(arg.task.httpRequest.url).toBe(
      'https://amjis-web-938361928218.asia-south1.run.app/api/build/task',
    )
    expect(arg.task.httpRequest.oidcToken.audience).toBe(ENV.taskAudience)
    expect(arg.task.httpRequest.oidcToken.serviceAccountEmail).toBe(ENV.invokerSaEmail)

    const decoded = JSON.parse(
      Buffer.from(arg.task.httpRequest.body, 'base64').toString('utf8'),
    ) as Record<string, string>
    expect(decoded.build_id).toBe('build-fixed-1')
    expect(decoded.chart_id).toBe('chart-abc')
    expect(decoded.ayanamsha_role).toBe('jh_true_chitra')
    expect(decoded.triggered_by).toBe('manual:uid-1')

    // build_events:enqueued row persisted.
    expect(query).toHaveBeenCalled()
    const sqlCalls = vi.mocked(query).mock.calls
    const insertCall = sqlCalls.find(c => /INSERT INTO build_events/i.test(c[0] as string))
    expect(insertCall).toBeDefined()
    const params = insertCall![1] as unknown[]
    expect(params[0]).toBe('build-fixed-1')
    expect(params[1]).toBe('chart-abc')
    expect(params[2]).toBe('jh_true_chitra')
  })
})
