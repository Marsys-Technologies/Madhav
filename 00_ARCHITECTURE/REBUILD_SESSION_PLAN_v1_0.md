---
canonical_id: REBUILD_SESSION_PLAN
version: 1.0
status: PLANNED — awaiting execution. Authored 2026-07-10 per CONDUCTOR RULINGS point 1 (mandatory,
  blocking, dedicated sequenced single-writer session) + the native's 7-point addendum of the same date.
  This is the Phase-1 exit gate for R6 TOTAL ELEVATION. Nothing in Phase 2 (2A/2B/2C) or Phase 3
  (3c/3d/3f) may start until every gate in §8 of this document passes.
role: The single authoritative runbook for the live rebuild of both canonical charts. Ring-3 diffs are
  judged against §1's Expected-Change Manifest, not against intuition. Anything that changes OUTSIDE
  the manifest halts execution pending root-cause explanation.
---

# Rebuild Session Plan — R6 TOTAL ELEVATION Phase-1 Exit Gate

## §0 — Why this session exists, and why it hasn't started casually

Phase-1 (lanes 1a–1f + 1b's delegate resolution) delegated shadbala/vimshopaka/ashtakavarga (1a),
special lagnas/upagrahas/sensitive points (1d), Tajika/yuddha/combustion/drishti (1e), dasha systems
(1c), and D60/ashtakavarga/compound-friendship vargas (1b) to PyJHora, and 1f stamped verification
integrity estate-wide. All five lanes are merged to `main` as **code**. None of that code has yet run
against the live `chart_facts`/`chart_dashas`/`chart_divisionals` tables for either canonical chart —
Phase-1's own Ring-1/Ring-2 was deliberately restricted to pytest + offline recomputation after the
concurrent-write race was discovered mid-session (§K of the run ledger), and all live `execute_run`
calls against the two shared charts were banned for the remainder of Phase 1. This session lifts that
ban, under a single-writer discipline, to actually apply Phase-1's code to live data.

**This is not optional bookkeeping.** Direct DB inspection (below) shows the native chart currently sits
with real writer-level failures on record, and lane 1a's shadbala/vimshopaka delegation has **never
once completed a successful live build on either chart** — every attempt died mid-`ga_strength` before
0h's watchdog fix existed. The current live `chart_facts` shadbala/vimshopaka/ashtakavarga rows are
pre-1a data. This session is the first opportunity to actually land it.

## §1 — Pre-flight state audit (ground truth, queried live 2026-07-10)

### §1.1 — `asset_throughput` current state (both charts, core L1 writers)

| asset_id | 482012f1 (native) | 1c826d5a (Abhinandan) |
|---|---|---|
| ga_positions | lit (2026-07-10 06:02) | lit (2026-07-07 23:20) |
| ga_dashas | **error** (06:02) | lit (06:19) |
| ga_structural | **error** (06:02) | **dormant** (06:45) |
| ga_strength | **error** (06:03) | **error** (06:45) |
| ga_sensitive | **error** (07-08 01:10) | lit (07-07 23:21) |
| ga_vargas | **error** (06:02) | lit (07-07 23:21) |
| ga_sade_sati | **error** (06:02) | **dormant** (06:45) |
| ga_nakshatra | **error** (06:05) | lit (07-07 23:22) |
| ga_panchanga | lit (06:04) | lit (07-07 23:21) |

**Diagnosis, not a new problem to chase**: `build_runs` shows `r6_chain_rebuild_2026_07_10` failing
repeatedly at `current_asset_id: ga_strength` (three separate attempts: 06:08–06:33, 06:46–07:20,
07:12–07:45, all `state: failed`) — this predates lane 0h's watchdog fix (PR #531, merged later this
session). This is almost certainly the exact T-5/T-9 root cause 0h fixed: `run_asset()` never stamped
`last_built_at` on the initial `'building'` transition, so a stale timestamp from a PRIOR build let the
15-minute watchdog reaper kill a genuinely in-progress `ga_strength` build (~11 min, no intermediate
heartbeat) almost immediately. The `error`/`dormant` marks above are the residue of pre-fix reaping, not
evidence of a code defect in Phase-1's writers themselves — but they must be **confirmed**, not assumed,
by this session's rebuild (if `ga_strength` fails again post-0h-fix, that IS a new, real problem and
halts the session per §7).

### §1.2 — Migration 430 (`bg_shashtiamsha_deities`, lane 1b's D60 real-deity table)

