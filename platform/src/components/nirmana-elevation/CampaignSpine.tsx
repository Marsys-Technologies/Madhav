'use client'

import { useState } from 'react'
import { CheckCircle2, ChevronDown, ChevronRight, CircleHelp, LockKeyhole, PauseCircle, XCircle } from 'lucide-react'
import { FoundationStage } from './FoundationStage'
import { LayerCard } from './LayerCard'
import { ProgrammeOverview } from './ProgrammeOverview'
import { ProvenanceChip } from './ProvenanceChip'
import type { NirmanaCampaignStage, NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import type { NirmanaStageId } from '@/lib/nirmana-elevation/projection'
import { POST_L5_STAGE_IDS, PRE_L0_STAGE_IDS } from '@/lib/nirmana-elevation/programme'
import { stageDisplayName } from './vocab'

function stageName(stage: NirmanaCampaignStage, snapshot: NirmanaElevationSnapshotV2): string {
  return stageDisplayName(stage.stage_id, snapshot)
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
  // A numeric counter is evidence, not a placeholder. In an unknown stage it
  // would imply that zero of a measured total has been completed.
  if (stage.state === 'unknown' || stage.earned === null || stage.required === null) return null
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

/** Sentinel toggle keys for the two collapsed-history summary rows (plan Ruling R1). */
type SpineGroupId = 'PHASE_A_GROUP' | 'PHASE_Z_GROUP'

/**
 * The pre-v2.1 sequential stage-machine rendering, preserved unchanged (same aria-expanded/
 * aria-controls/keyboard toggle pattern, FoundationStage dispatch, PHASE A/Z collapsed-group
 * summaries) inside a collapsed history drawer. Per plan Ruling R2, the per-layer L0-L5 rows
 * this used to render are dropped here — that live per-layer state now lives exclusively in
 * the six LayerCards above; `stages`/`projectCampaignStages` themselves stay untouched and
 * still carry the full 13-stage record for W6-ceremony/audit use, this view just stops
 * re-displaying the six layer rows a second time next to the cards that already show them.
 */
function StageMachineHistory({ snapshot }: { snapshot: NirmanaElevationSnapshotV2 }) {
  const [expanded, setExpanded] = useState<Set<NirmanaStageId | SpineGroupId>>(() => {
    const currentStage = snapshot.campaign.current_stage
    const initial = new Set<NirmanaStageId | SpineGroupId>()
    if (currentStage && PRE_L0_STAGE_IDS.includes(currentStage)) initial.add('PHASE_A_GROUP')
    if (currentStage && POST_L5_STAGE_IDS.includes(currentStage)) initial.add('PHASE_Z_GROUP')
    return initial
  })
  const stages = [...snapshot.stages].sort((left, right) => left.order - right.order)
  const phaseAStages = stages.filter((stage) => PRE_L0_STAGE_IDS.includes(stage.stage_id))
  const phaseZStages = stages.filter((stage) => POST_L5_STAGE_IDS.includes(stage.stage_id))

  const toggle = (stageId: NirmanaStageId | SpineGroupId) => {
    setExpanded((open) => {
      const next = new Set(open)
      if (next.has(stageId)) next.delete(stageId)
      else next.add(stageId)
      return next
    })
  }

  const renderStageItem = (stage: NirmanaCampaignStage, isLast: boolean) => {
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
            <span className="flex flex-wrap items-center gap-x-2 gap-y-1"><span className={`text-sm font-semibold ${isCurrent ? 'text-brand-gold-2' : 'text-brand-text-1'}`}>{name}</span><span className="flex items-center gap-1 text-xs text-brand-text-2">{statusIcon(stage.state)}{statusLabel(stage.state)}</span>{count && <span className="text-xs text-brand-text-3">{count}</span>}</span>
            <span className="mt-1 block font-mono text-[10px] text-brand-text-3">Stage ID: {stage.stage_id}</span>
            {stage.state === 'locked' && <span className="mt-1 block text-xs text-brand-text-3">Prerequisite: {stage.required_gate}</span>}
            {stage.state === 'blocked' && stage.blocked_reason && <span className="mt-1 block text-xs text-brand-err">Blocked: {stage.blocked_reason}</span>}
          </span>
        </button>
        {open && <div id={panelId} className="border-t border-brand-border px-3 py-3"><StageBody stage={stage} snapshot={snapshot} /></div>}
      </article>
      {!isLast && <div aria-hidden="true" className="ml-5 h-3 border-l border-brand-border" />}
    </li>
  }

  const renderGroupRow = (args: {
    groupId: SpineGroupId
    title: string
    state: NirmanaCampaignStage['state']
    memberStages: NirmanaCampaignStage[]
  }) => {
    const { groupId, title, state, memberStages } = args
    const open = expanded.has(groupId)
    const panelId = `campaign-group-${groupId}`
    return <li className="relative pb-3 last:pb-0">
      <article className="rounded-xl border border-brand-border bg-brand-bg">
        <button type="button" aria-expanded={open} aria-controls={panelId} onClick={() => toggle(groupId)} onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            toggle(groupId)
          }
        }} className="flex w-full items-start gap-3 rounded-xl px-3 py-3 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold-1">
          <span className="mt-0.5 shrink-0">{open ? <ChevronDown aria-hidden="true" className="size-4 text-brand-gold-2" /> : <ChevronRight aria-hidden="true" className="size-4 text-brand-text-3" />}</span>
          <span className="min-w-0 flex-1">
            <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <span className="text-sm font-semibold text-brand-text-1">{title}</span>
              <span className="flex items-center gap-1 text-xs text-brand-text-2">{statusIcon(state)}{statusLabel(state)}</span>
              <ProvenanceChip kind="evidence_derived" />
            </span>
            <span className="mt-1 block text-xs text-brand-text-3">{memberStages.length} collapsed {memberStages.length === 1 ? 'stage' : 'stages'}</span>
          </span>
        </button>
        {open && <div id={panelId} className="border-t border-brand-border px-3 py-3">
          <ol className="space-y-0">{memberStages.map((stage, index) => renderStageItem(stage, index === memberStages.length - 1))}</ol>
        </div>}
      </article>
    </li>
  }

  return <details className="rounded-xl border border-brand-border bg-brand-surface p-4">
    <summary className="cursor-pointer text-sm font-semibold text-brand-text-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold-1">
      Stage-machine history (13-stage record + Phase A drawer)
    </summary>
    <p className="mt-2 text-xs text-brand-text-3">Opening a stage is a local view preference, not execution state. Per-layer state now lives in the six layer cards above; this record retains the full stage-transition history for governance and freeze-ceremony use.</p>
    <div className="mt-3 space-y-4">
      <section aria-label="Phase A">
        <ol className="space-y-0" aria-label="Phase A stages">
          {renderGroupRow({ groupId: 'PHASE_A_GROUP', title: 'PHASE A', state: snapshot.programme.phase_a.state, memberStages: phaseAStages })}
        </ol>
      </section>
      <section aria-label="O-Wave">
        <ol className="space-y-0" aria-label="O-Wave work packages">
          <li className="relative pb-3 last:pb-0">
            <article className="rounded-xl border border-brand-border bg-brand-bg px-3 py-3">
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <h3 className="text-sm font-semibold text-brand-text-1">O-WAVE</h3>
                <span className="flex items-center gap-1 text-xs text-brand-text-2">{statusIcon(snapshot.programme.o_wave.state)}{statusLabel(snapshot.programme.o_wave.state)}</span>
                <ProvenanceChip kind="repo_declared" />
              </div>
              <ul className="mt-2 space-y-1 text-xs text-brand-text-2">
                {snapshot.programme.o_wave.wps.map((wp) => <li key={wp.wp_id}>{wp.name}: {wp.status}</li>)}
              </ul>
            </article>
          </li>
        </ol>
      </section>
      <section aria-label="Phase Z">
        <ol className="space-y-0" aria-label="Phase Z stages">
          {renderGroupRow({ groupId: 'PHASE_Z_GROUP', title: 'PHASE Z', state: snapshot.programme.phase_z.state, memberStages: phaseZStages })}
        </ol>
      </section>
    </div>
  </details>
}

