export type BuildStage = 'queued' | 'running' | 'substeps' | 'committing' | 'lit' | 'idle'

export interface SubstepInfo {
  index: number
  total: number
  label?: string
}

/** Returns fill percentage [0..100] for the given stage */
export function stageFill(stage: BuildStage, substep?: SubstepInfo): number {
  switch (stage) {
    case 'queued': return 3
    case 'running': return 12
    case 'substeps': {
      if (!substep || substep.total === 0) return 15
      const progress = substep.index / substep.total
      return 15 + progress * 73 // lerp 15..88
    }
    case 'committing': return 93
    case 'lit': return 100
    default: return 0
  }
}

/** Derive BuildStage from SSE overlay + polled state */
export function deriveBuildStage(params: {
  polledState: string
  sseState?: string
  substepIndex?: number
  substepTotal?: number
  isQueued?: boolean
}): BuildStage {
  const { polledState, sseState, substepIndex, substepTotal, isQueued } = params
  const effectiveState = sseState ?? polledState

  if (effectiveState === 'lit') return 'lit'
  if (effectiveState !== 'building') return 'idle'

  // building state
  if (isQueued) return 'queued'
  if (substepIndex !== undefined && substepTotal !== undefined && substepTotal > 0) {
    if (substepIndex >= substepTotal) return 'committing'
    return 'substeps'
  }
  return 'running'
}
