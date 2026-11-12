/**
 * Unit tests for lib/build/jobInvoker.ts — Platform Modernization 4.build_trigger.
 */

import { EventEmitter } from 'node:events'
import { createRequire } from 'node:module'
import { afterEach, describe, it, expect, vi } from 'vitest'
import {
  readJobInvokerEnv,
  jobPath,
  invokeBuildJob,
  invokeRunJob,
  RunSubmissionRejected,
  type JobInvokerEnv,
  type JobTransport,
} from '../jobInvoker'

const { cloudRunJob, spawnProcess } = vi.hoisted(() => ({ cloudRunJob: vi.fn(), spawnProcess: vi.fn() }))
vi.mock('child_process', () => ({ spawn: spawnProcess }))
vi.mock('@google-cloud/run', () => ({
  JobsClient: class { runJob = cloudRunJob },
}))

afterEach(() => {
  vi.unstubAllEnvs()
  cloudRunJob.mockReset()
  spawnProcess.mockReset()
})

const ENV: JobInvokerEnv = {
  gcpProject: 'madhav-astrology',
  jobLocation: 'asia-south1',
  jobId: 'brahma-build-pipeline-job',
}

describe('readJobInvokerEnv', () => {
  it('returns env block with sane defaults', () => {
    const out = readJobInvokerEnv({
      GOOGLE_CLOUD_PROJECT: 'p',
    } as unknown as NodeJS.ProcessEnv)
    expect(out.gcpProject).toBe('p')
    expect(out.jobLocation).toBe('asia-south1')
    expect(out.jobId).toBe('brahma-build-pipeline-job')
  })

  it('overrides default jobId when BUILD_JOB_NAME is set', () => {
    const out = readJobInvokerEnv({
      GOOGLE_CLOUD_PROJECT: 'p',
      BUILD_JOB_NAME: 'staging-build-job',
    } as unknown as NodeJS.ProcessEnv)
    expect(out.jobId).toBe('staging-build-job')
  })

  it('throws when GOOGLE_CLOUD_PROJECT is missing', () => {
    expect(() => readJobInvokerEnv({} as unknown as NodeJS.ProcessEnv)).toThrow()
  })
})

describe('jobPath', () => {
  it('builds projects/{p}/locations/{r}/jobs/{j}', () => {
    expect(jobPath(ENV)).toBe(
      'projects/madhav-astrology/locations/asia-south1/jobs/brahma-build-pipeline-job',
    )
  })
})

describe('invokeBuildJob', () => {
  it('passes chart_id + ayanamsha_role + build_id as container args; returns execution name', async () => {
    const seen: { jobName?: string; containerArgs?: string[]; envOverrides?: Record<string, string> } = {}
    const transport: JobTransport = {
      async runJob({ jobName, containerArgs, envOverrides }) {
        seen.jobName = jobName
        seen.containerArgs = containerArgs
        seen.envOverrides = envOverrides
        return {
          executionName:
            'projects/madhav-astrology/locations/asia-south1/jobs/brahma-build-pipeline-job/executions/exec-xyz',
        }
      },
    }

    const out = await invokeBuildJob(
      {
        buildId: 'build-1',
        chartId: 'chart-abc',
        ayanamshaRole: 'jh_true_chitra',
        triggeredBy: 'manual:uid-1',
      },
      { env: ENV, transport },
    )

    expect(out.executionName).toContain('exec-xyz')
    expect(seen.jobName).toBe(jobPath(ENV))
    expect(seen.containerArgs).toEqual([
      '--build-id', 'build-1',
      '--chart-id', 'chart-abc',
    ])
    expect(seen.envOverrides?.MARSYS_BUILD_ID).toBe('build-1')
    expect(seen.envOverrides?.MARSYS_BUILD_CHART_ID).toBe('chart-abc')
    expect(seen.envOverrides?.MARSYS_BUILD_AYANAMSHA_ROLE).toBe('jh_true_chitra')
  })
})

describe('invokeRunJob force flag (FIX2: a clear must never be followed by a delta-skip)', () => {
  function capture() {
    const seen: { envOverrides?: Record<string, string>; containerArgs?: string[] } = {}
    const transport: JobTransport = {
      async runJob({ containerArgs, envOverrides }) {
        seen.containerArgs = containerArgs
        seen.envOverrides = envOverrides
        return { executionName: 'exec-1' }
      },
    }
    return { seen, transport }
  }

  it('does NOT set NIRMANA_FORCE_EXECUTE by default', async () => {
    const { seen, transport } = capture()
    await invokeRunJob('run-1', { env: ENV, transport })
    expect(seen.containerArgs).toEqual(['--run-id', 'run-1'])
    expect(seen.envOverrides).toEqual({ MARSYS_RUN_ID: 'run-1' })
  })

  it('sets NIRMANA_FORCE_EXECUTE=1 on that one execution when forceExecute is true', async () => {
    const { seen, transport } = capture()
    await invokeRunJob('run-1', { env: ENV, transport, forceExecute: true })
    expect(seen.envOverrides).toEqual({ MARSYS_RUN_ID: 'run-1', NIRMANA_FORCE_EXECUTE: '1' })
  })
})

