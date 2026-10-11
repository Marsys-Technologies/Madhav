---
artifact: WORKTREE_DISPOSITIONS (KĀLA-YANTRA v3, Wave B, step B-0a)
content_version: 2.2
status: OWNER APPROVED 2026-10-11 (in chat with the planner) — execution pending in the next planner session; nothing has been removed yet
canonical_path: 00_ARCHITECTURE/briefs/kalayantra/WORKTREE_DISPOSITIONS_v2_1.md
compatibility_copy: 00_ARCHITECTURE/briefs/kalayantra/WORKTREE_DISPOSITIONS_v2_2.md (identical bytes; never edited on its own — Astra v2.2 KU-03)
authored_by: Claude Code (Opus 5.5, xhigh) — KĀLA-YANTRA v3 Planner, session local_ec1c912e-e039-4666-abc3-a815f9c4a2d1
observed_at: 2026-10-11T13:52Z–13:54Z
approved_source_commit: 3323430f249222724a24226cb1df46e389f5f255
plan: KALAYANTRA_RELAUNCH_PLAN_v2_2.md §5 (capacity reality), §14 B-0a
---

# Working-copy dispositions — Claude / Madhav policy root

## 1. What was measured

| fact | value | source |
|---|--:|---|
| Copies registered under `/Users/Dev/worktrees.noindex/madhav/claude/` | **40** | `git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree list --porcelain`, 13:54Z |
| Folders present there | 40 | `ls -d` of the same root (no orphan folders, no missing folders) |
| Ceiling (owner policy rule 4) | 15 | `/Users/Dev/.claude/CLAUDE.md`, policy agreed 2026-10-11 |
| Count the plan assumed | 33 | plan §5; Astra v2.2 walk item 3 observed 37 |
| Copies created today (2026-10-11 local) | 40 of 40 | folder creation times |
| All Madhav copies, every location and tool | 236 | same `worktree list` (outside this policy root; not in scope here) |

The count is still rising (33 → 37 → 40 during 2026-10-11). Thirty-seven of the forty
belong to the Suvarṇa certification work, which is live and keeps creating copies here.

Per copy I recorded: branch, commit, uncommitted tracked files, untracked files, whether
the branch on GitHub equals the local commit (`git ls-remote --heads origin`), commits not
on any GitHub branch (`git rev-list --count HEAD --not --remotes=origin`), the pull
request for the branch (`gh pr list --head … --state all`), and whether a running process
has the copy as its working folder (`lsof -a -d cwd`).

## 2. Recommendation in one view