**Confirmed applied to prod** (`_migrations_applied` id=315, applied 2026-07-10T09:06:43Z, sha256
matches the committed file) and populated: **60/60 rows** present. Lane 1b's D60 deity lookup will
resolve real rows once `ga_vargas` rebuilds — no migration gate blocks this session.

### §1.3 — Baseline row counts, current live state (both charts, pre-rebuild)

Categories expected to change this session (current/"before" counts — see §2 for what SHOULD happen):

| fact_category | 482012f1 | 1c826d5a | Lane that touches it |
|---|---|---|---|
| yoga_label | 34 | 41 | 0c (already rebuilt — reference baseline, not expected to move again) |
| dosha_label | 110 | 110 | 0c (hardcoded library, unaffected — must NOT move) |
| sade_sati_cycle | 160 | 160 | 0d (already rebuilt — must NOT move again) |
| graha_shadbala_total | 52 | 52 | **1a — expected to change** (real PyJHora shadbala replaces pre-1a values) |
| graha_shadbala_{cheshta,dig,drik,kala,naisargika,sthana} | 45/45/45/45/9/45 | same | **1a — component values expected to change; row COUNTS should hold (fixed structural cardinality — 9 grahas × 5 components + naisargika's fixed 9), only the numeric VALUES move** |
| vimsopaka_bala_per_graha | 35 | 35 | **1a — values expected to change, count fixed at 7 vargas × 5 grahas or similar fixed cardinality** |
| ashtakavarga_bindu | 480 | 480 | **1a/1b — values expected to change; count fixed (8 vargas × 60 or equivalent structural constant)** |
| ashtakavarga_bindu_per_varga | 6720 | 6720 | **1a/1b — same** |
| esoteric_point_pranapada_sphuta | 35 | 35 | **1d — expected to DROP toward 0 or be deleted entirely (M-9: fabricated sphutas deleted per B.10)** |
| esoteric_point_sphuta_fertility | 70 | 70 | **1d — same disposition as pranapada** |
| esoteric_point_trikona_dasha_sphuta | 35 | 35 | **1d — same disposition** |
| special_lagna | 110 | 110 | **1d — expected to change (PyJHora delegation replaces hand-rolled formulas); count may hold if cardinality is structural** |
| upagraha_position | 210 | 210 | **1d — expected to change (PyJHora delegation)** |
| sun_derived_upagraha | 140 | 140 | **1d — expected to change** |
| sensitive_point_gulika_mandi | 70 | 70 | **1d — expected to change** |
| aspect_tajik | 105 | 105 | **1e — expected to change (real Tajika aspects/orbs replace placeholder)** |
| tajik_hadda_lord | 1200 | 1200 | **1e — expected to change** |
| graha_yuddha_per_varga | **16** | **77** | **1e — EXPECTED TO CONVERGE toward parity.** This pre-existing cross-chart asymmetry (482012f1 has less than a quarter of 1c826d5a's yuddha rows) is itself evidence of the pre-fix "yuddha floor" bug 1e's M-19 fix addresses — post-rebuild these two numbers should relate by a real astronomical reason (different planetary configurations), not by one chart's floor-guard silently suppressing rows the other chart's didn't. |
| combustion_per_varga | 725 | 725 | **1e — expected to change (real combustion + Saturn drishti fixes)** |
| chart_divisionals total | 20,877 | 20,877 | **1b — expected to change (D60 deity/quality rows go from floored-NULL to real kroora/soumya values; ashtakavarga varga rows re-derive; compound-friendship-dependent dignity fields shift)** |
| chart_dashas total | 553,308 | 544,621 | **1c — expected to change (PyJHora dasha delegation may shift boundary timestamps/sub-day precision per V-1/V-9 class fixes already partially reflected from 0e; M-5/M-6/M-21 apply on top)** |

**What must stay BYTE-IDENTICAL, no exceptions**: the FORENSIC 7 anchors (Sun=Capricorn, Moon=Purva
Bhadrapada, Lagna=Aries all 5 ayanamshas, Tithi=Shukla Tritiya, Vara=Ravivara, Yoga=Shiva, Karana=Garaja)
and every `graha_position`/`graha_sign_attributes` row (the positional core — `ga_positions`, untouched
by any Phase-1 lane, last built 2026-07-07/07-10 and correct). **If any Phase-1 rebuild step changes a
graha's longitude, sign, or nakshatra by even a fraction of a degree, that is an instant halt** — no
Phase-1 lane touches ephemeris computation; a positional-core diff means data corruption, not a fix
landing.

### §1.4 — Baseline lineage (pinned per point 5 — the R5.3 cross-contamination lesson)

- **`origin/main` HEAD at plan authorship**: `3c7ab8ab490496ca646853f7a003850836239366`
  ("docs(r5.3): B4 acceptance re-run — honest close, gate NOT MET, backlog transfers to R6", #530).
  This is a **docs-only** commit (8 files, all `00_ARCHITECTURE/*` + one eval-results JSON + a one-line
  brief-status edit) from the concurrent, now-closed **R5.3 campaign** — confirmed via `git show --stat`,
  zero writer/orchestrator/migration/salience touches. It sits directly on top of R6's own `db7ec3a2`
  (this session's lane 3b-budgets merge). **Sole active campaign for the remainder of this session and
  the rebuild that follows: R6 TOTAL ELEVATION.** R5.3 is CLOSED (gate NOT MET, 39.5%, backlog
  transferred into this register — see §1.5) and contributes no further live sessions.
- **Local working tree**: confirmed on `main`, HEAD matches `origin/main` exactly (`3c7ab8ab`), zero
  divergence. `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` specifically checked byte-identical between local
  working copy and `origin/main`'s committed version (592/592 lines) — the file that looked untracked
  at session start is now fully reconciled; no silent-fork risk found.
- **Deployed Cloud Run revisions** (confirmed live, all `success` on the `Deploy to Cloud Run` workflow
  at `3c7ab8ab`): `amjis-web-00937-2m4`, `amjis-sidecar-00845-wz7`, `amjis-mcp-00420-cxp`.

**REFRESHED 2026-07-10, post-checkpoint (PR #536)** — `origin/main` HEAD advanced
`3c7ab8ab` → **`f969ac12b2918b5641d870ddbe211864e1275024`** ("docs(r6): checkpoint campaign
artifacts — run ledger, rebuild session plan, campaign docs", #536, this session's own commit,
6 files, `00_ARCHITECTURE/**` only, zero code/migration/orchestrator touches — confirmed via
`git show --stat`). Local `main` fast-forwarded cleanly to `f969ac12` (the 6 pre-existing untracked
local copies were verified byte-identical via `cmp` against the committed versions before removal,
then a plain fast-forward pull, no conflicts). Merge-base ancestry independently confirmed
(`git merge-base --is-ancestor f969ac12 origin/main`).

Post-merge CI (`CI — Ganga Quality Gate`, run 29110904798) passed clean on `f969ac12`, which
chain-triggered `Deploy to Cloud Run` (run 29111403165) via its `workflow_run` trigger (not
path-filtered for this post-merge path, unlike the PR-time build-check trigger). Outcome, checked
directly against live Cloud Run state:
- `Build & Deploy MCP` / `Build & Deploy Sidecar` / `Build & Deploy Pipeline Job Image` — **all
  skipped** (`Detect changed paths` correctly gated these on `platform-mcp/**`/`platform/**`, absent
  from this docs-only diff). `amjis-sidecar` (`amjis-sidecar-00845-wz7`) and `amjis-mcp`
  (`amjis-mcp-00420-cxp`) confirmed **unchanged** via `gcloud run services describe`.
- `Build & Deploy Web` — **did NOT skip** (ran for real, 3m21s) despite the docs-only diff; this
  job's path-gate is evidently broader/absent compared to MCP/Sidecar/Pipeline-Job-Image's. Produced
  a genuine new revision, **`amjis-web-00938-z7l`**, confirmed healthy and serving 100% traffic
  (`status.conditions[0].status = True`). Functionally a no-op (identical source, just a new
  revision number) but the lineage pin below reflects the new revision honestly rather than the
  stale pre-checkpoint one.

**Updated pin — this is now the lineage every subsequent Ring-3/TAP comparison in this session
compares against**: main `f969ac12`, `amjis-web-00938-z7l`, `amjis-sidecar-00845-wz7`,
`amjis-mcp-00420-cxp`, R6 sole active campaign (unchanged from below). **main and prod are now
fully clean and in sync** — zero uncommitted governance docs remain (only 4 stray, deliberately-
untouched `accuracy/*.json` root files, disposition pending the native's explicit decision,
unrelated to any campaign's writer/migration code).

- **Every later Ring-3/TAP battery this session and the rebuild session compares against THIS
  lineage** — main SHA `3c7ab8ab`, these three revisions, R6 as sole active campaign. A probe result
  that looks like a regression but traces to a DIFFERENT commit/revision than these is a lineage-
  contamination false alarm, not a real regression (the exact class of error the R5.3/R6 concurrent-
  branch churn produced earlier this session — see run ledger's RE-SYNC NOTE).

### §1.5 — The "3-flips" triage (folded in per point 6)

This is R5.3's own B4 acceptance close's zero-regression check (`R5_3_ACCEPTANCE_HONEST_CLOSE_v1_0.md
§4`, committed at `3c7ab8ab`) — 3 items flipped PASS(B1)→FAIL(B4) in the frozen answer battery:

| id | B1→B4 | Real regression? | Disposition |
|---|---|---|---|
| **X-5** | PASS→FAIL | **NO — battery staleness.** `synth_tail_divergence_get` was dead (500, schema drift) when B1's assertion was written expecting an honest failure. R6's own concurrent lane 0b fix (register row R-10) made the tool genuinely succeed — an IMPROVEMENT the stale battery assertion penalizes. | **Already Ring-3-confirmed PASS this session** (0b's R-10 row, prod-verified 2026-07-10). Re-confirm post-rebuild in §8's sweep — row volumes/content must not regress this fix. |
| **Q3-N-1** | PASS(14/11)→FAIL(6/11) | **Real, pre-existing content-depth gap — not caused by any code change.** `judgment_query` untouched by every R5.3 PR; same "raw JSON, not synthesized" gap `graha_portrait` had (B2 root-cause). B1's grading was lenient/marginal, not broken by anything. New register row **R-30**. | Out of this rebuild session's scope (a Phase-2/Phase-3 synthesis-depth item, not a data-correctness item) — confirm the register row stands unchanged post-rebuild (rebuilding chart data cannot fix a synthesis-narration gap), leave for Phase 2/3 triage. |
| **Q3-A-2** | PASS(13/11)→FAIL(5/11) | **Same pattern.** `bodha_signals_get`'s Jaimini response missing Amatyakaraka; untouched by any R5.3 PR. New register row **R-31**. | Same disposition as Q3-N-1 — confirm register row stands, defer the actual fix to Phase 2/3. |

**What this session must do with the 3-flips**: (1) re-confirm X-5/R-10 survives on rebuilt data (folded
into §8's Ring-3 sweep scope), (2) confirm R-30/R-31 are recorded correctly in the register and are
NOT accidentally touched/masked by this rebuild (a synthesis-depth gap in `judgment_query`/
`bodha_signals_get` has no data-layer fix available here — if rebuilt data makes either look
superficially different, that's re-grounding, not resolution, and must not be misreported as fixed).

## §2 — Expected-Change Manifest, synthesized (the judgment surface for §8's Ring-3 diffs)

**Rule**: every value/row-count delta Ring-3 observes post-rebuild is judged against this manifest.
IN-manifest changes are expected and PASS. OUT-of-manifest changes — any positional-core drift, any
FORENSIC-anchor drift, any category not listed here moving at all — HALT execution immediately per §7;
root-cause and explain before any further rebuild step, on either chart.

**Per-asset summary** (full per-category detail in §1.3):

| Asset | Lane(s) | Expected to change | Must NOT change |
|---|---|---|---|
| `ga_positions` | none (positional core) | nothing | graha longitude/sign/nakshatra/dignity-basis — FORENSIC 7 lives here |
| `ga_dashas` | 1c (M-5/M-6/M-21) + prior Phase-0 dict_row fix + 0f (M-7/M-8 Chara) + 0e (V-1/V-9) | dasha lord sequences, sub-period boundary timestamps (sub-day precision), Chara Dasha derivation, `chara_karaka` substep must complete cleanly (previously the substep that hard-failed pre-Phase-0-fix) | vimshottari/yogini/ashtottari system row COUNTS (10,375/16,748/6,592-class figures) — these succeeded before and are structural, not touched by 1c's fix scope |
| `ga_structural` | 1e (M-12–M-15/M-19/M-20/V-5) + 0c (Y-1/Y-9/Y-7, already live) | Tajika aspects/orbs, composite strength, graha_yuddha (convergence toward cross-chart parity), combustion, Saturn drishti | yoga_label/dosha_label counts (0c's fix already landed and Ring-3-confirmed; must hold at 34/41 and 110/110 respectively) |
| `ga_strength` | 1a (M-1/M-2/M-3) | shadbala component + total values, vimshopaka bala values, ashtakavarga bindu values — **first successful live build ever for this writer; must complete without the ga_strength-substep failure seen in the 3 pre-0h attempts** | row-count cardinality (52/45/45/etc. — these are structural: N grahas × M components, not data-dependent) |
| `ga_sensitive` | 1d (M-9/M-10/M-11/V-6/V-7/M-16/D-9/D-10) | special lagna values, upagraha values, sensitive-point values (real PyJHora delegation); fabricated sphuta rows (pranapada/fertility/trikona-dasha) EXPECTED TO DROP toward 0 or vanish (B.10 floor, not fabricate) | — |
| `ga_vargas` | 1b (M-4/M-17/M-18) | ashtakavarga-in-vargas values, D60 deity/quality (NULL→real kroora/soumya via migration 430's table), compound-friendship-dependent dignity fields | `chart_divisionals` row COUNT should hold near 20,877 unless D60 deity rows that were previously skipped (deity=NULL, quality=NULL → `continue`, no row emitted) now emit — in which case a row-count INCREASE is expected and correct, not a regression |
| `ga_sade_sati` | 0d (already live) | nothing further this session | sade_sati_cycle count must hold at 160/160, zero duplicate cycles (migration 429's unique indexes still enforce this) |
| **estate-wide** | 1f (M-22/D-3/D-14/D-4) | `verification_pass_status` distribution shifts as more writers produce real (not vacuous) computations — expect FEWER rows stamped with the highest-confidence tier where the underlying computation was previously vacuous/placeholder, MORE rows honestly stamped at a lower tier or with a `documented_approximation`/floored status | the vocabulary itself (must remain within each table's CHECK-constraint-legal set — this is exactly what `test_verification_pass_status_vocab.py`, fixed earlier this session for lane 1b's D60 branch, guards) |

## §3 — Canary order (point 2 — mandatory, non-negotiable sequencing)

**Abhinandan (`1c826d5a-41cb-4450-b4dc-59d440e5f75a`) rebuilds FIRST, in full, through every gate in
§8, before `482012f1` is touched at all.** A writer bug during this session costs the CONTROL chart —
recoverable via the §4 snapshot and re-run — never the calibrated native chart. Only after Abhinandan's
full gate stack (FORENSIC 7/7 — n/a for Abhinandan specifically since FORENSIC anchors are native-chart-
specific, but the equivalent positional-core-untouched check applies — + TAP-3b + TAP-7 + the manifest
check in §2) passes clean does `482012f1` begin.

If Abhinandan's rebuild surfaces ANY out-of-manifest change or writer failure: **halt before touching
482012f1**, root-cause, fix if the fix is in-scope for this session (a writer bug) or escalate to the
native if it implicates the frozen orchestrator contract (per §N.2) — never proceed to the native chart
on an unexplained canary result.

## §4 — Pre-rebuild snapshot (point 3 — non-negotiable, before ANY execute_run this session)

**Corrected mechanics (native ruling, 2026-07-10 — `pg_dump` cannot row-scope via `WHERE`, and a
`--data-only` restore into already-populated tables duplicates rows rather than restoring state; both
are replaced below):**

- **Snapshot** — per chart-scoped table, CSV export via `\copy`:
  ```
  \copy (SELECT * FROM chart_facts WHERE chart_id IN ('1c826d5a-41cb-4450-b4dc-59d440e5f75a','482012f1-710e-4a25-994a-93821f5871aa')) TO 'chart_facts_pre.csv' CSV
  \copy (SELECT * FROM chart_dashas WHERE chart_id IN (...)) TO 'chart_dashas_pre.csv' CSV
  \copy (SELECT * FROM chart_divisionals WHERE chart_id IN (...)) TO 'chart_divisionals_pre.csv' CSV
  -- same pattern per bodha_*/kala_*/phala_*/mimamsa_* table actually populated for these two chart_ids
  \copy (SELECT * FROM asset_throughput) TO 'asset_throughput_pre.csv' CSV   -- small, whole-table fine
  \copy (SELECT * FROM build_runs) TO 'build_runs_pre.csv' CSV              -- small, whole-table fine
  ```
- **Restore path** (documented here BEFORE starting, not improvised later): per table, inside a
  transaction —
  ```
  BEGIN;
  DELETE FROM chart_facts WHERE chart_id IN ('1c826d5a-...','482012f1-...');
  \copy chart_facts FROM 'chart_facts_pre.csv' CSV
  COMMIT;
  ```
  (repeat per table, same chart_id scoping).
- **Rehearsal (mandatory, before the first live `execute_run` this session)**: dump and restore ONE
  small table (`asset_throughput`, whole-table, already the smallest candidate) against a genuinely
  disposable scratch state — confirm the `DELETE`+`\copy` round-trip reproduces byte-identical row
  counts and content before trusting this path for the real tables. An untested rollback path is the
  same bravado in a different costume, per the native's framing.
- Files stored outside the repo (production row data, not a versioned artifact); file paths + row
  counts per table logged in the run ledger as the rollback reference. **No execute_run call happens
  before this snapshot exists, is verified via a rehearsed restore, and its row counts are logged.**

## §5 — Quiescence (point 4 — expanded scope)

### §5.1 — Cloud Scheduler jobs (live-queried, `madhav-astrology` project, `asia-south1`)

| Job | Schedule | State | Pause for this session? | Why |
|---|---|---|---|---|
| `watchdog-reaper` | */5 min | ENABLED | **YES — highest priority.** | §1.1's diagnosis directly implicates this job's pre-0h-fix reaping as the cause of `ga_strength`'s repeated failures. Even with 0h's fix landed, a long single-substep writer (`ga_strength` ~11 min, no heartbeat) racing against a 5-minute-cadence reaper during THIS session's live rebuild is exactly the collision this session must not risk re-triggering. |
| `amjis-mv-refresh` | every 6h | ENABLED | **YES.** | Materialized-view refresh reading `chart_facts`/`chart_dashas` mid-rebuild risks reading a half-written state (delete-then-insert idempotency means a refresh landing between the DELETE and the INSERT sees a transient empty/partial set) and could itself lock rows this session's writers need. |
| `canary-battery-daily` | daily 06:00 UTC | ENABLED | **YES.** | Runs the frozen answer battery against prod. If it fires mid-rebuild it (a) grades against inconsistent/transitional data, producing a false-negative report that contaminates the next campaign's baseline exactly per the lineage-pinning discipline in §1.4, and (b) adds unrelated load during the single-writer window. |
| `panchanga-daily-refresh` | monthly | ENABLED | Optional — low collision risk (next fire is likely >24h out), but pause anyway for the session's duration since it touches `chart_facts` panchanga categories and the cost of pausing is zero. | Defense in depth. |
| `amjis-pending-stream-reaper` | */10 min | ENABLED | **NO — leave running.** | Operates on `pending_streams` (chat infrastructure), zero overlap with `chart_facts`/`chart_dashas`/`chart_divisionals` or the orchestrator's build-state tables. Pausing it has no benefit and (per register row O-2) it's already misconfigured against a dead URI, unrelated follow-up, not this session's concern. |
| `brahma-prahara-watchdog` | */15 min | **already PAUSED** | N/A | Pre-existing pause, unrelated to this session — confirmed, not touched. |

Pause via `gcloud scheduler jobs pause <job> --location=asia-south1`; un-pause the same 4 jobs
(`watchdog-reaper`, `amjis-mv-refresh`, `canary-battery-daily`, `panchanga-daily-refresh`) at session
close per §9 — record exact pause/resume timestamps in the run ledger.

### §5.2 — Stalled-agent / stale-lock sweep (expanded per point 4)

Swept at plan-authorship time: **clean**. `git worktree list` shows only the main worktree (all five
round-of-5 lanes' worktrees already removed this session); no stray `.claude/worktrees/*` directories;
no `git worktree`-scoped lock files; the only lock present is `.git/objects/maintenance.lock`, an
ordinary transient git-gc artifact, not a stale session lock. No background `claude` processes are
bound to this repo's worktrees (the other `claude`/`Antigravity` processes visible in `ps aux` belong to
unrelated concurrent IDE sessions/other projects, confirmed by absence from `git worktree list`). **Re-
run this exact sweep immediately before §4's snapshot** (state can change between planning and
execution) — this is the same class of hazard as the stray staged reversion caught and discarded
earlier this session in the `r6-3b-budgets` worktree; a stalled background Ring-2/verification agent
leaving uncommitted state in a worktree that's about to be used for the live rebuild is the specific
failure mode being guarded against.

## §6 — Execution order (both charts, per canary sequencing in §3)

Per-chart order, respecting `asset_registry.depends_on` (confirmed: `ga_dashas.depends_on=['ga_positions']`
only; `ga_structural.depends_on` includes `ga_dashas`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`,
`ga_sensitive`, `ga_strength`, `ga_vargas` — i.e. `ga_structural` must be LAST among the L1 set):

1. `ga_dashas` (1c's PyJHora dasha delegation)
2. `ga_sensitive` (1d — special lagnas/upagrahas/sensitive points)
3. `ga_strength` (1a — shadbala/vimshopaka/ashtakavarga; **watch this substep specifically** per §1.1)
4. `ga_vargas` (1b — D60 deities/ashtakavarga-in-vargas/compound friendship)
5. `ga_nakshatra` + `ga_panchanga` verification (native ruling A2 — `ga_nakshatra` is in **error** state
   on the native chart per §1.1 AND is a declared dependency of `ga_structural`; it was missing from the
   original order and is added here. `ga_panchanga` is already `lit` on both charts — re-verify it holds
   clean, don't skip the check just because it's not red.)
6. `ga_structural` (1e, on top of already-live 0c — depends on all of the above, including the two
   added in step 5)
7. `ga_sade_sati` — **must end this session lit, not left red.** Per native ruling A2: every asset
   §1.1 shows as `error`/`dormant` must end this session either genuinely rebuilt or explicitly explained
   — no red mark stands unaddressed. If a rebuild shows `ga_sade_sati`'s data is already correct (0d's
   fix landed live earlier this session; sade_sati_cycle held at 160/160 with zero duplicates) and the
   `error`/`dormant` throughput mark is stale pre-0h watchdog residue rather than a real fault, clear it
   via a verified rebuild (even if the rebuild is effectively a confirming no-op) and record that
   explicitly in the ledger — do not just leave the red mark and move on.
8. Cascade: mark every downstream L2 (Bodha)/L3 (Kāla)/L4 (Phala)/L5 (Mīmāṃsā) asset stale (same
   class of ~49-asset closure Phase-0 already executed once this session) and rebuild wave-parallel —
   these consume the L1 outputs above and are stale relative to Phase-1's real values the moment step 1
   runs. **Cascade gating (native ruling A3, replacing per-category manifest enumeration — the L2-L5
   surface is too large to hand-enumerate honestly)**: gate the cascade on (a) distribution/degeneracy
   checks — no attribution column collapses to a single value, no all-one-valence result set, the same
   TAP-7-style degenerate-distribution guard used elsewhere in this campaign; (b) row-count DIRECTION
   consistency with the L1 deltas feeding each asset (an L1 category that grew should not feed an L2
   asset whose corresponding row count silently shrank, absent an explained aggregation reason); (c) the
   §8 serving-behavior checks (round-of-5 lanes' behavior on real post-cascade data). **The cascade runs
   OLD L2+ composition/synthesis logic (Phase 2 hasn't landed yet) over NEW L1 values** — this is
   expected and must be recorded as such, not treated as a defect; expect golden-battery/digest content
   to shift as a direct, correct consequence of fresher L1 inputs flowing through unchanged L2+ logic.
   **Any post-rebuild battery/digest comparison happens only AFTER the full cascade completes for a
   chart, never mid-cascade** — a battery run against a chart with some but not all of its 49 downstream
   assets refreshed is comparing against an internally inconsistent state, not a real result.

Run this full 8-step sequence for **Abhinandan first** (§3). Only after its full §8 gate stack passes
does the identical 8-step sequence run for the **native chart**.

**Manual watchdog discipline while `watchdog-reaper` is paused (native ruling A4)**: with the reaper
paused per §5.1, a genuinely hung build has no automatic backstop — the conductor IS the watchdog for
this session's duration. Explicit expectations per step: `ga_strength` ~11 minutes nominal (per prior
timing evidence); any step running **>30 minutes** triggers live investigation of the writer's actual
logs/substep state (never a blind kill, never indefinite silent waiting). **Record every step's actual
wall-clock duration in the run ledger** — these become the calibrated timeout inputs for re-tuning the
now-fixed watchdog's threshold once it's re-enabled at session close (§9).

## §7 — Halt conditions (non-negotiable)

Halt immediately, on either chart, at any step, if:
- Any FORENSIC-7 anchor changes.
- Any `graha_position`/`graha_sign_attributes` row changes (longitude, sign, nakshatra, dignity basis).
- Any fact_category NOT listed in §2's manifest changes materially.
- `ga_strength` (or any other writer) fails a substep post-0h-fix — this is now a genuinely new signal,
  not the known pre-fix watchdog artifact, and must be root-caused before any retry.
- A row-count or value change in an "expected to change" category moves in a direction or magnitude
  that has no plausible astrological/computational explanation traceable to the specific lane's fix
  (e.g., `graha_yuddha_per_varga` diverging FURTHER between charts instead of converging would be a
  halt, not a pass, since §2 specifically predicts convergence).
- Any stale-lock/staged-reversion hazard reappears in a worktree being used for this session (per §5.2's
  standing lesson).

On halt: do not retry the same step blindly. Root-cause via the writer's own logs/error text first (the
established pattern all session: dict_row bug, dosha-catalog crash, watchdog staleness were each found
this way, not by re-running and hoping). If the root cause implicates the FROZEN orchestrator contract
(§N.2), stop and escalate to the native with the specific contract change needed — do not implement it
unilaterally.

## §8 — Gate stack (must ALL pass, per chart, before the canary can clear and again before the whole
session can close)

1. **FORENSIC 7/7** (native chart only — Abhinandan's canary check is the positional-core-untouched
   check, no FORENSIC-anchor-specific gate applies to a non-canonical control chart).
2. **TAP-3b recompute battery** — full re-derivation cross-check.
3. **TAP-7 distinctness gates** — confirms the two charts remain genuinely distinct (no shared-fallback
   contamination — the exact class of bug 0f's Chara Dasha fix (M-7/M-8) already proved absent; must
   hold after this rebuild too).
4. **Ring-3 prod probe sweep — expanded scope (point 7)**: not just this rebuild's own Phase-1 rows, but
   **ALL Phase-0 + Phase-1 register rows** (the full FIXED-this-campaign set: R-15/O-6/O-5/O-2/R-9/R-10/
   R-12/R-14/T-7/V-8/P-6/Y-1/Y-9/Y-7/D-13/D-2/V-13/V-1/G-7/D-1/V-9/V-11/V-12/M-7/M-8 from Phase 0, plus
   1b's M-4/M-17/M-18, 1a's M-1/M-2/M-3, 1d's M-9/M-10/M-11/V-6/V-7/M-16/D-9/D-10, 1e's M-12–M-15/M-19/
   M-20/V-5, 1c's M-5/M-6/M-21, 1f's M-22/D-3/D-14/D-4) — re-probed against the FRESHLY REBUILT data,
   since several of these were only verified against pre-Phase-1 data or via offline pytest.
5. **Round-of-5 lanes' behavior on rebuilt data** (point 7, second half): confirm 3a's param-echo fixes,
   3b's response-budget trimming, and 3e's honesty fixes (receipt integrity, pact_status, error
   classification) do not regress when the underlying row volumes change post-rebuild — e.g., 3b's
   `assess_career` budget trimming was verified against a synthetic 1.6MB-shaped payload; confirm it
   still trims correctly against the REAL post-rebuild payload shape (which may differ now that
   `ga_strength`/`ga_sensitive`/`ga_vargas` emit different row volumes), and 3e's `reconcileReceiptWithTrimReport`
   correctly downgrades any receipt whose backing array is genuinely trimmed to zero on real (not
   synthetic) data.
6. **§1.5's 3-flips**: X-5/R-10 re-confirmed PASS on rebuilt data; R-30/R-31 confirmed unchanged
   (correctly still open, correctly not masked by the rebuild).
7. **Zero out-of-manifest changes** (§2/§7).

Only when every one of these passes, on BOTH charts, does the session close. Un-pause the 4 schedulers
(§5.1), record the full window (start/end timestamps, snapshot file reference, every gate's verdict,
every register row re-confirmed or newly flipped) in the run ledger, and only then may Phase 2A/2B/2C
and Phase 3c/3d/3f begin — per the native's unchanged sequencing ruling.

## §9 — Post-session

- Un-pause `watchdog-reaper`, `amjis-mv-refresh`, `canary-battery-daily`, `panchanga-daily-refresh`.
- Record the snapshot file path + pre/post row counts for every touched table, both charts, in the run
  ledger — this IS the rollback path; keep it referenced, not just taken.
- Update `MARSYS_DEFECT_GAP_REGISTER_v2_0.md`: flip every Phase-1 register row (M-1 through M-22, V-1
  through V-13 as applicable, D-9/D-10, etc.) from "code merged, not yet live-verified" to
  `FIXED [verify-against: prod, R6 2026-07-10]` or equivalent, each with its own Ring-3 evidence pointer
  — no blanket flip without a per-row citation.
- Update `CURRENT_STATE_v1_0.md` per the standing governance discipline.
- **Then** spawn Phase 2A/2B/2C + Phase 3c/3d/3f in parallel, per the original brief's unchanged
  sequencing.

---

*End of REBUILD_SESSION_PLAN v1.0. This document is the Ring-3 comparison surface for the entire
rebuild session — do not judge a diff against intuition; judge it against §2.*
