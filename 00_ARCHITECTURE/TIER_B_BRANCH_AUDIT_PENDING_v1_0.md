# Tier B Branch Audit — Required Next Session

After Tier A cleanup (5 origin branches + 3 worktrees removed, PRs #221/#224 closed), 32 origin branches remain ahead of main.

## Branch inventory

**L0FR streams (likely shipped to main via earlier wave-close, branches not pruned):**
- feature/l0fr-stream-b-ephemeris
- feature/l0fr-stream-c-text-ingestion
- feature/l0fr-stream-d-sutravali
- feature/l0fr-stream-e-panchanga-service
- feature/l0fr-stream-f-remedies

**PostDeploy streams:**
- feature/postdeploy-a-l0-activation
- feature/postdeploy-b-lel-strip
- feature/postdeploy-c-migration-test
- feature/postdeploy-d-governance-hygiene
- feature/postdeploy-e-multi-school

**WS streams (per memory `tier3-merge-queue`):**
- feature/ws0b-code-cluster-purge
- feature/ws1-drivable-portal
- feature/ws2-depth-build (TIER 3 per memory)
- feature/ws3-rule-base (TIER 3 per memory)

**V13 prod:**
- feature/v13-prod-1-triage
- feature/v13-prod-data
- feature/v13-prod-portal

**Build orchestrator:**
- feature/build-orch/stream-a
- feature/build-orch/stream-b
- feature/build-orch/stream-d

**PyJHora:**
- feature/pyjhora-direct-engine
- fix/pyjhora-dockerfile-bookworm
- fix/pyjhora-dockerfile-bookworm-v2

**Other:**
- audit/forensic-render-coverage
- brahma/bg-0-8-rebase
- chore/dupe-investigation-closeout
- chore/operator-run-a3-a4-a5
- conductor/stream-b
- feature/ux-workflow-overhaul
- fix/cockpit-mount-and-pipeline-gaps
- fix/new-client-form-rebuild
- fix/pariksha-second-pass
- fix/post-arc-cleanup

## Audit approach per branch

1. `gh pr list --head <branch>` — is there an open PR? if MERGED, was it squash? if OPEN, what state?
2. `git diff --name-only origin/main..origin/<branch>` — list files changed
3. For each changed file: does it exist on main? does its content match?
4. If all substantive content matches — delete branch
5. If divergent content exists — halt, surface to native

## Recommended sequencing

Tackle one stream-batch per session (e.g. L0FR streams in one paste, postdeploy in another) rather than all 32 at once.
Estimated effort: ~1 hour per stream-batch; 4-5 stream-batches total.

## Keep

`origin/track/l0-brahmagyan-build` — intentional planning branch. DO NOT DELETE.
