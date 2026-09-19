/**
 * Terminal earned-signal gate for the deploy workflow.
 *
 * A GitHub Actions workflow can conclude `success` when a prerequisite job is
 * skipped and every downstream mutation job is consequently skipped. That is
 * correct Actions mechanics but an invalid deployment signal when deployable
 * source changed. This detector runs with `always()` after every mutation job
 * and requires each mutation implied by the deployed-revision diff to have
 * actually succeeded.
 */

export type JobResult = 'success' | 'failure' | 'cancelled' | 'skipped' | string

export interface DeploymentOutcomeInput {
  eventName: string
  sha: string
  changesResult: JobResult
  forceAll: string
  changed: {
    web: string
    sidecar: string
    mcp: string
    pipeline: string
  }
  results: {
    migrate: JobResult
    web: JobResult
    sidecar: JobResult
    mcp: JobResult
    pipeline: JobResult
  }
}

export type DeploymentOutcomeMode =
  | 'not-a-deploy-event'
  | 'no-deployable-change'
  | 'earned-deployment'
  | 'blocked-invalid-signal'
  | 'blocked-mutation-skipped'

export interface DeploymentOutcomeResult {
  allowed: boolean
  mode: DeploymentOutcomeMode
  requiredFailures: string[]
  reason: string
}

function parseFlag(name: string, value: string): boolean {
  if (value === 'true') return true
  if (value === 'false') return false
  throw new Error(`${name} must be exactly true or false; observed ${JSON.stringify(value)}`)
}

export function evaluateDeploymentOutcome(input: DeploymentOutcomeInput): DeploymentOutcomeResult {
  if (input.eventName === 'pull_request') {
    return {
      allowed: true,
      mode: 'not-a-deploy-event',
      requiredFailures: [],
      reason: 'pull_request is build-only and makes no production deployment assertion.',
    }
  }

  try {
    if (input.changesResult !== 'success') {
      throw new Error(`change detector did not succeed (result=${input.changesResult})`)
    }

    const forceAll = parseFlag('force_all', input.forceAll)
    const changed = {
      web: parseFlag('web', input.changed.web),
      sidecar: parseFlag('sidecar', input.changed.sidecar),
      mcp: parseFlag('mcp', input.changed.mcp),
      pipeline: parseFlag('pipeline', input.changed.pipeline),
    }

    const required = new Map<string, JobResult>()
    if (forceAll || changed.web) {
      required.set('migrate', input.results.migrate)
      required.set('deploy-web', input.results.web)
    }
    if (forceAll || changed.sidecar) required.set('deploy-sidecar', input.results.sidecar)
    if (forceAll || changed.mcp) {
      required.set('migrate', input.results.migrate)
      required.set('deploy-mcp', input.results.mcp)
    }
    if (forceAll || changed.pipeline) {
      required.set('migrate', input.results.migrate)
      required.set('deploy-pipeline-job', input.results.pipeline)
    }

    if (required.size === 0) {
      return {
        allowed: true,
        mode: 'no-deployable-change',
        requiredFailures: [],
        reason: `No deployable source differs from production for ${input.sha}; no mutation signal is claimed.`,
      }
    }

    const requiredFailures = [...required]
      .filter(([, result]) => result !== 'success')
      .map(([name, result]) => `${name}=${result || '(missing)'}`)

    if (requiredFailures.length > 0) {
      return {
        allowed: false,
        mode: 'blocked-mutation-skipped',
        requiredFailures,
        reason:
          `Deployable source changed for ${input.sha}, but required mutation jobs did not succeed: ` +
          requiredFailures.join(', ') +
          '. Workflow success would be an unearned deployment signal.',
      }
    }

    return {
      allowed: true,
      mode: 'earned-deployment',
      requiredFailures: [],
      reason: `Every mutation required by the deployed-revision diff succeeded for ${input.sha}.`,
    }
  } catch (error) {
    return {
      allowed: false,
      mode: 'blocked-invalid-signal',
      requiredFailures: [],
      reason: error instanceof Error ? error.message : String(error),
    }
  }
}

function main(): void {
  const result = evaluateDeploymentOutcome({
    eventName: process.env.OUTCOME_EVENT_NAME ?? '',
    sha: process.env.OUTCOME_SHA ?? '(unknown sha)',
    changesResult: process.env.OUTCOME_CHANGES_RESULT ?? '',
    forceAll: process.env.OUTCOME_FORCE_ALL ?? '',
    changed: {
      web: process.env.OUTCOME_WEB_CHANGED ?? '',
      sidecar: process.env.OUTCOME_SIDECAR_CHANGED ?? '',
      mcp: process.env.OUTCOME_MCP_CHANGED ?? '',
      pipeline: process.env.OUTCOME_PIPELINE_CHANGED ?? '',
    },
    results: {
      migrate: process.env.OUTCOME_MIGRATE_RESULT ?? '',
      web: process.env.OUTCOME_WEB_RESULT ?? '',
      sidecar: process.env.OUTCOME_SIDECAR_RESULT ?? '',
      mcp: process.env.OUTCOME_MCP_RESULT ?? '',
      pipeline: process.env.OUTCOME_PIPELINE_RESULT ?? '',
    },
  })

  const annotation = result.reason.replace(/\n/g, '%0A')
  if (!result.allowed) {
    console.error(`::error title=Deployment outcome not earned (${result.mode})::${annotation}`)
    console.error(result.reason)
    process.exit(1)
  }
  console.log(`[deployment-outcome] ${result.mode}: ${result.reason}`)
}

if (process.env.NODE_ENV !== 'test') main()
