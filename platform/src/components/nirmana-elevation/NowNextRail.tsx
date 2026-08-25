import { AlertTriangle, ArrowRight, CircleHelp, PlayCircle } from 'lucide-react'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'

function activeCounts(snapshot: NirmanaElevationSnapshotV2) {
  const active = new Set(snapshot.active_runs.flatMap((run) => run.active_asset_ids)).size
  const blocked = snapshot.assets.filter((asset) => asset.lifecycle_state === 'blocked').length
  return { active, blocked }
}

export function NowNextRail({ snapshot }: { snapshot: NirmanaElevationSnapshotV2 }) {
  const currentStageIndex = snapshot.stages.findIndex((stage) => stage.stage_id === snapshot.campaign.current_stage)
  const currentLayer = snapshot.campaign.current_layer ? snapshot.layers.find((layer) => layer.layer_id === snapshot.campaign.current_layer) : undefined
  const nextStage = currentStageIndex >= 0 ? snapshot.stages[currentStageIndex + 1] : undefined
  const counts = activeCounts(snapshot)
  const qualityAttention = snapshot.data_quality.verdict !== 'reliable' || snapshot.data_quality.gaps.length > 0 || snapshot.data_quality.contradictions.length > 0 || snapshot.release.production_in_sync === false
  const currentName = currentLayer ? `${currentLayer.layer_id} · ${currentLayer.layer_name}` : 'Unknown current stage'
  const wave = snapshot.campaign.current_wave === null ? 'Unknown wave' : `Active wave ${snapshot.campaign.current_wave}`

  return <aside aria-label="Now, next, then campaign rail" className="grid gap-2 lg:grid-cols-4">
    <section className="rounded-xl border border-brand-border bg-brand-surface p-3"><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-gold-1">Now</p><p className="mt-1 flex items-center gap-1.5 text-sm font-medium text-brand-text-1"><PlayCircle aria-hidden="true" className="size-4 text-brand-gold-2" />{wave}</p><p className="mt-1 text-xs text-brand-text-2">{currentName} · {counts.active} active · {counts.blocked} blocked</p></section>
    <section className="rounded-xl border border-brand-border bg-brand-surface p-3"><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-gold-1">Next</p><p className="mt-1 text-sm font-medium text-brand-text-1">{currentLayer ? `${currentLayer.eligible_next_asset_ids.length} eligible after gate` : 'Unknown — no current layer'}</p><p className="mt-1 text-xs text-brand-text-2">{currentLayer?.required_gate ?? 'No named gate'}</p></section>
    <section className="rounded-xl border border-brand-border bg-brand-surface p-3"><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-gold-1">Then</p><p className="mt-1 flex items-center gap-1.5 text-sm font-medium text-brand-text-1"><ArrowRight aria-hidden="true" className="size-4 text-brand-gold-2" />{nextStage?.stage_id ?? 'Unknown'}</p><p className="mt-1 text-xs text-brand-text-2">{nextStage?.required_gate ?? 'No next stage is evidenced.'}</p></section>
    <section className="rounded-xl border border-brand-border bg-brand-surface p-3"><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-gold-1">Attention</p><p className="mt-1 flex items-center gap-1.5 text-sm font-medium text-brand-text-1">{qualityAttention ? <AlertTriangle aria-hidden="true" className="size-4 text-brand-warn" /> : <CircleHelp aria-hidden="true" className="size-4 text-brand-text-3" />}{qualityAttention ? 'Review evidence caveats' : 'No current attention receipt'}</p></section>
  </aside>
}
