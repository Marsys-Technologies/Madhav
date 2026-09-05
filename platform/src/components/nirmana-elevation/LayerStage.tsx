import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import type { WaveProgressCount } from '@/lib/nirmana-elevation/projection'
import { WaveLane } from './WaveLane'
import { WaveProgressBar } from './WaveProgressBar'
import { assetCompactLabel } from './vocab'

export function LayerStage({ layer, assets, onOpenAudit, waveProgress, showWaveProgressBar = true }: {
  layer: NirmanaElevationSnapshotV2['layers'][number]
  assets: NirmanaElevationSnapshotV2['assets']
  onOpenAudit: (assetId: string) => void
  waveProgress: WaveProgressCount[]
  /** LayerCard already renders this bar in its always-visible summary; set false there to avoid a duplicate. */
  showWaveProgressBar?: boolean
}) {
  const waves = [...layer.waves].sort((left, right) => left.wave_index - right.wave_index)
  const total = layer.assets_total
  const progressText = total === null
    ? 'Progress unknown — no layer total has been observed.'
    : `${layer.frozen} / ${total} assets frozen`

  return <div className="space-y-3">
    <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm text-brand-text-2">
      <p>Required gate: {layer.required_gate}</p>
      <p className="capitalize">{layer.state === 'unknown' ? 'No layer evidence yet' : layer.state}</p>
    </div>
    {showWaveProgressBar && <WaveProgressBar waveProgress={waveProgress} />}
    <div>
      <div
        role="progressbar"
        aria-label={`${layer.layer_id} · ${layer.layer_name} layer progress`}
        aria-valuemin={0}
        aria-valuenow={total === null ? undefined : layer.frozen}
        aria-valuemax={total ?? undefined}
        aria-valuetext={progressText}
        className="h-2 overflow-hidden rounded-full bg-brand-border"
      >
        <span className="block h-full rounded-full bg-brand-gold-2" style={{ width: total && total > 0 ? `${Math.min(100, (layer.frozen / total) * 100)}%` : '0%' }} />
      </div>
      <p className="mt-1 text-xs text-brand-text-3">{progressText}</p>
    </div>
    <ul aria-label="Asset state legend" className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-brand-text-3">
      {['Frozen', 'Active', 'Blocked', 'Eligible next', 'Locked', 'Unknown'].map((label) => <li key={label}>{label}</li>)}
    </ul>
    <section aria-label="Eligible-next preview" className="rounded-lg border border-brand-border bg-brand-surface p-3">
      <h4 className="text-xs font-semibold uppercase tracking-[0.12em] text-brand-text-2">Eligible-next preview</h4>
      {layer.eligible_next_asset_ids.length > 0
        ? <ul className="mt-2 flex flex-wrap gap-2">{layer.eligible_next_asset_ids.map((assetId) => {
          const asset = assets.find((candidate) => candidate.asset_id === assetId)
          return <li key={assetId} className="rounded border border-brand-border px-2 py-1 text-xs text-brand-gold-2">
            <span>{asset ? assetCompactLabel(asset) : 'Identity unavailable'}</span>
            <span className="ml-1 font-mono text-brand-text-3">({assetId})</span>
          </li>
        })}</ul>
        : <p className="mt-2 text-xs text-brand-text-3">No asset is evidenced as eligible next.</p>}
    </section>
    {waves.length > 0
      ? <div className="space-y-3">{waves.map((wave) => ['completed', 'locked', 'unknown'].includes(wave.state)
        ? <details key={wave.wave_index} className="rounded-xl border border-brand-border bg-brand-bg">
          <summary className="cursor-pointer px-3 py-3 text-sm font-semibold text-brand-gold-2">Wave {wave.wave_index} · {wave.state} · {wave.asset_ids.length} {wave.asset_ids.length === 1 ? 'asset' : 'assets'}</summary>
          <div className="px-3 pb-3"><WaveLane wave={wave} assets={assets} onOpenAudit={onOpenAudit} lockedBy={wave.state === 'locked' ? layer.required_gate : undefined} /></div>
        </details>
        : <WaveLane key={wave.wave_index} wave={wave} assets={assets} onOpenAudit={onOpenAudit} lockedBy={wave.state === 'locked' ? layer.required_gate : undefined} />)}</div>
      : <p className="text-sm text-brand-text-3">No waves are recorded for this layer.</p>}
  </div>
}