| group | copies | recommendation |
|---|--:|---|
| A. Needed by KĀLA-YANTRA v3 | 2 | keep |
| B. In use by Suvarṇa right now, or carrying an open pull request | 4 | keep (Suvarṇa's to release) |
| C. Finished: clean, everything on GitHub | 16 | remove |
| D. Type-check throwaways (`tsc_*`): clean, commit on GitHub | 10 | remove |
| E. Holds work that exists nowhere else | 8 | archive to `/Users/Dev/Archives/`, then remove |
| **Total** | **40** | **6 stay, 34 go → 9 free places under the ceiling of 15** |

## 3. Every copy

Columns: *unc.* = uncommitted tracked files; *unp.* = commits on no GitHub branch;
*GitHub* = `same` (branch there, same commit), `differs`, `no` (branch not there),
`n/a` (no branch checked out).

### A. Keep — KĀLA-YANTRA v3 (2)

| copy | branch | commit | unc. | unp. | GitHub | pull request | why |
|---|---|---|--:|--:|---|---|---|
| kalayantra-relaunch-plan | kalayantra/relaunch-plan (now switched to kalayantra/b0-model-reconcile) | 3323430f2 | 0 | 0 | same | #3438 open | the planner's only checkout until the count is ≤ 14 |
| audit-token-economy | audit/token-economy | 758e0dbb4 | 0 | 0 | same | #3439 open | the plan's pinned evidence (read item 3); release after #3439 merges |

### B. Keep — Suvarṇa is using them (4)

| copy | branch | commit | unc. | unp. | GitHub | pull request | why |
|---|---|---|--:|--:|---|---|---|
| campaign-coordination | (none) | 9aead1423 | 0 | 0 | n/a | — | a running loop works from it |
| detached-829d8db1d-dispatch | (none) | 83316abb9 | 0 | 0 | n/a | — | a running dispatch loop works from it |
| cert-l1-nakshatra-canonical | suvarna/cert-l1-nakshatra-canonical | c9ff10128 | 0 | 1 | differs | — | a database connection helper is running from it, and it holds 1 commit not on GitHub |
| n99-timeout-test-robust | suvarna/n99-timeout-test-robust | 4434edd66 | 0 | 0 | same | #3440 open | open pull request, touched 17:42 local |

### C. Remove — finished and fully on GitHub (16)

| copy | branch | commit | unc. | unp. | GitHub | pull request |
|---|---|---|--:|--:|---|---|
| cert-bg-rules-reseal-1366 | suvarna/cert-bg-rules-reseal-1366 | 95ad76382 | 0 | 0 | same | #3436 merged |
| cert-ga-structural-restore-1367 | suvarna/cert-ga-structural-restore-1367 | 39ebf636e | 0 | 0 | same | #3437 merged |
| suvarna-integration-final-fallback | suvarna/integration-final-fallback | 6adfd1990 | 0 | 0 | differs (GitHub is ahead) | #3435 merged |
| cert-dispatcher-family-override | suvarna/cert-dispatcher-family-override | f8ba91eb9 | 0 | 0 | same | #3430 closed |
| cert-ga-structural-integrity-speed-r2 | suvarna/cert-ga-structural-integrity-speed-r2 | 4b151c7ef | 0 | 0 | same | #3429 closed |
| n431-bgrules-measure | suvarna/n431-bgrules-measure | 8e7f82aab | 0 | 0 | same | #3431 closed |
| n431-jsonpath-multikind | suvarna/n431-jsonpath-multikind | 0eb9cca34 | 0 | 0 | same | #3421 closed |
| n431-nakshatra-dhanishta-fallback | suvarna/n431-nakshatra-dhanishta-fallback | f9018943e | 0 | 0 | same | #3434 closed |
| n431-prose-wildcard | suvarna/n431-prose-wildcard | 0eb85e1eb | 0 | 0 | same | #3432 closed |
| cert-ga-structural-nakshatra-tolerant | suvarna/cert-ga-structural-nakshatra-tolerant | feeacc5c2 | 0 | 0 | same | none |
| cert-nak-ts-phala | suvarna/cert-nak-ts-phala | ff860630b | 0 | 0 | same | none |
| n431-rehearsal-rev28b | suvarna/n431-rehearsal-rev28b | f17f632bf | 0 | 0 | same | none |
| integration-fix-unit | fixunit | da6c71bf7 | 0 | 0 | no — but the commit is on `origin/suvarna/integration-final-fallback` | none |
| n431-w8-integrity-budget | f4/n431-w8-integrity-budget | 61a27c390 | 0 | 0 | no — but the commit is on `origin/suvarna/integration-dryrun-3/-4` | none |
| detached-1bdd36761-engine | (none) | 11b8fec2b | 0 | 0 | n/a — commit is the merged head of #3435 | — |
| detached-sweep-3435 | (none) | 829d8db1d | 0 | 0 | n/a — commit is on `main` | — |

### D. Remove — type-check throwaways (10)

All have no branch, no uncommitted files, nothing unpushed, and their commit is on at
least one GitHub branch.

`tsc_11b8fec2b4447b608ca6208f` · `tsc_175dc84590256304978cd8f3` ·
`tsc_39ebf636e4eda2cbcb980bab` · `tsc_5038a267308b1d7b2135353d` ·
`tsc_6adfd199072689f115c37eed` · `tsc_94e6de45ab15deb10a0efa3e` ·
`tsc_95ad7638267fe99ad9b4818f` · `tsc_9bd3c50e68b3598084d87846` ·
`tsc_a63e3834b4e186dd4e6a565e` · `tsc_e879b9f43c4401aa6e552b4a`

### E. Archive, then remove — work that exists only on this machine (8)

| copy | branch | commit | unc. | unp. | what would be lost without an archive |
|---|---|---|--:|--:|---|
| n431-rehearsal-rev28 | suvarna/n431-rehearsal-rev28 | 2239a5b7f | 0 | 26 | 26 commits (registry revision 28 rehearsal); branch is not on GitHub |
| bg-rules-integrity-reseal | suvarna/bg-rules-integrity-reseal | 9df4ecea1 | 0 | 1 | 1 commit (migration 1366 placeholder) |
| tmp-fa | tmp-fa | e2a8d9872 | 0 | 1 | 1 commit (test re-pins for registry revision 28) |
| tmp-fb | tmp-fb | d7408feb0 | 0 | 1 | 1 commit (retired-grid test pins) |
| tmp-fc | tmp-fc | a70470b15 | 0 | 1 | 1 commit (remedies test pins) |
| detached-ba7c8cd7b-walkcheck | (none) | 7337fefce | 0 | 1 | 1 commit, self-described "throwaway walkcheck state" |
| detached-ba7c8cd7b-walkcheck2 | (none) | ba7c8cd7b | 23 | 0 | 23 staged, uncommitted test-file edits |
| detached-ba7c8cd7b-walkcheck3 | (none) | ba7c8cd7b | 24 | 0 | 24 staged, uncommitted test-file edits |

Archive form: unpushed commits → a git bundle; uncommitted edits → a patch file; both
under `/Users/Dev/Archives/`, named `madhav-<copy>-20261011.*`.

## 4. How to dispose

A helper re-checks every copy against this inventory immediately before acting and skips
any copy that has moved, become dirty, or is in use. It uses `git worktree remove` and
`git worktree prune` only (never `rm -rf`).

```bash
bash /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/planner/dispose_worktrees.sh
```

```bash
bash /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/planner/dispose_worktrees.sh --apply
```

The first is a dry run (verified 13:55Z: 34 handled, 0 skipped, nothing changed). The
second acts. The planner will run the second only on the owner's explicit instruction.

## 5. Capacity after disposal — two things the owner should know

1. **The ceiling is shared.** With 6 copies left there are 9 free places. KĀLA-YANTRA
   v3 Wave B needs one copy per bootstrap component (19 components, plan §14 B-1). The
   planner will therefore run B-1 in batches sized to the free places, never all at once.
   No plan change is needed for that.
2. **Suvarṇa refills the folder.** It created 37 copies here in about 18 hours. Unless
   it also removes its finished copies as it goes (owner policy rules 3 and 6), the
   count returns above 15 and B-1 stalls again. A fixed share (for example 8 places for
   KĀLA-YANTRA v3, 7 for Suvarṇa) would keep both moving.

One further observation, not a disposition: 8 test processes started 06:55 local are
still running from a folder that no longer exists (`integration-final-fallback-fix2`).
They belong to Suvarṇa; the planner has not touched them.

## 6. Owner decision record

| decision | owner's answer | date |
|---|---|---|
| Groups C and D (26 copies): remove | APPROVED as recommended | 2026-10-11 |
| Group E (8 copies): archive, then remove | APPROVED as recommended | 2026-10-11 |
| Group B (4 copies): keep until Suvarṇa releases them | APPROVED as recommended | 2026-10-11 |
| Share of the 15 places between KĀLA-YANTRA v3 and Suvarṇa | 8 for KĀLA-YANTRA v3, 7 for Suvarṇa. Rule when Suvarṇa overruns (owner-surrogate ruling, adopted by the owner): KĀLA-YANTRA creates a copy only when its own count is under 8 and the total is ≤ 14 before creation (a batch of n needs ≤ 15 − n); otherwise it waits, works by branch switch and reports once | 2026-10-11 |
| Who runs the disposal | the next planner session, with the helper in §4; copies the helper skips are left alone and reported; never forced | 2026-10-11 |
| The 8 stray Suvarṇa test processes (§5) | left alone; reported to Suvarṇa on the coordination log; KĀLA-YANTRA does not stop them (owner-surrogate ruling) | 2026-10-11 |
