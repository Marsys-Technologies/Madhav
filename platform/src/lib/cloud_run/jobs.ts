import { ExecutionsClient, JobsClient } from '@google-cloud/run'

const REGION = 'asia-south1'
const PROJECT = process.env.GCP_PROJECT ?? 'madhav-astrology'
// Single source of truth: BUILD_JOB_NAME (set in deploy.yml). Falls back to the
// real deployed job name, NOT the legacy `marsys-build-pipeline-job` which does
// not exist (Orchestrator Convergence Phase 1, 2026-06-12).
const JOB = process.env.BUILD_JOB_NAME ?? 'brahma-build-pipeline-job'

let _execClient: ExecutionsClient | null = null
function client() {
  if (!_execClient) _execClient = new ExecutionsClient()
  return _execClient
}

let _jobsClient: JobsClient | null = null
function jobsClient() {
  if (!_jobsClient) _jobsClient = new JobsClient()
  return _jobsClient
}

/**
 * Returns the image tag currently deployed on the Cloud Run Job, e.g.
 * "gcr.io/project/brahma-build-pipeline-job:abc1234". Used to surface
 * stale-image risk before a build is started.
 * Returns null if the API is unreachable or the job doesn't exist.
 */
export async function getJobImageTag(): Promise<string | null> {
  try {
    const name = `projects/${PROJECT}/locations/${REGION}/jobs/${JOB}`
    const [job] = await jobsClient().getJob({ name })
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const image = (job?.template as any)?.containers?.[0]?.image ?? null
    return (image as string | null)
  } catch {
    return null
  }
}

/**
 * Returns the set of build_ids whose Cloud Run executions are currently Running.
 * Excluded from reaping to avoid cancelling jobs that are actively working.
 *
 * Relies on the dispatcher having labeled each execution with `build-id=<uuid>`.
 * If Cloud Run API is unreachable, returns empty set — over-reaping is safer
 * than under-reaping; next 15-min cycle will correct any missed rows.
 */
export async function listLiveBuildExecutions(): Promise<Set<string>> {
  const parent = `projects/${PROJECT}/locations/${REGION}/jobs/${JOB}`
  const liveIds = new Set<string>()
  try {
    const [executions] = await client().listExecutions({ parent })
    for (const exec of executions) {
      if (exec.completionTime) continue  // completed — not live
      const buildId = exec.labels?.['build-id']
      if (buildId) liveIds.add(buildId)
    }
  } catch (err) {
    console.error('[listLiveBuildExecutions] Cloud Run API failed:', err)
  }
  return liveIds
}
