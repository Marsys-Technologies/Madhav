import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { AssetCard } from './AssetCard'

export function WaveLane({ wave, assets, onOpenAudit, lockedBy }: {
  wave: NirmanaElevationSnapshotV2['layers'][number]['waves'][number]
  assets: NirmanaElevationSnapshotV2['assets']
  onOpenAudit: (assetId: string) => void
  lockedBy?: string
}) {
  const assetsById = new Map(assets.map((asset) => [asset.asset_id, asset]))
  const waveAssets = wave.asset_ids.flatMap((assetId) => {
    const asset = assetsById.get(assetId)
    return asset && asset.wave_index === wave.wave_index ? [asset] : []
  })

  return <section aria-label={`Wave ${wave.wave_index}`} role="group" className="rounded-xl border border-brand-border bg-brand-bg p-3">
    <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
      <h4 className="font-mono text-sm font-semibold text-brand-gold-2">Wave {wave.wave_index}</h4>
      <p className="text-xs capitalize text-brand-text-2">{wave.state}</p>
    </div>
    {wave.state === 'locked' && lockedBy && <p className="mb-3 text-xs text-brand-text-3">Locked by: {lockedBy}</p>}
    {waveAssets.length > 0
      ? <div className="grid gap-3 lg:grid-cols-2 xl:grid-cols-3">{waveAssets.map((asset) => <AssetCard key={asset.asset_id} asset={asset} onOpenAudit={onOpenAudit} />)}</div>
      : <p className="text-sm text-brand-text-3">No assets with a valid wave assignment are available.</p>}
  </section>
}
