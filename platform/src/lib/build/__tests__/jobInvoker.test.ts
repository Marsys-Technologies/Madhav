/**
 * Unit tests for lib/build/jobInvoker.ts — Platform Modernization 4.build_trigger.
 */

import { describe, it, expect } from 'vitest'
import {
  readJobInvokerEnv,
  jobPath,
  invokeBuildJob,
  type JobInvokerEnv,
  type JobTransport,
} from '../jobInvoker'

const ENV: JobInvokerEnv = {
  gcpProject: 'madhav-astrology',
  jobLocation: 'asia-south1',
  jobId: 'marsys-build-pipeline-job',
}

describe('readJobInvokerEnv', () => {
  it('returns env block with sane defaults', () => {
    const out = readJobInvokerEnv({
      GCP_PROJECT: 'p',
    } as unknown as NodeJS.ProcessEnv)
    expect(out.gcpProject).toBe('p')
    expect(out.jobLocation).toBe('asia-south1')
    expect(out.jobId).toBe('marsys-build-pipeline-job')
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
      'projects/madhav-astrology/locations/asia-south1/jobs/marsys-build-pipeline-job',
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
            'projects/madhav-astrology/locations/asia-south1/jobs/marsys-build-pipeline-job/executions/exec-xyz',
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
      '--ayanamsha-role', 'jh_true_chitra',
      '--triggered-by', 'manual:uid-1',
    ])
    expect(seen.envOverrides?.MARSYS_BUILD_ID).toBe('build-1')
    expect(seen.envOverrides?.MARSYS_BUILD_CHART_ID).toBe('chart-abc')
    expect(seen.envOverrides?.MARSYS_BUILD_AYANAMSHA_ROLE).toBe('jh_true_chitra')
  })
})
