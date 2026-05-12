/**
 * pipeline_event_translator.ts — Gate III.
 *
 * Pure translation: pipeline step name (+ optional metadata) → astrological
 * narration string. Used by LiveReasoningCard to render trace events without
 * leaking internal jargon.
 */

import {
  PIPELINE_STEP_NARRATION,
  labelFor,
  containsBannedToken,
} from '@/lib/jyotish/domain_labels'

export interface NarrationOptions {
  /** Optional running count / progress descriptor surfaced inline. */
  count?: number
  /** Optional latency in ms — rendered only when ≥ 1500 ms. */
  latencyMs?: number
}

export function narratePipelineStep(stepName: string, options: NarrationOptions = {}): string {
  const base = PIPELINE_STEP_NARRATION[stepName] ?? labelFor('step', stepName)
  const parts: string[] = [base]
  if (typeof options.count === 'number' && options.count > 0) {
    parts.push(`(${options.count} so far)`)
  }
  if (typeof options.latencyMs === 'number' && options.latencyMs >= 1500) {
    const seconds = (options.latencyMs / 1000).toFixed(1)
    parts.push(`· ${seconds}s`)
  }
  const out = parts.join(' ')
  if (containsBannedToken(out)) {
    // Hard fallback — never let jargon escape. Strip narration and show only
    // the titlecased label.
    return labelFor('step', stepName)
  }
  return out
}

/**
 * For a single trace step payload, produce a narration string. Accepts the
 * minimal shape we need from a trace_step event so this module can stay
 * trace-internals-agnostic.
 */
export interface TraceStepLike {
  step_name: string
  status?: string
  latency_ms?: number
  data_summary?: {
    chunks_returned?: number
    rows_returned?: number
    [k: string]: unknown
  }
}

export function narrateTraceStep(step: TraceStepLike): string {
  const count =
    typeof step.data_summary?.chunks_returned === 'number'
      ? step.data_summary.chunks_returned
      : typeof step.data_summary?.rows_returned === 'number'
        ? step.data_summary.rows_returned
        : undefined
  return narratePipelineStep(step.step_name, { count, latencyMs: step.latency_ms })
}
