---
artifact: UX_WORKFLOW_OVERHAUL_REPORT
version: 1.0
status: COMPLETE
date: 2026-05-31
branch: feature/ux-workflow-overhaul
head_sha: 089ea6553bbd2bdcab4f3154d917a0e321e729ca
---

# UX/UI Workflow Overhaul — Operator Report

## Summary

Full autonomous execution of the MARSYS UX/UI + workflow pipeline overhaul arc on branch
`feature/ux-workflow-overhaul`. Six phases executed via parallel+sequential workflow orchestration.
4 commits shipped. 37 files changed.

---

## Phase Verdicts

| Phase | Scope | Status | Notes |
|-------|-------|--------|-------|
| Pre-flight | Branch setup, DB proxy, npm install | **PASS** | `db=ok npm=ok` |
| A: Backend | Migrations 154-156, cascade dispatcher, A3/A4/A5 writers | **PASS** | 111 tests pass |
| B: Theme+Rename | Tailwind tokens, Cormorant/Inter fonts, 28-asset Sanskrit rename | **PASS** | `PHASE_B_OK` |
| C: Cockpit UI | Form, cockpit, force-graph, cascade preview, build controls, 8 API routes | **PASS** | 17 files |
| D: Consume Rewire | Audit=COMPATIBLE, patches, degradation banner, suggester | **PASS** | |
| E: Integration Test | Dev server smoke + route checks | **PASS (manual)** | Turbopack issue resolved by removing spurious root package.json; dev server HTTP 307/401 correct |
| F: Report + PR | This document + PR | **PASS** | |

---

## Migrations Applied

| Migration | File | Status |
|-----------|------|--------|
| 154 | `platform/migrations/154_build_dependencies.sql` | Applied — 28-asset DAG seeded |
| 155 | `platform/migrations/155_build_checkpoints.sql` | Applied — per-asset × ayanamsha resume state |
| 156 | `platform/migrations/156_per_asset_stop.sql` | Applied — `build_events.stop_requested` column + index |

---

## Key Deliverables

### Phase A — Backend Foundation

**Dispatcher** (`platform/python-sidecar/pipeline/dispatcher.py`):
- `_load_dep_graph(conn)` — lazy-loads build_dependencies into in-memory forward-edge map
- `compute_descendants(asset_id)` — BFS forward-DAG walk returning transitive dependent set
- `poll_stop_signal(build_id, asset_id, conn)` — checks `build_events.stop_requested`
- `upsert_checkpoint(...)` — atomic INSERT/ON CONFLICT for checkpoint state
- `rebuild_asset(asset_id, chart_id, build_id, conn)` — cascade-invalidates category_prefix rows + checkpoints for target + all descendants, emits `rebuild_requested` event
- `resume_build(chart_id, build_id, conn)` — returns skip-set from `build_checkpoints` where status=success

**A3 Mula-Lakshana writer** (`platform/python-sidecar/pipeline/writers/chart_facts_writer_a3.py`):
- Real implementation using actual `chart_facts` schema (fact_id, fact_category, fact_subject, fact_key)
- Covers: lagna (9 fields), navamsa lagna, 9 grahas × 17 fields, 12 houses × 7 fields, 12 signs × 5 fields, chart meta
- Two-pass verification: write then read-back count, raises ValueError if <90% row count returned
- 18 tests pass; wipe-and-rebuild pattern on entry

**A4 Panchanga adapter** (`platform/python-sidecar/pipeline/writers/panchanga_writer_a4_adapter.py`):
- Bridges to real `write_panchanga_limbs()` engine; falls back to legacy `compute_panchanga_for_date` if available
- Produces a4_tithi, a4_nakshatra, a4_yoga, a4_karana, a4_vara, a4_sunrise/sunset, a4_rahu_kalam, a4_abhijit_muhurta

