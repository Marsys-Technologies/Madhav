---
canonical_id: CLEANUP_PLAN_2026_05_22
status: DRAFT
authored: 2026-05-22
authored_by: Cowork audit session
scope: main-checkout working tree + git branches + sibling worktrees under /Users/Dev/Vibe-Coding/Apps/
authority: native review required before any destructive action
artifact: CLEANUP_PLAN_2026-05-22
version: "1.0"
---

# Cleanup Plan — main + worktrees (2026-05-22)

This is a survey + disposition plan. It does **not** execute anything. Every destructive command is parked under §6 for native review.

---

## 1. Snapshot summary

| Surface | Count | Notes |
|---|---:|---|
| Worktrees registered | 10 | 1 main + 9 sibling |
| Local branches | 28 | |
| Local main vs origin/main | +1 / -0 | Unpushed: MCP Transformation planning commit `c98537e8` |
| Modified files in main working tree | 13 | All `00_ARCHITECTURE/` — R11 briefs + MCPT plan + R11 queue |
| Untracked files in main working tree | 14 | R11 conductor prompts + `round11_v2/` + `CAPABILITY_MATRIX.md` + `MULTI_PROVIDER_PARITY_ROADMAP.md` + `USER_INTERACTION_PREFERENCES.md` + `SUPERSESSION_NOTE.md` |
| Stale `.git` lock files | 2 | `.git/index.lock`, `.git/packed-refs.lock` — sandbox couldn't unlink (Operation not permitted). May exist on disk; needs manual `rm` from native shell. |

---

## 2. Worktree inventory + disposition

| Path | Branch | Disposition | Rationale |
|---|---|---|---|
| `Madhav` (main repo) | `main` | **KEEP** — main checkout | Working tree has 13 modified + 14 untracked R11/MCPT planning artifacts. **Native must triage these before any branch-pruning happens** (see §3). |
| `MadhavICR` | `icr/s2-l1-truth-index` | **NATIVE DECISION** | Branch tip `[ICR-S2] Add L1 Truth Index scorer — MSR grounding coverage 17.8%` is **not on origin/main**. CLAUDE.md §E says M5 Coverage Campaign COMPLETE 2026-05-21 — but v1.3 carry-forward queue item #1 names "MSR signal-grounding gap — 419/573 signals lack explicit FORENSIC/LEL citations", which is exactly this branch's deliverable. Ask: is this work meant to land via a PR, or was it absorbed elsewhere and the branch is stale? |
| `MadhavMCPT-FDN` | `feature/mcpt-foundation` | **KEEP** | MCP Transformation Wave 0 worktree — declared ACTIVE in §E. Branch sits at `c98537e8` (the unpushed planning commit). |
| `MadhavMCPT-BPHS` | `feature/mcpt-bphs` | **KEEP** | Same as above — MCPT v3.2 Classical-grounding worktree. |
| `MadhavMCPT-JK` | `feature/mcpt-jaim-kp` | **KEEP** | MCPT v3.2 Jaimini / KP worktree. |
| `MadhavMCPT-TAJ` | `feature/mcpt-tajaka` | **KEEP** | MCPT v3.3 Tajaka worktree. |
| `MadhavMCPT-DPT` | `feature/mcpt-depth` | **KEEP** | MCPT v3.3 Depth worktree. |
| `MadhavMCPT-GRD` | `feature/mcpt-grounding` | **KEEP** | MCPT v3.4 Grounding worktree. |
| `MadhavMCPT-FIN` | `feature/mcpt-final` | **KEEP** | MCPT v3.4 Final / red-team / main-merge worktree. |
| `MadhavR11` | `chat-v2/round11-claude-parity` | **RETIRE** | Branch is fully merged to `origin/main` (HEAD `2cabdbbd` = origin/main tip). Upstream tracking already stripped. Safe to `git worktree remove MadhavR11` then `git branch -D chat-v2/round11-claude-parity`. |
| `marsys-m6-prospective` | `feature/m6-prospective-testing` | **NATIVE DECISION** | Branch tip `M6-A-S1: PHASE_M6_PLAN_v1_0.md authored; M6 ACTIVE` is **not on origin/main**. CLAUDE.md §F says M5 is the active macro-phase; §L explicitly forbids pre-building infrastructure for later macro-phases. Either (a) the M6 scaffold was a draft that should never land, (b) it was authored prematurely and should be deferred, or (c) §F is now stale and M6 is real. The branch is 656 commits behind main — even if you want to land it, it needs a serious rebase. |

