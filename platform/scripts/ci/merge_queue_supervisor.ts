/**
 * Fail-closed CI and merge-queue classification for autonomous campaign work.
 *
 * This module deliberately has no API that cancels runs, reruns workflows, merges PRs,
 * or dispatches deployments. It turns observations into a bounded next action so the
 * conductor can keep independent work moving without mistaking ordinary CI latency for
 * an infrastructure outage.
 */

export const DEFAULT_CI_RUNTIME_POLICY = {
  /** A warning is useful context, never authority to cancel. */
  softWaitMinutes: 15,
  /** Derived from the observed 6–14 minute protected checks, with margin. */
  hardStallMinutes: 20,
  /** Two observations are required before a stalled-run classification. */
  confirmationMinutes: 5,
  /** Do not turn transient infrastructure noise into an unbounded retry loop. */
  maxTransientRetries: 2,
  /** A second identical deterministic failure receives specialist analysis. */
  maxIdenticalFailureAttempts: 2,
} as const

export type CampaignExecutionState =
  | 'ci_running'
  | 'merge_queue_wait'
  | 'merge_ready'
  | 'merged_release_pending'
  | 'release_authority_pending'
  | 'release_running'
  | 'live_revision_unverified'
  | 'acceptance_running'
  | 'blocked_authority'

export type SupervisorAction =
  | 'monitor'
  | 'continue_independent_work'
  | 'queue_merge'
  | 'reconcile_merged_state'
  | 'retry_transient_once'
  | 'dispatch_root_cause_specialist'
  | 'dispatch_native_surrogate'
  | 'request_authority_broker'
  | 'hold_dependent_cone'

export interface QueueSupervisorObservation {
  state: CampaignExecutionState
  now: string
  /** The exact source SHA being observed. A changed SHA invalidates prior timing evidence. */
  sha: string
  /** A protected merge is stronger evidence than a stale PR/check presentation. */
  mergedAt?: string
  /** GitHub mergeQueueEntry presence, not auto-merge UI appearance, is queue truth. */
  mergeQueueEntryPresent?: boolean
  /** Required checks have all completed successfully for this exact SHA. */
  requiredChecksGreen?: boolean
  /** The latest meaningful job/step transition, rather than the last log line. */
  lastProgressAt?: string
  /** Stable workflow/job/step state; a changed value starts a new stall-confirmation window. */
  progressFingerprint?: string
  /** Previous identical observation, persisted by the caller after a read-only poll. */
  previous?: {
    sha: string
    observedAt: string
    progressFingerprint: string
  }
  /** Stable workflow/job/step/error signature for a failed run. */
  failureFingerprint?: string
  /** Attempts already made for this exact fingerprint and SHA. */
  identicalFailureAttempts?: number
  /** Retries already consumed for a transient failure class and SHA. */
  transientRetries?: number
  /** The release cone needs an external credential or approval that is not provisioned. */
  authorityAvailable?: boolean
}

export interface SupervisorDecision {
  state: CampaignExecutionState
  action: SupervisorAction
  reason: string
  /** True only for a proven hard stall. A conductor still needs a separate action policy. */
  stallConfirmed: boolean
}

/**
 * An executable handoff envelope for the task runtime.  This is deliberately a
 * data contract, rather than an in-process model call: CI runs must not receive
 * an ambient model credential or acquire permission to perform a release.
 *
 * A conductor dispatches this envelope only when `SupervisorDecision.action` is
 * `dispatch_native_surrogate`, waits for the bounded ruling, then resumes the
 * original task at `resumeState`.  The surrogate is an adjudicator, not a new
 * owner of the campaign.
 */
export interface NativeSurrogateHandoff {
  model: 'gpt-5.6-sol'
  reasoningEffort: 'high'
  goal: string
  exactSha: string
  state: CampaignExecutionState
  failureFingerprint: string
  attemptHistory: {
    identicalFailureAttempts: number
    transientRetries: number
  }
  evidence: string[]
  safeActions: string[]
  authorityBoundary: string
  requiredReturnFields: Array<
    'decision'
    | 'rationale'
    | 'authorized_next_action'
    | 'disallowed_actions'
    | 'required_verifier'
    | 'resume_state'
  >
  resumeState: CampaignExecutionState
}

function parseTime(value: string | undefined, label: string): number | undefined {
  if (!value) return undefined
  const parsed = Date.parse(value)
  if (Number.isNaN(parsed)) throw new Error(`${label} must be an ISO-8601 timestamp`)
  return parsed
}

function minutesSince(now: string, then: string | undefined, label: string): number | undefined {
  const nowMs = parseTime(now, 'now')
  const thenMs = parseTime(then, label)
  if (nowMs === undefined || thenMs === undefined) return undefined
  return Math.max(0, (nowMs - thenMs) / 60_000)
}

/**
 * Builds the complete, least-privilege packet the task runtime can send to the
 * configured GPT-5.6 Sol/high Native Surrogate.  It refuses non-surrogate
 * decisions so ordinary CI latency cannot accidentally create a handoff.
 */
