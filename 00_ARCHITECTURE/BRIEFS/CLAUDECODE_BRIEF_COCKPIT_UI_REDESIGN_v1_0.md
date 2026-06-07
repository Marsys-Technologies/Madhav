---
canonical_id: CLAUDECODE_BRIEF_COCKPIT_UI_REDESIGN
version: 1.0
status: ACTIVE
authored: 2026-06-07
author: Cowork (planning)
executor: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: Cockpit (v2) UI redesign — Actions column, phase-header structure, constellation enhancement, build motion, scroll layout
branch: feature/cockpit-ui-redesign  (NEW branch OFF main; not committed onto main directly)
---

# CLAUDECODE_BRIEF — Cockpit UI redesign

> Execution surface: Claude Code in Antigravity IDE. Cowork authored + brainstormed this;
> it does not execute. Create a NEW branch off main: `git checkout main && git pull --ff-only
> && git checkout -b feature/cockpit-ui-redesign`. Localhost-first (code plane); data plane
> is prod via the proxy. Run `next dev --webpack`.

## §0 — Surface map (Cowork-read, grounded 2026-06-07)

The cockpit is the v2 component tree under
`platform/src/lib/components/cockpit/v2/`. Route: `/clients/[id]/build` → `CockpitShell`.
Relevant files for this brief:
- `DataAssetsView.tsx` — the 60/40 left/right split (layer panels left, graph right). The
  split + scroll behaviour (R5 below) lives here. Currently: `display:flex; gap:24px`,
  left `flex:0 0 60%`, right `flex:0 0 40%; position:sticky; top:24px`.
- `LayerPanel.tsx` — the phase (layer) accordion. Header shows Sanskrit/English name +
  asset count + row count + build button. Body grid columns `44% 30% 12% 14%`. (R2 below.)
- `AssetRow.tsx` — per-asset row. Grid `44% 30% 12% 14%` + `gap:8px` — the Actions overflow
  bug (R1 below) lives here AND in LayerPanel's matching column-header grid.
- `LiveDependencyGraph.tsx` — the SVG constellation. Spheres, glow filters, legend,
  H=W×1.25 aspect, Framer Motion already imported. (R3 + R4 below.)
- Design tokens: `platform/src/lib/styles/marsys-theme.css` (`--gold-high`, `--black`,
  `--black-raised`, `--black-line`, `--on-dark*`, `--r-card`, font stacks). Use these — no
  new hex. Constellation gold target: antique gold (see R3), NOT the dashboard `--brand-*`
  set (this surface uses the cockpit `marsys-theme.css` tokens).

## §R1 — Fix the Actions column overflow (assets rows)

**Bug (confirmed):** In both `AssetRow.tsx` (the row) and `LayerPanel.tsx` (the column-
header row), the grid is `gridTemplateColumns: '44% 30% 12% 14%'` (= 100%) PLUS
`gap: 8px` ×3. Percentages summing to 100% + gaps overflow the track, so the right-most
**Actions** cell is pushed past the container's right edge and gets clipped by the viewport.

**Fix:**
- Make the four tracks sum to LESS than 100% so the three gaps fit, OR (preferred) use
  `minmax(0, …fr)` fractional tracks so the gaps are absorbed and nothing overflows. E.g.
  `gridTemplateColumns: 'minmax(0,42%) minmax(0,28%) minmax(0,14%) minmax(0,16%)'` (tune
  to taste) — the Actions track widened to ~16% so both icons (RefreshCw + Clear) sit
  fully inside with the right-justify intact.
- Apply the SAME column template to the LayerPanel column-header grid and the AssetRow grid
  so headers and cells stay aligned (they must match exactly).
- Ensure no ancestor clips: the left pane in DataAssetsView is `flex:0 0 60%; minWidth:0` —
  keep `minWidth:0` (prevents grid blowout) and verify the Actions cell is fully visible at
  1280px and 1440px widths.
- Acceptance: at 1280×800 and 1440×900, both action icons in every asset row are fully
  visible, not clipped; header "Actions" label aligns over them.

## §R2 — Structure the phase-header asset-count + row-count

**Issue (confirmed):** In `LayerPanel.tsx` header (right cluster), `{assets.length} assets`
and `{totalRows} rows` are flex children with `gap:12px`, and the rows span only renders
`when totalRows > 0`. So the two numbers float to different horizontal positions per panel
depending on width and whether rows exist — "they show up anywhere."

