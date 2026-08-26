import { AlertTriangle, CheckCircle2, CircleHelp, Radio } from 'lucide-react'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'

function formatObservedAt(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.valueOf())) return 'Unknown'
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function stagePosition(snapshot: NirmanaElevationSnapshotV2): string {
  const stageId = snapshot.campaign.current_stage
  if (!stageId) return 'Current position unknown'
  if (!/^L[0-5]$/.test(stageId)) return stageId

  const layer = snapshot.layers.find((candidate) => candidate.layer_id === stageId)
  const wave = snapshot.campaign.current_wave
  return `${stageId} · ${layer?.layer_name ?? 'Unknown'}${wave === null ? '' : ` · Wave ${wave}`}`
}

function activeAssetCount(snapshot: NirmanaElevationSnapshotV2): number {
  return new Set(snapshot.active_runs.flatMap((run) => run.active_asset_ids)).size
}

function Metric({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="min-w-0 rounded-lg border border-brand-border bg-brand-bg px-3 py-3">
    <dt className="text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-text-3">{label}</dt>
    <dd className="mt-1 text-sm font-medium text-brand-text-1">{children}</dd>
  </div>
}

export function CampaignSnapshotStrip({ snapshot }: { snapshot: NirmanaElevationSnapshotV2 }) {
  const currentLayer = snapshot.campaign.current_stage && /^L[0-5]$/.test(snapshot.campaign.current_stage)
    ? snapshot.layers.find((layer) => layer.layer_id === snapshot.campaign.current_stage)
    : undefined
  const activeAssets = activeAssetCount(snapshot)
  const denominator = snapshot.progress.denominator_status === 'frozen'
    && snapshot.progress.assets_total !== null
    ? `${snapshot.progress.assets_frozen} / ${snapshot.progress.assets_total}`
    : 'Reconciling — no percentage'
  const caveats = [...snapshot.data_quality.gaps, ...snapshot.data_quality.contradictions]

  return <section aria-labelledby="campaign-snapshot-heading" className="rounded-xl border border-brand-border bg-brand-surface p-4">
    <div className="mb-3 flex flex-wrap items-end justify-between gap-3 border-b border-brand-border pb-3">
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-gold-1">Evidence projection</p>
        <h1 id="campaign-snapshot-heading" className="font-serif text-2xl font-medium text-brand-gold-cream">Nirmāṇa campaign</h1>
      </div>
      <p className="flex items-center gap-1.5 text-xs text-brand-text-3"><Radio aria-hidden="true" className="size-3.5" />Observed {formatObservedAt(snapshot.generated_at)}</p>
    </div>

    <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
      <Metric label="Current position">{stagePosition(snapshot)}</Metric>
      <Metric label="Overall elevation">{denominator}</Metric>
      <Metric label="Active now">{activeAssets === 1 ? '1 asset active' : `${activeAssets} assets active`}</Metric>
      <Metric label="Eligible now">{currentLayer
        ? <><span className="block">{currentLayer.eligible_next_asset_ids.length === 1 ? '1 asset eligible now' : `${currentLayer.eligible_next_asset_ids.length} assets eligible now`}</span><span className="mt-1 block text-xs font-normal text-brand-text-3">Completion prerequisite: {currentLayer.required_gate}</span></>
        : 'Unknown — no active layer'}</Metric>
      <Metric label="Freshness"><time dateTime={snapshot.generated_at}>{formatObservedAt(snapshot.generated_at)}</time></Metric>
    </dl>

    {(snapshot.data_quality.verdict !== 'reliable' || caveats.length > 0 || snapshot.release.production_in_sync === false) && (
      <aside role="status" className="mt-3 flex gap-2 rounded-lg border border-brand-warn/50 bg-brand-bg px-3 py-2 text-sm text-brand-text-2">
        {snapshot.data_quality.verdict === 'reliable' && snapshot.release.production_in_sync !== false
          ? <CheckCircle2 aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-brand-ok" />
          : <AlertTriangle aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-brand-warn" />}
        <div>
          <p className="font-medium text-brand-text-1">{snapshot.data_quality.verdict === 'reliable' ? 'Release attention' : `Data quality: ${snapshot.data_quality.verdict}`}</p>
          {snapshot.release.production_in_sync === false && <p>Production is not in sync with main.</p>}
          {caveats.map((caveat) => <p key={caveat}>{caveat}</p>)}
        </div>
      </aside>
    )}
    {snapshot.data_quality.verdict === 'unknown' && <p className="sr-only"><CircleHelp aria-hidden="true" /> Evidence quality is unknown.</p>}
  </section>
}
