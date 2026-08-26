import { AlertTriangle, CheckCircle2, CircleHelp, XCircle } from 'lucide-react'
import type { NirmanaElevationSnapshotV1 } from '@/lib/nirmana-elevation/types'

export const NIRMANA_V1_PUBLIC_SOURCE_ERROR = 'Authoritative source is unavailable.'
export const NIRMANA_V1_PUBLIC_ASSET_BLOCKER = 'Accepted asset execution requires attention.'

function statusText(value: string | null | undefined): string {
  if (!value) return 'Unknown'
  return value.replace(/[_-]/g, ' ')
}

function formatTime(value: string | Date | null | undefined): string {
  if (!value) return 'Unknown'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.valueOf())) return 'Unknown'
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(date)
}

function formatSeconds(value: number | null): string {
  if (value === null) return 'Unknown'
  if (value < 60) return `${value}s`
  const minutes = Math.floor(value / 60)
  const seconds = Math.round(value % 60)
  return seconds ? `${minutes}m ${seconds}s` : `${minutes}m`
}

function StatusMark({ state }: { state: string | null | undefined }) {
  const normalized = state?.toLowerCase() ?? 'unknown'
  const isGood = ['fresh', 'frozen', 'completed', 'reliable', 'in_sync', 'open'].includes(normalized)
  const isBad = ['blocked', 'unavailable', 'failed', 'error', 'degraded'].includes(normalized)
  const Icon = isGood ? CheckCircle2 : isBad ? XCircle : CircleHelp
  const tone = isGood ? 'text-brand-ok' : isBad ? 'text-brand-err' : 'text-brand-warn'

  return <Icon aria-hidden="true" className={`size-4 shrink-0 ${tone}`} />
}

function DataChip({ label, value, state }: { label: string; value: React.ReactNode; state?: string | null }) {
  return <div className="min-w-0 rounded-lg border border-brand-border bg-brand-surface px-3 py-2">
    <dt className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-text-3">
      {state !== undefined && <StatusMark state={state} />}
      {label}
    </dt>
    <dd className="mt-1 truncate text-sm font-medium text-brand-text-1">{value}</dd>
  </div>
}

function TruthStrip({ snapshot, fetchedAt }: { snapshot: NirmanaElevationSnapshotV1; fetchedAt: Date }) {
  const { campaign, release, data_quality: quality, progress } = snapshot
  const releaseState = release.production_in_sync === true ? 'fresh' : release.production_in_sync === false ? 'blocked' : 'unknown'

  return <section aria-labelledby="tracker-truth-strip" className="rounded-xl border border-brand-border bg-brand-surface p-4">
    <div className="mb-3 flex flex-wrap items-end justify-between gap-3 border-b border-brand-border pb-3">
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-gold-1">Live evidence projection</p>
        <h1 id="tracker-truth-strip" className="font-serif text-3xl font-medium tracking-wide text-brand-gold-cream">Nirmāṇa Elevation Tracker</h1>
      </div>
      <p className="text-xs text-brand-text-3">Fetched <time dateTime={fetchedAt.toISOString()} title={fetchedAt.toISOString()}>{formatTime(fetchedAt)}</time></p>
    </div>
    <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
      <DataChip label="Campaign" value={statusText(campaign.campaign_status)} state={campaign.campaign_status} />
      <DataChip label="Definition" value={campaign.definition_revision ?? 'Unversioned'} state={campaign.definition_status} />
      <DataChip label="Current position" value={campaign.current_layer ? `${campaign.current_layer} · Wave ${campaign.current_wave ?? 'unknown'}` : 'Unknown'} state={campaign.current_layer ? 'open' : 'unknown'} />
      <DataChip label="Data quality" value={statusText(quality.verdict)} state={quality.verdict} />
      <DataChip label="Production / main" value={release.production_in_sync === true ? 'In sync' : release.production_in_sync === false ? 'Out of sync' : 'Unknown'} state={releaseState} />
      <DataChip label="Deployed revision" value={release.deployed_revision ?? 'Unknown'} state={releaseState} />
      <DataChip label="Elevation denominator" value={progress.denominator_status === 'frozen' ? `${progress.assets_total ?? 'Unknown'} assets frozen` : 'Reconciling — no percentage'} state={progress.denominator_status === 'frozen' ? 'fresh' : 'unknown'} />
    </dl>
    {(quality.gaps.length > 0 || quality.contradictions.length > 0) && <div className="mt-3 rounded-md border border-brand-warn/40 bg-brand-warn/10 px-3 py-2 text-sm text-brand-text-2">
      <p className="flex items-center gap-2 font-medium text-brand-text-1"><AlertTriangle aria-hidden="true" className="size-4 text-brand-warn" /> Evidence caveats</p>
      <ul className="mt-1 list-disc space-y-1 pl-5">{[...quality.gaps, ...quality.contradictions].map((item) => <li key={item}>{item}</li>)}</ul>
    </div>}
  </section>
}

