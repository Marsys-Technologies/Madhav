---
brief_id: STREAM_C_VISUAL_V2_v1_0
status: ACTIVE
arc_id: build_e2e_arc
stream: C
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavVisualV2
branch: feat/visual-v2
base: feature/ux-workflow-overhaul
sessions: 9
estimated_loc: ~1100 across 12 files
visual_contract: 00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/VISUAL_CONTRACT_v2.md
---

# Stream C — Visual v2 implementation (≥ approved mockup)

Ships the obsidian + gold + Sanskrit-named visual design across all three
pages: entry form, cockpit, consume. Matches the v2 mockup the native
approved 2026-05-31. Elevates further on typography, animation, and
microcopy.

## Cross-cuts read first

- `00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/STREAM_COORDINATION_v1_0.md`
- `00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/VISUAL_CONTRACT_v2.md` ← **the spec**

## Hard gates

- NO Anthropic models.
- NO touching state, validation, or submit handlers in `NewClientForm.tsx` — those are Stream D's surface. C edits ONLY styling, layout, rendering of that file. If a session needs to touch state, halt and tag for coordination.
- NO mock data inside graph/progress components. They must accept real props/hooks. Storybook-style mock data lives in test files only.
- NO new color hex values outside `lib/styles/theme_tokens.ts`. Reuse the tokens.
- All Sanskrit names sourced from `lib/jyotish/asset_names.ts` (created in C-S1) — never inlined.

## §C-S1 — Sanskrit name map

Create `platform/src/lib/jyotish/asset_names.ts` per VISUAL_CONTRACT §"Sanskrit
asset name map". Export `ASSET_NAMES` const + `LAYER_NAMES` const + type
helpers. Tests in `__tests__/asset_names.test.ts`: all 28 assets have
sanskrit + english + subtitle; LAYER_NAMES covers L1/L2_5/L3/L4.

Gate: `cd platform && npm test -- asset_names.test.ts` → green.

## §C-S2 — Theme tokens

Create `platform/src/styles/theme_tokens.css` with the `:root` declarations
from VISUAL_CONTRACT §"Theme tokens". Import via `globals.css` or layout.
Verify Cormorant Garamond + Inter + JetBrains Mono are loaded from Google
Fonts (add `<link>` in root layout if missing).

Gate: `cd platform && npm run build` → green; visual check that tokens
resolve.

## §C-S3 — Force-graph DAG SVG component

Create `platform/src/components/cockpit/LiveDependencyGraph.tsx`. Props:

```typescript
interface Props {
  nodes: Array<{ asset_id: string; layer: 'L1'|'L2_5'|'L3'|'L4'; status: 'complete'|'running'|'pending'|'failed'|'skipped'; row_count?: number; progress?: number /* 0-1 */; }>
  edges: Array<{ from: string; to: string; live?: boolean; }>
  width?: number;
  height?: number;
}
```

Render per VISUAL_CONTRACT §"Page 2 §3 Yantra Chitra force-graph panel":
- 4-column layout (Adhara/Sambandha/Sutra/Vyavahara), positioned by layer
- Curved bezier edges with `marker-end` arrows
- Lit edges in `--gold-primary` (`#d4a648`) with their own marker
- Node visual per status (see ProgressRing below for running nodes)
- Sanskrit name labels next to each node from ASSET_NAMES
- Column headers + L1/L2.5/L3/L4 micro-labels at top
- Dashed gutter dividers between columns

Hook into `useSseSubscription(buildId)` — a NEW lightweight hook in
`platform/src/hooks/useSseSubscription.ts` that subscribes to
`/api/build/events/${buildId}` and returns `{ nodes, edges }` updated as
`node_added` / `edge_added` events arrive (this is exactly what Stream B's
R1 emits).

Tests in `__tests__/LiveBuildGraph.test.tsx`:
- renders all node states correctly
- live edge rendered with lit class
- column layout positions match
- handles empty state

Gate: `cd platform && npm test -- LiveBuildGraph.test.tsx` → green.

## §C-S4 — Progress ring SVG component

Create `platform/src/components/cockpit/ProgressRing.tsx`. Props:
`{ progress: number /* 0-1 */, radius?: number, strokeWidth?: number }`.

Render an SVG arc using `stroke-dasharray` + `stroke-dashoffset` to draw
the percentage filled. CSS transition on `stroke-dashoffset` for smooth
animation (500ms ease-out). Show the percentage text centered inside the
ring in 7px Inter mono-feel.

