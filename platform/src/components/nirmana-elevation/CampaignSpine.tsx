'use client'

import { useState } from 'react'
import { CheckCircle2, ChevronDown, ChevronRight, CircleHelp, LockKeyhole, PauseCircle, XCircle } from 'lucide-react'
import { FoundationStage } from './FoundationStage'
import type { NirmanaCampaignStage, NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import type { NirmanaStageId } from '@/lib/nirmana-elevation/projection'

function stageName(stage: NirmanaCampaignStage, snapshot: NirmanaElevationSnapshotV2): string {
  if (!/^L[0-5]$/.test(stage.stage_id)) return stage.stage_id
  const layer = snapshot.layers.find((candidate) => candidate.layer_id === stage.stage_id)
  return `${stage.stage_id} · ${layer?.layer_name ?? 'Unknown'}`
}

function statusLabel(state: NirmanaCampaignStage['state']): string {
  return state.charAt(0).toUpperCase() + state.slice(1)
}

function statusIcon(state: NirmanaCampaignStage['state']) {
  if (state === 'completed') return <CheckCircle2 aria-hidden="true" className="size-4 text-brand-ok" />
  if (state === 'locked') return <LockKeyhole aria-hidden="true" className="size-4 text-brand-text-3" />
  if (state === 'blocked') return <XCircle aria-hidden="true" className="size-4 text-brand-err" />
  if (state === 'paused') return <PauseCircle aria-hidden="true" className="size-4 text-brand-warn" />
  return <CircleHelp aria-hidden="true" className={`size-4 ${state === 'active' ? 'text-brand-gold-2' : 'text-brand-warn'}`} />
}

function countLabel(stage: NirmanaCampaignStage): string | null {
  if (stage.earned === null || stage.required === null) return null
  return `${stage.earned} / ${stage.required}`
}

function StageBody({ stage, snapshot }: { stage: NirmanaCampaignStage; snapshot: NirmanaElevationSnapshotV2 }) {
  if (stage.kind === 'census' || stage.kind === 'foundation') return <FoundationStage stage={stage} snapshot={snapshot} />

  return <div className="space-y-2 text-sm text-brand-text-2">
    <p>Required gate: {stage.required_gate}</p>
    {stage.blocked_reason && <p className="text-brand-err">Blocked: {stage.blocked_reason}</p>}
    {stage.completed_at && <p>Accepted: <time dateTime={stage.completed_at}>{stage.completed_at}</time></p>}
  </div>
}

export function CampaignSpine({ snapshot }: { snapshot: NirmanaElevationSnapshotV2 }) {
  const [expanded, setExpanded] = useState<Set<NirmanaStageId>>(
    () => new Set(snapshot.campaign.current_stage ? [snapshot.campaign.current_stage] : []),
  )
  const stages = [...snapshot.stages].sort((left, right) => left.order - right.order)

  const toggle = (stageId: NirmanaStageId) => {
    setExpanded((open) => {
      const next = new Set(open)
      if (next.has(stageId)) next.delete(stageId)
      else next.add(stageId)
      return next
    })
  }

  return <section aria-labelledby="campaign-spine-heading" className="rounded-xl border border-brand-border bg-brand-surface p-4">
    <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
      <div><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-gold-1">Sequential state machine</p><h2 id="campaign-spine-heading" className="text-lg font-semibold text-brand-text-1">Campaign spine</h2></div>
      <p className="text-xs text-brand-text-3">Opening a stage is a local view preference, not execution state.</p>
    </div>
    <ol className="space-y-0" aria-label="Nirmāṇa campaign stages">
      {stages.map((stage, index) => {
        const open = expanded.has(stage.stage_id)
        const name = stageName(stage, snapshot)
        const panelId = `campaign-stage-${stage.stage_id}`
        const isCurrent = stage.stage_id === snapshot.campaign.current_stage
        const count = countLabel(stage)
        return <li key={stage.stage_id} className="relative pb-3 last:pb-0">
          <article className={`rounded-xl border bg-brand-bg ${isCurrent ? 'border-brand-gold-1/70' : 'border-brand-border'}`}>
            <button type="button" aria-expanded={open} aria-controls={panelId} onClick={() => toggle(stage.stage_id)} onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault()
                toggle(stage.stage_id)
              }
            }} className="flex w-full items-start gap-3 rounded-xl px-3 py-3 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold-1">
              <span className="mt-0.5 shrink-0">{open ? <ChevronDown aria-hidden="true" className="size-4 text-brand-gold-2" /> : <ChevronRight aria-hidden="true" className="size-4 text-brand-text-3" />}</span>
              <span className="min-w-0 flex-1">
                <span className="flex flex-wrap items-center gap-x-2 gap-y-1"><span className={`font-mono text-sm font-semibold ${isCurrent ? 'text-brand-gold-2' : 'text-brand-text-1'}`}>{name}</span><span className="flex items-center gap-1 text-xs text-brand-text-2">{statusIcon(stage.state)}{statusLabel(stage.state)}</span>{count && <span className="text-xs text-brand-text-3">{count}</span>}</span>
                {stage.state === 'locked' && <span className="mt-1 block text-xs text-brand-text-3">Prerequisite: {stage.required_gate}</span>}
                {stage.state === 'blocked' && stage.blocked_reason && <span className="mt-1 block text-xs text-brand-err">Blocked: {stage.blocked_reason}</span>}
              </span>
            </button>
            {open && <div id={panelId} className="border-t border-brand-border px-3 py-3"><StageBody stage={stage} snapshot={snapshot} /></div>}
          </article>
          {index < stages.length - 1 && <div aria-hidden="true" className="ml-5 h-3 border-l border-brand-border" />}
        </li>
      })}
    </ol>
  </section>
}
