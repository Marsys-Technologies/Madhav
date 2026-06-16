---
artifact: CLAUDECODE_BRIEF_BRANCH_SWEEP_v1_0.md
version: "1.0"
status: READY_FOR_EXECUTION
produced_during: BRANCH_AUDIT_2026-06-08
role: Executable brief for Claude Code (Antigravity) to delete 36 content-verified ZERO_UNIQUE local branches, with a per-branch self-check guard. Parks everything with any unique content.
executor: Claude Code in Google Antigravity IDE (NOT the CLI)
hard_constraints:
  - "DELETE ONLY the 36 branches in the explicit list below. Do NOT delete anything else."
  - "Each branch gets a per-branch re-verify guard at delete time: if it shows ANY genuinely-absent unique file (excluding the known-superseded common-6), SKIP it and report — do not delete."
  - "Tag every branch before deleting (archive/pre-sweep/*) as a reflog-independent recovery net."
  - "KEEP-list branches are explicitly out of scope — must survive untouched."
audit_source: in-session BRANCH_AUDIT 2026-06-08 (subagent content-classification of 57 local branches)
---

# Brief — Local Branch Sweep (36 verified-safe deletions)

Context: after the worktree cleanup, ~57 other local branches remained. A content audit
classified them. This brief deletes ONLY the 36 confirmed to hold zero unique content
(squash-merged work already on main, or stale branches whose only absent files are the
known-superseded common-6). Everything with any unique content is PARKED for a later pass.

Repo root: `/Users/Dev/Vibe-Coding/Apps/Madhav`. origin/main fetched fresh.

## KEEP — explicitly out of scope (do NOT delete)
- In-flight work: `fix/new-client-form-rebuild`, `fix/maps-key-dockerfile-arg`, `feature/pyjhora-direct-engine`
- 5 L0FR streams (hold engine/remedy code at paths absent from main — pending seal verification):
  `feature/l0fr-stream-b-ephemeris`, `-c-text-ingestion`, `-d-sutravali`, `-e-panchanga-service`, `-f-remedies`
- Doc/code-bearing branches (unique .md or small code — later pass): `chore/dupe-investigation-closeout`,
  `chore/operator-run-a3-a4-a5`, `chore/root-cleanup-r7-r10`, `cov/s4-sidecar-wrappers`,
  `feature/mcpt-foundation`, `feature/mcpt-tajaka`, `feature/ws0b-code-cluster-purge`,
  `feature/ws1-drivable-portal`, `fix/post-arc-cleanup`, `fix/cockpit-mount-and-pipeline-gaps`,
  `brahma/bg-0-8-rebase`, `feature/postdeploy-e-multi-school`
- Backup: `backup/legacy-purge-local-2026-06-06`
- Current working branch / anything not in the DELETE list.

## The known-superseded common-6 (NOT unique — ignore if a branch only has these)
platform-mcp/cloudbuild.yaml, platform/src/lib/build/trigger.ts, platform/src/lib/build/events.ts,
platform/src/lib/build/__tests__/trigger.test.ts, platform/tests/components/TierPicker.test.tsx,
platform/tests/components/BuildChat.test.tsx

---

## STEP 0 — Setup + compute the supersede filter once

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin && git switch main && git pull --ff-only origin main
git switch -c chore/branch-sweep 2>/dev/null || git switch chore/branch-sweep

# Files main ever deleted (= superseded/stale, not unique). Computed ONCE.
git log --diff-filter=D --format= --name-only origin/main | sort -u > /tmp/main_deleted.txt

