import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import YAML from 'js-yaml'

import {
  evaluateDeploymentOutcome,
  observeWebReconciliation,
  type DeploymentOutcomeInput,
} from '../ci/deployment_outcome_gate'

function input(overrides: Partial<DeploymentOutcomeInput> = {}): DeploymentOutcomeInput {
  return {
    eventName: 'workflow_run',
    sha: '4adcf04978757d2f8e8157492f1922f8b5fb92e3',
    changesResult: 'success',
    forceAll: 'false',
    changed: { web: 'false', sidecar: 'false', mcp: 'false', pipeline: 'false' },
    results: {
      migrate: 'skipped',
      web: 'skipped',
      sidecar: 'skipped',
      mcp: 'skipped',
      pipeline: 'skipped',
    },
    ...overrides,
  }
}

describe('evaluateDeploymentOutcome — earned deployment signal', () => {
  it('CAN-FAIL: observed deployable-source changes with skipped mutation jobs are blocking', () => {
    const result = evaluateDeploymentOutcome(input({
      changed: { web: 'true', sidecar: 'false', mcp: 'true', pipeline: 'true' },
    }))
    expect(result.allowed).toBe(false)
    expect(result.mode).toBe('blocked-mutation-skipped')
    expect(result.requiredFailures).toEqual([
      'migrate=skipped',
      'deploy-web=skipped',
      'deploy-mcp=skipped',
      'deploy-pipeline-job=skipped',
    ])
  })

  it('passes only when every mutation required by changed deployable source succeeded', () => {
    const result = evaluateDeploymentOutcome(input({
      changed: { web: 'true', sidecar: 'false', mcp: 'true', pipeline: 'false' },
      results: {
        migrate: 'success', web: 'success', sidecar: 'skipped', mcp: 'success', pipeline: 'skipped',
      },
    }))
    expect(result.allowed).toBe(true)
    expect(result.mode).toBe('earned-deployment')
    expect(result.requiredFailures).toEqual([])
  })

  it.each([
    ['sidecar', 'deploy-sidecar'],
    ['mcp', 'deploy-mcp'],
    ['pipeline', 'deploy-pipeline-job'],
  ] as const)('requires a selected %s alongside the routine jobs', (component, job) => {
    const baseline = input()
    const result = evaluateDeploymentOutcome(input({
      changed: { ...baseline.changed, [component]: 'true' },
      results: { ...baseline.results, migrate: 'success', web: 'success' },
    }))
    expect(result.allowed).toBe(false)
    expect(result.requiredFailures).toEqual([`${job}=skipped`])
  })

  it.each(['workflow_run', 'workflow_dispatch'])('requires migration and Web for %s even with all flags false', eventName => {
    const missing = evaluateDeploymentOutcome(input({ eventName }))
    expect(missing.allowed).toBe(false)
    expect(missing.mode).toBe('blocked-mutation-skipped')
    expect(missing.requiredFailures).toEqual(['migrate=skipped', 'deploy-web=skipped'])

    const baseline = input()
    const earned = evaluateDeploymentOutcome(input({
      eventName,
      results: { ...baseline.results, migrate: 'success', web: 'success' },
    }))
    expect(earned.allowed).toBe(true)
    expect(earned.mode).toBe('earned-deployment')
    expect(earned.requiredFailures).toEqual([])
  })

  it.each(['failure', 'cancelled', 'skipped', ''])('requires explicit success for routine job result %j', result => {
    const baseline = input()
    for (const [field, job] of [['migrate', 'migrate'], ['web', 'deploy-web']] as const) {
      const outcome = evaluateDeploymentOutcome(input({
        results: { ...baseline.results, migrate: 'success', web: 'success', [field]: result },
      }))
      expect(outcome.allowed).toBe(false)
      expect(outcome.requiredFailures).toEqual([`${job}=${result || '(missing)'}`])
    }
  })

  it('requires every service on an admitted force-all dispatch', () => {
    const baseline = input()
    const result = evaluateDeploymentOutcome(input({
      eventName: 'workflow_dispatch',
      forceAll: 'true',
      results: { ...baseline.results, migrate: 'success', web: 'success' },
    }))
    expect(result.allowed).toBe(false)
    expect(result.requiredFailures).toEqual([
      'deploy-sidecar=skipped', 'deploy-mcp=skipped', 'deploy-pipeline-job=skipped',
    ])
  })

  it.each(['failure', 'cancelled', 'skipped', ''])('refuses unavailable changes evidence %j', changesResult => {
    const result = evaluateDeploymentOutcome(input({ changesResult }))
    expect(result.allowed).toBe(false)
    expect(result.mode).toBe('blocked-invalid-signal')
  })

  it('rejects an event outside the configured deploy workflow', () => {
    const result = evaluateDeploymentOutcome(input({ eventName: 'push' }))
    expect(result.allowed).toBe(false)
    expect(result.mode).toBe('blocked-invalid-signal')
  })

  it('fails closed when a change output is absent or malformed', () => {
    for (const malformed of ['', 'TRUE', 'unknown']) {
      const result = evaluateDeploymentOutcome(input({
        changed: { web: malformed, sidecar: 'false', mcp: 'false', pipeline: 'false' },
      }))
      expect(result.allowed, malformed).toBe(false)
      expect(result.mode).toBe('blocked-invalid-signal')
    }
  })

  it('does not turn the pull-request build-only event into a deployment assertion', () => {
    const result = evaluateDeploymentOutcome(input({ eventName: 'pull_request' }))
    expect(result.allowed).toBe(true)
    expect(result.mode).toBe('not-a-deploy-event')
  })
})

