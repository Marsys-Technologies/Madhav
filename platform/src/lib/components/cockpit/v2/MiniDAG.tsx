'use client'

import { motion } from 'framer-motion'

interface AssetNode {
  asset_id: string
  sanskrit_name: string
  english_name: string
  depends_on?: string[] | null
}

interface MiniDAGProps {
  targetAssetId: string
  planAssetIds: string[]
  assets: AssetNode[]
}

function buildLayers(targetId: string, inPlan: Set<string>, assets: AssetNode[]): string[][] {
  // BFS from target downward through depends_on relationships (reversed: who depends on target?)
  // The plan is topological: target first, then downstream dependents.
  // Build layers: target at top, then assets that depend on it, then assets that depend on those, etc.
  const assetMap = new Map(assets.map(a => [a.asset_id, a]))
  const layers: string[][] = [[targetId]]
  const placed = new Set([targetId])
  const remaining = [...inPlan].filter(id => id !== targetId)

  // Iteratively find assets whose all depends_on (that are in the plan) are already placed
  let iterations = 0
  while (remaining.length > 0 && iterations < 20) {
    iterations++
    const nextLayer: string[] = []
    const stillRemaining: string[] = []
    for (const id of remaining) {
      const asset = assetMap.get(id)
      const deps = (asset?.depends_on ?? []).filter(d => inPlan.has(d))
      if (deps.every(d => placed.has(d))) {
        nextLayer.push(id)
      } else {
        stillRemaining.push(id)
      }
    }
    if (nextLayer.length === 0) {
      // Cycle or unresolvable — dump remainder in a final layer
      layers.push(stillRemaining)
      break
    }
    nextLayer.forEach(id => placed.add(id))
    layers.push(nextLayer)
    remaining.splice(0, remaining.length, ...stillRemaining)
  }

  return layers
}

export function MiniDAG({ targetAssetId, planAssetIds, assets }: MiniDAGProps) {
  const inPlan = new Set(planAssetIds)
  const planAssets = assets.filter(a => inPlan.has(a.asset_id))

  // Build edges within the plan closure
  type Edge = { from: string; to: string }
  const edges: Edge[] = []
  for (const asset of planAssets) {
    for (const dep of (asset.depends_on ?? [])) {
      if (inPlan.has(dep)) {
        edges.push({ from: dep, to: asset.asset_id })
      }
    }
  }

  const layers = buildLayers(targetAssetId, inPlan, planAssets)

  const W = 380
  const H = Math.max(160, 40 + layers.length * 70)
  const layerY = (i: number) => 36 + i * 70
  const nodeX = (idx: number, count: number) => (W / (count + 1)) * (idx + 1)

  // Build position map for edge rendering
  const posMap = new Map<string, { x: number; y: number }>()
  layers.forEach((layer, li) => {
    layer.forEach((id, idx) => {
      posMap.set(id, { x: nodeX(idx, layer.length), y: layerY(li) })
    })
  })

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Rebuild closure DAG">
      <defs>
        <radialGradient id="miniRootBead" cx="32%" cy="28%" r="85%">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="25%" stopColor="#FFF8E0" />
          <stop offset="65%" stopColor="#ECC56A" />
          <stop offset="100%" stopColor="#7A5618" />
        </radialGradient>
        <radialGradient id="miniNodeBead" cx="35%" cy="30%" r="75%">
          <stop offset="0%" stopColor="#FFFBE8" />
          <stop offset="55%" stopColor="#EFE0BC" />
          <stop offset="100%" stopColor="#A47A28" />
        </radialGradient>
      </defs>

      {/* Edges */}
      {edges.map((e, i) => {
        const from = posMap.get(e.from)
        const to = posMap.get(e.to)
        if (!from || !to) return null
        const mx = (from.x + to.x) / 2
        const my = (from.y + to.y) / 2
        return (
          <motion.path
            key={i}
            d={`M ${from.x} ${from.y} C ${from.x} ${my} ${to.x} ${my} ${to.x} ${to.y}`}
            stroke="rgba(232,200,120,0.42)"
            strokeWidth="0.85"
            fill="none"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.5, delay: i * 0.05 }}
          />
        )
      })}

      {/* Nodes */}
      {layers.flatMap((layer, li) =>
        layer.map((assetId, idx) => {
          const asset = planAssets.find(a => a.asset_id === assetId)
          if (!asset) return null
          const isTarget = assetId === targetAssetId
          const cx = nodeX(idx, layer.length)
          const cy = layerY(li)
          const r = isTarget ? 8 : 6
          const labelY = li === 0 ? cy - 14 : cy + 20
          const sublabelY = li === 0 ? cy - 3 : cy + 30

          return (
            <g key={assetId}>
              <motion.circle
                cx={cx}
                cy={cy}
                r={r}
                fill={isTarget ? 'url(#miniRootBead)' : 'url(#miniNodeBead)'}
                stroke={isTarget ? '#ECC56A' : '#C4A268'}
                strokeWidth={isTarget ? 1.2 : 0.8}
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: li * 0.1 + idx * 0.03, type: 'spring' }}
                style={{ transformOrigin: `${cx}px ${cy}px` }}
              />
              <text
                x={cx}
                y={labelY}
                textAnchor="middle"
                fontFamily="var(--font-serif, serif)"
                fill="var(--gold-high, #ECC56A)"
                fontSize={li === 0 ? 11 : 9}
              >
                {asset.sanskrit_name}
              </text>
              <text
                x={cx}
                y={sublabelY}
                textAnchor="middle"
                fill="rgba(255,255,255,0.7)"
                fontSize={li === 0 ? 8 : 7}
              >
                {asset.english_name}
              </text>
            </g>
          )
        })
      )}
    </svg>
  )
}
