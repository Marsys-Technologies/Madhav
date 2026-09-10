import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import type { NirmanaStageId } from '@/lib/nirmana-elevation/projection'

type Asset = NirmanaElevationSnapshotV2['assets'][number]

const STAGE_DISPLAY_NAMES: Record<Exclude<NirmanaStageId, `L${number}`>, string> = {
  BOOTSTRAP: 'Bootstrap',
  T0_CENSUS: 'T0 · Asset and DAG census',
  PLAN_FROZEN: 'Plan frozen',
  DENOMINATOR_FROZEN: 'Denominator frozen',
  F0_FOUNDATION: 'F0 · Foundation readiness',
  CLOSING: 'Closing',
  COMPLETE: 'Complete',
}

export function stageDisplayName(stageId: NirmanaStageId, snapshot: NirmanaElevationSnapshotV2): string {
  if (/^L[0-5]$/.test(stageId)) {
    const layer = snapshot.layers.find((candidate) => candidate.layer_id === stageId)
    return `${stageId} · ${layer?.layer_name ?? 'Name unavailable'}`
  }
  return STAGE_DISPLAY_NAMES[stageId as keyof typeof STAGE_DISPLAY_NAMES]
}

export function assetPrimaryName(asset: Asset): string {
  return asset.sanskrit_name ?? asset.english_name
}

export function assetHeading(asset: Asset): string {
  return assetPrimaryName(asset)
}

export function assetCompactLabel(asset: Asset): string {
  return asset.english_name
}
