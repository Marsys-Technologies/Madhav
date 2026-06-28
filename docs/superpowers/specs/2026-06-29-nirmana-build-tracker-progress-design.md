---
title: Nirmāṇa Build Tracker — Progress Visualization Enhancements
date: 2026-06-29
status: APPROVED
author: Abhisek (native) + Claude
register: product
surface: platform/src/lib/components/cockpit/v2
related_mockup: .superpowers/brainstorm/87894-1782687151/nirmana-enhanced-v2.html
---

# Nirmāṇa Build Tracker — Progress Visualization Enhancements

## 1. Problem

The Nirmāṇa build tracker (`/clients/[id]/nirmana`) presents operator-grade build internals that
are noise to a non-operator viewer, and its existing progress signals are weak:

1. The chart-identity header carries a `WRITERS · QUEUE · BUILD · SIDECAR` telemetry strip — raw
   instrument internals that say nothing about *what is being built* or *how far along it is*.
2. The global progress bar is a single flat "X / Y assets complete" line. It always reads as if a
   full six-layer build is running, even when the active run is scoped to one layer or one asset +
   its downstream chain. It misrepresents partial builds.
3. The per-layer row counts (`16 assets | 585,660 rows`) are visually disorganized — figures drift,
   labels are implicit, and nothing aligns across layers.
4. The per-asset progress bars under an expanded layer are thin and low-information: a stage label
   and a state pill, but no sense of magnitude, build phase, or write frontier.

This is a **product-register** redesign of the build-status surface. It does **not** change the
orchestrator, the build APIs, the DAG, or any data contract. It is a presentation-layer enhancement
of existing components, using data already available to the cockpit (active run, plan, per-asset
stats, substep overlay).

## 2. Goals / Non-goals

**Goals**
- Replace the telemetry strip + flat global bar with a single **scope-aware build console**.
- Rethink the per-layer metric block into an **aligned two-gauge instrument**.
- **Significantly enhance** the per-asset progress bar (rows written, substep ticks, leading-edge
  write cap, richer service treatment).
- Preserve every existing affordance: all global, per-layer, and per-asset action buttons
  (Build/Rebuild · Refresh · Clear/Stop), role gating, the bilingual layer naming, the armillary
  graph, and the expand/collapse behavior.

**Non-goals**
- No change to the orchestrator (FROZEN), build APIs, asset registry, or DAG.
- No new "guest-only" route or permission tier. This is the same page for all viewers; only the
  presentation changes. (The earlier guest-view framing is dropped per native direction.)
- No removal of operator controls.
- No change to layer naming arrangement (Sanskrit stays on top, English subtitle below).

## 3. Theme contract (non-negotiable)

All work uses the existing live theme verbatim. No new colors, fonts, or radii outside these tokens
from `platform/src/lib/styles/marsys-theme.css`:

- Surfaces: `--black #0A0806`, `--black-raised #14110B`, `--black-line #241D10`
- Text: `--on-dark #F3EEE2`, `--on-dark-mut #B9AE93`, `--on-dark-faint #7C725B`
- Gold ramp: `--gold-high #ECC56A`, `--gold-bright #D2A23C`, `--gold-core #A87C2A`,
  `--gold-deep #8A5E12`, `--gold-engrave #6E4E0F`
- Error: `--marsys-error #B5474C`
- Fonts: `--display-stack` (Cormorant Garamond / serif) for Sanskrit + chart name;
  `--ui-stack` (system sans) for English + body; `--mono-stack` (SF Mono) for all numerics/labels
- Radii: `--r-btn 6px`, `--r-card 12px`
- Per-layer sun-node gold tints (unchanged from `LayerPanel.LAYER_GOLD`):
  brahmagyan `#ECC56A`, ganita `#D2A23C`, bodha `#A87C2A`, kala `#8A5E12`, phala `#B98A2E`,
  mimamsa `#6E4E0F`
- Motion: ease-out exponential; respect `prefers-reduced-motion` (existing `AssetProgressBar`
  pattern). Shimmer/slide via transform, never animated layout properties.

The approved reference rendering is `nirmana-enhanced-v2.html` in the brainstorm session dir.

## 4. Component-level design

### 4.1 Build Console — replaces telemetry strip + global bar