> Note: every worktree is shown `prunable` in `git worktree list` because this audit was run from a sandbox that doesn't share a filesystem view of `/Users/Dev/Vibe-Coding/Apps/`. On your machine, those entries are real directories — don't read `prunable` as "git wants me to delete them."

---

## 3. main working-tree triage (13 modified + 14 untracked)

All staged work is in `00_ARCHITECTURE/`. None of it is application code. None is in the §M.16 / cutover hot paths.

### 3a. Modified files (13)

All are R11 / MCPT planning artifacts that were already part of the planning workstream:

```
00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md
00_ARCHITECTURE/CONDUCTOR/session_queue_R11.yaml
00_ARCHITECTURE/chat_v2_briefs/round11/NATIVE_RULINGS_v1_0.md
00_ARCHITECTURE/chat_v2_briefs/round11/O-S1-system-prompt-layout-audit.md
00_ARCHITECTURE/chat_v2_briefs/round11/O-S2-prompt-cache-breakpoints.md
00_ARCHITECTURE/chat_v2_briefs/round11/O-S3-agentic-tool-loop.md
00_ARCHITECTURE/chat_v2_briefs/round11/O-S4-inline-citation-parity.md
00_ARCHITECTURE/chat_v2_briefs/round11/O-S5-adaptive-thinking-effort.md
00_ARCHITECTURE/chat_v2_briefs/round11/R11_MASTER_PLAN_v1_0.md
00_ARCHITECTURE/chat_v2_briefs/round11/S-S2-smooth-stream-v3-rate-target.md
00_ARCHITECTURE/chat_v2_briefs/round11/S-S4-inline-tool-cards.md
00_ARCHITECTURE/chat_v2_briefs/round11/V-S0-runtime-user-toggle.md
00_ARCHITECTURE/chat_v2_briefs/round11/V-S1-claude-typography-stack.md
```

**Recommendation: review + commit on a new branch** rather than directly on main. Suggested branch name: `chat-v2/round11-v2-planning`. These look like the work-in-progress that produced the `round11_v2/` directory; preserving them in a single coherent commit will pair them with that new directory.

### 3b. Untracked files (14 items)

