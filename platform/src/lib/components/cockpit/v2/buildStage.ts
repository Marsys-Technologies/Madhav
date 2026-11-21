import type { BuildPhase } from '@/hooks/useActiveRun'

export type BuildStage =
  | 'queued'
  | 'running'
  | 'computing'
  | 'writing'
  | 'substeps'
  | 'verifying'
  | 'publishing'
  | 'committing'
  | 'lit'
  | 'idle'

export interface SubstepInfo {
  index: number
  total: number
  label?: string
}

export interface PhaseDurationsMs {
  compute_ms?: number | null
  write_ms?: number | null
  verify_ms?: number | null
  publish_ms?: number | null
}

/** Human-readable display label for a durable orchestrator phase. */
export function phaseDisplayLabel(phase?: BuildPhase | null): string | null {
  switch (phase) {
    case 'queued': return 'Queued'
    case 'computing': return 'Computing'
    case 'writing': return 'Writing'
    case 'verifying': return 'Verifying'
    case 'publishing': return 'Publishing'
    case 'complete': return 'Complete'
    case 'skipped': return 'Skipped'
    case 'error': return 'Error'
    case 'aborted': return 'Aborted'
    default: return null
  }
}

/** Format a millisecond duration compactly for phase telemetry & ETA breakdowns. */
export function formatPhaseMs(ms: number): string {
  const safeMs = Math.max(0, Math.round(ms))
  if (safeMs < 1000) return `${safeMs}ms`
  const totalSeconds = safeMs / 1000
  if (totalSeconds < 60) {
    return totalSeconds >= 10 ? `${Math.round(totalSeconds)}s` : `${totalSeconds.toFixed(1)}s`
  }
  const minutes = Math.floor(totalSeconds / 60)
  const remSeconds = Math.round(totalSeconds % 60)
  if (minutes >= 60) {
    const hours = Math.floor(minutes / 60)
    const remMinutes = minutes % 60
    return remMinutes ? `${hours}h ${remMinutes}m` : `${hours}h`
  }
  return remSeconds ? `${minutes}m ${remSeconds}s` : `${minutes}m`
}

/** Format non-null per-phase millisecond measurements into a compact summary string. */
export function formatPhaseBreakdown(durations: PhaseDurationsMs): string | null {
  const parts: string[] = []
  if (durations.compute_ms != null) parts.push(`Compute ${formatPhaseMs(durations.compute_ms)}`)
  if (durations.write_ms != null) parts.push(`Write ${formatPhaseMs(durations.write_ms)}`)
  if (durations.verify_ms != null) parts.push(`Verify ${formatPhaseMs(durations.verify_ms)}`)
  if (durations.publish_ms != null) parts.push(`Publish ${formatPhaseMs(durations.publish_ms)}`)
  return parts.length > 0 ? parts.join(' · ') : null
}

/** Returns fill percentage [0..100] for the given stage */
export function stageFill(stage: BuildStage, substep?: SubstepInfo): number {
  switch (stage) {
    case 'queued': return 3
    case 'computing': return 8
    case 'running': return 12
    case 'writing': {
      if (!substep || substep.total === 0) return 28
      const progress = substep.index / substep.total
      return 15 + progress * 70
    }
    case 'substeps': {
      if (!substep || substep.total === 0) return 15
      const progress = substep.index / substep.total
      return 15 + progress * 73 // lerp 15..88
    }
    case 'verifying': return 90
    case 'publishing': return 96
    case 'committing': return 93
    case 'lit': return 100
    default: return 0
  }
}

/** Derive BuildStage from durable phase + SSE overlay + polled state */
export function deriveBuildStage(params: {
  polledState: string
  sseState?: string
  phase?: BuildPhase | null
  substepIndex?: number
  substepTotal?: number
  isQueued?: boolean
}): BuildStage {
  const { polledState, sseState, phase, substepIndex, substepTotal, isQueued } = params
  const effectiveState = sseState ?? polledState

  if (isQueued) return 'queued'
  if (effectiveState === 'lit' || effectiveState === 'service_ok') return 'lit'
  if (effectiveState !== 'building') return 'idle'

  if (phase === 'verifying') return 'verifying'
  if (phase === 'publishing') return 'publishing'
  if (phase === 'writing') {
    if (substepIndex !== undefined && substepTotal !== undefined && substepTotal > 1) {
      return 'substeps'
    }
    return 'writing'
  }
  if (phase === 'computing') return 'computing'

  // Legacy pre-1420 building fallback (no durable phase column yet)
  if (substepIndex !== undefined && substepTotal !== undefined && substepTotal > 0) {
    if (substepIndex >= substepTotal) return 'committing'
    return 'substeps'
  }
  return 'running'
}
