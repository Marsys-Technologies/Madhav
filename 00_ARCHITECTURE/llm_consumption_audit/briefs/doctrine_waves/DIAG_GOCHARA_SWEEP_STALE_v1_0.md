---
artifact: DIAG_GOCHARA_SWEEP_STALE
type: FOCUSED DIAGNOSTIC MEMO (single-issue session, not a wave open)
wave_context: D-5 Gochara-Chitra (CLOSED GREEN-WITH-PARTIALS per STATE_D-5.md/REPORT_D-5.md on
  origin/main, advanced to D-4b)
opened: 2026-07-21 (session date per harness clock; DB timestamps below are UTC)
conductor: Claude Code (Sonnet 5), fully autonomous diagnostic session per native directive
status: See §6 disposition
---

# DIAG — Gochara forward-sweep (`ka_gochara_sweep`) STALE badge + 1-row count

## §1 — The finding, confirmed by direct query

`asset_throughput` for chart `482012f1-710e-4a25-994a-93821f5871aa`:

| asset_id | state | last_built_at | last_error |
|---|---|---|---|
| `ka_gochara_sweep` | **error** | 2026-07-20T18:54:37Z | `BLOCKED: upstream dependency(ies) timeout:1800s did not complete in this run; skipped to avoid building on incomplete data` |
| `ka_gochara_resonance` (upstream) | lit | 2026-07-20T00:38:57Z | — |

Direct table count `SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=...` = **1**, matching
the cockpit badge exactly (not a display artifact).

## §2 — Diagnosis by data, in the native's prescribed order

**1. Freshness reality.** `ka_gochara_sweep`'s only declared dependency (`asset_registry.depends_on`)
is `ka_gochara_resonance`, last built 2026-07-20T00:38:57Z — *older* than every one of the sweep's
three most recent attempts (13:28, 16:29, 18:24 UTC on 07-20), so the badge is not explained by an
upstream having rebuilt out from under it. The real code-fix timeline (git, origin/main):
- `5ceedd75` (#663, hot-path INFO→DEBUG perf fix) merged 2026-07-20T16:16:41Z
- `81a77f26` (#665, plateau-disclosure + top-K local-maxima RED-C/RED-D fix) merged
  2026-07-20T18:11:32Z (23:41:32 IST)

Both fixes were on `origin/main` **before** the last rebuild attempt (`ccb7f597...`, started
2026-07-20T18:24:36Z) even started. So the deployed *source* is current. The gap is that the
chart's *materialized data* was never successfully rebuilt against that fixed code — three
consecutive `d5-redc-redd-post-merge-rebuild` dispatches (13:28→13:58, 16:29→16:59, 18:24→18:54,
each ~30 min) all ended `state='failed'`, each having committed only **one** substep
(`major_gain:year:60`) before the per-asset `writer_timeout_seconds=1800` watchdog killed the run.
Because `ka_gochara_sweep` follows the standard §N.3 per-chart delete-then-insert idempotency
pattern, each new dispatch's own start wipes the prior attempt's partial rows before re-attempting
— so the live row today is whatever the *last* attempt (18:24) managed: 1 substep, shape
`window_start=2010-01-01, window_end=2011-01-01` (an exact 1-year window, `left_active`/
`right_active` both `true` — i.e., still the OLD pre-plateau-disclosure-fix shape family, not the
2-year plateau the close report describes — see §4).

**2. Cockpit-trap check (§N.4).** `asset_registry.count_sql` for `ka_gochara_sweep` is
`SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1` — correctly scoped to the asset's
actual target table, chart-scoped. Direct table count (1) matches this exactly. **Not a
count_sql/display defect** (cause 2 ruled out).

**3. CR-113 ghost check.** `SELECT ... FROM build_runs WHERE state NOT IN ('completed','failed',
'stopped')` returns **zero rows** — no orphaned/stuck run is poisoning this asset's freshness
computation. All 8 of `ka_gochara_sweep`'s `build_runs` rows (both the `d5-gochara-chitra-rebuild`
and `d5-redc-redd-post-merge-rebuild` cohorts) are cleanly terminal (`failed`). **Not a stuck-run
defect** (cause 3 ruled out).

**4. State anomaly?** No — this is the inverse of the pattern the native flagged as a possible new
orchestrator anomaly ("data says built-and-fresh but flag says stale"). Here the flag (`error`,
1 row) **agrees with** the live data (1 row, genuinely incomplete). The badge is telling the truth.

## §3 — Root cause: the badge is CORRECT (Cause 1, legitimately stale)

`ka_gochara_sweep`'s writer has never, in any of its last 3 post-fix dispatch attempts, gotten past
its own first (highest-priority) substep within the 1800s per-writer budget. This is a genuine,
still-open **performance** characteristic of the writer under its current chunking (300 substeps:
100 years × 3 populated event-classes) — the #663 logging fix did not resolve it (it merged
*before* the still-failing 18:24 attempt). `_mark_asset_blocked`'s generic on-block message
(`platform/python-sidecar/pipeline/orchestrator/runner.py:207-246`) is reused for both "a real
upstream dependency failed" and "this asset's own writer exceeded its timeout" (the latter is
signalled internally as a synthetic `blocking_deps=["timeout:1800s"]`, see `execute_dag` line 340)
— so the surfaced message ("upstream dependency(ies) timeout:1800s did not complete") is a
**pre-existing, orchestrator-level mislabeling** (the asset blocked on its *own* timeout, not a
real upstream), not something introduced by D-5. This is flagged for a future hygiene pass (label
self-timeout distinctly from upstream-failure) but is **not** touched here — it is FROZEN-adjacent
`runner.py`, and the message, while confusingly worded, is not factually wrong about *why* the
asset has no fresh, complete row set.

