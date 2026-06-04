---
brief_id: SIDECAR_RESIDUALS_v1_0
status: ACTIVE
authored_by: Cowork (planning)
executor: Claude Code in Google Antigravity IDE
authored_at: 2026-05-31
model_directive: Use Gemini Pro / DeepSeek. Anthropic banned per native standing order.
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav (single checkout — no parallel streams)
base_branch: feature/ux-workflow-overhaul    # PR #172 work — NOT main
work_branch: fix/sidecar-residuals-graph-events-and-chart-id
estimated_loc: ~120 LOC across 4 files
---

# CLAUDECODE_BRIEF — Sidecar Residuals (force-graph SSE typed events + build_events.chart_id)

## Context

PR #172 (UX/Workflow overhaul, merged-pending on `feature/ux-workflow-overhaul`)
shipped the cockpit force-graph and the `<PartialDataBanner>` data-readiness UI.
Executor flagged two open residuals that block end-to-end function:

**R1 — force-graph stays visually static during a build.**
The cockpit consumer at `platform/src/components/cockpit/LiveBuildGraph.tsx`
listens for SSE event types `node_added` and `edge_added`. The sidecar emitter
at `platform/python-sidecar/pipeline/build_events.py` currently only emits
`step_started` / `step_complete` / `step_failed` / `build_*`. The cockpit thus
sees zero structure-mutation events and the graph never accretes nodes.

**R2 — `<PartialDataBanner>` shows "no data" for every chart mid-build.**
The data-readiness route reads `build_events` filtered by `chart_id`. The
`build_events` table IS being written by `dispatcher.py` (cascade + resume
events include `chart_id`), but the per-asset row-write events from each
writer go to `build_notifications`, NOT `build_events`. The readiness lookup
therefore finds nothing per-asset.

The fix is small + sidecar-only. No DB migration needed (columns already exist).

## Scope

`may_touch`:
- `platform/python-sidecar/pipeline/build_events.py` (extend EventType, add 2 helpers)
- `platform/python-sidecar/pipeline/dispatcher.py` (wire emits into per-asset flow)
- `platform/python-sidecar/pipeline/__tests__/test_build_events.py` (new tests)
- `platform/src/types/sse_events.ts` (add the two event types to the union)
- `platform/src/components/cockpit/LiveBuildGraph.tsx` (sanity-check the
   consumer expectations — read-only; only modify if event-shape mismatch
   forces it)

`must_not_touch`:
- Any individual writer file (forensic_writer, msr_writer, cgm_writer, etc.) —
  the new emit calls land in dispatcher.py around their invocation, NOT inside
  the writers themselves
- Any migration file
- Any 00_ARCHITECTURE/ file
- The `/api/clients/create` route (separate brief: CHART_DEDUPE_v1_0)
- The cockpit force-graph React internals (graph layout, rendering) — only
  the type union is in scope on the FE side

## Pre-flight

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin
git checkout feature/ux-workflow-overhaul
git pull origin feature/ux-workflow-overhaul
git checkout -b fix/sidecar-residuals-graph-events-and-chart-id
```

Verify the cockpit consumer's expected event shape FIRST:

```bash
grep -n "node_added\|edge_added\|addEventListener" platform/src/components/cockpit/LiveBuildGraph.tsx
grep -n "node_added\|edge_added" platform/src/types/sse_events.ts || echo "TYPES NOT YET ADDED"
```

Lock the payload shape to whatever LiveBuildGraph.tsx already consumes. The
brief proposes a default shape below; **if the cockpit expects different
field names, prefer the cockpit's shape** — the sidecar is the side that
adapts.

## Task R1 — Typed SSE events for graph mutation

### R1.1 — extend `build_events.py`

In `platform/python-sidecar/pipeline/build_events.py`:

1. Add to `EventType` literal union:
   ```python
   EventType = Literal[
       'build_queued', 'build_started', 'step_started', 'step_complete',
       'step_failed', 'build_complete', 'build_failed', 'build_cancelled',
       'node_added', 'edge_added',   # NEW
   ]
   ```

2. Add two helper functions (place after `emit_step_event`):

   ```python
   def emit_node_added(
       conn,
       build_id: str,
       chart_id: str,
       asset_id: str,
       ayanamsha_id: Optional[str],
       row_count: int,
       layer: str,                    # 'L1' | 'L2_5' | 'L3'
   ) -> None:
       """
       Emit a graph-node-added event the moment an asset's first rows persist.
       Cockpit force-graph adds the node to its layout on receipt.

       Payload contract (locked to LiveBuildGraph.tsx consumer):
         { type, build_id, chart_id, asset_id, ayanamsha_id, row_count, layer, timestamp }
       """
       emit_event(
           conn, build_id, 'node_added',
           asset_id=asset_id,
           ayanamsha_id=ayanamsha_id,
           rows_written=row_count,
           extra={'chart_id': chart_id, 'layer': layer},
       )


   def emit_edge_added(
       conn,
       build_id: str,
       chart_id: str,
       from_asset: str,
       to_asset: str,
       edge_kind: str = 'depends_on',
   ) -> None:
       """
       Emit a graph-edge-added event when a downstream asset begins consuming
       an upstream asset. Cockpit force-graph draws the edge on receipt.

       Payload contract:
         { type, build_id, chart_id, from_asset, to_asset, edge_kind, timestamp }
       """
       emit_event(
           conn, build_id, 'edge_added',
           extra={
               'chart_id': chart_id,
               'from_asset': from_asset,
               'to_asset': to_asset,
               'edge_kind': edge_kind,
           },
       )
   ```

   Both helpers reuse the existing `emit_event` plumbing (which already does
   the INSERT INTO build_notifications + error-non-fatal pattern). Do not
   duplicate that plumbing.

### R1.2 — wire the calls in `dispatcher.py`

In `platform/python-sidecar/pipeline/dispatcher.py`, locate the per-asset
build loop (the section that drives each writer per ayanamsha). For every
successful first-row persist of an asset:

```python
from .build_events import emit_node_added, emit_edge_added

