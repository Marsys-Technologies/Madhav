/**
 * Terminal earned-signal gate for the deploy workflow.
 *
 * GitHub can report success after a skipped prerequisite causes dependent
 * jobs to skip. After the deploy workflow admits a run, routine migration
 * and Web deployment are required. The deployed-revision diff and force-all
 * flag select the additional components that must succeed.
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
    if (input.eventName !== 'workflow_run' && input.eventName !== 'workflow_dispatch') {
      throw new Error(`unsupported deployment event ${JSON.stringify(input.eventName)}`)
    }
    if (input.changesResult !== 'success') {
      throw new Error(`change detector did not succeed (result=${input.changesResult})`)
    }

    const forceAll = parseFlag('force_all', input.forceAll)
    parseFlag('web', input.changed.web)
    const changed = {
      sidecar: parseFlag('sidecar', input.changed.sidecar),
      mcp: parseFlag('mcp', input.changed.mcp),
      pipeline: parseFlag('pipeline', input.changed.pipeline),
    }

    const required = new Map<string, JobResult>([
      ['migrate', input.results.migrate],
      ['deploy-web', input.results.web],
    ])
    if (forceAll || changed.sidecar) required.set('deploy-sidecar', input.results.sidecar)
    if (forceAll || changed.mcp) required.set('deploy-mcp', input.results.mcp)
    if (forceAll || changed.pipeline) required.set('deploy-pipeline-job', input.results.pipeline)

    const requiredFailures = [...required]
      .filter(([, result]) => result !== 'success')
      .map(([name, result]) => `${name}=${result || '(missing)'}`)

    if (requiredFailures.length > 0) {
      return {
        allowed: false,
        mode: 'blocked-mutation-skipped',
        requiredFailures,
        reason:
          `Required deployment jobs did not succeed for ${input.sha}: ` +
          requiredFailures.join(', ') +
          '. Workflow success would be an unearned deployment signal.',
      }
    }

    return {
      allowed: true,
      mode: 'earned-deployment',
      requiredFailures: [],
      reason: `Routine migration, Web deployment, and every selected component succeeded for ${input.sha}.`,
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

/**
 * Reports only what the current workflow can establish. A path match or a
 * missing deployed source can request a conservative rebuild. A path miss
 * carries no proof of effective image inputs or runtime configuration.
 */
export function observeWebReconciliation(input: DeploymentOutcomeInput) {
  const observed = input.results.web
  const actualWebJobResult = observed === 'success' || observed === 'failure' ||
    observed === 'cancelled' || observed === 'skipped' ? observed : 'unknown'
  const evidence = { comparison: 'unknown', actualWebJobResult } as const

  if (input.eventName !== 'workflow_run' && input.eventName !== 'workflow_dispatch') {
    return { ...evidence, requested: 'unknown', reason: 'not-a-deploy-event' } as const
  }
  if (input.changesResult !== 'success') {
    return { ...evidence, requested: 'unknown', reason: 'change-detection-unavailable' } as const
  }
  const { web, sidecar, mcp, pipeline } = input.changed
  const flags = [input.forceAll, web, sidecar, mcp, pipeline]
  if (flags.some((flag) => flag !== 'true' && flag !== 'false')) {
    return { ...evidence, requested: 'unknown', reason: 'invalid-change-signal' } as const
  }
  if (input.forceAll === 'true') {
    return { ...evidence, requested: 'rebuild', reason: 'force-all' } as const
  }
  if (input.eventName === 'workflow_dispatch') {
    return { ...evidence, requested: 'rebuild', reason: 'manual-dispatch' } as const
  }
  if (web === 'true') {
    return { ...evidence, requested: 'rebuild', reason: 'web-selected' } as const
  }
  if (mcp === 'true') {
    return { ...evidence, requested: 'rebuild', reason: 'mcp-needs-matching-web' } as const
  }
  return { ...evidence, requested: 'unknown', reason: 'comparison-unavailable' } as const
}

function main(): void {
  const input: DeploymentOutcomeInput = {
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
  }
  const result = evaluateDeploymentOutcome(input)

  if (process.env.OUTCOME_WEB_SHADOW === 'true') {
    const observation = observeWebReconciliation(input)
    console.log(`[web-reconciliation-shadow] ${JSON.stringify(observation)}`)
  }

  const annotation = result.reason.replace(/\n/g, '%0A')
  if (!result.allowed) {
    console.error(`::error title=Deployment outcome not earned (${result.mode})::${annotation}`)
    console.error(result.reason)
    process.exit(1)
  }
  console.log(`[deployment-outcome] ${result.mode}: ${result.reason}`)
}

if (process.env.NODE_ENV !== 'test') main()
