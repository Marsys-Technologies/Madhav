# Nirmana Build Tracker — Comprehensive Fixes

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all observed issues in the Nirmana build tracker — CGM writer data bugs, orchestrator state correctness, missing registry data, UI Plan button, and stale documentation — making the L2 Bodha build seamless end-to-end.

**Architecture:** Python sidecar orchestrator (wave-parallel `execute_dag()` + `_schedule_parallel()`) feeds state to a Next.js frontend via SSE (`useCockpitSSE`) and polling (`useActiveRun`). Asset state lives in `asset_throughput` (per-chart current state) and `build_run_assets` (per-run history). The UI renders per-asset rows in `LayerPanel` → `AssetRow`.

**Tech Stack:** Python 3.11 + psycopg3 + ThreadPoolExecutor (sidecar), Next.js 15 + TypeScript + Framer Motion (frontend), PostgreSQL (DB), Vertex AI (bo_samskara embeddings).

---

## Observation ↔ Task Map

**Phase 1 — Original 13 scheduler/UI observations (Tasks 1–13):**
Tasks 1 and 2 are ✅ COMMITTED. Tasks 3–13 are pending.

| ID | Severity | Task | Root cause |
|----|----------|------|------------|
| F1 | Critical | ~~Task 1~~ ✅ DONE | `_futures_wait()` has no timeout — Vertex AI hang blocks scheduler forever |
| F5 | High | ~~Task 2~~ ✅ DONE | No per-asset timeout enforcement in `execute_dag()` |
| F4 | High | Task 3 | Stop button gated on `current_asset_id` match, not live asset state |
| F3 | High | Task 4 | Error state never stored (F1 root); verify visual display after F1 fix |
| F6 | Medium | Task 5 | Accordion expand in pre-build state — investigate & verify |
| F8 | Medium | Task 6 | Plan order (topo) vs table order (sort_order) may diverge |
| F12 | Medium | Task 7 | `estimated_seconds` is static registry value, null for Bodha |
| F13 | Low | Task 8 | PlanModal asset list shows no DRAFT/CURRENT badge |
| F7 | Medium | Task 9 | Font preload warnings — verification only |
| F9 | Medium | Task 10 | bo_samvada position 10 — confirm by design, document |
| F10 | Medium | Task 11 | bo_cdlm_summary 5 rows — confirm by design, document |
| F11 | Medium | Task 12 | bo_sangati 100 rows — confirm by design, document |
| F14 | Low | Task 13 | L2 handoff doc missing bo_drishti + bo_anveshana |

**Phase 2 — CGM writer data bugs (Tasks 14–18, discovered 2026-06-29 via deep root-cause analysis):**
These are the primary blockers for bo_cgm_motifs and bo_cgm_paths producing 0 rows.

| ID | Severity | Task | Root cause |
|----|----------|------|------------|
| B1 | P0 | Task 14 | `bo_bimba._fetch_graha_positions()` uses `subject.title()` — maps 7/9 graha codes wrong (MAR→Mar≠Mars) → 7 grahas get `position_in_chart_jsonb=null` → stellium and self-ruling chain detectors produce 0 rows |
| B2 | P0 | Task 15 | `asset_runner.py` unconditionally writes `state='lit'` after any successful writer run, even when `rows_written=0` → plan API `action:'build'` excludes the asset (state='lit' ≠ dormant/error/missing) → Build button yields empty plan |
| B3 | P0 | Task 16 | Current `asset_throughput` state for bo_cgm_motifs + bo_cgm_paths is `lit` (wrong) despite 0 rows — needs one-time data correction via migration |
| B4 | P1 | Task 17 | `asset_registry.target_table` is NULL for both CGM assets — registry incomplete |
| B5 | P1 | Task 18 | `CascadePreviewModal` shows "No assets in plan." with no actionable context when plan is empty — user has no recovery path |

---

## File Map

| File | Tasks |
|------|-------|
| `platform/python-sidecar/pipeline/orchestrator/runner.py` | 1, 2 |
| `platform/src/lib/components/cockpit/v2/LayerPanel.tsx` | 3, 5 |
| `platform/src/lib/components/cockpit/v2/AssetRow.tsx` | 4 |
| `platform/src/app/api/cockpit/plan/route.ts` | 7 |
| `platform/src/lib/build/plan.ts` | 7, 8 |
| `platform/src/lib/components/cockpit/v2/PlanModal.tsx` | 8 |
| `platform/scripts/seed/asset_registry_seed.ts` | 6, 8 |
| `00_ARCHITECTURE/L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md` | 13 |

---

## Task 1 — F1: Add per-asset timeout to wave-parallel scheduler

**Root cause:** `execute_dag()` (runner.py:246) calls `_futures_wait(in_flight, return_when=FIRST_COMPLETED)` with no `timeout`. When bo_samskara's Vertex AI embedding call hangs indefinitely (blocking I/O — not a crash), the worker thread never raises, so the crash-recovery path (lines 350–375) never fires. The scheduler waits forever, the run stays `running`, the UI shows "Building…" with no error.

**Files:**
- Modify: `platform/python-sidecar/pipeline/orchestrator/runner.py`

- [ ] **Step 1: Read the current `execute_dag()` function**

  Read lines 183–265. Confirm:
  - Line 246: `done, _ = _futures_wait(list(in_flight), return_when=FIRST_COMPLETED)` — no timeout argument.
  - Lines 247–252: `fut.result()` is called; a future that hangs never lands here.
  - No per-asset elapsed time tracking exists.

- [ ] **Step 2: Write the failing test**

  Add to `platform/python-sidecar/tests/test_wave_scheduler.py` (this file already exists and imports `execute_dag` — add at the bottom rather than creating a new file to reuse the existing infrastructure):

  ```python
  def test_asset_timeout_marks_as_failed():
      """An asset that runs longer than ASSET_TIMEOUT_SEC must be marked failed."""
      import time as _t
      import threading

      hang_started = threading.Event()

      def run_fn(asset_id):
          hang_started.set()
          _t.sleep(999)  # simulates a hanging Vertex AI call
          return "lit"

      import pipeline.orchestrator.runner as mod
      orig = mod.ASSET_TIMEOUT_SEC
      mod.ASSET_TIMEOUT_SEC = 2  # 2s for test speed
      try:
          start = _t.monotonic()
          failed, terminal = execute_dag(
              plan=["bo_samskara"],
              deps_of={"bo_samskara": []},
              run_fn=run_fn,
              worker_limit=1,
              on_timeout=lambda a, msg: None,
          )
          elapsed = _t.monotonic() - start
      finally:
          mod.ASSET_TIMEOUT_SEC = orig

      assert "bo_samskara" in failed, "timed-out asset must be in failed set"
      assert elapsed < 10, "scheduler must not hang past timeout"
  ```

- [ ] **Step 3: Run test to confirm failure**

  ```bash
  cd platform/python-sidecar
  python -m pytest tests/test_wave_scheduler.py::test_asset_timeout_marks_as_failed -v
  ```
  Expected: `FAILED` — `execute_dag` has no `on_timeout` parameter yet and hangs.