function LayerRail({ snapshot }: { snapshot: NirmanaElevationSnapshotV1 }) {
  const layers = [...snapshot.layers].sort((a, b) => a.order - b.order)
  return <section aria-labelledby="layer-rail-heading" className="rounded-xl border border-brand-border bg-brand-surface p-4">
    <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
      <div><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-gold-1">Ordered workflow</p><h2 id="layer-rail-heading" className="text-lg font-semibold text-brand-text-1">Sequential layer rail</h2></div>
      <span className="text-xs text-brand-text-3">{snapshot.progress.layers_frozen} of {snapshot.progress.layers_total} layers frozen</span>
    </div>
    <ol className="grid gap-3 md:grid-cols-6" aria-label="Nirmāṇa layers L0 through L5">
      {layers.map((layer) => <li key={layer.layer_id} className="relative rounded-lg border border-brand-border bg-brand-bg p-3">
        <div className="flex items-center justify-between gap-2"><h3 className="font-mono text-sm font-semibold text-brand-gold-2">{layer.layer_id}</h3><span className="flex items-center gap-1 text-xs capitalize text-brand-text-2"><StatusMark state={layer.state} />{statusText(layer.state)}</span></div>
        <dl className="mt-3 grid grid-cols-2 gap-x-2 gap-y-2 text-xs">
          <div><dt className="text-brand-text-3">Total</dt><dd className="font-medium text-brand-text-1">{layer.assets_total ?? 'Reconciling'}</dd></div>
          <div><dt className="text-brand-text-3">Reviewed</dt><dd className="font-medium text-brand-text-1">{layer.optimization_reviewed}</dd></div>
          <div><dt className="text-brand-text-3">Rebuilt / dispositioned</dt><dd className="font-medium text-brand-text-1">{layer.rebuilt_or_dispositioned}</dd></div>
          <div><dt className="text-brand-text-3">Verified</dt><dd className="font-medium text-brand-text-1">{layer.verified}</dd></div>
          <div><dt className="text-brand-text-3">Frozen</dt><dd className="font-medium text-brand-text-1">{layer.frozen}</dd></div>
        </dl>
      </li>)}
    </ol>
  </section>
}

function WaveAssets({ label, ids }: { label: string; ids: string[] }) {
  return <div><dt className="text-[10px] font-semibold uppercase tracking-[0.14em] text-brand-text-3">{label} · {ids.length}</dt><dd className="mt-1 break-words font-mono text-xs text-brand-text-1">{ids.length ? ids.join(', ') : 'None'}</dd></div>
}