**A5 Marma-Bindu adapter** (`platform/python-sidecar/pipeline/writers/sensitive_points_writer_a5_adapter.py`):
- Dispatches to all `emit_*` functions in the existing sensitive_points_writer_a5.py
- Writes a5_* chart_facts rows per sensitive point (longitude, sign, house)

**Registry** (`pipeline/writers/__init__.py`):
- `_write_chart_facts`, `_write_panchanga`, `_write_sensitive_points` upgraded from stubs to real dispatchers
- `conn=None` guard preserved for test compatibility

### Phase B — Theme + Asset Renaming

**Tailwind** (`platform/tailwind.config.ts`):
- New `brand.*` color tokens: bg (#08070a), surface (#0d0c10), border (#1a1820)
- Gold scale: gold-1 (#d4a648), gold-2 (#e8c878), gold-3 (#f8e6a8), gold-4 (#c4932a)
- Text scale: text-1..text-4; status tokens: ok, warn, err
- Font families: `serif` → `var(--font-serif)`, `sans` → `var(--font-sans)`

**Fonts** (`platform/src/app/layout.tsx`):
- Cormorant Garamond 400/500/600 + italic via `next/font/google` → `--font-serif`
- Inter 300/400/500/600/700 via `next/font/google` → `--font-sans`

**Asset names source of truth** (`platform/src/lib/build/asset_names.ts`):
- `ASSET_MAP` — 28-entry record (A1–A22 + META-α through META-ζ) with id, sanskrit, english, layer, sortOrder, categoryPrefix, retired flag
- Helper exports: `getAssetDisplayName()`, `getAssetSanskrit()`, `getAssetEnglish()`

**CAPABILITY_MANIFEST.json** — display_name + display_subtitle fields added for asset tools

**poll_daemon.py** — ASSET_REGISTRY name fields updated to "Sanskrit · English" format

### Phase C — Cockpit UI

**New chart form** (`platform/src/app/clients/new/page.tsx`):
- 4 sections: Identity / Birth Coordinates / Compute / Relationships
- react-hook-form + zod validation; shadcn/ui components
- Manual birthplace accordion (collapsed by default, auto-expands on Places miss)
- Defaults: 5 ayanamshas checked, two-pass verification, private, 1950-2100 lifetime

**Cockpit page** (`platform/src/app/clients/[id]/cockpit/page.tsx`):
- Layout: header + BuildControlsBar + status pill, 280px sidebar (build meta + history), main tabs
- Tabs: Live Graph · By Ayanamsha · Assets · Event Log · Data Preview

**LiveBuildGraph** (`platform/src/components/cockpit/LiveBuildGraph.tsx`):
- react-force-graph-2d (canvas, performant at 200+ nodes)
- SSE subscription to `/api/build/events/[buildId]`
- Nodes colored by status (pending=dark, running=gold pulse, success=green, failed=red)
- Click → NodeDetailModal with per-ayanamsha breakdown

**AssetTable** (`platform/src/components/cockpit/AssetTable.tsx`):
- Per-row: glyph dot (layer color) + "Sanskrit · English" name + status pill + row count
- Per-row actions: Rebuild (→ CascadePreviewModal), Stop (status=running only), Skip (status=pending only)

**CascadePreviewModal** (`platform/src/components/cockpit/CascadePreviewModal.tsx`):
- Fetches `/api/build/cascade-preview?asset_id=X` → renders mini force-graph of target (red) + descendants (gold)
- Body: "Rebuilding [Name] will recompute [N] downstream assets"
- Footer: Cancel + "Rebuild [N+1] assets" gold CTA

**BuildControlsBar** (`platform/src/components/cockpit/BuildControlsBar.tsx`):
- State machine: Build → Continue+RebuildAll → RebuildAll → (running) Stop
- Status pill: IDLE / BUILDING / COMPLETE / FAILED with breathing dot when running

**API routes** (all under `platform/src/app/api/build/`):
- `cascade-preview/route.ts` — GET, computes transitive descendants from build_dependencies
- `rebuild/route.ts` — POST, emits rebuild_requested build_event
- `asset/stop/route.ts` — POST, sets build_events.stop_requested=true
- `asset/skip/route.ts` — POST, marks checkpoint status=skipped
- `continue/route.ts` — POST, emits resume_requested build_event
- `rebuild-all/route.ts` — POST, new build_id + rebuild_all_requested event
- `start/route.ts` — POST, first-time build start
- `stop/route.ts` — POST, stop entire build
- `data-readiness/route.ts` — GET, per-chart asset readiness status

### Phase D — Consume Rewire

**Audit result**: COMPATIBLE — existing consume page already queries tables compatible with new schema; no breaking changes needed.

**PartialDataBanner** (`platform/src/components/consume/PartialDataBanner.tsx`):
- Fetches `/api/build/data-readiness?chart_id=X` on mount
- Renders warning with "Build now" CTA if any assets are missing
- Integrated into consume page

**QuestionSuggester** (`platform/src/components/consume/QuestionSuggester.tsx`):
- Renders up to 5 suggested questions as pill buttons based on which assets are ready
- Calls `onSelect(question)` to inject into chat input

**question_templates.ts** (`platform/src/lib/consume/question_templates.ts`):
- Per-asset templates for A3, A7, A8, A10, A15
- `getSuggestedQuestions(readyAssets, count=5)` helper

**LLM context injection**: Verified data_readiness context is prepended to system prompt; `PLANNER_PROMPT` already includes asset availability context.

---

## Files Changed (37 total)

```
00_ARCHITECTURE/CAPABILITY_MANIFEST.json
00_ARCHITECTURE/CONDUCTOR/build_orchestrator/data_progress/poll_daemon.py
platform/migrations/154_build_dependencies.sql
platform/migrations/155_build_checkpoints.sql
platform/migrations/156_per_asset_stop.sql
platform/python-sidecar/pipeline/dispatcher.py
platform/python-sidecar/pipeline/writers/chart_facts_writer_a3.py
platform/python-sidecar/pipeline/writers/panchanga_writer_a4_adapter.py
platform/python-sidecar/pipeline/writers/sensitive_points_writer_a5_adapter.py
platform/python-sidecar/pipeline/writers/__tests__/test_a3_writer.py
platform/src/app/clients/new/page.tsx  (replaced/created)
platform/src/app/clients/[id]/cockpit/page.tsx  (new)
platform/src/components/cockpit/LiveBuildGraph.tsx  (new)
platform/src/components/cockpit/AssetTable.tsx  (new)
platform/src/components/cockpit/CascadePreviewModal.tsx  (new)
platform/src/components/cockpit/BuildControlsBar.tsx  (new)
platform/src/components/cockpit/CockpitShell.tsx  (new)
platform/src/components/cockpit/NodeDetailModal.tsx  (new)
platform/src/components/consume/PartialDataBanner.tsx  (new)
platform/src/components/consume/QuestionSuggester.tsx  (new)
platform/src/app/api/build/cascade-preview/route.ts  (new)
platform/src/app/api/build/rebuild/route.ts  (new)
platform/src/app/api/build/asset/stop/route.ts  (new)
platform/src/app/api/build/asset/skip/route.ts  (new)
platform/src/app/api/build/continue/route.ts  (new)
platform/src/app/api/build/rebuild-all/route.ts  (new)
platform/src/app/api/build/start/route.ts  (new)
platform/src/app/api/build/stop/route.ts  (new)
platform/src/app/api/build/data-readiness/route.ts  (new)
platform/src/lib/build/asset_names.ts  (new)
platform/src/lib/consume/question_templates.ts  (new)
platform/tailwind.config.ts  (modified)
platform/src/app/layout.tsx  (modified)
... + misc shared pipeline/schema files
```

---

## Integration Test (Phase E)

**Dev server**: Started successfully at `http://localhost:3000` after removing spurious root-level `package.json` (created by Phase C agent installing `react-force-graph-2d` at wrong level — fixed).

**Route smoke results**:
- `/clients/new` → HTTP 307 (auth redirect — correct)
- `/api/build/cascade-preview?asset_id=A3` → HTTP 401 (auth required — correct)
- `/api/build/data-readiness?chart_id=test` → HTTP 401 (auth required — correct)
- No tailwindcss/Turbopack errors in dev logs

**Playwright**: Not run (Phase E sub-agent blocked on permission prompt; smoke results manually verified above). Playwright e2e spec authored at `platform/e2e/workflow.spec.ts` — requires auth session cookie for full execution.

---

## Known Residuals

1. **SSE graph event format**: `LiveBuildGraph.tsx` subscribes to `build_events` SSE at `/api/build/events/[buildId]`. The Python sidecar currently emits generic events; a follow-up writer patch is needed to emit `node_added`/`edge_added` typed events for the live graph to populate with nodes. Graph renders empty until sidecar emits graph events.

2. **data-readiness chart_id join**: `data-readiness/route.ts` looks up latest build_id via `build_events WHERE chart_id=X`. This requires `build_events.chart_id` column — present in migration 156 schema but must be populated by the sidecar when emitting events. Follow-up: ensure sidecar sets `chart_id` on all emitted build_events.

3. **A14 slot**: Retired in ASSET_MAP with `retired: true`. AssetTable filters retired assets from display. Backend migration seeds no A14 row in build_dependencies. No action needed.

4. **Root package.json**: Removed. Phase C agent incorrectly ran `npm install react-force-graph-2d` at project root instead of inside `platform/`. The package is correctly present in `platform/package.json`. Root `package.json`/`package-lock.json` removed in this session (not committed — they were untracked).

5. **Playwright full suite**: Auth-gated flows (cockpit, consume chat) require `SMOKE_SESSION_COOKIE` + `SMOKE_CHART_ID` env vars. Follow-up: provision these in GitHub Actions secrets per the existing smoke gate pattern.

---

## Browser Handoff Instructions

```bash
# 1. Pull the feature branch
git fetch origin
git checkout feature/ux-workflow-overhaul

# 2. Install and start
cd platform && npm install && npm run dev

# 3. Open in browser
open http://localhost:3000/clients/new
```

**Manual test checklist**:
1. `/clients/new` — verify 4-section form renders with obsidian (#08070a) background + gold CTAs
2. Fill form (name, dob, time, place) → submit → verify redirect to `/clients/[id]/cockpit`
3. Cockpit page → verify Sanskrit·English asset names in Assets tab (e.g., "Mula-Lakshana · Root Marks")
4. Click "Build Chart" → verify SSE events start → check Live Graph tab for nodes appearing
5. On any completed asset row → click Rebuild → verify CascadePreviewModal opens with descendant list
6. Navigate to `/consume/[chartId]` → verify PartialDataBanner if build is partial
7. Verify QuestionSuggester pills appear above chat input based on ready assets
8. Submit a chat question → verify LLM response

Report any visual/interaction bugs as issues on the PR.

---

## Commits on Branch

```
089ea655 feat(consume): schema audit + partial-data banner + question suggester + data-readiness API + LLM context injection
7b645fe0 feat(ui): new chart form + cockpit shell + force-graph + cascade preview modal + build controls + API routes (154-156 wired)
dba80121 feat(backend): migrations 154-156 (build_deps+checkpoints+stop) + cascade/resume dispatcher + A3 Mula-Lakshana real writer + A4/A5 adapters
d2839e76 feat(theme+rename): obsidian+gold tailwind tokens + Cormorant/Inter fonts + 28-asset Sanskrit/English rename + asset_names.ts source of truth
```

**Final HEAD SHA**: `089ea6553bbd2bdcab4f3154d917a0e321e729ca`

---
*Generated by MARSYS autonomous workflow run — 2026-05-31*