- [ ] **Step 4: Add `ASSET_TIMEOUT_SEC` constant + `on_timeout` callback to `execute_dag()`**

  Add `import time as _time` to the **module-level import block** (around line 12, with the other stdlib imports). Do not put it inside `execute_dag()`.

  After the existing imports (around line 26), add:
  ```python
  ASSET_TIMEOUT_SEC: int = int(os.environ.get("ORCHESTRATOR_ASSET_TIMEOUT_SEC", "300"))
  _POLL_INTERVAL: float = 5.0  # seconds between signal checks + timeout checks
  ```

  In `execute_dag()` signature (line 183), add `on_timeout=None`:
  ```python
  def execute_dag(
      plan: list[str],
      deps_of: dict[str, list[str]],
      run_fn,
      worker_limit: int,
      seed_completed: Optional[set] = None,
      on_block=None,
      should_stop=None,
      on_timeout=None,          # NEW: called when an asset exceeds ASSET_TIMEOUT_SEC
  ) -> tuple[set[str], Optional[str]]:
  ```

  Add `_on_timeout = on_timeout or (lambda a, msg: None)` after the existing `_block`/`_stop` lines.

  Add per-asset start-time tracking dict just before the `with ThreadPoolExecutor` block (uses the module-level `_time` import added above):
  ```python
  _in_flight_start: dict = {}  # future -> submit_time (monotonic)
  ```

  When dispatching a future (after `in_flight[pool.submit(run_fn, a)] = a`), also record the start time:
  ```python
  _fut = pool.submit(run_fn, a)
  in_flight[_fut] = a
  _in_flight_start[_fut] = _time.monotonic()
  pending.remove(a)
  progressed = True
  ```

  Replace line 246 (`done, _ = _futures_wait(...)`) with:
  ```python
  done, _ = _futures_wait(
      list(in_flight), return_when=FIRST_COMPLETED, timeout=_POLL_INTERVAL
  )
  ```

  After the `for fut in done:` block (after line 252), add the timeout check:
  ```python
  # Per-asset timeout: any in-flight future older than ASSET_TIMEOUT_SEC is forfeit.
  _now = _time.monotonic()
  for _tfut in list(in_flight):
      _age = _now - _in_flight_start.get(_tfut, _now)
      if _age > ASSET_TIMEOUT_SEC:
          _ta = in_flight.pop(_tfut)
          _in_flight_start.pop(_tfut, None)
          failed.add(_ta)
          _msg = f"asset_timeout: {_ta} exceeded {ASSET_TIMEOUT_SEC}s (actual {_age:.0f}s)"
          logger.error("[orchestrator] %s", _msg)
          _on_timeout(_ta, _msg)
  ```

  Also clean up `_in_flight_start` when futures complete normally (inside `for fut in done:`):
  ```python
  for fut in done:
      a = in_flight.pop(fut)
      _in_flight_start.pop(fut, None)   # NEW
      (failed if fut.result() == "error" else completed).add(a)
  ```

- [ ] **Step 5: Wire `on_timeout` in `_schedule_parallel()`**

  In `_schedule_parallel()`, after the `on_block` closure (around line 383), add:
  ```python
  def on_timeout(asset_id: str, msg: str) -> None:
      """Open a fresh connection to mark the timed-out asset as error."""
      try:
          from .asset_runner import mark_asset_error as _mark_err
          _tconn = connect()
          _tconn.autocommit = False
          _tcur = _tconn.cursor()
          _mark_err(_tconn, _tcur, run_id, eff(asset_id), asset_id, msg)
          _tconn.close()
      except Exception as _te:
          logger.error("[orchestrator] timeout-cleanup failed for %s: %s", asset_id, _te)
  ```

  Pass it to `execute_dag()` at line 386:
  ```python
  return execute_dag(
      plan=pending,
      deps_of=deps_of,
      run_fn=worker,
      worker_limit=_WORKER_LIMIT,
      seed_completed=completed,
      on_block=on_block,
      should_stop=should_stop,
      on_timeout=on_timeout,   # NEW
  )
  ```

- [ ] **Step 6: Run test to confirm pass**

  ```bash
  cd platform/python-sidecar
  python -m pytest tests/test_wave_scheduler.py::test_asset_timeout_marks_as_failed -v
  ```
  Expected: `PASSED` — scheduler returns within `ASSET_TIMEOUT_SEC + POLL_INTERVAL` seconds with `bo_samskara` in the failed set.

- [ ] **Step 7: Run full test suite**

  ```bash
  cd platform/python-sidecar
  python -m pytest tests/ -v --tb=short
  ```
  Expected: all existing tests pass (the new `on_timeout=None` default is backward-compatible).

- [ ] **Step 8: Commit**

  ```bash
  git add platform/python-sidecar/pipeline/orchestrator/runner.py \
           platform/python-sidecar/tests/test_wave_scheduler.py
  git commit -m "fix(orchestrator): per-asset timeout in execute_dag — prevents infinite stall on hung writer"
  ```

---

## Task 2 — F5: Emit SSE stall event + clear run state on timeout

**Context:** Task 1 fixes the scheduler. This task ensures the frontend and run record reflect the timeout correctly: the run must NOT stay `running` after all assets are either complete/failed/timed-out.

**Files:**
- Modify: `platform/python-sidecar/pipeline/orchestrator/runner.py`

- [ ] **Step 1: Verify run completion after timeout**

  After Task 1, when an asset times out:
  1. `on_timeout()` calls `mark_asset_error()` → writes `asset_throughput.state='error'`, emits `asset.state_change` SSE.
  2. The future is added to `failed`.
  3. Downstream assets get blocked via `on_block`.
  4. `execute_dag()` returns `(failed_set, None)`.
  5. `execute_run()` calls `mark_run_state(... "completed", ended_at=True)` and emits `run.state_change` with `state: "completed"`.

  This is correct behavior — a run that completed with failures is still `completed` (not `running`).

- [ ] **Step 2: Emit explicit stall SSE for observability**

  In `on_timeout()` (added in Task 1), after `mark_asset_error()`, add a run-scoped SSE event so the UI can surface "N assets timed out":
  ```python
  emit_event({
      "type": "asset.timeout",
      "chart_id": eff(asset_id),
      "asset_id": asset_id,
      "run_id": run_id,
      "timeout_sec": ASSET_TIMEOUT_SEC,
  })
  ```

- [ ] **Step 3: Verify frontend surfacing via existing `asset.state_change` event**

  The `on_timeout` callback calls `mark_asset_error()`, which already emits `asset.state_change` with `to_state: "error"`. The frontend SSE hook (`useCockpitSSE.ts`) has a registered `addEventListener` for `asset.state_change` — this fires correctly and turns the asset row red. No additional frontend handler is needed for `asset.timeout`.

  Do NOT add `asset.timeout` as a named SSE event type: browser `EventSource` only dispatches named events to explicitly registered `addEventListener` listeners, and `asset.timeout` is not in the `CockpitEvent` union type. Adding an unregistered handler would be silently dropped and is unnecessary since `asset.state_change → error` covers the same ground.

  Confirm this works: after implementing Task 1, trigger a build with a deliberately slow writer and verify the asset row turns red within `ASSET_TIMEOUT_SEC + 5s` via the existing error surfacing path.

- [ ] **Step 4: Verify in browser (after running a build)**

  Start a Layer 2 Bodha build. Confirm:
  - If bo_samskara completes normally: no change in behavior.
  - If bo_samskara were to stall (simulate by temporarily making the writer `time.sleep(999)`): within `ASSET_TIMEOUT_SEC + 5s`, the asset row turns red/error, downstream assets show "blocked by upstream failure", and the run transitions to `completed`.

- [ ] **Step 5: Commit**

  ```bash
  git add platform/python-sidecar/pipeline/orchestrator/runner.py
  git commit -m "fix(orchestrator): emit asset.timeout SSE on per-asset stall; run completes via asset.state_change→error"
  ```

---

## Task 3 — F4: Fix Stop button appearing on completed assets

**Root cause:** `LayerPanel.tsx:381` computes `isActiveAsset` by checking `activeRun.current_asset_id === asset.asset_id`. In wave-parallel builds, `current_asset_id` is set when an asset *starts* and isn't cleared when it *completes*. After bo_cdlm_summary finishes (but the run stalls on bo_samskara), `current_asset_id` still points to bo_cdlm_summary, so it keeps showing the Stop button.

**Fix:** Gate Stop on the live asset throughput state (`'building'`) rather than the stale `current_asset_id` column.

**Files:**
- Modify: `platform/src/lib/components/cockpit/v2/LayerPanel.tsx`

- [ ] **Step 1: Read the current `isActiveAsset` expression**

  Read `LayerPanel.tsx` around lines 375–390. Confirm line 381:
  ```tsx
  isActiveAsset={assetRunActive && activeRun!.current_asset_id === asset.asset_id}
  ```
  The `stats` prop (a `Map<string, AssetStats>`) is already available in LayerPanel — confirm it's in scope at the `<AssetRow>` render site.

- [ ] **Step 2: Write the failing test**

  In `platform/src/lib/components/cockpit/v2/__tests__/LayerPanel.test.tsx` (create or add):
  ```typescript
  it('does not show Stop button on a completed asset during an active run', () => {
    // Simulate: run is active, current_asset_id = 'bo_samskara',
    // bo_cdlm_summary is state='lit' (completed this run)
    // The Stop button should NOT appear on bo_cdlm_summary
    const stats = new Map([
      ['bo_cdlm_summary', { state: 'lit', actual_rows: 5, last_built_at: new Date().toISOString() }],
      ['bo_samskara', { state: 'building', actual_rows: 0, last_built_at: null }],
    ])
    const activeRun = { id: 'run-1', state: 'running', current_asset_id: 'bo_cdlm_summary', scope: 'layer' }
    // Render LayerPanel with these props and assert StopIconButton is absent for bo_cdlm_summary
    // and present for bo_samskara
    // (actual render assertions depend on your test setup)
  })
  ```

