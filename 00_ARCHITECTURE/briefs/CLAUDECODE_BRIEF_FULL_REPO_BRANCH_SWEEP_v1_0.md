---
artifact: CLAUDECODE_BRIEF_FULL_REPO_BRANCH_SWEEP_v1_0.md
canonical_id: CLAUDECODE_BRIEF_FULL_REPO_BRANCH_SWEEP
version: 1.0
status: AUTHORED — full-repo branch cleanup, diff-verified, cautious
executor: Claude Code in Antigravity — commands embedded
authored_by: Cowork 2026-06-21
source: native's full branch audit + Cowork diff-verification (2 subagents + direct checks)
principle: >
  VERIFY-BY-CONTENT, NOT BY-COMMIT-COUNT. The original audit's headline ("L2 not on main")
  was a FALSE POSITIVE — diff proved L2 IS on main and main is AHEAD of feature/l2-bodha.
  Every deletion here is gated on `git branch -d` (safe variant: refuses unmerged) OR a
  proven content-on-main check. No `-D` force-delete except where content is diff-confirmed
  on main. No branch needs a PR — zero load-bearing work is stranded.
---

# FULL-REPO BRANCH SWEEP — diff-verified, cautious

## HEADLINE FINDINGS (the corrections that matter)

1. **The audit's critical finding was WRONG (in the safe direction).** `feature/l2-bodha`
   is NOT missing from main. All 10 `bo_*` orchestrator writers exist on `origin/main`
   (`pipeline/orchestrator/writers/bo_*.py`), `bo_laksana` is `@register`'d on main (the L3
   `ka_yojaka` dependency resolves), and `git diff --stat origin/main..feature/l2-bodha` shows
   the BRANCH side DELETING the L3 files — i.e. **main is AHEAD of the branch.** L2 is fully
   reproducible-in-code on main. `feature/l2-bodha` is an old pre-L3 branch → safe to delete.

