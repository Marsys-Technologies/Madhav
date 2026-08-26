import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { assetCompactLabel } from './vocab'

const MILESTONE_LABELS: Record<NirmanaElevationSnapshotV2['assets'][number]['milestones'][number]['milestone_id'], string> = {
  analysed: 'Analysed',
  decision_accepted: 'Decision accepted',
  built_or_dispositioned: 'Built or dispositioned',
  deployed_and_executed: 'Deployed and executed',
  verified: 'Verified',
  frozen: 'Frozen',
}

function stateLabel(state: NirmanaElevationSnapshotV2['assets'][number]['milestones'][number]['state']): string {
  if (state === 'not_applicable') return 'not applicable'
  return state
}

function segmentClass(state: NirmanaElevationSnapshotV2['assets'][number]['milestones'][number]['state']): string {
  if (state === 'earned') return 'border-brand-ok/70 bg-brand-ok/25 text-brand-ok'
  if (state === 'current') return 'border-brand-gold-1 bg-brand-gold-1/25 text-brand-gold-1'
  if (state === 'not_applicable') return 'nirmana-milestone-hatched border-dashed border-brand-border bg-[repeating-linear-gradient(135deg,transparent,transparent_3px,rgba(148,163,184,0.18)_3px,rgba(148,163,184,0.18)_6px)] text-brand-text-3'
  return 'border-brand-border bg-brand-bg text-brand-text-3'
}

export function MilestoneBar({ asset }: { asset: NirmanaElevationSnapshotV2['assets'][number] }) {
  const earned = asset.milestones_earned
  const required = asset.milestones_required
  const hasCounters = earned !== null && required !== null
  const progressText = hasCounters
    ? `${earned} of ${required} required milestones earned`
    : 'Asset completion is not yet evidenced'
  const progressWidth = hasCounters && required > 0
    ? `${Math.min(100, (earned / required) * 100)}%`
    : '0%'

  return <div className="space-y-1.5">
    <div
      role="progressbar"
      aria-label={`${assetCompactLabel(asset)} asset completion`}
      aria-valuemin={0}
      aria-valuenow={earned ?? undefined}
      aria-valuemax={required ?? undefined}
      aria-valuetext={progressText}
      className="h-2 overflow-hidden rounded-full bg-brand-border"
    >
      <span className="block h-full rounded-full bg-brand-gold-2" style={{ width: progressWidth }} />
    </div>
    <ol className="grid grid-cols-6 gap-1" aria-label={`Milestones for ${asset.asset_id}`}>
      {asset.milestones.map((milestone) => {
        const label = MILESTONE_LABELS[milestone.milestone_id]
        const state = stateLabel(milestone.state)
        return <li key={milestone.milestone_id} aria-label={`${label}: ${state}`} className={`flex min-h-7 items-center justify-center rounded border text-center text-[9px] font-medium leading-tight ${segmentClass(milestone.state)}`}>
          <span className="sr-only">{label}: {state}</span>
          <span aria-hidden="true">{milestone.state === 'not_applicable' ? 'N/A' : label.slice(0, 1)}</span>
        </li>
      })}
    </ol>
    {hasCounters
      ? <p className="text-xs text-brand-text-2">{asset.milestones_earned} of {asset.milestones_required} required milestones</p>
      : <p className="text-xs text-brand-text-3">Milestone count unavailable</p>}
    {asset.milestones.some((milestone) => milestone.state === 'not_applicable') && <p className="text-xs text-brand-text-3">N/A milestones are <span>not applicable</span> and excluded from the required count.</p>}
  </div>
}
