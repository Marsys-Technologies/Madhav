import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import YAML from 'js-yaml'

import {
  evaluateDeploymentOutcome,
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

  it('requires a changed sidecar to deploy even though sidecar does not use the migration barrier', () => {
    const result = evaluateDeploymentOutcome(input({
      changed: { web: 'false', sidecar: 'true', mcp: 'false', pipeline: 'false' },
    }))
    expect(result.allowed).toBe(false)
    expect(result.requiredFailures).toEqual(['deploy-sidecar=skipped'])
  })

  it('does not manufacture a deployment requirement for a docs-only run', () => {
    const result = evaluateDeploymentOutcome(input())
    expect(result.allowed).toBe(true)
    expect(result.mode).toBe('no-deployable-change')
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

  it('runs an always-evaluated terminal signal across every mutation job', () => {
    const signal = workflow.jobs['deployment-outcome']
    expect(signal).toBeDefined()
    expect(signal.if).toContain('always()')
    expect(signal.if).toContain("github.event_name != 'pull_request'")
    expect(signal.needs).toEqual(expect.arrayContaining([
      'changes', 'migrate', 'deploy-web', 'deploy-sidecar', 'deploy-mcp', 'deploy-pipeline-job',
    ]))
    expect(signal.steps?.some((step) => (step.run ?? '').includes('ci/deployment_outcome_gate.ts'))).toBe(true)
  })
})
