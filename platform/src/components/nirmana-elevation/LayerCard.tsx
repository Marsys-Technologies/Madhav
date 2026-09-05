'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { deriveLayerActivityState } from '@/lib/nirmana-elevation/projection'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { LayerStage } from './LayerStage'
import { WaveProgressBar } from './WaveProgressBar'

type LayerActivityState = ReturnType<typeof deriveLayerActivityState>

const STATE_LABEL: Record<LayerActivityState, string> = {
  completed: 'Completed',
  active: 'Active',
  pending: 'Pending',
  unknown: 'Unknown',
}

const STATE_CLASS: Record<LayerActivityState, string> = {
  completed: 'border-brand-ok/60 bg-brand-ok/10 text-brand-ok',
  active: 'border-brand-gold-1/60 bg-brand-gold-1/10 text-brand-gold-2',
  pending: 'border-brand-border bg-brand-bg text-brand-text-3',
  unknown: 'border-brand-warn/60 bg-brand-warn/10 text-brand-warn',
}

/**
 * Plan Ruling R7: frontier counts mirror the campaign charter's C10 SQL exactly (the
 * transitive depends_on closure, with an ancestor satisfied by asset_frozen only). C12's
 * service-probe satisfaction is NOT modeled, so this count may under-report eligibility for
 * assets whose only unmet ancestor is a service-kind asset satisfied by a green health probe.
 */
const FRONTIER_LIMITATION_NOTE = 'Frontier counts mirror the charter’s C10 SQL (transitive depends_on closure; an ancestor is satisfied only by asset_frozen). C12’s service-probe satisfaction is not modeled, so this count may under-report eligibility for assets with service-kind ancestors.'

function relativeTime(iso: string | null, now: number = Date.now()): string {
  if (iso === null) return 'No evidence yet'
  const then = Date.parse(iso)
  if (Number.isNaN(then)) return 'No evidence yet'
  const diffSeconds = Math.max(0, Math.round((now - then) / 1000))
  if (diffSeconds < 60) return 'moments ago'
  const minutes = Math.round(diffSeconds / 60)
  if (minutes < 60) return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`
  const days = Math.round(hours / 24)
  return `${days} ${days === 1 ? 'day' : 'days'} ago`
}

export function LayerCard({ layer, assets, onOpenAudit, defaultOpen = false }: {
  layer: NirmanaElevationSnapshotV2['layers'][number]
  assets: NirmanaElevationSnapshotV2['assets']
  onOpenAudit: (assetId: string) => void
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  const state = deriveLayerActivityState({
    assetsTotal: layer.assets_total,
    frozen: layer.frozen,
    milestonesEarned: layer.completion.earned,
  })
  const percent = layer.completion.percent
  const panelId = `layer-card-panel-${layer.layer_id}`

  const toggle = () => setOpen((value) => !value)

  return <article className="rounded-xl border border-brand-border bg-brand-surface">
    <div className="flex flex-col gap-2 px-4 py-3">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={toggle}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            toggle()
          }
        }}
        className="flex w-full items-center justify-between gap-2 rounded-lg text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold-1"
      >
        <span className="flex items-center gap-2">
          <span aria-hidden="true" className="shrink-0">{open ? <ChevronDown className="size-4 text-brand-gold-2" /> : <ChevronRight className="size-4 text-brand-text-3" />}</span>
          <span className="text-sm font-semibold text-brand-text-1">{layer.layer_id} · {layer.layer_name}</span>
        </span>
        <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] ${STATE_CLASS[state]}`}>{STATE_LABEL[state]}</span>
      </button>

      <div className="space-y-1">
        <div
          role="progressbar"
          aria-label={`${layer.layer_id} cumulative completion`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percent ?? undefined}
          data-progress-state={percent === null ? 'indeterminate' : 'determinate'}
          className="h-1.5 overflow-hidden rounded-full bg-brand-border"
        >
          <span className="block h-full rounded-full bg-brand-gold-2" style={{ width: percent === null ? '0%' : `${percent}%` }} />
        </div>
        <p className="text-xs text-brand-text-2">{percent === null ? '—' : `${percent}%`} · {layer.completion.earned}/{layer.completion.required} milestones</p>
      </div>

      <WaveProgressBar waveProgress={layer.wave_progress} />

      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-brand-text-3">
        <span>{layer.frozen}/{layer.assets_total ?? '—'} frozen</span>
        <span title={FRONTIER_LIMITATION_NOTE}>frontier: {layer.frontier_ready.length} ready</span>
        <span>last activity {relativeTime(layer.last_evidence_at)}</span>
      </div>
    </div>

    {open && <div id={panelId} className="border-t border-brand-border px-4 py-4">
      <LayerStage layer={layer} assets={assets} onOpenAudit={onOpenAudit} waveProgress={layer.wave_progress} showWaveProgressBar={false} showRawState={false} />
    </div>}
  </article>
}