export function buildNativeSurrogateHandoff(
  observation: QueueSupervisorObservation,
  decision = evaluateQueueObservation(observation),
): NativeSurrogateHandoff | undefined {
  if (decision.action !== 'dispatch_native_surrogate' || !observation.failureFingerprint) return undefined

  return {
    model: 'gpt-5.6-sol',
    reasoningEffort: 'high',
    goal: 'Resolve the bounded campaign ambiguity without expanding authority; return a decision packet so the original task can resume.',
    exactSha: observation.sha,
    state: observation.state,
    failureFingerprint: observation.failureFingerprint,
    attemptHistory: {
      identicalFailureAttempts: observation.identicalFailureAttempts ?? 0,
      transientRetries: observation.transientRetries ?? 0,
    },
    evidence: [
      `supervisor_reason:${decision.reason}`,
      `observed_at:${observation.now}`,
      `progress_fingerprint:${observation.progressFingerprint ?? 'not-recorded'}`,
    ],
    safeActions: [
      'inspect exact-SHA evidence and governing constraints',
      'select one reversible, charter-scoped next action',
      'name an independent verifier before resumption',
    ],
    authorityBoundary: 'Do not create credentials, grant IAM, deploy, alter traffic, or substitute for an unprovisioned external authority.',
    requiredReturnFields: [
      'decision',
      'rationale',
      'authorized_next_action',
      'disallowed_actions',
      'required_verifier',
      'resume_state',
    ],
    resumeState: observation.state,
  }
}

/**
 * Classify one observation. The caller must persist only observations for the same SHA and
 * progress fingerprint; a rebased PR or a new job step always starts a fresh confirmation window.
 */
export function evaluateQueueObservation(
  observation: QueueSupervisorObservation,
  policy = DEFAULT_CI_RUNTIME_POLICY,
): SupervisorDecision {
  if (observation.mergedAt) {
    return {
      state: 'merged_release_pending',
      action: 'reconcile_merged_state',
      stallConfirmed: false,
      reason: `Protected merge at ${observation.mergedAt} outranks queue/check presentation; reconcile release state for ${observation.sha}.`,
    }
  }

  if (observation.state === 'blocked_authority' || observation.state === 'release_authority_pending') {
    if (observation.authorityAvailable) {
      return {
        state: 'release_running',
        action: 'monitor',
        stallConfirmed: false,
        reason: 'The required release authority is now available; release may proceed through its protected exact-SHA path.',
      }
    }
    return {
      state: 'blocked_authority',
      action: 'request_authority_broker',
      stallConfirmed: false,
      reason: 'Only the release dependency cone is blocked by absent authority; continue source, test, and evidence work.',
    }
  }

  if (observation.state === 'merge_ready' && observation.requiredChecksGreen && !observation.mergeQueueEntryPresent) {
    return {
      state: 'merge_ready',
      action: 'queue_merge',
      stallConfirmed: false,
      reason: 'Required checks are green and no merge-queue entry exists for this exact SHA.',
    }
  }

  if (observation.state === 'merge_queue_wait' || observation.mergeQueueEntryPresent) {
    return {
      state: 'merge_queue_wait',
      action: 'continue_independent_work',
      stallConfirmed: false,
      reason: 'A real merge-queue entry is a waiting state, not a campaign-wide blocker.',
    }
  }

  if (observation.failureFingerprint) {
    const attempts = observation.identicalFailureAttempts ?? 0
    if (attempts >= policy.maxIdenticalFailureAttempts) {
      return {
        state: observation.state,
        action: 'dispatch_native_surrogate',
        stallConfirmed: false,
        reason: `Failure fingerprint ${observation.failureFingerprint} repeated ${attempts} times for ${observation.sha}; adjudicate rather than retry blindly.`,
      }
    }
    if ((observation.transientRetries ?? 0) < policy.maxTransientRetries) {
      return {
        state: observation.state,
        action: 'retry_transient_once',
        stallConfirmed: false,
        reason: `Transient failure fingerprint ${observation.failureFingerprint} is within the bounded retry budget.`,
      }
    }
    return {
      state: observation.state,
      action: 'dispatch_root_cause_specialist',
      stallConfirmed: false,
      reason: `Transient retry budget is exhausted for ${observation.failureFingerprint}; diagnose the root cause before another attempt.`,
    }
  }

  if (observation.state === 'ci_running') {
    const sinceProgress = minutesSince(observation.now, observation.lastProgressAt, 'lastProgressAt')
    const priorAge = observation.previous?.sha === observation.sha
      ? minutesSince(observation.now, observation.previous.observedAt, 'previous.observedAt')
      : undefined
    const unchanged = Boolean(
      observation.previous
      && observation.previous.sha === observation.sha
      && observation.previous.progressFingerprint === observation.progressFingerprint,
    )
    const hardStall = sinceProgress !== undefined
      && sinceProgress >= policy.hardStallMinutes
      && unchanged
      && priorAge !== undefined
      && priorAge >= policy.confirmationMinutes

    if (hardStall) {
      return {
        state: 'ci_running',
        action: 'dispatch_root_cause_specialist',
        stallConfirmed: true,
        reason: `No meaningful CI transition for ${Math.floor(sinceProgress)} minutes across two observations; this is a confirmed stall candidate, not a log-silence guess.`,
      }
    }

    const prefix = sinceProgress !== undefined && sinceProgress >= policy.softWaitMinutes
      ? `CI has exceeded the ${policy.softWaitMinutes}-minute advisory threshold`
      : 'CI is within its observed normal window'
    return {
      state: 'ci_running',
      action: 'continue_independent_work',
      stallConfirmed: false,
      reason: `${prefix}; monitor the exact SHA and keep independent work moving.`,
    }
  }

  return {
    state: observation.state,
    action: 'monitor',
    stallConfirmed: false,
    reason: `State ${observation.state} has no destructive recovery action. Monitor exact evidence and preserve the dependency boundary.`,
  }
}
