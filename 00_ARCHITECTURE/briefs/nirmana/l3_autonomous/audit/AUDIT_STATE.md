# KĀLA READINESS AUDIT — STATE

**FINAL — AUDIT COMPLETE (2026-09-22, closed by the strategic session).** All 12 deliverables are on
`main` (PR #2707 W1–W3, PR #2708 W4 + verdict + decision list). Verdict: **strategy
GO-WITH-CONDITIONS; environment GO for non-mutating work, NO-GO for production builds** (four
defects E-1…E-4). The supervisor was stopped after cycle 14: cycles 10–14 were honest IDLE-OK polls
of CI with nothing left to do, so the close-out (this note, `AUDIT_DONE`, the v1.1 addendum to the
readiness audit, and `../KALA_NATIVE_RULING_SHEET_v1_0.md`) was done directly rather than by
spending further cycles. 14 cycles, ~3h wall. One process defect found and fixed mid-run (cycle 4
exited with background subagents pending — see the charter's foreground-subagent law). Known
residual: the supervisor's progress fingerprint counts non-commit changes, so an idle cycle reads
`progress=yes`; fix before reusing the supervisor for the elevation campaign.
**Next:** native rulings R1–R6 (ruling sheet). Everything below is the cycle-9 state, kept as record.

**Position:** cycle 9 complete (2026-09-22). All twelve §7 deliverables remain content-complete
(unchanged in substance from cycle 8). This cycle's entire contribution was **push/PR mechanics**
that had gone stale between cycles: PR #2707 (cycles 1-6, W1/W2/W3 close) turned out to have
**already merged** into `main` during the gap since cycle 8 closed — but as a **squash merge**,
which broke the direct ancestry relationship cycle 8 had assumed. This meant cycle 7+8's three
unpushed local commits, once pushed, produced a **real add/add merge conflict** against the new
`main` (not a queue lock) when opened as a fresh PR. That conflict is now resolved, pushed, and a
new PR (**#2708**) is open with auto-merge armed and CI running. **`AUDIT_DONE` is not yet written**
— per the charter's own "Done" clause ("final docs PR is merged, **or queued with every check
green**"), #2708's checks are still `pending`/running, not yet green. This is the only reason this
cycle does not print `AUDIT COMPLETE`.

**Branch:** `l3/kala-readiness-audit`. **Worktree:** `/Users/Dev/madhav-l3/audit` (persistent
across cycles — not disposable; local-only commits are safe here between cycles).

## Cycle 9 — what happened

1. **PR/sync hygiene — mandatory first action per cycle 8's own handoff instructions:**
   - `git fetch origin l3/kala-readiness-audit` → origin still at `98be7fd33` (unchanged since
     cycle 6's push — cycle 7/8's three commits, `bc617d9db`/`84efeb02a`/`3d9605b79`, plus cycle
     8's own state-rewrite commit `fa63442a0`, were still local-only, exactly as cycle 8 recorded).
   - `gh pr view 2707` (REST-style read) reported `state: OPEN, mergedAt: null` — **this was
     stale/cached.** Cross-checked via GraphQL (`pullRequest(number: 2707) { state mergedAt
     mergeStateStatus mergeQueueEntry }`) which correctly reported `state: MERGED, mergedAt:
     2026-09-21T21:34:03Z, mergeQueueEntry: null`. **Lesson for future cycles: prefer the GraphQL
     read over `gh pr view`'s cached fields when the two might disagree** — added to known traps
     below.
   - Confirmed via `git log 9b3c3b219..origin/main` that PR #2707 landed as squash commit
     `796c5d47e` on `origin/main`. The `l3/kala-readiness-audit` branch ref on origin was **not**
     deleted or fast-forwarded by the squash-merge — it remained at its pre-merge tip (`98be7fd33`,
     unlocked, since the merge-queue lock releases once the PR is off the queue).
   - **`git push origin l3/kala-readiness-audit` — succeeded on the first attempt this cycle**
     (`98be7fd33..fa63442a0`, fast-forward). The charter's per-cycle "no third identical attempt"
     rule from cycles 7-8 no longer applied since the underlying blocker (queue lock) was gone.
   - `gh pr list --head l3/kala-readiness-audit --state all` confirmed #2707 as `MERGED` and no
     other open PR existed for this branch — so a **new** PR was required for cycles 7-8's content
     (old PR is closed, cannot be reused), matching cycle 8's own contingency plan exactly.
   - Comparing `git diff origin/main HEAD` (direct two-tree diff, **not** the misleading
     triple-dot/merge-base form — see known traps) showed only **4 files** genuinely differ from
     the new `main`: `AUDIT_STATE.md` (full rewrite, as expected for a "rewritten every cycle"
     file), the new W4 deliverable `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` (never in #2707,
     created cycle 7), `KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` (+8 lines, cycle 8's stale-flag
     note), and `_work/DOMAIN_A.md` (+34 lines, cycle 8's addendum).
   - Opened **PR #2708** (`docs(l3-audit): KĀLA readiness audit — W4 close (cycles 7-8, verdict +
     decision list)`, base `main`, head `l3/kala-readiness-audit`). `gh pr merge 2708 --squash
     --auto` reported `! The merge strategy for main is set by the merge queue` (informational, not
     an error — the repo enforces its own merge-queue strategy) but `autoMergeRequest` was already
     populated on the PR (repo-level auto-arm on PR creation, matching the pattern seen on #2706/
     #2707). Confirmed armed via `gh pr view 2708 --json autoMergeRequest`.
   - **Discovered and resolved a real add/add merge conflict** (not a queue lock — the true
     obstacle cycle 8 had not yet encountered): `git merge-tree` against the *wrong* (but
     git-computed) merge-base `9b3c3b219` showed `AUDIT_STATE.md`, `KALA_ACCEPTANCE_REGIME_
     MAPPING_v1_0.md`, and `_work/DOMAIN_A.md` all as "added in both" with genuinely divergent
     content (main's squash-merged cycle-6 version vs. this branch's cycle-8 version) — GitHub's
     own merge check agreed (`mergeable: CONFLICTING`, `mergeStateStatus: DIRTY`). **Force-push and
     `reset --hard` are both charter-forbidden**, so resolved via a standard `git merge origin/main
     --no-edit`: kept HEAD's version whole for `AUDIT_STATE.md` (correct per its own "rewritten
     completely by every cycle" contract — cycle 8's content strictly supersedes cycle 6's), and
     for the other two files confirmed by direct inspection that origin/main's side of each
     conflict was empty (pure cycle-8 appends with nothing to reconcile against) before resolving.
     Verified zero leftover `<<<<<<<`/`=======`/`>>>>>>>` markers anywhere under the audit dir
     before committing. Merge commit `ec640136602a4ba71d521e9e8f5096189cd282f2` pushed clean.
   - Re-checked mergeability post-push: `mergeable: MERGEABLE`, `mergeStateStatus: BLOCKED`
     (checks still running — 24 checks observed via `gh pr checks 2708`, most `pending`, a handful
     already `pass`, two `skipping` for the same known-native-only reasons as every prior cycle:
     Census Battery §G master gate, the MCP per-tool smoke battery needing a native-set bearer
     token). This matches the charter's own precedent exactly — not a stall.
   - **PR #2695 (F8):** re-checked; `state: OPEN, mergeStateStatus: UNKNOWN, mergedAt: null` — no
     change in substance from cycle 8 (still unmerged, still poisoning provenance for any dispatch
     that would touch it). The `mergeStateStatus` value itself flickered (`BLOCKED` cycle 8 →
     `UNKNOWN` this cycle) which is expected GitHub-side noise per the known trap already on file
     about `mergeStateStatus` not being an authoritative signal.
   - **Deploy-sync table** (read-only `gcloud run services describe`, `asia-south1`, no dispatch):

     | Surface | Deployed revision SHA | vs `origin/main` (`796c5d47e`) | Deployable drift? |
     |---|---|---|---|
     | `amjis-web` | `9b3c3b219` (unchanged since cycle 8) | behind by 1 commit (#2707) | **No** — `git diff 9b3c3b219..origin/main --stat -- platform/` is empty; #2707 was docs-only |
     | `amjis-mcp` | `09d998940` (PR #2698, unchanged) | behind | **No** — same docs-only delta, plus the zero-content-drift result already established cycle 8 for `platform-mcp/` |
     | `amjis-sidecar` | `09d998940` (PR #2698, unchanged) | behind | **No** — same |
     | builder image | tracks the sidecar path | behind | **No** — same |

     **No deploy dispatched this cycle** — the only new commit on `main` since the last check
     (`796c5d47e`, i.e. PR #2707 itself) touches only `00_ARCHITECTURE/`, confirmed via
     `git diff 9b3c3b219..origin/main --stat -- platform/` returning empty. Both remaining
     deploy-dispatch budget slots preserved (0 of 2 used all-time).

2. **No new wave dispatched, no subagents spawned this cycle.** Consistent with cycle 8's own
   conclusion (re-confirmed, not re-litigated): all ten named deliverables plus the verdict/
   decision-list synthesis are content-complete and unchanged in substance; this cycle's entire
   task was mechanical (push, conflict resolution, PR open, auto-merge arm) work that a subagent
   dispatch would not have improved — the conductor did it directly, matching the audit's own
   established precedent for single-owner mechanical/deterministic tasks (cycle 6's grep
   re-verification, cycle 7's path correction, cycle 8's SQL re-run).

3. **Commit — pushed all pending work this cycle.** Two pushes: (a) the fast-forward of cycles
   7-8's three previously-local commits (`98be7fd33..fa63442a0`), and (b) the merge-conflict
   resolution commit `ec640136602a4ba71d521e9e8f5096189cd282f2` (`origin/main` merged in, conflicts
   resolved as above). Working tree clean after both. **Zero unpushed local commits remain** —
   `git log origin/l3/kala-readiness-audit -1` and `git log HEAD -1` are identical
   (`ec640136602a4ba71d521e9e8f5096189cd282f2`).

## Cycle 9 spot-verification / direct-work log (conductor; no subagents dispatched this cycle)

- **`gh pr view 2707`'s cached `mergedAt: null` vs. GraphQL's accurate `mergedAt:
  2026-09-21T21:34:03Z`** — caught by cross-checking two independent read paths before acting on
  either, per this audit's own "measured, not inferred" governing rule. Acting on the stale REST
  read alone would have wasted a cycle re-attempting a push against a branch that was actually
  already unlocked.
- **`git diff origin/main...HEAD` (triple-dot) vs. `git diff origin/main HEAD` (direct tree
  diff)** — the triple-dot form, relative to `git merge-base` (`9b3c3b219`, a point before the
  audit directory existed on shared history), showed all 61 files as pure additions, which would
  have led to opening a PR that re-proposed cycles 1-6's already-merged content wholesale. The
  direct two-tree diff correctly isolated the actual 4-file delta. **New known trap, recorded
  below.**
- **`git merge-tree` against the same (correct-per-git, misleading-for-content) merge-base**
  reproduced the exact conflict GitHub's own `mergeable: CONFLICTING` check reported, confirming
  the conflict was real (a genuine content divergence from the squash-merge breaking direct
  ancestry) and not a false positive from a bad local check.
- **Read both non-`AUDIT_STATE.md` conflict hunks in full** before resolving (`KALA_ACCEPTANCE_
  REGIME_MAPPING_v1_0.md` lines 369-379, `_work/DOMAIN_A.md` lines 140-176) — confirmed the
  `origin/main` side of each was empty (nothing to lose by keeping HEAD's side) rather than
  assuming it from the file names alone.
- **Post-resolution grep for leftover conflict markers** (`<<<<<<<`, `=======`, `>>>>>>>`) across
  the whole audit directory returned zero matches before committing.
- **`git diff 9b3c3b219..origin/main --stat -- platform/`** — empty, confirming #2707 was
  genuinely docs-only and no deploy is owed for it.

No claim independently checked this cycle failed verification, apart from the one stale field
(`gh pr view`'s `mergedAt`) that the GraphQL cross-check itself caught and corrected before any
action was taken on it.

## Observed at seed / carried forward (re-confirmed cycle 9 where re-touched)

| Fact | Value |
|---|---|
| `origin/main` | `796c5d47e` (PR #2707 squash-merged, cycles 1-6 content) — advanced from cycle 8's `9b3c3b219` |
| Current campaign definition | `t3-2026-09-11-8b884eac` — unchanged |
| PR #2706 (F1 repair) | MERGED. No further action. Unchanged. |
| **PR #2707** (this audit's cycles 1-6 W1/W2/W3 closure docs PR) | **MERGED** (`2026-09-21T21:34:03Z`, squash commit `796c5d47e`) — cycle 8 had it as still-queued; it merged in the gap between cycles. No further action. |
| **PR #2708** (NEW this cycle — cycles 7-8 W4 closure docs PR) | OPEN, auto-merge armed, `mergeable: MERGEABLE`, `mergeStateStatus: BLOCKED` (CI running — checks `pending`, a handful already `pass`, two `skipping` for the usual native-only reasons). Content: `AUDIT_STATE.md` rewrite, `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` (new), stale-note in T3, Domain A addendum. |
| PR #2695 (F8) | OPEN, `mergeStateStatus: UNKNOWN` (was `BLOCKED` cycle 8, `UNKNOWN` cycle 7 — this field is known-noisy, see traps) — still unmerged either way |
| `kala_activation`/`kala_convergence` for canonical chart | 0 rows each — root cause fully diagnosed (cycle 6), unresolved (native decision list item 4) — unchanged |
| `ka_gochara_v3_century_materialize` BUILD-PROTECTED guard | Still live, unresolved (native decision list item 7) — unchanged |
| `kala_timeline_spec` vs `kala_timeline` | Two similarly-named tables, only one live — unchanged since cycle 7 |
| Safety-exclusion coverage gap | `detectMortalityExclusion` wired into only 2 of 9 registered `kala_views` tools — unchanged, native decision list item 12 |
| Domain A instrument verdict | READY (unchanged since cycle 8's fix-confirmation) |
| True L3 frozen count under `t3` | 0 of 23 (unchanged since cycle 8) |
| Deploy region | All three Cloud Run services in `asia-south1` (unchanged since cycle 8) |
| Deploy-sync table | Still no genuine deployable drift on any surface — PR #2707 (the only new commit on `main` since last check) was docs-only. No deploy dispatched. |

## Packet table

All ten named deliverables + the W4 verdict/decision-list synthesis remain **DONE**, content
unchanged from cycle 8 — see cycle 8's entry in git history (`git show
84efeb02a:00_ARCHITECTURE/briefs/nirmana/l3_autonomous/audit/AUDIT_STATE.md`) for the full
per-packet table; not reproduced here verbatim since nothing changed. Full list, status only:

| Packet | Status |
|---|---|
| F1 egate repair + sibling sweep | **DONE** (PR #2706, merged) |
| F2 inheritance quantification | **DONE** |
| F3 four-way DAG reconciliation | **DONE** |
| F4 privilege matrix | **DONE** |
| F5 consumer-path trace ×23 | **DONE** |
| F6 deploy lag | **DONE** |
| F7 data census | **DONE** |
| F8 PR #2695 state | **DONE** (re-checked this cycle, unchanged) |
| Domain A | **DONE**, READY as instrument (cycle 8 fix) |
| Domain B–J | **DONE**, all unchanged |
| T1 traceability ×3 clusters | **DONE** |
| T2 proving journeys | **DONE** |
| T3 acceptance-regime mapping | **DONE** (one stale-flag note, cycle 8) |
| T4 brief conformance | **DONE** |
| T5 tensions | **DONE** |
| T6 boundaries | **DONE** |
| §5 execution/velocity design | **DONE** |
| §6 setup + runbook | **DONE** |
| Readiness audit synthesis (W4) | **DONE** — `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md`, now in PR #2708 pending merge |
| Verdict + native decision list | **DONE** — folded into the same file; verdict itself (GO-WITH-CONDITIONS strategy / split NO-GO+GO environment) unchanged |

## In flight

- **PR #2706** (F1 repair): MERGED. No further action.
- **PR #2707** (cycles 1-6 closure): **MERGED** this gap (`796c5d47e`). No further action.
- **PR #2708** (cycles 7-8 W4 closure, NEW this cycle): OPEN, auto-merge armed, `mergeable:
  MERGEABLE`, CI running (`mergeStateStatus: BLOCKED` pending checks, not a stall — matches every
  prior cycle's 6-14 min precedent). **Next cycle's mandatory first action:**
  1. `git fetch origin l3/kala-readiness-audit && git log origin/l3/kala-readiness-audit -1` —
     confirm no drift (should still be `ec640136602a4ba71d521e9e8f5096189cd282f2` unless a human
     touched the branch).
  2. `gh api graphql` for PR #2708's `state`/`mergedAt`/`mergeQueueEntry` (**prefer GraphQL over
     `gh pr view`'s cached fields** — this cycle's own lesson) and `gh pr checks 2708`.
  3. **If merged:** all twelve §7 deliverables are now live on `main`. Confirm no further local
     commits are pending (there should be none — this cycle left the tree clean and fully pushed).
     If genuinely nothing else is outstanding, write `audit/AUDIT_DONE` (empty file), commit, push,
     print `CYCLE <n>: AUDIT COMPLETE -> next: native review`.
  4. **If still open/checks running:** this is normal CI latency, not a stall. Do not re-push, do
     not re-open a PR, do not force anything. If genuinely nothing else is eligible (expected — no
     new wave has been eligible since cycle 8), print `CYCLE <n>: IDLE-OK <reason> -> next: PR
     #2708 merge` with zero git writes, per the charter's own IDLE-OK provision — do **not**
     fabricate work to avoid an idle cycle.
  5. **If checks show a genuine failure** (not `pending`/`skipping`): diagnose; this would be the
     first real CI failure this audit branch has produced against its own docs-only content, so
     treat it as a real signal, not assume it's the known-native-only skip pattern.
- No deploy dispatched this cycle (see deploy-sync table above — no genuine drift). No lease
  claimed or held on `origin/campaign-coordination`.
- **No new audit wave is eligible.** Unchanged from cycle 8's own conclusion, re-confirmed this
  cycle. The only remaining work of any kind is PR #2708 clearing CI and merging, then writing
  `AUDIT_DONE`.

## Budget

| Resource | Used | Ceiling |
|---|---|---|
| Cycles (supervisor numbering) | 9 (of which 7 have actually closed with a local commit: 1, 2, 3, 6, 7, 8, 9) | 40 |
| Subagent dispatches | 36 (cycles 1-8) + 0 (cycle 9, mechanical push/merge/PR work only) = **36** | 120 |
| PRs opened | 3 (#2706 merged, #2707 merged, **#2708 NEW this cycle**, open with auto-merge armed) | 6 |
| Deploy dispatches | 0 | 2 |
| Production mutations | 0 | **0** |
| Local disposable Postgres instances started/stopped | 2 (cycles 2 and 4), both fully torn down — none this cycle | n/a — local-only |

## Native decision list

**Unchanged in ranking and content from cycle 8's list (itself unchanged in ranking from cycle
7's) in `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md`'s "Readiness verdict and native decision list"
section — read it there, not here.** No item was added, removed, re-ranked, or edited this cycle;
this cycle's work was entirely push/PR/merge-conflict mechanics, not new audit findings. Top-line
summary for a reader of this file alone:

1. F2 (t3 definition inheritance) — still first, still the largest single lever.
2. Design the missing acceptance receipts, or amend the delivery target.
3. Per-asset admission authority — zero assets formally authorized to start today.
4. The `kala_*` CASCADE data-loss remediation — highest severity, demoted by reach only.
5-20. Unchanged from cycle 7 — see the full list in `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md`.
   Item 18 remains DISCHARGED (cycle 8).

## Known traps encountered this cycle (add to future subagent briefs — carried forward, re-confirmed, plus two new)

- **NEW this cycle — `gh pr view <n>`'s JSON fields (notably `mergedAt`, `state`) can read stale/
  cached even when the PR has genuinely merged.** Cross-check with the GraphQL API
  (`pullRequest(number: N) { state mergedAt mergeStateStatus mergeQueueEntry { position state
  estimatedTimeToMerge } }`) before concluding a PR is still open, especially after any gap between
  cycles where a queued PR plausibly finished processing.
- **NEW this cycle — after a PR merges via squash, its source branch ref is *not* automatically
  advanced or deleted** (at least under this repo's settings) — it sits at its pre-merge tip,
  unlocked. A fresh push to that branch will succeed (fast-forward), but the branch's content will
  then have **diverged from `main`'s squash commit at the git level** (same logical content, no
  shared exact-commit ancestry beyond the true fork point), which can produce a **real** add/add
  merge conflict when a *new* PR is opened from that branch against the now-advanced `main` — this
  is not a queue lock and will not resolve itself; it needs an actual `git merge origin/main`
  (never force-push/reset --hard) with the conflicts resolved by hand.
- **NEW this cycle — `git diff A...B` (triple-dot, merge-base-relative) can be badly misleading
  when `A` and `B` share a very old true merge-base** (e.g. from before a whole directory was
  created on either side) — it will show large swaths of already-shared content as pure additions.
  **Use `git diff A B` (direct two-tree diff) to see what has actually changed between two refs'
  current content**, and reserve triple-dot for when you specifically want "what changed in B since
  it forked from A."
- **`gcloud run services describe` needs the correct region** (`asia-south1`, not `us-central1`) —
  carried forward from cycle 8, re-confirmed correct this cycle.
- **A `mergeStateStatus` of `BLOCKED`/`UNKNOWN`/`CLEAN`/`DIRTY` on a PR is not by itself the full
  picture** — carried forward from cycle 8 (queue-position nuance) and reinforced this cycle in a
  new way: `DIRTY` specifically flags a real merge conflict (confirmed this cycle by cross-checking
  `mergeable: CONFLICTING` and independently reproducing the same conflict locally via
  `git merge-tree`), whereas `BLOCKED`/`UNKNOWN` on a conflict-free PR usually just means checks are
  still running. Don't conflate the two — `DIRTY`/`CONFLICTING` needs an actual merge/rebase; the
  others just need CI to finish.
- **Two identical push rejections in one cycle are not evidence of a local bug** — carried forward
  from cycle 8, not re-triggered this cycle (the queue lock that caused cycles 7-8's rejections was
  gone by the time this cycle checked).
- **A packet can sit fully complete on disk and never make it into the packet table** — carried
  forward from cycles 4/7/8, re-confirmed not recurring this cycle.
- **Repo-relative greps must use the actual tree, not an assumed top-level shorthand** — carried
  forward from cycle 7, re-applied correctly this cycle for the `platform/` deploy-sync path check.
