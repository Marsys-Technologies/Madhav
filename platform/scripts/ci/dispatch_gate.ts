/**
 * Manual-dispatch deploy gate — closes the `workflow_dispatch` CI-gate bypass.
 *
 * ── The bypass this closes ────────────────────────────────────────────────────────────────────
 * `.github/workflows/deploy.yml` gates every deploy job on
 *     github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success'
 * so a manual dispatch deploys to production **whether or not CI passed, or even ran**, on that
 * SHA. Observed 3x in one night (SAMĀPTI, Dvārapāla RULING 71 / RULING 73-CLOSE) — twice
 * succeeding roughly four minutes AHEAD of CI completion, once failing safely against the
 * migration guard's fail-closed. RULING 73-CLOSE held it "unchanged, not hardened" for that night,
 * explicitly because gating manual dispatch could block a legitimate emergency deploy. That is a
 * real constraint, not a reason to leave the hole open — so this gate keeps emergency deploys
 * possible and makes them *deliberate* instead of *default*.
 *
 * ── The mechanism ─────────────────────────────────────────────────────────────────────────────
 * Manual dispatch now DEFAULTS to the same CI-green requirement as an automatic deploy. Bypassing
 * it requires the operator to select a non-default choice whose value literally reads
 * `EMERGENCY-OVERRIDE-CI-NOT-GREEN` AND to type a substantive reason. Two deliberate acts, both
 * recorded in the run log — a reflex click cannot produce them.
 *
 * Chosen over the alternatives because it is the smallest change with the fewest new failure
 * modes: no new job topology (it runs inside the existing `changes` job, which already gates every
 * deploy job), no new credentials, no dry-run/plan mode to get out of sync with the real path, and
 * no removal of `workflow_dispatch` itself. The emergency door stays unlocked; it just stopped
 * being the one you fall through.
 *
 * This module is the pure decision function plus a thin CLI so the logic is unit-testable off
 * GitHub Actions — the gate is a real detector with a real can-fail proof, not a YAML expression
 * nobody can exercise (CLAUDE.md §N.8).
 */

/** The exact, deliberately-shouty token an operator must select to bypass the CI-green default. */
export const EMERGENCY_OVERRIDE_TOKEN = 'EMERGENCY-OVERRIDE-CI-NOT-GREEN'

/** The safe default. Anything unrecognised is treated as this — fail safe, not fail open. */
export const REQUIRE_CI_GREEN = 'require-ci-green'

/** Minimum length of a written justification. Long enough that "x" or "asdf" will not pass. */
export const MIN_EMERGENCY_REASON_LENGTH = 20

export interface DispatchGateInput {
  /** github.event_name */
  eventName: string
  /** inputs.ci_gate — only meaningful for workflow_dispatch */
  ciGate: string
  /** inputs.emergency_reason */
  emergencyReason: string
  /**
   * Conclusion of the most recent COMPLETED run of the CI workflow for this exact SHA:
   * 'success' | 'failure' | 'cancelled' | 'timed_out' | ... , or 'none' when CI has not
   * completed for this SHA at all (the observed pattern: dispatch fired ahead of CI).
   */
  ciConclusion: string
  /** github.sha, for the message */
  sha: string
  /** Optional link to the CI run, for the message */
  ciRunUrl?: string
}

export type DispatchGateMode =
  | 'not-a-dispatch'
  | 'ci-green'
  | 'emergency-override'
  | 'blocked-ci-not-green'
  | 'blocked-missing-reason'

export interface DispatchGateResult {
  allowed: boolean
  mode: DispatchGateMode
  /** Human-readable explanation, surfaced into the Actions log either way. */
  reason: string
}

