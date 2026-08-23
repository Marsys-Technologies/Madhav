import { describe, it, expect, vi } from 'vitest'
import fs from 'fs'
import path from 'path'
import YAML from 'js-yaml'

// The opt-out this file's subject is keyed on (Nirmāṇa R-28.1 / D-49 / SQ-17). `dispatch_gate.ts`
// now RUNS BY DEFAULT and only stays silent when a caller explicitly says `IMPORT_ONLY=1`; the
// guard used to key on `NODE_ENV !== 'test'`, which made a silent no-op the default in every
// environment CI already sets `NODE_ENV: test` for. This test imports the module for its pure
// exports, so it is the caller that must opt out — and it must do so BEFORE the import below
// executes, which is what `vi.hoisted` is for (vitest lifts it above the import block).
vi.hoisted(() => {
  process.env.IMPORT_ONLY = '1'
})

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

/**
 * ── Entrypoint-guard detector (Nirmāṇa R-28.1 / V-28 / D-49 / SQ-17) ─────────────────────────
 *
 * Until this repair, `dispatch_gate.ts` ended with `if (process.env.NODE_ENV !== 'test')`, so a
 * gate placed in any workflow job that exports `NODE_ENV: test` — which `.github/workflows/ci.yml`
 * already does for unit-tests, db-integration-tests and planner-regression — exited 0 with no
 * output, having evaluated nothing. Nothing in this file could see that: every test above imports
 * the pure decision function and never executes the CLI, so the guard had no detector at all.
 *
 * These two cases are that detector. They spawn the real script, and they are paired: the first
 * proves the gate RUNS and BLOCKS under `NODE_ENV=test`, the second proves the explicit
 * `IMPORT_ONLY=1` opt-out still silences it (which is what lets this file import the module at the
 * top). Flipping the guard's polarity, or reverting it to the NODE_ENV form, fails the first.
 *
 * WHAT THESE DO NOT ESTABLISH (stated per D-41's requirement, not assumed): they exercise the
 * guard and `main()`'s wiring only. The decision logic itself is covered by the pure-function
 * tests above; a defect in `evaluateDispatchGate` that still produced a non-zero exit on this
 * input would leave these two green.
 */
describe('entrypoint guard — the gate runs by default and is silent only on an explicit opt-out', () => {
  const platformDir = path.resolve(__dirname, '..', '..')
  const BLOCKING_ENV = {
    GATE_EVENT_NAME: 'workflow_dispatch',
    GATE_CI_GATE: REQUIRE_CI_GREEN,
    GATE_EMERGENCY_REASON: '',
    GATE_CI_CONCLUSION: 'failure',
    GATE_SHA: 'deadbeefdeadbeefdeadbeefdeadbeefdeadbeef',
  }

  async function runGate(extraEnv: Record<string, string>) {
    const { execFileSync } = await import('child_process')
    let out = ''
    let status = 0
    try {
      out = execFileSync('npx', ['tsx', 'scripts/ci/dispatch_gate.ts'], {
        cwd: platformDir,
        env: { ...process.env, ...BLOCKING_ENV, ...extraEnv },
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe'],
        timeout: 60_000,
      })
    } catch (err) {
      const e = err as { status?: number; stdout?: string; stderr?: string }
      status = e.status ?? -1
      out = `${e.stdout ?? ''}${e.stderr ?? ''}`
    }
    return { out, status }
  }

  it('CAN-FAIL: under NODE_ENV=test with no opt-out, a blocked dispatch still exits 1 and says why', async () => {
    // IMPORT_ONLY is cleared deliberately: this test process sets it to '1' so it can import the
    // module, and `...process.env` would otherwise hand that opt-out to the child.
    const { out, status } = await runGate({ NODE_ENV: 'test', IMPORT_ONLY: '' })
    expect(out).toContain('BLOCKED: CI concluded "failure"')
    expect(status).toBe(1)
  }, 60_000)

  it('the explicit IMPORT_ONLY=1 opt-out still suppresses the CLI (what lets this file import it)', async () => {
    const { out, status } = await runGate({ NODE_ENV: 'test', IMPORT_ONLY: '1' })
    expect(out).toBe('')
    expect(status).toBe(0)
  }, 60_000)
})