- [ ] **Step 3: Change `isActiveAsset` to use throughput state**

  In `LayerPanel.tsx` line 381, replace:
  ```tsx
  isActiveAsset={assetRunActive && activeRun!.current_asset_id === asset.asset_id}
  ```
  with:
  ```tsx
  isActiveAsset={assetRunActive && stats.get(asset.asset_id)?.state === 'building'}
  ```

  This uses the live `asset_throughput.state` (polled every 5s) instead of the stale `current_asset_id` column. A completed asset has `state='lit'`; only actively-building assets have `state='building'`.

- [ ] **Step 4: Verify in browser**

  Run a Bodha build. During the build, confirm:
  - Assets with `state='building'` (currently executing) show the Stop button.
  - Assets with `state='lit'` (completed in this run) do NOT show Stop.
  - After the run completes (`run.state_change` SSE or polling), Stop disappears from all assets.

- [ ] **Step 5: Commit**

  ```bash
  git add platform/src/lib/components/cockpit/v2/LayerPanel.tsx
  git commit -m "fix(cockpit): Stop button uses live throughput state instead of stale current_asset_id"
  ```

---

## Task 4 — F3: Verify error state visual display in AssetRow

**Context:** With F1 fixed, `asset_throughput.state` is now correctly set to `'error'` when an asset times out or crashes. This task verifies the UI actually shows the red error state — no code changes expected, but a verification + defensive check.

**Files:**
- Read: `platform/src/lib/components/cockpit/v2/AssetRow.tsx` (lines 140–165 for StatusDot, 342–360 for error text)

- [ ] **Step 1: Verify StatusDot renders red for `state='error'`**

  Read `AssetRow.tsx` lines 120–165. Find the `StatusDot` component. Confirm:
  - `state='error'` maps to a red/pink color (not dormant grey or gold).
  - The `hasError` flag at line 253 (`stat?.error != null && ...`) correctly triggers red error text below the progress bar (lines 342–360).

  If StatusDot has no explicit case for `'error'` and falls through to a dormant color, add it:
  ```typescript
  const color = state === 'lit' ? 'rgba(76,175,80,0.9)'
    : state === 'building' ? 'rgba(236,197,106,0.9)'
    : state === 'error' ? 'rgba(232,108,108,0.9)'    // ensure this exists
    : state === 'stale' ? 'rgba(236,197,106,0.45)'
    : 'rgba(255,255,255,0.15)' // dormant
  ```

- [ ] **Step 2: Verify stats API returns `state='error'` for errored assets**

  Read `platform/src/app/api/cockpit/stats/route.ts`. Confirm the query selects `state` from `asset_throughput` without filtering out `'error'` rows.

- [ ] **Step 3: Verify `hasError` suppression logic is correct**

  In `AssetRow.tsx` line 253:
  ```typescript
  const hasError = stat?.error != null && stat.error !== 'missing_table' && !isDataPlaneDown
  ```
  Confirm that when `state='error'` and `last_error` is populated in `asset_throughput`, the stats API maps `last_error` → `stat.error`. Trace the field name through the stats route query.

- [ ] **Step 4: Manual E2E test**

  In the Python sidecar, temporarily make bo_laksana raise a deliberate error:
  ```python
  # In bo_laksana.py run(), top of function:
  raise RuntimeError("deliberate_test_error")
  ```
  Trigger a Bodha build. Confirm:
  - bo_laksana row turns red in the UI within 10s.
  - Error text below the progress bar shows `RuntimeError: deliberate_test_error` (truncated at 64 chars).
  - Downstream assets show "blocked by upstream failure" in amber.
  - Revert the deliberate error before committing.

- [ ] **Step 5: Commit (only if code changes were needed)**

  ```bash
  git add platform/src/lib/components/cockpit/v2/AssetRow.tsx
  git commit -m "fix(cockpit): ensure StatusDot shows red for state='error'"
  ```
  Skip commit if no changes were needed (verification only).

---

## Task 5 — F6: Investigate and fix layer accordion in pre-build state

**Context:** Observation reports that clicking the Bodha layer header when no build is active doesn't expand to show individual assets. Code inspection shows `onClick={() => setExpanded(!expanded)}` which should toggle. Investigation required to find the actual cause.

**Files:**
- Read: `platform/src/lib/components/cockpit/v2/LayerPanel.tsx` (lines 100–170)
- Likely read: wherever `LayerPanel` is rendered (search for `<LayerPanel`)

- [ ] **Step 1: Trace `defaultExpanded` from parent to LayerPanel**

  ```bash
  grep -rn "LayerPanel\|defaultExpanded\|forceExpand" \
    platform/src/lib/components/cockpit/v2/ | grep -v "\.d\.ts"
  ```
  Find which component renders `<LayerPanel>` and what value it passes for `defaultExpanded`.

- [ ] **Step 2: Check if accordion body conditionally renders vs always-mounts**

  Read `LayerPanel.tsx` lines 320–400. Confirm:
  - Body uses `{expanded && (...)}` — it unmounts when collapsed (correct, just hidden).
  - No `key` prop on LayerPanel that would remount the component on state changes (which would reset `expanded` to `defaultExpanded`).

- [ ] **Step 3: Check for click propagation issues**

  Read the header `<button>` element (lines ~155–220). Confirm:
  - The `onClick={setExpanded(!expanded)}` button is the outermost header element.
  - No child element inside the header calls `e.stopPropagation()`.
  - The BuildActionButton inside the header does NOT capture clicks that bubble to the header button.

- [ ] **Step 4: Reproduce the bug in browser**

  Navigate to the Nirmana page with no active run. Click the Bodha layer header. Observe:
  - If it expands: the bug is intermittent or was a one-time observation. Document as `cannot reproduce — working as designed`.
  - If it doesn't expand: open browser DevTools console, click again, look for JS errors.

- [ ] **Step 5: Fix if reproducible**

  The most likely cause is that `defaultExpanded` changes after user interaction, re-triggering the `useEffect` that sets `expanded=true`. If `defaultExpanded` is derived from a computed value (e.g., `activeRun?.scope_target === layer`) that flips to `false` mid-session, the useEffect only fires on change to `true` (never back to `false`), so this isn't the issue.

  Alternative: if the parent passes a new `key` to LayerPanel when chart state changes, the component remounts with `expanded=defaultExpanded`. Fix by removing unnecessary `key` changes:
  ```tsx
  // If you find something like this in the parent:
  <LayerPanel key={`${layer}-${activeRun?.id}`} .../>
  // Change to:
  <LayerPanel key={layer} .../>
  ```

- [ ] **Step 6: Commit (only if a fix was applied)**

  ```bash
  git add platform/src/lib/components/cockpit/v2/LayerPanel.tsx  # or parent component
  git commit -m "fix(cockpit): layer accordion expands correctly in pre-build state"
  ```

---

## Task 6 — F8: Align build plan dialog order with table order

**Context:** The Build Plan dialog (PlanModal) shows assets in topological execution order (from `resolveBuildPlan()` → `topoSort()`). The expanded layer table shows assets in `sort_order` from the registry. These may diverge. Both should show assets in the same topological order so the user can compare them easily.

**Files:**
- Read: `platform/scripts/seed/asset_registry_seed.ts` (Bodha asset entries)
- Read: `platform/src/lib/build/plan.ts` (topoSort)

- [ ] **Step 1: Compare current sort_order vs topo order for Bodha assets**

  ```bash
  # Query the DB for current bodha sort_order
  psql "$DATABASE_URL" -c "
    SELECT asset_id, sort_order, depends_on
    FROM asset_registry
    WHERE layer = 'bodha'
    ORDER BY sort_order
  "
  ```

  Separately, trace `topoSort()` in `plan.ts` for the Bodha assets to determine their topological order. Write the topo order on paper:
  1. bo_laksana (no deps)
  2. bo_bimba, bo_karanajala, bo_sangati, bo_samvada_prelim (depend on bo_laksana)
  3. bo_samskara (depends on bo_sangati / bo_msr)
  4. bo_upaya (depends on bo_msr / bo_laksana)
  5. bo_pramana_mapa (depends on bo_sangati)
  6. bo_chart_gestalt, bo_cdlm_summary, bo_cgm_motifs, bo_cgm_paths (synthesis — depend on multiple)
  7. bo_samvada (VIEW writer — depends on all data tables)
  8. bo_drishti, bo_anveshana (if registered)

