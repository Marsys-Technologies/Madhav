/**
 * Watchdog clause 1 (orphan-run reaper) decision-boundary tests.
 *
 * INCIDENT (2026-07-31/08-01): run e5cde4dc (chart 1c826d5a, ka_gochara_sweep) was
 * falsely marked 'failed' by clause 1 while the Cloud Run container was ALIVE and
 * progressing — build_substep_progress showed fresh commits (~5-6.5 min cadence)
 * that the pre-fix reaper never consulted, and asset_throughput.last_built_at can
 * lag behind real substep-commit time (see route.ts file-header incident note for
 * the full root-cause account: NOT client-clock skew — every heartbeat write
 * already uses DB-side NOW() — but a PostgreSQL semantic where NOW()/
 * CURRENT_TIMESTAMP reflects transaction-START time, and a heavy writer's substep
 * runs as one multi-minute transaction).
 *
 * (a) is the RED-first reproduction: under the PRE-FIX policy (10-min window,
 * asset_throughput only) this exact input WOULD be reaped. Under the fixed policy
 * it must NOT be — build_substep_progress corroborates the run is genuinely alive
 * even though asset_throughput lags past the (now-widened) window.
 * (b) proves the reaper's genuine purpose survives: a truly dead run (no heartbeat,
 * no substep progress, for 30+ minutes) must still be reaped.
 */
import { describe, it, expect } from 'vitest'
import {
  wouldReapOrphanRun,
  ORPHAN_RUN_MIN_AGE_MINUTES,
  ORPHAN_RUN_EVIDENCE_WINDOW_MINUTES,
  type OrphanRunReaperInput,
} from '../orphanRunReaperPolicy'

const NOW = new Date('2026-08-01T04:30:05Z') // the incident kill timestamp
const minutesAgo = (n: number) => new Date(NOW.getTime() - n * 60_000)

function baseInput(overrides: Partial<OrphanRunReaperInput> = {}): OrphanRunReaperInput {
  return {
    runState: 'running',
    startedAt: minutesAgo(45), // well past the 30-min minimum age
    latestAssetThroughputAt: null,
    latestSubstepProgressAt: null,
    ...overrides,
  }
}

/** Pre-fix behaviour, reproduced verbatim for the RED-first assertion below:
 *  asset_throughput.last_built_at alone, 10-minute window. */
function preFixWouldReap(input: OrphanRunReaperInput, now: Date): boolean {
  if (input.runState !== 'running') return false
  if (now.getTime() - input.startedAt.getTime() <= 30 * 60_000) return false
  const cutoff = now.getTime() - 10 * 60_000
  const hasRecentThroughput =
    input.latestAssetThroughputAt != null && input.latestAssetThroughputAt.getTime() > cutoff
  return !hasRecentThroughput
}

describe('watchdog clause 1 — orphan-run reaper policy', () => {
  it('sanity: thresholds match the fix (30-min age gate, 15-min evidence window)', () => {
    expect(ORPHAN_RUN_MIN_AGE_MINUTES).toBe(30)
    expect(ORPHAN_RUN_EVIDENCE_WINDOW_MINUTES).toBe(15)
  })

  describe('(a) false-kill reproduction — live run with lagging asset_throughput', () => {
    // asset_throughput.last_built_at is 20 min stale (beyond even the widened
    // 15-min window) but build_substep_progress shows a commit 5 min ago —
    // exactly tonight's shape: the container was alive, the substep ledger
    // proves it, asset_throughput alone did not.
    const input = baseInput({
      latestAssetThroughputAt: minutesAgo(20),
      latestSubstepProgressAt: minutesAgo(5),
    })

    it('RED (pre-fix, asset_throughput-only @10min): WOULD have been reaped', () => {
      expect(preFixWouldReap(input, NOW)).toBe(true)
    })

    it('GREEN (post-fix): is NOT reaped — build_substep_progress corroborates life', () => {
      expect(wouldReapOrphanRun(input, NOW)).toBe(false)
    })
  })

  describe('(a2) both signals fresh (5 min old) — the plainly-alive control case', () => {
    it('is not reaped', () => {
      const input = baseInput({
        latestAssetThroughputAt: minutesAgo(5),
        latestSubstepProgressAt: minutesAgo(5),
      })
      expect(wouldReapOrphanRun(input, NOW)).toBe(false)
    })
  })

  describe('(b) truly-orphaned run — no heartbeat, no substep progress', () => {
    it('is reaped after the 30-min age gate with neither signal recent', () => {
      const input = baseInput({
        latestAssetThroughputAt: null,
        latestSubstepProgressAt: null,
      })
      expect(wouldReapOrphanRun(input, NOW)).toBe(true)
    })

    it('is reaped when both signals are stale (older than the 15-min window)', () => {
      const input = baseInput({
        latestAssetThroughputAt: minutesAgo(45),
        latestSubstepProgressAt: minutesAgo(40),
      })
      expect(wouldReapOrphanRun(input, NOW)).toBe(true)
    })

    it('is NOT reaped before the 30-min age gate, even with no evidence at all', () => {
      const input = baseInput({
        startedAt: minutesAgo(10),
        latestAssetThroughputAt: null,
        latestSubstepProgressAt: null,
      })
      expect(wouldReapOrphanRun(input, NOW)).toBe(false)
    })

    it('non-running states are never reaped by this clause', () => {
      const input = baseInput({ runState: 'completed' })
      expect(wouldReapOrphanRun(input, NOW)).toBe(false)
    })
  })

  describe('boundary: either signal alone, freshly within the window, is sufficient', () => {
    it('recent asset_throughput alone spares the run', () => {
      const input = baseInput({
        latestAssetThroughputAt: minutesAgo(14),
        latestSubstepProgressAt: null,
      })
      expect(wouldReapOrphanRun(input, NOW)).toBe(false)
    })

    it('recent build_substep_progress alone spares the run', () => {
      const input = baseInput({
        latestAssetThroughputAt: null,
        latestSubstepProgressAt: minutesAgo(14),
      })
      expect(wouldReapOrphanRun(input, NOW)).toBe(false)
    })
  })
})
