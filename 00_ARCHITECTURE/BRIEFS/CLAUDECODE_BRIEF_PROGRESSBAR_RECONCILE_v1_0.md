---
artifact: CLAUDECODE_BRIEF_PROGRESSBAR_RECONCILE_v1_0.md
canonical_id: PROGRESSBAR_RECONCILE_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-12
authored_for: Claude Code in Antigravity IDE
diagnosis_source: GA8_ROWCOUNT_AND_PROGRESSBAR_DIAGNOSIS_v1_0 + the verify-before-fix results (2026-06-12)
data_plane: ALWAYS prod via Cloud SQL proxy
key_finding: The dark progress bar is NOT missing data and NOT a count timeout. asset_throughput is stale/absent (ga_sensitive dormant w/ 8,055 rows in chart_facts but no throughput record; ga_strength rows_written=1,330 vs real 2,184). Two-part fix: re-run the 2 assets + make the bar reconcile against count_sql so this can't recur.
---

# Progress-Bar Reconcile + Targeted Re-run — Execution Brief v1.0

## §0 — What the diagnostics proved (so we fix the right thing)
- Data is COMPLETE for all 4 assets (count_sql: ga_strength 2,184; ga_sensitive 8,055; ga_sade_sati
  11,019; ga_structural 74,644). NOT missing.
- count_sql is FAST (<1.1s each; `chart_facts_category_idx (chart_id, fact_category)` is effective).
  NOT a timeout. Total chart_facts = 96,617.
- Root cause = `asset_throughput` staleness: ga_sensitive `dormant` (never got a throughput record —
  its data came from a prior L1 build path that didn't write throughput); ga_strength stale partial-
  run record (1,330 vs real 2,184). ga_sade_sati + ga_structural are `lit` + correct.
- **This is CLAUDE.md §N.4's known "stats route reads count_sql NOT asset_throughput" trap — surfacing
  in the progress-bar/AssetNode component, which still trusts `asset_throughput.state`.**

## §1 — PART A (narrow): re-run the 2 assets to write current throughput records
Re-run **ga_sensitive** and **ga_strength** through the orchestrator for the native chart
(482012f1-710e-4a25-994a-93821f5871aa) so they get fresh `lit` throughput records with correct
`rows_written`. This is data-plane (operator/orchestrator), per the FROZEN contract — `POST
/api/cockpit/runs scope=asset` for each, or the runner. Do NOT rebuild ga_sade_sati / ga_structural
(already lit + correct). **[verify-against: prod]** after: `SELECT asset_id, state, rows_written FROM
asset_throughput WHERE chart_id='482012f1-...' AND asset_id IN ('ga_sensitive','ga_strength');` →
both `lit`, rows_written matching count_sql (ga_sensitive 8,055; ga_strength 2,184).

## §2 — PART B (systemic): the bar reconciles against count_sql — stale throughput can't show dark
The progress-bar visual state currently comes from `asset_throughput.state`
(`platform/src/components/build_orchestrator/AssetNode.tsx` + the routes that feed it). The stats
route ALREADY computes the real count from count_sql. Reconcile them so the REAL DATA wins for the
"does this asset have data?" determination:

- When `asset_throughput` says `dormant`/absent/stale BUT count_sql returns > 0 rows for that chart,
  the bar must show the asset as **populated (lit-equivalent), with its real count** — NOT dark.
  Optionally badge it "data present, build-state stale" so the discrepancy is visible (don't hide it).
- When count_sql = 0 AND no throughput → genuinely dark (correct).
- When count_sql errors/times out → show error explicitly (no-silent-drop), never a fake 0.
- Keep `asset_throughput` as the build-HISTORY record (last_built_at, which run, heartbeats) — it's
  still useful for "when/how was this built." It just stops being the SOLE source of truth for "is
  there data." count_sql/chart_facts is authoritative for data-presence (the §N.4 principle).

Implementation: the cockpit status/stats path already has the count; thread it into the AssetNode
state derivation so `state` = reconcile(throughput_state, live_count). Reuse the existing
`/api/cockpit/stats` count rather than adding a new query.

## §3 — Why both parts (not just the re-run)
Part A alone fixes today's two dark bars but leaves the systemic gap: ANY asset populated outside a
clean orchestrator run (a prior L1 build, a partial run, a direct migration) will show dark again,
even though its data is fine — the exact thing that just happened. Part B closes that permanently by
making the bar trust the real data, consistent with how the stats route already works. The native
chose BOTH.

## §4 — Acceptance [verify-against: prod / localhost:3000]
- [ ] ga_sensitive + ga_strength re-run → `lit` throughput, rows_written = count_sql (8,055 / 2,184).
- [ ] Progress bar (and Atlas, which shares /api/cockpit/stats) shows all 4 assets populated with real counts.
- [ ] Reconcile logic: an asset with stale/absent throughput but count_sql>0 shows populated (not dark), ideally badged "build-state stale"; count_sql=0+no-throughput shows dark; count_sql error shows error.
- [ ] No regression: lit assets with matching throughput still show lit; the build-history (last_built_at) still readable.
- [ ] Spot-check a deliberately-cleared asset still shows dark correctly (reconcile didn't break the empty case).

## §5 — Out of scope
No data rebuild of ga_sade_sati/ga_structural; no count_sql changes (they're correct + fast); no index
work (chart_facts_category_idx is adequate). Atlas inherits the fix automatically (shares the stats path).

---
*End of PROGRESSBAR_RECONCILE v1.0. Re-run ga_sensitive + ga_strength for fresh throughput (Part A);
make the bar reconcile against count_sql so real data wins over stale/absent throughput (Part B) —
closing the §N.4 cockpit-truth trap in the progress-bar component. Data was never missing; the bar
was trusting the wrong source.*