- [ ] **Step 2: Check if sort_order already matches topological order**

  Compare the DB `sort_order` values to the topo order above. If `sort_order=10` means "10th in layer" and already matches the topo sequence, no code change needed — F8 is cosmetic only (document as working).

- [ ] **Step 3: Fix sort_order if misaligned**

  If sort_order doesn't match topological order, write a surgical migration:
  ```sql
  -- platform/migrations/XXXX_bodha_sort_order_topo_align.sql
  UPDATE asset_registry SET sort_order = 1 WHERE asset_id = 'bo_laksana';
  UPDATE asset_registry SET sort_order = 2 WHERE asset_id = 'bo_bimba';
  -- ... continue for all bodha assets in topo order
  ```
  Also update the seed script to keep them in sync for future resets.

- [ ] **Step 4: Commit (only if changes were made)**

  ```bash
  git add platform/migrations/ platform/scripts/seed/asset_registry_seed.ts
  git commit -m "fix(seed): bodha asset sort_order aligned to topological execution order"
  ```

---

## Task 7 — F12: Populate estimated build time from historical medians

**Context:** The Build Plan dialog shows "estimated unknown" because `asset_registry.estimated_seconds` is null for Bodha assets. Fix: query `build_run_assets` for the historical median elapsed per asset, sum for the plan.

**Files:**
- Modify: `platform/src/app/api/cockpit/plan/route.ts`
- Modify: `platform/src/lib/build/plan.ts`

- [ ] **Step 1: Read the current plan route**

  Read `plan/route.ts` lines 1–53. Confirm `estimated_seconds` comes from `asset_registry` (line 28) and flows through `resolveBuildPlan()`. Confirm `BuildPlan.estimated_seconds` is summed from per-asset `estimated_seconds` in `plan.ts`.

- [ ] **Step 2: Write the failing test**

  In `platform/src/lib/build/__tests__/plan.test.ts` (create if absent):
  ```typescript
  it('uses historical median when registry estimated_seconds is null', () => {
    const registry = [
      { asset_id: 'bo_laksana', layer: 'bodha', depends_on: [], estimated_seconds: null },
      { asset_id: 'bo_bimba',   layer: 'bodha', depends_on: ['bo_laksana'], estimated_seconds: null },
    ]
    const throughput = new Map([
      ['bo_laksana', { asset_id: 'bo_laksana', state: 'dormant' as const }],
      ['bo_bimba',   { asset_id: 'bo_bimba', state: 'dormant' as const }],
    ])
    const historicalMedians = new Map([
      ['bo_laksana', 45],   // 45 seconds historical median
      ['bo_bimba', 120],    // 120 seconds historical median
    ])
    const plan = resolveBuildPlan({
      scope: 'layer', scope_target: 'bodha', action: 'build',
      registry, throughput, historicalMedians,
    })
    expect(plan.estimated_seconds).toBe(165)  // 45 + 120
  })
  ```

- [ ] **Step 3: Add `historicalMedians` param to `resolveBuildPlan()`**

  In `plan.ts`, update `ResolveBuildPlanArgs`:
  ```typescript
  interface ResolveBuildPlanArgs {
    scope: BuildScope
    scope_target: string | null
    action: BuildAction
    registry: RegistryEntry[]
    throughput: Map<AssetId, ThroughputEntry>
    historicalMedians?: Map<AssetId, number>   // NEW: per-asset median elapsed seconds
  }
  ```

  In `resolveBuildPlan()`, locate the existing `estimated_seconds` computation (which uses a for-loop pattern to sum per-asset `estimated_seconds` from the registry). **Match the existing style** — do NOT use `Array.reduce` (it cannot short-circuit on null). Replace/extend the existing loop to prefer historical median over registry value:

  ```typescript
  // Prefer historical median over static registry estimate. Abort (return null)
  // if ANY plan asset has no source — a partial sum would be misleading.
  let estimated_seconds: number | null = 0
  for (const id of sorted) {   // 'sorted' is the topo-sorted plan array
    const reg = regMap.get(id)
    const hist = historicalMedians?.get(id) ?? null
    const perAsset = hist ?? reg?.estimated_seconds ?? null
    if (perAsset === null) { estimated_seconds = null; break }
    estimated_seconds += perAsset
  }
  ```

  This mirrors the existing loop structure in `plan.ts` (lines ~222–230) and correctly returns `null` — rather than a partial sum — when any asset lacks an estimate.

- [ ] **Step 4: Run unit test**

  ```bash
  cd platform
  npx tsc --noEmit && npx vitest run src/lib/build/__tests__/plan.test.ts
  ```
  Expected: PASSED.

- [ ] **Step 5: Add historical median query to plan/route.ts**

  ```typescript
  const [registryResult, throughputResult, historyResult] = await Promise.all([
    query<RegistryEntry>(
      `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on, estimated_seconds
       FROM asset_registry WHERE has_writer = true ORDER BY layer, sort_order`
    ),
    query<ThroughputEntry>(
      `SELECT DISTINCT ON (asset_id) asset_id, state
         FROM asset_throughput
        WHERE chart_id=$1 OR chart_id IS NULL
        ORDER BY asset_id, (chart_id = $1) DESC NULLS LAST`,
      [chart_id]
    ),
    query<{ asset_id: string; median_sec: number }>(
      // Median elapsed seconds per asset across all successful runs, all charts.
      // Uses PERCENTILE_CONT(0.5) — PostgreSQL built-in, no extension needed.
      `SELECT asset_id,
              PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY EXTRACT(EPOCH FROM (ended_at - started_at))
              )::int AS median_sec
         FROM build_run_assets
        WHERE state = 'complete'
          AND started_at IS NOT NULL
          AND ended_at IS NOT NULL
        GROUP BY asset_id`
    ),
  ])

  const throughput = new Map(throughputResult.rows.map(r => [r.asset_id, r]))
  const historicalMedians = new Map(historyResult.rows.map(r => [r.asset_id, r.median_sec]))
  const plan = resolveBuildPlan({
    scope, scope_target, action,
    registry: registryResult.rows,
    throughput,
    historicalMedians,
  })
  ```

- [ ] **Step 6: Verify in browser**

  After at least one successful Bodha build, open the Build Plan dialog for Bodha. Confirm "estimated ~Xm" shows a real number instead of "unknown".

  On first run (no history yet), it still shows "unknown" — this is correct behavior; the next build populates the history.

- [ ] **Step 7: Commit**

  ```bash
  git add platform/src/app/api/cockpit/plan/route.ts \
           platform/src/lib/build/plan.ts \
           platform/src/lib/build/__tests__/plan.test.ts
  git commit -m "feat(cockpit/plan): estimated build time from historical build_run_assets medians"
  ```

---

## Task 8 — F13: Show DRAFT/CURRENT badge in Build Plan dialog

**Context:** The Build Plan dialog lists all assets in the plan but shows no indication of which are DRAFT (experimental, not yet promoted). DRAFT assets include: `bo_chart_gestalt`, `bo_cdlm_summary`, `bo_cgm_motifs`, `bo_cgm_paths`. These should show a small "DRAFT" badge so the operator knows they're running experimental writers.

**Files:**
- Modify: `platform/src/lib/components/cockpit/v2/PlanModal.tsx`

- [ ] **Step 1: Read PlanModal.tsx to find the plan list render site**

  Read `PlanModal.tsx` lines 169–230. Find where `planData.plan` (array of asset IDs) is rendered as a list. Note how asset IDs are displayed (just the ID string, or enriched with names from an `assets` prop).

- [ ] **Step 2: Add `catalog_status` to the `AssetNode` interface**

  In `PlanModal.tsx` (lines 17–22), extend `AssetNode`:
  ```typescript
  interface AssetNode {
    asset_id: string
    sanskrit_name: string
    english_name: string
    depends_on?: string[] | null
    catalog_status?: 'CURRENT' | 'DRAFT' | 'RETIRED' | null   // NEW
  }
  ```