**Fix:**
- Give the header-right cluster a FIXED mini-layout so the two data points always land in
  the same place across every phase. E.g. a small 2-column grid (or two fixed-width cells):
  a right-aligned "assets" cell and a right-aligned "rows" cell, each a fixed width (e.g.
  72px + 96px), with the build button + clear icon after them.
- ALWAYS render the rows cell — show `— rows` (em dash) when `totalRows === 0` instead of
  hiding it, so the column never collapses and the alignment holds.
- Keep the mono font + sizes; this is purely positional structure, not restyling.
- Acceptance: open several phases; "N assets" and "N rows" sit at identical x-positions in
  every phase header, aligned in their columns, regardless of value.

## §R3 — Constellation enhancement (LiveDependencyGraph) — "Refined SVG + richer depth"

Native picked: stay in SVG (no canvas/WebGL rewrite) but make it richer + high-quality.
Native feedback drivers: (a) remove the legend; (b) spheres should be a DARKER antique
gold; (c) the glow is "blinding" and washes out the spheres — make spheres legible.

**R3.1 — Remove the legend.** Delete the `LAYER_ORDER.map(...)` legend block
(`LiveDependencyGraph.tsx` ~lines 472–483, the `{l} · rx{NN}` text). It's a dev artifact
that only pushes the image down. Reclaim that vertical space.

**R3.2 — Darker antique-gold spheres.** Current bead gradient is near-white at center
(`#FFFBE8 → #EFE0BC → #A47A28`) — too bright. Change the node bead gradient to antique
gold, e.g. `#E8C878 (0%) → #C49A3E (40%) → #6B4E18 (100%)`; ROOT slightly brighter
(`#F4D98A → #D4A648 → #5C3F12`). The spheres should read as solid burnished-gold orbs, not
glowing white dots. Tune against `marsys-theme.css` gold tokens.

**R3.3 — Replace the blinding halo with a contained rim-light + atmosphere.** The current
`glowS/M/L/Root` filters are large `feGaussianBlur` (stdDeviation up to 9) applied to the
whole node group — that halo is what blinds. Instead:
- Reduce/▢remove the heavy Gaussian blur on the node fill itself.
- Add a SEPARATE soft "atmosphere" circle BEHIND each sphere (a radial-gradient disc,
  ~2–3× the sphere radius, low opacity ~0.12–0.18 gold→transparent) so there's a gentle
  presence without washing out the sphere's surface.
- Keep a small specular highlight dot (the existing inner white circle) but smaller/softer
  so the sphere reads 3D, not flared.
- Net: each sphere is crisply legible; glow is ambient, not blinding.

**R3.4 — Richer depth (native chose "+ richer depth").**
- Per-sphere radial shading already comes from the gradient — ensure the light direction is
  consistent (top-left highlight) across all spheres so they read as lit orbs.
- Keep + refine the background depth polygons (triplets of lit nodes) at low opacity for a
  sense of a connected field.
- Keep the orbital ellipses but make them fainter/cleaner (thin 0.6px, low-opacity gold).
- Add a subtle page-level radial vignette behind the SVG (darker at edges) for depth — via
  the container background, not a heavy SVG filter.
- Parallax dust: keep the existing particle motion but ensure it's subtle (low opacity);
  it's ambiance, not noise.

