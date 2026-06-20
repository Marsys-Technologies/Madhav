# Pre-L2 Full Hygiene Pass — commit, merge, then careful cleanup (paste into Claude Code)

**Read CLAUDE.md §C first.** Goal: get the ENTIRE repo clean before L2 Bodha opens — nothing uncommitted,
nothing stranded in a worktree, nothing real lost in a stash, branch list triaged. The native ruled:
**commit-grouped-then-push (urgent), INSPECT-each-before-removing (safe — destructive ops only after
confirmation), full hygiene before L2.** Execute PHASE 1 first (it's urgent + safe); PHASES 2-4 are destructive
— do each with the confirmation gate stated, and HALT on anything ambiguous rather than guess.

## ⚠️ DESTRUCTIVE-OP RAILS
- NEVER `git stash drop` / `worktree remove` / `branch -D` until its contents are inspected AND confirmed
  empty-or-already-merged. The native's rule: inspect each, remove only the confirmed-safe.
- For ANY stash/branch/worktree whose contents are NOT clearly already-on-main, HALT and list it for the native
  to rule on — do not drop it.
- Do all of this on a clean tree AFTER Phase 1 commits (so a mistake can't lose the L0/auth/ga_structural work).

---

## PHASE 1 — COMMIT THE UNCOMMITTED PR #301 WORK (URGENT — it's only in the working tree)

**CRITICAL FINDING:** branch `feature/prashna-embed-across-layers` (HEAD d7b0b837) has **53 uncommitted changes**
that include the ENTIRE L0-permission + auth-fix + ga_structural-v2.0-final work. PR #301 on GitHub does NOT
contain these — they exist only in the working tree and would be LOST on a discard. Commit them now, grouped:

1. **ga_structural v2.0 finals:** `ga_writers/ga_structural_writer.py`,
   `pipeline/orchestrator/writers/ga_structural.py`, `GA_STRUCTURAL_REBUILD_VERIFY_v2_0.md`, the conductor halt
   logs, `_rebuild_ga_structural_v2.py` (decide: keep as a tool or drop if one-shot).
   → commit: `feat(ga_structural): v2.0 completeness rebuild — all-30-varga, graph-theoretic restored, L1-authority clean`
2. **L0 build-permission model:** `cockpit/runs/route.ts`, `cockpit/clear/route.ts`, `clear/execute/route.ts`,
   `LayerPanel.tsx`, `AssetRow.tsx`, `LayerPanel_L0Gate.test.tsx`, the new `cockpit/runs/__tests__/` +
   `cockpit/stats/__tests__/`.
   → commit: `feat(cockpit): L0 build-permission model — guest builds L1-L5, L0 super_admin global-only`
3. **Auth role rename (client→guest):** `auth/session/route.ts`, `lib/db/types.ts`, `access-control.ts`, the
   admin routes (`admin/users`, `access-requests/approve`), `me/role`, `panchang/charts`, the component files
   (`AppShell`, `AppShellRail`, `MobileNavSheet`, `ProfileSideRail`, `admin/types.ts`, `NewUserDialog`,
   `ApproveDialog`), the `clients/[id]` pages, and the updated tests (`trace_route`, `command_center`,
   `dashboard`, `AuthGate`, `AppShell`).
   → commit: `fix(auth): canonical guest role — close signup 500, align ~25 sites (client was never a user role)`
4. **Session briefs + verify docs** (untracked `00_ARCHITECTURE/BRIEFS/*`, `NIRMANA_UIUX_ENHANCEMENT_REPORT`,
   `docs/superpowers/plans/*`): commit as `docs(pre-l2): session briefs + verification records`.
   - **`design-explorations/` (untracked dir):** INSPECT first — if it's real design work, commit it; if scratch,
     gitignore or remove. HALT for native if unclear.
5. Run the full test suite + `tsc` after committing; confirm green. Push to update PR #301.
6. **Confirm PR #301 now CONTAINS the L0/auth/ga_structural diffs** (`gh pr diff 301 --stat` shows them) — the
   whole point: the PR must actually carry the verified work, not just describe it.

**After Phase 1: a reviewer/merge of #301 gets the real work.** Phases 2-4 then run on a committed-clean tree.

---

## PHASE 2 — MERGE PR #301

Once Phase 1 is pushed + CI confirms NO NEW failures vs main's known pre-existing ones (per memory, main carries
a few pre-existing CI reds — distinguish new from inherited): merge #301 to main. ga_structural v2.0 lands;
L0-permission + auth + Prashna + foundation + cosmetics all land. Confirm main HEAD has them post-merge.

---

## PHASE 3 — STASH TRIAGE (25 stashes — INSPECT each, classified below)

Per-stash disposition from the diff-stat inspection (2026-06-19). **DROP only the ALREADY-LANDED ones; HALT +
list the SUBSTANTIVE ones for native ruling — do not auto-drop those.**

| stash | contents | likely disposition (CONFIRM before acting) |
|---|---|---|
| `{0}` `{1}` | conductor halt logs (L1) | LIKELY DROP — halt logs, superseded; confirm not unique |
| `{2}` | AssetRow/LayerPanel edits | LIKELY SUPERSEDED by Phase-1 cosmetic commit — diff vs main; drop if subsumed |
| `{3}` | mig 294 ga_vastu floor 45→40 | CHECK — is mig 294 already on main? if yes drop |
| `{4}` | ga_yoga_writer 1-line | CHECK vs main; drop if present |
| `{5}` `{6}` | Bodha B1 brief / session_queue | CHECK — Bodha brief may be wanted for L2; HALT |
| `{7}` `{8}` | GA5-9 spec renames + A3 spec (460+108 lines) | **SUBSTANTIVE — HALT.** Spec content; confirm already in 00_ARCHITECTURE before any drop |
| `{9}` | clear/route + ICR detector DELETIONS (662 del) | **HALT — large deletions.** Is the ICR removal intended + already done on main? |
| `{10}` `{14}` | empty | DROP (empty) |
| `{11}` `{20}` `{21}` `{22}` | chat-v2 / consume UI (May) | LIKELY STALE — confirm superseded; HALT if any unique UI |
| `{12}` | CLAUDECODE_BRIEF.md rewrite | CHECK — root brief; likely superseded |
| `{13}` | accuracy json 1-line | LIKELY DROP |
| `{15}` `{16}` | MCPT transformation (310 lines ×2) | **SUBSTANTIVE — HALT.** MCP work; confirm landed |
| `{17}` `{18}` `{19}` | deploy.yml / brief / capability-audit (574 lines) | **{19} SUBSTANTIVE — HALT** (capability audit + SESSION_LOG 162 lines) |
| `{23}` `{24}` | router/planner (1934 + 990 lines!) | **HIGHLY SUBSTANTIVE — HALT.** Large router work; MUST confirm landed before any drop |

**Rule: every "HALT" stash gets a 3-way check — is its content already on main (`git log`/grep)? If yes → safe
drop. If no → it's unrecovered work; surface to native with the diff, do NOT drop.** Especially `{23}/{24}`
(router, ~2,900 lines) and `{7}/{8}/{19}` (specs + audit).

---

## PHASE 4 — WORKTREE + BRANCH CLEANUP (inspect each)

### Worktrees (11 — all show `prunable`, but verify)
- **5 `.claude/worktrees/agent-*`:** sub-agent scratch. `git -C <path> status` each; if zero uncommitted AND the
  branch is merged/disposable → `git worktree remove`. These are normally safe (memory: agent-* accumulate, safe
  to rm when no session active) — but status-check each first.
- **6 subsystem worktrees** (`MadhavAstrovastu/Dignity/Medical/Prashna/Transit/Yoga` on `feature/subsystem-*`):
  **INSPECT each** — `git -C <path> status --short` + `git -C <path> rev-list --count main..HEAD`. These hold
  the 7-subsystem program work ([[project-subsystem-program]]). If a worktree has uncommitted changes OR
  unmerged commits → that's real subsystem work; HALT and surface it (do NOT remove). Only remove worktrees that
  are clean AND fully merged. The subsystem program is GATED behind L2/nakshatra per memory — its branches
  likely STAY, just detach the worktree if clean.

### Branches (70 local, ~40 unmerged-to-main)
Triage in batches (per [[project-tier-b-branch-audit-pending]] approach — gh pr list + content-match):
- L0FR streams (`l0fr-stream-*`), mcpt (`mcpt-*`), panchanga, ws0/ws1 — likely merged-by-content → verify each
  has zero unmerged commits (`git rev-list --count main..<branch>`) → delete if 0.
- KEEP: `feature/subsystem-*` (active program), `feature/panchanga-service-registry` (pending its own PR per
  memory), anything with unmerged commits.
- For EACH branch with unmerged commits: surface to native (don't delete) — could be unrecovered work.
- Produce a branch-disposition table (branch → unmerged-commit-count → DELETE/KEEP/HALT) for native review
  before any `branch -D`.

---

## DELIVERABLE
- Phase 1: 4 grouped commits pushed; PR #301 confirmed to CONTAIN the L0/auth/ga_structural diffs; tests green.
- Phase 2: #301 merged; main HEAD carries all six workstreams.
- Phase 3: stash-disposition table (dropped / HALT-for-native), with proof each dropped stash is already on main.
- Phase 4: worktree + branch disposition tables; only confirmed-safe removed; everything ambiguous surfaced.
- A final `git status` (clean tree) + `git worktree list` + `git stash list` + `git branch` showing the
  end-state, and a short HYGIENE_PASS_REPORT listing what was removed and what was kept-pending-native.

**HALT-and-surface beats delete on anything not provably already-on-main. The goal is a clean tree for L2 — NOT
zero stashes/branches at the cost of losing unrecovered work.** When Phase 1+2 land and the tree is clean, L2
Bodha can open.