- [ ] **Step 3: Render a DRAFT badge in the plan list**

  In the plan list render, after each asset's name, add:
  ```tsx
  {(() => {
    const node = assets?.find(a => a.asset_id === assetId)
    if (node?.catalog_status === 'DRAFT') {
      return (
        <span style={{
          fontSize: '8px',
          fontFamily: 'var(--mono-stack)',
          color: 'rgba(236,197,106,0.7)',
          border: '1px solid rgba(236,197,106,0.3)',
          borderRadius: '2px',
          padding: '0px 3px',
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          flexShrink: 0,
        }}>
          DRAFT
        </span>
      )
    }
    return null
  })()}
  ```

- [ ] **Step 4: Ensure the parent passes `catalog_status` in the `assets` prop**

  Search for where `PlanModal` is rendered in `CockpitShell.tsx`:
  ```bash
  grep -n "PlanModal" platform/src/lib/components/cockpit/v2/CockpitShell.tsx
  ```
  Confirm the `assets` prop is populated from the registry fetch (which includes `catalog_status`). If not, add `catalog_status` to whatever type is used for the registry response and pass it through.

- [ ] **Step 5: Verify in browser**

  Open the Bodha Build Plan dialog. Confirm:
  - `bo_chart_gestalt`, `bo_cdlm_summary`, `bo_cgm_motifs`, `bo_cgm_paths` show a gold "DRAFT" badge.
  - Other assets show no badge.

- [ ] **Step 6: Commit**

  ```bash
  git add platform/src/lib/components/cockpit/v2/PlanModal.tsx
  git commit -m "feat(cockpit/plan): show DRAFT badge on experimental assets in build plan dialog"
  ```

---

## Task 9 — F7: Verify font preload warnings resolved

**Context:** 61 identical `e4af272ccee01ff0-s.p.woff2` preload warnings fired during a 5-minute build session. Root layout already has `preload: false` for both fonts (per obs 31044 — committed in the previous session). This task verifies the fix holds and documents the investigation.

**Files:**
- Read: `platform/src/app/layout.tsx` (already confirmed `preload: false` for both fonts)

- [ ] **Step 1: Confirm `preload: false` is present for both fonts**

  Read `layout.tsx` lines 16–36. Confirm:
  ```typescript
  const cormorant = Cormorant_Garamond({
    ...
    preload: false,   // must be present
  })
  const jetbrainsMono = JetBrains_Mono({
    ...
    preload: false,   // must be present
  })
  ```
  If missing for either font, add it.

- [ ] **Step 2: Verify in browser during a build**

  Open Chrome DevTools → Console, filter by `preload`. Trigger a Bodha build. Observe for 2 minutes. Confirm:
  - 0 woff2 preload warnings during the build (SSE ticks should not cause font preload re-emission).
  - If warnings still appear: open the Network tab, filter by "Font", identify the request origin. Look for component remounts via React DevTools (components re-mounting re-trigger font injection). Check if any component uses `key={...}` with changing values that causes full remount.

- [ ] **Step 3: Commit (only if layout.tsx was changed)**

  ```bash
  git add platform/src/app/layout.tsx
  git commit -m "fix(layout): disable font preload for Cormorant + JetBrains Mono to suppress SSE-tick warnings"
  ```

---

## Task 10 — F9: Document bo_samvada DAG position as by-design

**Context:** bo_samvada appears at position 10 in the build plan (after bo_pramana_mapa). This seems late but is architecturally correct: bo_samvada is a DDL VIEW writer that creates `vw_chart_digest` — an aggregating VIEW over all `bodha_*` tables. It MUST run after all data tables are populated, hence after the full wave completes.

**Files:**
- Modify: `platform/python-sidecar/pipeline/orchestrator/writers/bo_samvada.py`

- [ ] **Step 1: Read the writer and confirm the dependency reason**

  Read `bo_samvada.py` lines 1–40. Confirm:
  - Writer creates a VIEW (DDL, not INSERT).
  - The VIEW's `SELECT` spans multiple `bodha_*` tables (laksana, bimba, karanajala, msr, samskara, etc.).
  - `depends_on` in asset_registry includes all data assets it aggregates.

- [ ] **Step 2: Add a docstring note**

  At the top of `bo_samvada.py`, enhance the module docstring:
  ```python
  """
  bo_samvada — Chart Digest View (L2 Bodha)
  ==========================================
  DDL writer: creates or replaces VIEW `vw_chart_digest` aggregating all bodha_*
  data tables into a single queryable surface.

  POSITION NOTE: bo_samvada is intentionally the LAST bodha asset in execution order.
  It is a VIEW definition (DDL, not INSERT) that spans all bodha_* tables. It must
  execute only after all upstream data tables are fully populated for the chart.
  This is by design — position 10 (or last) in the build plan is correct.
  rows_written = 1 (the VIEW itself counts as 1 object created).
  """
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add platform/python-sidecar/pipeline/orchestrator/writers/bo_samvada.py
  git commit -m "docs(bo_samvada): document late DAG position as by-design (VIEW writer over all bodha_* tables)"
  ```

---

## Task 11 — F10: Document bo_cdlm_summary 5-row design floor

**Context:** bo_cdlm_summary writes to `bodha_cdlm_chart_summary` — one row per chart × ayanamsha combination. With 5 canonical ayanamshas (lahiri_chitrapaksha, raman, krishnamurti, surya_siddhanta_classical, true_chitra), the expected floor is exactly 5 rows. This is correct and expected.

**Files:**
- Modify: `platform/python-sidecar/pipeline/orchestrator/writers/bo_cdlm_summary.py`

- [ ] **Step 1: Read the writer and confirm the 5-row logic**

  Read `bo_cdlm_summary.py`. Confirm:
  - Writer iterates over `CANONICAL_AYAS` (5 ayanamshas).
  - Each iteration inserts/upserts 1 row into `bodha_cdlm_chart_summary`.
  - Total = 5 rows per chart.

- [ ] **Step 2: Confirm `target_floor` in asset_registry seed**

  ```bash
  grep -A5 "bo_cdlm_summary" platform/scripts/seed/asset_registry_seed.ts
  ```
  Confirm `target_floor: 5` is set. If it's set to a different value or null, update:
  ```typescript
  target_floor: 5,  // 1 row per canonical ayanamsha (5 total)
  ```

- [ ] **Step 3: Add a docstring note to the writer**

  ```python
  """
  FLOOR NOTE: Exactly 5 rows per chart (1 per canonical ayanamsha). This is by design.
  target_floor = 5 in asset_registry.
  """
  ```

- [ ] **Step 4: Commit**

  ```bash
  git add platform/python-sidecar/pipeline/orchestrator/writers/bo_cdlm_summary.py \
           platform/scripts/seed/asset_registry_seed.ts
  git commit -m "docs(bo_cdlm_summary): document 5-row floor as by-design (1 per ayanamsha)"
  ```

---

## Task 12 — F11: Document bo_sangati 100-row sparsity

**Context:** bo_sangati writes to `bodha_cdlm_cells` (domain-pair linkages, A ≤ B unique pairs) and `bodha_convergence`. 100 rows for the canonical chart is the computed intersection count for that specific chart's MSR signals. Sparsity is expected — not all domain pairs co-occur in every chart.

**Files:**
- Modify: `platform/python-sidecar/pipeline/orchestrator/writers/bo_sangati.py`

- [ ] **Step 1: Read the writer and confirm the 100-row origin**

  Read `bo_sangati.py`. Confirm:
  - Writer reads `bodha_msr_signals` (MSR signals for the chart).
  - Computes domain-pair co-occurrences for A ≤ B (upper triangle only, no double-counting).
  - For this chart, 100 pairs emerge from the signal intersection — this is a data characteristic, not a bug.

- [ ] **Step 2: Add docstring note**

  ```python
  """
  SPARSITY NOTE: Row count varies per chart (depends on how many domain pairs co-occur
  in that chart's MSR signals). 100 rows for chart 482012f1-... is expected and correct.
  Sparse charts with few cross-domain signals will produce fewer rows. This is by design.
  """
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add platform/python-sidecar/pipeline/orchestrator/writers/bo_sangati.py
  git commit -m "docs(bo_sangati): document variable row count as chart-dependent (not a sparsity bug)"
  ```

