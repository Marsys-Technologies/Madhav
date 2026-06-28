---
status: COMPLETE
completed_on: 2026-06-28
completed_by: ABHINANDAN-REGEN-TRACKER-SHAKEDOWN-2026-06-28
---

# Abhinandan Regeneration + Full Nirmāṇa Build-Tracker Shakedown — Claude Code (Antigravity) Brief

> Paste this whole file into Claude Code in Antigravity. Drive the regeneration through the Nirmāṇa build tracker using **Chrome MCP**, and use the run as a complete shakedown of the tracker: correctness, UI, number reconciliation, refresh behavior, and performance (UI + data-generation speed). Read `CLAUDE.md` + `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` first. FROZEN orchestrator contract.

---

## 0 — Mission

Two intertwined goals, one run:

1. **Regenerate** Abhinandan Mohanty's chart (`1c826d5a-41cb-4450-b4dc-59d440e5f75a`) end-to-end (clear L1–L5 → global Rebuild), on the corrected post-remediation code, fixing any clear/build bug encountered.
2. **Shake down and ELEVATE the build tracker itself** — this is NOT only a data-correctness run. Treat it as the opportunity to find and fix tracker defects across **five axes**: (A) correctness, (B) UI/UX, (C) number reconciliation, (D) refresh/liveness behavior, (E) performance — both UI responsiveness and the **speed of data generation**. Fix what you find, commit/merge/deploy clean.

The deep "did-the-data-fixes-take" astrological/data correctness audit (salience stratification, domain population, contradictions, etc.) is a **SEPARATE later session** — do NOT do that deep data audit here. Here, "correctness" means the tracker tells the truth (numbers reconcile, states are accurate, no stale display), not re-auditing the generated astrology.

---

## 1 — INVIOLABLE PRINCIPLES

1. **NEVER touch Brahma Jñāna (L0 / `bg_*` / `layer='brahmagyan'`)** — not cleared, rebuilt, refreshed, by any path. Global Rebuild impacts **L1–L5 only**. **Before triggering rebuild, verify the global plan excludes L0** (`runs/route.ts:92-96` filters `layer !== 'brahmagyan'` at `scope='global'`; `plan.ts:167-178` never auto-pulls `bg_*`). If any `bg_*` appears in the global plan → STOP, fix so it cannot. After rebuild, spot-check `bg_*` counts unchanged.
2. **Scope: Abhinandan `1c826d5a` ONLY.** Never touch native `482012f1` or any other chart's DATA. **No native contamination** — after rebuild, verify Abhinandan's panchanga/positions derive from HIS birth data (02-Mar-1985 · 09:40 · Bhubaneswar), not Abhisek's 1984-02-05.
3. **No silent partial success.** Per-asset verify `lit` + row counts; `state='completed'` ≠ fully built. Full success or an explicit failure list.
4. **Full autonomy**, Abhinandan only: clear → fix → rebuild → fix → optimize → commit/merge/deploy, unattended.
5. **FROZEN orchestrator contract** — conforming fixes only; a needed contract change is STOP-and-raise.
6. **The Cloud Run Job runs DEPLOYED code** (not local) — every server-side fix must be committed + deployed before re-triggering. UI fixes are exercised on localhost (`npm run dev -- --webpack`, per the Turbopack-thrash workaround) which writes to the prod data-plane via the Cloud SQL proxy.

---

## 2 — PRE-FLIGHT (verify prod schema + deployed image)

Via the Cloud SQL Auth Proxy (read-only check first; apply only if missing):
- **Migration 361** — `kala_convergence.domain` column exists AND `mode` CHECK allows `'D'`. If missing, apply `platform/supabase/migrations/361_kala_convergence_domain.sql` surgically. (Missing → B4 domain writers error mid-build.)
- **Migration 358** — `bo_chart_gestalt`, `bo_cdlm_summary`, `bo_cgm_motifs`, `bo_cgm_paths` registered with `has_writer=true`. If missing, apply `platform/migrations/358_bodha_orphaned_writer_registry.sql`. (Missing → 4 new bodha writers silently absent from the plan.)
- **Deployed sidecar/job image** (`amjis-sidecar` / `brama-build-pipeline-job`) is on post-remediation SHA (`8a0ac5af`+). Verify the running revision matches the merge SHA before relying on a rebuild; CDN adds 30–60s.
- Confirm `gcloud run services describe ... --format='value(status.traffic[0].revisionName)'` for both `amjis-web` and the sidecar.

---

## 3 — PHASE 1: CLEAR L1–L5 (fix delete bugs + capture UI/number/refresh behavior)

Open `/clients/1c826d5a/nirmana` via Chrome MCP. For each of L1–L5 (NOT Brahma Jñāna), trigger the layer-level Clear and confirm rows actually go to 0 / dormant. **While doing this, actively observe and log tracker behavior for the shakedown (axes B/C/D below).**

