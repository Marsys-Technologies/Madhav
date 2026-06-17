'use client'

import { useEffect, useRef } from 'react'
import type { AssetWithState } from './LiveDependencyGraph'
import type { ActiveRun } from '@/hooks/useActiveRun'

// ── Antique-gold palette (art constants — intentional literal values) ──────────
const GOLD_RING_IDLE = 'rgba(196,154,62,0.16)'
const GOLD_RING_LIVE = 'rgba(232,200,120,0.26)'
const GOLD_EDGE_HOVER = 'rgba(236,197,106,0.50)'
const GOLD_EDGE_FLOW = 'rgba(232,200,120,0.34)'

// ── Layers: one planet (graha) per layer, each on its own tilted great-ring ────
const LAYER_ORDER = ['brahmagyan', 'ganita', 'bodha', 'kala', 'phala', 'mimamsa'] as const
type Layer = typeof LAYER_ORDER[number]
const LAYER_NAMES: Record<string, string> = {
  brahmagyan: 'Brahma Jñāna', ganita: 'Gaṇita', bodha: 'Bodha',
  kala: 'Kāla', phala: 'Phala', mimamsa: 'Mīmāṃsā',
}
// radius (fraction of the pane's short side), 3-D ring tilt, and the planet's
// fixed seat-angle on its ring so the six bodies are spread, not aligned.
const RING: Record<string, { frac: number; tx: number; tz: number; seat: number }> = {
  brahmagyan: { frac: 0.150, tx: 0.34, tz: 0.00, seat: 0.0 },
  ganita:     { frac: 0.225, tx: -0.42, tz: 0.62, seat: 1.05 },
  bodha:      { frac: 0.290, tx: 0.52, tz: -0.50, seat: 2.10 },
  kala:       { frac: 0.345, tx: -0.22, tz: 1.02, seat: 3.15 },
  phala:      { frac: 0.395, tx: 0.66, tz: 0.34, seat: 4.20 },
  mimamsa:    { frac: 0.430, tx: 0.12, tz: -0.92, seat: 5.25 },
}
const CAM_TILT = 0.30
const RSEG = 80

// ── 3-D helpers ───────────────────────────────────────────────────────────────
type V3 = { x: number; y: number; z: number }
const rotX = (p: V3, a: number): V3 => { const c = Math.cos(a), s = Math.sin(a); return { x: p.x, y: c * p.y - s * p.z, z: s * p.y + c * p.z } }
const rotY = (p: V3, a: number): V3 => { const c = Math.cos(a), s = Math.sin(a); return { x: c * p.x + s * p.z, y: p.y, z: -s * p.x + c * p.z } }
const rotZ = (p: V3, a: number): V3 => { const c = Math.cos(a), s = Math.sin(a); return { x: c * p.x - s * p.y, y: s * p.x + c * p.y, z: p.z } }

const NS = 'http://www.w3.org/2000/svg'
const make = (t: string, a: Record<string, string | number>) => {
  const e = document.createElementNS(NS, t)
  for (const k in a) e.setAttribute(k, String(a[k]))
  return e
}
// SVG arc path (clockwise from startDeg to endDeg), used for the built-fraction ring.
function arcPath(cx: number, cy: number, r: number, frac: number): string {
  if (frac <= 0) return ''
  if (frac >= 0.999) {
    return `M ${cx} ${cy - r} A ${r} ${r} 0 1 1 ${cx - 0.01} ${cy - r} Z`
  }
  const a0 = -Math.PI / 2
  const a1 = a0 + frac * Math.PI * 2
  const x0 = cx + r * Math.cos(a0), y0 = cy + r * Math.sin(a0)
  const x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1)
  const large = frac > 0.5 ? 1 : 0
  return `M ${x0.toFixed(2)} ${y0.toFixed(2)} A ${r.toFixed(2)} ${r.toFixed(2)} 0 ${large} 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`
}

// ── Per-layer aggregate ─────────────────────────────────────────────────────
type LayerAgg = { count: number; state: string; builtFrac: number }
function aggregate(assets: AssetWithState[]): LayerAgg {
  const total = assets.length || 1
  const building = assets.some(a => a.state === 'building')
  const built = assets.filter(a => a.state === 'lit').length
  const stale = assets.some(a => a.state === 'stale')
  const state = building ? 'building' : built === 0 ? 'dormant' : stale ? 'stale' : 'lit'
  return { count: assets.length, state, builtFrac: built / total }
}

