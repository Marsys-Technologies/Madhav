'use client'

import { useMemo, useState, useRef, useEffect } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import type { AssetRow } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
import type { ActiveRun } from '@/hooks/useActiveRun'

// ── Types ──────────────────────────────────────────────────────────────────────

type AssetState = 'lit' | 'building' | 'stale' | 'dormant' | 'error' | 'partial' | 'not_migrated' | 'service_ok'

interface AssetWithState extends AssetRow {
  state: AssetState
  last_built_at: string | null
  actual_rows: number | null
  build_state_stale?: boolean
  // Badge-honesty (pre-D-4b readiness pass): populated only when state === 'partial'.
  substep_progress?: { committed: number; total: number | null }
}

// ── Antique-gold palette (art constants — intentional literal values) ──────────

const GOLD_NODE_LIGHT = '#E8C878'
const GOLD_NODE_MID   = '#C49A3E'
const GOLD_NODE_DARK  = '#6B4E18'
const GOLD_ROOT_LIGHT = '#F4D98A'
const GOLD_ROOT_MID   = '#D4A648'
const GOLD_ROOT_DARK  = '#5C3F12'

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

// ── Node position (with optional orbital offset for build-time rotation) ──────

function nodePosition(
  asset: AssetWithState,
  siblings: AssetWithState[],
  W: number,
  H: number,
  orbitOffset: number = 0
): { cx: number; cy: number } {
  const orbit = ORBITS[asset.layer] ?? { rx: 0.45, ry: 0.40 }
  const idx = siblings.findIndex(a => a.asset_id === asset.asset_id)
  const baseAngle = (idx / siblings.length) * 360 + orbitOffset
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
  rootSpoke:  { stroke: 'rgba(236,197,106,0.45)', width: 1.1 },
  direct:     { stroke: 'rgba(196,154,62,0.35)',  width: 0.7 },
  crossWeave: { stroke: 'rgba(180,140,96,0.28)',  width: 0.6 },
  skip:       { stroke: 'rgba(196,154,62,0.22)',  width: 0.5, dasharray: '2,2' },
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
  if (state === 'dormant' || state === 'not_migrated') return 0.7
  return 1.0
}

function fillFor(state: AssetState): string {
  if (state === 'dormant' || state === 'not_migrated') return 'none'
  return 'url(#nodeBead)'
}

function strokeFor(state: AssetState): string {
  if (state === 'dormant' || state === 'not_migrated') return 'rgba(107,78,24,0.5)'
  // 'partial': a resumable, in-progress materialization (real committed substeps exist),
  // distinct from a genuinely broken 'error' — visually grouped with 'stale', never with
  // 'lit'/'building' (badge-honesty, pre-D-4b readiness pass).
  if (state === 'stale' || state === 'partial') return 'rgba(140,104,36,0.55)'
  if (state === 'building') return GOLD_NODE_MID
  if (state === 'lit')      return GOLD_ROOT_MID
  return GOLD_NODE_LIGHT
}