---

## Task 13 — F14: Update L2 handoff doc with bo_drishti + bo_anveshana

**Context:** `L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md` documents the 8-asset Bodha DAG from the original spec. The production build has 14 `bo_*` assets including `bo_drishti` (Question Lenses) and `bo_anveshana` (Discovery Engine) which are not in the handoff doc.

**Files:**
- Modify: `00_ARCHITECTURE/L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md`

- [ ] **Step 1: Read the current DAG section of the handoff doc**

  ```bash
  grep -n "bo_\|DAG\|asset" 00_ARCHITECTURE/L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md | head -60
  ```
  Find the section describing the 8-asset DAG. Note the current asset list and the "8-asset" claim.

- [ ] **Step 2: Query the actual asset list from the registry**

  ```bash
  psql "$DATABASE_URL" -c "
    SELECT asset_id, sort_order, catalog_status, depends_on
    FROM asset_registry
    WHERE layer = 'bodha'
    ORDER BY sort_order
  "
  ```
  Record the complete 14-asset list with dependencies.

- [ ] **Step 3: Update the handoff doc's DAG section**

  Update the asset count claim from "8-asset Bodha DAG" to the actual count. Add entries for `bo_drishti` and `bo_anveshana` with their positions in the DAG and their declared dependencies.

  Format to add (in the appropriate table or list):
  ```markdown
  | bo_drishti    | Question Lenses        | DRAFT   | [dependencies] | [position] |
  | bo_anveshana  | Discovery Engine       | DRAFT   | [dependencies] | [position] |
  ```

  Update the version and changelog in the frontmatter:
  ```yaml
  version: 1.1
  status: CURRENT
  ```
  Add to changelog:
  ```markdown
  ## v1.1 (2026-06-29)
  - §2 DAG section updated: 14-asset list replaces 8-asset original spec;
    added bo_drishti (Question Lenses) and bo_anveshana (Discovery Engine)
    with confirmed positions and dependencies from production registry.
  ```

- [ ] **Step 4: Update the artifact registry to reflect the version bump**

  Per `CLAUDE.md §B.8` (versioning discipline) and `ONGOING_HYGIENE_POLICIES_v1_0.md`, every canonical artifact version change must be reflected in `CAPABILITY_MANIFEST.json`. Failure to do so causes `drift_detector.py` to flag a disagreement between the file's frontmatter (`v1.1`) and the registry (`v1.0`).

  In `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`, find the entry for `L2_BODHA_CAMPAIGN_HANDOFF` and update its `version` field from `"1.0"` to `"1.1"`.

  If `CANONICAL_ARTIFACTS_v1_0.md` also lists the version (it may, as a SUPERSEDED snapshot), update the table row there too.

- [ ] **Step 5: Commit**

  ```bash
  git add 00_ARCHITECTURE/L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md \
           00_ARCHITECTURE/CAPABILITY_MANIFEST.json \
           00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
  git commit -m "docs(L2-handoff): update DAG section to 14-asset production list (add bo_drishti + bo_anveshana)"
  ```

---

## Phase 2 Tasks — CGM Writer Data Bugs

### Task 14 — B1: Fix bo_bimba graha position mapping (PRIMARY DATA FIX)

**Root cause:** `_fetch_graha_positions()` (bo_bimba.py:109,132) uses `subject.title()` to convert L1 fact_subject codes to KNOWN_GRAHAS names. This accidentally works for `SUN`→`Sun` and `MOON`→`Moon` (4-letter codes that title-case to the full name), but fails for all others: `MAR`→`Mar` (not `Mars`), `MER`→`Mer` (not `Mercury`), `JUP`→`Jup` (not `Jupiter`), `VEN`→`Ven` (not `Venus`), `SAT`→`Sat` (not `Saturn`), `RAH_MEAN`→`Rah_Mean` (not `Rahu`), `KET_MEAN`→`Ket_Mean` (not `Ketu`). Result: 7/9 graha nodes get `position_in_chart_jsonb=null` in bodha_cgm_nodes after every bo_bimba build.

**Downstream effect:**
- `bo_cgm_motifs` stellium detector: `node.get("position_in_chart_jsonb")` returns null for 7/9 grahas → nodes skipped → 0 stellia detected
- `bo_cgm_paths` self-ruling detector: `_is_self_ruling(subject, pos)` returns False when pos=None → 0 self-ruling chains emitted → 0 rows

**Verified in DB:** `SELECT COUNT(*), COUNT(position_in_chart_jsonb), node_type FROM bodha_cgm_nodes WHERE chart_id='482...' GROUP BY node_type` → `graha: 45 total, 10 with_position` (only Sun+Moon across 5 ayanamshas have positions; 7 grahas × 5 ayanamshas = 35 missing).

**Files:**
- Modify: `platform/python-sidecar/pipeline/orchestrator/writers/bo_bimba.py`

- [ ] **Step 1: Add `_SUBJECT_TO_GRAHA` mapping dict at module level**

  After the `KNOWN_GRAHAS` list (around line 40), add:
  ```python
  # L1 fact_subject codes → KNOWN_GRAHAS canonical names.
  # subject.title() only works for SUN→Sun and MOON→Moon; all others are abbreviated
  # (MAR, MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN) and title-case to wrong values.
  _SUBJECT_TO_GRAHA: dict[str, str] = {
      "SUN":      "Sun",
      "MOON":     "Moon",
      "MAR":      "Mars",
      "MER":      "Mercury",
      "JUP":      "Jupiter",
      "VEN":      "Venus",
      "SAT":      "Saturn",
      "RAH_MEAN": "Rahu",
      "KET_MEAN": "Ketu",
  }
  ```

- [ ] **Step 2: Replace `subject.title()` with `_SUBJECT_TO_GRAHA` lookup in both loops**

  In `_fetch_graha_positions()` (lines ~82–142), there are TWO places that do `graha = subject.title()`:
  - Line 109 (sign rows loop): `graha = subject.title()`
  - Line 132 (house rows loop): `graha = subject.title()`

  Replace both with:
  ```python
  graha = _SUBJECT_TO_GRAHA.get(subject.upper(), subject.title())
  ```

  This exact change is needed at both lines. The `.get(..., subject.title())` fallback handles any future fact_subject that isn't in the mapping.

- [ ] **Step 3: Write the failing test**

  In `platform/python-sidecar/tests/l2/` (or wherever bo_bimba tests live — check with `ls platform/python-sidecar/tests/l2/`), add a test function. If no test file exists for bo_bimba, add to a new file `tests/l2/test_bo_bimba_position_mapping.py`:

  ```python
  import pytest
  from pipeline.orchestrator.writers.bo_bimba import _SUBJECT_TO_GRAHA, KNOWN_GRAHAS

  def test_all_known_grahas_have_mapping():
      """Every KNOWN_GRAHA must be reachable via the fact_subject mapping."""
      mapped_values = set(_SUBJECT_TO_GRAHA.values())
      for graha in KNOWN_GRAHAS:
          assert graha in mapped_values, (
              f"KNOWN_GRAHA '{graha}' has no entry in _SUBJECT_TO_GRAHA — "
              f"it will never get position_in_chart_jsonb populated"
          )

  def test_subject_to_graha_mapping_is_correct():
      """Spot-check that abbreviated codes map to full English names."""
      assert _SUBJECT_TO_GRAHA["MAR"] == "Mars"
      assert _SUBJECT_TO_GRAHA["MER"] == "Mercury"
      assert _SUBJECT_TO_GRAHA["JUP"] == "Jupiter"
      assert _SUBJECT_TO_GRAHA["VEN"] == "Venus"
      assert _SUBJECT_TO_GRAHA["SAT"] == "Saturn"
      assert _SUBJECT_TO_GRAHA["RAH_MEAN"] == "Rahu"
      assert _SUBJECT_TO_GRAHA["KET_MEAN"] == "Ketu"
      assert _SUBJECT_TO_GRAHA["SUN"] == "Sun"
      assert _SUBJECT_TO_GRAHA["MOON"] == "Moon"

  def test_title_case_fallback_does_not_produce_wrong_values():
      """Demonstrate the old bug: subject.title() was wrong for abbreviated codes."""
      assert "MAR".title() != "Mars"    # was producing "Mar"
      assert "MER".title() != "Mercury" # was producing "Mer"
      assert "JUP".title() != "Jupiter" # was producing "Jup"
  ```