export function evaluateDispatchGate(input: DispatchGateInput): DispatchGateResult {
  const { eventName, ciGate, emergencyReason, ciConclusion, sha, ciRunUrl } = input

  // Automatic (workflow_run) deploys are already gated by
  // `github.event.workflow_run.conclusion == 'success'` in deploy.yml. This gate exists solely to
  // give manual dispatch the SAME standard — it must never add a second, different opinion to the
  // automatic path, or a normal deploy could start failing for reasons unrelated to its own CI.
  if (eventName !== 'workflow_dispatch') {
    return {
      allowed: true,
      mode: 'not-a-dispatch',
      reason:
        `event is "${eventName}", not workflow_dispatch — the manual-dispatch gate does not apply. ` +
        `The workflow_run CI gate in deploy.yml governs this run.`,
    }
  }

  const wantsOverride = ciGate === EMERGENCY_OVERRIDE_TOKEN

  if (!wantsOverride) {
    // Default path (including any unrecognised ci_gate value — fail safe).
    if (ciConclusion === 'success') {
      return {
        allowed: true,
        mode: 'ci-green',
        reason: `CI is green for ${sha} (conclusion: success). Manual deploy proceeds under the same gate as an automatic one.`,
      }
    }
    const observed =
      ciConclusion === 'none'
        ? 'CI has NOT completed for this SHA (no completed run found)'
        : `CI concluded "${ciConclusion}" for this SHA`
    return {
      allowed: false,
      mode: 'blocked-ci-not-green',
      reason:
        `BLOCKED: ${observed}.\n` +
        `  sha: ${sha}\n` +
        (ciRunUrl ? `  ci run: ${ciRunUrl}\n` : '') +
        `This is the workflow_dispatch CI-gate bypass (Dvārapāla RULING 71 / 73-CLOSE, observed 3x). ` +
        `A manual deploy is held to the same standard as an automatic one.\n` +
        `If this IS a genuine emergency, re-run the dispatch with:\n` +
        `  ci_gate         = ${EMERGENCY_OVERRIDE_TOKEN}\n` +
        `  emergency_reason = <at least ${MIN_EMERGENCY_REASON_LENGTH} characters saying what is on fire>\n` +
        `Otherwise: wait for CI to finish and deploy normally.`,
    }
  }

  if (emergencyReason.trim().length < MIN_EMERGENCY_REASON_LENGTH) {
    return {
      allowed: false,
      mode: 'blocked-missing-reason',
      reason:
        `BLOCKED: ci_gate is "${EMERGENCY_OVERRIDE_TOKEN}" but emergency_reason is missing or too short ` +
        `(${emergencyReason.trim().length} chars, need >= ${MIN_EMERGENCY_REASON_LENGTH}).\n` +
        `Overriding the CI gate requires a written, substantive reason — it is recorded in the run log ` +
        `and in the close report. Selecting the override without stating why is exactly the reflex this ` +
        `gate exists to interrupt.`,
    }
  }

  return {
    allowed: true,
    mode: 'emergency-override',
    reason:
      `EMERGENCY OVERRIDE ACCEPTED — deploying ${sha} WITHOUT a green CI gate ` +
      `(CI conclusion for this SHA: ${ciConclusion}).\n` +
      `  stated reason: ${emergencyReason.trim()}\n` +
      `This override is deliberate and recorded. Post-incident, confirm CI on this SHA and note the ` +
      `override in the deploy/merge ledger.`,
  }
}

// ── CLI ───────────────────────────────────────────────────────────────────────────────────────
// Reads the same values deploy.yml has, emits GitHub Actions annotations, exits 0 (proceed) or
// 1 (blocked — which fails the `changes` job and therefore skips every deploy job that needs it).

function main(): void {
  const result = evaluateDispatchGate({
    eventName: process.env.GATE_EVENT_NAME ?? '',
    ciGate: process.env.GATE_CI_GATE ?? REQUIRE_CI_GREEN,
    emergencyReason: process.env.GATE_EMERGENCY_REASON ?? '',
    ciConclusion: process.env.GATE_CI_CONCLUSION ?? 'none',
    sha: process.env.GATE_SHA ?? '(unknown sha)',
    ciRunUrl: process.env.GATE_CI_RUN_URL || undefined,
  })

  const oneLine = result.reason.replace(/\n/g, '%0A')
  if (!result.allowed) {
    console.error(`::error title=Manual dispatch blocked (${result.mode})::${oneLine}`)
    console.error(result.reason)
    process.exit(1)
  }

  if (result.mode === 'emergency-override') {
    console.log(`::warning title=CI gate overridden for a manual deploy::${oneLine}`)
  }
  console.log(`[dispatch-gate] ${result.mode}: ${result.reason}`)
}

// Guard: only execute when run directly, not when imported by tests.
if (process.env.NODE_ENV !== 'test') {
  main()
}