function edgeOpacityMultiplier(fromState: AssetState, toState: AssetState): number {
  if (fromState === 'dormant' || toState === 'dormant' || fromState === 'not_migrated' || toState === 'not_migrated') return 0
  if (fromState === 'building' || toState === 'building') return 0.45
  if (fromState === 'stale' || toState === 'stale' || fromState === 'partial' || toState === 'partial') return 0.32
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
  const prefersReducedMotion = useReducedMotion()

  // Orbital rotation state for active builds
  const orbitAngleRef = useRef(0)
  const [orbitAngle, setOrbitAngle] = useState(0)
  const isActiveRun = activeRun != null
  const ORBIT_DEG_PER_SEC = 3 // full revolution ~2 min

  // Responsive sizing — track height when container has fixed height (R5 pane)
  useEffect(() => {
    if (!containerRef.current) return
    const ro = new ResizeObserver(entries => {
      const entry = entries[0]
      if (entry) {
        const W = entry.contentRect.width
        const measuredH = entry.contentRect.height
        const H = measuredH > 100 ? measuredH : Math.round(W * 1.25)
        setDims({ W, H })
      }
    })
    ro.observe(containerRef.current)
    return () => ro.disconnect()
  }, [])

  // Slow orbital drift when a build is active; paused otherwise and for reduced-motion
  useEffect(() => {
    if (!isActiveRun || prefersReducedMotion) return
    let rafId: number
    let lastTime: number | null = null
    const tick = (time: number) => {
      if (lastTime !== null) {
        const delta = time - lastTime
        orbitAngleRef.current = (orbitAngleRef.current + ORBIT_DEG_PER_SEC * delta / 1000) % 360
        setOrbitAngle(orbitAngleRef.current)
      }
      lastTime = time
      rafId = requestAnimationFrame(tick)
    }
    rafId = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafId)
  }, [isActiveRun, prefersReducedMotion])

  const { W, H } = dims

  // Pre-compute sibling groups by layer
  const siblingsByLayer = useMemo(() => {
    const m = new Map<string, AssetWithState[]>()
    for (const a of assets) {
      const arr = m.get(a.layer) ?? []
      arr.push(a)
      m.set(a.layer, arr)
    }
    for (const [, arr] of m) arr.sort((x, y) => x.asset_id.localeCompare(y.asset_id))
    return m
  }, [assets])

  // Compute positions (deterministic; reacts to orbitAngle during active builds)
  const posMap = useMemo(() => {
    const m = new Map<string, { cx: number; cy: number }>()
    m.set('ROOT', { cx: W / 2, cy: H * 0.55 })
    for (const a of assets) {
      const siblings = siblingsByLayer.get(a.layer) ?? []
      m.set(a.asset_id, nodePosition(a, siblings, W, H, orbitAngle))
    }
    return m
  }, [assets, siblingsByLayer, W, H, orbitAngle])

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

  // Building asset IDs for targeted animation.
  // In local dev, SSE doesn't deliver state_change events (heartbeat-only fallback),
  // so stats polling may never catch the brief 'building' window for fast assets.
  // When a run is active, treat every asset in the run plan as "building" for
  // animation purposes — this ensures orbital drift, edge shimmer, and node pulses
  // all fire for the entire build, not just the ~1s each asset is in the DB state.
  const buildingIds = useMemo(() => {
    const fromState = new Set(assets.filter(a => a.state === 'building').map(a => a.asset_id))
    if (activeRun && activeRun.plan && activeRun.plan.length > 0) {
      for (const id of activeRun.plan) fromState.add(id)
    }
    return fromState
  }, [assets, activeRun])

  // Hover closures
  const { upstreamSet, downstreamSet } = useMemo(() => {
    if (!hoveredId) return { upstreamSet: new Set<string>(), downstreamSet: new Set<string>() }
    const upstreamSet = new Set<string>()
    const downstreamSet = new Set<string>()
    const visitUp = (id: string) => {
      const a = assets.find(x => x.asset_id === id)
      if (!a) return
      for (const dep of (a.depends_on ?? [])) {
        if (!upstreamSet.has(dep)) { upstreamSet.add(dep); visitUp(dep) }
      }
    }
    visitUp(hoveredId)
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

  // Deterministic particle dust
  const particles = useMemo(() => {
    const count = 30
    return Array.from({ length: count }, (_, i) => ({
      x: (hash(`p${i}`) % 900) / 1000 * W,
      y: (hash(`q${i}`) % 900) / 1000 * H,
      r: 0.6 + (hash(`r${i}`) % 4) / 10,
    }))
  }, [W, H])

  // Background polygons (connect lit/building node triplets)
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
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        // Depth vignette — darker at edges for a sense of field depth
        background: 'radial-gradient(ellipse at 50% 55%, transparent 35%, rgba(4,3,1,0.50) 100%)',
      }}
    >
      <svg
        width={W}
        height={H}
        viewBox={`0 0 ${W} ${H}`}
        style={{ display: 'block', overflow: 'visible' }}
      >
        <defs>
          {/* Darker antique-gold sphere gradient — burnished orb, top-left light source */}
          <radialGradient id="nodeBead" cx="35%" cy="30%" r="75%">
            <stop offset="0%"   stopColor={GOLD_NODE_LIGHT} />
            <stop offset="40%"  stopColor={GOLD_NODE_MID} />
            <stop offset="100%" stopColor={GOLD_NODE_DARK} />
          </radialGradient>
          {/* ROOT — slightly brighter than node beads */}
          <radialGradient id="rootBead" cx="32%" cy="28%" r="85%">
            <stop offset="0%"   stopColor={GOLD_ROOT_LIGHT} />
            <stop offset="45%"  stopColor={GOLD_ROOT_MID} />
            <stop offset="100%" stopColor={GOLD_ROOT_DARK} />
          </radialGradient>
          {/* Soft atmosphere disc — radial gold → transparent, rendered behind each sphere */}
          <radialGradient id="atmosphereGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor={GOLD_NODE_MID} stopOpacity="0.14" />
            <stop offset="100%" stopColor={GOLD_NODE_MID} stopOpacity="0" />
          </radialGradient>
          {/* ROOT atmosphere — slightly brighter presence */}
          <radialGradient id="atmosphereRoot" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor={GOLD_ROOT_MID} stopOpacity="0.18" />
            <stop offset="100%" stopColor={GOLD_ROOT_MID} stopOpacity="0" />
          </radialGradient>
          {/* Contained glow — only used on building state; small blur so sphere stays legible */}
          <filter id="glowBuilding" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="1.8" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Particle dust — low opacity ambient field */}
        {particles.map((p, idx) => (
          <motion.circle
            key={`p-${idx}`}
            r={p.r}
            fill={GOLD_NODE_DARK}
            initial={{ cx: p.x, cy: p.y, opacity: 0.28 }}
            animate={{
              cx: [p.x, p.x + 6 + (idx % 3) * 2, p.x - 4, p.x],
              cy: [p.y, p.y - 5, p.y + 3, p.y],
              opacity: [0.28, 0.42, 0.30, 0.28],
            }}
            transition={{
              duration: 15 + (idx % 10) * 1.5,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        ))}

        {/* Background depth polygons */}
        {litNodes.length >= 3 && polyOpacity > 0 && (() => {
          const triplets: [string, string, string][] = []
          for (let i = 0; i < Math.min(litNodes.length - 2, 20); i++) {
            triplets.push([litNodes[i].asset_id, litNodes[i + 1].asset_id, litNodes[(i + 2) % litNodes.length].asset_id])
          }
          return triplets.map(([a, b, c], polyIdx) => {
            const pa = posMap.get(a); const pb = posMap.get(b); const pc = posMap.get(c)
            if (!pa || !pb || !pc) return null
            return (
              <polygon
                key={`poly-${polyIdx}`}
                points={`${pa.cx},${pa.cy} ${pb.cx},${pb.cy} ${pc.cx},${pc.cy}`}
                fill="rgba(65,50,28,1)"
                stroke="rgba(130,100,50,0.14)"
                strokeWidth={0.5}
                className="poly-pulse"
                style={
                  {
                    '--base-op': polyOpacity,
                    animationDuration: `${8 + polyIdx * 2}s`,
                  } as React.CSSProperties
                }
              />
            )
          })
        })()}

        {/* Orbital ellipses — thin + faint */}
        {Object.entries(ORBITS).map(([, orb]) => (
          <ellipse
            key={`orb-${orb.rx}`}
            cx={W / 2}
            cy={H * 0.55}
            rx={W * orb.rx}
            ry={H * orb.ry}
            fill="none"
            stroke="rgba(196,154,62,0.06)"
            strokeWidth={0.6}
          />
        ))}

        {/* Edges — rendered behind nodes */}
        {edges.map((e, i) => {
          const from = posMap.get(e.fromId)
          const to = posMap.get(e.toId)
          if (!from || !to) return null
          const style = EDGE_STYLES[e.tier]
          const fromState = e.fromId === 'ROOT' ? 'lit' : stateMap.get(e.fromId)
          const toState = stateMap.get(e.toId)
          const mult = edgeOpacityMultiplier(fromState ?? 'dormant', toState ?? 'dormant')
          const finalOpacity = edgeOpacity(e.fromId, e.toId, mult)
          if (finalOpacity < 0.01) return null

          // Flowing "data transfer" shimmer on edges connected to actively building nodes
          const isFlowing = !prefersReducedMotion && isActiveRun &&
            (buildingIds.has(e.fromId) || buildingIds.has(e.toId))

          if (isFlowing) {
            return (
              <motion.line
                key={i}
                x1={from.cx} y1={from.cy}
                x2={to.cx} y2={to.cy}
                stroke={GOLD_NODE_MID}
                strokeWidth={style.width * 1.6}
                strokeDasharray="4 3"
                animate={{
                  opacity: finalOpacity * 1.4,
                  strokeDashoffset: [0, -7],
                }}
                transition={{
                  opacity: { duration: 0.8, ease: 'easeInOut' },
                  strokeDashoffset: { duration: 1.1, repeat: Infinity, ease: 'linear' },
                }}
              />
            )
          }

          return (
            <motion.line
              key={i}
              x1={from.cx} y1={from.cy}
              x2={to.cx} y2={to.cy}
              stroke={style.stroke}
              strokeWidth={style.width}
              strokeDasharray={style.dasharray}
              initial={{ opacity: 0 }}
              animate={{ opacity: finalOpacity }}
              transition={{ duration: 0.8, ease: 'easeInOut', delay: i * 0.05 }}
            />
          )
        })}

        {/* Nodes */}
        {assets.map((a, nodeIndex) => {
          const pos = posMap.get(a.asset_id)
          if (!pos) return null
          const r = NODE_RADIUS[a.layer] ?? 6
          const state = a.state
          const opacity = stateOpacity(state) * nodeOpacity(a.asset_id)

          const isDormant = state === 'dormant' || state === 'not_migrated'
          const isBuilding = state === 'building' || buildingIds.has(a.asset_id)
          const isLit = state === 'lit'
          const isStale = state === 'stale'

          // Pulse when the asset is in the run plan or explicitly in 'building' state
          const shouldPulse = !prefersReducedMotion && isBuilding && isActiveRun

          return (
            <g
              key={a.asset_id}
              style={{ cursor: 'pointer' }}
              opacity={opacity}
              onMouseEnter={() => setHoveredId(a.asset_id)}
              onMouseLeave={() => setHoveredId(null)}
              onClick={() => onNodeClick(a.asset_id)}
              filter={isBuilding ? 'url(#glowBuilding)' : undefined}
            >
              {/* Soft atmosphere disc — behind sphere, gentle gold presence */}
              {!isDormant && (
                <circle
                  cx={pos.cx}
                  cy={pos.cy}
                  r={r * 2.6}
                  fill="url(#atmosphereGrad)"
                />
              )}

              {/* Main sphere */}
              {shouldPulse ? (
                <motion.circle
                  cx={pos.cx}
                  cy={pos.cy}
                  r={r}
                  fill={fillFor(state)}
                  stroke={strokeFor(state)}
                  strokeWidth={1.5}
                  animate={{ scale: [1, 1.13, 1], opacity: [1, 0.82, 1] }}
                  transition={{
                    duration: 2.2,
                    repeat: Infinity,
                    ease: 'easeInOut',
                    delay: nodeIndex * 0.18,
                  }}
                  style={{ transformBox: 'fill-box', transformOrigin: 'center' }}
                />
              ) : (isLit || isBuilding) ? (
                <circle
                  cx={pos.cx}
                  cy={pos.cy}
                  r={r}
                  fill={fillFor(state)}
                  stroke={strokeFor(state)}
                  strokeWidth={1.5}
                  fillOpacity={isStale ? 0.4 : 1}
                  opacity={stateOpacity(state)}
                  className="bead-breathe"
                  style={{
                    transformBox: 'fill-box',
                    transformOrigin: 'center',
                    animationDelay: `${nodeIndex * 0.15}s`,
                  }}
                />
              ) : (
                <motion.circle
                  cx={pos.cx}
                  cy={pos.cy}
                  r={r}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: stateOpacity(state) }}
                  transition={{ duration: 0.6, ease: 'easeOut' }}
                  fill={fillFor(state)}
                  stroke={strokeFor(state)}
                  strokeWidth={1.5}
                  fillOpacity={isStale ? 0.4 : 1}
                />
              )}

              {/* Specular highlight — smaller + softer for legible 3D read */}
              {(isLit || isBuilding) && (
                <circle
                  cx={pos.cx - r * 0.28}
                  cy={pos.cy - r * 0.28}
                  r={r * 0.20}
                  fill="rgba(255,255,255,0.52)"
                />
              )}

              {/* Invisible enlarged hit target */}
              <circle cx={pos.cx} cy={pos.cy} r={r + 4} fill="transparent" />
            </g>
          )
        })}

        {/* ROOT node */}
        {(() => {
          const pos = posMap.get('ROOT')
          if (!pos) return null
          const r = NODE_RADIUS.ROOT
          return (
            <g>
              {/* Root atmosphere disc */}
              <circle cx={pos.cx} cy={pos.cy} r={r * 2.8} fill="url(#atmosphereRoot)" />
              <circle cx={pos.cx} cy={pos.cy} r={r} fill="url(#rootBead)" stroke={GOLD_ROOT_MID} strokeWidth={1.5} />
              {/* Specular highlight */}
              <circle cx={pos.cx - 5} cy={pos.cy - 5} r={4} fill="rgba(255,255,255,0.70)" />
            </g>
          )
        })()}

        {/* Layer legend REMOVED per R3.1 */}

        {/* Hover tooltip */}
        {hoveredId && (() => {
          const pos = posMap.get(hoveredId)
          const asset = assets.find(a => a.asset_id === hoveredId)
          if (!pos || !asset) return null
          const tx = Math.min(pos.cx + 14, W - 130)
          const ty = Math.max(pos.cy - 20, 10)
          return (
            <g>
              <rect x={tx - 4} y={ty - 12} width={128} height={30} rx={4} fill="rgba(18,14,6,0.90)" stroke="rgba(196,154,62,0.30)" strokeWidth={0.8} />
              <text x={tx} y={ty} fontFamily="var(--ui-stack)" fontSize={10} fill={GOLD_NODE_LIGHT}>{asset.english_name}</text>
              <text x={tx} y={ty + 11} fontFamily="var(--mono-stack)" fontSize={8.5} fill="rgba(255,255,255,0.48)">{asset.asset_id}</text>
            </g>
          )
        })()}
      </svg>
    </div>
  )
}

export type { AssetWithState }