### KNOWN delete bug — fix it (L4 `ph_rectification` "Birth-time rectification" won't clear)
Root cause (confirmed): `ph_rectification` writes TWO tables — `phala_rectification` (185 rows) + `phala_rectification_best` (staged-best row, per its `volume_explanation`) — but its `count_sql`/`target_table` reference only `phala_rectification`. So `deriveDeleteSqlFromCountSql` clears only the primary table and silently leaves `phala_rectification_best` → it reappears in the preview → "won't clear." This is the SAME multi-table-writer class already fixed for `ga_condition` + the L2 bodha writers in `EXPLICIT_CLEAR_OPS` (`platform/src/lib/cockpit/assetClearSpec.ts` — read its comment block).
**Fix:** add a `ph_rectification` entry to `EXPLICIT_CLEAR_OPS` listing BOTH tables, FK-child-first (each `WHERE chart_id = $1`). Add a test. Re-verify the clear empties both tables. Then sweep EVERY asset for the same class — any multi-table writer whose secondary tables aren't in the clear spec, or a `count_sql` that doesn't regex-derive a DELETE → add the `EXPLICIT_CLEAR_OPS` entry + test. Goal: **every L1–L5 asset clears completely, no residue, no "won't clear."**

### Delete/clear correctness + reconciliation (axis C) — verify during clear
- The clear-preview totals must RECONCILE (the original hardening flagged: layer-header rows vs delete-preview "Total rows deleted" diverging on some layers — e.g. global/L0-style `rows_written` vs live `count_sql`). For each L1–L5 layer's delete preview, confirm `assets_clearable + assets_reset_only = affected`, rows tie out, and the displayed "N tables / N assets" denominators are consistent. Fix any non-reconciling total at the source (`/api/cockpit/clear/route.ts` — same single-coherent-summary principle as the E1 hardening).
- The downstream/cascade list must render as a structured, human-named (Sanskrit+English), layer-grouped tree — not a raw asset-id dump or a `slice(0,3)+'…'` truncation. Fix if regressed.

### Refresh-after-delete bug (axis D) — FIX (confirmed at source)
**Confirmed defect:** `ClearConfirmModal.tsx` has NO refetch trigger after a successful clear — the clear succeeds server-side but nothing tells the UI to re-poll, so counts stay stale until the 30s idle tick (`useAssetStats.ts:71` `pollMs = isBuilding ? 5_000 : 30_000`). **Fix:** on successful clear/execute, force an immediate `refetchStats()` + `refreshRun()` (+ registry refetch if asset set changed), exactly as the build-completion path should. The user explicitly reports "refresh is not happening immediately after deletion" — make post-delete refresh instant, not 30s-delayed. Add coverage.

---

## 4 — PHASE 2: GLOBAL REBUILD (fix build bugs + capture liveness/performance)

1. Re-confirm the global plan excludes L0 (Principle 1).
2. From the tracker, trigger **global Rebuild** for `1c826d5a` (dispatches the Cloud Run Job running deployed writers).
3. **Fix any build bug to completion** — root-cause, fix in code, redeploy if server-side, re-trigger the failed asset/subtree until lit. Expect possible first-run issues in newly-corrected/added writers (4 new bodha writers, Mode-D AV-bindhu, domain propagation, Navamsha signals). A newly-populated domain or a new table's rows is the FIX WORKING, not a bug.
4. **Completion gate:** every intended L1–L5 asset `lit` with sane row counts (per-asset table); the 4 new bodha tables have rows; L5 builds. List anything errored/excluded.

### During the build — capture liveness + performance (axes D/E)
- **Live feedback (D):** do the progress bars actually grow with rows (not 12%→100% snap)? Does the ArmillaryGraph DAG react (planets light from the active plan, queued vs building distinct)? Do per-asset states update promptly, or lag the 30s/5s poll? Does SSE deliver `data:` frames (not just `: hb`)? Note + fix regressions against the sealed hardening behavior.
- **Numbers during build (C):** do live counts climb truthfully and match DB? Does the header layer-total reconcile with the sum of per-asset counts? Fix divergences.

---

## 5 — AXIS E: PERFORMANCE — measure, then optimize (both UI and data-gen speed)

Treat this as a first-class deliverable, not an afterthought. The user explicitly wants speed improved where there's genuine opportunity — **without compromising correctness or determinism** (per the deterministic-first rule).

