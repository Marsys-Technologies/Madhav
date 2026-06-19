---
title: Nirmāṇa Build-Tracker UI/UX Enhancement Report
status: DRAFT
version: 1.0
date: 2026-06-17
author: Opus 4.8 (design audit)
scope: cockpit/v2 Nirmāṇa page
---

# Nirmāṇa Build-Tracker — UI/UX Enhancement Report

> Report only. No component was edited. All `file:line` references are against `platform/src/...` at the time of audit. Token values are quoted from `src/lib/styles/marsys-theme.css` and `src/app/globals.css`.

---

## 1. Executive summary

Nirmāṇa is already a competent dark operator dashboard, but it currently reads as a *table with a decorative diagram bolted to one side*, not as a single living instrument. The two halves do not yet speak to each other: the left pane is a precise, well typed asset ledger; the right pane is a quiet orbital diagram that only wakes during builds and otherwise sits inert. The path to elevation is not more ornament, it is *coherence and life*: a small shared motion vocabulary applied consistently, a sphere graph that breathes at idle and choreographs a real ignition during builds, and a bidirectional bond between row and bead so hovering one lights the other. We should also retire three brand-law smells already in the code: the `borderLeft: 3px solid <layercolor>` side stripe on every layer header (`LayerPanel.tsx:109`), the multi-hue layer palette that imports sapphire/emerald/teal/amethyst into a "Committed gold-on-black" identity (`LayerPanel.tsx:15-22` and `LiveDependencyGraph` edge tiers), and the `type:'spring'` overshoot in `MiniDAG.tsx:145`. The dark theme is unambiguously correct here, an operator watches a multi-minute build in a low-light focused session, so depth must come from value and chroma steps in the gold ramp rather than new colors. The single highest-leverage move is the sphere: it is the page's emotional center and is currently under-animated relative to its visual prominence. With a disciplined raw-RAF orbital engine plus a Framer-orchestrated ignition timeline, Nirmāṇa can become the kind of instrument an acharya would describe as *alive without being busy*.

---

## 2. Current-state assessment, per component

### 2.1 Page shell + route — `page.tsx`, `CockpitShell.tsx`
**Strengths.** Clean server-prefetch of chart meta (`page.tsx:40-44`) avoids a "Loading chart…" flash. The `॥ Nirmāṇa ॥` display heading with serif daṇḍa marks (`page.tsx:57-61`) is exactly the classical register the brand wants. The shell is a disciplined flex column at `height:100vh` with `overflow:hidden` (`CockpitShell.tsx:113-124`).

**Weaknesses.**
- `console.log('[Shell] render …')` ships to production (`CockpitShell.tsx:52`). Remove.
- Tab body swaps are instant conditional renders (`CockpitShell.tsx:140-151`); there is no cross-fade or directional slide, so switching tabs feels like a hard cut. No `AnimatePresence`.
- The "Enable Pro view to access this tab" empty message (`CockpitShell.tsx:147-151`) is plain centered text with no iconography or affordance pointing at the ◆ Pro pill that toggles it.

### 2.2 Header + telemetry — `CockpitHeader.tsx`
**Strengths.** Good information density: name + ◆ Pro + subtitle on the left, action cluster on the right, telemetry strip below. The mono telemetry strip (`CockpitHeader.tsx:204-234`) is the right *idea*.

