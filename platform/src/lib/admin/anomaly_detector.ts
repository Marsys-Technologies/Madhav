// Realigned for new pipeline 2026-05-12 (Gate II W6).
// The `context_assembly` anomaly branch is dormant — the legacy
// trace.context_assembly field is always null post-Gate II. The branch is
// retained as a guard for older trace rows from the legacy-pipeline era.
import type { TraceDocument } from './trace_assembler'

export type AnomalySeverity = 'ERROR' | 'WARNING' | 'INFO'

export interface Anomaly {
  /** `classify` is retained as a legacy stage tag; new code emits `planner` instead. */
  stage: 'classify' | 'planner' | 'plan' | 'fetch' | 'context_assembly' | 'synthesis' | 'overall'
  severity: AnomalySeverity
  message: string
  step_id: string | null
  metric?: { actual: number; p50: number; ratio: number }
}

export function detectAnomalies(trace: TraceDocument): Anomaly[] {
  const anomalies: Anomaly[] = []
  const baselines = trace.baselines

  // 1. Plan latency outlier — compare plan latency to total p50 as proxy
  if (
    trace.plan?.latency_ms != null &&
    baselines?.p50_total_latency_ms != null &&
    baselines.p50_total_latency_ms > 0
  ) {
    const p50 = baselines.p50_total_latency_ms
    const ratio = trace.plan.latency_ms / p50
    if (ratio > 2.0) {
      anomalies.push({
        stage: 'plan',
        severity: ratio > 3.0 ? 'ERROR' : 'WARNING',
        message: `Plan latency ${trace.plan.latency_ms}ms (${ratio.toFixed(1)}× p50)`,
        step_id: 'plan',
        metric: { actual: trace.plan.latency_ms, p50, ratio },
      })
    }
  }

  // 2. Failed fetch steps
  for (const fetch of trace.fetches) {
    if (fetch.error_class !== 'OK') {
      anomalies.push({
        stage: 'fetch',
        severity: 'ERROR',
        message: `${fetch.bundle} fetch failed: ${fetch.error_class}`,
        step_id: fetch.bundle,
      })
    }
  }

  // 3. Empty fetch steps (non-error but returned 0 items)
  for (const fetch of trace.fetches) {
    if (fetch.error_class === 'OK' && fetch.kept_count === 0 && fetch.raw_count === 0) {
      anomalies.push({
        stage: 'fetch',
        severity: 'WARNING',
        message: `${fetch.bundle} returned 0 items — possible filter too narrow`,
        step_id: fetch.bundle,
      })
    }
  }

  // 4. Context assembly budget pressure
  if (trace.context_assembly) {
    const dropped = trace.context_assembly.token_ledger.dropped_count
    const total = trace.context_assembly.items.length
    if (total > 0 && dropped / total > 0.3) {
      anomalies.push({
        stage: 'context_assembly',
        severity: 'WARNING',
        message: `Context assembly dropped ${dropped}/${total} items (${Math.round((dropped / total) * 100)}%) — budget pressure`,
        step_id: 'context_assembly',
      })
    }

    // Priority violation: a DROPPED item scored higher than all INCLUDED items
    const includedScores = trace.context_assembly.items
      .filter(i => i.status === 'INCLUDED' && i.relevance_score != null)
      .map(i => i.relevance_score!)
    const maxIncludedScore = includedScores.length > 0 ? Math.max(...includedScores) : null
    const droppedHigher = trace.context_assembly.items.filter(
      i =>
        i.status === 'DROPPED' &&
        i.relevance_score != null &&
        maxIncludedScore != null &&
        i.relevance_score > maxIncludedScore,
    )
    if (droppedHigher.length > 0) {
      anomalies.push({
        stage: 'context_assembly',
        severity: 'ERROR',
        message: `Priority violation: ${droppedHigher.length} dropped item(s) scored higher than included items`,
        step_id: 'context_assembly',
      })
    }
  }

  // 5. Synthesis citation density below threshold
  const scorecard = trace.synthesis?.scorecard as
    | { citation_density?: number; composite_score?: number }
    | null
    | undefined
  if (scorecard?.citation_density != null && scorecard.citation_density < 0.5) {
    anomalies.push({
      stage: 'synthesis',
      severity: 'WARNING',
      message: `Low citation density: ${scorecard.citation_density.toFixed(2)} (expected ≥ 0.5)`,
      step_id: 'synthesis',
    })
  }
  if (scorecard?.composite_score != null && scorecard.composite_score < 0.6) {
    anomalies.push({
      stage: 'synthesis',
      severity: scorecard.composite_score < 0.4 ? 'ERROR' : 'WARNING',
      message: `Synthesis quality score: ${scorecard.composite_score.toFixed(2)} (below 0.6 threshold)`,
      step_id: 'synthesis',
    })
  }

  return anomalies.sort((a, b) => {
    const order: Record<AnomalySeverity, number> = { ERROR: 0, WARNING: 1, INFO: 2 }
    return order[a.severity] - order[b.severity]
  })
}

export function buildHealthSummary(
  health: TraceDocument['query']['health'],
  anomalies: Anomaly[],
): string {
  if (anomalies.length === 0) return 'All stages nominal'
  const firstError = anomalies.find(a => a.severity === 'ERROR')
  if (firstError) return `Critical failure in ${firstError.stage}`
  const firstWarning = anomalies[0]
  const msg = firstWarning.message
  return `Degraded: ${msg.length > 60 ? msg.slice(0, 57) + '…' : msg}`
}
