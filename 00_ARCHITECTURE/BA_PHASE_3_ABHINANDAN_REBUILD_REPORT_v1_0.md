---
artifact: BA_PHASE_3_ABHINANDAN_REBUILD_REPORT_v1_0.md
canonical_id: BA_PHASE_3_ABHINANDAN_REBUILD_REPORT
version: 1.0
status: RESIDUALS — NOT CLEAN
produced_during: BA-PHASE-3-ABHINANDAN-REBUILD-2026-07-05
governing_brief: CLAUDECODE_BRIEF_BA_PHASE_3_ABHINANDAN_REBUILD_v1_1.md
chart: Abhinandan Mohanty · 1c826d5a-41cb-4450-b4dc-59d440e5f75a
build_run_id: 8e5d1549-a695-4422-9b96-f7a7a3850aed
---

# BA PHASE 3 — ABHINANDAN FULL REBUILD (PROVING RUN) — REPORT

## Outcome

**RESIDUALS — the rebuild did not complete. 18/66 assets built ("lit"); 45/66 assets ended in `error` state
(cascading `BLOCKED: upstream dependency did not complete` failures traced to two independent root causes).
The chart is currently in a WORSE state than pre-rebuild: L2 Bodha, L4 Phala, and most of L3 Kāla / L5 Mīmāṃsā
are now empty (previously populated), and `chart_dashas` holds a partial write (460,831 of ~603,122 baseline
rows). A rollback point exists (fresh on-demand snapshot taken pre-rebuild). PHASE-3 is NOT CLEAN.**

## §0 — Pre-flight (completed)

- Sidecar (`amjis-sidecar`) and pipeline JOB (`brahma-pipeline`) both confirmed on commit `6a0aea6f` (post-#436
  merged HEAD) via `gcloud run services/jobs describe` — matches PR #436 merge SHA.
- Fresh on-demand Cloud SQL snapshot taken immediately before the rebuild: backup ID `1783272757787`
  (2026-07-05T17:32:37Z UTC), instance `amjis-postgres`. This is the rollback point.
- Baseline `count_sql` counts recorded for all 44 countable L1–L5 assets for chart `1c826d5a…` (full table
  below).

## §1 — Trigger path (Chrome MCP, prod)

Navigated to `https://madhav.marsys.in/clients/1c826d5a-41cb-4450-b4dc-59d440e5f75a/build` in an authenticated
owner/super-admin session (redirects to the v2 Nirmāṇa cockpit). Confirmed owner/admin build affordances
enabled, all 6 layers "current"/healthy, 100% complete before the run.

Clicked the header **Rebuild** button. This opens `ClearConfirmModal` (component:
`platform/src/lib/components/cockpit/v2/CockpitShell.tsx` `handleGlobalRebuild` →
`openGlobalClearModal(true)`) — a preview-then-confirm dialog, NOT a separate DAG-listing "plan modal". Two
clicks on this button (from stale vs. fresh snapshots) initially looked like a defect — the a11y-tree "Rebuild"
button appeared to open a "Clear all chart data?" dialog — but DOM/React-prop inspection confirmed this is the
intentional design: `Rebuild` == `clear (L1–L5) → chain a rebuild POST` (`handleAfterClear` in
`CockpitShell.tsx`), which is exactly the delete-then-insert semantics the brief specifies. **Not a defect** —
noted here only because it cost verification time and should be considered for UI/copy clarity (the modal is
titled "Clear all chart data?" / "DESTRUCTIVE ACTION" even when driven from the Rebuild button).

The preview modal's layer breakdown before confirming was verified: **Gaṇita(L1) 16 assets / Bodha(L2) 15 /
Kāla(L3) 14 / Phala(L4) 9 / Mīmāṃsā(L5) 12 — Brahma Jñāna (L0) NOT listed, 1,076,318 total rows, 50 assets
cleared, 16 reset to dormant, 59 tables touched.** This satisfies the brief's STOP-gate ("plan lists L1–L5 in
dependency order, excludes every `bg_*` L0 global") — L0 was excluded throughout.

