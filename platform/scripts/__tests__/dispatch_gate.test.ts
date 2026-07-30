import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import YAML from 'js-yaml'

import {
  evaluateDispatchGate,
  EMERGENCY_OVERRIDE_TOKEN,
  REQUIRE_CI_GREEN,
  MIN_EMERGENCY_REASON_LENGTH,
  type DispatchGateInput,
} from '../ci/dispatch_gate'

function input(overrides: Partial<DispatchGateInput> = {}): DispatchGateInput {
  return {
    eventName: 'workflow_dispatch',
    ciGate: REQUIRE_CI_GREEN,
    emergencyReason: '',
    ciConclusion: 'success',
    sha: 'deadbeefdeadbeefdeadbeefdeadbeefdeadbeef',
    ...overrides,
  }
}

const GOOD_REASON = 'prod is down, CI runner outage, deploying the revert by hand'

describe('evaluateDispatchGate — the workflow_dispatch CI-gate bypass', () => {
  // ── The bypass itself: this is the case that used to sail straight through ──────────────────

  it('CAN-FAIL: a manual dispatch fired BEFORE CI completes is BLOCKED (the observed 3x pattern)', () => {
    const r = evaluateDispatchGate(input({ ciConclusion: 'none' }))
    expect(r.allowed).toBe(false)
    expect(r.mode).toBe('blocked-ci-not-green')
    expect(r.reason).toContain('has NOT completed')
  })

  it('CAN-FAIL: a manual dispatch on a SHA whose CI FAILED is BLOCKED', () => {
    const r = evaluateDispatchGate(input({ ciConclusion: 'failure' }))
    expect(r.allowed).toBe(false)
    expect(r.mode).toBe('blocked-ci-not-green')
    expect(r.reason).toContain('failure')
  })

  it('blocks a cancelled or timed-out CI run too', () => {
    for (const conclusion of ['cancelled', 'timed_out', 'action_required', 'skipped', 'neutral']) {
      expect(evaluateDispatchGate(input({ ciConclusion: conclusion })).allowed).toBe(false)
    }
  })

  // ── Emergency capability is preserved — that was RULING 73-CLOSE's stated objection ─────────

  it('allows an emergency override when the operator selects the token AND states a reason', () => {
    const r = evaluateDispatchGate(
      input({ ciConclusion: 'failure', ciGate: EMERGENCY_OVERRIDE_TOKEN, emergencyReason: GOOD_REASON })
    )
    expect(r.allowed).toBe(true)
    expect(r.mode).toBe('emergency-override')
    expect(r.reason).toContain(GOOD_REASON)
  })

  it('the override token alone is NOT enough — a substantive reason is required', () => {
    const r = evaluateDispatchGate(
      input({ ciConclusion: 'failure', ciGate: EMERGENCY_OVERRIDE_TOKEN, emergencyReason: 'x' })
    )
    expect(r.allowed).toBe(false)
    expect(r.mode).toBe('blocked-missing-reason')
  })

  it('whitespace does not count as a reason', () => {
    const r = evaluateDispatchGate(
      input({
        ciGate: EMERGENCY_OVERRIDE_TOKEN,
        ciConclusion: 'failure',
        emergencyReason: ' '.repeat(MIN_EMERGENCY_REASON_LENGTH + 10),
      })
    )
    expect(r.allowed).toBe(false)
    expect(r.mode).toBe('blocked-missing-reason')
  })

  // ── Fail-safe defaults ─────────────────────────────────────────────────────────────────────

  it('an unrecognised ci_gate value is treated as require-ci-green (fail safe, not fail open)', () => {
    const r = evaluateDispatchGate(input({ ciGate: 'yolo', ciConclusion: 'failure' }))
    expect(r.allowed).toBe(false)
    expect(r.mode).toBe('blocked-ci-not-green')
  })

  it('a near-miss of the override token does not override', () => {
    for (const near of [
      EMERGENCY_OVERRIDE_TOKEN.toLowerCase(),
      `${EMERGENCY_OVERRIDE_TOKEN} `,
      'EMERGENCY-OVERRIDE',
    ]) {
      const r = evaluateDispatchGate(
        input({ ciGate: near, ciConclusion: 'failure', emergencyReason: GOOD_REASON })
      )
      expect(r.allowed).toBe(false)
    }
  })

  // ── The unaffected paths ───────────────────────────────────────────────────────────────────

  it('a manual dispatch on a green SHA proceeds normally — emergency capability is not the common path', () => {
    const r = evaluateDispatchGate(input({ ciConclusion: 'success' }))
    expect(r.allowed).toBe(true)
    expect(r.mode).toBe('ci-green')
  })

  it('a normal workflow_run-triggered deploy is UNAFFECTED, whatever the inputs look like', () => {
    for (const conclusion of ['success', 'failure', 'none']) {
      const r = evaluateDispatchGate(input({ eventName: 'workflow_run', ciConclusion: conclusion }))
      expect(r.allowed).toBe(true)
      expect(r.mode).toBe('not-a-dispatch')
    }
  })

  it('a pull_request build-check run is UNAFFECTED', () => {
    const r = evaluateDispatchGate(input({ eventName: 'pull_request', ciConclusion: 'none' }))
    expect(r.allowed).toBe(true)
    expect(r.mode).toBe('not-a-dispatch')
  })
})