**Location:** `CockpitHeader.tsx`. Remove the `WRITERS · QUEUE · BUILD · SIDECAR` telemetry strip
(lines ~274–321) and the existing flat global progress bar (lines ~323–354). Replace both with a
single console block that sits in the same slot, below the chart identity row.

**Idle state** (no active run): a muted readout of overall instrument completeness —
`Idle · N of 6 layers live · last built <relative>` with right-aligned `TOTAL <rows>` and
`COMPLETE <pct>`. The segmented bar shows layer-level completion (one segment per layer, filled if
that layer is fully lit).

**Building state** (active run): a pulsing `--gold-high` dot + `Building` + a **scope chip** naming
what the run covers, plus right-aligned `ELAPSED <mm:ss>` and `ASSETS <done> / <plan total>`.

**Scope-aware plan bar (core idea).** The progress visualization is driven by the **active run's
`plan`** (the ordered asset list already returned by `/api/cockpit/runs/active`), not by a fixed
six-layer assumption. Render one thin segment per asset in the plan, grouped into per-layer clusters
with a small gold-ramp label above each cluster. Segment states: `done` (filled gold), `active`
(shimmer sweep on the current asset), `pending` (empty track). Consequences:
- Full-chart build → all in-scope layer clusters appear.
- Single-layer build → only that layer's cluster appears.
- Asset + downstream build → only the assets in that dependency chain appear, across whatever
  layers they touch.

**Scope chip copy** derives from `activeRun.scope` / `scope_target`:
- `global` → "Full chart · N layers"
- `layer` → "<Sanskrit name> layer only"
- `asset` → "<asset_id> + K downstream" (K = plan length − 1)

**Data sources (all existing):** `activeRun.plan`, `activeRun.scope`, `activeRun.scope_target`,
`activeRun.current_asset_id`, `activeRun.started_at` (elapsed), per-asset `state` from the stats map
(done vs pending), the asset registry (to map asset_id → layer for clustering). Sidecar health and
the writers/queue/build telemetry move out of the header surface (sidecar health can be relocated to
an unobtrusive status indicator or dropped from this surface — see §6 open item).

### 4.2 Layer gauge — rethought per-layer metrics

**Location:** `LayerPanel.tsx` header right zone (lines ~187–224, the `{N} assets | {rows} rows`
metric group).

Replace the inline metric run with a fixed-width (~170px) **two-column gauge**:
- Left column: `<done> / <total>` (done in `--gold-high` bold, denominator faint) under a
  `--mono-stack` micro-label `ASSETS BUILT`.
- Right column (right-aligned, tabular-nums): total rows for the layer under micro-label `ROWS`.
- A 3px completion bar spans the gauge width beneath both columns; fill = assets-built ÷ total.
  Active layer's fill carries the shimmer sweep.

Because the gauge is fixed-width with right-aligned numerics, the figures line up vertically across
every layer row — fixing the disorganization. `done` count = assets in the layer whose state is
`lit`/`service_ok`. Pending layers show `0 / N` and `—` rows with an empty bar.

A per-layer **state pill** (`Live` / `Building` / `Pending`) sits between the gauge and the action
cluster, so a collapsed layer's status reads without expanding.

### 4.3 Asset progress bar — significantly enhanced

**Location:** `AssetProgressBar.tsx` (data assets) and the `ServiceHealthPill` in `AssetRow.tsx`
(service assets). Bar height grows 22px → 28px; radius 4px.

**Data asset bar:**
- **Fill = stage/substep progress** (rows-only decision per native: the target floor is NOT shown
  and NOT used as the fill denominator, honoring rule N.4 "floors aspirational, not gates"). Reuse
  the existing `stageFill(stage, substep)` monotonic-floor logic for the building fill width. Live =
  100%, error = 100% red, queued/dormant = empty.
- **Rows-written numeric** always visible, left-aligned, `--mono-stack`, tabular-nums
  (`536,471`). No target/denominator. Queued rows may show a faint "queued" hint; no target estimate.
- **Substep tick marks**: faint vertical dividers (`rgba(255,255,255,0.07)`) splitting the track into
  the asset's substep count, shown while building.
- **Leading-edge cap**: a 2px `--gold-high` bar with glow at the fill frontier while building,
  marking the live write position. Suppressed under `prefers-reduced-motion`.