- [ ] **Step 4: Run test to confirm it passes**

  ```bash
  cd platform/python-sidecar
  python -m pytest tests/l2/test_bo_bimba_position_mapping.py -v
  ```
  Expected: all 3 tests PASS.

- [ ] **Step 5: Run full Python test suite**

  ```bash
  cd platform/python-sidecar
  python -m pytest tests/ -v --tb=short
  ```
  Expected: all tests pass (change is backward-compatible; fallback `subject.title()` preserves old behavior for unknown subjects).

- [ ] **Step 6: Commit**

  ```bash
  git add platform/python-sidecar/pipeline/orchestrator/writers/bo_bimba.py \
           platform/python-sidecar/tests/l2/test_bo_bimba_position_mapping.py
  git commit -m "fix(bo_bimba): _fetch_graha_positions uses _SUBJECT_TO_GRAHA lookup instead of subject.title() — restores position_in_chart_jsonb for 7/9 grahas"
  ```

---

### Task 15 — B2: Fix asset_runner to write `dormant` state when writer produces 0 rows

**Root cause:** `asset_runner.py` lines 466–476 unconditionally write `state='lit'` to `asset_throughput` after any successful (no-exception) writer run, regardless of `rows_written`. When bo_cgm_motifs and bo_cgm_paths complete without error but produce 0 rows, they get `state='lit'`. The plan resolver's `action:'build'` filter is `!t || t.state === 'dormant' || t.state === 'error'` — it excludes `lit` assets. So clicking Build opens an empty plan → confirm button disabled → user is stuck.

**Fix:** When `rows_written == 0` and the asset is chart-scoped (not a global service singleton), write `dormant` instead of `lit`. This makes `action:'build'` correctly re-include the asset in future plan resolutions.

**Files:**
- Modify: `platform/python-sidecar/pipeline/orchestrator/asset_runner.py`

- [ ] **Step 1: Read the current state-write block**

  Read `asset_runner.py` lines 459–505. Confirm line 472:
  ```python
  cur.execute(
      """UPDATE asset_throughput
         SET state = 'lit', last_built_at = NOW(), rows_written = %s, ...
         WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id = %s""",
      (rows_written, upstream_hash, writer_hash, chart_id, asset_id),
  )
  ```
  Also confirm line 486: `emit_event({..., "to_state": "lit"})`.

- [ ] **Step 2: Write the failing test**

  In `platform/python-sidecar/tests/` (find the relevant test file for asset_runner, or add to `test_fix_plan_proofs.py`):

  ```python
  def test_zero_row_writer_produces_dormant_not_lit(monkeypatch, pg_conn):
      """
      A writer that returns rows_inserted=0 must write state='dormant' to
      asset_throughput, not 'lit'. Otherwise action='build' excludes the asset
      from the plan (plan resolver only picks dormant/error/missing state).
      """
      # This is an integration test — requires a live DB connection.
      # If the test harness uses mocks, adapt accordingly.
      # The key assertion: after running a writer that returns 0 rows,
      # asset_throughput.state should be 'dormant', not 'lit'.
      # Verify by reading asset_throughput after the writer call.
      pass  # implement using the project's existing test infrastructure
  ```

  Note: look at existing tests in `test_fix_plan_proofs.py` or similar to understand the test harness conventions before implementing the full test.

- [ ] **Step 3: Add `final_state` computation before the UPDATE**

  In `asset_runner.py`, at line 466 (after `rows_written = int(...)`), add:

  ```python
  # When a chart-scoped data writer produces 0 rows, record 'dormant' rather than
  # 'lit'. 'lit' would cause the plan resolver's action='build' filter to exclude
  # the asset (filter picks only dormant/error/missing), leaving the Build button
  # stuck with an empty plan. 'dormant' correctly signals "ran but produced nothing
  # — safe to retry". Global assets (chart_id is None) are service singletons and
  # always get 'lit' regardless of rows_written.
  final_state = 'lit'
  if rows_written == 0 and chart_id is not None:
      final_state = 'dormant'
  ```

- [ ] **Step 4: Replace `'lit'` literal with `final_state` in the UPDATE and emit_event**

  At line 472, change:
  ```python
  # BEFORE:
  SET state = 'lit', last_built_at = NOW(), rows_written = %s,
  ```
  to:
  ```python
  # AFTER (use %s parameter for the state):
  SET state = %s, last_built_at = NOW(), rows_written = %s,
  ```

  And update the parameter tuple to prepend `final_state`:
  ```python
  # BEFORE:
  (rows_written, upstream_hash, writer_hash, chart_id, asset_id),
  # AFTER:
  (final_state, rows_written, upstream_hash, writer_hash, chart_id, asset_id),
  ```

  Also update the SSE emit at line 486:
  ```python
  # BEFORE:
  emit_event({..., "to_state": "lit"})
  # AFTER:
  emit_event({..., "to_state": final_state})
  ```

- [ ] **Step 5: Run Python test suite**

  ```bash
  cd platform/python-sidecar
  python -m pytest tests/ -v --tb=short
  ```
  Expected: all existing tests pass.

- [ ] **Step 6: Commit**

  ```bash
  git add platform/python-sidecar/pipeline/orchestrator/asset_runner.py
  git commit -m "fix(asset_runner): write state='dormant' when chart-scoped writer returns 0 rows — prevents Plan API empty-plan bug"
  ```

---

### Task 16 — B3: Migration to correct current asset_throughput state for CGM assets

**Context:** Before Task 15's fix, bo_cgm_motifs and bo_cgm_paths were marked `lit` in `asset_throughput` after producing 0 rows. The fix in Task 15 prevents future occurrences, but the current DB state is wrong — both assets currently show `state='lit'` despite having 0 rows. This migration resets them to `dormant` so that `action:'build'` works immediately after deploying Tasks 14–15.

**Verified:** `SELECT asset_id, state FROM asset_throughput WHERE chart_id='482012f1...' AND asset_id IN ('bo_cgm_motifs','bo_cgm_paths')` → both show `state='lit'`.

**Files:**
- Create: `platform/supabase/migrations/374_cgm_throughput_state_correction.sql`

- [ ] **Step 1: Check the next available migration number**

  ```bash
  ls platform/supabase/migrations/ | grep -v "^_" | sort | tail -5
  ```
  The last migration is `373_throughput_orphan_cleanup.sql`. Use `374`.

- [ ] **Step 2: Write the migration**

  Create `platform/supabase/migrations/374_cgm_throughput_state_correction.sql`:

  ```sql
  -- Migration 374: correct asset_throughput state for CGM assets
  -- bo_cgm_motifs and bo_cgm_paths completed with 0 rows but were marked 'lit'
  -- (pre-Task-15 bug: asset_runner wrote 'lit' unconditionally).
  -- Reset to 'dormant' so action='build' correctly picks them up for rebuild.
  -- Scoped to rows with 0 actual rows (rows_written=0) to avoid touching charts
  -- where these assets legitimately produced rows in a future correct build.
  UPDATE asset_throughput
  SET state = 'dormant'
  WHERE asset_id IN ('bo_cgm_motifs', 'bo_cgm_paths')
    AND state = 'lit'
    AND (rows_written = 0 OR rows_written IS NULL)
    AND chart_id IS NOT NULL;
  ```

- [ ] **Step 3: Apply the migration via the project's migration runner**

  ```bash
  # Use the project's standard migration approach (check platform/package.json scripts
  # or platform/scripts/ for the migrate command):
  cd platform
  npx supabase db push  # or equivalent
  ```

  Verify:
  ```bash
  # After migration, confirm state changed:
  # SELECT asset_id, state, rows_written FROM asset_throughput
  # WHERE asset_id IN ('bo_cgm_motifs', 'bo_cgm_paths') AND chart_id IS NOT NULL;
  # Expected: state = 'dormant' for all rows with rows_written = 0
  ```

- [ ] **Step 4: Run migration guard review**

  Before committing, invoke the `migration-guard` agent to review `374_cgm_throughput_state_correction.sql` for safety.

- [ ] **Step 5: Commit**

  ```bash
  git add platform/supabase/migrations/374_cgm_throughput_state_correction.sql
  git commit -m "fix(migration 374): reset bo_cgm_motifs/bo_cgm_paths asset_throughput state lit→dormant for 0-row builds"
  ```

