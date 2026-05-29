'use client'

import AssetNode, { AssetNodeData } from './AssetNode'

interface AssetNodeGridProps {
  assets: AssetNodeData[]
  onAssetClick?: (data: AssetNodeData) => void
}

export default function AssetNodeGrid({ assets, onAssetClick }: AssetNodeGridProps) {
  return (
    <div
      className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 p-4"
      data-testid="asset-node-grid"
    >
      {assets.map(asset => (
        <AssetNode key={asset.asset_id} data={asset} onClick={onAssetClick} />
      ))}
    </div>
  )
}
