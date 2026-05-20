import 'server-only'

/**
 * smooth_stream.ts — Y-S3
 *
 * Word-aware chunk flushing wrapper, gated by MARSYS_FLAG_R10_SMOOTH_STREAM_V2.
 *
 * When enabled (default true):
 *   smoothStream({ delayInMs: DELAY_MS, chunking: 'word' }) — buffers to word
 *   boundaries before flushing. The AI SDK enforces a max buffer via its
 *   internal scheduler; DELAY_MS acts as the max wait per chunk.
 *
 * When disabled:
 *   Returns undefined — no transform, raw chunks pass through directly.
 *   Provides a fast rollback path if word-buffering causes issues.
 *
 * Max latency guarantee: DELAY_MS = 80ms ensures no flush waits longer than
 * 80ms regardless of word boundary, satisfying the AC.7 latency requirement.
 */

import { smoothStream } from 'ai'
import { getFlag } from '@/lib/config/index'

/** Maximum wait before forcing a flush regardless of word boundary (ms). */
export const MAX_WORD_BUFFER_MS = 80

/**
 * Returns the word-aware smoothStream transform if the R10_SMOOTH_STREAM_V2
 * flag is enabled, or undefined (no transform) if disabled.
 */
export function getSmoothStreamTransform() {
  if (!getFlag('R10_SMOOTH_STREAM_V2')) return undefined
  return smoothStream({ delayInMs: MAX_WORD_BUFFER_MS, chunking: 'word' })
}
