---
artifact: BUILD_TRACKER_HARDENING_MASTER_v1_0.md
canonical_id: BUILD_TRACKER_HARDENING_MASTER
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
supersedes_context: BUILD_TRACKER_HARDENING_HANDOFF_v1_0.md (handoff → execution plan)
purpose: >
  Master sequencing brief for making the Nirmāṇa build tracker + orchestrator fully operational,
  robust, and accurate across Refresh, Delete/Clear, Build, and Rebuild — for both native and
  non-native charts. Grounded in a direct code audit of the live paths (2026-06-25, main e52b75cf).
  Cowork authored; Claude Code (Antigravity) executes. Each operation has its own paste brief.
audience: Claude Code (Antigravity) + native (Abhisek)
---

# Build Tracker Hardening — Master Sequencing Brief

## §0 — Why this brief exists
The handoff (`BUILD_TRACKER_HARDENING_HANDOFF_v1_0.md`) framed the mission. This brief grounds it in a
**direct read of the live code** and turns it into an ordered, executable plan. Four companion paste
briefs do the per-operation work:

1. `BUILD_TRACKER_REFRESH_BRIEF_v1_0.md` — make the tracker show DB truth (stale-display class).
2. `BUILD_TRACKER_CLEAR_BRIEF_v1_0.md` — prove delete completeness + no over-delete (resumes the
   in-flight verification).
3. `BUILD_TRACKER_BUILD_BRIEF_v1_0.md` — layer build UI→orchestrator→all assets to completion.
4. `BUILD_TRACKER_REBUILD_BRIEF_v1_0.md` — force re-run of lit assets, per-asset delete-then-insert.

## §1 — Audit-confirmed live paths (use these, not the handoff's older names)
- **Build trigger is `POST /api/cockpit/runs`** (`platform/src/app/api/cockpit/runs/route.ts`).
  `/api/build/start` is **DECOMMISSIONED (returns HTTP 410)** — do not wire anything to it.
- **Plan builder:** `platform/src/lib/build/plan.ts` `resolveBuildPlan` — reads
  `asset_registry.depends_on` (the authoritative DAG), topo-sorts, filters candidates per action.
- **Job invoker:** `platform/src/lib/build/jobInvoker.ts` `invokeRunJob(runId)` → Cloud Run Job
  `brahma-build-pipeline-job` (asia-south1), arg `--run-id`.
- **Orchestrator:** `platform/python-sidecar/pipeline/orchestrator/runner.py` `execute_run`.
- **Stats / Refresh:** `platform/src/app/api/cockpit/stats/route.ts`.
- **Clear preview / execute:** `platform/src/app/api/cockpit/clear/route.ts` +
  `clear/execute/route.ts`; spec in `platform/src/lib/cockpit/assetClearSpec.ts`.

## §2 — The four audit findings that drive the work (read before sequencing)

**F1 — Stale display is STRUCTURAL, not cosmetic (highest leverage).**
`stats/route.ts` `fetchAllCounts` uses `asset_throughput.rows_written` as the **primary** count and
only falls back to live `count_sql` when `rows_written IS NULL`. The clear route sets
`state='dormant'` but **never nulls `rows_written`**. Net effect: after a clear, the stats route keeps
returning the pre-clear count, and `deriveState` (rows>0 ⇒ `lit`) reports the asset as still built.
**The tracker lies after every clear and every partial build.** Fix is small and central — own it in
the Refresh brief (clear nulls rows_written) with a defensive stats-route guard.

**F2 — Clear DELETE derivation fails closed on *shape*, not *breadth*.**
`deriveDeleteSqlFromCountSql` regex-rewrites `SELECT count(*) … FROM …` → `DELETE FROM …`. It returns
null (fail-closed) only when the SELECT/FROM prefix doesn't match — i.e. on non-simple shapes
(JOINs, subquery sums). A *simple but semantically broad* count_sql (e.g. one missing its
`fact_category` predicate) would derive a broad DELETE that over-deletes shared-table rows. The
in-flight UI verification on `1c826d5a` is the correct arbiter; the Clear brief consumes its result.

**F3 — `build_runs.state='completed'` means "plan walked", not "all healthy".**
`runner.py` sets `completed` unconditionally after the plan loop (line ~170). Per-asset errors are
only surfaced by the error-count badge. The Build brief must assert: a run with any errored asset is
NEVER shown as fully green, and the layer header reflects error count.

