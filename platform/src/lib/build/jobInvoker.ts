/**
 * Cloud Run Jobs invoker for `brahma-build-pipeline-job`.
 *
 * Server-side library used by /api/build/task. The Cloud Run Jobs API
 * accepts an `RunJobRequest` with `Overrides.ContainerOverrides[].args` so we
 * can pass `--chart-id` and `--ayanamsha-role` per invocation.
 *
 * Lazy-loads @google-cloud/run so vitest doesn't need GCP creds. Tests pass
 * an injected transport.
 */

import 'server-only'

// Literal-string import so webpack can resolve @google-cloud/run as an
// external package (listed in serverExternalPackages in next.config.ts).
// The _name parameter is kept for call-site compatibility.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
async function loadGcpModule(_name: string): Promise<unknown> {
  return import('@google-cloud/run')
}

export interface JobInvocationArgs {
  buildId: string
  chartId: string
  ayanamshaRole: 'jh_true_chitra' | 'kp'
  triggeredBy: string
}

export interface JobInvocationResult {
  /** Cloud Run Job execution full name (projects/.../executions/...) */
  executionName: string
}

export interface JobTransport {
  runJob(args: {
    jobName: string
    containerArgs: string[]
    envOverrides: Record<string, string>
  }): Promise<JobInvocationResult>
}

export interface JobInvokerEnv {
  gcpProject: string
  jobLocation: string
  jobId: string
}

export function readJobInvokerEnv(env: NodeJS.ProcessEnv = process.env): JobInvokerEnv {
  // Safety guard: when BUILD_EXECUTOR=local, the operator explicitly declared that
  // this environment should NOT dispatch to Cloud Run. Throw early so the runs API
  // can catch and return a 503 rather than silently dispatching a real GCP job from
  // a local dev server connected to the production database.
  if (env.BUILD_EXECUTOR === 'local') {
    throw new Error(
      '[build/jobInvoker] BUILD_EXECUTOR=local — Cloud Run dispatch is disabled in this environment. ' +
      'Run the orchestrator manually: python -m pipeline.orchestrator.main --run-id <run_id>'
    )
  }

  const missing: string[] = []
  const get = (k: string, fallback?: string): string => {
    const v = env[k]
    if (!v && !fallback) missing.push(k)
    return v ?? fallback ?? ''
  }
  const out: JobInvokerEnv = {
    gcpProject: get('GCP_PROJECT'),
    jobLocation: get('BUILD_JOB_LOCATION', env.GCP_REGION ?? 'asia-south1'),
    jobId: get('BUILD_JOB_NAME', 'brahma-build-pipeline-job'),
  }
  if (missing.length > 0) {
    throw new Error(`[build/jobInvoker] missing env vars: ${missing.join(', ')}`)
  }
  return out
}

async function defaultTransport(): Promise<JobTransport> {
  const mod = await loadGcpModule('@google-cloud/run')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const client = new (mod as any).JobsClient()
  return {
    async runJob({ jobName, containerArgs, envOverrides }) {
      const [op] = await client.runJob({
        name: jobName,
        overrides: {
          containerOverrides: [
            {
              args: containerArgs,
              env: Object.entries(envOverrides).map(([name, value]) => ({ name, value })),
            },
          ],
        },
      })
      const execName: string =
        // op is a LRO; `.name` is the execution resource id once the LRO is created.
        (op?.name as string | undefined) ?? (op?.latestResponse?.name as string | undefined) ?? ''
      return { executionName: execName }
    },
  }
}

export function jobPath(env: JobInvokerEnv): string {
  return `projects/${env.gcpProject}/locations/${env.jobLocation}/jobs/${env.jobId}`
}

export async function invokeBuildJob(
  args: JobInvocationArgs,
  opts: { env?: JobInvokerEnv; transport?: JobTransport } = {},
): Promise<JobInvocationResult> {
  const env = opts.env ?? readJobInvokerEnv()
  const transport = opts.transport ?? (await defaultTransport())
  return transport.runJob({
    jobName: jobPath(env),
    containerArgs: [
      '--build-id', args.buildId,
      '--chart-id', args.chartId,
    ],
    envOverrides: {
      MARSYS_BUILD_ID: args.buildId,
      MARSYS_BUILD_CHART_ID: args.chartId,
      MARSYS_BUILD_AYANAMSHA_ROLE: args.ayanamshaRole,
    },
  })
}

/** New orchestrator: invoke with --run-id only. */
export async function invokeRunJob(
  runId: string,
  opts: { env?: JobInvokerEnv; transport?: JobTransport } = {},
): Promise<JobInvocationResult> {
  const env = opts.env ?? readJobInvokerEnv()
  const transport = opts.transport ?? (await defaultTransport())
  return transport.runJob({
    jobName: jobPath(env),
    containerArgs: ['--run-id', runId],
    envOverrides: { MARSYS_RUN_ID: runId },
  })
}
