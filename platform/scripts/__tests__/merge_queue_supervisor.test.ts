import { describe, expect, it } from 'vitest'

import {
  buildNativeSurrogateHandoff,
  DEFAULT_CI_RUNTIME_POLICY,
  evaluateQueueObservation,
  type QueueSupervisorObservation,
} from '../ci/merge_queue_supervisor'

const SHA = 'a'.repeat(40)

function observation(overrides: Partial<QueueSupervisorObservation> = {}): QueueSupervisorObservation {
  return {
    state: 'ci_running',
    now: '2026-09-18T20:40:00.000Z',
    sha: SHA,
    lastProgressAt: '2026-09-18T20:35:00.000Z',
    progressFingerprint: 'unit-tests:running',
    ...overrides,
  }
}

describe('merge-queue supervisor', () => {
  it('CAN-FAIL: does not classify a healthy nine-minute check as stalled', () => {
    const result = evaluateQueueObservation(observation({
      lastProgressAt: '2026-09-18T20:31:00.000Z',
      previous: { sha: SHA, observedAt: '2026-09-18T20:35:00.000Z', progressFingerprint: 'job:running' },
    }))

    expect(result.action).toBe('continue_independent_work')
    expect(result.stallConfirmed).toBe(false)
  })

  it('requires the hard threshold and two unchanged observations before calling a stall', () => {
    const result = evaluateQueueObservation(observation({
      lastProgressAt: '2026-09-18T20:15:00.000Z',
      previous: { sha: SHA, observedAt: '2026-09-18T20:30:00.000Z', progressFingerprint: 'unit-tests:running' },
    }))

    expect(result.action).toBe('dispatch_root_cause_specialist')
    expect(result.stallConfirmed).toBe(true)
  })

  it('does not reuse an observation from a different SHA as stall evidence', () => {
    const result = evaluateQueueObservation(observation({
      lastProgressAt: '2026-09-18T20:15:00.000Z',
      previous: { sha: 'b'.repeat(40), observedAt: '2026-09-18T20:30:00.000Z', progressFingerprint: 'job:running' },
    }))

    expect(result.action).toBe('continue_independent_work')
    expect(result.stallConfirmed).toBe(false)
  })

  it('does not classify a changed CI step as stalled', () => {
    const result = evaluateQueueObservation(observation({
      lastProgressAt: '2026-09-18T20:15:00.000Z',
      progressFingerprint: 'governance:running',
      previous: { sha: SHA, observedAt: '2026-09-18T20:30:00.000Z', progressFingerprint: 'unit-tests:running' },
    }))

    expect(result.action).toBe('continue_independent_work')
    expect(result.stallConfirmed).toBe(false)
  })

  it('treats a real merge-queue entry as a waiting state and preserves independent work', () => {
    const result = evaluateQueueObservation(observation({ state: 'merge_queue_wait', mergeQueueEntryPresent: true }))

    expect(result.action).toBe('continue_independent_work')
    expect(result.state).toBe('merge_queue_wait')
  })

  it('reconciles a merge before attempting any queue recovery', () => {
    const result = evaluateQueueObservation(observation({
      mergedAt: '2026-09-18T20:59:35.000Z',
      failureFingerprint: 'stale-failure',
    }))

    expect(result.action).toBe('reconcile_merged_state')
  })

  it('requires a real queue action only when exact-SHA checks are green and no entry exists', () => {
    const result = evaluateQueueObservation(observation({
      state: 'merge_ready',
      requiredChecksGreen: true,
      mergeQueueEntryPresent: false,
    }))

    expect(result.action).toBe('queue_merge')
  })

  it('escalates a repeated deterministic fingerprint to the Native Surrogate', () => {
    const sourceObservation = observation({
      failureFingerprint: 'migration:1040:owner-membership',
      identicalFailureAttempts: DEFAULT_CI_RUNTIME_POLICY.maxIdenticalFailureAttempts,
    })
    const result = evaluateQueueObservation(sourceObservation)

    expect(result.action).toBe('dispatch_native_surrogate')
    expect(buildNativeSurrogateHandoff(sourceObservation, result)).toMatchObject({
      model: 'gpt-5.6-sol',
      reasoningEffort: 'high',
      exactSha: SHA,
      failureFingerprint: 'migration:1040:owner-membership',
      resumeState: 'ci_running',
    })
  })

  it('does not emit a surrogate handoff for ordinary CI waiting', () => {
    const sourceObservation = observation()
    expect(buildNativeSurrogateHandoff(sourceObservation)).toBeUndefined()
  })

  it('keeps an authority absence scoped to release and does not call it a general failure', () => {
    const result = evaluateQueueObservation(observation({
      state: 'release_authority_pending',
      authorityAvailable: false,
    }))

    expect(result.state).toBe('blocked_authority')
    expect(result.action).toBe('request_authority_broker')
    expect(result.reason).toContain('continue source')
  })
})