```
00_ARCHITECTURE/CAPABILITY_MATRIX.md                                   ← Claude Takeover governance — KEEP, COMMIT
00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md                       ← Claude Takeover governance — KEEP, COMMIT
00_ARCHITECTURE/USER_INTERACTION_PREFERENCES.md                        ← Cowork interaction rules — KEEP, COMMIT
00_ARCHITECTURE/chat_v2_briefs/round11/SUPERSESSION_NOTE.md            ← R11 v1 → v2 supersession marker — KEEP, COMMIT
00_ARCHITECTURE/chat_v2_briefs/round11_v2/                             ← Claude Takeover active arc (61 files: 4 governance + phase-A/ 17 + phase-B/ 12 + phase-CDE/ 28) — KEEP, COMMIT
  ├─ R11V2_MASTER_PLAN_v1_0.md                                         ← Umbrella plan
  ├─ PATTERN_2PLUS_LAUNCH_GUIDE.md                                     ← Multi-session backup launch path
  ├─ META_CONDUCTOR_KICKOFF_PROMPT.md                                  ← PRIMARY launch path (Meta-Conductor single-session)
  ├─ phase-A/ (17 files: R11A_PLAN + 14 briefs + 2 Claude Code prompts)
  ├─ phase-B/ (12 files: R11B_PLAN + 10 briefs + 1 KICKOFF)
  └─ phase-CDE/ (28 files: R11CDE_PLAN + 27 briefs + 1 KICKOFF)
00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_META_R11_v1_0.md             ← Meta-Conductor Level-0 spec — KEEP, COMMIT
00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11A_v1_0.md                 ← R11.A Level-1 Conductor — KEEP, COMMIT
00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11B_v1_0.md                 ← R11.B Level-1 Conductor — KEEP, COMMIT
00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11CDE_v1_0.md               ← R11.CDE Level-1 Conductor — KEEP, COMMIT
00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_META.md                          ← MCP Transformation (separate workstream) — KEEP, COMMIT
00_ARCHITECTURE/CONDUCTOR/MCP_DEPLOY_AND_VERIFY_PROMPT_v1_0.md          ← MCP Transformation — KEEP, COMMIT
00_ARCHITECTURE/CONDUCTOR/session_queue_R11A.yaml                       ← R11.A queue (14 entries) — KEEP, COMMIT
00_ARCHITECTURE/CONDUCTOR/session_queue_R11B.yaml                       ← R11.B queue (10 entries) — KEEP, COMMIT
00_ARCHITECTURE/CONDUCTOR/session_queue_R11CDE.yaml                     ← R11.CDE queue (27 entries) — KEEP, COMMIT
```

**Recommendation: keep all of these.** Per CLAUDE.md they are exactly the deliverables an active planning session produces. `SUPERSESSION_NOTE.md` + `round11_v2/` indicates a deliberate redesign of R11. None of these are accidental temp files.

Add them to the same `chat-v2/round11-v2-planning` branch as the modified files in §3a.

### 3c. The 1 already-committed-but-unpushed commit on local main

```
c98537e8 MCP Transformation: planning artifacts (master plan, 17 briefs, 7 queues, 7 kickoffs, setup script)
```

CLAUDE.md §E declares the MCP Transformation workstream as ACTIVE pending Wave 0. The 7 MCPT worktrees are sitting at this exact SHA. **Push this to origin/main** — that flushes the planning commit and brings the 7 MCPT branches into "0 ahead / 0 behind" parity with origin/main. Suggested: `git push origin main`.

---

## 4. Branch disposition (28 total)

### 4a. SAFE TO DELETE — fully merged via true merge (5)

| Branch | Evidence |
|---|---|
| `chat-v2/round11-claude-parity` | HEAD `2cabdbbd` = origin/main tip |
| `cov/s10-sade-sati-migration` | merged-into-origin/main per `git branch --merged origin/main` |
| `feature/phase-4c-panchang` | merged-into-origin/main |
| `fix/panchang-bootstrap-guard-target` | merged-into-origin/main |
| `perf/s2-asset-catalog` | merged-into-origin/main |

### 4b. SAFE TO DELETE — squash/cherry-picked content on origin/main (6)

These branches each have N "unique" commits, but each commit's content is present on origin/main with a different SHA (squash-merged PR):

| Branch | Match on main |
|---|---|
| `cov/s2-manifest-tool-entries` | `03439cc3 [COV-S2] … (#119)` |
| `cov/s3-compressor-expose-to-planner` | `e9cf20dc [COV-S3] … (#123)` |
| `cov/s9-tool-registry-migration` | `81e3230e [COV-S9] … (#120)` |
| `chat-v2/ui-gap-remediation` | `bbd75eb8 feat(panchang): chat-side enrichment` |
| `governance-hygiene/drift-detector-fix` | `d8c1d996 fix(governance): harden drift_detector.py (#113)` |
| `feature/phase-4c-prod-fixes` | All 4 commits matched on main (F.2 fix, F.1 brief, v5.0 brief, CF.V13.4 queue item) |

