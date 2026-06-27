---
artifact: BUILD_TRACKER_HARDENING_HANDOFF_v1_0.md
canonical_id: BUILD_TRACKER_HARDENING_HANDOFF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
purpose: >
  Self-contained context handoff to a NEW Cowork conversation whose mission is to make the Nirmāṇa
  build tracker + orchestrator FULLY OPERATIONAL, ROBUST, and RELIABLE for BOTH native and
  non-native charts — across Refresh, Build, Rebuild, and Delete/Clear. Carries the in-flight
  verification prompt (under process) so the new session resumes without re-deriving anything.
audience: Claude (Cowork) — new conversation
---

# Build Tracker Hardening — Context Handoff

## §0 — Mission of the new conversation
Make the **Nirmāṇa build tracker** and the **orchestrator** behind it fully operational, robust, and
reliable, for **both the native chart and non-native charts**, across all four operations. Suggested
order to harden + prove each (start with the safest, lowest-blast-radius first):
1. **Refresh** (read-only-ish; re-reads counts/state) — prove it shows TRUTH, fast.
2. **Delete / Clear** (asset / layer / global scope) — prove it deletes completely, no silent skips,
   no over-delete across shared tables.
3. **Build** (layer-scope from the web page → orchestrator → all assets in DAG order to completion).
4. **Rebuild** (force re-run of already-lit assets; delete-then-insert per asset).

The acceptance bar for every operation: **what the tracker shows must equal what the database
contains** (no stale-display lies), and **every operation either fully succeeds or reports exactly
what failed** (no silent partial success).

## §1 — The system, in one screen
- **Product split:** Cowork PLANS + AUTHORS prompts/briefs. **Claude Code in Antigravity EXECUTES.**
  Every Cowork output is a pasteable prompt or a committed .md — never chat bullets the user
  hand-translates.
- **Press-Build path (end to end):** Nirmāṇa UI (`platform/src/components/cockpit/*` +
  `platform/src/lib/components/cockpit/v2/*`) → `/api/build/start` (builds a `build_run` row:
  scope/scope_target/plan JSONB) → `platform/src/lib/build/jobInvoker.ts` launches **Cloud Run Job
  `brahma-build-pipeline-job`** (asia-south1) with `--run-id` → `pipeline/orchestrator/runner.py`
  walks the plan, calls `run_asset()` per asset (FROZEN contract). **The orchestrator runs IN THE
  CLOUD JOB, not localhost.** Localhost only triggers + displays.
- **Display truth:** `asset_throughput` (state / rows_written) ← read by `/api/cockpit/stats` ←
  rendered as tracker progress. Stale asset_throughput = the tracker lies even when data is fine.
- **Charts:**
  - Native = **Abhisek Mohanty** `482012f1-710e-4a25-994a-93821f5871aa` — the FORENSIC-anchored
    foundation chart. NEVER run destructive verification on it.
  - Non-native test = **Abhinandan Mohanty** `1c826d5a-41cb-4450-b4dc-59d440e5f75a` — SAFE for
    destructive tests (no downstream native citations). All clear/rebuild verification runs here.
- **Data plane is ALWAYS prod** via Cloud SQL proxy **:5433**. No local Postgres. Every merge to
  `main` AUTO-DEPLOYS the web app; the Cloud Run JOB image is a SEPARATE build (a stale job image
  silently runs old orchestrator code — `job_image_tag` is surfaced in the start response, fix B2).
- **L1 data model (critical):** most L1 (ga_) assets write into the SHARED `chart_facts` table,
  partitioned by `fact_category` (e.g. `panchanga_*`, `graha_avastha_%_per_varga`). A few own
  dedicated tables: `ga_dashas`→chart_dashas, `ga_vargas`→chart_divisionals,
  `ga_condition`→ga_condition_composite + chart_facts avastha rows. chart_facts / chart_divisionals
  are SHARED ACROSS LAYERS (L0 + others), so any clear/delete MUST be category-scoped or it
  over-deletes another layer's rows.

