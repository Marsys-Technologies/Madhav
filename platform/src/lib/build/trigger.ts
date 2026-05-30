/**
 * Platform Modernization — unit 4.build_trigger (Stream B).
 *
 * Server-side library: enqueue a Cloud Task that posts to /api/build/task,
 * and persist a `build_events:enqueued` row so the cockpit can show
 * "queued" before the Job even starts.
 *
 * Pure server-only — keep transport (Cloud Tasks client) injectable so
 * unit tests can run without GCP creds.
 */

import 'server-only'
import { randomUUID } from 'node:crypto'
import { query } from '@/lib/db/client'

// Literal-string import so webpack can resolve @google-cloud/tasks as an
// external package (listed in serverExternalPackages in next.config.ts).
// The _name parameter is kept for call-site compatibility.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
async function loadGcpModule(_name: string): Promise<unknown> {
  return import('@google-cloud/tasks')
}

export type AyanamshaRole = 'jh_true_chitra' | 'kp'

export interface BuildRequest {
  chartId: string
  ayanamshaRole: AyanamshaRole
  triggeredBy: string // 'manual:<uid>' | 'cron:<id>'
}

export interface TaskTransport {
  /** Creates a Cloud Task. Resolves to the task name. */
  createTask(args: {
    parent: string
    task: {
      httpRequest: {
        httpMethod: 'POST'
        url: string
        headers: Record<string, string>
        body: string // base64-encoded JSON
        oidcToken: { serviceAccountEmail: string; audience: string }
      }
    }
  }): Promise<{ name: string }>
}

export interface BuildTriggerEnv {
  gcpProject: string
  queueLocation: string
  queueId: string
  invokerSaEmail: string
  taskAudience: string // also the URL prefix for /api/build/task
}

export interface BuildTriggerResult {
  buildId: string
  taskName: string
}

/**
 * Read env once; throw a structured error if any required var is missing.
 * The /api/build/start route catches this and surfaces 503.
 */
export function readBuildTriggerEnv(env: NodeJS.ProcessEnv = process.env): BuildTriggerEnv {
  const missing: string[] = []
  const get = (k: string): string => {
    const v = env[k]
    if (!v) missing.push(k)
    return v ?? ''
  }
  const out: BuildTriggerEnv = {
    gcpProject: get('GCP_PROJECT'),
    queueLocation: get('BUILD_TASK_QUEUE_LOCATION'),
    queueId: get('BUILD_TASK_QUEUE'),
    invokerSaEmail: get('BUILD_TASK_INVOKER_SA'),
    taskAudience: get('BUILD_TASK_AUDIENCE'),
  }
  if (missing.length > 0) {
    throw new Error(
      `[build/trigger] missing env vars: ${missing.join(', ')}. ` +
        'Apply infra/cloud_tasks then redeploy amjis-web.',
    )
  }
  return out
}

/** Lazy-loaded default transport — only imported when running in production. */
async function defaultTransport(): Promise<TaskTransport> {
  // String-variable indirection keeps the Vite/Vitest static analyzer from
  // trying to resolve the GCP SDK at test time; the package is only present
  // in the production build.
  const mod = await loadGcpModule('@google-cloud/tasks')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const client = new (mod as any).CloudTasksClient()
  return {
    async createTask({ parent, task }) {
      const [resp] = await client.createTask({ parent, task })
      return { name: resp.name ?? '' }
    },
  }
}

/** Build the Cloud Tasks queue path. */
export function queuePath(env: BuildTriggerEnv): string {
  return `projects/${env.gcpProject}/locations/${env.queueLocation}/queues/${env.queueId}`
}

/** Idempotency / observability: log the enqueue as the first build_events row. */
async function persistEnqueuedRow(args: {
  buildId: string
  chartId: string
  ayanamshaRole: AyanamshaRole
  triggeredBy: string
  taskName: string
}): Promise<void> {
  await query(
    `INSERT INTO build_events
       (build_id, stage_seq, chart_id, ayanamsha_role, asset, stage, status, message, metadata)
     VALUES ($1, 0, $2, $3, 'orchestrator', 'enqueue', 'started', $4, $5::jsonb)
     ON CONFLICT (build_id, stage_seq) DO NOTHING`,
    [
      args.buildId,
      args.chartId,
      args.ayanamshaRole,
      `Build enqueued by ${args.triggeredBy}`,
      JSON.stringify({ task_name: args.taskName, triggered_by: args.triggeredBy }),
    ],
  )
}

export async function enqueueBuild(
  req: BuildRequest,
  opts: {
    env?: BuildTriggerEnv
    transport?: TaskTransport
    buildId?: string
    now?: () => Date
  } = {},
): Promise<BuildTriggerResult> {
  const env = opts.env ?? readBuildTriggerEnv()
  const transport = opts.transport ?? (await defaultTransport())
  const buildId = opts.buildId ?? `build-${randomUUID()}`

  const payload = {
    build_id: buildId,
    chart_id: req.chartId,
    ayanamsha_role: req.ayanamshaRole,
    triggered_by: req.triggeredBy,
  }

  const url = `${env.taskAudience.replace(/\/$/, '')}/api/build/task`
  const body = Buffer.from(JSON.stringify(payload), 'utf8').toString('base64')

  const { name } = await transport.createTask({
    parent: queuePath(env),
    task: {
      httpRequest: {
        httpMethod: 'POST',
        url,
        headers: { 'Content-Type': 'application/json' },
        body,
        oidcToken: {
          serviceAccountEmail: env.invokerSaEmail,
          audience: env.taskAudience,
        },
      },
    },
  })

  await persistEnqueuedRow({
    buildId,
    chartId: req.chartId,
    ayanamshaRole: req.ayanamshaRole,
    triggeredBy: req.triggeredBy,
    taskName: name,
  })

  return { buildId, taskName: name }
}