These need `-D` (force delete) because git's "merged" detector only finds true-merge parents, not squash/cherry-picks.

### 4c. SAFE TO DELETE — remote branch already gone (4)

Branches whose upstream was deleted from origin (visible as `[origin/...: gone]` in `git branch -vv`):

| Branch | |
|---|---|
| `governance-hygiene/gh-fp-backfill` | upstream gone |
| `governance-hygiene/gh-path-fix` | upstream gone |
| `governance-hygiene/gh-phantom-ref-fix` | upstream gone |
| `governance-hygiene/learning-layer-frontmatter` | upstream gone |

These almost certainly correspond to closed/merged PRs whose source branches were deleted on GitHub. The local copies are residue.

### 4d. KEEP — active workstreams (10)

| Branch | Reason |
|---|---|
| `main` | obvious |
| `feature/conductor-to-main` | §E Conductor workstream `ACTIVE — cherry-pick to main pending`. 23 unique commits, 265 behind. Cherry-pick procedure is documented in `00_ARCHITECTURE/CONDUCTOR/WAVE_2_MIGRATION_NOTE.md`. |
| `feature/mcpt-foundation` | MCPT Wave 0 (FDN worktree) |
| `feature/mcpt-bphs` | MCPT v3.2 (BPHS worktree) |
| `feature/mcpt-jaim-kp` | MCPT v3.2 (JK worktree) |
| `feature/mcpt-tajaka` | MCPT v3.3 (TAJ worktree) |
| `feature/mcpt-depth` | MCPT v3.3 (DPT worktree) |
| `feature/mcpt-grounding` | MCPT v3.4 (GRD worktree) |
| `feature/mcpt-final` | MCPT v3.4 (FIN worktree) — also has remote upstream `origin/feature/mcpt-final` |

### 4e. NATIVE DECISION REQUIRED (3)

| Branch | Question |
|---|---|
| `chat-v2/pr-111-remediation` | 5 unique governance-doc commits (AC.3 through AC.8 + cloudbuild build-args). None match by subject on origin/main. §E v3.3 says "PR #112 merged to main" closed this remediation. Were the governance docs folded into other CURRENT_STATE / SESSION_LOG commits when they landed? If yes → safe to drop. If no → cherry-pick the docs commits, then drop. |
| `chore/root-cleanup-r7-r10` | Single commit `chore: archive 54 root transient files to 99_ARCHIVE per ROOT_FILE_POLICY`. Not on main. ROOT_FILE_POLICY exists and is enforced — was this archive done differently, or is this pending? |
| `cov/s4-sidecar-wrappers` | Tip is `wip(icr/s2): L1 truth index scaffolding — preserved before wrap-up orchestrator run`. WIP. This overlaps in subject with `icr/s2-l1-truth-index` — likely the same line of work in two places. |

---

## 5. Risks + ordering

Pre-flight before any destruction:

1. **Resolve lock files.** Sandbox saw `.git/index.lock` and `.git/packed-refs.lock` it couldn't unlink. From your terminal:
   ```bash
   ls -la /Users/Dev/Vibe-Coding/Apps/Madhav/.git/*.lock
   # if no other git process is running:
   rm -f /Users/Dev/Vibe-Coding/Apps/Madhav/.git/index.lock /Users/Dev/Vibe-Coding/Apps/Madhav/.git/packed-refs.lock
   ```
2. **`git fetch --all --prune` after lock cleanup** — refreshes the remote view so any "gone" determinations are current.
3. **Commit + push main's planning work first** (§3 + §3c). If you delete `chat-v2/round11-claude-parity` before saving the R11 working-tree changes, nothing is lost (they're untracked / unstaged, not on that branch) — but commit anyway so the recovery path is `git reflog` instead of "hope".
4. **MCPT branches are not yet on origin** for 6 of 7. After pushing main, you may want to also push the seven `feature/mcpt-*` branches so the Conductor / Antigravity sub-agents have a remote to base against:
   ```bash
   for b in foundation bphs jaim-kp tajaka depth grounding; do git push -u origin feature/mcpt-$b; done
   # feature/mcpt-final already has upstream
   ```