function WaveBoard({ snapshot }: { snapshot: NirmanaElevationSnapshotV1 }) {
  const currentLayer = snapshot.campaign.current_layer
  const layer = snapshot.layers.find((candidate) => candidate.layer_id === currentLayer) ?? snapshot.layers.find((candidate) => candidate.state === 'open')
  const assetsById = new Map(snapshot.assets.map((asset) => [asset.asset_id, asset]))

  if (!layer) return <section aria-labelledby="waves-heading" className="rounded-xl border border-brand-border bg-brand-surface p-4"><h2 id="waves-heading" className="text-lg font-semibold text-brand-text-1">Current-layer waves</h2><p className="mt-2 text-sm text-brand-text-3">Current layer is unknown; no wave claim is displayed.</p></section>

  return <section aria-labelledby="waves-heading" className="rounded-xl border border-brand-border bg-brand-surface p-4">
    <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2"><div><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-gold-1">Concurrency-aware execution</p><h2 id="waves-heading" className="text-lg font-semibold text-brand-text-1">Current-layer waves · {layer.layer_id}</h2></div><span className="text-xs text-brand-text-3">Only committed asset states are shown.</span></div>
    <div className="space-y-3">{layer.waves.length === 0 ? <p className="rounded-md border border-dashed border-brand-border p-4 text-sm text-brand-text-3">No waves have been recorded for this layer.</p> : layer.waves.map((wave) => {
      const active = new Set(wave.active_asset_ids)
      const blocked = new Set(wave.blocked_asset_ids)
      const completed = wave.asset_ids.filter((id) => assetsById.get(id)?.lifecycle_state === 'frozen')
      const pendingOrUnreported = wave.asset_ids.filter((id) => !active.has(id) && !blocked.has(id) && !completed.includes(id))
      return <article key={wave.wave_index} className="rounded-lg border border-brand-border bg-brand-bg p-3" aria-label={`Wave ${wave.wave_index}`}>
        <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-mono text-sm font-semibold text-brand-gold-2">Wave {wave.wave_index}</h3><span className="flex items-center gap-1 text-xs capitalize text-brand-text-2"><StatusMark state={wave.state} />{statusText(wave.state)}</span></div>
        <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4"><WaveAssets label="Pending / unreported" ids={pendingOrUnreported} /><WaveAssets label="Active" ids={wave.active_asset_ids} /><WaveAssets label="Blocked" ids={wave.blocked_asset_ids} /><WaveAssets label="Completed" ids={completed} /></dl>
      </article>
    })}</div>
  </section>
}