describe('invokeRunJob — definite refusal evidence is opt-in', () => {
  it('classifies a missing project as rejected before an SDK call', async () => {
    vi.stubEnv('GOOGLE_CLOUD_PROJECT', undefined)
    vi.stubEnv('GCP_PROJECT', undefined)
    vi.stubEnv('GCLOUD_PROJECT', undefined)
    const error = invokeRunJob('synthetic-run', { reportDefiniteRejection: true })
    await expect(error).rejects.toBeInstanceOf(RunSubmissionRejected)
    expect(cloudRunJob).not.toHaveBeenCalled()
  })

  it.each([3, 5, 7, 9, 16])('wraps a direct SDK application refusal (status %s)', async (code) => {
    const refusal = Object.assign(new Error('synthetic refusal'), { code })
    cloudRunJob.mockRejectedValueOnce(refusal)
    const submission = invokeRunJob('synthetic-run', { env: ENV, reportDefiniteRejection: true })
    await expect(submission).rejects.toBeInstanceOf(RunSubmissionRejected)
    await expect(submission).rejects.toMatchObject({ cause: refusal })
    expect(cloudRunJob).toHaveBeenCalledOnce()
  })

  it.each([1, 2, 4, 8, 13, 14])('preserves an uncertain SDK error (status %s) without retry', async (code) => {
    const uncertain = Object.assign(new Error('synthetic uncertainty'), { code })
    cloudRunJob.mockRejectedValueOnce(uncertain)
    await expect(invokeRunJob('synthetic-run', { env: ENV, reportDefiniteRejection: true })).rejects.toBe(uncertain)
    expect(cloudRunJob).toHaveBeenCalledOnce()
  })

  it('classifies a local spawn failure before any child was created', async () => {
    vi.stubEnv('BUILD_EXECUTOR', 'local')
    const child = Object.assign(new EventEmitter(), { stderr: new EventEmitter(), pid: undefined })
    spawnProcess.mockImplementationOnce(() => {
      queueMicrotask(() => child.emit('error', new Error('synthetic spawn failure')))
      return child
    })
    await expect(invokeRunJob('synthetic-run', { reportDefiniteRejection: true })).rejects.toBeInstanceOf(RunSubmissionRejected)
    expect(spawnProcess).toHaveBeenCalledOnce()
    expect(cloudRunJob).not.toHaveBeenCalled()
  })

  it('preserves uncertainty when an existing local child exits during the grace period', async () => {
    vi.stubEnv('BUILD_EXECUTOR', 'local')
    const child = Object.assign(new EventEmitter(), { stderr: new EventEmitter(), pid: 4321, exitCode: 1 })
    spawnProcess.mockReturnValueOnce(child)
    const rejection = invokeRunJob('synthetic-run', { reportDefiniteRejection: true })
    await expect(rejection).rejects.toThrow('exited immediately')
    await expect(rejection).rejects.not.toBeInstanceOf(RunSubmissionRejected)
    expect(spawnProcess).toHaveBeenCalledOnce()
    expect(cloudRunJob).not.toHaveBeenCalled()
  })

  it('does not inspect a code getter for default or injected callers', async () => {
    const code = vi.fn(() => { throw new Error('the getter must not be read') })
    const rejection = Object.defineProperty(new Error('synthetic original rejection'), 'code', { get: code })
    cloudRunJob.mockRejectedValueOnce(rejection)
    await expect(invokeRunJob('synthetic-run', { env: ENV })).rejects.toBe(rejection)
    const transport = { runJob: vi.fn().mockRejectedValueOnce(rejection) }
    await expect(invokeRunJob('synthetic-run', { env: ENV, transport, reportDefiniteRejection: true })).rejects.toBe(rejection)
    expect(code).not.toHaveBeenCalled()
  })

  it('preserves named pending and successful initial GAX operations but treats named terminal failure as unknown', async () => {
    const fromTest = createRequire(import.meta.url)
    const fromCloudRun = createRequire(fromTest.resolve('@google-cloud/run'))
    const { Operation, createDefaultBackoffSettings } = fromCloudRun('google-gax')
    const getOperation = vi.fn(() => { throw new Error('the initial response must not be polled') })
    const descriptor = {
      operationsClient: { getOperation },
      responseDecoder: vi.fn(() => ({ name: 'synthetic-execution' })),
    }
    const name = 'synthetic-operation'
    const initial = { name, done: true, result: 'error', error: { code: 7, message: 'synthetic terminal error' } }
    const operation = (raw: object) => new Operation(raw, descriptor, createDefaultBackoffSettings())
    const failed = operation(initial)
    expect(failed.done).toBe(true)
    expect(failed.error).toMatchObject({ code: 7 })
    expect(failed.latestResponse).toBe(initial)
    cloudRunJob.mockResolvedValueOnce([failed])
    await expect(invokeRunJob('synthetic-run', { env: ENV, reportDefiniteRejection: true })).resolves.toEqual({ executionName: '' })
    cloudRunJob.mockResolvedValueOnce([failed])
    await expect(invokeRunJob('synthetic-run', { env: ENV })).resolves.toEqual({ executionName: name })

    const pending = operation({ name, done: false })
    const succeeded = operation({ name, done: true, result: 'response', response: { value: new Uint8Array() } })
    for (const good of [pending, succeeded]) {
      cloudRunJob.mockResolvedValueOnce([good])
      await expect(invokeRunJob('synthetic-run', { env: ENV, reportDefiniteRejection: true })).resolves.toEqual({ executionName: name })
    }
    expect(cloudRunJob).toHaveBeenCalledTimes(4)
    expect(getOperation).not.toHaveBeenCalled()
  })

  it('leaves default callers and injected transport errors unchanged', async () => {
    const refusal = Object.assign(new Error('synthetic failure'), { code: 7 })
    cloudRunJob.mockRejectedValueOnce(refusal)
    await expect(invokeRunJob('synthetic-run', { env: ENV })).rejects.toBe(refusal)
    const transport = { runJob: vi.fn().mockRejectedValueOnce(refusal) }
    await expect(invokeRunJob('synthetic-run', { env: ENV, transport, reportDefiniteRejection: true })).rejects.toBe(refusal)
    expect(transport.runJob).toHaveBeenCalledOnce()
  })
})
