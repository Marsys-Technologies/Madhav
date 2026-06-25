---
artifact: BRANCH_ADJUDICATION_MERGE_OR_DELETE_v1_0.md
canonical_id: BRANCH_ADJUDICATION_MERGE_OR_DELETE
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
parent: GIT_RECONCILE_MAIN_PROD_SYNC_v1_0.md
purpose: >
  Resolve EVERY branch (local + remote) to a definitive MERGE or DELETE outcome — nothing left
  hanging. The verdict for each must come from a real per-branch content audit (does this work belong
  on main, is it superseded, does it still apply on top of current main), not from ahead/behind counts.
  Execute the certain outcomes this pass; sequence the foundation-merges before the regenerate-everything
  run so the foundation is complete and we regenerate once.
audience: Claude Code (Antigravity)
---

# Branch adjudication — every branch ends as MERGE or DELETE

## §0 — Native intent
"Do a full audit to be certain what needs to be merged and what needs to be deleted. I don't want to
keep anything hanging." So: NO permanent "review/hold" bucket. Each branch → a final verdict +
evidence. The only allowed verdicts:
- **DELETE** — content already on main (cherry all `-`), or a ghost, or a superseded/abandoned
  experiment the audit shows is not wanted.
- **MERGE** — unique work that belongs on main and applies cleanly (or near-cleanly) on current main.
- **MERGE-AFTER-REWORK** — unique work that is WANTED but cannot be merged as-is (far behind main,
  conflicts, partial supersession). Still resolves to "merge", but via rebase / cherry-pick / re-author
  of the wanted subset. The audit specifies exactly what rework. (This is NOT "hold" — it's a merge with
  a defined path; it just may run as its own focused sub-task.)
A branch is only DELETE-for-abandoned if the audit can say WHY it's not wanted, not merely that it's old.

PRESERVE-SAFETY: `git bundle create ~/madhav-reconcile-backup-$(date +%Y%m%d).bundle --all` BEFORE any
delete. Anything deleted is recoverable from the bundle.

## §1 — Per-branch audit protocol (apply to ALL local + remote branches)
For each branch run, and record:
1. `git cherry -v main origin/<branch>` → count unique (`+`) commits. Zero unique → DELETE (already
   shipped); skip to next.
2. `git diff main...origin/<branch> --stat` → classify the unique content:
   - **CODE/MIGRATION/DATA** (writers, src, migrations, MCP tools, capability manifest) — high stakes.
   - **DOCS/GOVERNANCE/CONDUCTOR-LOGS** (.md briefs, session logs, smriti) — low stakes; usually DELETE
     unless the doc is a canonical artifact not yet on main (then MERGE the doc).
3. APPLICABILITY check (the certainty step): does the unique work still apply / is it still wanted on
   CURRENT main?
   - Is its feature already implemented differently on main? (superseded → DELETE with reason)
   - Does it touch files heavily changed since it forked? (`git log --oneline main ^origin/<branch> --
     <paths>`) → conflict risk → MERGE-AFTER-REWORK.
   - Is it foundation (L0/L1) work the native's regenerate-everything run should build on? → MERGE or
     MERGE-AFTER-REWORK (never DELETE foundation code without explicit native confirmation).
4. CONFLICT probe for MERGE candidates: `git merge-tree $(git merge-base main origin/<branch>) main
   origin/<branch>` (or a throwaway `git merge --no-commit --no-ff` in a scratch worktree, then abort) →
   clean? → MERGE. Conflicts? → MERGE-AFTER-REWORK with the conflicting paths named.
5. VERDICT + one-line reason + (for MERGE-AFTER-REWORK) the exact rework.

## §2 — Known inputs from the Phase-1 audit (start here, then verify each)
DELETE (proven zero-unique / ghost — re-confirm cherry, then delete):
conductor/stream-b, feature/l0-phase-beta, feature/l0fr-stream-f-remedies,
feature/l1-closure-p-c-governance, feature/mcpt-foundation, fix/new-client-form-rebuild,
feature/cicd-cleanup-efficiency. Plus local: feature/admin-password-mgmt, feature/admin-tab-overhaul.