**F4 — Two DAG sources still diverge.** `plan.ts` reads `asset_registry.depends_on`; the cascade
preview reads the `build_dependencies` table. Plan correctness rides on `depends_on`. Reconciliation
is a governance task (§5) — flag, don't silently "fix" mid-hardening.

## §3 — Execution order (safest blast radius first)
Do them in this order; each gates the next. **All destructive steps run ONLY on non-native
`1c826d5a` (Abhinandan Mohanty). NEVER on native `482012f1`.**

| # | Op | Brief | Gate to advance |
|---|-----|-------|-----------------|
| 0 | Commit the pending modal-portal fix (§4) | this brief | typecheck + build green, committed |
| 1 | **Refresh** | REFRESH_BRIEF | tracker count == DB count for a cleared + a built asset |
| 2 | **Clear** | CLEAR_BRIEF | BEFORE/AFTER DB proof: full delete, zero over-delete, zero failed_tables |
| 3 | **Build** | BUILD_BRIEF | layer build lights every in-scope asset; errored asset never reads green |
| 4 | **Rebuild** | REBUILD_BRIEF | rebuild of lit assets re-runs + delete-then-inserts; counts stable, no accretion |

## §4 — STEP 0: commit the pending modal-portal fix (do this first, it's already verified live)
Four files are modified-but-uncommitted in the dev tree (verified hot-reloaded live per handoff §4):
`platform/src/lib/components/cockpit/v2/ClearConfirmModal.tsx`,
`platform/src/lib/components/cockpit/v2/PlanModal.tsx`,
`platform/src/components/cockpit/CascadePreviewModal.tsx`,
`platform/src/components/cockpit/NodeDetailModal.tsx`
(they add `createPortal`/`useEffect`; CascadePreview also caps at 90vh with internal scroll).

PASTE TO CLAUDE CODE:
```
Confirm the working tree on main has exactly these 4 modified files (git status):
  platform/src/lib/components/cockpit/v2/ClearConfirmModal.tsx
  platform/src/lib/components/cockpit/v2/PlanModal.tsx
  platform/src/components/cockpit/CascadePreviewModal.tsx
  platform/src/components/cockpit/NodeDetailModal.tsx
Run `cd platform && npm run typecheck && npm run build`. If both pass, commit ONLY those 4 files with:
  fix(cockpit): portal modals to body + cap cascade height (dialogs no longer clipped by constellation panel)
Do NOT commit any other working-tree changes (the 3 staged .md briefs stay untracked for now). Report
the commit SHA and the typecheck/build result. If typecheck or build fails, STOP and paste the error.
```

## §5 — Loose ends inherited from handoff §4 (track, schedule — do NOT fold into hardening)
- **PyJHora FORENSIC 7/7 re-validation** — engine live (#332), anchors unproven. Brief staged:
  `L1_PYJHORA_REVALIDATION_REBUILD_BRIEF_v1_0.md`. Schedule AFTER tracker hardening so the rebuild
  used to re-validate runs on a tracker you trust.
- **GATE P0 registry query** — confirm on prod which `ga_*` assets are `layer='L1' AND is_active=true`
  and that `ga_transit_anchors` is correctly excluded (service-not-storage) before any full L1 build
  is trusted. Run as the first read-only step of the Build brief.
- **Two-DAG reconciliation** (F4) — `asset_registry.depends_on` vs `build_dependencies`. Governance
  task; matters before L2/L3/L4 build buttons are trusted. Flagged, not in scope here.

## §6 — Operating rules (unchanged, restated for the executor)
- Cowork plans/authors; Claude Code executes. Output pasteable prompts or committed .md.
- Destructive verification ONLY on `1c826d5a`. NEVER on native `482012f1`.
- Data plane = prod via Cloud SQL proxy `:5433`. No local Postgres. Localhost only triggers+displays.
- Every main merge auto-deploys the web app; the Cloud Run JOB image is a SEPARATE build — confirm
  `job_image_tag` in the runs response before trusting a run's orchestrator code.
- Chrome is read-tier → use the Claude-in-Chrome MCP for clicks.
- Truth bar: tracker display == DB reality; full success or an explicit failure list — never silent
  partial success.
- FROZEN orchestrator contract — harden via conforming writers/routes; a needed contract change is
  STOP-and-raise.
