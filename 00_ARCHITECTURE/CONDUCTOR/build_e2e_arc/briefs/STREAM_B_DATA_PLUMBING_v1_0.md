---
brief_id: STREAM_B_DATA_PLUMBING_v1_0
status: ACTIVE
arc_id: build_e2e_arc
stream: B
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataPlumbing
branch: feat/data-plumbing
base: feature/ux-workflow-overhaul
sessions: 7
estimated_loc: ~250 across 5 files
---

# Stream B — Sidecar SSE typed events + chart_id population + dedupe merge

Ships the data-plane plumbing so the cockpit's live graph can actually
accrete nodes and PartialDataBanner can find rows mid-build. Also folds
the already-shipped chart-dedupe arc onto this branch.

## Cross-cuts read first

- `00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/STREAM_COORDINATION_v1_0.md`
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SIDECAR_RESIDUALS_v1_0.md` (the original R1+R2 brief — this stream subsumes it)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CHART_DEDUPE_v1_0.md` (already executed on fix/chart-dedupe; B-S1 just merges)

## Hard gates

- NO Anthropic models.
- NO writing to any writer file under `python-sidecar/pipeline/writers/`. Only `build_events.py` + `dispatcher.py` + the test file.
- NO migration. The `build_events.chart_id` column already exists.
- If a referenced column on `build_steps` doesn't exist (cancel_reason etc.), DROP that line — never invent.
- SSE payload shape: if `LiveBuildGraph.tsx` already destructures specific field names, adapt the Python emit — FE wins. Discover via grep BEFORE coding.

## §B-S1 — Merge fix/chart-dedupe into feat/data-plumbing

```bash
git fetch origin
git merge --no-ff origin/fix/chart-dedupe -m "merge: chart-dedupe a5845e22 into data-plumbing"
```

If conflicts: halt and write blocker note. Do not improvise resolution.
The chart-dedupe arc touches `route.ts` + new migration + dedupe script;
no overlap with sidecar files, so this should be a clean merge.

Gate: `git log --oneline | grep -q 'chart-dedupe'`.

## §B-S2 — emit_node_added + emit_edge_added helpers

In `platform/python-sidecar/pipeline/build_events.py`:

1. Extend `EventType` literal union: add `'node_added'`, `'edge_added'`.
2. Add `emit_node_added(conn, build_id, chart_id, asset_id, ayanamsha_id, row_count, layer)` — reuses existing `emit_event` plumbing. Payload shape:
   `{ type, build_id, chart_id, asset_id, ayanamsha_id, row_count, layer, timestamp }`
3. Add `emit_edge_added(conn, build_id, chart_id, from_asset, to_asset, edge_kind)`.
   Payload shape: `{ type, build_id, chart_id, from_asset, to_asset, edge_kind, timestamp }`

Tests in `__tests__/test_build_events.py`:
- node_added writes notification
- edge_added writes notification
- emit failure is non-fatal

Gate: `cd platform/python-sidecar && python -m pytest pipeline/__tests__/test_build_events.py -v`.

## §B-S3 — Dispatcher wires typed events

In `platform/python-sidecar/pipeline/dispatcher.py`:

1. Import the new helpers.
2. After each writer's first successful row-write for an asset+ayanamsha, call `emit_node_added`.
3. For each upstream→downstream dependency edge (read from `build_dependencies` table — seeded by migration 154), call `emit_edge_added` ONCE per build when the downstream begins. Dedupe with in-memory `set[tuple[str,str]]`.

Gate: `cd platform/python-sidecar && python -m pytest pipeline/__tests__/ -v` (full sidecar tests green).

## §B-S4 — emit_step_event mirrors completions to build_events.chart_id

Extend `emit_step_event` signature with optional `chart_id: str | None = None`.
When supplied and `status == 'complete'`, after the existing build_steps
UPDATE + build_notifications INSERT, ALSO INSERT a row into `build_events`
(the table whose schema dispatcher.py already uses at lines 256-264).

Thread `chart_id` through every call site of `emit_step_event` (mostly in
dispatcher.py). Build loop already has chart_id in scope.

Wrap the build_events INSERT in try/except so a failure here does NOT
roll back the build_steps update or build_notifications row.

Tests:
- complete with chart_id writes build_events row
- complete without chart_id skips build_events INSERT (backwards-compat)
- build_events INSERT failure is non-fatal

Gate: `cd platform/python-sidecar && python -m pytest -k chart_id -v`.

## §B-S5 — sse_events.ts type union

In `platform/src/types/sse_events.ts`:

Add discriminated-union variants for `node_added` and `edge_added` matching
the Python payload shapes from B-S2. If `LiveBuildGraph.tsx` already
destructures different field names, adapt the Python payload (in B-S2) —
never the FE.

Gate: `cd platform && npm run build` → green.

## §B-S6 — Local smoke

End-to-end proof against the local DB via Cloud SQL proxy:

```bash
mkdir -p /tmp/build_e2e_smoke
bash platform/scripts/start_db_proxy.sh &
sleep 5
cd platform && npm install
# Apply migrations 140-156 (auto-migration runner from Stream A may not be
# merged yet — use direct psql for local smoke)
for i in $(seq 140 156); do
  psql "$DATABASE_URL" -f migrations/${i}_*.sql 2>/dev/null || true
done
# Boot dev server, mint a session cookie, trigger a build, capture SSE
npm run dev &
sleep 15
NATIVE_CHART_ID="362f9f17-95a5-490b-a5a7-027d3e0efda0"
# If native chart absent in local DB, document and skip — operator will see
# it in prod after auto-deploy. Local smoke partial is acceptable.
SESSION_COOKIE=$(npx tsx scripts/mint_session_cookie.ts --uid local-smoke --chart-id $NATIVE_CHART_ID 2>/dev/null || echo "")
if [ -n "$SESSION_COOKIE" ]; then
  BUILD_RESP=$(curl -s -X POST http://localhost:3000/api/build/start \
    -H "Cookie: __session=$SESSION_COOKIE" \
    -H "Content-Type: application/json" \
    -d "{\"chart_id\":\"$NATIVE_CHART_ID\"}")
  BUILD_ID=$(echo "$BUILD_RESP" | jq -r '.build_id')
  timeout 60 curl -N "http://localhost:3000/api/build/events/$BUILD_ID" \
    -H "Cookie: __session=$SESSION_COOKIE" > /tmp/build_e2e_smoke/sse_events.log 2>&1 || true
  # Verify R1 + R2
  grep "event: node_added" /tmp/build_e2e_smoke/sse_events.log || echo "R1 WARN: no node_added in 60s"
  psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM build_events WHERE build_id='$BUILD_ID' AND chart_id='$NATIVE_CHART_ID';" \
    > /tmp/build_e2e_smoke/r2_count.txt
fi
```

Gate: `test -f /tmp/build_e2e_smoke/sse_events.log` (even if partial; document state in commit body).

## §B-S7 — Final commit + cherry-pick to main

Per STREAM_COORDINATION §5. Note: this cherry-pick lands on a main that
already has A's auto-deploy chain (if A finished first). If A hasn't
landed yet, the merge to main goes through OLD manual deploy — that's
fine, A catches up.

Gate: `git log origin/main..HEAD --oneline | head -1` returns 0.

---

End of Stream B brief.