function AssetLedger({ snapshot }: { snapshot: NirmanaElevationSnapshotV1 }) {
  return <section aria-labelledby="ledger-heading" className="rounded-xl border border-brand-border bg-brand-surface p-4">
    <div className="mb-4"><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-gold-1">Primary evidence references</p><h2 id="ledger-heading" className="text-lg font-semibold text-brand-text-1">Asset evidence ledger</h2></div>
    <div className="overflow-x-auto rounded-lg border border-brand-border"><table className="min-w-[920px] w-full text-left text-xs">
      <caption className="sr-only">Asset execution and evidence state</caption>
      <thead className="bg-brand-bg text-brand-text-3"><tr><th scope="col" className="px-3 py-2 font-medium">Asset</th><th scope="col" className="px-3 py-2 font-medium">Position</th><th scope="col" className="px-3 py-2 font-medium">Obligation</th><th scope="col" className="px-3 py-2 font-medium">State</th><th scope="col" className="px-3 py-2 font-medium">Truthful progress</th><th scope="col" className="px-3 py-2 font-medium">Timing</th><th scope="col" className="px-3 py-2 font-medium">Evidence</th></tr></thead>
      <tbody className="divide-y divide-brand-border">{snapshot.assets.map((asset) => <tr key={asset.asset_id} className="align-top hover:bg-brand-bg/70">
        <td className="px-3 py-3"><p className="font-medium text-brand-text-1">{asset.display_name}</p><p className="mt-0.5 font-mono text-brand-text-3">{asset.asset_id}</p></td>
        <td className="px-3 py-3 text-brand-text-2"><p>{asset.layer} · Wave {asset.wave_index ?? 'unassigned'}</p><p className="mt-0.5 font-mono text-brand-text-3">{asset.producer_id ?? 'No producer recorded'}</p></td>
        <td className="px-3 py-3 capitalize text-brand-text-2">{statusText(asset.execution_obligation)}</td>
        <td className="px-3 py-3"><p className="flex items-center gap-1 text-brand-text-1"><StatusMark state={asset.lifecycle_state} />{statusText(asset.lifecycle_state)}</p><p className="mt-1 text-brand-text-3">Readiness: {statusText(asset.readiness_state)}</p><p className="mt-1 text-brand-text-3">Run: {statusText(asset.current_run_state)}</p></td>
        <td className="px-3 py-3 text-brand-text-2">{asset.progress_mode === 'determinate' && asset.work_committed !== null && asset.work_total !== null ? `${asset.work_committed} / ${asset.work_total} ${asset.current_unit_label ?? 'units'}` : asset.progress_mode === 'indeterminate' ? `Indeterminate — ${asset.current_unit_label ?? 'stage not instrumented'}` : 'Not applicable'}{asset.blocker && <p className="mt-1 flex max-w-48 items-start gap-1 text-brand-err"><AlertTriangle aria-hidden="true" className="mt-0.5 size-3 shrink-0" />{NIRMANA_V1_PUBLIC_ASSET_BLOCKER}</p>}</td>
        <td className="px-3 py-3 text-brand-text-2"><p>Baseline: {formatSeconds(asset.baseline_duration_seconds)}</p><p className="mt-1">Final: {formatSeconds(asset.final_duration_seconds)}</p><p className="mt-1">Improvement: {asset.improvement_percent === null ? 'Unknown' : `${asset.improvement_percent} points`}</p></td>
        <td className="px-3 py-3"><details><summary className="cursor-pointer text-brand-gold-2 underline underline-offset-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold-1">Evidence ({asset.evidence_refs.length})</summary><ul className="mt-2 space-y-1 font-mono text-brand-text-3">{asset.evidence_refs.length ? asset.evidence_refs.map((ref) => <li key={ref}>{ref}</li>) : <li>No evidence references recorded</li>}</ul></details></td>
      </tr>)}</tbody>
    </table></div>
  </section>
}

function Sources({ snapshot }: { snapshot: NirmanaElevationSnapshotV1 }) {
  return <section aria-labelledby="sources-heading" className="rounded-xl border border-brand-border bg-brand-surface p-4"><h2 id="sources-heading" className="text-sm font-semibold text-brand-text-1">Source evidence and release observation</h2><div className="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-3">{snapshot.sources.map((source) => <div key={source.source_id} className="rounded-md border border-brand-border bg-brand-bg p-3"><p className="flex items-center gap-1.5 text-sm font-medium text-brand-text-1"><StatusMark state={source.state} />{source.source_id}</p><p className="mt-1 text-xs text-brand-text-3">{source.provenance} · observed {formatTime(source.observed_at)}</p>{source.error && <p className="mt-1 text-xs text-brand-err">{NIRMANA_V1_PUBLIC_SOURCE_ERROR}</p>}</div>)}</div><p className="mt-3 text-xs text-brand-text-3">Main SHA: <span className="font-mono">{snapshot.release.main_sha ?? 'Unknown'}</span> · Deployed SHA: <span className="font-mono">{snapshot.release.deployed_sha ?? 'Unknown'}</span> · observed {formatTime(snapshot.release.observed_at)}</p></section>
}

export function NirmanaElevationTrackerV1({ snapshot, fetchedAt }: { snapshot: NirmanaElevationSnapshotV1; fetchedAt: Date }) {
  return <>
    <aside role="status" className="rounded-xl border border-brand-warn/50 bg-brand-warn/10 px-4 py-3 text-sm text-brand-text-2">Tracker upgrade pending — showing schema v1 evidence view.</aside>
    <TruthStrip snapshot={snapshot} fetchedAt={fetchedAt} />
    <LayerRail snapshot={snapshot} />
    <WaveBoard snapshot={snapshot} />
    <AssetLedger snapshot={snapshot} />
    <Sources snapshot={snapshot} />
  </>
}
