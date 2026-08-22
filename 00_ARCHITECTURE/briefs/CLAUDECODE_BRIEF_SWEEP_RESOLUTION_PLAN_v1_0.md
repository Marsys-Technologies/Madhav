---
canonical_id: CLAUDECODE_BRIEF_SWEEP_RESOLUTION_PLAN
version: 1.0
status: PROPOSED — plan only, nothing executed
date: 2026-08-22
author: Claude Code (Fable 5), at native's request
scope: resolution of every open item surfaced by the 2026-08-22 hygiene sweeps (Madhav worktrees/branches, /Users/Dev scratch folders, Marsys-Mines-ERP-V2 landing)
supersedes_nothing: this is the follow-on to CLAUDECODE_BRIEF_WORKTREE_AND_STRAY_ARTIFACT_SWEEP_v1_0 (executed) — it plans the residuals, plus one new P0 the execution itself created
---

# Sweep resolution plan

## 0. State of the world right now (verified 2026-08-22 ~23:45 IST, read-only)

| Surface | State |
|---|---|
| Madhav checkout | on `salvage/wrapped-campaigns-clean` (6 commits over origin/main), **not** the branch I worked on |
| `salvage/wrapped-campaign-artifacts` | intact, local + origin, tip `a63ab7c0d`; carries my 4 commits; PR #1488 OPEN (100 commits) |
| `salvage/wrapped-campaigns-clean` | created by another session: the 6 original salvage commits cherry-picked onto origin/main; PR #1489 OPEN; **contains none of my landed content** |
| `.codex/config.toml` (Madhav) | prod MCP key `mcp_prod_eeNr…` in plaintext; **NOT gitignored on the checked-out branch** (my gitignore commit lives only on #1488's branch) |
| Worktrees | Madhav 1 ✓ · ERP **25** (23 under `/private/tmp`) |
| Local branches | Madhav 5 ✓ · ERP **32** |
| Stash (Madhav) | 7 entries, all other campaigns' WIP, shared across worktrees |
| PR #117 (ERP) | OPEN, MERGEABLE, **gitleaks FAILED** — recursive false positive (see §3) |
| Bundle | `Apps/Madhav-branch-archive-20260822.bundle`, 138 refs, verify PASS |
| Previously-unconfirmed 6 bundle branches | **all now confirmed landed** (§6) — no action |

---

## P0 — stop the loss (do today, in this order)

### 1. Reconcile PR #1488 vs PR #1489 — the fork

**Decision: #1489 is the right base. Re-land my content onto it; close #1488 as superseded.**
The other session's instinct was correct — a 100-commit PR carrying a 179-commit merge is the wrong
shape for a docs landing. What it lacks is awareness of the four commits made after it branched.

| Commit on #1488 | Content | How it goes onto #1489 |
|---|---|---|
| `d51389dbd` | SALVAGE_LEDGER, SAMPŪRTI Δ3 log, 35 codex-v4 JSONs, 7 PARIŚEṢA prompts, sweep brief | `git cherry-pick` — plain commit, applies clean |
| `86b9934cd` | **merge** of `parisesa/campaign-state` (130 files, +129,308) | **do NOT cherry-pick the merge.** Tree-copy instead: `git checkout parisesa/campaign-state -- 00_ARCHITECTURE/briefs/parisesa verification_artifacts/PARISESA_V4_GA3_REBUILD_20260821` → one squashed commit. Same files, one commit, no 179-commit history drag. |
| `257efccb6` | gitignore: `.codex/config.toml`, `.codex/worktrees/`, `.claude/worktrees/` | cherry-pick (drop the `.claude/worktrees/` line — `.claude/` is already ignored wholesale at `.gitignore:5`, the line was redundant) |
| `a63ab7c0d` | 75 overnight campaign plans + README | cherry-pick — plain commit |

Procedure (coordination matters — a second agent is live on this exact branch):
1. **Acquire a lease** in `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` naming
   `salvage/wrapped-campaigns-clean` + the four file groups above. Rule X-1 (lease-before-merge) is
   non-deferrable in this repo; the earlier collision proves why.
2. Do the work in a throwaway worktree off `salvage/wrapped-campaigns-clean` (not the shared checkout —
   that is the other agent's surface). Remove the worktree after push.
3. Push the 4 commits **onto `salvage/wrapped-campaigns-clean`** (additive; no force). #1489 grows from
   6 → 10 commits and now carries everything.
4. Verify on origin: `git ls-tree -r origin/salvage/wrapped-campaigns-clean | grep -c` for each of the
   four file groups. Byte-compare SALVAGE_LEDGER and the 75 plans against the #1488 copies.
5. Comment on #1488: "superseded by #1489 — all content re-landed as 4 squashed commits, verified
   byte-identical." **Close #1488. Do not delete its branch** until #1489 is merged (it is the
   backup). Release the lease.

Gate: nothing in step 5 until step 4 passes. If the other session pushes to the branch mid-way,
rebase my 4 commits on its tip — never the other way round.

### 2. Rotate the production MCP key and close the exposure

Native-only action; the plan just sequences it.
1. Mint a new key for the `amjis-mcp` Cloud Run service (wherever `mcp_prod_*` keys are issued).
2. Update every consumer: `~/Vibe-Coding/Apps/Madhav/.codex/config.toml` (local file, stays
   uncommitted), the claude.ai MARSYS-JIS connector, `MARSYS_MCP_KEY` in any shell profile / launchd
   plist, and the Cloud Run env if the server validates against a stored list.
3. Revoke `mcp_prod_eeNr…`. Verify: a request with the old key returns 401; with the new key, 200.
4. Land the gitignore (P0-1 handles it). Until #1489 merges, the key is one `git add -A` from a
   commit on `main` — so **do 2 before anything else touches the Madhav checkout.**
5. Grep all three repos' history once: `git log -p --all -S'mcp_prod_' | head` — confirm the key
   was never committed. (Earlier check said untracked-only; confirm against history, not just status.)

---

## P1 — close the open PRs (this week)

### 3. PR #117 (ERP) — gitleaks false positive, recursive

Gitleaks flags `docs/status/phase-reports/a30-cleanslate.md:112` (`generic-api-key`, entropy rule).
The line is the report *quoting* the prose that was itself a documented false positive
(`A2-HOSTING-ELEVATION-PLAN.md:234`, already in `.gitleaksignore`). A report about a false positive
triggers the same false positive. Fix: append the fingerprint gitleaks printed, in the file's
existing format:
```
990c35c50edcb40d893e90f1395357e24bfc194a:docs/status/phase-reports/a30-cleanslate.md:generic-api-key:112
```
One-line commit on `docs/a30-phase-reports-landing`; CI re-runs; merge. Check `a30-wrapup.md:38/62`
did *not* trigger (it quotes the fingerprint string, not the prose) — the run shows only one finding,
so it did not.

### 4. Merge order
1. #117 (ERP) — after §3, independent of everything else.
2. #1489 (Madhav) — after P0-1 step 4 verification. Then delete `salvage/wrapped-campaign-artifacts`
   local + origin, and `parisesa/campaign-state` local (origin copy stays — it is the campaign's own
   ref, and `CURRENT_STATE` may point at it).

### 5. Ruling N4 — `SAMPURTI_REBASE_PLAN_v1_0.md` discrepancy

The copy landed under `briefs/overnight_campaign_plans/` carries 10 lines the ratified
`briefs/sampurti/REBASE_PLAN_v1_0.md` lacks: **N4 (native, 2026-08-13 00:5x IST) — P-G1 closes
per-class; remaining 21 classes complete incrementally via `ka_kshetra` checkpoint-resume; the
monolithic-single-run requirement is retired.**

Decision required from the native — two honest options:
- **(a) N4 is a real ruling that was never folded back.** Amend `briefs/sampurti/REBASE_PLAN_v1_0.md`
  in place (frontmatter changelog entry, version bump per B.8), note it in `SAMPURTI_STATE.md`, and
  check whether the L3 `ka_kshetra` writer behaviour actually honours checkpoint-resume as the ruling
  assumes — if the ruling bound behaviour that was never built, that is a finding, not a doc edit.
- **(b) N4 was provisional and superseded by the SAMPŪRTI seal.** Leave the sampurti copy alone; add
  one line to the overnight README marking the 10 lines historical.
Recommendation: (a) *if* `SAMPURTI_STATE.md` or the seal report already references per-class closure
(grep `per-class\|GREEN-PER-CLASS\|6/27`); otherwise (b). Either way it is a one-session task.

### 6. The six previously-unconfirmed bundle branches — RESOLVED, no action

| Branch | Disposition |
|---|---|
| `f123tmp` | tip identical to `parisesa/repair-F123-dead-pointer` → **PR #1379 MERGED** |
| `adversary-base`, `review-base` | `pariprashna/receipt/validate.ts` is on `origin/main` → squash-landed |
| `pr1404merge` | PR #1404 MERGED |
| `pr-1112-check` | PR #1112 MERGED |
| `morning-merge-tmp` | the EKAVĀKYATĀ close commit (`44ccf6661`) names `#1310` as the landed morning merge; the 18 unlanded lanes are dispositioned there — this branch is the superseded pre-merge state |

The bundle stays as insurance. Delete it after #1489 has been on `main` for 30 days.

### 7. `AGENTS.md` (ERP) — the edit I destroyed

Facts: the lost edit sat on a base (`64b0db1`, D-118) that was 44 commits stale; upstream `ac3c69f`
(D-119, 21 Aug) rewrote the same file in the same direction (Codex → Claude Code handoff). The edit
is unrecoverable — unstaged, no blob, no snapshot. Resolution:
1. Native reads current `AGENTS.md` (D-119). If it already says what the lost edit was going to say —
   done, nothing to redo. This is the likely case.
2. If not, re-apply the intent on top of D-119 as a normal docs PR.
3. Process fix (mine, not the native's): never `reset --hard` on a dirty tree;
   `git switch -c <branch> origin/main` refuses instead of clobbering. Recorded in
   `ONGOING_HYGIENE_POLICIES` via P3-11 so it binds future sessions, not just this one.

---

## P2 — repeat the sweep where it has not run yet

### 8. Marsys-Mines-ERP-V2 — same disease, not yet treated

25 worktrees (23 in `/private/tmp`, which macOS purges), 32 local branches, 4 untracked WIP items.
Run the **same brief** as the Madhav sweep, with the lessons applied:
- Classify every worktree + branch (PR-merged / no-delta / unmerged-no-PR / detached / dirty) — the
  script from the Madhav run, pointed at this repo.
- Bundle → verify → delete. Keep `main` + whatever the ERP's own coordination doc names as live
  (`docs/a304-p2-foundation-runbook`? `review-81`? — the `+` marks mean they are currently checked
  out somewhere; check `_briefs/WORK-QUEUE.md` before touching any of them).
- **Never `git stash`, never `reset --hard`** on the shared checkout.
- WIP triage, each needs a native call: `.agents/` (71 skills — probably a symlink target, check),
  `.codex/` (no key, just chrome-devtools — gitignore it), `_to_delete/` (the name is the
  disposition — but look first), `_briefs/CLAUDE-CODE-P2-F15-RESUME-PROMPT.md` (live handoff? land it
  or delete it, not leave it untracked).
- Delete `docs/a30-readiness-closeout` (0 ahead of origin/main) and, after #117 merges,
  `docs/a30-phase-reports-landing`.

### 9. Madhav remote branches — 719 on origin

56 are ancestors of `origin/main` (trivially deletable). Far more are squash-merged and invisible to
`--merged`. Plan: one script that, for every `origin/*` branch, asks `gh pr list --head <b> --state
merged` and deletes the remote ref if the PR is MERGED and the tip is older than 7 days; parks the
rest in a list for the native. Dry-run first, output the list, then delete in one pass. Keep:
`main`, `campaign-coordination`, `parisesa/campaign-state`, `codex/madhav-onboarding`, any branch
named in `CURRENT_STATE` or `CAMPAIGN_COORDINATION`, and anything with an OPEN PR. Expected: ~500+
deletions. Separate PR-less branches with real deltas go to the native as a short table, same as §6.

### 10. Stash stack — 7 entries

All belong to closed campaigns (coord-d3s30, parishkara/mr-41-42, siddhanta ×2, pratijna-satya,
shabda-shuddhi ×2). Entry `stash@{1}` explicitly says "do not drop" — respect it. For each: `git
stash show -p stash@{N} | head`, check whether the diff is on `origin/main` already, and present a
7-row table to the native. Drop only on explicit approval, one at a time by **SHA not index**
(indices shift as you drop). Zero-risk alternative: `git stash list` + `git stash show -p` for each
into a file under `verification_artifacts/`, then drop all — the content is preserved, the stack is
clean.

### 11. `.claude/worktrees/{parishkara,utkarsha}-conductor-logs` — 115 MB

Closed-campaign conductor logs; already gitignored. Native decision: delete, or tar to
`~/Archive/` first. Recommendation: `tar czf` to the same place as the bundle, then delete. Two
minutes.

---

## P3 — make it not happen again

### 12. Amend `ONGOING_HYGIENE_POLICIES_v1_0.md` (governance change — needs native approval per CLAUDE.md §L)

Proposed new section **§O — Campaign-close sweep**, three rules drawn from what this sweep found:
1. A campaign is not CLOSED until its worktrees are removed, its branches are bundled+deleted or
   explicitly parked with a pointer, and its scratch directories (anything under `~`, `Apps/`,
   `/private/tmp`) are landed or deleted. The close report lists what was kept and where.
2. Agent scratch output never lands outside the repo. Execution reports, evidence, prompts go under
   `00_ARCHITECTURE/briefs/<campaign>/` at write time, not at close time. `/private/tmp` is for
   worktrees only and must be assumed gone tomorrow.
3. On a shared checkout: no `git stash`, no `reset --hard`, no checkout of another session's branch.
   Use a worktree; remove it when done.
Also record the two incidents (shared-stash pop; `reset --hard` on dirty tree) in §K's incident
register if one exists, else as a changelog entry.

### 13. `drift_detector.py` — 79 pre-existing findings

All `registry_disagreement`: `CAPABILITY_MANIFEST.json` names ~77 artifacts that
`CANONICAL_ARTIFACTS_v1_0.md §1` does not. Pre-dates every sweep. Per CLAUDE.md §C.2 the manifest is
authoritative and CANONICAL_ARTIFACTS is SUPERSEDED-historical — so the correct fix is probably to
**stop the detector cross-checking against a superseded registry** (`*_USE_MANIFEST=true` should
make this a no-op, and evidently does not for this check), not to backfill 77 rows into a dead
document. One governance session; exit code 3 → 0.

### 14. Small / optional
- ERP `.codex/config.toml` — no key, but gitignore it for symmetry with Madhav.
- `~/go` — live GOPATH, keep. `go clean -modcache` reclaims ~90 MB if Go is idle; cosmetic.
- `Apps/Madhav-branch-archive-20260822.bundle` — delete at #1489 + 30 days (§6).

---

## Sequencing summary

```
P0-2 key rotation ──┐
P0-1 fork reconcile ┴─→ P1-4 merge #1489 ─→ delete old branches ─→ (30d) delete bundle
P1-3 gitleaks fix ────→ P1-4 merge #117  ─→ P2-8 ERP sweep
P1-5 N4 ruling   (independent, one session)
P1-7 AGENTS.md   (independent, native read — probably nothing to do)
P2-9/10/11       (independent, after P0)
P3-12/13         (governance sessions, after P2)
```
Nothing in P1–P3 is blocked on anything but P0. P0-1 and P0-2 are the only two things that get worse
by waiting.