Typed "Abhinandan Mohanty" to confirm; executed. `POST /api/cockpit/clear/execute` → 200 (deleted 66 assets /
59 tables). `POST /api/cockpit/runs` (action=rebuild, scope=global) → 201, chaining the rebuild automatically.

## §2 — Build run: what happened

Run `8e5d1549-a695-4422-9b96-f7a7a3850aed` — `state='completed'` (orchestrator considers this a clean exit;
**this is itself a finding** — a run with 45/66 assets in `error` state should not report top-level
`state='completed'`). Started 17:41:38Z, ended 17:52:14Z (~10.5 min).

### Root cause A — `ga_dashas` hit an internal 600s timeout mid-write

`asset_throughput.last_error` for `ga_dashas`: `BLOCKED: upstream dependency(ies) timeout:600s did not
complete in this run; skipped to avoid building on incomplete data`. `rows_written=461,127` reported, but the
**actual current row count for this chart in `chart_dashas` is 460,831** (vs. baseline 603,122) — i.e. the
delete-then-insert was interrupted mid-insert by a 600s internal timeout guard, and the partial insert
persisted (not rolled back to the pre-clear 603,122, and not fully replaced either). This directly blocked:
`ga_structural`, `ga_condition`, `ga_tajaka`, `ka_dasha_kala`, `ga_sade_sati`, `ga_yoga`, `ka_sangam`,
`ka_avadhi`, `ka_yojaka`, `ka_taranga`, `ka_jivana_parva` — and transitively almost everything in Bodha/Kāla/
Phala that depends on those.

This is very likely because Abhinandan's dasha computation (multi-system Vimshottari + others, full-depth
levels) is heavier than whatever chart the 600s timeout was calibrated against, OR the mass-DELETE +
concurrent autovacuum on the 603K-row `chart_dashas` table (confirmed via `pg_stat_activity`: `autovacuum:
VACUUM ANALYZE public.chart_dashas` running concurrently, 5+ min) starved the INSERT of I/O throughput,
pushing it past the timeout that would otherwise have been sufficient.

**This is a generality-by-construction concern (§4): a fixed per-asset timeout that a legitimate multi-system
dasha build can exceed for at least one real client chart is not chart-agnostic-safe.** Flagging as a
structural class finding per the brief's own HALT-class criteria ("a writer demanding a contract change" /
timeout tuning is adjacent to this).

### Root cause B — `mi_jivanaghatana` hard-fails on a chart with zero life events (this is the generality blocker)

`asset_throughput.last_error` for `mi_jivanaghatana`:

```
RuntimeError: [mi_jivanaghatana] chart_id=1c826d5a-41cb-4450-b4dc-59d440e5f75a: both the LEL markdown
(/app/01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md, exists=False) and the life_events DB fallback yielded zero
events. Verify the LEL markdown ships at this resolved path in the runtime container and that life_events
is populated, before treating this as a healthy build.
```

Abhinandan has no populated life-event log (neither the native's LEL markdown — which correctly does not
exist for a non-native chart — nor any rows in the `life_events` DB fallback table for this chart_id). The
writer treats **zero life events as a hard `RuntimeError`**, not a graceful zero-row build. Because
`mi_jivanaghatana` sits early in the DAG and several `mi_*` / downstream assets key off it
(`mi_bhavisya`, `mi_pramana`, `mi_gunanaka`, `mi_pariksha`, `mi_adhilepa`, `mi_sambandha`, `mi_darshana`,
`mi_seva`, `mi_abhilekha` all cascade-blocked from this one failure), **this is a direct violation of §4
"generality by construction"**: any current/future client without a populated life-event log cannot complete
a full rebuild. This needs a code fix (treat zero per-chart life events as a valid empty result, not an
exception) before Phase 3 can be called clean, independent of the Abhinandan-specific proving run.