Used by LiveDependencyGraph for running nodes. Standalone reusable.

Tests: renders 0%, 50%, 100% correctly; updates smoothly on prop change
(verify CSS transition class present).

Gate: `cd platform && npm test -- ProgressRing.test.tsx` → green.

## §C-S5 — Sampurna gati overall progress bar

Create `platform/src/components/cockpit/OverallProgress.tsx`. Props:

```typescript
{
  totalNodes: number;        // 140
  completeNodes: number;     // 47
  etaSeconds?: number;       // 702
  perAyanamsha: Array<{ id: string; complete: number; total: number; }>;
}
```

Renders per VISUAL_CONTRACT §"Page 2 §2 Sampurna gati":
- Italic Cormorant "Sampurna gati · Overall progress" left
- Monospace "47 / 140 nodes · 33.6% · ETA 11m 42s" right
- 6px tall track + gold fill width=percent
- Below: 5 per-ayanamsha sub-counts in 9px monospace

Hook: `useBuildProgress(chartId)` — polls `/api/build/active?chart_id=X`
every 5s and computes aggregates from build_steps.

Tests: renders correctly; updates on prop change.

Gate: `cd platform && npm test -- OverallProgress.test.tsx` → green.

## §C-S6 — Telemetry strip

Create `platform/src/components/cockpit/TelemetryStrip.tsx`. Props:
`{ qps: number; activeWriters: number; queueDepth: number; sidecarHealthy: boolean; buildId: string; }`.

Renders the bottom row of the force-graph panel per VISUAL_CONTRACT:
monospace labels in `--text-secondary`, values in `--gold-primary` or
`--success`.

Hook: `useTelemetry(buildId)` — polls a NEW `/api/build/telemetry` (10 LOC)
that reads from build_events aggregations.

Tests: renders metrics; healthy/unhealthy state classes.

Gate: `cd platform && npm test -- TelemetryStrip.test.tsx` → green.

## §C-S7 — Asset table v2

Refactor / create `platform/src/components/cockpit/AssetTable.tsx` per
VISUAL_CONTRACT §"Page 2 §4 Per-layer asset tables":
- 5-column grid (row_num | name+subtitle | progress | row count | status)
- Section headings per layer (Sanskrit + English + L-tag + count)
- Rows pull from `ASSET_NAMES` for naming
- Per-row Rebuild action (icon button — wires to a `onRebuild(asset_id)` prop)
- Cascade hint footer

Tests: renders 28 rows in layer order; click Rebuild calls handler.

Gate: `cd platform && npm test -- AssetTable.test.tsx` → green.

## §C-S8 — Form visual polish

In `platform/src/components/clients/NewClientForm.tsx`, edit ONLY:
- Layout (grid columns matching VISUAL_CONTRACT §"Page 1")
- Typography (Sanskrit section headers, micro-label uppercase)
- Field styling (obsidian inputs, gold focus border)
- Glyph + wordmark header
- Footer microcopy with the "5 × 28 = 140 nodes" line

DO NOT TOUCH:
- Form state (`useState`, validation logic, submit handler) — D's territory
- The `fetch('/api/clients/create', ...)` call — D's territory
- Field names or schema

Tests in `__tests__/NewClientForm.test.tsx` (visual rendering only):
section headings present, Sanskrit names rendered, 3-column identity grid.

Gate: `cd platform && npm test -- NewClientForm.test.tsx` → green.

## §C-S8.5 — Wire BuildButton.tsx into cockpit page (coordination from Stream A)

`platform/src/components/cockpit/BuildButton.tsx` exists (57 LOC, shipped
in commit 5ef88415 with L4 polling + state-aware Build/Cancel/Resume).
It is NOT YET imported into `platform/src/app/clients/[id]/build/page.tsx`.

This session wires it in. The page IS within Stream C's may_touch since
C owns the cockpit visual surface. Replace any existing inline Build CTA
with `<BuildButton chartId={params.id} />`.

Tests: ensure the build page renders BuildButton when a chart_id is present.

Gate: `cd platform && npm test -- build/page.test.tsx` → green.

## §C-S9 — Final commit + cherry-pick to main

Per STREAM_COORDINATION §5. If the cherry-pick to main collides with D's
parallel changes on `NewClientForm.tsx`, the conflict-resolution policy
applies: clean rebase, then `-X theirs` for visual-only lines, escalate
to halt if structural conflict.

Gate: `git log origin/main..HEAD --oneline | head -1` returns 0.

---

End of Stream C brief.
