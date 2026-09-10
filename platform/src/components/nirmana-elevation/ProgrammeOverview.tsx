import { CheckCircle2, CircleDashed, CircleDot } from 'lucide-react'
import { PROGRAMME_ARC_PHASES } from '@/lib/nirmana-elevation/programme'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { ProvenanceChip } from './ProvenanceChip'

type ArcPhase = NirmanaElevationSnapshotV2['programme']['arc'][number]
type OWave = NirmanaElevationSnapshotV2['programme']['o_wave']
type WpRow = OWave['wps'][number]

const ARC_LABELS: Partial<Record<ArcPhase['phase_id'], string>> = Object.fromEntries(
  PROGRAMME_ARC_PHASES.map((phase) => [phase.phase_id, phase.label]),
)

function arcStateLabel(state: string): string {
  return state.charAt(0).toUpperCase() + state.slice(1).replace(/_/g, ' ')
}

function ArcStateIcon({ state }: { state: string }) {
  if (state === 'completed') return <CheckCircle2 aria-hidden="true" className="size-3.5 text-brand-ok" />
  if (state === 'pending') return <CircleDashed aria-hidden="true" className="size-3.5 text-brand-text-3" />
  return <CircleDot aria-hidden="true" className="size-3.5 text-brand-gold-2" />
}

function wpLine(wp: WpRow, tag?: string): string {
  const pr = wp.merged_pr ? ` · PR #${wp.merged_pr.number}` : ''
  return `${wp.name}: ${wp.status}${pr}${tag ? ` (${tag})` : ''}`
}

function ArcChipHeader({ phase }: { phase: ArcPhase }) {
  return <span className="flex flex-wrap items-center gap-1.5">
    <ArcStateIcon state={phase.state} />
    <span className="text-xs font-semibold text-brand-text-1">{ARC_LABELS[phase.phase_id] ?? phase.phase_id}</span>
    <span className="text-[11px] text-brand-text-2">{arcStateLabel(phase.state)}</span>
    <ProvenanceChip kind={phase.provenance} />
  </span>
}

function OWaveChip({ phase, oWave }: { phase: ArcPhase; oWave: OWave }) {
  return <details className="min-w-[11rem] rounded-lg border border-brand-border bg-brand-bg px-2.5 py-2">
    <summary className="cursor-pointer list-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold-1">
      <ArcChipHeader phase={phase} />
    </summary>
    <ul className="mt-2 space-y-1 text-xs text-brand-text-2">
      {oWave.wps.map((wp) => <li key={wp.wp_id}>{wpLine(wp)}</li>)}
      {oWave.addenda.map((wp) => <li key={wp.wp_id}>{wpLine(wp, 'post-wave addendum')}</li>)}
    </ul>
  </details>
}

function ArcChip({ phase }: { phase: ArcPhase }) {
  return <div className="min-w-[11rem] rounded-lg border border-brand-border bg-brand-bg px-2.5 py-2" title={phase.note}>
    <ArcChipHeader phase={phase} />
  </div>
}

export function ProgrammeOverview({ snapshot }: { snapshot: NirmanaElevationSnapshotV2 }) {
  const { overall, excluded_assets: excludedAssets, arc, o_wave } = snapshot.programme
  const percent = overall.percent
  const { assets_frozen: frozenTotal, assets_total: assetsTotal } = snapshot.progress

  return <section aria-labelledby="programme-overview-heading" className="rounded-xl border border-brand-border bg-brand-surface p-4">
    <div className="mb-3">
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-gold-1">Asset elevation — overall</p>
      <h2 id="programme-overview-heading" className="text-lg font-semibold text-brand-text-1">Overall programme completion</h2>
    </div>

    <div className="flex flex-wrap items-baseline gap-3">
      <span className="font-serif text-3xl font-medium text-brand-gold-cream">{percent === null ? '—' : `${percent}%`}</span>
      <span className="text-sm text-brand-text-2">asset elevation</span>
    </div>
    <div
      role="progressbar"
      aria-label="Overall asset elevation completion"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={percent ?? undefined}
      data-progress-state={percent === null ? 'indeterminate' : 'determinate'}
      className="mt-2 h-2.5 overflow-hidden rounded-full bg-brand-border"
    >
      <span className="block h-full rounded-full bg-brand-gold-2" style={{ width: percent === null ? '0%' : `${percent}%` }} />
    </div>
    {/* Distinctly worded from CampaignSnapshotStrip's "Current position" metric (which renders
        `programme.position_label` verbatim) even though both draw on the same underlying
        counts — the two surfaces intentionally never repeat identical text on the page. */}
    <p className="mt-1 text-xs text-brand-text-3">{overall.earned} of {overall.required} required milestones earned · {frozenTotal} of {assetsTotal ?? '—'} assets frozen. 100% is asset elevation complete, not campaign close — Phase Z close-out follows.</p>
    {/* Fix 5: without this, the bar can read 100% while the frozen count is (128-K)/128 for
        assets excluded from the denominator because their obligation never resolved a
        milestone count — the reader has no way to know K exists. */}
    {excludedAssets !== null && excludedAssets > 0 && (
      <p className="mt-1 text-xs text-brand-text-3">{excludedAssets} {excludedAssets === 1 ? 'asset' : 'assets'} excluded (obligation unresolved)</p>
    )}

    <div className="mt-4 flex flex-wrap gap-2" aria-label="Programme arc">
      {arc.map((phase) => phase.phase_id === 'O_WAVE'
        ? <OWaveChip key={phase.phase_id} phase={phase} oWave={o_wave} />
        : <ArcChip key={phase.phase_id} phase={phase} />)}
    </div>
  </section>
}
