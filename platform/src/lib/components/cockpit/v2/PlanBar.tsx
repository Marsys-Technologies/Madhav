'use client'

import { motion } from 'framer-motion'

const LAYER_NAMES: Record<string, string> = {
  brahmagyan: 'Brahma Jñāna',
  ganita: 'Gaṇita',
  bodha: 'Bodha',
  kala: 'Kāla',
  phala: 'Phala',
  mimamsa: 'Mīmāṃsā',
}
const LAYER_GOLD: Record<string, string> = {
  brahmagyan: '#ECC56A', ganita: '#D2A23C', bodha: '#A87C2A',
  kala: '#8A5E12', phala: '#B98A2E', mimamsa: '#6E4E0F',
}

function layerFromAssetId(id: string): string {
  const prefix = id.split('_')[0]
  const map: Record<string, string> = {
    bg: 'brahmagyan', ga: 'ganita', bo: 'bodha',
    ka: 'kala', ph: 'phala', mi: 'mimamsa',
  }
  return map[prefix] ?? 'unknown'
}

interface LayerCluster { layer: string; assets: string[] }

function groupIntoClusters(plan: string[]): LayerCluster[] {
  const clusters: LayerCluster[] = []
  for (const assetId of plan) {
    const layer = layerFromAssetId(assetId)
    const last = clusters[clusters.length - 1]
    if (last && last.layer === layer) { last.assets.push(assetId) }
    else { clusters.push({ layer, assets: [assetId] }) }
  }
  return clusters
}

interface PlanBarProps {
  plan: string[]
  currentAssetId: string | null
  assetStateMap: Map<string, string>
}

export function PlanBar({ plan, currentAssetId, assetStateMap }: PlanBarProps) {
  if (plan.length === 0) return null
  const clusters = groupIntoClusters(plan)
  const total = plan.length
  const prefersReducedMotion = typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  return (
    <div style={{ width: '100%' }}>
      {/* Cluster labels */}
      <div style={{ display: 'flex', gap: '3px', marginBottom: '3px' }}>
        {clusters.map((cluster, i) => (
          <div
            key={`${cluster.layer}-${i}`}
            style={{ flex: cluster.assets.length + ' 0 0%', minWidth: 0, overflow: 'hidden' }}
          >
            <div style={{
              fontSize: '8px', fontFamily: 'var(--display-stack)',
              color: LAYER_GOLD[cluster.layer] ?? '#A87C2A',
              opacity: 0.75, whiteSpace: 'nowrap',
              overflow: 'hidden', textOverflow: 'ellipsis',
              letterSpacing: '0.03em',
            }}>
              {LAYER_NAMES[cluster.layer] ?? cluster.layer}
            </div>
          </div>
        ))}
      </div>
      {/* Segment track */}
      <div style={{ display: 'flex', gap: '3px', height: '6px' }}>
        {clusters.map((cluster, i) => {
          const gold = LAYER_GOLD[cluster.layer] ?? '#A87C2A'
          return (
            <div
              key={`${cluster.layer}-${i}`}
              style={{ flex: cluster.assets.length + ' 0 0%', display: 'flex', gap: '1px' }}
            >
              {cluster.assets.map(assetId => {
                const state = assetStateMap.get(assetId)
                const isActive = assetId === currentAssetId
                const isDone = state === 'lit' || state === 'service_ok'
                return (
                  <div
                    key={assetId}
                    style={{
                      flex: 1, borderRadius: '2px', position: 'relative', overflow: 'hidden',
                      background: isDone ? gold : isActive ? gold + '55' : 'rgba(122,86,24,0.18)',
                      border: '1px solid ' + (isDone ? gold + '88' : isActive ? gold + '44' : 'rgba(122,86,24,0.22)'),
                      transition: 'background 0.4s ease',
                    }}
                    title={assetId}
                  >
                    {isActive && !prefersReducedMotion && (
                      <div style={{
                        position: 'absolute', inset: 0, pointerEvents: 'none',
                        background: 'linear-gradient(90deg, transparent 0%, rgba(236,197,106,0.45) 50%, transparent 100%)',
                        animation: 'shimmer 1.8s linear infinite',
                      }} />
                    )}
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>
    </div>
  )
}