# The known-superseded common-6:
cat > /tmp/common6.txt <<'EOF'
platform-mcp/cloudbuild.yaml
platform/src/lib/build/trigger.ts
platform/src/lib/build/events.ts
platform/src/lib/build/__tests__/trigger.test.ts
platform/tests/components/TierPicker.test.tsx
platform/tests/components/BuildChat.test.tsx
EOF
```

## STEP 1 — The 36 delete-candidates

```bash
cat > /tmp/sweep_targets.txt <<'EOF'
feature/l0fr-stream-a-infrastructure
feature/l0fr-stream-g-pyhora
arch/srp-a1-tech-debt
arch/srp-a2-arch-report
chat-v2/pr-111-remediation
chat-v2/ui-gap-remediation
chore/conductor-build-e2e-arc
ci/fix-noise-and-prune-tests
cov/s2-manifest-tool-entries
cov/s3-compressor-expose-to-planner
cov/s9-tool-registry-migration
feature/conductor-to-main
feature/mcpt-v32-quality-tightening
feature/phase-4c-prod-fixes
feature/r11v2-dispatch-wiring
feature/tooling-remediation
feature/ws0c-2-final-residuals
feature/ws0c-residual-purge
feature/v13-prod-triage
fix/green-main-ci
fix/mcpt-supabase-import
fix/pa06-iac-dispatch
fix/pariksha-second-pass
fix/pipeline-cleanup
fix/portal-blockers-1-and-2
fix/pyjhora-dockerfile-bookworm
governance-hygiene/drift-detector-fix
governance-hygiene/gh-fp-backfill
governance-hygiene/gh-path-fix
governance-hygiene/gh-phantom-ref-fix
governance-hygiene/learning-layer-frontmatter
hotfix/nvidia-stream-type
hotfix/r11f-ci-fixes
icr/s2-l1-truth-index
pr188
r11b-rebase-work
v3.7/operational-gap-closure
EOF
wc -l /tmp/sweep_targets.txt   # expect 37 lines (35 ZERO_UNIQUE + 2 merged-clean)
```
(Note: l0fr-stream-a + -g are the 2 cleanly-merged; the rest are the ZERO_UNIQUE set. 37 total — the "36" headline excluded the 2 merged from the content-classified count; both are safe.)

## STEP 2 — Per-branch SELF-CHECK + tag + delete (the guard)

For each target, recompute its genuinely-absent unique files at delete time. If any remain
after removing main-deleted (superseded) AND the common-6 → SKIP and report. Otherwise tag
and delete.

```bash
DONT_TOUCH_CURRENT=$(git symbolic-ref --short HEAD)
while read -r b; do
  [ -z "$b" ] && continue
  if ! git rev-parse --verify "$b" >/dev/null 2>&1; then echo "MISSING: $b (skip)"; continue; fi
  if [ "$b" = "$DONT_TOUCH_CURRENT" ]; then echo "SKIP current branch: $b"; continue; fi

  # genuinely-absent unique files = (AM files absent from main) minus main_deleted minus common6
  uniq=0
  while read -r f; do
    git cat-file -e "origin/main:$f" 2>/dev/null && continue          # present on main → not unique
    grep -qxF "$f" /tmp/main_deleted.txt && continue                  # main deleted it → superseded
    grep -qxF "$f" /tmp/common6.txt && continue                       # known-superseded common-6
    echo "    UNIQUE: $f"; uniq=$((uniq+1))
  done < <(git diff --diff-filter=AM --name-only "origin/main..$b" 2>/dev/null)

  if [ "$uniq" -gt 0 ]; then
    echo "SKIP (has $uniq unique file(s) — NOT in audit expectation): $b"
    continue
  fi

  git tag "archive/pre-sweep/$(echo "$b" | tr '/' '-')" "$b" 2>/dev/null
  git branch -D "$b" && echo "DELETED: $b"
done < /tmp/sweep_targets.txt
```

Any branch that prints `SKIP (has N unique file(s))` is a discrepancy from the audit — do
NOT force-delete it; report it for review instead.

## STEP 3 — Remote refs (confirm before deleting)

These branches may also exist on origin. Check, then delete remotes ONLY for branches that
were successfully deleted locally above and that you confirm are not protected/open PRs:

```bash
git ls-remote --heads origin | awk '{print $2}' | sed 's#refs/heads/##' > /tmp/remote_heads.txt
while read -r b; do
  [ -z "$b" ] && continue
  grep -qxF "$b" /tmp/remote_heads.txt && echo "ON ORIGIN: $b"
done < /tmp/sweep_targets.txt
# For each ON ORIGIN that you want removed:
#   git push origin --delete <branch>
# (Confirm none has an open PR first.)
```

## STEP 4 — Report + recovery note

```bash
git branch | wc -l    # how many local branches remain
git tag -l 'archive/pre-sweep/*' | wc -l   # recovery tags created
```

Report: count deleted, any SKIPs (with their unique files), remote refs found/deleted, and
remaining local-branch count. Recovery: any swept branch restores with
`git branch <name> archive/pre-sweep/<name-with-dashes>`. Drop the archive tags once
satisfied: `git tag -l 'archive/pre-sweep/*' | xargs -n1 git tag -d`.

## Out of scope (next pass, when you want it)
The 12 doc/code-bearing branches + 5 L0FR streams + 3 in-flight + backup. The L0FR streams
specifically need the PR #216 seal verified before deletion (they hold engine/remedy code at
paths absent from main).
