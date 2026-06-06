'use client'

import { useMemo, useState, useRef, useEffect } from 'react'
import type { AssetRow } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
import type { ActiveRun } from '@/hooks/useActiveRun'

// ── Types ──────────────────────────────────────────────────────────────────────

type AssetState = 'dormant' | 'building' | 'lit' | 'stale' | 'error' | null

interface AssetWithState extends AssetRow {
  state: AssetState
  last_built_at: string | null
  actual_rows: number | null
}

// ── Layer → orbit ring (ratio of SVG dimensions) ──────────────────────────────

const ORBITS: Record<string, { rx: number; ry: number }> = {
  brahmagyan: { rx: 0.10, ry: 0.10 },
  ganita:     { rx: 0.18, ry: 0.16 },
  bodha:      { rx: 0.25, ry: 0.22 },
  kala:       { rx: 0.32, ry: 0.28 },
  phala:      { rx: 0.37, ry: 0.32 },
  mimamsa:    { rx: 0.40, ry: 0.36 },
}

const NODE_RADIUS: Record<string, number> = {
  ROOT:       18,
  brahmagyan: 9,
  ganita:     7.5,
  bodha:      7,
  kala:       6.5,
  phala:      7,
  mimamsa:    11,
}

const LAYER_ORDER = ['brahmagyan', 'ganita', 'bodha', 'kala', 'phala', 'mimamsa']

// ── Deterministic hash (djb2-like) ────────────────────────────────────────────

function hash(s: string): number {
  let h = 5381
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h) ^ s.charCodeAt(i)
  return Math.abs(h)
}

// ── Node position ─────────────────────────────────────────────────────────────

function nodePosition(
  asset: AssetWithState,
  siblings: AssetWithState[],
  W: number,
  H: number
): { cx: number; cy: number } {
  const orbit = ORBITS[asset.layer] ?? { rx: 0.45, ry: 0.40 }
  const idx = siblings.findIndex(a => a.asset_id === asset.asset_id)
  const baseAngle = (idx / siblings.length) * 360
  const jitter = asset.layer === 'mimamsa' ? 0 : (hash(asset.asset_id) % 11) - 5
  const angle = ((baseAngle + jitter) * Math.PI) / 180
  const cx = W / 2 + W * orbit.rx * Math.sin(angle)
  const cy = H * 0.55 - H * orbit.ry * Math.cos(angle)
  return { cx, cy }
}

// ── Edge classification ───────────────────────────────────────────────────────

type EdgeTier = 'rootSpoke' | 'direct' | 'crossWeave' | 'skip'

interface EdgeSpec {
  fromId: string
  toId: string
  tier: EdgeTier
}

const EDGE_STYLES: Record<EdgeTier, { stroke: string; width: number; dasharray?: string }> = {
  rootSpoke:  { stroke: 'rgba(236,197,106,0.55)', width: 1.3 },
  direct:     { stroke: 'rgba(232,200,120,0.42)', width: 0.85 },
  crossWeave: { stroke: 'rgba(212,180,108,0.36)', width: 0.75 },
  skip:       { stroke: 'rgba(232,200,120,0.28)', width: 0.6, dasharray: '2,2' },
}

function classifyEdge(fromLayer: string, toLayer: string): EdgeTier {
  if (fromLayer === 'ROOT' || toLayer === 'ROOT') return 'rootSpoke'
  const fi = LAYER_ORDER.indexOf(fromLayer)
  const ti = LAYER_ORDER.indexOf(toLayer)
  const gap = Math.abs(ti - fi)
  if (gap === 0) return 'direct'
  if (gap === 1) return 'direct'
  if (gap === 2) return 'crossWeave'
  return 'skip'
}

// ── State → visual ────────────────────────────────────────────────────────────

function stateOpacity(state: AssetState): number {
  if (state === 'dormant' || state == null) return 0.7
  return 1.0
}

function edgeOpacityMultiplier(fromState: AssetState, toState: AssetState): number {
  if (fromState === 'dormant' || toState === 'dormant' || fromState == null || toState == null) return 0
  if (fromState === 'building' || toState === 'building') return 0.4
  if (fromState === 'stale' || toState === 'stale') return 0.3
  return 1.0
}

