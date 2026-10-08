/**
 * Unit tests for lib/build/jobInvoker.ts — Platform Modernization 4.build_trigger.
 */

import { describe, it, expect } from 'vitest'
import {
  readJobInvokerEnv,
  jobPath,
  invokeBuildJob,
  invokeRunJob,
  type JobInvokerEnv,
  type JobTransport,
} from '../jobInvoker'

const ENV: JobInvokerEnv = {
  gcpProject: 'madhav-astrology',
  jobLocation: 'asia-south1',
  jobId: 'brahma-build-pipeline-job',
}

describe('readJobInvokerEnv', () => {
  it('returns env block with sane defaults', () => {
    const out = readJobInvokerEnv({
      GCP_PROJECT: 'p',
    } as unknown as NodeJS.ProcessEnv)
    expect(out.gcpProject).toBe('p')
    expect(out.jobLocation).toBe('asia-south1')
    expect(out.jobId).toBe('brahma-build-pipeline-job')
  })

  it('overrides default jobId when BUILD_JOB_NAME is set', () => {
    const out = readJobInvokerEnv({
      GCP_PROJECT: 'p',
      BUILD_JOB_NAME: 'staging-build-job',
    } as unknown as NodeJS.ProcessEnv)
    expect(out.jobId).toBe('staging-build-job')
  })

  it('throws when GCP_PROJECT is missing', () => {
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