// ── The wiring, asserted against the real workflow file ───────────────────────────────────────
// A correct decision function that deploy.yml never consults would be a §N.8 signal with no
// detector behind it. These assertions fail if the gate is unwired or the bypass is reintroduced.

describe('deploy.yml wiring', () => {
  const yml = YAML.load(
    fs.readFileSync(path.resolve(__dirname, '../../../.github/workflows/deploy.yml'), 'utf8')
  ) as any

  const DEPLOY_JOBS = ['deploy-web', 'deploy-sidecar', 'deploy-mcp', 'deploy-pipeline-job']

  it('workflow_dispatch still exists — emergency manual deploy was not removed', () => {
    // YAML parses the bare key `on:` as boolean true; accept either spelling.
    const on = yml.on ?? yml[true]
    expect(on).toHaveProperty('workflow_dispatch')
  })

  it('workflow_dispatch declares the ci_gate / emergency_reason / force_all_services inputs', () => {
    const on = yml.on ?? yml[true]
    const inputs = on.workflow_dispatch.inputs
    expect(Object.keys(inputs).sort()).toEqual(
      ['ci_gate', 'emergency_reason', 'force_all_services'].sort()
    )
    expect(inputs.ci_gate.default).toBe(REQUIRE_CI_GREEN)
    expect(inputs.ci_gate.options).toContain(EMERGENCY_OVERRIDE_TOKEN)
    expect(inputs.force_all_services.default).toBe(false)
  })

  it('the changes job runs the dispatch gate', () => {
    const steps = yml.jobs.changes.steps as Array<{ run?: string }>
    const gateStep = steps.find(s => (s.run ?? '').includes('ci/dispatch_gate.ts'))
    expect(gateStep).toBeDefined()
  })

  it('every deploy job depends on the changes job, so the gate actually binds to it', () => {
    for (const job of DEPLOY_JOBS) {
      expect(yml.jobs[job].needs, `${job} must need [changes]`).toContain('changes')
    }
  })

  it('no deploy job still short-circuits its path gate on event_name == workflow_dispatch', () => {
    // This is the second half of the bypass: `github.event_name == 'workflow_dispatch' ||
    // needs.changes.outputs.X == 'true'` force-deployed every service regardless of whether its
    // paths changed. It is now `needs.changes.outputs.force_all == 'true' || ...`, an explicit,
    // opt-in input rather than an automatic consequence of dispatching.
    for (const job of ['deploy-sidecar', 'deploy-mcp', 'deploy-pipeline-job']) {
      const cond = String(yml.jobs[job].if)
      expect(cond, `${job}`).toContain("needs.changes.outputs.force_all == 'true'")
      expect(
        cond.includes("github.event_name == 'workflow_dispatch' || needs.changes.outputs"),
        `${job} must not re-introduce the dispatch path-gate short-circuit`
      ).toBe(false)
    }
  })

  it('the changes job still exposes the per-service path outputs plus force_all', () => {
    expect(Object.keys(yml.jobs.changes.outputs).sort()).toEqual(
      ['force_all', 'mcp', 'pipeline', 'sidecar'].sort()
    )
  })
})
