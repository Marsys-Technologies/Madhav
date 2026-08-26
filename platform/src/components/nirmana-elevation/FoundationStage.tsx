import { AlertTriangle, CheckCircle2, CircleHelp, LockKeyhole } from 'lucide-react'
import type { NirmanaCampaignStage, NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'

function labelForState(state: string, blockedReason: string | null = null): string {
  if (state === 'unknown') return 'Unknown — acceptance checkpoints are not recorded'
  if (state === 'blocked') return blockedReason ? `Blocked — ${blockedReason}` : 'Blocked'
  if (state === 'locked') return 'Locked'
  return state.charAt(0).toUpperCase() + state.slice(1)
}

function LaneIcon({ state }: { state: string }) {
  if (state === 'completed') return <CheckCircle2 aria-hidden="true" className="size-4 text-brand-ok" />
  if (state === 'locked') return <LockKeyhole aria-hidden="true" className="size-4 text-brand-text-3" />
  if (state === 'blocked') return <AlertTriangle aria-hidden="true" className="size-4 text-brand-err" />
  return <CircleHelp aria-hidden="true" className="size-4 text-brand-warn" />
}

export function FoundationStage({ stage, snapshot }: { stage: NirmanaCampaignStage; snapshot: NirmanaElevationSnapshotV2 }) {
  if (stage.kind === 'census') {
    return <div className="grid gap-2 text-sm text-brand-text-2 sm:grid-cols-2">
      <p><span className="text-brand-text-3">Definition:</span> {snapshot.campaign.definition_revision ?? 'Unknown'}</p>
      <p><span className="text-brand-text-3">Definition status:</span> {snapshot.campaign.definition_status}</p>
      <p><span className="text-brand-text-3">Elevation denominator:</span> {snapshot.progress.denominator_status === 'frozen' ? `${snapshot.progress.assets_total ?? 'Unknown'} assets` : 'Reconciling — no percentage'}</p>
      <p><span className="text-brand-text-3">Required gate:</span> {stage.required_gate}</p>
    </div>
  }

  if (stage.kind !== 'foundation') {
    return <p className="text-sm text-brand-text-2">Required gate: {stage.required_gate}</p>
  }

  return <div>
    <p className="text-sm text-brand-text-2">Foundation lanes are shown only from typed acceptance evidence.</p>
    <ul className="mt-3 space-y-2" aria-label="Foundation lanes">
      {stage.foundation_lanes?.map((lane) => <li key={lane.lane_id} className="rounded-lg border border-brand-border bg-brand-bg px-3 py-2">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <p className="flex items-center gap-2 font-medium text-brand-text-1"><LaneIcon state={lane.state} /><span className="font-mono text-brand-gold-2">{lane.lane_id}</span>{lane.name}</p>
          <p className="text-xs text-brand-text-2">{labelForState(lane.state, lane.blocked_reason)}</p>
        </div>
      </li>)}
      {!stage.foundation_lanes && <li className="rounded-lg border border-dashed border-brand-border px-3 py-2 text-sm text-brand-text-3">Unknown — foundation lane acceptance evidence is unavailable.</li>}
    </ul>
  </div>
}