// ── Component ─────────────────────────────────────────────────────────────────

interface Props {
  assets: AssetWithState[]
  activeRun: ActiveRun | null
  onNodeClick: (assetId: string) => void
}

export function LiveDependencyGraph({ assets, activeRun, onNodeClick }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [dims, setDims] = useState({ W: 400, H: 520 })
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  // Responsive sizing
  useEffect(() => {
    if (!containerRef.current) return
    const ro = new ResizeObserver(entries => {
      const entry = entries[0]
      if (entry) {
        const W = entry.contentRect.width
        setDims({ W, H: Math.round(W * 1.25) })
      }
    })
    ro.observe(containerRef.current)
    return () => ro.disconnect()
  }, [])

  const { W, H } = dims

  // Pre-compute sibling groups by layer
  const siblingsByLayer = useMemo(() => {
    const m = new Map<string, AssetWithState[]>()
    for (const a of assets) {
      const arr = m.get(a.layer) ?? []
      arr.push(a)
      m.set(a.layer, arr)
    }
    // Sort siblings alphabetically for stable ordering
    for (const [, arr] of m) arr.sort((x, y) => x.asset_id.localeCompare(y.asset_id))
    return m
  }, [assets])

  // Compute positions (deterministic)
  const posMap = useMemo(() => {
    const m = new Map<string, { cx: number; cy: number }>()
    m.set('ROOT', { cx: W / 2, cy: H * 0.55 })
    for (const a of assets) {
      const siblings = siblingsByLayer.get(a.layer) ?? []
      m.set(a.asset_id, nodePosition(a, siblings, W, H))
    }
    return m
  }, [assets, siblingsByLayer, W, H])

  // Compute edges
  const edges = useMemo<EdgeSpec[]>(() => {
    const result: EdgeSpec[] = []
    for (const a of assets) {
      if (!a.depends_on || a.depends_on.length === 0) {
        result.push({ fromId: 'ROOT', toId: a.asset_id, tier: classifyEdge('ROOT', a.layer) })
        continue
      }
      for (const dep of a.depends_on) {
        const depAsset = assets.find(x => x.asset_id === dep)
        const depLayer = depAsset?.layer ?? 'ROOT'
        result.push({ fromId: dep, toId: a.asset_id, tier: classifyEdge(depLayer, a.layer) })
      }
    }
    return result
  }, [assets])

  // Hover closures
  const { upstreamSet, downstreamSet } = useMemo(() => {
    if (!hoveredId) return { upstreamSet: new Set<string>(), downstreamSet: new Set<string>() }

    const upstreamSet = new Set<string>()
    const downstreamSet = new Set<string>()

    // Upstream walk
    const visitUp = (id: string) => {
      const a = assets.find(x => x.asset_id === id)
      if (!a) return
      for (const dep of (a.depends_on ?? [])) {
        if (!upstreamSet.has(dep)) { upstreamSet.add(dep); visitUp(dep) }
      }
    }
    visitUp(hoveredId)

    // Downstream walk
    const visitDown = (id: string) => {
      for (const a of assets) {
        if ((a.depends_on ?? []).includes(id) && !downstreamSet.has(a.asset_id)) {
          downstreamSet.add(a.asset_id)
          visitDown(a.asset_id)
        }
      }
    }
    visitDown(hoveredId)

    return { upstreamSet, downstreamSet }
  }, [hoveredId, assets])

  // Deterministic particle dust (seeded by asset count)
  const particles = useMemo(() => {
    const count = 30
    return Array.from({ length: count }, (_, i) => ({
      x: (hash(`p${i}`) % 900) / 1000 * W,
      y: (hash(`q${i}`) % 900) / 1000 * H,
      r: 0.6 + (hash(`r${i}`) % 4) / 10,
    }))
  }, [W, H])

  // Background polygons (connect lit node triplets)
  const litNodes = assets.filter(a => a.state === 'lit' || a.state === 'building')
  const polyOpacity = Math.min(0.10, (litNodes.length / Math.max(assets.length, 1)) * 0.10)

  const stateMap = useMemo(() => {
    const m = new Map<string, AssetState>()
    for (const a of assets) m.set(a.asset_id, a.state)
    return m
  }, [assets])

  function nodeOpacity(id: string): number {
    if (!hoveredId) return 1
    if (id === hoveredId || upstreamSet.has(id) || downstreamSet.has(id)) return 1
    return 0.15
  }

  function edgeOpacity(fromId: string, toId: string, baseMult: number): number {
    const dimmed = hoveredId &&
      fromId !== hoveredId && toId !== hoveredId &&
      !upstreamSet.has(fromId) && !upstreamSet.has(toId) &&
      !downstreamSet.has(fromId) && !downstreamSet.has(toId)
    return (dimmed ? 0.08 : 1.0) * baseMult
  }

  return (
    <div ref={containerRef} style={{ width: '100%', position: 'relative' }}>
      <svg
        width={W}
        height={H}
        viewBox={`0 0 ${W} ${H}`}
        style={{ display: 'block', overflow: 'visible' }}
      >
        <defs>
          <radialGradient id="nodeBead" cx="35%" cy="30%" r="75%">
            <stop offset="0%"   stopColor="#FFFBE8" />
            <stop offset="55%"  stopColor="#EFE0BC" />
            <stop offset="100%" stopColor="#A47A28" />
          </radialGradient>
          <radialGradient id="rootBead" cx="32%" cy="28%" r="85%">
            <stop offset="0%"   stopColor="#FFFFFF" />
            <stop offset="25%"  stopColor="#FFF8E0" />
            <stop offset="65%"  stopColor="#ECC56A" />
            <stop offset="100%" stopColor="#7A5618" />
          </radialGradient>
          <filter id="glowS" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="glowM" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="glowL" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="glowRoot" x="-150%" y="-150%" width="400%" height="400%">
            <feGaussianBlur stdDeviation="9" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Particle dust */}
        {particles.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r={p.r} fill="#A47A28" opacity={0.35} />
        ))}

        {/* Background depth polygons */}
        {litNodes.length >= 3 && polyOpacity > 0 && (() => {
          const triplets: [string, string, string][] = []
          for (let i = 0; i < Math.min(litNodes.length - 2, 20); i++) {
            triplets.push([litNodes[i].asset_id, litNodes[i + 1].asset_id, litNodes[(i + 2) % litNodes.length].asset_id])
          }
          return triplets.map(([a, b, c], i) => {
            const pa = posMap.get(a); const pb = posMap.get(b); const pc = posMap.get(c)
            if (!pa || !pb || !pc) return null
            return (
              <polygon
                key={i}
                points={`${pa.cx},${pa.cy} ${pb.cx},${pb.cy} ${pc.cx},${pc.cy}`}
                fill={`rgba(70,55,32,${polyOpacity})`}
                stroke={`rgba(140,110,60,0.18)`}
                strokeWidth={0.5}
              />
            )
          })
        })()}

        {/* Orbital ellipses */}
        {Object.entries(ORBITS).map(([, orb]) => (
          <ellipse
            key={`orb-${orb.rx}`}
            cx={W / 2}
            cy={H * 0.55}
            rx={W * orb.rx}
            ry={H * orb.ry}
            fill="none"
            stroke="rgba(236,197,106,0.07)"
            strokeWidth={0.6}
          />
        ))}

        {/* Edges (rendered behind nodes) */}
        {edges.map((e, i) => {
          const from = posMap.get(e.fromId)
          const to = posMap.get(e.toId)
          if (!from || !to) return null
          const style = EDGE_STYLES[e.tier]
          const fromState = e.fromId === 'ROOT' ? 'lit' : stateMap.get(e.fromId)
          const toState = stateMap.get(e.toId)
          const mult = edgeOpacityMultiplier(fromState ?? null, toState ?? null)
          const finalOpacity = edgeOpacity(e.fromId, e.toId, mult)
          if (finalOpacity < 0.01) return null
          return (
            <line
              key={i}
              x1={from.cx} y1={from.cy}
              x2={to.cx} y2={to.cy}
              stroke={style.stroke}
              strokeWidth={style.width}
              strokeDasharray={style.dasharray}
              opacity={finalOpacity}
            />
          )
        })}

        {/* Nodes */}
        {assets.map(a => {
          const pos = posMap.get(a.asset_id)
          if (!pos) return null
          const r = NODE_RADIUS[a.layer] ?? 6
          const state = a.state
          const opacity = stateOpacity(state) * nodeOpacity(a.asset_id)

          const isDormant = state === 'dormant' || state == null
          const isBuilding = state === 'building'
          const isLit = state === 'lit'
          const isStale = state === 'stale'

          const fill = isDormant ? 'none' : 'url(#nodeBead)'
          const rimColor = isDormant ? 'rgba(122,86,24,0.5)'
            : isStale ? 'rgba(164,122,40,0.5)'
            : isBuilding ? '#C4A268'
            : isLit ? '#D4A648'
            : '#ECC56A'

          const glowFilter = isDormant ? undefined
            : isBuilding ? 'url(#glowS)'
            : isStale ? undefined
            : 'url(#glowM)'

          return (
            <g
              key={a.asset_id}
              style={{ cursor: 'pointer' }}
              opacity={opacity}
              onMouseEnter={() => setHoveredId(a.asset_id)}
              onMouseLeave={() => setHoveredId(null)}
              onClick={() => onNodeClick(a.asset_id)}
              filter={glowFilter}
            >
              <circle
                cx={pos.cx}
                cy={pos.cy}
                r={r}
                fill={fill}
                stroke={rimColor}
                strokeWidth={isDormant ? 0.8 : 1.1}
                fillOpacity={isStale ? 0.4 : 1}
              />
              {/* Inner highlight for lit/building state */}
              {(isLit || isBuilding) && (
                <circle
                  cx={pos.cx - r * 0.28}
                  cy={pos.cy - r * 0.28}
                  r={r * 0.28}
                  fill="rgba(255,255,255,0.65)"
                />
              )}
              {/* Invisible larger hit target */}
              <circle cx={pos.cx} cy={pos.cy} r={r + 4} fill="transparent" />
            </g>
          )
        })}

        {/* ROOT node */}
        {(() => {
          const pos = posMap.get('ROOT')
          if (!pos) return null
          return (
            <g filter="url(#glowRoot)">
              <circle cx={pos.cx} cy={pos.cy} r={NODE_RADIUS.ROOT} fill="url(#rootBead)" stroke="#ECC56A" strokeWidth={1.5} />
              <circle cx={pos.cx - 5} cy={pos.cy - 5} r={5} fill="rgba(255,255,255,0.80)" />
            </g>
          )
        })()}

        {/* Layer legend — top-left */}
        {W >= 300 && LAYER_ORDER.map((l, i) => {
          const orb = ORBITS[l]
          return (
            <g key={l} transform={`translate(12, ${16 + i * 16})`}>
              <ellipse cx={8} cy={5} rx={6} ry={3} fill="none" stroke="rgba(236,197,106,0.30)" strokeWidth={0.7} />
              <text x={18} y={9} fontFamily="var(--ui-stack)" fontSize={9} fill="rgba(255,255,255,0.40)">
                {l} · rx{Math.round(orb.rx * 100)}
              </text>
            </g>
          )
        })}

        {/* Hover tooltip */}
        {hoveredId && (() => {
          const pos = posMap.get(hoveredId)
          const asset = assets.find(a => a.asset_id === hoveredId)
          if (!pos || !asset) return null
          const tx = Math.min(pos.cx + 14, W - 130)
          const ty = Math.max(pos.cy - 20, 10)
          return (
            <g>
              <rect x={tx - 4} y={ty - 12} width={128} height={30} rx={4} fill="rgba(20,16,8,0.88)" stroke="rgba(236,197,106,0.3)" strokeWidth={0.8} />
              <text x={tx} y={ty} fontFamily="var(--ui-stack)" fontSize={10} fill="#ECC56A">{asset.english_name}</text>
              <text x={tx} y={ty + 11} fontFamily="var(--mono-stack)" fontSize={8.5} fill="rgba(255,255,255,0.50)">{asset.asset_id}</text>
            </g>
          )
        })()}
      </svg>
    </div>
  )
}

export type { AssetWithState }
