# KĀLA READINESS AUDIT — STATE  (rewritten completely by every cycle)

**Position:** cycle 2 complete (2026-09-22). W1 is now fully DONE — all 14 W1 packets (F3, F4, F5,
F6, F7, F8, Domains A, B, D, G(pending), H, I, J) verified except Domain G, deferred to cycle 3 (see
below). REPAIR lane F1 also completed this cycle (fix authored, independently verified,
CI-wired, auto-merge armed) — ahead of schedule (charter allowed it to start in W1, serial). W2 is
next: T1–T6 + Domains C, F.
**Branch:** `l3/kala-readiness-audit` from `origin/main@20f4d02dc`. **Worktree:**
`/Users/Dev/madhav-l3/audit`. `origin/main` unchanged since seed — still `20f4d02dc` (this cycle's
PR #2706 is queued, not yet merged — see PRs below).

## Correction to cycle 1's packet table

Cycle 1's table listed "Domain D E G H I J" as one TODO row under W1. Re-reading the charter's own
wave list (`AUDIT_CHARTER.md` "Waves" section) confirms Domain **G** is NOT in the W1 list —
W1 = "domains A, B, D, E, G, H, I, J" is what cycle 1 literally wrote, but the CHARTER's actual W1
line reads "domains A, B, D, E, G, H, I, J" too (8 domains) while W2 = "domains C and F". So G *is*
W1-scoped per the charter. This cycle did NOT attempt Domain G (cross-campaign safety / Pūrṇa
lease protocol) — it remains the one open W1 domain for cycle 3, alongside Domain E which cycle 1
mis-filed as done-via-F6 (F6 covers deploy lag specifically; Domain E's full scope — deploy-gate
path patterns, `deployment-outcome` earned signal, merge queue, generated-artifact regeneration
protocol — is broader than F6 and was NOT separately attempted). **Correcting the record:
Domain E and Domain G are the two genuinely open W1 domains for cycle 3**, not zero.

## Cycle 2 — what happened

1. **PR/sync hygiene:** clean at cycle open — 0 PRs authored by this audit as of cycle 2 start
   (confirmed via `gh pr list --author "@me"` — the ~15 open PRs under that filter are all
   Pūrṇa/Codex campaign work, unrelated to this audit, none touch `l3/kala-*` or `l3/egate-*`
   branches). No root-level misplaced `audit/` directory found (self-heal check: clean).
2. **Wave picked:** remainder of W1 — F5, F7, Domains D, H, I, J (6 packets dispatched in parallel)
   — **plus** the REPAIR lane (F1), started this cycle per the charter's "may start in W1"
   allowance, done serially by the conductor itself (not a subagent) since it required DB
   read-only validation + a disposable local Postgres for the regression test, better suited to
   direct execution than delegation.
3. **Fan-out, attempt 1:** F7, Domain D, Domain H, Domain I, Domain J all completed cleanly on
   first attempt (7–14 min each, well-bounded). **F5 stalled** the same 600s no-progress watchdog
   cycle 1 hit on other packets — this time on a packet cycle 1 had *not yet written* a
   tightly-bounded brief for (F5's original brief lacked cycle 1's "small fixed command budget,
   one-shot queries only" language, since it was authored fresh this cycle before this note was
   internalized into every brief — lesson re-confirmed, now written into this cycle's own briefs
   below for cycle 3 to inherit literally, not just as a summary).
4. **F5 retry:** split into two independently-capped subagents (Part A: 11 assets + the 2 named
   divergences; Part B: 11 assets + retired `ka_gochara_sweep`), each with an explicit ≤25-tool-call
   ceiling. Both completed cleanly (22 and 7 tool calls respectively) and were merged into one
   `F5.md` deliverable by the conductor.
5. **REPAIR lane (F1) — completed end-to-end this cycle:**
   - Fixed `egate.sql`'s `frozen`/`route` CTEs and `capsule_audit.sql`'s §1/§2/§3 (defense-in-depth
     on §2 per Domain A's recommendation) to scope every read of
     `nirmana_elevation_campaign_events` to the currently-frozen `definition_revision`.
   - **Live-validated the fix against real production** (read-only, both files are pure `SELECT`):
     before the fix, `capsule_audit.sql` §3 reported L3 = 13 frozen (cross-revision-contaminated);
     after, L3 = 0 frozen — exactly matching the independently-known ground truth (frozen under
     `t3`: L0 0/40 · L1 0/19 · **L2 8/22** · L3 0/23 · L4 0/9 · L5 0/15). L2's 8 stayed correct
     both before and after (the one layer with real `t3`-scoped freezes) — strong evidence the fix
     is correct, not merely plausible.
   - Authored a regression test (`platform/tests/integration/nirmana_egate_definition_scope.db.test.ts`)
     that runs the REAL files via `psql` (not a reimplementation — both scripts use psql
     meta-commands a plain SQL client can't execute) against a disposable local Postgres. **Proved
     the test is a genuine regression guard, not a tautology:** ran it against the pre-fix files
     (via `git stash`) and confirmed it fails with the exact "BUG REPRODUCED" assertions; ran it
     against the post-fix files and confirmed 3/3 pass. Local disposable Postgres was started
     (`brew services start postgresql@15`), used, and fully torn down (database dropped, service
     stopped, symlink removed) before continuing — no state left behind.
   - Opened PR #2706. **Dispatched an independent verifier subagent** (did not author the fix) —
     verdict **VERIFIED-WITH-CONCERNS**: SQL logic and test field-index assertions both
     independently confirmed correct, but caught a real gap — the new test had no CI wiring
     (`describe.skipIf` meant it silently skipped on every CI run, providing zero automatic
     protection despite passing locally). **Fixed same cycle:** renamed the test's env var to
     reuse `NIRMANA_ELEVATION_TEST_DATABASE_URL` (same disposable DB as sibling
     `nirmana_elevation_asset_labels.db.test.ts`, isolated by its own literal `nirmana_evidence`
     schema) and added the explicit `npx vitest run .../nirmana_egate_definition_scope.db.test.ts`
     line to the same CI job step that already runs its sibling. Re-verified locally: 3/3 still
     pass. Pushed the fix, commented on the PR with the verifier's findings and the resolution,
     **armed auto-merge** (`mergeStateStatus: BLOCKED` pending CI at time of writing — not
     unusual, CI takes 6–14 min; not polled in-session per the no-idle law).
6. **Integrate:** every packet's headline claim independently spot-re-run by the conductor before
   being marked DONE (see each packet's note below + the specific commands re-run). One new
   cross-cutting finding surfaced and corroborated across two independent packets this cycle:
   **`ka_gochara`'s writer targets `kala_gochara_windows_v2` but its live consumer surface reads
   the un-suffixed `kala_gochara_windows`** — F5 found this from the consumer side; it directly
   corroborates cycle 1's F3 finding (seed vs strategy disagreement on this exact table) from the
   serving side. Two new genuinely-unresolved findings (`ka_tulana`, `ka_dasha_kala` consumer
   wrappers reading a neighboring asset's table, not their own) are flagged per §N.8, not asserted.
7. **Commit + push:** this cycle's commit on `l3/kala-readiness-audit` follows this file. PR #2706
   on `l3/egate-definition-scope` (separate branch) pushed twice this cycle, auto-merge armed.

## Observed at seed / carried forward (re-confirmed cycle 2 where re-touched)

| Fact | Value |
|---|---|
| `origin/main` | `20f4d02dc` (#2703) — still unchanged; PR #2706 queued, not yet merged |
| Leases on `origin/campaign-coordination` | not re-checked this cycle (no deploy dispatch attempted) |
| PR #2695 | not re-checked this cycle (F8 already DONE as of cycle 1, no new information) |
| Current campaign definition | `t3-2026-09-11-8b884eac` — **now independently re-confirmed twice**: once by cycle 1's DB query, once by this cycle's live before/after `capsule_audit.sql` re-run (F1 fix validation) |
| Total remote branches | **1060** (Domain I; cycle 1/seed's "~113" estimate corrected — off by ~9.4x). L3-name-matching subset: **138**. Both re-confirmed by the conductor via direct `git branch -r` count. |

## Cycle 2 findings summary (full detail in each deliverable / `_work` file)

- **F5 (consumer-path trace ×23) — DONE.** → `_work/F5.md`. 20/23 identities same-code-wired
  (11 high-confidence table-verified, 9 medium/surface-level). 1 retired asset (`ka_gochara_sweep`)
  confirmed correctly inert. **3 real findings:** `ka_gochara` writer/consumer table-name mismatch
  (`kala_gochara_windows_v2` vs `kala_gochara_windows` — corroborates cycle 1 F3); `ka_tulana` and
  `ka_dasha_kala` consumer wrappers read a neighboring asset's table with no evidence either
  writer's own output is served anywhere. The two originally-named divergences
  (`call_ephemeris_at_t`, `call_dasha_eligibility`) both CONFIRMED exactly as reported.
- **F7 (data census) — DONE.** → `_work/F7.md`. 37 `kala_*` tables censused for the canonical
  chart. Item 4a (`kala_activation_predicates` ≈50,678) CONFIRMED exact, plus a new sub-finding:
  79 rows (0.156%) have an MSR `signal_id` that doesn't resolve against `bodha_msr_signals`. Item
  4b CORRECTED — the ~8.6M-row table is `kala_field` (8,570,075 rows), not `kala_field_snapshots`.
  Item 4c CONFIRMED (0 rows for canonical chart) with a nuance: the table isn't globally empty (1
  row, different chart). Item 6 (`ga_dashas_replacement_in_progress`) COULD-NOT-VERIFY (live
  API-response claim, not a DB fact) — indirect signal checked instead (`chart_dashas` has 483,870
  rows for the canonical chart, ruling out "empty table" as the cause). New finding: **9 of 37**
  `kala_*` tables are non-empty globally but have **zero rows for the canonical chart** — every row
  belongs to a different chart (mostly `1c826d5a-…`, Abhinandan Mohanty).
- **Domain D (generation/W1 substrate) — DONE.** → `_work/DOMAIN_D.md`. **NEEDS DECISION.**
  Migrations 1035/1036 install a real, well-built exact-context generation/snapshot/rollback
  substrate with genuinely-enforced `session_user = 'data_plane_builder'` (write) /
  `data_plane_migrator` (rollback) gating — confirmed by direct quote, spot-re-verified by the
  conductor. But it is **L1/L2-only by explicit self-declaration** ("no L3 activation authority is
  introduced") and **entirely unexercised in production** (0 rows in every generation/head table,
  both layers). No L3-equivalent generation-head table exists. First-ever-generation abort has no
  dedicated rollback (the one rollback function requires an already-complete head to roll back
  from) — real recovery is resume-the-same-generation-id, not rollback; orphaned partial state from
  an abandoned (not resumed) first build has no reclaim function and persists forever, though it is
  never served to readers.
- **Domain H (hub/invalidation hazards) — DONE.** → `_work/DOMAIN_H.md`. **NEEDS DECISION.** All 7
  named hub modules located and their importer sets confirmed/corrected with file:line evidence
  (spot-re-verified by the conductor: `ph_nimitta`'s cross-layer `ka_dasha_kala` import confirmed
  exact). `ka_gochara` and `ka_sangam` are the two highest-coupling assets (each depends on 3 of
  the 7 hubs). `_local_import_files`/`get_writer_source_hash` is a real, correct transitive-closure
  code-identity detector, wired into a working CI staleness check and a hard dispatch-time abort —
  genuinely solid, not theater. **The gap:** neither of those two consumers marks any already-built
  DB row stale or schedules a rebuild — `compute_downstream_closure` (the only real data-staleness
  mechanism) is scoped strictly to `asset_registry.depends_on` edges between *registered assets*,
  and none of the 7 hubs are registered assets, so a hub-only code edit has no automated bridge to
  "these sibling writers' rows are now stale." That bridge is currently a manual grep-and-read
  exercise — this audit packet's own method.
- **Domain I (source inventory) — DONE.** → `_work/DOMAIN_I.md`. **Methodological catch, fixed
  first:** the audit worktree's clone was shallow (53 commits only), which would have falsely
  flagged nearly every branch as "undelivered" via bogus no-merge-base errors — fixed with
  `git fetch --unshallow` before any content diff. **Branch count corrected: 1060 total** (not
  ~113 — conductor independently re-confirmed via direct count, 1060 vs Domain I's own 1059, a
  trivial 1-branch timing difference), **138 L3-name-matching** (not ~113 either). Sampled 15 of
  the 137 L3-named branches, prioritized toward the hardest assets (kshetra/sangam/gochara/kala):
  14/15 DELIVERED (content-identical to `origin/main`, mostly via PR #2607's squash-delivery, the
  same one cycle 0/seed had wrongly called "stranded" before), 1/15 STALE (a pre-fix vocabulary bug
  a later commit already corrected on main), 0/15 GENUINELY_UNDELIVERED. Honest scope statement:
  ~11% of L3-named branches sampled, non-random (worst-case-first), no extrapolation claimed for
  the other 122.
- **Domain J (session/tooling) — DONE.** → `_work/DOMAIN_J.md`. **NOT READY** (2/5 sub-checks
  READY, 3 NOT READY). READY: stream worktrees (the plan's actual commitments — integration
  worktree + 8 preservation branches pushed — both live-confirmed); credential routes (`dbenv.sh`/
  `dbenv_builder.sh` exist, structurally route through `gcloud secrets`, no value ever printed).
  NOT READY: the `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE` transcript-persistence hazard is named
  only in the audit's own prompt text, nowhere mechanically enforced; `.claude/settings.local.json`
  is `{"dangerouslySkipPermissions": true}` with **no** allowlist/denylist — every safety
  constraint this audit operates under (read-only, no git mutations, no credential printing) is
  enforced by prompt instruction only, zero harness-level control (conductor spot-confirmed the
  file's exact content); the DR runbook correctly scopes `kala_*` tables into its 24h RPO tier but
  self-documents PITR as disabled and no restore drill ever run for that tier.

## Packet table

| Packet | Wave | Status | Output | Notes |
|---|---|---|---|---|
| F3 four-way DAG reconciliation | W1 | **DONE** | `KALA_DAG_RECONCILIATION_v1_0.md` | verified cycle 1 |
| F4 privilege matrix | W1 | **DONE** | `KALA_PRIVILEGE_MATRIX_v1_0.md` | verified cycle 1; repair candidate queued |
| F5 consumer-path trace ×23 | W1 | **DONE** | `_work/F5.md` | verified cycle 2; 3 real findings, feeds T1 |
| F6 deploy lag | W1 | **DONE** | `_work/F6.md` | verified cycle 1; feeds W4 synthesis |
| F7 data census | W1 | **DONE** | `_work/F7.md` | verified cycle 2; aggregates only |
| F8 PR #2695 state | W1 | **DONE** | `_work/F8.md` | verified cycle 1; feeds W4 synthesis |
| Domain A | W1 | **DONE** | `_work/DOMAIN_A.md` | verified cycle 1; NOT READY verdict |
| Domain B | W1 | **DONE** | `_work/DOMAIN_B.md` | verified cycle 1; READY verdict |
| Domain D | W1 | **DONE** | `_work/DOMAIN_D.md` | verified cycle 2; NEEDS DECISION |
| Domain E | W1 | **TODO** | `_work/DOMAIN_E.md` | **corrected: NOT actually done via F6** — F6 only covers deploy lag, not E's full scope (deploy-gate patterns, `deployment-outcome` signal, merge queue, artifact regen protocol) |
| Domain G | W1 | **TODO** | `_work/DOMAIN_G.md` | cross-campaign safety / Pūrṇa lease protocol — not attempted cycle 1 or 2 |
| Domain H | W1 | **DONE** | `_work/DOMAIN_H.md` | verified cycle 2; NEEDS DECISION |
| Domain I | W1 | **DONE** | `_work/DOMAIN_I.md` | verified cycle 2; caught+fixed a shallow-clone methodology bug |
| Domain J | W1 | **DONE** | `_work/DOMAIN_J.md` | verified cycle 2; NOT READY |
| F1 egate repair + sibling sweep | REPAIR | **DONE** | PR #2706 (`l3/egate-definition-scope`) | fixed, live-validated, tested, independently verified, CI-wired, auto-merge armed — queued, not yet merged |
| F2 inheritance quantification | W2 | TODO | `_work/F2.md` | options with cost/risk; do NOT choose |
| T1 traceability ×3 clusters | W2 | TODO | `KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md` | F3+F5 both now available — unblocked for cycle 3 |
| T2 proving journeys | W2 | TODO | `KALA_PROVING_JOURNEYS_BASELINE_v1_0.md` | |
| T3 acceptance-regime mapping | W2 | TODO | `KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` | Domain A's capsule_audit finding + this cycle's live F1 before/after numbers are directly relevant input |
| T4 brief conformance | W2 | TODO | `KALA_BRIEF_CONFORMANCE_v1_0.md` | Gochara v0.3 present |
| T5 tensions · T6 boundaries | W2 | TODO | `_work/T5.md`, `_work/T6.md` | |
| Domains C F | W2 | TODO | `_work/DOMAIN_<x>.md` | C on a disposable DB only — same pattern this cycle proved out for the F1 regression test |
| §5 execution/velocity design | W3 | TODO | `KALA_EXECUTION_DESIGN_v1_0.md` | |
| §6 setup + runbook | W3 | TODO | `KALA_CAMPAIGN_RUNBOOK_v1_0.md` | tested, not asserted |
| Readiness audit synthesis | W4 | TODO | `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` | needs Domains E+G + rest of W2 first |
| Verdict + native decision list | W4 | TODO | in the readiness audit + this file's list below | F2 first |

## In flight

- **PR #2706** (`l3/egate-definition-scope`, F1 repair): OPEN, MERGEABLE, auto-merge armed
  (`mergeMethod: MERGE`, merge-queue policy). `mergeStateStatus: BLOCKED` as of last check —
  expected while CI runs (6–14 min typical); not polled in-session. Cycle 3 should check
  `gh pr view 2706 --json state,mergeStateStatus` first thing and re-arm auto-merge if a push
  (there won't be one) or a queue eviction dropped it.
- No deploy dispatched this cycle. No lease claimed or held on `origin/campaign-coordination`.

## Budget

| Resource | Used | Ceiling |
|---|---|---|
| Cycles | 2 | 40 |
| Subagent dispatches | 10 (cycle 1) + 9 (cycle 2: 6 initial + 1 failed F5 + 2 F5 retries + 1 independent verifier = 10, corrected count below) | 120 |
| Subagent dispatches (cycle 2 exact) | 6 initial (F5, F7, D, H, I, J) + 1 F5 stall (no retry-of-same-brief, counted once) + 2 F5-split retries + 1 independent PR verifier = **10** | — |
| PRs opened | 1 (#2706, this cycle) | 6 |
| Deploy dispatches | 0 | 2 |
| Production mutations | 0 | **0** |
| Local disposable Postgres instances started/stopped | 1 (`postgresql@15` via brew, fully torn down) | n/a — local-only, not production |

## Native decision list (accumulates, ordered by work unblocked)

1. **F2** — how does definition `t3` relate to freezes recorded under superseded definitions?
   (still to be quantified — cycle 3+ packet, unstarted). This cycle's F1 fix makes the *tooling*
   trustworthy for whichever answer is chosen, but does not itself answer the question.
2. **F4 repair candidate** — grant `SELECT` on `bg_transit_moorti`, `phala_rectification`,
   `bg_synthetic_cohort`, `bg_synthetic_cohort_md` to `data_plane_builder`. Small, targeted,
   unblocks `ka_moorti_nirnaya` and `ka_kshetra` builds today. Not yet authorized or migrated.
3. **F8 / PR #2695** — needs either the Pūrṇa-owned `BEYOND_ACARYA_ACCEPTANCE_v5.json` baseline
   regeneration or an explicit scoped governance override. Unchanged this cycle.
4. **Domain A / capsule_audit.sql** — **RESOLVED THIS CYCLE.** Fixed in the same PR as F1
   (#2706), same defect class, same fix shape, as recommended in cycle 1's note.
5. **F5's `ka_gochara` table-name mismatch** — writer targets `kala_gochara_windows_v2`, live
   consumer surface reads `kala_gochara_windows`. Needs a native/owner ruling: is this a stalled
   cutover (fix the consumer to read `_v2`), an intentional dual-table design (document it), or
   evidence the "W6.4 cutover" label in the consumer file is simply wrong? Directly relevant to
   Q1 in the elevation plan's native-question list per cycle 1's carried-forward strategy tensions.
6. **F5's `ka_tulana` / `ka_dasha_kala` consumer-table gaps** — both assets' serving wrappers read
   a different asset's table, with no evidence either writer's own output is consumed anywhere.
   Needs a deeper trace (this audit's bounded scan could not resolve it) before T1's traceability
   matrix can honestly mark `CONSUMER_INTEGRATED` for either.
7. **Domain D / Domain H** — both landed NEEDS DECISION, not a blocking item on their own, but
   both feed directly into §5's execution/velocity design (W3): does the campaign adopt the
   1035/1036 generation-head pattern for L3, or rely on `asset_throughput`/`build_runs` alone? Does
   `asset_registry` need a way to declare non-asset code hubs so `compute_downstream_closure` can
   see them? Both are design decisions for W3, not yet due for a native ruling.

## Known traps encountered this cycle (add to future subagent briefs — carried forward from cycle 1, re-confirmed)

- **Unconstrained subagents still stall.** Even with cycle 1's lesson nominally known, an F5 brief
  authored fresh this cycle without explicitly inlining "small fixed command budget, one-shot
  queries only, cap output with head -N, ≤N tool calls total" stalled the exact same way. **Do not
  rely on remembering the lesson — copy the literal constraint text into every W1/W2 brief from the
  template this cycle's retries used** (see the F5 Part A/B prompts in this cycle's transcript for
  the exact wording that worked: explicit numeric tool-call ceiling, not just "keep it short").
- **Local disposable Postgres is available and viable for regression tests that need a real DB.**
  `brew services start postgresql@15` (already installed, just not running) worked cleanly for
  proving the F1 regression test genuinely fails pre-fix and passes post-fix — a real TDD-style
  proof, not just "the test looks right." Remember to fully tear down afterward (drop DB, stop
  service, remove any `node_modules` symlink used to run vitest from a fresh worktree without a
  full `npm install`) — done this cycle, left no residue.
- **A new worktree has no `node_modules`.** Symlinking `platform/node_modules` from the main audit
  worktree (`ln -s /Users/Dev/madhav-l3/audit/platform/node_modules <new-worktree>/platform/node_modules`)
  is a fast way to run `npx vitest`/`npx eslint`/`npx tsc` in a freshly created repair worktree
  without a full `npm ci`. Remove the symlink before considering the worktree "clean" — it's not
  something to commit and isn't needed once local testing is done.
- **`.db.test.ts` files are silent no-ops without explicit CI wiring** — `describe.skipIf(!ENV_VAR)`
  means an unwired test reports 0/skipped forever, never a failure, so CI stays green regardless of
  whether the test would pass or fail. Always check `.github/workflows/ci.yml` for an explicit
  `npx vitest run tests/integration/<exact-file>.db.test.ts` line referencing your new test by name
  — grep for the file's basename in `ci.yml`, don't assume a `describe.skipIf` guard plus an env
  var name is sufficient (this cost a full independent-verification round-trip this cycle; check it
  before opening the PR next time, not after).