# After the writer's first successful write for this asset+ayanamsha
emit_node_added(
    conn,
    build_id=build_id,
    chart_id=chart_id,
    asset_id=asset_id,
    ayanamsha_id=ayanamsha_id,
    row_count=rows_written,
    layer=_layer_for_asset(asset_id),   # use ASSET_REGISTRY layer field
)
```

For each upstream→downstream dependency edge (read from
`build_dependencies` table seeded by migration 154 in PR #172), emit
`emit_edge_added` once per build, the first time the downstream begins.
Deduplicate emits per build with a small in-memory set
`emitted_edges: set[tuple[str,str]]`.

### R1.3 — tests

Add to `platform/python-sidecar/pipeline/__tests__/test_build_events.py`:

1. `test_emit_node_added_writes_notification` — patches conn, asserts INSERT
   INTO build_notifications fired with event_type='node_added' and payload
   contains `chart_id`, `asset_id`, `layer`, `row_count`.

2. `test_emit_edge_added_writes_notification` — same pattern for edge_added,
   payload contains `from_asset`, `to_asset`, `edge_kind`.

3. `test_emit_node_added_failure_is_non_fatal` — make conn.cursor() raise;
   assert function returns None without re-raising (matches existing pattern).

Run:
```bash
cd platform/python-sidecar
python -m pytest pipeline/__tests__/test_build_events.py -v
```

### R1.4 — FE type alignment

Read `platform/src/types/sse_events.ts`. If it already has discriminated-union
entries for `node_added` and `edge_added`, verify field names match the
payloads above; adjust the Python `extra={...}` to match if mismatched. If the
types are absent, add them:

```ts
export type BuildSseEvent =
  | { type: 'build_queued'; build_id: string; timestamp: string }
  | // ... existing variants ...
  | {
      type: 'node_added';
      build_id: string;
      chart_id: string;
      asset_id: string;
      ayanamsha_id: string | null;
      row_count: number;
      layer: 'L1' | 'L2_5' | 'L3';
      timestamp: string;
    }
  | {
      type: 'edge_added';
      build_id: string;
      chart_id: string;
      from_asset: string;
      to_asset: string;
      edge_kind: 'depends_on' | string;
      timestamp: string;
    };
```

If `LiveBuildGraph.tsx` already destructures different field names, **the FE
wins** — change the Python payload, not the consumer.

## Task R2 — populate `build_events.chart_id` for per-asset rows

The `build_events` table is already chart_id-aware (dispatcher.py inserts
include it for cascade + resume rows). The gap is per-asset write events,
which currently only go to `build_notifications`.

Decision (Cowork): mirror each per-asset `emit_step_event('complete', …)`
call with one `build_events` row using the same `chart_id`. Same connection,
same transaction, same non-fatal failure pattern.

### R2.1 — extend `emit_step_event`

In `build_events.py`, change `emit_step_event` to accept an optional
`chart_id` parameter (default `None`) and, when supplied and status is
`'complete'`, ALSO INSERT a row into `build_events` after the existing
build_steps UPDATE + build_notifications INSERT. The new row mirrors
the schema dispatcher.py uses (already documented at dispatcher.py:249-264):

```python
cur.execute(
    """
    INSERT INTO build_events
        (build_id, stage_seq, chart_id, ayanamsha_role, asset, stage, status, metadata, emitted_at)
    VALUES (
        %s,
        COALESCE((SELECT MAX(stage_seq)+1 FROM build_events WHERE build_id=%s), 1),
        %s, %s, %s, %s, %s, %s, NOW()
    )
    """,
    (
        build_id, build_id, chart_id, ayanamsha_id, asset_id,
        stage, status, json.dumps({'rows_written': rows_written}),
    ),
)
```

Wrap that single statement in a try/except so a `build_events` insert
failure does NOT roll back the `build_steps` update or the
`build_notifications` row.

### R2.2 — pass chart_id at every call site

In `dispatcher.py` (and any other caller of `emit_step_event`), pass
`chart_id` through. Quick scan + thread it; the build loop already has
chart_id in scope.

### R2.3 — test

In `test_build_events.py`:

`test_emit_step_event_complete_writes_build_events_row_when_chart_id_supplied` —
patches conn, asserts that on `status='complete'` the INSERT INTO
build_events fires with the correct chart_id, asset, stage, status.

`test_emit_step_event_complete_skips_build_events_when_chart_id_absent` —
asserts NO INSERT INTO build_events fires when chart_id is None
(backwards-compat for existing tests).

`test_emit_step_event_build_events_insert_failure_is_non_fatal` — make the
build_events insert raise; assert build_steps update + build_notifications
insert still committed.

## Smoke (local)

```bash
# DB proxy + dev server
bash platform/scripts/start_db_proxy.sh &
cd platform && npm install && npm run dev