---

### Task 17 — B4: Migration to set target_table for CGM assets

**Context:** `asset_registry.target_table` is NULL for both bo_cgm_motifs and bo_cgm_paths. The stats route and other tooling use `target_table` to derive the table for row-count checks. While `count_sql` is set (and works), a null `target_table` is an incomplete registry entry that `drift_detector.py` may flag.

**Verified:** `SELECT asset_id, target_table FROM asset_registry WHERE asset_id IN ('bo_cgm_motifs','bo_cgm_paths')` → both `target_table = null`.

**Files:**
- Create: `platform/supabase/migrations/375_cgm_target_table.sql`

- [ ] **Step 1: Write the migration**

  Create `platform/supabase/migrations/375_cgm_target_table.sql`:

  ```sql
  -- Migration 375: set target_table for bo_cgm_motifs and bo_cgm_paths
  -- Both assets had target_table=null from initial registration.
  -- The DB tables (bodha_cgm_motifs, bodha_cgm_paths) were created in migration 226.
  UPDATE asset_registry
  SET target_table = 'bodha_cgm_motifs'
  WHERE asset_id = 'bo_cgm_motifs';

  UPDATE asset_registry
  SET target_table = 'bodha_cgm_paths'
  WHERE asset_id = 'bo_cgm_paths';
  ```

- [ ] **Step 2: Apply the migration**

  ```bash
  cd platform
  npx supabase db push  # or equivalent migration runner
  ```

  Verify:
  ```bash
  # SELECT asset_id, target_table FROM asset_registry
  # WHERE asset_id IN ('bo_cgm_motifs','bo_cgm_paths');
  # Expected: target_table = 'bodha_cgm_motifs' and 'bodha_cgm_paths'
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add platform/supabase/migrations/375_cgm_target_table.sql
  git commit -m "fix(migration 375): set target_table for bo_cgm_motifs and bo_cgm_paths in asset_registry"
  ```

---

### Task 18 — B5: Fix CascadePreviewModal empty-plan UX

**Root cause:** When `plan.length === 0`, `CascadePreviewModal.tsx` lines 235–239 show:
```tsx
<div>No assets in plan.</div>
```
The confirm button is disabled (`confirmDisabled = isLoading || plan.length === 0`). The user sees a disabled button with no explanation — no recovery path is offered. After Tasks 14–16 this situation should not arise for CGM assets, but it can still happen for edge cases (e.g. a user clicking Build on an asset that is already `lit` with actual rows — `action:'build'` correctly excludes it).

**Files:**
- Modify: `platform/src/components/cockpit/CascadePreviewModal.tsx`

- [ ] **Step 1: Read the current empty state render**

  Read `CascadePreviewModal.tsx` lines 220–255. Find the empty state block (currently around lines 235–239):
  ```tsx
  if (plan.length === 0) {
    <div>No assets in plan.</div>
  }
  ```
  Also confirm line 91: `const confirmDisabled = isLoading || plan.length === 0`
  And lines 275–292: the confirm button's disabled styling.

- [ ] **Step 2: Replace empty state with informative guidance**

  Replace the empty state `<div>No assets in plan.</div>` with:
  ```tsx
  <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px', lineHeight: 1.5 }}>
    <div style={{ marginBottom: '6px' }}>No assets require building.</div>
    <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)' }}>
      This asset is already built and up-to-date. Use <strong>Rebuild</strong> to
      force-rerun it (right-click or trigger from the layer panel).
    </div>
  </div>
  ```

  Note: the text says "Rebuild" but there is no separate rebuild button in the current UI — after Tasks 14–16, this empty-plan case should only appear for genuinely-lit assets. The message is informational.

- [ ] **Step 3: Add tooltip to disabled confirm button**

  Wrap the confirm button with a `title` attribute when disabled:
  ```tsx
  <button
    disabled={confirmDisabled}
    title={confirmDisabled && !isLoading ? 'No assets in plan — nothing to build' : undefined}
    ...
  >
    Confirm
  </button>
  ```

- [ ] **Step 4: Verify in browser**

  Call `POST /api/cockpit/plan` with `action:'build'` on a lit asset (e.g. bo_bimba which has rows). Confirm the modal shows the new "No assets require building" message and the disabled button has the tooltip.

- [ ] **Step 5: Commit**

  ```bash
  git add platform/src/components/cockpit/CascadePreviewModal.tsx
  git commit -m "fix(cockpit): CascadePreviewModal shows actionable guidance when plan is empty"
  ```

---

## Execution Order

**Phase 2 FIRST (Tasks 14–18 — data bugs unblock the build):**

1. **Task 14** (B1 — bo_bimba position mapping) — ROOT CAUSE for 0 rows; fix this first so rebuilt CGM writers produce real data
2. **Task 15** (B2 — asset_runner dormant state) — prevents recurrence of lit-but-0-rows state; fix before next global build
3. **Task 16** (B3 — throughput state correction migration) — one-time data fix; apply immediately after Task 15 so Build button works today
4. **Task 17** (B4 — target_table migration) — registry completeness; quick, apply alongside 16
5. **Task 18** (B5 — modal UX) — UI polish; low-risk, independent

**Phase 1 SECOND (Tasks 3–13 — scheduler/UI issues; Tasks 1–2 already committed):**

6. **Task 3** (F4 — Stop button fix) — independent, quick
7. **Task 4** (F3 — error display verify) — requires Task 1 to be testable E2E
8. **Task 9** (F7 — font preload verify) — quick verification
9. **Tasks 10, 11, 12** (F9, F10, F11 — docstrings) — fast, parallel
10. **Task 5** (F6 — accordion investigate) — investigation-heavy
11. **Task 6** (F8 — sort order verify) — requires DB query
12. **Task 7** (F12 — estimated time) — TypeScript + SQL change
13. **Task 8** (F13 — DRAFT badge) — UI polish
14. **Task 13** (F14 — handoff doc) — documentation

---

## Acceptance Criteria

**Phase 2 (CGM writer data bugs):**
- [ ] After rebuild of bo_bimba: `SELECT COUNT(*), COUNT(position_in_chart_jsonb) FROM bodha_cgm_nodes WHERE chart_id='482012f1...' AND node_type='graha'` → `45 total, 45 with_position` (was 45/10).
- [ ] After rebuild of bo_cgm_paths: table has > 0 rows (at minimum: Jupiter in Sagittarius → 5 self-ruling chains, 1 per ayanamsha).
- [ ] After rebuild of bo_cgm_motifs: stellium detection fires for any house with 3+ grahas (if present in chart; otherwise 0 rows is expected and documented).
- [ ] `asset_throughput.state` for a 0-row chart-scoped writer is `dormant` (not `lit`) after the fix.
- [ ] Clicking "Build" on a dormant CGM asset opens the CascadePreviewModal with plan `["bo_cgm_motifs"]` (or `["bo_cgm_paths"]`) and an enabled Confirm button.
- [ ] `asset_registry.target_table` is `bodha_cgm_motifs` / `bodha_cgm_paths` for both assets.
- [ ] CascadePreviewModal shows informative guidance (not "No assets in plan.") when plan is empty.

**Phase 1 (scheduler/UI issues; Tasks 1–2 already committed):**
- [ ] A Bodha layer build that previously stalled indefinitely now terminates within `ORCHESTRATOR_ASSET_TIMEOUT_SEC` (default 300s) with the hanging asset marked error (red in UI) and downstream assets marked "blocked by upstream failure" (amber).
- [ ] The Stop button appears only on assets whose `asset_throughput.state = 'building'` during an active run — not on completed assets.
- [ ] Error state (state='error') shows a red status dot and truncated error text in the asset row.
- [ ] Zero font preload warnings in the browser console during a 5-minute build session.
- [ ] Build Plan dialog shows "estimated ~Xm" after at least one successful build (historical medians).
- [ ] DRAFT assets show a gold "DRAFT" badge in the Build Plan dialog.
- [ ] `L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md` lists all 14 `bo_*` assets with correct positions and dependencies.
- [ ] All Python tests pass: `pytest platform/python-sidecar/tests/ -v`.
- [ ] TypeScript compiles clean: `npx tsc --noEmit` in `platform/`.