Order of operations once §4e questions are answered:

```
(a) lock cleanup → fetch → verify
(b) commit R11/MCPT planning work to chat-v2/round11-v2-planning
(c) git push origin main
(d) delete §4a branches (true-merged, plain -d works)
(e) delete §4b branches (squash-merged, need -D)
(f) delete §4c branches (upstream gone, need -D)
(g) git worktree remove MadhavR11; git worktree prune
(h) act on §4e decisions
(i) act on MadhavICR / marsys-m6-prospective decisions (§2)
```

---

## 6. Concrete commands (parked — do not run without native sign-off)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# § 5.1 — lock cleanup (run only after confirming no live git process)
# rm -f .git/index.lock .git/packed-refs.lock

# § 5.2 — refresh
# git fetch --all --prune

# § 5.3b — commit R11/MCPT planning work
# git checkout -b chat-v2/round11-v2-planning
# git add 00_ARCHITECTURE/
# git commit -m "plan(r11-v2): R11 supersession + round11_v2 master plan + conductor prompts + capability matrix + multi-provider parity roadmap"
# git checkout main

# § 5.3c — push the MCP Transformation planning commit
# git push origin main

# § 5.4a-c — delete merged + squashed + gone branches (review names before running)
# for b in chat-v2/round11-claude-parity cov/s10-sade-sati-migration feature/phase-4c-panchang fix/panchang-bootstrap-guard-target perf/s2-asset-catalog; do git branch -d $b; done
# for b in cov/s2-manifest-tool-entries cov/s3-compressor-expose-to-planner cov/s9-tool-registry-migration chat-v2/ui-gap-remediation governance-hygiene/drift-detector-fix feature/phase-4c-prod-fixes; do git branch -D $b; done
# for b in governance-hygiene/gh-fp-backfill governance-hygiene/gh-path-fix governance-hygiene/gh-phantom-ref-fix governance-hygiene/learning-layer-frontmatter; do git branch -D $b; done

# § 5.g — retire MadhavR11 worktree
# git worktree remove /Users/Dev/Vibe-Coding/Apps/MadhavR11
# git worktree prune

# § 5.4d — push MCPT branches so Antigravity sub-agents have remotes
# for b in foundation bphs jaim-kp tajaka depth grounding; do git push -u origin feature/mcpt-$b; done
```

---

## 7. Open questions the native must answer

1. `chat-v2/pr-111-remediation` — drop or cherry-pick? (5 governance docs commits not on main)
2. `chore/root-cleanup-r7-r10` — drop or land? (1 commit archiving 54 root files)
3. `cov/s4-sidecar-wrappers` — drop or land? (WIP carrying ICR/s2 scaffolding)
4. `icr/s2-l1-truth-index` + `MadhavICR` worktree — does the v1.3 carry-forward audit item #1 (MSR signal-grounding) land via this branch or a fresh one? CLAUDE.md §E declares the M5 Coverage Campaign COMPLETE — is this branch obsolete or carrying its follow-on?
5. `feature/m6-prospective-testing` + `marsys-m6-prospective` worktree — drop (premature per §L), defer (rebase later when M6 is officially active), or land (M5 is implicitly done and §F should be amended)?
6. Should `feature/conductor-to-main` (23 commits, 265 behind) be cherry-picked to main soon, or held until after MCPT Wave 0 ships? §E says "cherry-pick to main pending (Wave 1 split-PR PR 1)" — is that gated on anything specific?

Once those six are answered, the cleanup is mechanical.

---

*End of CLEANUP_PLAN_2026-05-22.md*
