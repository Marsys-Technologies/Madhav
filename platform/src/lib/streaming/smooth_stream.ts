import 'server-only'

/**
 * smooth_stream.ts — R11.C C-S2 (extends Y-S3)
 *
 * Layered rate-targeting on top of Y-S3's word-aware flush.
 *
 * Layer 1 (Y-S3 — always active when R10_SMOOTH_STREAM_V2=true):
 *   smoothStream({ delayInMs: MAX_WORD_BUFFER_MS, chunking: 'word' })
 *   Buffers to word boundaries, max 80ms wait before forcing a flush.
 *
 * Layer 2 (R11.C — active when R11C_SMOOTH_STREAM_V3=true, default true):
 *   Rate-target ~TARGET_CPS characters per second over a sliding window.
 *   When the upstream is bursty (LLM outputs a large chunk at once), this
 *   layer paces the flush so the UI receives tokens at a steady rhythm.
 *
 *   Algorithm:
 *   - Track accumulated characters + elapsed time in a sliding window.
 *   - If the observed rate > TARGET_CPS, insert a short delay before flushing
 *     the next chunk.
 *   - If the observed rate < TARGET_CPS (provider is slow), flush immediately.
 *   - MAX_WORD_BUFFER_MS cap is preserved — no flush waits longer than 80ms.
 *
 * Rollback:
 *   R11C_SMOOTH_STREAM_V3=false → falls back to Y-S3 word-aware behavior.
 *   R10_SMOOTH_STREAM_V2=false  → no smoothing at all (raw stream passthrough).
 */

import { smoothStream } from 'ai'
import { getFlag } from '@/lib/config/index'

/** Maximum wait before forcing a flush regardless of word boundary (ms). */
export const MAX_WORD_BUFFER_MS = 80

/**
 * Target characters-per-second rate for the R11.C rate-targeting layer.
 * 40 cps is the empirical sweet spot for Marsys — fast enough to feel
 * responsive, slow enough for users to track reasoning as it streams.
 *
 * Measured on a 5-second bursty-input window, observed mean cps should
 * fall within ±15% of this value (i.e., 34–46 cps).
 */
export const TARGET_CPS = 40

/**
 * Sliding window size (ms) for rate measurement.
 * CPS is computed over the last RATE_WINDOW_MS milliseconds of output.
 */
export const RATE_WINDOW_MS = 1000

/**
 * RateTargetState: stateful accumulator for the rate-target layer.
 *
 * Not exported for direct use — call createRateTargetState() instead.
 * Tests use this type to inspect internal state.
 */
export interface RateTargetState {
  /** Timestamps (ms) of recent flush events in the sliding window. */
  flushTimestamps: number[]
  /** Character counts for each flush event (parallel to flushTimestamps). */
  flushChars: number[]
  /** Total characters flushed in the current window. */
  windowChars: number
}

/**
 * Returns a fresh RateTargetState.
 */
export function createRateTargetState(): RateTargetState {
  return { flushTimestamps: [], flushChars: [], windowChars: 0 }
}

/**
 * Record a flush event in the rate-target state.
 */
export function recordFlush(
  state: RateTargetState,
  chunkLen: number,
  nowMs: number,
): void {
  state.flushTimestamps.push(nowMs)
  state.flushChars.push(chunkLen)
  state.windowChars += chunkLen
}

/**
 * Returns the milliseconds to delay before flushing `chunkLen` characters,
 * given the current window state and the current timestamp.
 *
 * Returns 0 if no delay is needed (provider is slow or rate-target inactive).
 */
export function computeFlushDelay(
  state: RateTargetState,
  chunkLen: number,
  nowMs: number,
  targetCps: number = TARGET_CPS,
  windowMs: number = RATE_WINDOW_MS,
): number {
  // Prune expired entries from the window
  const cutoff = nowMs - windowMs
  let pruneIdx = 0
  while (
    pruneIdx < state.flushTimestamps.length &&
    state.flushTimestamps[pruneIdx] < cutoff
  ) {
    state.windowChars -= state.flushChars[pruneIdx]
    pruneIdx++
  }
  if (pruneIdx > 0) {
    state.flushTimestamps.splice(0, pruneIdx)
    state.flushChars.splice(0, pruneIdx)
  }

  // Compute current rate (chars in window / window duration)
  const windowDuration =
    state.flushTimestamps.length > 0
      ? nowMs - state.flushTimestamps[0]
      : 0

  if (windowDuration < 50) {
    // Not enough history — flush immediately
    return 0
  }

  const currentCps = (state.windowChars * 1000) / windowDuration

  if (currentCps <= targetCps) {
    // Below target — flush immediately, do not throttle
    return 0
  }

  // Above target — compute ideal delay to bring rate back to target
  // Ideal time to flush `chunkLen` more chars:
  //   idealDelayMs = (chunkLen / targetCps) * 1000  (time to flush at target CPS)
  // Subtract the time already elapsed since last flush.
  const msPerChar = 1000 / targetCps
  const idealFlushMs = chunkLen * msPerChar
  const lastFlush =
    state.flushTimestamps.length > 0
      ? state.flushTimestamps[state.flushTimestamps.length - 1]
      : nowMs - windowMs
  const elapsedSinceLast = nowMs - lastFlush
  const delay = Math.max(0, idealFlushMs - elapsedSinceLast)

  // Cap at MAX_WORD_BUFFER_MS to preserve Y-S3 latency guarantee
  return Math.min(delay, MAX_WORD_BUFFER_MS)
}

/**
 * Returns the word-aware smoothStream transform (Y-S3 layer) if
 * R10_SMOOTH_STREAM_V2 is enabled, or undefined if disabled.
 *
 * The R11.C rate-target layer (Layer 2) operates via computeFlushDelay()
 * + recordFlush() at the stream-flush boundary. This function only provides
 * Layer 1 (the AI SDK's word-aware chunker).
 */
export function getSmoothStreamTransform() {
  if (!getFlag('R10_SMOOTH_STREAM_V2')) return undefined
  return smoothStream({ delayInMs: MAX_WORD_BUFFER_MS, chunking: 'word' })
}

/**
 * Returns true if the R11.C rate-target layer is active.
 * When false, Layer 2 is bypassed and Y-S3 word-aware flush is the only layer.
 */
export function isRateTargetEnabled(): boolean {
  return getFlag('R10_SMOOTH_STREAM_V2') && getFlag('R11C_SMOOTH_STREAM_V3')
}
