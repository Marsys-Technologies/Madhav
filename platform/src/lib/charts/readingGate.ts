import 'server-only'
import { getChartReadinessMap, isDerivedChartReady } from '@/lib/charts/readiness'
import { readinessRefusalMessage } from '@/lib/charts/readinessCopy'

/**
 * The single admission check used by readiness-gated reading doors (legacy
 * consult, MCP prashna_ask and super-admin chat/build). A new reading starts
 * there only when the shared readiness authority says Ready — a Ready chart may
 * carry a non-blocking refresh warning. Anything else
 * (Building, Needs rebuild, Failed, Partially built, Not built) or an unreadable
 * readiness refuses with CHART_RECOMPUTE_REQUIRED and state-specific copy, so
 * old or incomplete results never produce a reading through those doors.
 * Paripraśna does not use this gate: its planner works from available material
 * and its surface displays a non-blocking chart-completeness notice.
 */
export type ReadingGateResult =
  | { ok: true }
  | { ok: false; code: 'CHART_RECOMPUTE_REQUIRED'; state: string; message: string; retryable: boolean }

/**
 * A refusal is retryable only when it clears on its own: an actively
 * progressing build, or a readiness lookup that failed. Needs rebuild, Failed,
 * Partially built and Not built need an explicit rebuild/operator/user action.
 */
const TRANSIENT_STATES = new Set(['building', 'unavailable'])

export async function checkReadingReadiness(chartId: string): Promise<ReadingGateResult> {
  let state = 'unavailable'
  try {
    const readiness = (await getChartReadinessMap([chartId])).get(chartId)
    if (readiness && isDerivedChartReady(readiness)) return { ok: true }
    state = readiness?.state ?? 'unavailable'
  } catch (err) {
    console.error('[charts/readingGate] readiness lookup failed:', (err as Error)?.message)
  }
  return {
    ok: false,
    code: 'CHART_RECOMPUTE_REQUIRED',
    state,
    message: readinessRefusalMessage(state),
    retryable: TRANSIENT_STATES.has(state),
  }
}