# Trigger a build for the native chart in another shell:
# (use the cockpit Build button at http://localhost:3000/clients/<native_uuid>/build)

# Watch SSE on the build:
curl -N "http://localhost:3000/api/build/events/<build_id>" -b "__session=<your_session>"
# Expect node_added events as each asset's first row lands;
# expect edge_added events as downstream assets begin.

# Verify build_events.chart_id populated:
psql "$DATABASE_URL" -c "SELECT chart_id, asset, status, COUNT(*) \
  FROM build_events WHERE build_id='<build_id>' GROUP BY 1,2,3 ORDER BY 1,2;"
# Expect chart_id non-null for every row.
```

Smoke is operator-driven if no DB proxy is available in the executor's
environment. Document smoke outcome (PASS/SKIPPED) in the commit body.

## Commit + push

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git add platform/python-sidecar/pipeline/build_events.py
git add platform/python-sidecar/pipeline/dispatcher.py
git add platform/python-sidecar/pipeline/__tests__/test_build_events.py
git add platform/src/types/sse_events.ts
# only stage LiveBuildGraph.tsx if a field-name fix was required:
git add platform/src/components/cockpit/LiveBuildGraph.tsx 2>/dev/null || true

git status
git commit -m "fix(sidecar): typed graph mutation SSE events + per-asset build_events.chart_id

R1: emit_node_added + emit_edge_added helpers; wired in dispatcher per-asset.
    Cockpit force-graph (PR #172) now receives structure-mutation events
    and accretes nodes/edges during build.

R2: emit_step_event optionally mirrors completion to build_events with
    chart_id. PartialDataBanner data-readiness lookup now finds per-asset
    rows mid-build.

No schema migration — build_events.chart_id column already present
(migration 118). No FE behavior change beyond type-union extension.

Brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SIDECAR_RESIDUALS_v1_0.md
PR #172 base. Native sign-off PENDING; do not merge to main."

git push -u origin fix/sidecar-residuals-graph-events-and-chart-id
```

## Hard gates

- DO NOT modify any writer file under `python-sidecar/pipeline/writers/`.
- DO NOT add a migration. The columns already exist.
- DO NOT modify the force-graph layout/rendering — only the event type union.
- DO NOT merge `fix/sidecar-residuals-…` into anything.
- DO NOT use Anthropic models.
- DO NOT broaden scope to "while we're here" cleanups in dispatcher.py or
  build_events.py. Land only the R1/R2 changes above.

## Acceptance criteria

- [ ] `python -m pytest platform/python-sidecar/pipeline/__tests__/test_build_events.py -v` all green.
- [ ] `npm run build` in `platform/` succeeds.
- [ ] `grep -rn "emit_node_added\|emit_edge_added" platform/python-sidecar/pipeline/` shows calls in BOTH `build_events.py` (defs) AND `dispatcher.py` (callers).
- [ ] `grep -n "chart_id" platform/python-sidecar/pipeline/build_events.py` shows chart_id threaded through emit_step_event.
- [ ] `sse_events.ts` type union includes `node_added` and `edge_added` variants.
- [ ] Smoke either PASSED or documented SKIPPED-no-DB-proxy in commit body.

## Operator post-merge

1. Merge `fix/sidecar-residuals-…` into `feature/ux-workflow-overhaul`.
2. Cherry-pick to main after PR #172 lands.
3. Rebuild sidecar image + push (`platform-sidecar/cloudbuild.yaml` — NOT root cloudbuild.yaml).
4. Smoke a chart build from the cockpit; verify graph accretes nodes live and PartialDataBanner counts climb.

---

End of brief.