export function CampaignSpine({ snapshot, onOpenAudit = () => {} }: { snapshot: NirmanaElevationSnapshotV2; onOpenAudit?: (assetId: string) => void }) {
  // Same fallback the pre-v2.1 spine used: default to L0 when no current stage is evidenced,
  // otherwise open whichever layer is currently governed as "current" (a display default —
  // nothing here gates or locks any other layer; all six cards always render, per Ruling R2).
  const currentStage = snapshot.campaign.current_stage
  const defaultOpenLayerId = currentStage && /^L[0-5]$/.test(currentStage) ? currentStage : 'L0'

  return <section aria-labelledby="campaign-spine-heading" className="space-y-4">
    <div><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-gold-1">Nirmāṇa campaign</p><h2 id="campaign-spine-heading" className="text-lg font-semibold text-brand-text-1">Campaign spine</h2></div>

    <ProgrammeOverview snapshot={snapshot} />

    <section aria-labelledby="layer-cards-heading" className="rounded-xl border border-brand-border bg-brand-surface p-4">
      <div className="mb-3"><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-gold-1">All six layers run concurrently — nothing here is locked</p><h3 id="layer-cards-heading" className="text-sm font-semibold text-brand-text-1">Layers</h3></div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {snapshot.layers.map((layer) => <LayerCard
          key={layer.layer_id}
          layer={layer}
          assets={snapshot.assets}
          onOpenAudit={onOpenAudit}
          defaultOpen={layer.layer_id === defaultOpenLayerId}
        />)}
      </div>
    </section>

    <StageMachineHistory snapshot={snapshot} />
  </section>
}