interface Props {
  assets: AssetWithState[]
  activeRun: ActiveRun | null
  onNodeClick: (assetId: string) => void
  /** Bidirectional bond: id of the row/bead hovered anywhere (shared with the table). */
  hoveredId?: string | null
  /** Called when a halo bead is hovered so the matching table row can light up. */
  onHover?: (assetId: string | null) => void
}

interface PlanetRefs { g: SVGGElement; atmo: SVGCircleElement; arc: SVGPathElement; main: SVGCircleElement; spec: SVGCircleElement; hit: SVGCircleElement }
interface BeadRefs { g: SVGGElement; main: SVGCircleElement; spec: SVGCircleElement; hit: SVGCircleElement }

export function ArmillaryGraph({ assets, activeRun, onNodeClick, hoveredId, onHover }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const ringsRef = useRef<SVGGElement>(null)
  const edgesRef = useRef<SVGGElement>(null)
  const planetsRef = useRef<SVGGElement>(null)
  const halosRef = useRef<SVGGElement>(null)
  const rootRef = useRef<SVGGElement>(null)
  const dustRef = useRef<SVGGElement>(null)
  const tipRef = useRef<HTMLDivElement>(null)

  const assetsRef = useRef(assets)
  const activeRunRef = useRef(activeRun)
  const onClickRef = useRef(onNodeClick)
  const onHoverRef = useRef(onHover)
  const dimsRef = useRef({ W: 400, H: 520 })
  const phiRef = useRef(0)
  // hover: either a specific asset (from a halo bead or a table row) or a whole layer (planet)
  const hoverRef = useRef<{ assetId: string | null; layer: Layer | null }>({ assetId: null, layer: null })
  const bloomRef = useRef<Map<Layer, number>>(new Map(LAYER_ORDER.map(l => [l, 0])))

  const ringElsRef = useRef<Record<string, SVGPathElement>>({})
  const planetMapRef = useRef<Map<Layer, PlanetRefs>>(new Map())
  const beadMapRef = useRef<Map<string, BeadRefs>>(new Map())

  assetsRef.current = assets
  activeRunRef.current = activeRun
  onClickRef.current = onNodeClick
  onHoverRef.current = onHover

  const idSignature = assets.map(a => a.asset_id).sort().join(',')

  // ── Build DOM when the set of assets changes ──
  useEffect(() => {
    const ringsG = ringsRef.current, planetsG = planetsRef.current, halosG = halosRef.current, dustG = dustRef.current
    if (!ringsG || !planetsG || !halosG || !dustG) return
    ringsG.replaceChildren(); planetsG.replaceChildren(); halosG.replaceChildren(); dustG.replaceChildren()

    // rings
    const ringEls: Record<string, SVGPathElement> = {}
    for (const L of LAYER_ORDER) {
      const p = make('path', { fill: 'none', stroke: GOLD_RING_IDLE, 'stroke-width': 0.8 }) as SVGPathElement
      ringsG.appendChild(p); ringEls[L] = p
    }
    ringElsRef.current = ringEls

    // dust
    for (let i = 0; i < 30; i++) {
      const c = make('circle', { cx: Math.random() * 100 + '%', cy: Math.random() * 100 + '%', r: 0.5 + Math.random() * 1.0, fill: '#6B4E18', opacity: 0.2 }) as SVGCircleElement
      c.style.animation = `armDust ${6 + Math.random() * 8}s ease-in-out ${Math.random() * 4}s infinite`
      dustG.appendChild(c)
    }

    // planets (one per layer)
    const pmap = new Map<Layer, PlanetRefs>()
    for (const L of LAYER_ORDER) {
      const g = make('g', { cursor: 'pointer', tabindex: 0, role: 'button', 'aria-label': `${LAYER_NAMES[L]} layer` }) as SVGGElement
      const atmo = make('circle', { r: 1, fill: 'url(#armAtmo)' }) as SVGCircleElement
      const arc = make('path', { fill: 'none', stroke: 'rgba(236,197,106,0.85)', 'stroke-width': 1.6, 'stroke-linecap': 'round' }) as SVGPathElement
      const main = make('circle', { r: 1, 'stroke-width': 1.5 }) as SVGCircleElement
      const spec = make('circle', { r: 1, fill: 'rgba(255,255,255,0.55)', opacity: 0 }) as SVGCircleElement
      const hit = make('circle', { r: 1, fill: 'transparent' }) as SVGCircleElement
      g.append(atmo, arc, main, spec, hit)
      g.addEventListener('pointerenter', () => layerEnter(L))
      g.addEventListener('pointerleave', () => layerLeave())
      g.addEventListener('focus', () => layerEnter(L))
      g.addEventListener('blur', () => layerLeave())
      g.addEventListener('click', () => {
        const first = assetsRef.current.find(a => a.layer === L)
        if (first) onClickRef.current(first.asset_id)
      })
      planetsG.appendChild(g)
      pmap.set(L, { g, atmo, arc, main, spec, hit })
    }
    planetMapRef.current = pmap

    // halo beads (one per asset, hidden until its layer blooms)
    const bmap = new Map<string, BeadRefs>()
    for (const a of assetsRef.current) {
      const g = make('g', { cursor: 'pointer', tabindex: 0, role: 'button', 'aria-label': `${a.english_name}, ${a.state}` }) as SVGGElement
      const main = make('circle', { r: 1, 'stroke-width': 1, opacity: 0 }) as SVGCircleElement
      const spec = make('circle', { r: 1, fill: 'rgba(255,255,255,0.5)', opacity: 0 }) as SVGCircleElement
      const hit = make('circle', { r: 1, fill: 'transparent' }) as SVGCircleElement
      g.append(main, spec, hit)
      g.addEventListener('pointerenter', () => beadEnter(a.asset_id))
      g.addEventListener('pointerleave', () => beadLeave())
      g.addEventListener('click', (e: Event) => { e.stopPropagation(); onClickRef.current(a.asset_id) })
      g.addEventListener('keydown', (e: KeyboardEvent) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClickRef.current(a.asset_id) } })
      halosG.appendChild(g)
      bmap.set(a.asset_id, { g, main, spec, hit })
    }
    beadMapRef.current = bmap
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idSignature])

  // ── Hover handlers (single source: hoverRef) ──
  function setTip(text: { title: string; sub: string; state: string; color: string } | null) {
    const tip = tipRef.current; if (!tip) return
    if (!text) { tip.style.opacity = '0'; return }
    tip.querySelector('.arm-sa')!.textContent = text.title
    tip.querySelector('.arm-id')!.textContent = text.sub
    const st = tip.querySelector('.arm-st') as HTMLElement
    st.textContent = text.state; st.style.color = text.color
    tip.style.opacity = '1'
  }
  const stateColor = (s: string) => s === 'lit' ? '#8FD49B' : s === 'building' ? '#E8C878' : s === 'stale' ? '#D2A23C' : '#7C725B'
  function applyAssetHover(id: string | null) {
    const a = id ? assetsRef.current.find(x => x.asset_id === id) : null
    hoverRef.current = { assetId: id, layer: a ? (a.layer as Layer) : null }
    setTip(a ? { title: a.sanskrit_name, sub: a.english_name, state: `● ${a.state}  ·  ${LAYER_NAMES[a.layer] ?? a.layer}`, color: stateColor(a.state) } : null)
  }
  function layerEnter(L: Layer) {
    hoverRef.current = { assetId: null, layer: L }
    const members = assetsRef.current.filter(a => a.layer === L)
    const agg = aggregate(members)
    const built = Math.round(agg.builtFrac * members.length)
    setTip({ title: LAYER_NAMES[L], sub: `${members.length} assets · ${built}/${members.length} built`, state: `● ${agg.state}`, color: stateColor(agg.state) })
  }
  function layerLeave() { hoverRef.current = { assetId: null, layer: null }; setTip(null) }
  function beadEnter(id: string) { applyAssetHover(id); onHoverRef.current?.(id) }
  function beadLeave() { applyAssetHover(null); onHoverRef.current?.(null) }

  // External bond: table-row hover → bloom that asset's layer + highlight the bead.
  useEffect(() => { applyAssetHover(hoveredId ?? null) }, [hoveredId])

  // ── Resize ──
  useEffect(() => {
    if (!containerRef.current) return
    const ro = new ResizeObserver(entries => {
      const e = entries[0]
      if (e) {
        const W = e.contentRect.width
        const H = e.contentRect.height > 100 ? e.contentRect.height : Math.round(W * 1.25)
        dimsRef.current = { W, H }
      }
    })
    ro.observe(containerRef.current)
    return () => ro.disconnect()
  }, [])

  // ── Main RAF loop ──
  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduce) phiRef.current = 0.42
    let raf = 0
    let last = performance.now()

    const tick = (now: number) => {
      const dt = Math.min((now - last) / 1000, 0.05); last = now
      const A = assetsRef.current
      const run = activeRunRef.current
      const isBuild = run != null
      if (!reduce) phiRef.current += (isBuild ? 0.10 : 0.05) * dt
      const PHI = phiRef.current
      const { W, H } = dimsRef.current
      const CX = W / 2, CY = H * 0.52
      const unit = Math.min(W, H)
      const FOC = unit * 1.05

      // group assets by layer + aggregate
      const byLayer = new Map<Layer, AssetWithState[]>()
      for (const L of LAYER_ORDER) byLayer.set(L, [])
      for (const a of A) { const arr = byLayer.get(a.layer as Layer); if (arr) arr.push(a) }
      const aggOf = new Map<Layer, LayerAgg>()
      for (const L of LAYER_ORDER) aggOf.set(L, aggregate(byLayer.get(L)!))

      // which layers should bloom: hovered layer + layers with a building asset
      const hov = hoverRef.current
      const buildingLayers = new Set<Layer>()
      for (const L of LAYER_ORDER) if (byLayer.get(L)!.some(a => a.state === 'building')) buildingLayers.add(L)
      // ease bloom toward target
      for (const L of LAYER_ORDER) {
        const target = (hov.layer === L || buildingLayers.has(L)) ? 1 : 0
        const cur = bloomRef.current.get(L) ?? 0
        const next = cur + (target - cur) * Math.min(1, dt * 6)
        bloomRef.current.set(L, Math.abs(next - target) < 0.002 ? target : next)
      }

      const ringPoint = (layer: string, theta: number): V3 => {
        const r = RING[layer]; const R = r.frac * unit
        let p: V3 = { x: Math.cos(theta) * R, y: Math.sin(theta) * R, z: 0 }
        p = rotX(p, r.tx); p = rotZ(p, r.tz)
        return p
      }
      const project = (p: V3) => { const s = FOC / (FOC - p.z); return { x: CX + p.x * s, y: CY + p.y * s, s, z: p.z } }

      // rings
      const ringEls = ringElsRef.current
      for (const L of LAYER_ORDER) {
        const el = ringEls[L]; if (!el) continue
        let d = ''
        for (let i = 0; i <= RSEG; i++) {
          const th = (i / RSEG) * Math.PI * 2
          let p = ringPoint(L, th); p = rotY(p, PHI); p = rotX(p, CAM_TILT)
          const pr = project(p)
          d += (i ? 'L' : 'M') + pr.x.toFixed(1) + ' ' + pr.y.toFixed(1) + ' '
        }
        el.setAttribute('d', d)
        el.setAttribute('stroke', (hov.layer === L) ? GOLD_RING_LIVE : isBuild ? 'rgba(212,170,80,0.20)' : GOLD_RING_IDLE)
      }

      // planet positions
      const planetPos: Record<string, { x: number; y: number; s: number; z: number; r: number }> = {}
      for (const L of LAYER_ORDER) {
        let p = ringPoint(L, RING[L].seat); p = rotY(p, PHI); p = rotX(p, CAM_TILT)
        const pr = project(p)
        const count = aggOf.get(L)!.count
        const baseR = unit * 0.024
        const sizeFactor = 0.72 + 0.5 * Math.sqrt(count / 22)
        planetPos[L] = { ...pr, r: baseR * sizeFactor * pr.s }
      }

      // depth-sort planets + ROOT (painter's algorithm)
      const planetsG = planetsRef.current!, rootG = rootRef.current!
      const order = [...LAYER_ORDER].sort((a, b) => planetPos[a].z - planetPos[b].z)
      let rootPlaced = false
      for (const L of order) {
        if (!rootPlaced && planetPos[L].z > 0) { planetsG.appendChild(rootG); rootPlaced = true }
        const pr = planetMapRef.current.get(L); if (pr) planetsG.appendChild(pr.g)
      }
      if (!rootPlaced) planetsG.appendChild(rootG)

      // draw planets
      for (const L of LAYER_ORDER) {
        const n = planetMapRef.current.get(L); if (!n) continue
        const pos = planetPos[L]; const agg = aggOf.get(L)!
        const isBuilding = agg.state === 'building'
        const isDormant = agg.state === 'dormant'
        const isLit = agg.state === 'lit'
        const fill = isDormant ? 'none' : isBuilding ? 'url(#armBuild)' : 'url(#armBead)'
        const stroke = isDormant ? 'rgba(107,78,24,0.7)' : agg.state === 'stale' ? 'rgba(166,108,52,0.8)' : isBuilding ? '#E8C878' : '#C49A3E'
        const focused = hov.layer === L
        const r = pos.r * (focused ? 1.12 : 1)
        const fade = pos.z < 0 ? 0.62 : 1
        const op = (isDormant ? 0.7 : 1) * fade
        n.main.setAttribute('cx', String(pos.x)); n.main.setAttribute('cy', String(pos.y))
        n.main.setAttribute('r', r.toFixed(2)); n.main.setAttribute('fill', fill); n.main.setAttribute('stroke', stroke)
        n.main.setAttribute('opacity', String(op)); n.main.setAttribute('filter', isBuilding ? 'url(#armGlow)' : '')
        n.atmo.setAttribute('cx', String(pos.x)); n.atmo.setAttribute('cy', String(pos.y))
        n.atmo.setAttribute('r', (r * (isBuilding ? 3.0 : 2.4)).toFixed(2)); n.atmo.setAttribute('opacity', String(isDormant ? 0.25 : op * 0.95))
        // built-fraction arc (partial layers)
        n.arc.setAttribute('d', (!isDormant && agg.builtFrac > 0 && agg.builtFrac < 0.999) ? arcPath(pos.x, pos.y, r + 3.5, agg.builtFrac) : '')
        n.arc.setAttribute('opacity', String(0.8 * fade))
        const showSpec = isLit || isBuilding
        n.spec.setAttribute('cx', (pos.x - r * 0.3).toFixed(2)); n.spec.setAttribute('cy', (pos.y - r * 0.3).toFixed(2))
        n.spec.setAttribute('r', (r * 0.26).toFixed(2)); n.spec.setAttribute('opacity', String(showSpec ? op * 0.85 : 0))
        n.hit.setAttribute('cx', String(pos.x)); n.hit.setAttribute('cy', String(pos.y)); n.hit.setAttribute('r', (r + 8).toFixed(2))
      }

      // ROOT sun
      rootG.setAttribute('transform', `translate(${CX},${CY})`)
      const rootR = unit * 0.042
      const rm = rootG.querySelector('.arm-root-main') as SVGCircleElement
      const ra = rootG.querySelector('.arm-root-atmo') as SVGCircleElement
      const rs = rootG.querySelector('.arm-root-spec') as SVGCircleElement
      if (rm) rm.setAttribute('r', rootR.toFixed(2))
      if (ra) ra.setAttribute('r', (rootR * (isBuild ? 3.6 : 3.0)).toFixed(2))
      if (rs) { rs.setAttribute('cx', (-rootR * 0.32).toFixed(2)); rs.setAttribute('cy', (-rootR * 0.32).toFixed(2)); rs.setAttribute('r', (rootR * 0.26).toFixed(2)) }

      // halo beads — fan out around their layer-planet, scaled by bloom
      for (const a of A) {
        const n = beadMapRef.current.get(a.asset_id); if (!n) continue
        const L = a.layer as Layer
        const bloom = bloomRef.current.get(L) ?? 0
        if (bloom < 0.01) {
          n.main.setAttribute('opacity', '0'); n.spec.setAttribute('opacity', '0')
          n.g.setAttribute('pointer-events', 'none')
          continue
        }
        n.g.setAttribute('pointer-events', 'auto')
        const members = byLayer.get(L)!
        const idx = members.indexOf(a)
        const cnt = members.length
        const planet = planetPos[L]
        const ang = (idx / cnt) * Math.PI * 2 + PHI * 0.6
        const haloR = (planet.r + 8) + planet.r * 2.4 * bloom
        const bx = planet.x + Math.cos(ang) * haloR
        const by = planet.y + Math.sin(ang) * haloR
        const isFocused = a.asset_id === hov.assetId
        const beadR = (unit * 0.011) * planet.s * (0.5 + 0.5 * bloom) * (isFocused ? 1.6 : 1)
        const isDormant = a.state === 'dormant' || a.state === 'not_migrated'
        const isBuilding = a.state === 'building'
        const fill = isDormant ? 'none' : isBuilding ? 'url(#armBuild)' : 'url(#armBead)'
        const stroke = isDormant ? 'rgba(107,78,24,0.7)' : a.state === 'stale' ? 'rgba(166,108,52,0.8)' : isBuilding ? '#E8C878' : '#C49A3E'
        const dimOther = hov.assetId && !isFocused
        const op = (isDormant ? 0.6 : 1) * bloom * (dimOther ? 0.4 : 1)
        n.main.setAttribute('cx', bx.toFixed(2)); n.main.setAttribute('cy', by.toFixed(2)); n.main.setAttribute('r', beadR.toFixed(2))
        n.main.setAttribute('fill', fill); n.main.setAttribute('stroke', stroke); n.main.setAttribute('opacity', String(op))
        n.main.setAttribute('filter', isBuilding ? 'url(#armGlow)' : '')
        const showSpec = (a.state === 'lit' || isBuilding)
        n.spec.setAttribute('cx', (bx - beadR * 0.3).toFixed(2)); n.spec.setAttribute('cy', (by - beadR * 0.3).toFixed(2))
        n.spec.setAttribute('r', (beadR * 0.28).toFixed(2)); n.spec.setAttribute('opacity', String(showSpec ? op * 0.8 : 0))
        n.hit.setAttribute('cx', bx.toFixed(2)); n.hit.setAttribute('cy', by.toFixed(2)); n.hit.setAttribute('r', (beadR + 6).toFixed(2))
        // thin tether from planet to bloomed bead
      }

      // contextual edges — layer→layer dependencies (hovered layer's chain, or build flow)
      const edgesG = edgesRef.current!
      edgesG.replaceChildren()
      // build the set of unique inter-layer edges
      const layerEdges = new Set<string>()
      for (const a of A) for (const d of (a.depends_on ?? [])) {
        const dep = A.find(x => x.asset_id === d)
        if (dep && dep.layer !== a.layer) layerEdges.add(`${dep.layer}>${a.layer}`)
      }
      const drawEdge = (from: Layer | 'ROOT', to: Layer, col: string, w: number, flow: boolean) => {
        const fp = from === 'ROOT' ? { x: CX, y: CY } : planetPos[from]
        const tp = planetPos[to]
        if (!fp || !tp) return
        const mx = (fp.x + tp.x) / 2, my = (fp.y + tp.y) / 2 - 24
        const path = make('path', { d: `M${fp.x} ${fp.y} Q ${mx} ${my} ${tp.x} ${tp.y}`, fill: 'none', stroke: col, 'stroke-width': w })
        if (flow) { path.setAttribute('stroke-dasharray', '4 4'); path.setAttribute('stroke-dashoffset', String((-now / 40) % 8)) }
        edgesG.appendChild(path)
      }
      if (hov.layer) {
        for (const key of layerEdges) {
          const [f, t] = key.split('>') as [Layer, Layer]
          if (f === hov.layer || t === hov.layer) drawEdge(f, t, GOLD_EDGE_HOVER, 1.0, false)
        }
      } else if (isBuild) {
        for (const key of layerEdges) {
          const [f, t] = key.split('>') as [Layer, Layer]
          if (buildingLayers.has(t) || buildingLayers.has(f)) drawEdge(f, t, GOLD_EDGE_FLOW, 0.9, true)
        }
      }

      // tooltip follows the hovered planet / bead
      const tip = tipRef.current
      if (tip && tip.style.opacity === '1') {
        let p: { x: number; y: number } | null = null
        if (hov.assetId) { const a = A.find(x => x.asset_id === hov.assetId); if (a) { const L = a.layer as Layer; p = planetPos[L] } }
        else if (hov.layer) p = planetPos[hov.layer]
        if (p) {
          const tipW = tip.offsetWidth || 160, tipH = tip.offsetHeight || 40
          const lx = Math.max(tipW / 2 + 4, Math.min(W - tipW / 2 - 4, p.x))
          const flip = p.y < tipH + 14
          tip.style.left = `${lx}px`; tip.style.top = `${flip ? p.y + 14 : p.y - 12}px`
          tip.style.transform = flip ? 'translate(-50%, 0)' : 'translate(-50%, -120%)'
        }
      }

      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [])

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%', height: '100%', position: 'relative',
        background: 'radial-gradient(ellipse at 50% 52%, rgba(16,12,8,0.0) 35%, rgba(4,3,1,0.55) 100%)',
      }}
    >
      <style>{`
        @keyframes armDust{0%,100%{opacity:.16}50%{opacity:.40}}
        @keyframes armSun{0%,100%{filter:drop-shadow(0 0 16px rgba(236,197,106,.42))}50%{filter:drop-shadow(0 0 28px rgba(236,197,106,.64))}}
      `}</style>
      <svg width="100%" height="100%" style={{ display: 'block', overflow: 'visible' }}>
        <defs>
          <radialGradient id="armBead" cx="35%" cy="30%" r="75%">
            <stop offset="0%" stopColor="#F4E3B0" /><stop offset="45%" stopColor="#C49A3E" /><stop offset="100%" stopColor="#5C3F12" />
          </radialGradient>
          <radialGradient id="armBuild" cx="35%" cy="30%" r="75%">
            <stop offset="0%" stopColor="#FFF3CE" /><stop offset="45%" stopColor="#E8C878" /><stop offset="100%" stopColor="#8A5E12" />
          </radialGradient>
          <radialGradient id="armRoot" cx="36%" cy="30%" r="82%">
            <stop offset="0%" stopColor="#FFFCEF" /><stop offset="34%" stopColor="#F4D98A" /><stop offset="70%" stopColor="#D2A23C" /><stop offset="100%" stopColor="#5C3F12" />
          </radialGradient>
          <radialGradient id="armAtmo" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#C49A3E" stopOpacity="0.16" /><stop offset="100%" stopColor="#C49A3E" stopOpacity="0" />
          </radialGradient>
          <filter id="armGlow" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="1.6" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        <g ref={dustRef} />
        <g ref={ringsRef} />
        <g ref={edgesRef} />
        <g ref={halosRef} />
        <g ref={planetsRef} />
        <g ref={rootRef} style={{ animation: 'armSun 5s ease-in-out infinite' }}>
          <circle className="arm-root-atmo" r="40" fill="url(#armAtmo)" />
          <circle className="arm-root-main" r="20" fill="url(#armRoot)" stroke="#D2A23C" strokeWidth="1.5" />
          <circle className="arm-root-spec" cx="-7" cy="-7" r="5" fill="rgba(255,255,255,0.72)" />
        </g>
      </svg>
      <div
        ref={tipRef}
        style={{
          position: 'absolute', pointerEvents: 'none', opacity: 0, transition: 'opacity 0.12s',
          transform: 'translate(-50%, -120%)', background: 'rgba(14,11,6,0.94)',
          border: '1px solid rgba(196,154,62,0.34)', borderRadius: '6px', padding: '7px 10px',
          maxWidth: '210px', lineHeight: 1.3, zIndex: 5,
        }}
      >
        <div className="arm-sa" style={{ fontFamily: 'var(--display-stack, "Cormorant Garamond", serif)', fontVariant: 'small-caps', fontSize: '15px', color: 'var(--gold-high, #ECC56A)', letterSpacing: '0.03em' }} />
        <div className="arm-id" style={{ fontFamily: 'var(--ui-stack)', fontSize: '11px', color: 'var(--on-dark-mut, #B9AE93)', marginTop: '1px' }} />
        <div className="arm-st" style={{ fontFamily: 'var(--mono-stack)', fontSize: '9.5px', marginTop: '3px' }} />
      </div>
    </div>
  )
}