ADJUDICATE (have unique commits — audit per §1, assign MERGE / MERGE-AFTER-REWORK / DELETE-with-reason):
- **L0 foundation code (lean MERGE — wanted for the regen foundation unless audit proves superseded):**
  feature/l0fr-stream-b-ephemeris (ephemeris engine + 6 caps), feature/l0fr-stream-c-text-ingestion
  (classical-text ingestion+retrieval, 5 MCP tools), feature/l0fr-stream-d-sutravali (1907-line
  extractor, 1213 rules), feature/postdeploy-e-multi-school (dual-ayanamsha concordance + bodha_graph —
  only 42 behind), feature/ganita-naming-reconciliation (migration 195 + asset_registry + pyhora fixes).
- **Real fixes (audit if still needed vs already-fixed-on-main):** feature/postdeploy-b-lel-strip
  (l4_anchors fix), feature/postdeploy-d-governance-hygiene (drift_detector fix),
  fix/cockpit-mount-and-pipeline-gaps (cockpit fix), chore/operator-run-a3-a4-a5 (CI fixes, 798 behind —
  likely superseded).
- **Large/old feature branches (likely MERGE-AFTER-REWORK or DELETE — assess intent):**
  feature/ws1-drivable-portal (4283 insertions, 529 behind — is the portal already on main differently?),
  feature/ws0b-code-cluster-purge (31k deletions, 531 behind — a purge that may already have happened or
  may be unsafe now).
- **Docs/planning/conductor (lean DELETE unless a canonical artifact is missing from main):**
  chore/dupe-investigation-closeout, feature/bg-nakshatra-l0 (but CHECK: SUBSYSTEM_PROGRAM_ROADMAP /
  YOGA / TRANSIT master plans — are these canonical artifacts the native wants on main?),
  feature/postdeploy-a-l0-activation, feature/postdeploy-c-migration-test, track/l0-brahmagyan-build.

## §3 — EXECUTE (this pass — no hanging branches)
After the §1 audit yields a verdict for EVERY branch, and the native APPROVES the verdict table:
3.1 — BACKUP bundle (all refs).
3.2 — COMMIT the 2 untracked briefs (this one + GIT_RECONCILE + L1_REGEN) to 00_ARCHITECTURE/; drop the
  stash (GA3 complete); delete the 2 stale local branches.
3.3 — DELETE all DELETE-verdict branches (local `git branch -D`, remote `git push origin --delete`).
3.4 — MERGE all clean-MERGE-verdict branches into main (PR or ff per repo norm), CI green after each /
  batched; keep main green. Foundation (L0/L1) merges land BEFORE the regenerate-everything run.
3.5 — MERGE-AFTER-REWORK branches: execute the defined rework (rebase/cherry-pick the wanted subset) →
  merge. If a rework is large enough to need its own session, schedule it explicitly as the NEXT task
  (still "merge", just sequenced) — but it is RESOLVED (assigned an owner+plan), not left hanging.
3.6 — End state: `git branch -a` shows only main + any actively-in-rework branch with a scheduled merge.
  Zero undecided branches.

## §4 — Gate to regeneration
The regenerate-everything run does NOT start until §3 is complete: every foundation branch is either
merged or proven-not-wanted, main is green, and main==prod parity re-proven (web + job image at the new
main HEAD; rebuild the job image since foundation L0/L1 merges changed writer/migration code). THEN the
NATIVE_BIRTH bug-class sweep, THEN regenerate. This is the whole point: regenerate ONCE on a foundation
that is complete and correct.

## §5 — Deliverables + guardrails
DELIVER: the per-branch verdict table (branch → unique-commit count → content class → applicability →
conflict probe → VERDICT → reason → rework-if-any); then post-execution, what merged / deleted / rework-
scheduled + the backup bundle path + final `git branch -a`.
GUARDRAILS: bundle backup before any delete; NEVER delete foundation (L0/L1) code branches without an
explicit native confirmation of "not wanted"; far-behind branches are MERGE-AFTER-REWORK, never a blind
merge that breaks main; nothing is left as "review/hold" — every branch resolves. Native approves the
§2 verdict table before §3 executes.