**R3.5 — High resolution / crispness.** Ensure the SVG `viewBox` matches the rendered px
1:1 (it's responsive via ResizeObserver — keep that) and strokes are thin (0.5–0.6px) for a
refined look. No raster; SVG stays vector-crisp at any DPI.

## §R4 — Build-time motion (Framer Motion) — "Both combined"

Native picked: gentle always-on whole-constellation drift, PLUS stronger pulse + flowing
edges on the spheres that are ACTIVELY BUILDING. The point is to convey "dynamic
astrological factors are being tracked, data engineering + AI interpreting them" — but only
meaningfully animate during a build.

- **Idle (no active run):** the constellation is calm. A very gentle, slow drift is
  acceptable (subtle), but nothing attention-grabbing. Spheres steady.
- **Active build (activeRun != null, or per-asset `state === 'building'`):**
  - Whole-constellation gentle rotation: the spheres travel slowly along their orbit rings
    (rotate the orbital system slowly), to read as "tracking dynamic factors." Keep slow
    (e.g. a full revolution over 60–120s) so it's hypnotic, not dizzying.
  - The currently-building sphere(s) get a stronger pulse (scale/opacity breathe) and their
    connecting edges animate a flowing "data transfer" shimmer (e.g. animated dash offset or
    a travelling gradient along the edge) from dependency → dependent, signalling data +
    AI flow.
  - When the build completes / goes idle, rotation eases to a stop and edges settle.
- Use Framer Motion (already imported). Gate ALL build-motion on actual build state — read
  `activeRun` (passed to LiveDependencyGraph) and per-asset `state==='building'`.
- **Respect `prefers-reduced-motion`** — pin animations when the user prefers reduced motion
  (the global CSS guard exists; ensure Framer Motion respects it too).
- Acceptance: with no active run the graph is calm; trigger a build (or simulate building
  state) and the constellation rotates slowly + the building spheres pulse + their edges
  flow; on completion it settles. Cowork will verify live in Chrome during a real build.

## §R5 — Layout: independent scroll panes (left content scrolls, right graph fixed)

Native picked "decide after seeing it" → implement independent panes, Cowork verifies in
Chrome and we adjust if it feels off at the native's screen size.

**Current:** `DataAssetsView` is one flex row; the right graph is `position:sticky; top:24px`
so it scrolls partway with the page, and the whole image is tall (H=W×1.25) which forces
page scroll.

**Target:**
- Make the cockpit content area a fixed-height region (e.g. `height: calc(100vh - <header+tabbar>)`)
  with TWO independently-scrolling/fixed panes:
  - Left pane (≈60%, the layer panels): `overflow-y: auto` — scrolls on its own.
  - Right pane (≈40%, the graph): fixed in place, does NOT scroll with the left; the graph
    sizes to fit the pane height (cap its height to the pane, don't let H=W×1.25 force it
    taller than the viewport — clamp H to the available pane height, recompute the layout to
    fit).
- The graph should feel anchored on the right while you scroll phases/assets on the left.
- Keep `minWidth:0` on both panes (prevents overflow). Ensure no horizontal scroll appears.
- Acceptance: scrolling the phase list on the left does NOT move the graph; the graph stays
  fully visible (not clipped, no internal scroll) at 1280×800 and 1440×900. Cowork verifies
  and we tune the height math if the graph is too tall/short on the native's display.

## §6 — Constraints
- Cockpit tokens: use `marsys-theme.css` vars; no literal hex beyond the constellation
  gradients (which are intentional art — keep them as named constants near the top of
  LiveDependencyGraph). No `--obsidian-*` legacy.
- No tier gating anywhere (standing directive).
- Do NOT hardcode Anthropic/Claude.
- `next dev --webpack`; `tsc --noEmit` clean on touched files + run the cockpit vitest
  (LayerPanel / AssetRow / any LiveDependencyGraph tests) before commit.
- Framer Motion only; no new animation libs.

## §7 — Acceptance summary
- AC1 Actions icons fully visible in every asset row (1280 + 1440); headers aligned.
- AC2 Phase-header "N assets" / "N rows" land at identical positions across all phases;
  rows shows "— rows" when zero.
- AC3 Graph legend removed.
- AC4 Spheres are darker antique gold + legible; glow is contained (not blinding); depth
  reads (shading, polygons, vignette, faint orbits).
- AC5 Build-time: idle = calm; active build = slow constellation rotation + building-sphere
  pulse + flowing edges; settles on completion; respects reduced-motion.
- AC6 Independent scroll panes: left scrolls, right graph fixed + fully visible, no
  horizontal scroll.
- AC7 tsc clean + cockpit vitest green on touched files.
- Cowork re-verifies AC1–AC6 in Chrome on localhost (including triggering a real build for
  AC5), then we tune R5 height math if needed.

## §8 — Git
```
git checkout main && git pull --ff-only
git checkout -b feature/cockpit-ui-redesign
# implement R1–R5
git add -A
git commit -m "cockpit UI: fix Actions overflow, structure phase-header counts, remove graph legend, antique-gold constellation w/ contained glow + depth, build-time motion, independent scroll panes"
git push origin feature/cockpit-ui-redesign
```
Do NOT merge to main yet — Cowork verifies in Chrome first, then native gates the merge.