describe('observeWebReconciliation', () => {
  it('keeps an unchanged path signal unknown even when the actual Web job succeeded', () => {
    const actual = { ...input().results, migrate: 'success', web: 'success' }
    expect(observeWebReconciliation(input({ results: actual }))).toEqual({
      comparison: 'unknown', requested: 'unknown', reason: 'comparison-unavailable', actualWebJobResult: 'success',
    })
  })

  it.each([
    [{ changed: { ...input().changed, web: 'true' } }, 'web-selected'],
    [{ changed: { ...input().changed, mcp: 'true' } }, 'mcp-needs-matching-web'],
    [{ eventName: 'workflow_dispatch' }, 'manual-dispatch'],
    [{ eventName: 'workflow_dispatch', forceAll: 'true' }, 'force-all'],
  ] satisfies [Partial<DeploymentOutcomeInput>, string][])('records rebuild demand without claiming completion', (overrides, reason) => {
    expect(observeWebReconciliation(input(overrides))).toEqual({
      comparison: 'unknown', requested: 'rebuild', reason, actualWebJobResult: 'skipped',
    })
  })

  it.each(['failure', 'cancelled', 'skipped', ''])('cannot qualify a comparison when changes is %s', changesResult => {
    expect(observeWebReconciliation(input({ changesResult }))).toEqual({
      comparison: 'unknown', requested: 'unknown', reason: 'change-detection-unavailable', actualWebJobResult: 'skipped',
    })
  })

  it('drops malformed signals and does not echo unexpected job metadata', () => {
    expect(observeWebReconciliation(input({
      changed: { ...input().changed, web: 'TRUE' },
      results: { ...input().results, web: 'unexpected result' },
    }))).toEqual({
      comparison: 'unknown', requested: 'unknown', reason: 'invalid-change-signal', actualWebJobResult: 'unknown',
    })
  })

  it('makes no deployment assertion for another event', () => {
    expect(observeWebReconciliation(input({ eventName: 'pull_request' }))).toEqual({
      comparison: 'unknown', requested: 'unknown', reason: 'not-a-deploy-event', actualWebJobResult: 'skipped',
    })
  })
})

describe('deploy.yml earned-signal wiring', () => {
  const workflow = YAML.load(
    fs.readFileSync(path.resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8'),
  ) as {
    jobs: Record<string, {
      needs?: string[]
      if?: string
      outputs?: Record<string, unknown>
      steps?: Array<{ run?: string }>
    }>
  }

  it('publishes a web change signal derived from the deployed web revision', () => {
    expect(Object.keys(workflow.jobs.changes.outputs ?? {})).toContain('web')
    const detect = workflow.jobs.changes.steps?.find((step) => (step.run ?? '').includes('deployed_sha'))
    expect(detect?.run).toContain("web=$(decide web")
  })

  it('admits routine migration and Web through prerequisites independently of source flags', () => {
    const migrate = workflow.jobs.migrate
    const web = workflow.jobs['deploy-web']
    expect(migrate.if).toContain("needs.changes.result == 'success'")
    expect(migrate.if).not.toContain('needs.changes.outputs.')
    expect(web.needs).toEqual(['changes', 'migrate'])
    expect(web.if).toContain("needs.changes.result == 'success'")
    expect(web.if).toContain("needs.migrate.result == 'success'")
    expect(web.if).not.toContain('needs.changes.outputs.')
  })

  it('runs an always-evaluated terminal signal across every mutation job', () => {
    const signal = workflow.jobs['deployment-outcome']
    expect(signal).toBeDefined()
    expect(signal.if).toContain('always()')
    expect(signal.if).toContain("github.event_name != 'pull_request'")
    // A cancelled/superseded upstream skips `changes`; that is SKIPPED, not an unearned deploy.
    expect(signal.if).toContain("needs.changes.result != 'skipped'")
    expect(signal.needs).toEqual(expect.arrayContaining([
      'changes', 'migrate', 'deploy-web', 'deploy-sidecar', 'deploy-mcp', 'deploy-pipeline-job',
    ]))
    expect(signal.steps?.some((step) => (step.run ?? '').includes('ci/deployment_outcome_gate.ts'))).toBe(true)
  })
})