## §4 — A discrepancy surfaced pre-rebuild, then resolved by the rebuild itself (disclosed, not chased further)

Before this session's rebuild (§5), `origin/main`'s `STATE_D-5.md` `gate_run_3` block (the wave's
own close-time verification, dated 2026-07-20T23:50:00Z) asserted "all 3 named-specimen priority
substeps (`major_gain:year:60/61`, `marriage:year:63`) confirmed committed under the fresh v6
fingerprint," with `major_gain` `continuity_state={raw_start:2010-01-01, raw_end:2012-01-01,...}`
(a 2-year plateau) and a marriage verdict of FAIL ("only ONE served row, 2013-01-06/07,
`chara_karaka` active, `guru_shani_double_transit` inactive"). At the start of this diagnostic
session, direct query showed only **1** row (`major_gain:year:60` alone, 1-year window) — not
reproducing the close report's claimed 3-row, 2-year-plateau state, with no intervening
`build_runs` row to explain a regression from 3→1. That discrepancy is reported here as originally
found; this session did not chase its cause (out of scope for a single-issue diagnostic).

**After this session's rebuild (§5) ran to completion, the live data changed materially** — see
§5's results. The rebuild's own output now shows the major_gain plateau exactly as the close
report described (`raw_end=2012-01-01`) — supporting the reading that gate_run_3 verified real,
correctly-shaped data that subsequently got wiped (by a `_RESUME_VERSION`-triggered delete-then-
insert on a later, incomplete dispatch) rather than the close report having fabricated its
verification. **However, §5's marriage-specimen result contradicts the close report's FAIL verdict
outright** — see §5 for the specifics. This is flagged prominently for native review; it is not
this session's place to overturn a closed wave's gate disposition, but the live evidence
materially conflicts with it and should not be left unflagged.

## §5 — Rebuild (this session) — RESULT: substantial progress, still structurally incomplete

Per the native's pre-authorized Cause-1 disposition, one scope-limited rebuild was dispatched:
`platform/scripts/dispatch_d5_redc_redd_rebuild.py` → `build_run fc9b92d3-d410-4f03-922f-b0400b5f04ea`
→ `gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1
--args=--run-id,fc9b92d3-...` (execution `brahma-build-pipeline-job-l5rb9`,
2026-07-20T19:44:26Z → 20:14:32Z, ~30 min, ended `state=failed` — the asset-level writer again hit
its own `writer_timeout_seconds=1800` budget before all 300 planned substeps completed).

**What actually materialized (verified by direct query, not by re-reading any prior report):**

- `major_gain:year:60` (resumed instantly from the prior attempt's ledger, 0s) and
  `major_gain:year:61` (completed 2s after run start) → consolidated into **one** `major_gain` row:
  `window_start=2009-12-31, window_end=2010-12-31, continuity_state={raw_start:2010-01-01,
  raw_end:2012-01-01, left_active:true, right_active:true}` — the corrected 2-year open-edged
  plateau, matching the RED-C plateau-disclosure fix's intent and the close report's own
  description of a PASS. Confirmed: **plateau open-edge flags are present and correctly both
  `true`** (per the native's requested spot-check).
- `marriage:year:63` (completed ~14.5 min later, 2026-07-20T19:59:00Z, after a long stall —
  this is the substep the writer previously could never reach) → **52 rows**, a dense field of
  local-maxima point candidates spanning Jan 2013–Dec 2013 (top-K local-maxima serving, RED-D
  fix). Critically: `guru_shani_double_transit` is **active** (`weight=0.1, active=true`) at
  peak dates `2013-06-02` through `2013-12-29`, **including 2013-12-07 and 2013-12-15 — the two
  peaks immediately bracketing the LEL marriage date of 2013-12-11.** This directly contradicts
  `STATE_D-5.md`'s closed marriage-verdict of FAIL ("`guru_shani_double_transit` inactive"). Under
  this session's fresh, independently-verified rebuild, the named mechanism **does** activate
  near the true date. (Native's requested "both 2013 marriage peaks" spot-check: there are in fact
  dozens of candidate peaks across 2013 under the corrected top-K serving, not two — the specimen
  question is whether one of them both (a) sits near 2013-12-11 and (b) carries the named
  mechanism; both hold for 2013-12-07/12-15.)

**What did not materialize:** only these 3 named-specimen substeps + the already-resumed prior
ones exist; the sweep's other ~297 substeps (remaining years × the 3 event-classes, plus whatever
`career_advancement` needs) still have never run. `asset_throughput` therefore still correctly
shows `state=error`, `last_error="BLOCKED: upstream dependency(ies) timeout:1800s did not complete
in this run..."` (see §3 — this message is accurate in substance, if confusingly worded, since the
asset's own writer, not a real upstream, is what timed out) — **the STALE/error badge remains
correct after this rebuild**, because the asset genuinely is not fully materialized. Direct count:
`SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=...` = **53** (up from 1 pre-rebuild).

## §6 — Disposition

**Cause 1 (legitimately stale) — CONFIRMED, badge is correct, no defect in the badge/cockpit
mechanism.** `count_sql` is properly scoped (§2.2); no stuck/orphaned run poisons the computation
(§2.3); the `error` state and 1800s-timeout message accurately reflect that `ka_gochara_sweep` has
never completed a full materialization pass for chart 482012f1 — before this session only 1 of
~300 substeps had ever committed, and after one more scope-limited rebuild attempt only 3 have
(the 3 the wave's own specimens needed). This is a genuine, still-open **performance/throughput**
characteristic of the writer (each of the 3 committed substeps that involve real astronomical
computation takes on the order of minutes to ~15 minutes; the remaining substeps have not been
observed to complete at all within one 1800s dispatch), not a cockpit display defect, not a stuck
build_run, and not a new orchestrator state anomaly (cause 4 does not apply — the flag and the
data agree).

**Action taken this session:** one rebuild dispatched and monitored to completion (§5). Per the
native's own framing that RED-C/RED-D fixes were the in-scope work and that this is a
single-issue, non-wave-opening diagnostic, **no further rebuild attempts were dispatched** and no
code was changed. Getting `ka_gochara_sweep` to full (300/300 substep) materialization is a
throughput problem that this session did not attempt to fix (would require either raising
`writer_timeout_seconds` for this asset, further chunking, or repeated dispatches — an engineering
call for a future session/lane, not a diagnostic one).

**Escalation for native review (not resolved here):**
1. **RED-D residual is likely stale.** `STATE_D-5.md`'s closed marriage-verdict (FAIL, mechanism
   inactive) does not reproduce against this session's freshly-rebuilt, independently-queried data
   — `guru_shani_double_transit` **is** active at peaks bracketing 2013-12-11. If the D-4b Grand
   Bakeoff is carrying this as a named residual to chase, it may already be resolved; recommend a
   fresh gate_run_4-style spot-check before continued design work assumes the residual stands.
2. **Full materialization is still pending.** `ka_gochara_sweep` needs an unknown number of
   further ~30-min dispatch cycles (at the observed rate: 1-3 substeps per successful cycle, ~300
   total) to reach 100% — or a throughput fix — before the cockpit will show a clean `lit` state.
   This is expected, not a bug, but is worth a deliberate decision (dispatch-to-completion now vs.
   defer to D-4b) rather than leaving the asset silently `error` indefinitely.
3. **Orchestrator message hygiene (cosmetic, not urgent):** `_mark_asset_blocked` in
   `platform/python-sidecar/pipeline/orchestrator/runner.py` produces the same "upstream
   dependency(ies) ... did not complete" wording whether a real upstream failed or the asset's own
   writer hit its timeout (`execute_dag`'s synthetic `blocking_deps=["timeout:Ns"]`, line 340).
   Recommend distinguishing the two cases in a future FROZEN-orchestrator-adjacent hygiene pass
   (raised, not touched, per §N.2).

No code changes were made. Worktree: `.claude/worktrees/gochara-sweep-diag` on branch
`diag/gochara-sweep-stale` off `origin/main` (5b57d49f). This memo is committed there and pushed;
no merge to `main` was performed (a documentation-only diagnostic finding, left for native/
conductor review alongside the D-4b readiness pass).
