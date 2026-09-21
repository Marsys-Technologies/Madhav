# KĀLA READINESS AUDIT — STATE  (rewritten completely by every cycle)

**Position:** cycle 8 complete (2026-09-22). All twelve §7 deliverables are content-complete
(ten named files + verdict/decision list folded into `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md`'s
final section). Decision-list item 18 (the one remaining open follow-up identified by cycle 7) is
now **discharged**: `capsule_audit.sql` was re-run live under its now-fixed scoping, Domain A's
verdict flipped NOT READY → READY (as an instrument), and its corrected output was folded into
decision-list item 1 as independent corroboration. **What remains before `AUDIT_DONE` can honestly
be written: three local commits (cycle 7's `bc617d9db` + `84efeb02a`, cycle 8's `3d9605b79`) still
have not reached `origin` — two push attempts this cycle were both rejected identically
(`GH006`, branch locked by PR #2707's entry into GitHub's merge queue), and per the no-idle law a
third identical attempt was not made.** This is the only reason this cycle does not print
`AUDIT COMPLETE`.

**Branch:** `l3/kala-readiness-audit`. **Worktree:** `/Users/Dev/madhav-l3/audit` (persistent
across cycles — not disposable; local-only commits are safe here between cycles).

## Cycle 8 — what happened

1. **PR/sync hygiene:**
   - `git fetch origin l3/kala-readiness-audit` → origin still at `98be7fd33` (cycle 6's last
     push); local `HEAD` was 2 commits ahead (`bc617d9db`, `84efeb02a`, both from cycle 7,
     unpushed per cycle 7's own note).
   - **PR #2707** (this audit's cumulative closure docs PR): `OPEN`, `mergedAt: null`. Checked the
     actual merge-queue entry via GraphQL (`mergeQueueEntry { position state estimatedTimeToMerge
     }`) rather than relying on `mergeStateStatus` alone — returned `position: 1`, `state:
     AWAITING_CHECKS`, `estimatedTimeToMerge: 798` (~13 min). `gh pr checks 2707` showed all
     required checks `pass`, only the known `skipping` gates (TAP-5/7+S-13, Census Battery,
     boot-time pointer validation, the native-only MCP smoke battery) non-pass. This matches the
     charter's own "CI here takes 6-14 min, not a stall" precedent exactly — no root-cause chase
     needed, this is the queue doing its job.
   - **Attempted `git push origin l3/kala-readiness-audit` twice this cycle** (once before this
     cycle's new work, once after committing it) — **both rejected identically**: `GH006,
     Protected branch update failed ... A pull request for this branch has been added to a merge
     queue. Branches that are queued for merging cannot be updated.` Per the charter's no-idle law
     ("two identical failures stop that attempt... never a third identical attempt"), did **not**
     attempt a third push this cycle. This is an external branch-level lock, not a bug in anything
     this session did — the fix is the queue finishing, not a different push invocation.
   - **PR #2695 (F8):** re-checked; `mergeStateStatus` now reads `BLOCKED` (was `UNKNOWN` as of
     cycle 7) — noted as a minor fact update, substance unchanged: still `OPEN`, still unmerged,
     still poisoning provenance for any dispatch that would touch it.
   - **Deploy-sync table** (required every cycle, read-only `gcloud run services describe`, no
     dispatch): all three services live in `asia-south1` (prior cycles' region guesses were
     wrong; discovered the correct region via `gcloud run services list` first).

     | Surface | Deployed revision SHA | vs `origin/main` (`9b3c3b219`) | Deployable drift? |
     |---|---|---|---|
     | `amjis-web` | `9b3c3b219` | exact match | None — at HEAD |
     | `amjis-mcp` | `09d998940` (PR #2698) | behind | **No** — `git log 09d998940069..origin/main -- platform-mcp/` returns zero commits |
     | `amjis-sidecar` | `09d998940` (PR #2698) | behind | **No** — same check against `platform/python-sidecar/` returns zero commits |
     | builder image (`platform/python-sidecar/Dockerfile.pipeline`) | covered by the sidecar path check above | behind | **No** — same zero-commit result |

     **No deploy dispatched this cycle** — no genuine deployable drift exists on any surface
     (MCP/sidecar are behind by SHA but byte-identical in content for their own paths since the
     last deploy; redeploying now would produce the same artifact). This preserves both remaining
     deploy-dispatch budget slots.

2. **Discharged decision-list item 18** (the one substantive piece of unfinished work cycle 7
   flagged, distinct from pure push mechanics — this justified doing real audit work this cycle,
   not just retrying a push). Read `platform/scripts/nirmana/capsule_audit.sql` in full to confirm
   the F1-class fix covers all three sections (§1/§2/§3 each join on `WHERE definition_revision =
   (SELECT definition_revision FROM frozen_def)`), then ran it live, read-only
   (`source dbenv.sh`; role `amjis_app`; `psql -f platform/scripts/nirmana/capsule_audit.sql`):

   ```
   §1 (incomplete evidence chain): 0 rows
   §2 (identity separation): 11 rows, all verdict = 'ok'
   §3 (per-layer, t3-scoped): L0=0/40 L1=0/19 L2=8/22(36.4%) L3=0/23 L4=0/9 L5=0/15 frozen — 8/128 total (6.3%)
   ```

   **Domain A's instrument verdict flips NOT READY → READY**: the tool can now genuinely
   distinguish "verified under `t3`" from "verified at some point, under some definition, ever" —
   the exact gap its original NOT READY verdict identified is closed. **But the correctly-scoped
   output is itself a severe finding, not a clean bill of health:** under the old unscoped
   aggregation §3 read L3 as 13/23 frozen (56.5%); correctly scoped, **L3 is 0/23 frozen under
   `t3`** — every prior "13 frozen L3 assets" reading was cross-definition contamination. This
   independently corroborates (a second instrument, a different query shape) F2's and the
   readiness query's own finding that 22/23 assets read `NOT_READY-BLOCKED-ANCESTORS` with zero
   READY-shaped rows — raising confidence this is the campaign's genuine current position, not an
   artifact of one query's construction. Folded into decision-list item 1, not left as a
   standalone new item.

   Updated in place: `_work/DOMAIN_A.md` (addendum appended), `KALA_ENVIRONMENT_READINESS_AUDIT_
   v1_0.md` (Domain A section verdict + new addendum block, §2b split-verdict text, decision-list
   items 1 and 18, frontmatter scope note, conductor spot-verification log, closing footer).

3. **Flagged one stale cross-reference found while verifying item 18** (not itself a defect in the
   audit, but worth recording so a future reader isn't misled): `KALA_ACCEPTANCE_REGIME_MAPPING_
   v1_0.md` §5 states "neither `egate.sql` nor `capsule_audit.sql` contains the string
   `definition_revision`" — this was **true when that T3 packet was authored** (before PR #2706
   merged) but is now stale, since PR #2706 is on `main` as of cycle 6. Per the archival/
   retain-in-place hygiene policy, did not rewrite the historical claim — appended a short
   "STALE as of cycle 8" note pointing to the current authoritative record instead. That same T3
   packet's own §5 worked example, notably, had *already independently reproduced* the "0 scoped"
   L3 figure via a hand-rolled equivalent query before PR #2706 merged — this cycle's live run of
   the actual (now-fixed) tool confirms that figure was correct, not a coincidence.

4. **No new wave dispatched, no subagents spawned this cycle.** The only substantive open item
   (decision-list item 18) was a single, mechanical, read-only SQL re-run plus a bounded set of
   doc edits — following this audit's own established precedent (cycle 6's F1 grep-count
   re-verification, cycle 7's Domain F path-correction), work of this shape is done directly by
   the conductor rather than delegated, since delegating a single deterministic query and citing
   its own output adds a verification hop without adding coverage. All ten named deliverables plus
   verdict/decision list remain otherwise unchanged from cycle 7 — **no new wave is eligible**
   until origin catches up and a human/native reviews the merged result.

5. **Commit — pushed 0 of 3 pending commits this cycle (external block, not this cycle's
   action).** Committed this cycle's Domain A re-run + T3 stale-flag + deploy-sync findings as
   `3d9605b79`, on top of cycle 7's `bc617d9db`/`84efeb02a`. Working tree clean after commit. Both
   push attempts (before and after this commit) rejected identically per item 1 above.

## Cycle 8 spot-verification / direct-work log (conductor; no subagents dispatched this cycle)

- **Merge-queue state, precisely** (not previously checked via the queue-specific API): GraphQL
  `mergeQueueEntry` on PR #2707 → `position: 1`, `state: AWAITING_CHECKS`,
  `estimatedTimeToMerge: 798`. Confirms "in flight, not stalled" with a number, not just a status
  string.
- **`capsule_audit.sql` full-file read** (not just `grep -c`): confirmed by direct inspection that
  all three sections join on the `frozen_def` CTE with `WHERE definition_revision = (SELECT
  definition_revision FROM frozen_def)` — §1 and §3 carry explicit "F1-class fix"/"F1 fix" inline
  comments; §2 uses the identical CTE pattern without its own comment (matches cycle 7's own
  correction of the line-number citation, re-confirmed, not re-litigated).
- **Live re-run of `capsule_audit.sql`** (see item 2 above) — first time this exact tool has been
  executed live end-to-end by this audit, as opposed to grepped for scoping-string presence.
- **`git log 09d998940069..origin/main -- platform-mcp/`** and the same for
  `platform/python-sidecar/` → both zero commits, confirming no deployable drift on either surface
  despite the SHA gap.
- **Region correction for `gcloud run services describe`**: prior assumption (`us-central1`) was
  wrong; `gcloud run services list` shows all three services in `asia-south1`. Recorded as a new
  known trap below so a future cycle doesn't re-discover this by trial and error.

No claim independently checked this cycle failed verification.

## Observed at seed / carried forward (re-confirmed cycle 8 where re-touched)

| Fact | Value |
|---|---|
| `origin/main` | `9b3c3b219` (#2706, F1 repair) — unchanged since cycle 6; re-confirmed cycle 8 |
| Current campaign definition | `t3-2026-09-11-8b884eac` — unchanged |
| PR #2706 (F1 repair) | MERGED. No further action. |
| PR #2707 (this audit's cumulative closure docs PR — still does NOT contain cycles 7 or 8's commits) | OPEN, in GitHub's merge queue at position 1, `state: AWAITING_CHECKS`, ETA ~13 min at last check, all required checks `pass` |
| PR #2695 (F8) | OPEN, `mergeStateStatus: BLOCKED` (was `UNKNOWN` as of cycle 7) — unmerged either way |
| `kala_activation`/`kala_convergence` for canonical chart | 0 rows each — root cause fully diagnosed (cycle 6), unresolved (native decision list item 4) |
| `ka_gochara_v3_century_materialize` BUILD-PROTECTED guard | Still live, unresolved (native decision list item 7) |
| `kala_timeline_spec` vs `kala_timeline` | Two similarly-named tables, only one live (`kala_timeline_spec`, written by `ka_kshetra`); `kala_timeline` fully DARK — unchanged since cycle 7 |
| Safety-exclusion coverage gap | `detectMortalityExclusion` wired into only 2 of 9 registered `kala_views` tools — unchanged since cycle 7, native decision list item 12 |
| **NEW this cycle — Domain A instrument verdict** | READY (was NOT READY pre-F1-fix). `capsule_audit.sql` §1/§2/§3 all now genuinely `t3`-scoped and live-confirmed. |
| **NEW this cycle — true L3 frozen count under `t3`** | **0 of 23** (not 13/23 as the pre-fix unscoped aggregation had shown). All 8 of the campaign's `t3`-scoped `asset_frozen` events belong to L2. Corroborates F2/readiness-query's 22/23 `NOT_READY-BLOCKED-ANCESTORS` finding via a second, independent instrument. |
| **NEW this cycle — deploy region** | All three Cloud Run services (`amjis-web`, `amjis-mcp`, `amjis-sidecar`) live in `asia-south1`, not `us-central1`. |
| **NEW this cycle — deploy-sync table** | `amjis-web` at `origin/main` HEAD exactly; `amjis-mcp`/`amjis-sidecar` behind by SHA (`09d998940`, PR #2698) but zero content drift on their own paths — no deploy dispatched, none needed. |

## Packet table

| Packet | Wave | Status | Output | Notes |
|---|---|---|---|---|
| F1 egate repair + sibling sweep | REPAIR | **DONE** | PR #2706 (merged) | unchanged |
| F2 inheritance quantification | W2 | **DONE** | `_work/F2.md` | unchanged |
| F3 four-way DAG reconciliation | W1 | **DONE** | `KALA_DAG_RECONCILIATION_v1_0.md` | unchanged |
| F4 privilege matrix | W1 | **DONE** | `KALA_PRIVILEGE_MATRIX_v1_0.md` | unchanged |
| F5 consumer-path trace ×23 | W1 | **DONE** | `_work/F5.md` | unchanged |
| F6 deploy lag | W1 | **DONE** | `_work/F6.md` | unchanged |
| F7 data census | W1 | **DONE** | `KALA_DATA_CENSUS_v1_0.md` | unchanged |
| F8 PR #2695 state | W1 | **DONE** | `_work/F8.md` | `mergeStateStatus` now `BLOCKED` (was `UNKNOWN`), still unmerged |
| Domain A | W1 | **DONE**, re-verified cycle 8 | `_work/DOMAIN_A.md` | **verdict flipped NOT READY → READY** (instrument now genuinely scoped); output corroborates item 1 |
| Domain B | W1 | **DONE** | `_work/DOMAIN_B.md` | unchanged |
| Domain C | W2 | **DONE** | `_work/DOMAIN_C.md` | unchanged |
| Domain D | W1 | **DONE** | `_work/DOMAIN_D.md` | unchanged |
| Domain E | W1 | **DONE** | `_work/DOMAIN_E.md` | unchanged |
| Domain F | W2 | **DONE** | `_work/DOMAIN_F.md` | unchanged since cycle 7's correction |
| Domain G | W1 | **DONE** | `_work/DOMAIN_G.md` | unchanged |
| Domain H | W1 | **DONE** | `_work/DOMAIN_H.md` | unchanged |
| Domain I | W1 | **DONE** | `_work/DOMAIN_I.md` | unchanged |
| Domain J | W1 | **DONE** | `_work/DOMAIN_J.md` | unchanged |
| T1 traceability ×3 clusters | W2 | **DONE** | `KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md` | unchanged |
| T2 proving journeys | W2 | **DONE** | `KALA_PROVING_JOURNEYS_BASELINE_v1_0.md` | unchanged |
| T3 acceptance-regime mapping | W2 | **DONE** | `KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` | one stale cross-reference flagged in place this cycle (§5, pre-PR-#2706 grep observation) — substance unaffected |
| T4 brief conformance | W2 | **DONE** | `KALA_BRIEF_CONFORMANCE_v1_0.md` | unchanged |
| T5 tensions | W2 | **DONE** | `_work/T5.md` | unchanged |
| T6 boundaries | W2 | **DONE** | `_work/T6.md` | unchanged |
| §5 execution/velocity design | W3 | **DONE** | `KALA_EXECUTION_DESIGN_v1_0.md` | unchanged |
| §6 setup + runbook | W3 | **DONE** | `KALA_CAMPAIGN_RUNBOOK_v1_0.md` | unchanged |
| Readiness audit synthesis | W4 | **DONE** | `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` | updated cycle 8: Domain A section, §2b, decision-list items 1+18, frontmatter, spot-verification log, footer |
| Verdict + native decision list | W4 | **DONE** | folded into `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md`'s final section | item 18 discharged, item 1 strengthened with cycle-8 corroboration; verdict itself (GO-WITH-CONDITIONS strategy / split NO-GO+GO environment) unchanged |

## In flight

- **PR #2706** (F1 repair): MERGED. No further action.
- **PR #2707** (cumulative closure docs PR — still does NOT contain cycles 7 or 8's commits): OPEN,
  in GitHub's merge queue at position 1, `state: AWAITING_CHECKS`, ETA ~13 min at last check, all
  required checks `pass`. **Will very likely merge on its own before the next cycle starts** — no
  action needed to make that happen.
- **THREE unpushed local commits** sit on top of `98be7fd33` in this persistent worktree:
  `bc617d9db` (cycle 7 W4 close), `84efeb02a` (cycle 7 push-status correction), `3d9605b79`
  (cycle 8 item-18 discharge). **Next cycle's mandatory first action, in order:**
  1. `git fetch origin l3/kala-readiness-audit && git log origin/l3/kala-readiness-audit -1`.
  2. `gh pr view 2707 --json state,mergedAt` — has it merged since this cycle's close?
  3. **If merged:** `origin/l3/kala-readiness-audit` will have advanced (fast-forwarded into
     `main`, and depending on repo settings the branch ref may or may not still exist). Rebase
     these three local commits onto the new state (or, if the branch ref is gone, push this
     worktree's content as a fresh branch and open a **new** PR for cycles 7+8's deliverables —
     do **not** force-push, do **not** delete/recreate the branch without first confirming
     origin's exact post-merge state). This satisfies "Done" for a *new* docs PR.
  4. **If still queued/open:** try `git push origin l3/kala-readiness-audit` exactly **once**. If
     it succeeds, proceed to check whether all twelve deliverables are now live on `main` (or
     queued clean in a PR) and, if so, write `AUDIT_DONE`, commit, push, print `AUDIT COMPLETE`.
     If it fails identically a third calendar-time-separate time (i.e., this would be the third
     attempt across cycles 7-8-9), do **not** retry a fourth time in that same cycle — record it,
     move to any other eligible work, and let the queue keep processing; the ETA figures observed
     so far (798s at cycle 8's check) suggest this should resolve well within a cycle or two.
- No deploy dispatched this cycle (see deploy-sync table above — no genuine drift). No lease
  claimed or held on `origin/campaign-coordination`.
- **No new wave is eligible.** All content-complete deliverables are unchanged except the item-18
  discharge recorded above. The only remaining work is push/PR mechanics.

## Budget

| Resource | Used | Ceiling |
|---|---|---|
| Cycles (supervisor numbering) | 8 (of which 6 have actually closed with a local commit: 1, 2, 3, 6, 7, 8) | 40 |
| Subagent dispatches | 34 (cycles 1-6) + 2 (cycle 7, W4, both foreground) + 0 (cycle 8, direct conductor work only) = **36** | 120 |
| PRs opened | 2 (#2706 merged, #2707 still open — no new PR opened cycle 8, still targeting #2707 once pushable) | 6 |
| Deploy dispatches | 0 | 2 |
| Production mutations | 0 | **0** |
| Local disposable Postgres instances started/stopped | 2 (cycles 2 and 4), both fully torn down — none this cycle | n/a — local-only |

## Native decision list

**Unchanged in ranking from cycle 7's 20-item list in `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md`'s
"Readiness verdict and native decision list" section — read it there, not here.** The only content
change this cycle: item 1 (F2) gained a corroborating-evidence paragraph (the `capsule_audit.sql`
re-run's 0/23 L3-frozen-under-`t3` result), and item 18 is now marked **DISCHARGED** rather than
open. No item was added, removed, or re-ranked. Top-line summary for a reader of this file alone:

1. F2 (t3 definition inheritance) — still first, still the largest single lever; now doubly
   evidenced (readiness query's own 22/23 `NOT_READY-BLOCKED-ANCESTORS` reading, plus
   `capsule_audit.sql`'s independently-derived 0/23 L3-frozen-under-`t3`).
2. Design the missing acceptance receipts, or amend the delivery target.
3. Per-asset admission authority — zero assets formally authorized to start today.
4. The `kala_*` CASCADE data-loss remediation — highest severity, demoted by reach only.
5-20. Unchanged from cycle 7 — see the full list in `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md`.
   Item 18 is now DISCHARGED, not open.

## Known traps encountered this cycle (add to future subagent briefs — carried forward, re-confirmed, plus one new)

- **NEW this cycle — `gcloud run services describe` needs the correct region, and it is not
  `us-central1`.** All three Cloud Run services for this project (`amjis-web`, `amjis-mcp`,
  `amjis-sidecar`) live in `asia-south1`. `gcloud run services list` (no region flag) will surface
  the correct region in its labels; `describe` silently returns "Cannot find service" for the
  wrong region rather than an explicit region-mismatch error, which can misread as "service does
  not exist."
- **A `mergeStateStatus` of `BLOCKED`/`UNKNOWN`/`CLEAN` on a queued PR is not the authoritative
  signal of queue position or ETA — the GraphQL `mergeQueueEntry { position state
  estimatedTimeToMerge }` field is.** `mergeStateStatus` read `CLEAN` this cycle (meaning
  "mergeable, no blocking review/status issues") even while the branch was actively locked by the
  queue and rejecting pushes — these are two different questions (mergeability vs. queue
  processing state) and conflating them could read a genuinely-in-progress merge as either
  "stalled" or "already done" incorrectly.
- **A packet can sit fully complete on disk and never make it into the packet table** — carried
  forward from cycles 4/7, re-confirmed not recurring this cycle (`ls _work/*.md` diffed cleanly
  against this file's table before closing).
- **Repo-relative greps must use the actual tree, not an assumed top-level shorthand** — carried
  forward from cycle 7 (`platform/python-sidecar/{pipeline,services}/`, not bare
  `pipeline/`/`services/`); re-applied correctly this cycle for the deploy-sync `git log` path
  checks (`platform-mcp/`, `platform/python-sidecar/`).
- **A subagent's (or the conductor's own) markdown discussing configuration files by name can
  trigger a harness false-positive instruction-pattern scan** — carried forward from cycles 6/7,
  not re-triggered this cycle (no subagents dispatched).
- **Two identical push rejections in one cycle are not evidence of a local bug** — the fix is the
  external queue finishing, not a different push invocation, syntax, or force flag. Never
  force-push to route around a `GH006` merge-queue lock.
