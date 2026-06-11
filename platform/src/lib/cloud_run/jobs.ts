import { ExecutionsClient } from '@google-cloud/run'

const REGION = 'asia-south1'
const PROJECT = process.env.GCP_PROJECT ?? 'madhav-astrology'
// Single source of truth: BUILD_JOB_NAME (set in deploy.yml). Falls back to the
// real deployed job name, NOT the legacy `marsys-build-pipeline-job` which does
// not exist (Orchestrator Convergence Phase 1, 2026-06-12).
const JOB = process.env.BUILD_JOB_NAME ?? 'brahma-build-pipeline-job'

let _client: ExecutionsClient | null = null
function client() {
  if (!_client) _client = new ExecutionsClient()
  return _client
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