## §2 — What's already been done (durable, on main)
- **PyJHora engine swap merged** (#332): `natal_engine` retired, `pyjhora_adapter` live. The
  FORENSIC 7/7 re-validation on a fresh native rebuild is **DEFERRED / OPEN** — engine is in prod
  but not yet proven to reproduce the birth anchors. (Memory: project-pyjhora-engine-validation-deferred.)
- **Merge train COMPLETE**: 12 PRs + campaign fixes landed; repo pruned to `main` only.
- **Layer-build reliability pass (commit 0d79f13b)**: 6 failure modes fixed (plan completeness via
  `asset_registry WHERE layer=$1 AND is_active=true`; error-count badge so a layer with an errored
  asset never reads "done" green; rebuild action bypasses skip-if-lit; dead SSE endpoint removed;
  job_image_tag surfaced; SSE overlay clears on run.state_change completed). KNOWN LIMITATIONS:
  (a) TWO DAG sources still exist — `asset_registry.depends_on` (plan builder, authoritative) vs
  `build_dependencies` table (cascade preview, cosmetic) — reconciliation is a pending governance
  task; (b) `build_runs.state='completed'` means "plan walked", not "all healthy" (the badge
  surfaces errors); (c) watchdog 15-min stuck-asset can false-positive on very long sub-steps
  (Python overwrites on completion).
- **Cockpit modal clipping FIXED (uncommitted in dev tree — see §4):** all 4 cockpit modals
  (ClearConfirmModal, PlanModal, CascadePreviewModal, NodeDetailModal) now render via React portal
  to document.body (escapes the constellation SVG's stacking context); CascadePreviewModal also
  capped at 90vh with internal scroll so its long plan list doesn't push buttons off-screen.
- **Layer-clear partial-delete FIXED (commits c239d61d, 7ac8f3c0):** root cause was a TABLE-centric
  clear over a fact_category-partitioned shared-table model — assets with NULL target_table were
  silently skipped, and chart_facts assets over-/under-cleared. Fix:
  `platform/src/lib/cockpit/assetClearSpec.ts` — `deriveDeleteSqlFromCountSql()` makes **count_sql
  the single source of truth** for both counting and deleting (regex SELECT count(*)…→DELETE…,
  fails CLOSED returning null on any non-simple shape); `EXPLICIT_CLEAR_OPS` overrides for
  ga_pyjhora_engine (null=clean skip) and ga_condition (two atomic ops). `clear/execute/route.ts`
  now: no silent skips (unresolved asset → failed_tables), per-ASSET savepoint (atomic multi-op),
  resolution order = explicit → derived-from-count_sql → target_table fallback → fail.

## §3 — Verification IN FLIGHT (the prompt under process — paste its RESULT into the new convo)
The CURRENT open task is an END-TO-END Chrome-MCP verification of the layer-clear fix, driven through
the UI as a real user, with DB before/after as the arbiter, on the SAFE chart 1c826d5a. The exact
prompt handed to Claude Code is reproduced verbatim below. **The user will paste the RESULT of this
prompt into the new conversation** — the new session should read that result first, treat any
under-delete / over-delete / UI-vs-DB divergence it found as the immediate next work item, then
proceed to harden Refresh → Build → Rebuild per §0.

--- BEGIN IN-FLIGHT PROMPT (verbatim) ---
Verify the layer-clear partial-delete fix (commits c239d61d, 7ac8f3c0) END-TO-END through the
cockpit UI in Chrome, driving it as a real user would, on chart Abhinandan Mohanty
1c826d5a-41cb-4450-b4dc-59d440e5f75a (non-native test chart — SAFE, no downstream native citations).
Do NOT touch native 482012f1. Use the Claude-in-Chrome MCP (mcp__Claude_in_Chrome__*) for all UI
actions — Chrome is read-tier so screen-clicking is blocked; the Chrome MCP is DOM-aware and is the
correct tool. Pair the visual clear with DB reads (Cloud SQL proxy :5433) for the row-truth, because
the cockpit count can be stale (asset_throughput) and must not be trusted as proof on its own.

PRE — confirm the dev server on localhost:3000 is serving the fix (commit 7ac8f3c0 or later). If not,
restart it. Confirm chart 1c826d5a is the target. Open a NEW Chrome MCP tab (tabs_create_mcp).

STEP 1 — BEFORE state (DB, read-only via :5433). Record:
  SELECT 'chart_facts' tbl, count(*) FROM chart_facts WHERE chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a'
  UNION ALL SELECT 'chart_dashas', count(*) FROM chart_dashas WHERE chart_id='1c826d5a-...'
  UNION ALL SELECT 'chart_divisionals', count(*) FROM chart_divisionals WHERE chart_id='1c826d5a-...'
  UNION ALL SELECT 'ga_condition_composite', count(*) FROM ga_condition_composite WHERE chart_id='1c826d5a-...';
  SELECT fact_category, count(*) FROM chart_facts WHERE chart_id='1c826d5a-...' GROUP BY 1 ORDER BY 2 DESC;
  Tag which fact_categories are L1/ga_ vs L0/other-layer (so STEP 4 checks the right targets and can
  prove no collateral over-delete of non-ga_ rows).

STEP 2 — Drive the clear through the UI (Chrome MCP), as a user:
  - navigate to http://localhost:3000/clients/1c826d5a-41cb-4450-b4dc-59d440e5f75a/nirmana
  - read_page / screenshot to locate the Gaṇita layer row; expand it if needed.
  - Click the Gaṇita LAYER clear control (the trash/clear icon at the LAYER level — scope='layer',
    scope_target='ganita'). This opens the ClearConfirmModal ("Clear all ganita assets?").
  - screenshot the dialog. CONFIRM it shows the expected scope (all ganita assets) and reads the
    full preview (tables, downstream-stale list). Verify the dialog is NOT clipped (the portal fix).
  - Click the confirm button ("Clear layer" / "Clear data"). (Layer-ganita is NOT L0, so no typed
    confirmation is required — if the UI unexpectedly demands it, screenshot and STOP.)
  - Wait for completion; screenshot the result + capture the network response of
    /api/cockpit/clear/execute (read_network_requests) — record cleared.assets / ops / rows and ANY
    failed_tables. Non-empty failed_tables = a real gap; report it, do not call it success.

STEP 3 — Observe the tracker post-clear (UI truth):
  screenshot the Gaṇita layer. Record what each asset row now shows (LIVE/row-count vs NOT BUILT /
  dormant) and the layer header total. Note: if rows still show counts, that may be stale
  asset_throughput, NOT undeleted data — STEP 4's DB read is the arbiter, not this screenshot.

STEP 4 — AFTER state (DB) + PROVE it. Re-run STEP 1's queries. ACCEPTANCE:
  - every L1/ga_ fact_category in chart_facts → 0 for this chart;
  - chart_dashas, chart_divisionals (ga_ portion), ga_condition_composite → 0 for this chart;
  - OVER-DELETE GUARD: every NON-ga_ (L0/other) fact_category is UNCHANGED vs BEFORE — a layer clear
    of L1 must not touch shared-table rows owned by other layers. Any drop here = broad-delete
    regression → HALT and report.
  - clear/execute response had zero failed_tables.
  Report BEFORE→AFTER side by side. Any L1 category still >0 = the under-delete this fix targets;
  name the asset + its derived DELETE. Any non-ga_ drop = over-delete; halt.

STEP 5 — Reconcile UI vs DB: if STEP 3 (tracker) and STEP 4 (DB) DISAGREE (e.g. tracker still shows
rows but DB is 0), that's the stale-display class (asset_throughput / stats route), a SEPARATE issue
from the clear — report it distinctly so it isn't confused with a clear failure.

CONSTRAINTS: all destructive action ONLY on 1c826d5a via the UI; never 482012f1. Chrome MCP for all
clicks (Chrome is read-tier). DB reads via :5433 for the row-truth. Deliver: the BEFORE/AFTER DB
table (the proof), the clear/execute response, the dialog + post-clear screenshots, and a clear
PASS/FAIL with any under-delete, over-delete, or UI-vs-DB-divergence called out. STOP and report.
--- END IN-FLIGHT PROMPT ---

## §4 — Open loose ends the new conversation inherits
1. **Modal-fix commit pending:** the 4-modal portal fix + CascadePreview height-cap are in the dev
   tree, hot-reloaded + verified live, but NOT yet committed. Files:
   `lib/components/cockpit/v2/ClearConfirmModal.tsx`, `lib/components/cockpit/v2/PlanModal.tsx`,
   `components/cockpit/CascadePreviewModal.tsx`, `components/cockpit/NodeDetailModal.tsx`. They add
   `createPortal`/`useEffect` imports across 4 files — run typecheck/build before committing.
   Suggested message: `fix(cockpit): portal modals to body + cap cascade height (dialogs no longer
   clipped by constellation panel)`.
2. **PyJHora FORENSIC 7/7 re-validation** still OPEN (engine live, anchors unproven). Briefs already
   staged: `L1_PYJHORA_REVALIDATION_REBUILD_BRIEF_v1_0.md` (validation companion) +
   `LAYER_BUILD_RELIABILITY_BRIEF_v1_0.md` (the press-Build-builds-the-layer reliability work).
3. **GATE P0 registry query** (the authoritative L1 manifest — which ga_ assets are
   `layer='L1' AND is_active=true`, and is `ga_transit_anchors` correctly excluded as service-not-
   storage) — still needs running on prod before a full L1 build is trusted.
4. **Two-DAG-source reconciliation** (asset_registry.depends_on vs build_dependencies) — pending
   governance task; matters before L2/L3/L4 build buttons are trusted.
5. **Stale asset_throughput display class** — partly fixed (Phase-0 hybrid fallback in stats route;
   the runner.py global-scope fix + migration-331 guard), but watch for it whenever UI count ≠ DB
   count; it's a SEPARATE bug from any clear/build failure and must not be conflated.
6. **Count-source unification — FIXED + EMPIRICALLY VERIFIED (2026-06-25).** The tracker showed THREE
   different totals for one layer (header 698,340 from asset_throughput.rows_written; delete preview
   561,875 from clear-spec-only 10/17 assets; live stats 0/dormant). Root cause: 3 readers, 3 sources.
   Gap reconciled exactly: 7 omitted assets (5 filtered for no target_table/count_sql:
   ga_strength/ga_sensitive/ga_sade_sati/ga_structural/ga_pyjhora_engine; 2 deduped-away on shared
   chart_facts: ga_panchanga/ga_nakshatra) = 139,061 − 2,596 staleness premium = 136,465 (=698,340−561,875).
   Fix (4 files): stats/route.ts now runs live count_sql for `scope==='per_chart'` (keeps rows_written
   shortcut for global bg_); clear/route.ts counts ALL assets via clear-spec resolution + aggregates by
   table + surfaces `not_clearable_assets` (no silent omission); ClearConfirmModal + ClearIconButton
   show the not-clearable line. VERIFIED on 1c826d5a: header==stats==DB at baseline/post-clear/post-
   rebuild (694,496 → 0 within one refresh → 683,975 live truth). NOTE: post-rebuild < baseline is
   CORRECT (live truth replacing inflated stale rows_written, not data loss). Commit the 4 files if
   not already on main.
7. **Two writer errors `ga_nakshatra` + `ga_sensitive` — FIXED + VERIFIED (2026-06-25).** Surfaced
   during the count-source verification rebuild on 1c826d5a (both errored, 0 rows). Root cause:
   dict_row-cursor + PyJHora-adapter-return shape mismatches (the engine swap touched what these
   writers receive). Fixes live on 1c826d5a: `_check_bg_nakshatra_present` dict_row guard,
   `_fetch_bg_nakshatra` fix, cross-ayanamsha cursor fix, ga_sensitive AK-divergence warning path.
   Both now `state=complete`, last_error=null, real rows (ga_nakshatra 1,813 across all 14 categories;
   ga_sensitive 1,050+ karaka categories). REGRESSION TESTS lock all three error shapes permanently
   (this was the 3rd break — the test is the durable fix). Commit if not already on main.
8. **L4 Phala upstream-completeness audit DONE; fixes STAGED BEHIND L2 (2026-06-25).** Audit
   (`L4_PHALA_UPSTREAM_COMPLETENESS_FIX_BRIEF_v1_0.md`): 6/9 ph_ assets SOUND; 2 NO + 1 borderline.
   KEY REFRAME: L4 thinness is largely L2 damage propagating downstream — 3 of 4 fixes are GATED ON L2.
   - DONE NOW (commit 6be29e10): ph_muhurta instrumented (LIMIT 100 = M3 design; WARN if >100 anchors).
   - ph_pramana: NOT a bug — `life_event_log` table doesn't exist (real table `life_events` = L5
     calibration corpus); SAVEPOINT is designed graceful degradation. Future-migration task: create
     `life_event_log` with domain vocab aligned to phala_anchors.domain (career/health/relationship/
     spiritual/transition). Not a code fix.
   - STAGED (commit d5456ead, `L4_PHALA_STAGED_FIX_SPECS_v1_0.md`, BLOCKED-ON-L2): (B.1) ph_sankrama —
     CONFIRMED vocab mismatch bodha_cdlm_cells.domain_row `spirituality`/`character` vs
     phala_anchors.domain `spiritual`/`transition` (= the 96.5% career skew); fix at L2 source (CDLM
     canonicalization), post-L2 gate SQL decides if ph_sankrama needs zero change or a thin shared-map
     patch. (B.2) ph_nimitta Axis 3 CGM paths — loader discards data (`return {}`); fix = chart-level
     top-20 path distribution (msr_signals has no graha_primary col). (B.3) ph_nimitta Axis 5 — real
     HNSW nearest-neighbor join (index bse_embedding_hnsw on vector(768) confirmed) replacing
     self-reference. APPLY §B as ONE L4 re-fix pass AFTER L2 CGM+embeddings+CDLM-vocab proven sound on
     1c826d5a — applying earlier wires correct code to degenerate data. ⇒ **L2 remediation is the
     unblock for L4 completeness; do L2 first.**

## §5 — Operating rules the new conversation must keep
- Cowork plans/authors; Claude Code executes. Output pasteable prompts or committed .md.
- Destructive verification ONLY on non-native `1c826d5a`. NEVER on native `482012f1`.
- Data plane = prod via :5433. Every main merge auto-deploys web; the Cloud Run JOB image is
  separate — confirm `job_image_tag` before trusting a build run's code.
- Chrome is read-tier → use Claude-in-Chrome MCP for clicks, not screen control.
- Truth bar for every tracker operation: tracker display == DB reality; full success or explicit
  failure list — never silent partial success.
- L0 (Brahmagyan) untouched by L1 work; the clear's L0 typed-confirmation guard stays.
- FROZEN orchestrator contract — harden via writers/routes that conform; a needed contract change
  is STOP-and-raise.
- Relevant memory: native-canonical-chart-id, project-pyjhora-engine-validation-deferred,
  feedback-cowork-vs-antigravity-split, feedback-localhost-codeplane-prod-dataplane,
  feedback-degenerate-distribution-guard.
```
