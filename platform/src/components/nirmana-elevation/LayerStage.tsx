import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { WaveLane } from './WaveLane'

export function LayerStage({ layer, assets, onOpenAudit }: {
  layer: NirmanaElevationSnapshotV2['layers'][number]
  assets: NirmanaElevationSnapshotV2['assets']
  onOpenAudit: (assetId: string) => void
}) {
  const waves = [...layer.waves].sort((left, right) => left.wave_index - right.wave_index)

  return <div className="space-y-3">
    <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm text-brand-text-2">
      <p>Layer gate: {layer.required_gate}</p>
      <p className="capitalize">{layer.state}</p>
    </div>
    {waves.length > 0
      ? <div className="space-y-3">{waves.map((wave) => <WaveLane key={wave.wave_index} wave={wave} assets={assets} onOpenAudit={onOpenAudit} lockedBy={wave.state === 'locked' ? layer.required_gate : undefined} />)}</div>
      : <p className="text-sm text-brand-text-3">No waves are recorded for this layer.</p>}
  </div>
}
