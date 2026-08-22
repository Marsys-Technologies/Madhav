---
canonical_id: CLAUDECODE_BRIEF_WORKTREE_AND_STRAY_ARTIFACT_SWEEP
version: 1.0
status: PROPOSED
date: 2026-08-22
author: Claude Code (Fable 5), at native's request
scope: post-PARIŚEṢA-V4 hygiene — stray artifacts at `Apps/` level, 111 registered worktrees, ~100 local branch refs, one plaintext credential
may_touch:
  - /Users/Dev/Vibe-Coding/Apps/{00_ARCHITECTURE,CONDUCTOR_LOG.md,.worktrees,SALVAGE_LEDGER.md,pp-fix1,Madhav-worktrees}
  - registered worktree paths under /Users/Dev/par-night, /private/tmp, .claude/worktrees, .codex/worktrees
  - local branch refs (bundle-then-delete)
  - .gitignore
  - verification_artifacts/DEFECT_SALVAGE_2026-08-05/
  - 00_ARCHITECTURE/briefs/{sampurti,parisesa}/
must_not_touch:
  - origin/* (no remote branch deletion in this brief)
  - anything pariprashna-named (live campaign)
  - platform/** source, migrations, CI
  - the two long-lived state branches' content: campaign-coordination, parisesa/campaign-state
---

# Worktree + Stray-Artifact Sweep — decisions and execution plan

## 0. What was found (evidence, 2026-08-22 22:30–23:10 IST)

Six items the native asked about all live in `/Users/Dev/Vibe-Coding/Apps/` — the **parent**
of the repo — not inside it. Four are wrong-cwd accidents, one is a redundant worktree, one is
a genuine record with no other copy.

| Item | Verdict | Evidence |
|---|---|---|
| `Apps/00_ARCHITECTURE/` (28 KB) | junk | two `.DS_Store` + a 7-line truncated `CONDUCTOR_HALT_LOG.md`; the real 42 KB one is at `00_ARCHITECTURE/CONDUCTOR/l1-ganita-build/` |
| `Apps/CONDUCTOR_LOG.md` (64 B) | junk | two lines, "Resumed from session: A-01"; 18 real logs under `00_ARCHITECTURE/CONDUCTOR/` |
| `Apps/.worktrees/samapti` | junk | empty dir |
| `Apps/pp-fix1/` (1.6 GB) | redundant worktree | branch `fix/prospective-ledger-empty-daterange`; `prospective_ledger.ts` byte-identical to `origin/main` (fix landed via PARIPŪRṆA 2026-08-15) |
| `Apps/Madhav-worktrees/codex-onboarding` | redundant worktree | every file on `codex/madhav-onboarding` is on main; main is *ahead* (MSR_v5_0 row) |
| `Apps/Madhav-worktrees/codex-onboarding-coordination` | worktree redundant; 1 file to rescue | `CAMPAIGN_COORDINATION.md` delta is subsumed by `origin/campaign-coordination` (1 stray line); `SAMPURTI_SESSION_LOG.md` (20 lines, Δ3 session notes incl. OOM-kill diagnosis) exists nowhere else |
| `Apps/SALVAGE_LEDGER.md` (34 KB) | **keep — sole copy** | 2026-08-05 DEFECT_SALVAGE session ledger: Gate-0 halts, credential-paste incident + rotation, real prod DB writes with before/after tier counts (`main` 18cd00fd→6f1b8d45). Not in repo, not in git history. Secret-scanned clean (only a `<user>:<password>` placeholder) |

Wider finding while looking: the repo had **205 registered worktrees** at first count, **112**
ten minutes later (49 `par-night/wt` registrations vanished; that dir is now 0 B — something else
was pruning concurrently, so **re-run classification at execution time**). Remaining 111 non-main
worktrees consume ≈ **57 GB**: `par-night/codex-wt` 33 G · `/private/tmp/claude-504` 14 G (worktrees
only; scratchpads stay) · `.claude/worktrees` 8.4 G · `.codex/worktrees` 1.2 G · Apps-level ≈ 2.2 G.

Classification of the 111 (script: `/tmp/wtclass.json`, re-generate at execution):

| Class | n | Disposition |
|---|---|---|
| PR-MERGED (branch's PR merged) | 58 | remove worktree; delete local branch |
| NO-DELTA (0 commits ahead / empty diff) | 3 | same |
| DETACHED HEAD | 13 | remove worktree (5 "dirty" = regenerated `platform/src/generated/projections/*.json` + `R1_PROJECTION_COMPILER_REPORT.md` only — codegen noise, not work) |
| Lease / coordination-log forks | 8 | remove; delete — every line is in `origin/campaign-coordination` (0–2 stray lines, checked per branch) |
| Codex `v4-*` fix branches, no PR | 25 | remove; delete — each defect is `LANDED` via a *differently named* PR (squash hides it from `git cherry`): F-117 #1320/#1415 · F-133 #1321 · F-25 #1371 · F-26 #1370 · F-27 #1406 · F-33 #1369 · F-34 #1315 · F-41 #1304 · F-53 #1336 (ledger: SERVICE_CLOSED) · F-06 #1411 · D-08 #1405 · F-155 profile #1463 · SF-002/004 OAuth #1413/#1470 · aspect-authority + fact-pin + assessment-pointer → squash 967f08da3 (#1319) per ledger F-64/F-18 evidence |
| `parisesa/repair-F182-mantra-sweep` | 1 | remove; delete — F-182 merged as #1438 from a sibling branch |
| `codex/v4-fallback-evidence` | 1 | **rescue 35 evidence JSONs** (`state/codex-v4/*`, 0 of 35 on main or on campaign-state), then remove |
| `parisesa/campaign-state` (179 ahead, in sync with origin) | 1 | **land onto main** — it is the V4 campaign record (ledger.json, journal.ndjson, phase0 batches, GA3 rebuild BEFORE/AFTER artifacts); purely additive (130 files, 0 deletions). Precedent: PR #1488 (this checkout) already lands SAMPURTI/UTKARSA/EKAVAKYATA records the same way |
| `campaign-coordination` (330 ahead, in sync with origin) | 1 | keep branch (long-lived by design); remove worktree |

**Security finding (not in the original ask, must not be buried):** `.codex/config.toml`
(untracked, NOT gitignored) holds a production MCP key in plaintext
(`mcp_prod_eeNr…`, `marsys-jis-direct` URL query-string). It was one `git add -A` from being
committed, and has now appeared in at least one agent transcript. Disposition: gitignore it
(Phase 5) and **recommend rotation** — rotation itself is the native's action, not this brief's.

## 1. Decisions taken (the calls)

1. **Delete outright:** `Apps/00_ARCHITECTURE/`, `Apps/CONDUCTOR_LOG.md`, `Apps/.worktrees/`.
2. **Land on main** (through the already-open salvage PR #1488, which exists for exactly this):
   `SALVAGE_LEDGER.md`, `SAMPURTI_SESSION_LOG.md`, the 35 `state/codex-v4` evidence files,
   the whole `parisesa/campaign-state` tree, and the 7 untracked root `PARISESA_*.md` prompts.
3. **Remove all 111 worktrees.** Dirty ones are codegen noise → `--force`.
4. **Delete ~98 local branch refs** — but only after writing them to ONE git bundle outside the
   repo, so every deleted ref is recoverable with a single `git fetch <bundle>`. No remote deletes.
5. **Keep:** `campaign-coordination`, `parisesa/campaign-state` (until its landing PR merges),
   `salvage/wrapped-campaign-artifacts` (current), `main`.
6. **Gitignore** `.codex/config.toml`, `.codex/worktrees/`, `.claude/worktrees/`.
7. **Do not** rotate credentials, touch origin branches, or touch anything `pariprashna-*`.

Where things land (per `ROOT_FILE_POLICY.md §4`):
- `SALVAGE_LEDGER.md` → `verification_artifacts/DEFECT_SALVAGE_2026-08-05/SALVAGE_LEDGER.md` (audit/verification record; content verbatim — it is append-only)
- `SAMPURTI_SESSION_LOG.md` → `00_ARCHITECTURE/briefs/sampurti/SAMPURTI_SESSION_LOG_delta3.md`
- `state/codex-v4/*.json` → `00_ARCHITECTURE/briefs/parisesa/state/codex-v4/` (sits beside campaign-state's own `state/` tree)
- root `PARISESA_*.md` ×7 → `00_ARCHITECTURE/briefs/parisesa/prompts/`
- `parisesa/campaign-state` → `git merge --no-ff` into the salvage branch (history preserved; fall back to tree-copy if any conflict appears)

## 2. Execution phases

### Phase 0 — Gates (read-only)
- `pgrep -fl "parisesa|par-night"` → must be empty (no conductor). Confirm no other agent is
  mid-sweep: `git worktree list | wc -l` stable across two reads 60 s apart.
- Re-run the classification script; diff against the table above; **stop on any new
  `UNMERGED-no-PR` branch not listed here.**
- `git -C <each dirty worktree> status --porcelain --untracked-files=no` → only
  `generated/projections/*` + `R1_PROJECTION_COMPILER_REPORT.md`; anything else → stop, report.

### Phase 1 — Apps-level junk
```
rm -rf /Users/Dev/Vibe-Coding/Apps/00_ARCHITECTURE \
       /Users/Dev/Vibe-Coding/Apps/CONDUCTOR_LOG.md \
       /Users/Dev/Vibe-Coding/Apps/.worktrees
```

### Phase 2 — Rescue + land (on `salvage/wrapped-campaign-artifacts`)
1. `mkdir -p verification_artifacts/DEFECT_SALVAGE_2026-08-05 && git mv`-equivalent copy of
   `Apps/SALVAGE_LEDGER.md` → there; delete the original only after the commit exists.
2. `git show codex/onboarding-lease:SAMPURTI_SESSION_LOG.md > 00_ARCHITECTURE/briefs/sampurti/SAMPURTI_SESSION_LOG_delta3.md`
3. `git archive codex/v4-fallback-evidence state/codex-v4 | tar -x -C 00_ARCHITECTURE/briefs/parisesa/state/` (re-rooted)
4. `mkdir 00_ARCHITECTURE/briefs/parisesa/prompts && git mv PARISESA_*.md` there.
5. Commit: `chore(salvage): land DEFECT_SALVAGE ledger, SAMPURTI Δ3 log, codex-v4 evidence, PARIŚEṢA-V4 prompts`
6. `git merge --no-ff parisesa/campaign-state -m "docs(parisesa): land PARIŚEṢA-V4 campaign-state record onto main"` — expect 0 conflicts (additive). If conflicts: abort, tree-copy instead.
7. `python platform/scripts/governance/drift_detector.py` — new files under `00_ARCHITECTURE/` may need manifest/FILE_REGISTRY rows; fix before push.
8. Push; PR #1488 picks it up. Do **not** merge the PR in this brief — the native reviews.

### Phase 3 — Worktree removal (≈57 GB)
```
git worktree list --porcelain | awk '/^worktree /{print $2}' | grep -v '/Apps/Madhav$' \
  | while read p; do git worktree remove --force "$p"; done
git worktree prune
```
Then `ls /Users/Dev/par-night /private/tmp | grep -i parisesa` and report leftover
*non-registered* dirs (e.g. `par-night/parisesa-v4-conductor` 403 M, `f117-fix`, `f178-f180`)
for the native — they are not worktrees and are outside this brief's delete authority.

### Phase 4 — Branch refs (bundle → delete)
```
KEEP='^(main|campaign-coordination|parisesa/campaign-state|salvage/wrapped-campaign-artifacts)$'
git for-each-ref --format='%(refname:short)' refs/heads | grep -Ev "$KEEP" > /tmp/del.txt
git bundle create /Users/Dev/Vibe-Coding/Apps/Madhav-branch-archive-20260822.bundle $(cat /tmp/del.txt)
git bundle verify /Users/Dev/Vibe-Coding/Apps/Madhav-branch-archive-20260822.bundle   # must PASS
xargs git branch -D < /tmp/del.txt
```
Recovery, if ever needed: `git fetch <bundle> <branch>:<branch>`.
Local-only; `origin/*` untouched. A list of remote branches that are now merged/superseded is
emitted to `/tmp/remote-candidates.txt` for a *separate* native decision.

### Phase 5 — Prevent recurrence
Append to `.gitignore`:
```
# agent runtime state — never commit (config.toml carries a live MCP key)
.codex/config.toml
.codex/worktrees/
.claude/worktrees/
```
(`.codex/agents/*.toml` stay tracked — they are on main by design.)

### Phase 6 — Verify (evidence before claims)
- `git worktree list | wc -l` → `1`
- `git branch | wc -l` → `4`
- `git bundle verify …` → PASS (re-run)
- `du -sh /Users/Dev/par-night /private/tmp/claude-504 .claude/worktrees .codex/worktrees`
- `git check-ignore .codex/config.toml` → ignored
- `drift_detector.py` + `schema_validator.py` clean; PR #1488 CI green
- `ls /Users/Dev/Vibe-Coding/Apps/` shows only: `Madhav`, the bundle, other projects

## 3. Residuals handed to the native (not executed here)
1. **Rotate `mcp_prod_eeNr…`** (Cloud Run MCP API key).
2. Decide remote-branch deletion from `/tmp/remote-candidates.txt`.
3. Non-worktree leftovers in `par-night/` and `/private/tmp/` (Phase 3 report).
4. Merge PR #1488 after review.
5. Consider an `ONGOING_HYGIENE_POLICIES` §-entry: "campaign close includes worktree + branch sweep" — governance doc change, needs native approval per CLAUDE.md §L.