**Weaknesses.**
- **The ◆ glyph is a literal lozenge character in a string** (`CockpitHeader.tsx:142`, `'◆ Pro'`). Brand law permits the sun-node / sacred-geometry motif only; a bare Unicode diamond is an uncontrolled decorative mark. Replace with a 1px-stroke inline SVG sun-node or four-point star drawn to the same spec as the `TabBar` icons.
- **Telemetry is a static readout, not instrument-like.** Values are plain text spans; `BUILD running` only recolors to `#60a5fa` (a raw blue hex, `CockpitHeader.tsx:226`) with no pulse, count, or motion. There is no sense of *flow* (queue depth changing, writers spinning up). This is the single biggest "competent dashboard, not instrument" tell in the header.
- **Hardcoded hexes break the OKLCH token discipline:** `#60a5fa` (line 226) and the `rgba(168,124,42,…)` Pro-pill backgrounds (lines 130-131) are off-ramp. The Pro pill should use the gold ramp tokens (`--gold-core`, `--gold-engrave`).
- The trash icon uses Tailwind `hover:bg-red-500/20 text-red-400` (`CockpitHeader.tsx:195`) — a raw Tailwind red rather than the brand `--marsys-error` (#B5474C). Destructive affordances should still speak the brand's muted garnet, not a generic alert red.
- Sidecar health polls every 30s with no visible "checking" state beyond a `…` glyph (`CockpitHeader.tsx:71-75`).

### 2.3 Tab bar — `TabBar.tsx`
**Strengths.** Hand-drawn 1.5px-stroke SVG icons on a 24px grid with `currentColor` (`TabBar.tsx:12-73`) are on-brand and crisp. Active state uses a 2px `--gold-engrave` bottom border (`TabBar.tsx:111-113`).

**Weaknesses.**
- The active underline is a static border swap; there is no shared *animated* underline that slides between tabs (the classic "magic ink" `layoutId` move Framer makes trivial). With only 1-3 tabs this is a cheap, high-polish win.
- `transition: 'color 0.15s, background 0.15s'` (`TabBar.tsx:117`) animates `background`, which is fine, but the border has no transition so the active indicator pops.

### 2.4 Layer panels — `LayerPanel.tsx`
**Strengths.** Bilingual two-line header (22px serif gold Sanskrit over 14px English, `LayerPanel.tsx:118-141`) is the strongest typographic moment on the page. The metric group with a hairline divider between "N assets" and "N rows" (`LayerPanel.tsx:148-157`) is genuinely instrument-like and should be a model for the rest of the page.

**Weaknesses.**
- **BRAND-LAW VIOLATION — the 3px colored side stripe.** `borderLeft: \`3px solid ${LAYER_COLOR[layer]}\`` (`LayerPanel.tsx:109`) is exactly the "side-stripe border >1px as colored accent" the brand laws ban. Worse, the colors are jewel hues (`#6B9FD4` sapphire, `#5BAF7A` emerald, `#4AAFAF` teal, `#9B7FD4` amethyst — `LayerPanel.tsx:15-22`) that fracture the gold-on-black identity. *Proposed alternative:* a 1px gold-hairline divider with a small sun-node at the left edge (the brand's sanctioned "gold hairline with a sun node" motif), where layer identity is conveyed by a single-character serif index or a value-step in the gold ramp, not a hue.
- **Expand/collapse is instant** (`LayerPanel.tsx:60`, `useState(expanded)`; `:207` `{expanded && …}`). No height/opacity animation. The chevron is a literal `▼`/`▶` text glyph (`LayerPanel.tsx:114`) rather than a rotating SVG caret. This is the most jarring "no motion system" moment after tab switching.
- The action cluster (Build/Refresh/Stop/Delete) re-renders identically at three scopes (header/layer/row) with subtle size differences; there's monotony but it is *defensible* monotony (consistency of an instrument). Not a priority.

### 2.5 Asset rows + progress bars — `AssetRow.tsx`, `AssetProgressBar.tsx`
**Strengths.** The `StatusDot` (`AssetRow.tsx:87-124`) collapsing a text chip into a single glowing dot is a good restraint move. The highlight-on-focus uses `inset box-shadow` + background with a 0.4s ease transition (`AssetRow.tsx:155-157`) — correct, animates compositor-friendly properties. The progress bar's building-shimmer sweep (`AssetProgressBar.tsx:51-63`) animates `left` across an overflow-hidden mask, which is acceptable.

**Weaknesses.**
- **Rows do not animate in.** When a layer expands, all rows appear at once with no stagger (`LayerPanel.tsx:236-256` maps directly to `AssetRowComponent`). A 30-40ms stagger would make expansion feel intentional.
- **The progress fill animates `width`** (`AssetProgressBar.tsx:44-48`, `animate={{ width: \`${pct}%\` }}`). This is a layout-triggering property; the brand law says animate transform/opacity only. For a thin bar at this scale it is cheap, but the correct form is a `scaleX` transform on a full-width fill with `transformOrigin:left`.
- **Building pill color is blue.** `pillColor: 'rgba(120,180,255,0.9)'` for the building state (`AssetProgressBar.tsx:15`) introduces a cool blue into a gold instrument. The building state should read as *hot gold* (the bar is literally filling with gold), not blue. Same blue recurs in `ServiceHealthPill` (`AssetRow.tsx:49`).
- The numeric overlay reserves a fixed `pr-[60px]` for the pill (`AssetProgressBar.tsx:70`); at narrow widths the centered number can still crowd. Minor.
- Error text is hard-truncated to 24/28 chars (`AssetRow.tsx:211`, `:77`) with no tooltip on the truncated remainder. The full error only shows on the service pill `title`.

### 2.6 The sphere graph — `LiveDependencyGraph.tsx` (see §3 for the deep dive)
**Strengths.** Genuinely the most ambitious component: deterministic node placement (`nodePosition`, `:61-76`), edge tiering (`:88-104`), depth vignette (`:310`), particle dust (`:269-276`), atmosphere discs, specular highlights, hover up/down-stream closure dimming (`:244-266`), reduced-motion respect (`useReducedMotion`, `:145`), and a clean separation between CSS-keyframe infinite loops (`bead-breathe`, `poly-pulse`) and JS RAF (`globals.css:1029-1043`).

**Weaknesses (summarized; expanded in §3).**
- **Dead at idle.** Orbital drift only runs when `isActiveRun` (`:170-185`). With no build, the sphere is static save for particle dust and the CSS bead-breathe on already-lit nodes. The page's centerpiece is motionless most of the time.
- **No depth sorting.** Beads render in `assets.map` order (`:464`), so back-orbit beads can paint over the ROOT and front beads, breaking the 3D read. There is no painter's-algorithm sort by computed `cy`/scale.
- **Orbit drift mutates React state every frame.** `setOrbitAngle` in the RAF tick (`:178`) re-runs the entire `posMap` `useMemo` and re-renders every node/edge each frame — expensive at 50+ nodes. This should drive a `<g transform>` or imperative attribute updates, not React state.
- **Build "choreography" is flat.** All building nodes pulse simultaneously with a per-index delay (`:508-514`), and flowing edges shimmer, but there is no *topological ignition* — ROOT does not pulse first, edges do not light in dependency order, the target does not flare on completion.
- **ROOT lacks presence.** It is a static gradient circle with a specular dot (`:566-579`). No breathing, no rotating specular sweep, no bloom. For the literal root of the instrument it is underweight.
- Jewel-hue edge/node imports (`GOLD_NODE_*` is fine; but the layer-color system elsewhere leaks in). Edge tiers are all gold-family here (good).

### 2.7 Modals — `PlanModal.tsx`, `MiniDAG.tsx`, `ClearConfirmModal.tsx`
- **No entrance animation on PlanModal/ClearConfirmModal.** The modal is a plain conditional with a click-outside backdrop (`PlanModal.tsx:90`) — no `AnimatePresence`, no scale/opacity in, no backdrop fade. Modal-as-hard-cut.
- **BRAND-LAW VIOLATION — spring overshoot.** `MiniDAG.tsx:145` uses `transition={{ …, type: 'spring' }}` on node entrance, producing elastic overshoot the motion laws ban ("no bounce, no elastic, no spring overshoot"). Replace with an ease-out exponential tween.

### 2.8 Loading / empty / error / first-run states
- **No first-run / unbuilt-chart state.** A brand-new chart shows six collapsed layer panels with "— rows" and a sphere of dormant outline beads. There is no welcoming "This instrument has not been built. Begin with Brahma Jñāna." moment. This is the single biggest *empty-state* gap.
- Loading is bare text ("Loading assets…", `DataAssetsView.tsx:142-154`; "Loading dependency graph…", `:26-29`) — no skeleton, no shimmer.
- Error is bare red text (`DataAssetsView.tsx:157-170`).
- `AgentsView`/`WorkflowView` empty copy is serviceable but contains an em dash in UI microcopy ("No active agents — build may be queued…", `AgentsView.tsx:120`), which the copy law bans (use a comma or period).

### 2.9 Responsiveness + accessibility
- The 60/40 split is `flex: '0 0 60%'` / `'0 0 40%'` (`DataAssetsView.tsx:202,230`) with no breakpoint; on a narrow viewport the sphere pane becomes too small to read and the table columns crush. No stacking behavior.
- **A11y gaps:** the layer header is a clickable `<div>` (`LayerPanel.tsx:100`) not a `<button>`, with no `role`, `aria-expanded`, or keyboard handler — expand/collapse is mouse-only. The chevron is a decorative text glyph with no `aria-hidden`. The sphere `<g>` nodes are clickable but not keyboard-focusable and have no `role`/`aria-label`. The telemetry strip has no `aria-live` so screen readers never hear BUILD state changes.
- Focus-visible styling is not defined for the icon buttons.

### 2.10 Brand-law violation register (consolidated)
| # | Violation | Location | Law |
|---|---|---|---|
| V1 | 3px colored side-stripe border | `LayerPanel.tsx:109` | side-stripe >1px colored accent — banned |
| V2 | Jewel multi-hue layer palette | `LayerPanel.tsx:15-22` | gold-on-black identity; no new hues |
| V3 | Spring overshoot on node entrance | `MiniDAG.tsx:145` | no spring/elastic/bounce |
| V4 | Blue building-state color | `AssetProgressBar.tsx:15`, `AssetRow.tsx:49`, `CockpitHeader.tsx:226` | no off-ramp hues |
| V5 | Literal ◆ glyph as decoration | `CockpitHeader.tsx:142` | sacred-geometry motif only |
| V6 | Em dash in UI microcopy | `AgentsView.tsx:120` | no em dashes in microcopy |
| V7 | Raw Tailwind red on destructive | `CockpitHeader.tsx:195` | use `--marsys-error` |
| V8 | `width` animation (layout prop) | `AssetProgressBar.tsx:44` | animate transform/opacity only |
| V9 | `console.log` in production | `CockpitShell.tsx:52` | hygiene |

---

## 3. The sphere / orbital animation deep-dive (top priority)

The `LiveDependencyGraph` is the soul of Nirmāṇa. Today it is a precise static diagram that animates only during builds. The goal: a graph that is **quietly alive at idle, and dramatically choreographed during a build**, within "restraint over ornament."

### 3.1 Orbital mechanics — continuous Keplerian drift

**Problem.** Drift runs only when `isActiveRun` (`:170-185`), and it drives React state (`setOrbitAngle`), forcing a full `posMap` recompute + re-render every frame (`:202-210`).

**Proposal.**
1. **Idle ambient drift, very slow.** Each orbit ring gets its own angular velocity — inner rings faster, outer slower (a Keplerian falloff `ω ∝ 1/r^1.5`). At idle, scale all velocities down to ~8-15% of build speed so the field *breathes* rather than spins. Respect `prefers-reduced-motion` by freezing to the static layout (already the pattern).
2. **Per-layer angular velocity.** Replace the single `ORBIT_DEG_PER_SEC = 3` (`:151`) with a per-layer map keyed off orbit radius.
3. **Drive transforms, not React state.** Rotate each orbit ring's nodes inside a `<g>` via an imperatively-updated `transform={rotate(θ, cx, cy)}` (or per-node attribute writes through `ref`s), so the RAF loop never calls `setState`. This is the single biggest perf fix and is what makes 50+ nodes at 60fps trivial.
4. **Subtle 3D tilt / parallax.** The orbits are already elliptical (`ry < rx`, `:30-37`) which reads as a tilted plane. Add a slow ±2° wobble to the global tilt and a depth-based parallax: nodes nearer the viewer (larger `sin` of orbital phase) translate slightly more on tilt than far ones.

```tsx
// Per-layer angular velocity (deg/sec), Keplerian-ish falloff by orbit radius.
const OMEGA: Record<string, number> = {
  brahmagyan: 6.0, ganita: 4.2, bodha: 3.2, kala: 2.6, phala: 2.2, mimamsa: 1.8,
}
const IDLE_SCALE = 0.12 // idle drift is 12% of build-speed

// One ref per layer-ring <g>; RAF writes transform directly, no React state.
const ringRefs = useRef<Record<string, SVGGElement | null>>({})
useEffect(() => {
  if (prefersReducedMotion) return
  let raf = 0, last = performance.now()
  const tick = (t: number) => {
    if (document.hidden) { raf = requestAnimationFrame(tick); last = t; return } // throttle hidden
    const dt = (t - last) / 1000; last = t
    const scale = isActiveRun ? 1 : IDLE_SCALE
    for (const layer of LAYER_ORDER) {
      const g = ringRefs.current[layer]; if (!g) continue
      const prev = parseFloat(g.dataset.theta ?? '0')
      const next = (prev + OMEGA[layer] * scale * dt) % 360
      g.dataset.theta = String(next)
      g.setAttribute('transform', `rotate(${next} ${W/2} ${H*0.55})`)
    }
    raf = requestAnimationFrame(tick)
  }
  raf = requestAnimationFrame(tick)
  return () => cancelAnimationFrame(raf)
}, [isActiveRun, prefersReducedMotion, W, H])
```

> Note: wrapping each layer's beads in a single `<g transform="rotate(...)">` requires nodes to be positioned at their orbit *without* the `orbitOffset` baked in (set `orbitOffset=0` in `nodePosition`, `:66`), letting the group transform supply rotation. Labels/tooltips must counter-rotate or be rendered in a non-rotating overlay layer so text stays upright.

### 3.2 Depth sorting (painter's algorithm)

**Problem.** Nodes paint in array order (`:464`), so a far bead can cover ROOT.

**Proposal.** Before render, sort the node list by depth = the orbital phase's `cos` (the same term that already computes `cy`, `:74`). Back-half beads (behind ROOT) render first, dimmer and slightly smaller; front-half beads render last, larger and brighter. ROOT renders between the two halves so back beads pass *behind* it.

```tsx
// depth in [-1,1]: -1 = far (behind ROOT), +1 = near (in front)
function depthOf(phase: number) { return -Math.cos(phase) }
const ordered = [...assets].sort((a, b) => depthOf(phaseOf(a)) - depthOf(phaseOf(b)))
// then: const d = depthOf(phase); r *= (0.85 + 0.15*(d+1)/2); opacity *= (0.6 + 0.4*(d+1)/2)
```

This single change does more for the "real orbital field" feeling than any amount of glow.

### 3.3 The ROOT sphere — real presence

ROOT (`:566-579`) should feel like the still point the whole instrument turns around.
- **Slow breathing glow.** A second, larger atmosphere disc whose opacity oscillates 0.10→0.18 over ~6s (CSS keyframe, GPU-composited). Distinct from bead-breathe so ROOT has its own, slower rhythm.
- **Rotating specular sweep.** Replace the static specular dot (`:576`) with a small bright arc that slowly orbits the sphere's surface (a `<circle>` whose `cx/cy` follow a tiny circle via the same RAF), suggesting a light source moving over a burnished orb. Keep it ≤20% of ROOT radius so the sphere stays legible.
- **Atmosphere bloom on build.** When a run starts, ROOT's atmosphere disc briefly expands and brightens (the ignition cue — see §3.4).

### 3.4 Build choreography — the ignition sequence

Today every building node pulses at once. Replace with a **topologically ordered ignition timeline**, the page's signature moment:

1. **t=0 ROOT pulse + atmosphere bloom.** ROOT scales 1→1.12→1, atmosphere brightens. "The instrument wakes."
2. **t≈0.2s edges light in topological order.** Walk the build plan (`activeRun.plan`) in order; each edge into a to-be-built node lights with the flow-shimmer (`:427-446`), staggered by topological depth, not array index `i*0.05` (`:458`).
3. **per-asset target flare on completion.** When an asset transitions to `lit` (SSE `asset.state_change`, already handled in `DataAssetsView.tsx:64-73`), that bead does a one-shot flare: scale 1→1.25→1 with a brief glow-filter bump, then settles. This is the reward signal the operator watches for.
4. **ripple settle.** After the flare, a faint expanding ring emanates from the bead and fades (one-shot `<circle>` r:0→r*3, opacity 0.4→0), then the field returns to its building drift.

This is a *timeline* — sequenced, dependency-aware, one-shot per asset — which is exactly where Framer's declarative loops get clunky and a timeline library (or a small hand-rolled scheduler) shines.

### 3.5 Idle life (restraint over ornament)

At idle: the very-slow orbital drift (§3.1 at 12% speed), the existing particle dust, and ROOT's slow breathing glow. That is *enough*. No flowing edges, no node pulses at idle. The contrast between this hush and the build ignition is what makes the build feel significant.

### 3.6 Library recommendation

| Option | Where it shines | Cost |
|---|---|---|
| **Framer Motion (installed)** | React-idiomatic node mount/unmount, hover dimming, the AssetProgressBar/modal/tab motion. `useAnimationFrame` exists. | Timeline *orchestration* (sequenced ignition, per-asset one-shots keyed off SSE) is clunky; infinite RAF that mutates many SVG attrs fights React's render model. |
| **GSAP (new dep)** | `gsap.timeline()` for the ignition sequence; `gsap.ticker` for one shared throttled RAF; MotionPath for true orbital paths; per-target tweens off SSE events without re-render. Purpose-built for exactly §3.4. | New dependency (~`gsap` core ~50KB min+gz for what we'd use); a second animation mental model alongside Framer; team must learn it. |
| **Raw RAF + CSS keyframes** | The continuous orbital drift (§3.1) and ROOT breathing (§3.3) — zero deps, full control, already the pattern (`bead-breathe`). | Hand-rolling the ignition *timeline* and per-asset one-shots is real work and error-prone. |

**Recommendation: a split, not a single winner.**
- **Keep Framer Motion** for all React-lifecycle motion (row enter, tab underline, modal in/out, progress fills, hover closure dimming). It is installed and idiomatic.
- **Drive the continuous orbital engine + ROOT breathing with raw RAF + CSS** (§3.1, §3.3) — no new dependency, best perf, matches the existing `bead-breathe` precedent.
- **Adopt GSAP *only if* the build-ignition timeline (§3.4) proves too unwieldy in hand-rolled form.** GSAP earns its bundle specifically for the sequenced, dependency-ordered, SSE-triggered one-shot choreography and nothing else. If we install it, scope it to `LiveDependencyGraph` and lazy-load it inside the already-`dynamic` import (`DataAssetsView.tsx:21-31`) so it never enters the main bundle.

Net: **no install required for the highest-impact 80% (idle drift, depth sort, ROOT presence).** Reserve GSAP as a surgical, lazy-loaded add for the ignition timeline if and only if we build that.

### 3.7 Performance + a11y guardrails
- Transform/opacity only; never animate SVG geometry attrs in a loop where a `<g transform>` will do.
- `will-change: transform` on the rotating ring `<g>`s and ROOT.
- One shared RAF (not one per effect); bail when `document.hidden` (sketch in §3.1).
- Full `prefers-reduced-motion` path: freeze to static layout, keep states legible, no drift/pulse/flare (extend the existing `prefersReducedMotion` guards).
- Make nodes keyboard-reachable: render each `<g>` with `tabIndex={0}`, `role="button"`, `aria-label={\`${english_name}, ${state}\`}`, and an `onKeyDown` Enter/Space → `onNodeClick`.

---

## 4. Page-wide motion system

Define a tiny token vocabulary once (e.g. `src/lib/components/cockpit/v2/motion.ts`) and apply it everywhere. Exponential ease-out, no springs.

```ts
// motion.ts — the Nirmāṇa motion vocabulary
export const EASE = {
  out:   [0.16, 1, 0.3, 1]   as const, // expo-out: decisive arrival, no overshoot
  inOut: [0.83, 0, 0.17, 1]  as const, // quint in-out: for reversible (expand/collapse)
}
export const DUR = { micro: 0.12, base: 0.22, panel: 0.32, modal: 0.26 }
export const STAGGER = 0.035 // 35ms row/edge rhythm
```

**Apply to:**
- **Tab switch** — a shared sliding underline via `layoutId`, plus a 0.12s cross-fade of the body:
```tsx
// TabBar active indicator (replaces static borderBottom, TabBar.tsx:111-113)
{isActive && (
  <motion.div layoutId="tab-underline"
    style={{ position:'absolute', left:0, right:0, bottom:0, height:2, background:'var(--gold-engrave)' }}
    transition={{ duration: DUR.base, ease: EASE.out }} />
)}
```
- **Panel expand/collapse** (currently instant, `LayerPanel.tsx:207`) — animate `height:auto` + opacity, and rotate the chevron:
```tsx
<AnimatePresence initial={false}>
  {expanded && (
    <motion.div key="body"
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: DUR.panel, ease: EASE.inOut }}
      style={{ overflow: 'hidden' }}>
      …rows…
    </motion.div>
  )}
</AnimatePresence>
// chevron: <motion.svg animate={{ rotate: expanded ? 90 : 0 }} transition={{ duration: DUR.base, ease: EASE.out }} />
```
- **Row enter** — staggered fade/translate when a layer opens (`STAGGER` per index).
- **Progress fill** — switch `width` → `scaleX` (`AssetProgressBar.tsx:44`), `transformOrigin:left`, `ease: EASE.out`.
- **Pill state change** — cross-fade the pill label/color on state transition rather than hard swap.
- **Modal in/out** — wrap PlanModal/ClearConfirmModal in `AnimatePresence`; backdrop opacity 0→1, panel `{opacity, scale: 0.98→1}`, `EASE.out`, `DUR.modal`.
- **Number count-ups** — the row count and progress numbers should tween (e.g. Framer `useMotionValue` + `animate`) rather than snap, reinforcing the "live readout" feel — especially in the telemetry strip and the layer "N rows" figure.

---

## 5. Overall UI/UX elevation (modern techniques, beyond motion)

1. **Make the two panes one instrument (bidirectional bond).** `onNodeClick` already scrolls to a row (`DataAssetsView.tsx:106-118`). Add the reverse and the hover bond:
   - **Row hover → bead glow.** Lift `hoveredId` into `DataAssetsView` shared state; `AssetRow` `onMouseEnter` sets it, `LiveDependencyGraph` reads it (it already has internal `hoveredId` and closure-dimming, `:288-300`). Hovering a row dims the rest of the field and lights the matching bead + its up/downstream closure.
   - **Bead hover → row highlight.** Symmetric: the graph's `hoveredId` highlights the corresponding row (reuse the existing `highlighted` path, `AssetRow.tsx:155-157`).
   This single change is what turns "table + diagram" into "one instrument."

2. **Telemetry as an instrument readout.** Reframe the strip (`CockpitHeader.tsx:204-234`) as a row of small labeled gauges: WRITERS as a count that tweens, QUEUE as a depth bar, BUILD as a state lamp that *pulses* gold while running (not blue), SIDECAR as a steady/blinking dot. Add `aria-live="polite"`. Keep it monospace and tiny — instrument, not dashboard.

3. **Reduce card monotony with rhythm, not more cards.** Every section is a `--r-card` box on `--black-raised` (header, each layer panel). Vary *vertical rhythm* instead: tighter spacing inside a layer's rows, more air between layers; let the header card be the only fully-enclosed card and render layer panels as hairline-separated bands (sun-node divider) rather than six identical bordered boxes. This directly addresses the "cards are the lazy answer" critique while honoring 8-pt spacing.

4. **State transition vocabulary (dormant → building → lit).** Make the three states feel like a *journey*: dormant = outline bead / empty bar / muted row; building = hot-gold fill + flow + bead pulse; lit = settled solid gold + one-shot flare on arrival. The flare (§3.4) is the emotional payoff. Ensure the row, the bar, and the bead all transition *together* (shared state already flows through `DataAssetsView`).

5. **First-run / unbuilt-chart empty state.** When all assets are dormant, replace the quiet table with a centered classical invocation: a concentric-ring frame (sanctioned motif) around the ROOT sphere enlarged, with the line *"This instrument has not been built. We begin with Brahma Jñāna."* and a single primary Build action. This is the missing welcome moment (no current handling, §2.8).

6. **Scroll affordances on the 60% pane.** The left pane scrolls (`DataAssetsView.tsx:202`) with no indication of more content. Add a top/bottom fade mask (CSS `mask-image` linear gradient) that appears when scrollable, so the operator knows there are layers below the fold.

7. **Micro-interactions on icon buttons.** Lift-on-hover (translateY(-1px)) + a 1px gold-hairline ring on `:focus-visible` across Build/Refresh/Stop/Delete, unifying their feel and closing the focus-visible a11y gap.

---

## 6. Prioritized enhancement backlog

| Item | Impact | Effort | Brand-risk | Priority |
|---|---|---|---|---|
| Bidirectional row↔bead bond (hover lights both, §5.1) | H | M | Low | **P0** |
| Idle orbital drift + drive via `<g transform>` not setState (§3.1) | H | M | Low | **P0** |
| Depth sorting / painter's algorithm (§3.2) | H | S | Low | **P0** |
| Motion token file + panel expand/collapse animation (§4) | H | S | Low | **P0** |
| Remove 3px jewel side-stripe → gold hairline + sun-node (V1,V2) | M | S | Low (fixes a violation) | **P0** |
| Fix building-state blue → hot gold (V4) | M | S | Low (fixes a violation) | **P0** |
| ROOT presence: breathing glow + rotating specular (§3.3) | H | M | Low | **P1** |
| Build ignition timeline: ROOT pulse → edges in topo order → flare → ripple (§3.4) | H | L | Med (must stay restrained) | **P1** |
| Tab sliding underline + body cross-fade (§4) | M | S | Low | **P1** |
| Telemetry as instrument readout + `aria-live` (§5.2) | M | M | Low | **P1** |
| Row stagger-in on expand (§4) | M | S | Low | **P1** |
| Progress fill `width`→`scaleX` (V8) | L | S | Low | **P1** |
| First-run / unbuilt empty state (§5.5) | M | M | Low | **P1** |
| Modal AnimatePresence in/out + kill MiniDAG spring (V3, §2.7) | M | S | Low (fixes a violation) | **P1** |
| Replace ◆ glyph with sun-node SVG (V5); marsys-error on destructive (V7) | L | S | Low | **P2** |
| Layer header `<button>` + aria-expanded; node keyboard focus (§2.9, §3.7) | M | M | Low | **P2** |
| Number count-ups in telemetry + layer rows (§4) | L | S | Low | **P2** |
| Scroll fade masks on 60% pane (§5.6) | L | S | Low | **P2** |
| Icon-button lift + focus-visible ring (§5.7) | L | S | Low | **P2** |
| Em-dash → comma in AgentsView copy (V6); remove `console.log` (V9) | L | S | Low | **P2** |
| Responsive stacking below a breakpoint (§2.9) | M | M | Low | **P2** |

**Sequencing.** P0 is one coherent first slice: it fixes two brand violations, installs the motion vocabulary, makes the graph alive at idle and correctly depth-sorted, and bonds the two panes — the smallest set that moves the page from "dashboard" to "instrument." P1 is the cinematic layer (ROOT presence, ignition timeline, telemetry, empty state). P2 is hygiene, a11y completion, and responsiveness.

---

## 7. Recommended tech approach + next step

**What to install:** *Nothing for P0/P1's core.* The orbital engine and ROOT breathing use raw RAF + CSS (the existing `bead-breathe` precedent). All React-lifecycle motion uses the already-installed `framer-motion@^12.38`. **Only** consider `gsap` (lazy-loaded inside the existing `dynamic` import of `LiveDependencyGraph`, `DataAssetsView.tsx:21`) *if* the §3.4 ignition timeline proves unwieldy hand-rolled. Decide that after attempting the timeline in plain RAF.

**File-by-file change map (P0 slice):**
- **New** `src/lib/components/cockpit/v2/motion.ts` — `EASE`, `DUR`, `STAGGER` tokens.
- `LiveDependencyGraph.tsx` — per-layer `OMEGA` map; ring `<g>` refs + single RAF driving `transform` (replace `:147-185`); depth-sort + size/opacity by depth (`:464`); accept a `hoveredId`/`onHover` prop pair for the bond; `prefers-reduced-motion` + `document.hidden` guards; node `tabIndex/role/aria-label`.
- `DataAssetsView.tsx` — lift `hoveredId` to shared state; pass `onHover`/`hoveredId` to both `LayerPanel`→`AssetRow` and `LiveDependencyGraph` (`:199-237`).
- `AssetRow.tsx` — `onMouseEnter/Leave` → shared hover; consume shared `highlighted`.
- `LayerPanel.tsx` — `AnimatePresence` height/opacity on body (`:207`); rotating SVG chevron; **remove `borderLeft:3px`** (`:109`), replace with 1px gold hairline + sun-node; convert header `<div>`→`<button aria-expanded>`.
- `AssetProgressBar.tsx` — building `pillColor` → gold; `width`→`scaleX` fill.
- `marsys-theme.css` / token usage — ensure no raw `#60a5fa`; building state reads from gold ramp.

**Suggested first PR slice (P0, one reviewable unit):** "Nirmāṇa — instrument coherence pass": motion tokens + panel-expand animation + remove jewel side-stripe (→ gold hairline) + fix building-blue + bidirectional row↔bead hover bond + idle orbital drift (transform-driven) + depth sorting. This is self-contained, fixes V1/V2/V4/V8/V9, and delivers the single biggest perceptual jump. Reserve the ignition timeline (§3.4) and ROOT cinematics for a focused P1 follow-up PR where a GSAP decision can be made in isolation.

---

*End of report v1.0. Report only; no components modified.*