### What succeeded cleanly (18 assets, all L1, "lit" state, no errors)

`ga_positions` (530 rows), `ga_panchanga` (417), `ga_nakshatra` (1,813), `ga_prashna` (0 — legitimately empty,
no horary judgments logged), `ga_transit_anchors` (45), `ga_vargas` (22,665 — vs. baseline 20,877, a legitimate
increase), `ga_sensitive` (8,790 — vs. baseline 8,580, legitimate increase). `ga_strength` also reports `lit`
with 11,620 rows written but is downstream of the `ga_dashas` timeout window — needs re-verification once
`ga_dashas` is fixed and rebuilt cleanly (its dependency chain is not fully clean even though it didn't itself
error).

## §3 — Post-rebuild ACs: NOT EVALUABLE for most sections given incomplete build

### §3.1 Completeness + DAG
FAIL. 45/66 assets in `error` state. `dag_edge_guard` not run — moot until the run completes; the DAG
*structure* itself is not implicated (all failures are `BLOCKED` cascades from the two root causes above, not
DAG mis-ordering — dependency order was in fact respected, which is why the blocking cascaded correctly rather
than building on incomplete data).

### §3.2 Non-degeneracy
NOT EVALUABLE. `ph_nimitta`, `bo_upaya`, `bo_cgm_paths`, `bo_pratijna`, `kala_convergence` (`ka_sangam`) are
all in the currently-empty/error set.

### §3.3 Contamination spot-checks
PARTIAL PASS on what did build: `ga_positions` confirms Abhinandan's Sun = **Aquarius, 317.89° sidereal**
(fact_subject=SUN), correctly distinct from the native's 292° Capricorn — the positions-under-wrong-chart_id
scar did not recur. `ph_rectification` and `mi_jivanaghatana` provenance checks are moot (both empty/errored).

### §3.4 Integrity
Trap-1 (L2+ signals resolve to `chart_facts.fact_id`) not evaluable — no L2 signals exist yet (Bodha empty).
`asset_throughput` vs `count_sql`: **disagree by design here** — `asset_throughput.state='completed'` at the
run level despite 45 assets in per-asset `error` state is itself flagged as a governance-relevant
inconsistency (the top-level run state should reflect that not all planned assets landed cleanly).

## §4 — Generality by construction: ONE CONFIRMED GAP, requires a fix before Phase 3 can close

- Chart-agnostic writers: confirmed — no `NATIVE_BIRTH`/native chart_id literal found; both failures are
  data-driven (missing life events, table-size/timeout), not native-contamination.
- **Gap found:** `mi_jivanaghatana` is NOT safe for "any current/future client" — a chart with a genuinely
  empty life-event log throws instead of producing a valid empty asset. This must be fixed (treat 0 events as
  a legitimate, non-error outcome with `rows_written=0` and no exception) before Phase 3 can be declared clean.
