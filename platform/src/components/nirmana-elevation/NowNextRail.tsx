import { AlertTriangle, ArrowRight, CircleHelp, PlayCircle } from 'lucide-react'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { assetCompactLabel, stageDisplayName } from './vocab'

function activeCounts(snapshot: NirmanaElevationSnapshotV2) {
  const active = snapshot.assets.filter((asset) => asset.campaign_state === 'active').length
  const blocked = snapshot.assets.filter((asset) => asset.campaign_state === 'blocked').length
  return { active, blocked }
}

export function NowNextRail({ snapshot }: { snapshot: NirmanaElevationSnapshotV2 }) {
  const currentStage = snapshot.campaign.current_stage
  const currentStageIndex = snapshot.stages.findIndex((stage) => stage.stage_id === snapshot.campaign.current_stage)
  const currentLayer = currentStage && /^L[0-5]$/.test(currentStage)
    ? snapshot.layers.find((layer) => layer.layer_id === currentStage)
    : undefined
  const nextStage = currentStageIndex >= 0 ? snapshot.stages[currentStageIndex + 1] : undefined
  const counts = activeCounts(snapshot)
  const monitor = snapshot.sources.find((source) => source.source_id === 'program_monitor')
  const programAttention = snapshot.program_sync.status !== 'in_sync' || monitor?.state === 'stale'
  const qualityAttention = programAttention || snapshot.data_quality.verdict !== 'reliable' || snapshot.data_quality.gaps.length > 0 || snapshot.data_quality.contradictions.length > 0 || snapshot.release.production_in_sync === false
  const currentName = !currentStage
    ? 'Execution not yet evidenced'
    : currentLayer
      ? `${currentLayer.layer_id} · ${currentLayer.layer_name}`
      : stageDisplayName(currentStage, snapshot)
  const wave = currentLayer && snapshot.campaign.current_wave !== null ? `Active wave ${snapshot.campaign.current_wave}` : null
  const thenStage = nextStage ?? (!currentStage ? snapshot.stages[0] : undefined)

  return <aside aria-label="Now, next, then campaign rail" className="grid gap-2 lg:grid-cols-4 xl:grid-cols-1">
    <section className="rounded-xl border border-brand-border bg-brand-surface p-3"><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-gold-1">Now</p><p className="mt-1 flex items-center gap-1.5 text-sm font-medium text-brand-text-1"><PlayCircle aria-hidden="true" className="size-4 text-brand-gold-2" />{currentName}</p><p className="mt-1 text-xs text-brand-text-2">{currentStage ? <>{wave ? `${wave} · ` : ''}{counts.active} active · {counts.blocked} blocked</> : 'No stage activity is evidenced.'}</p></section>
    <section className="rounded-xl border border-brand-border bg-brand-surface p-3"><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-gold-1">Eligible now</p>{currentLayer ? <><p className="mt-1 text-sm font-medium text-brand-text-1">{currentLayer.eligible_next_asset_ids.length === 1 ? '1 asset eligible now' : `${currentLayer.eligible_next_asset_ids.length} assets eligible now`}</p>{currentLayer.eligible_next_asset_ids.length > 0 && <ul className="mt-1 space-y-1 text-xs text-brand-gold-2">{currentLayer.eligible_next_asset_ids.map((assetId) => {
      const asset = snapshot.assets.find((candidate) => candidate.asset_id === assetId)
      return <li key={assetId}>{asset ? assetCompactLabel(asset) : assetId}</li>
    })}</ul>}<p className="mt-1 text-xs text-brand-text-2">Completion prerequisite: {currentLayer.required_gate}</p></> : <p className="mt-1 text-sm font-medium text-brand-text-1">Unavailable — no active layer is evidenced</p>}</section>
    <section className="rounded-xl border border-brand-border bg-brand-surface p-3"><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-gold-1">Then</p><p className="mt-1 flex items-center gap-1.5 text-sm font-medium text-brand-text-1"><ArrowRight aria-hidden="true" className="size-4 text-brand-gold-2" />{thenStage ? stageDisplayName(thenStage.stage_id, snapshot) : 'Unknown'}</p><p className="mt-1 text-xs text-brand-text-2">{thenStage ? `Next-stage prerequisite: ${thenStage.required_gate}` : 'No next stage is evidenced.'}</p></section>
    <section className="rounded-xl border border-brand-border bg-brand-surface p-3"><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-gold-1">Attention</p><p className="mt-1 flex items-center gap-1.5 text-sm font-medium text-brand-text-1">{qualityAttention ? <AlertTriangle aria-hidden="true" className="size-4 text-brand-warn" /> : <CircleHelp aria-hidden="true" className="size-4 text-brand-text-3" />}{programAttention ? 'Review synchronization notice' : qualityAttention ? 'Review evidence caveats' : 'No current attention receipt'}</p></section>
  </aside>
}