- **Inline `step i/total`** indicator while building; **state pill** (`LIVE` / `BUILDING` /
  `QUEUED` / `FAILED` / `OUT OF SYNC` / etc.) at the right edge — reuse existing `STATE_COLORS` pills.
- Shimmer sweep during `running` / `substeps` stages (existing behavior, retained).

**Service asset treatment** (enhanced): replace the flat gold health fill with a pulsing green
heartbeat dot + `Service responding` label + right-edge state pill (`LIVE` / `PROBING` / `FAILED` /
`DORMANT`). Same 28px geometry so service and data rows align. Colors stay on the gold/green/red
state palette already in use.

### 4.4 Preserved, unchanged
- Expanded asset table columns (Asset / Progress / Last built / Actions) and the
  services-sorted-first ordering.
- All action buttons + role gating (brahmagyan super-admin gate), Stop-only-on-building-asset logic,
  Clear-when-idle logic.
- Bilingual naming: layer rows = Sanskrit (serif, on top) + English (below); asset rows = Sanskrit
  (serif) + asset_id below. Status dot + Database/Cpu type glyph.
- Armillary graph (right pane), expand/collapse animation, highlight-on-hover linkage.

## 5. Components touched

| File | Change |
|---|---|
| `cockpit/v2/CockpitHeader.tsx` | Remove telemetry strip + flat global bar; add Build Console (idle + building states) with scope chip and scope-aware plan bar. |
| `cockpit/v2/LayerPanel.tsx` | Replace metric run with two-column gauge + completion bar; add per-layer state pill. |
| `cockpit/v2/AssetProgressBar.tsx` | 28px bar; always-on rows numeric; substep ticks; leading-edge cap; inline step indicator. Fill stays stage/substep-based (no target). |
| `cockpit/v2/AssetRow.tsx` | Enhance `ServiceHealthPill` → heartbeat treatment; pass substep count for ticks; 28px alignment. |
| New: `cockpit/v2/BuildConsole.tsx` (optional extraction) | The console + plan bar, if `CockpitHeader` grows too large. Keeps the header focused. |
| New: `cockpit/v2/PlanBar.tsx` (optional extraction) | The scope-aware segmented plan bar, isolated + unit-testable. |

Extraction is preferred where a file would otherwise exceed its current responsibility (the console
and plan-bar logic warrant their own focused units).

## 6. Open items for implementation planning
- **Sidecar health relocation.** The console drops `SIDECAR` from the header readout. Decide whether
  to surface sidecar health elsewhere (small corner indicator) or rely on the existing
  `useCockpitStatus` surface. Default: keep a minimal sidecar dot in the header actions row.
- **Plan→layer clustering source.** Confirm the asset→layer map for clustering comes from the
  registry already loaded in the cockpit (no new fetch).
- **Elapsed timer.** `started_at` → live `mm:ss` needs a 1s interval tick; gate it on an active run
  and clear on unmount.
- **Reduced-motion.** Shimmer, heartbeat, leading cap, and the plan-bar active sweep must all
  respect `prefers-reduced-motion`.

## 7. Acceptance criteria
1. With no active run, the console shows the idle completeness readout and per-layer segmented
   completion; no `WRITERS/QUEUE/BUILD/SIDECAR` strip remains.
2. During a **global** run, the plan bar shows all in-scope layer clusters; the scope chip reads
   "Full chart".
3. During a **layer** run, the plan bar shows only that layer's cluster; chip names the layer.
4. During an **asset+downstream** run, the plan bar shows only the planned assets; chip reads
   "<asset> + K downstream".
5. Each layer row shows the aligned two-gauge block; numerics align vertically across all layers.
6. Each data-asset bar shows rows-written (no target), substep ticks while building, a leading-edge
   cap while building, an inline step indicator, and a right-edge state pill; fill is stage-based.
7. Service-asset rows show the heartbeat treatment, aligned to 28px.
8. All pre-existing action buttons, role gates, and Stop/Clear logic behave exactly as before.
9. Theme tokens, fonts, and per-layer gold tints are unchanged; `prefers-reduced-motion` is honored.
10. No orchestrator/API/DAG/data-contract change; build behavior is identical.