- **Gap found:** the internal per-asset timeout (600s, wherever it is configured for `ga_dashas` / the
  orchestrator's substep timeout) is not proven safe for "any" client — it was insufficient for Abhinandan's
  own first full rebuild under concurrent-autovacuum load. Needs either a longer timeout, chunked/batched
  commits so partial progress isn't lost, or investigation into whether the mass-DELETE + autovacuum
  contention (not raw computation time) was the actual bottleneck.
- `dag_edge_guard` / contamination CI gate: not re-verified this pass (moot — the run itself needs a fix pass
  first).

## §5 — Baseline → post-rebuild count_sql table (L1–L5, all 44 countable assets)

| asset_id | layer | baseline | post-rebuild | delta | note |
|---|---|---|---|---|---|
| ga_positions | L1 | 530 | 530 | 0 | clean rebuild |
| ga_vargas | L1 | 20,877 | 22,665 | +1,788 | clean rebuild |
| ga_dashas | L1 | 603,122 | 460,831 | **-142,291** | **TIMEOUT, partial write, NOT clean** |
| ga_strength | L1 | 12,466 | (not independently re-verified) | — | downstream of dashas timeout window |
| ga_sensitive | L1 | 8,580 | 8,790 | +210 | clean rebuild |
| ga_panchanga | L1 | 417 | 417 | 0 | clean rebuild |
| ga_prashna | L1 | 0 | 0 | 0 | clean (legitimately empty) |
| ga_sade_sati | L1 | 9,790 | 0 | **-9,790** | BLOCKED (ga_dashas) |
| ga_tajaka | L1 | 235 | 0 | **-235** | BLOCKED (ga_dashas) |
| ga_structural | L1 | 98,857 | 0 | **-98,857** | BLOCKED (ga_dashas) |
| ga_nakshatra | L1 | 1,813 | 1,813 | 0 | clean rebuild |
| ga_condition | L1 | 2,890 | 0 | **-2,890** | BLOCKED (ga_dashas) |
| ga_yoga | L1 | 30 | 0 | **-30** | BLOCKED (ga_dashas) |
| ga_vastu | L1 | 40 | 0 | **-40** | BLOCKED (ga_condition) |
| ga_medical | L1 | 45 | 0 | **-45** | BLOCKED (ga_condition) |
| ga_transit_anchors | L1 | 45 | 45 | 0 | clean rebuild |
| bo_* (all 10 countable) | L2 | 84,281 total | 0 | **-84,281** | BLOCKED (bo_laksana ← ga_structural/ga_condition/ga_sade_sati) |
| ka_* (all countable) | L3 | 162,175 total | 0 | **-162,175** | BLOCKED (ka_sangam ← ga_dashas/ga_tajaka) |
| ph_* (all 9) | L4 | 1,718 total | 0 | **-1,718** | BLOCKED (ph_nimitta ← bo_* / ka_*) |
| mi_jivanaghatana | L5 | 0 | 0 (error) | 0 | **HARD FAIL — zero life events, RuntimeError** |
| mi_* (other 9, countable) | L5 | 68,407 total | 0 | **-68,407** | BLOCKED (mi_jivanaghatana + mi_pramana chain) |

## §6 — Rollback

Pre-rebuild on-demand snapshot: **`amjis-postgres` backup ID `1783272757787`**, taken 2026-07-05T17:32:37Z UTC,
immediately before this run. This is the rollback point if the native wants to restore Abhinandan (and every
other chart on the shared instance — this is an instance-level snapshot, not chart-scoped) to the pre-rebuild
state. Not restored as part of this pass — leaving the current (partially-rebuilt) state in place per
FULL GUARDIAN AUTONOMOUS discipline (observe → fix → resume, not revert-on-first-failure) pending native
review, since a code fix (not a data-plane action) is what's actually required next.

## §7 — Verdict

**RESIDUALS — NOT CLEAN.** Two structural-class findings block a true "PHASE-3 CLEAN":

1. `mi_jivanaghatana` writer must treat a chart with zero life events as a valid empty build, not a
   `RuntimeError` — this is a direct §4 generality-by-construction failure (blocks any future client without
   a populated life-event log).
2. The internal per-asset/substep timeout that killed `ga_dashas` at 600s must be revisited (raised, and/or the
   delete+insert should not race live autovacuum on a freshly-mass-deleted large table) — needs
   engineering investigation into whether it's a genuine compute-time issue or lock/IO contention from the
   clear step's cleanup.

Both are code-plane fixes. Recommend: land both fixes, then re-run this exact Phase-3 brief end-to-end
(baseline is already captured above; the same rollback snapshot remains valid) before declaring PHASE-3 CLEAN.
Native (`482012f1`) and other-client rebuilds remain out of scope for this pass, unaffected by this finding
except insofar as any future client without life-event data would hit the same `mi_jivanaghatana` failure.