### E.1 — Data-generation speed (the big lever)
- **Measure first:** instrument/observe per-asset build duration across the full L1–L5 run (the orchestrator already heartbeats; capture wall-clock per asset + total). Produce a ranked "slowest assets" list with where the time goes (DB writes? per-row Python compute? per-ayanamsha loops? N+1 queries? missing batch insert?).
- **Investigate concrete levers (propose + implement where safe + deterministic):**
  - Is the orchestrator walking assets **strictly sequentially** when independent same-layer assets (no shared `depends_on`) could run **in parallel**? If safe under the FROZEN contract + the chart advisory lock + per-substep savepoints, parallelize independent assets. **STOP-and-raise if it needs a contract change.**
  - Are writers doing **row-by-row inserts** where a batched `executemany` / `COPY` would be far faster? (Several were already moved to `executemany`; find the remaining ones.)
  - **N+1 query patterns** — upstream reads inside per-row loops that could be one bulk fetch.
  - **Redundant recomputation** across ayanamshas / vargas where a value is invariant.
  - **Missing indexes** surfaced by the build's own queries (the FK-covering-index fix earlier cut a 5-min clear hang — look for the same class on build-read paths).
  - Embedding/Vertex AI batch sizes (bo_samskara) — already batch=100; confirm optimal.
- **Bar:** every optimization must preserve identical output (determinism) and pass tests. No speed-for-correctness trades. Quantify the before/after (e.g. "L2 build 8m12s → 3m05s").

### E.2 — UI / tracker responsiveness
- Page load + interaction latency on the tracker (cockpit shell, layer accordions, DAG render). Any jank, excessive re-renders, oversized payloads from `/api/cockpit/registry` or `/stats`?
- The registry 60s ISR cache + the 30s/5s stats poll — is the refresh cadence right, or are there stale-window gaps (esp. post-action, see §3 refresh fix)?
- Fix concrete UI perf issues (memoization, payload trimming, avoiding full-tree re-render on a single asset's SSE update).

---

## 6 — AXIS A & B: CORRECTNESS (tracker-truth) + UI/UX polish (opportunistic)

While running the above, fix tracker defects you encounter:
- **A (tracker correctness):** states accurate (lit/stale/dormant/error/building reflect DB truth); service vs data assets correctly distinguished; no asset mislabeled; `build_state_stale` reconciles rather than showing a bare unexplained badge.
- **B (UI/UX):** service/data icons present + correct; gold (not green) progress paths for lit/healthy (the brand revert — confirm it held); StatusDot health semantics intact; modals coherent; date formatting `dd-MMM-yyyy`; framer-motion transitions smooth; no clipped/missing controls. Enhance, don't replace, the armillary/gold aesthetic. Don't gold-plate — fix real defects + clear polish wins, not speculative redesign.

---

## 7 — PHASE 3: CLEAN CLOSE

1. Commit/merge/push ALL fixes (delete fixes, refresh fix, reconciliation fixes, perf optimizations, UI fixes) in logical groups; CI green (exit 0 or known-residuals exit=3); deploy. Re-verify the live sidecar/job + web revisions == main SHA.
2. `git status` clean; HEAD == origin/main.
3. Spot-checks: L0 `bg_*` counts unchanged; Abhinandan panchanga is his, not Abhisek's (no native contamination); the 4 new bodha tables populated; L5 built.
4. **Governance:** update `CURRENT_STATE_v1_0.md` + append SESSION_LOG. **Heading `## <SESSION_ID> — <date>, <status>`** — SESSION_ID is the FIRST token after `##` (NO leading "Session" word, NO colon — that mistake broke CI twice); NO embedded double-quotes in YAML list items; update `last_session_id` in CURRENT_STATE §2.

---

## 8 — REPORT (structured, end)

- **Regeneration:** clear results (+ every delete bug fixed: asset, root cause, file:line, test); rebuild completion table (per-asset lit + rows, L1–L5, incl. 4 new bodha tables + L5); every build bug fixed.
- **Tracker shakedown by axis:**
  - A correctness: defects found + fixed.
  - B UI/UX: defects + polish, before/after.
  - C reconciliation: which totals diverged + the fix (numbers now tie out).
  - D refresh/liveness: the post-delete instant-refresh fix + any SSE/poll fixes.
  - E performance: the slowest-assets measurement, each optimization + quantified before/after (data-gen) and UI responsiveness wins.
- **Safety:** L0-untouched + no-native-contamination spot-check results.
- **Sync:** final git/revision state, pushed SHA.
- Explicit note: deep data-correctness audit deferred to a separate session.

---

## 9 — GUARDRAILS RECAP

L0 never touched — verify the global plan excludes it BEFORE rebuild + spot-check after. Abhinandan `1c826d5a` only — never `482012f1`; no native contamination (verify post-build). FROZEN contract — conforming fixes only; parallelization or any contract-adjacent change = STOP-and-raise. Performance optimizations must preserve deterministic, identical output + pass tests — never trade correctness for speed. Surgical migrations (verify next-free number across BOTH `platform/migrations/` and `platform/supabase/migrations/`). Delete fixes follow the `EXPLICIT_CLEAR_OPS` multi-table pattern. Cloud Run Job runs deployed code — deploy server-side fixes before re-triggering. SESSION_LOG heading: id-first, no "Session" word, no colon. Full success or explicit failure list — never silent partial.
