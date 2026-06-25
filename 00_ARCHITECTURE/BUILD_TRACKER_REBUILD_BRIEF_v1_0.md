---
artifact: BUILD_TRACKER_REBUILD_BRIEF_v1_0.md
canonical_id: BUILD_TRACKER_REBUILD_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
parent: BUILD_TRACKER_HARDENING_MASTER_v1_0.md
purpose: Prove Rebuild force-re-runs already-lit assets via per-asset delete-then-insert, with stable counts (no accretion) and correct downstream-stale propagation.
audience: Claude Code (Antigravity)
---

# Rebuild Hardening — "re-run lit assets cleanly; counts don't drift"

## §0 — The path (audited)
`resolveBuildPlan` with `action='rebuild'`: asset-scope → target + full transitive downstream;
layer/global → all in-scope assets. `runner.py` bypasses skip-if-lit because the guard is
`if action != "rebuild" and is_asset_complete(...)`. Each writer does its own per-chart
**delete-then-insert** scoped to `(chart_id × natural key)` (§N.3 idempotency standard, FROZEN
contract). So rebuild correctness rides on (a) the route forcing the re-run and (b) each writer
replacing rather than accreting.

## §1 — What this brief must prove
- Rebuild of a LIT asset actually re-executes the writer (not skipped).
- The row count after rebuild EQUALS the count before (delete-then-insert; no doubling/accretion).
- asset_throughput.rows_written + last_built_at refresh; state stays/returns 'lit'.
- Downstream assets are marked 'stale' by the rebuild seed and (on a layer rebuild) re-run in order.
- The tracker reflects all of the above truthfully (REFRESH fix must hold).

## §2 — End-to-end rebuild proof (on 1c826d5a ONLY)
PASTE TO CLAUDE CODE (run after BUILD brief is PASS so the layer is freshly lit):
```
Prove Rebuild on Abhinandan Mohanty 1c826d5a-41cb-4450-b4dc-59d440e5f75a (SAFE non-native). NEVER
native 482012f1. Chrome read-tier → mcp__Claude_in_Chrome__*. DB via :5433 is the arbiter. Confirm
job_image_tag is current before trusting orchestrator behavior.

A — ASSET-scope rebuild (accretion guard):
  Pick a lit ga_ asset with a stable deterministic row count (e.g. ga_dashas→chart_dashas).
  PRE DB: SELECT count(*) FROM chart_dashas WHERE chart_id='1c826d5a-...';  → record N.
  PRE throughput: state, rows_written, last_built_at for that asset.
  Press the ASSET Rebuild control in the UI. Capture the runs response: plan MUST include the target
  (proving skip-if-lit was bypassed) plus its transitive downstream.
  Watch to completion. POST DB: count == N EXACTLY (delete-then-insert; NOT 2N, NOT N+delta).
  POST throughput: last_built_at advanced, rows_written == N, state='lit'.
  ACCEPTANCE: count unchanged at N. Any drift (2N or partial) = a writer accretion/idempotency bug →
  name the asset + its writer module and STOP.

B — DOWNSTREAM-stale propagation:
  Confirm the rebuild seed marked the target's transitive downstream 'stale' (asset_throughput.state)
  and, if you ran a LAYER rebuild, that those downstream assets re-ran in DAG order and returned 'lit'.

C — TRACKER truth: after rebuild, the tracker count for the rebuilt asset == DB count, and
  last-built timestamp updated. (Relies on the REFRESH fix — if the tracker shows a stale count here,
  that's an F1 regression, report it distinctly from any rebuild issue.)

Deliver: PRE/POST DB counts (proving N==N), the runs response plan (proving bypass), the throughput
before/after, the downstream-stale list, and a PASS/FAIL. STOP and report.
```

## §3 — Likely hardening edits (apply only if §2 surfaces them)
- If a rebuild DOUBLES rows → the writer isn't doing per-chart delete-then-insert per §N.3. Fix the
  writer to mirror `ga_writers/_idempotency.py` (delete `(chart_id × natural key)` then insert).
  This is a writer fix conforming to the FROZEN contract, NOT an orchestrator change.
- If rebuild SKIPS the target (treated as lit) → the `action != "rebuild"` guard isn't reached;
  inspect that the route passed `action='rebuild'` all the way into the build_runs row and that
  runner.py read it. (Audit shows the code is correct; verify the data path.)
- If downstream didn't go stale → check the rebuild seed feeds `computeDownstreamClosure`.

## §4 — Done when
Asset and layer rebuilds re-run lit assets, counts are stable (delete-then-insert, no accretion),
downstream goes stale and re-runs in order, and the tracker shows the refreshed truth. Then the four
operations (Refresh, Clear, Build, Rebuild) are each DB-proven on 1c826d5a — the acceptance bar from
the master brief is met.