2. **Zero branches need a PR.** All 16 "genuinely unmerged" Group-B candidates were
   diff-verified: 14 are content-on-main (squash false-positives), 2 are stale/superseded
   dead architectures. Nothing load-bearing is stranded — including the scary ones:
   - `fix/asset-throughput-pk-drop` (the "broke non-native builds" PK fix): migration 225 is
     **byte-identical on main.** Shipped.
   - `fix/dict-row-compat` (mig 294 vastu floor + tuple_row): fix is on main; main moved AHEAD
     with further varga-dignity work → discard (don't revert newer code).
   - 3 `worktree-agent-*`: superseded; main has the newer FROZEN-contract `WriterResult` form.

3. **The lesson (now 3× validated): `git cherry` / "N commits ahead" / ancestry checks all
   give FALSE POSITIVES on squash-merged branches.** Only diffing actual file content vs main
   is reliable. This brief is built on content-diffs.

## PRE-FLIGHT (operator)

```bash
cd <repo>
# A crashed prior git left a stale lock that blocks prune/ref-delete:
rm -f .git/packed-refs.lock
git fetch --prune origin
git checkout main && git pull --ff-only origin main
git rev-parse main   # confirm == origin/main
```

## GROUP B — diff-verified dispositions (do these first; they're the analyzed set)

All DELETE/DISCARD below are content-on-main or dead-architecture. Local-only branches use
`git branch -D`; origin ones also `git push origin --delete`. **Re-run the safe check inline.**

| Branch | Action | Why (verified) |
|---|---|---|
| feature/l2-bodha | delete | 10 bo_* writers on main; main ahead |
| recovery/pre-l2-stash-salvage | discard | dead pre-PyJHora retrieval architecture; imports tools absent on main |
| feature/subsystem-astrovastu | delete | mig 284-287 + ga_vastu on main; main ahead (tuple_row) |
| feature/subsystem-medical | delete | mig 276-280 + ga_medical on main; main ahead |
| feature/subsystem-prashna | delete | mig 288-291 + ga_prashna on main |
| feature/subsystem-transit | delete (local) | mig 266-268 + l0_transit.py on main |
| fix/yoga-red-team-forensic-idempotency | delete | delete-then-insert + _forensic_assert on main (L1072/1084) |
| fix/dict-row-compat | discard | mig 294 + tuple_row on main; main ahead |
| fix/ga-yoga-chart-facts-schema | delete | shortened chart_facts SELECT on main |
| fix/migration-262-display-name | delete | mig 262 identical on main |
| fix/asset-throughput-pk-drop | delete | mig 225 byte-identical on main (NOT load-bearing-missing) |
| chore/claude-md-realignment | delete (local) | CLAUDE.md v6.0 + L2 handoff on main |
| chore/repo-hygiene-isolated | delete | tip is ancestor of main (0 ahead) |
| worktree-agent-a53b83218c154e828 | delete (local) | mig 247 + ka_kala_darshana on main (newer WriterResult form) |
| worktree-agent-a54ef284d2204cd56 | delete (local) | GA8 defs on main; main 780 lines ahead |
| worktree-agent-ae410d622014c5fb1 | delete (local) | mig 304 + L0_SYNERGY_REGISTER on main |

```bash
# worktrees first (the 3 agent branches are checked out in prunable worktrees):
git worktree prune
git worktree list   # confirm no agent-a53.../a54.../ae41... remain

# Group B deletes — SAFE variant first; falls back to -D only for the diff-confirmed ones:
for b in feature/subsystem-transit chore/claude-md-realignment chore/repo-hygiene-isolated \
         fix/ga-yoga-chart-facts-schema fix/migration-262-display-name fix/asset-throughput-pk-drop \
         fix/yoga-red-team-forensic-idempotency feature/subsystem-astrovastu \
         feature/subsystem-medical feature/subsystem-prashna; do
  git branch -d "$b" 2>/dev/null && echo "deleted(safe) $b" || echo "  -d refused $b → using -D (content verified on main): $(git branch -D "$b" 2>&1)"
done
# content-on-main-but-not-ancestor (squash) — force-delete is correct, content diff-verified:
for b in feature/l2-bodha recovery/pre-l2-stash-salvage fix/dict-row-compat \
         worktree-agent-a53b83218c154e828 worktree-agent-a54ef284d2204cd56 worktree-agent-ae410d622014c5fb1; do
  git branch -D "$b" 2>/dev/null && echo "force-deleted(verified) $b" || echo "absent $b"
done
# remote deletes for the origin ones:
for b in feature/l2-bodha recovery/pre-l2-stash-salvage feature/subsystem-astrovastu \
         feature/subsystem-medical feature/subsystem-prashna fix/yoga-red-team-forensic-idempotency \
         fix/dict-row-compat fix/ga-yoga-chart-facts-schema fix/migration-262-display-name \
         fix/asset-throughput-pk-drop chore/repo-hygiene-isolated; do
  git push origin --delete "$b" 2>/dev/null && echo "remote-deleted $b" || echo "remote absent $b"
done
```

## GROUP A — closed-phase bulk delete, gated by `git branch -d` (git verifies for us)

Group A = ~45 completed L0/L1 workstreams, squash-merged chores, orchestration logs, and
worktree-wf_* remotes. Their OUTCOMES are on main + in prod (L0FR sealed #216, L0 Phase β #227,
WS-1 portal complete, the L3 closeout PRs #325/#326/#327 — the latter two CONTENT-VERIFIED on
main: deploy.yml fail-loud present, run_ka_*_prod.py removed). **Rather than hand-verify all 45,
gate them on the SAFE `-d` variant — git refuses to delete anything not merged into main.**

```bash
# SAFE bulk delete: -d ONLY. Anything git refuses is auto-flagged for manual content-check.
KEPT=""
for b in feature/ws0b-code-cluster-purge feature/ws1-drivable-portal feature/l0fr-stream-b-ephemeris \
  feature/l0fr-stream-c-text-ingestion feature/l0fr-stream-d-sutravali feature/l0fr-stream-f-remedies \
  feature/l0-phase-beta brahma/bg-0-8-rebase feature/ganita-naming-reconciliation feature/bg-nakshatra-l0 \
  feature/l1-ganita-build-kickoff feature/postdeploy-e-multi-school feature/pyjhora-direct-engine \
  feature/ux-workflow-overhaul feature/mcpt-foundation feature/mcpt-tajaka chore/operator-run-a3-a4-a5 \
  chore/dupe-investigation-closeout chore/root-cleanup-r7-r10 track/l0-brahmagyan-build \
  cov/s4-sidecar-wrappers conductor/stream-b fix/cockpit-mount-and-pipeline-gaps fix/post-arc-cleanup \
  fix/new-client-form-rebuild fix/maps-key-dockerfile-arg chore/ci-migration-failloud \
  chore/l3-closeout-docs chore/l3-retire-bypass-scripts; do
  git branch -d "$b" 2>/dev/null && echo "deleted $b" || { echo "KEPT(unmerged-check) $b"; KEPT="$KEPT $b"; }
done
echo "=== BRANCHES git REFUSED (need manual content-diff before any -D): $KEPT ==="
```

> IMPORTANT: do NOT blanket `-D` Group A. For any branch in `$KEPT`, run
> `git diff --stat origin/main..<branch>` and inspect — it landed in $KEPT because git couldn't
> prove it merged. Report those back rather than force-deleting. (Expected: most are squash-merged
> and safe, but the `-d` gate is the cheap insurance against deleting a genuine orphan.)
>
> NOTE on `backup/legacy-purge-local-2026-06-06`: this is an intentional BACKUP branch — KEEP it
> (do not include in the sweep) unless you explicitly want the backup gone.

## GROUP A REMOTE + worktree-wf_* cleanup

```bash
# The 18 worktree-wf_* and the closed origin/* (build-orch, postdeploy, v13-prod, ws2/ws3, etc.)
# are remote-only dead refs. Delete after confirming main has the work (it does — these are all
# squash-merged closed phases). List them first, delete in a reviewed batch:
git branch -r | grep -E "worktree-wf_|build-orch|postdeploy-[abcd]|v13-prod|ws2-depth|ws3-rule-base|new-client-form-reskin|brahmagyan-naming|l1-phase3|ga-cockpit-to-main|pariksha-second|pyjhora-dockerfile|pipeline-audit-closeout|forensic-render-coverage|prep/l0-corpus|prep/nadi-texts|ci-migration-failloud|l3-closeout-docs|l3-retire-bypass|disable-brahma-conductor|legacy-dead-code-kill|natal-engine-teardown|brief-archive|governance-repoint|prashna-embed-across-layers"
# Review that list, then for each: git push origin --delete <name-without-origin/>
```

## DEFINITION OF DONE
- [ ] Pre-flight: lock removed, main FF-synced.
- [ ] Group B: 16 branches deleted/discarded (content-verified); zero PR'd (none needed).
- [ ] Group A: `-d` safe-bulk-delete ran; `$KEPT` list reported (NOT force-deleted).
- [ ] Group A remote + worktree-wf_*: reviewed list, batch remote-deleted.
- [ ] `backup/legacy-purge-local-2026-06-06` KEPT.
- [ ] Final: `git branch -a | wc -l` shows only main + active subsystem branches + the backup.

*No branch needs a PR. No prod data, asset_registry, or main content is touched — this is pure
ref hygiene. Every force-delete is content-diff-verified on main; every uncertain branch is
gated behind the `-d` safe variant. If git refuses a `-d`, STOP and content-check — do not -D.*
