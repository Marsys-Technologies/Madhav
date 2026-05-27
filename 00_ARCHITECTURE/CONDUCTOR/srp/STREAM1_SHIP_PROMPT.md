# SRP Stream 1 — Ship Prompt
# Paste this ENTIRE prompt into a Claude Code chat session.
#
# Folder: /Users/Dev/Vibe-Coding/Apps/Madhav (same as always)
# Purpose: Push fixes to origin/main, open PRs for test branches,
#          then give you the exact deploy commands to run.
# ─────────────────────────────────────────────────────────────────────────────

You are shipping the SRP Stream 1 output to production.
Run every step in order. Report each outcome before moving to the next.
Do not push, merge, or deploy anything until you have confirmed the
pre-flight checks in Steps 1–3.

---

## STEP 1 — Confirm local main is ahead of origin/main with the right commits

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

echo "=== Commits ahead of origin/main ==="
git fetch origin main --quiet
git log origin/main..main --oneline

echo ""
echo "=== Confirm both fix merges are present ==="
git log --oneline --merges | head -5
```

Expected: you should see exactly two merge commits ahead of origin/main:
  - "merge: SRP-F-1 portal fixes into main (local conductor merge)"
  - "merge: SRP-F-2 MCP sidecar fixes into main (local conductor merge)"

If you see more or fewer commits, STOP and report — do not push until confirmed.

---

## STEP 2 — Confirm fix content is in local main (spot-checks)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

echo "=== FIX-1: 14 UDA tools in primitives_registry ==="
grep -c "temporal\|kp_query\|query_kp_ruling_planets\|resonance_register\|cluster_atlas\|contradiction_register\|query_ucn_walk\|query_cdlm_lookup\|query_rm_walk\|query_jaimini_drishti\|timeline_query\|query_signal_state" \
  platform/src/lib/mcp/primitives_registry.ts

echo ""
echo "=== FIX-2: msr_sql.ts reads forward_looking from params ==="
grep "params.*forward_looking\|forward_looking.*params" \
  platform/src/lib/retrieve/msr_sql.ts | head -3

echo ""
echo "=== FIX-3: valence enum uses DB vocabulary ==="
grep "benefic\|malefic\|context-dependent" \
  platform-mcp/src/tools/query_signals.ts | head -3

echo ""
echo "=== FIX-4: SAMPLE_STEP_DAYS map in query_ephemeris ==="
grep "SAMPLE_STEP_DAYS" \
  platform-mcp/src/tools/query_ephemeris.ts | head -3

echo ""
echo "=== FIX-5: significance field name (not min_significance) ==="
grep "significance:" platform-mcp/src/tools/lel_query.ts | head -3
grep "min_significance" platform-mcp/src/tools/lel_query.ts \
  && echo "WARN: min_significance still present!" \
  || echo "OK: min_significance removed"

echo ""
echo "=== FIX-6: source_version 1.7 ==="
grep "1\.7" platform-mcp/src/tools/lel_query.ts | head -2
```

All checks should return non-empty matches (or "OK" for FIX-5 absence check).
If any check fails, STOP and report — do not push.

---

## STEP 3 — Run vitest one final time on local main before pushing

```bash
echo "=== Final vitest on platform (local main) ==="
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
npx vitest run 2>&1 | tail -15

echo ""
echo "=== Final vitest on platform-mcp (local main) ==="
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform-mcp
npx vitest run 2>&1 | tail -15
```

Expected: 0 failures in both. If there are failures, report them verbatim.
Do not push if tests fail.

---

## STEP 4 — Push local main to origin/main

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git push origin main
echo "Push exit code: $?"
git log origin/main..main --oneline | wc -l | xargs echo "Commits still ahead of origin/main:"
```

Expected after push: "Commits still ahead of origin/main: 0"

---

## STEP 5 — Push all test branches to origin

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

for branch in test/srp-t1-portal-unit test/srp-t2-mcp-unit \
              test/srp-t3-integration test/srp-t4-system; do
  wt_path=$(git worktree list | grep "$branch" | awk '{print $1}')
  if [ -n "$wt_path" ]; then
    echo "=== Pushing $branch from $wt_path ==="
    git -C "$wt_path" push origin "$branch"
    echo "Exit code: $?"
  else
    # Branch may be in the worktree under a slightly different label
    # Try pushing by branch name directly
    echo "=== Pushing $branch (from remote refs) ==="
    git push origin "refs/heads/$branch" 2>&1 || \
    git -C "/Users/Dev/Vibe-Coding/Apps/$(basename $wt_path 2>/dev/null || echo MadhavSRP-T1)" \
      push origin "$branch" 2>&1 || echo "WARN: could not find worktree for $branch"
  fi
done

echo ""
echo "=== Verify all test branches on origin ==="
git fetch --all --quiet
for branch in test/srp-t1-portal-unit test/srp-t2-mcp-unit \
              test/srp-t3-integration test/srp-t4-system; do
  git ls-remote --exit-code origin "$branch" > /dev/null 2>&1 \
    && echo "  origin/$branch: PRESENT" \
    || echo "  origin/$branch: MISSING"
done
```

---

## STEP 6 — Open PRs for the 4 test branches

Use the GitHub CLI (`gh`) to open the PRs. This avoids needing a browser.

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Check gh is available
gh --version 2>/dev/null || echo "gh CLI not found — will fall back to URLs"

# Get the remote repo name
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
echo "Repo: $REPO"
```

If `gh` is available, open all 4 PRs:

```bash
gh pr create \
  --title "test(SRP-T-1): portal retrieval unit tests — primitives_registry + msr_sql + lel_query" \
  --body "Adds 4 test files covering FIX-1/2/5/6/7 from the SRP portal fixes session.
- platform/src/lib/mcp/__tests__/primitives_registry.test.ts
- platform/src/lib/mcp/__tests__/primitives_dispatch.test.ts
- platform/src/lib/retrieve/__tests__/msr_sql.test.ts
- platform/src/lib/retrieve/__tests__/lel_query.test.ts
354 tests, 0 failures. Depends on: fix/srp-f1-portal-fixes (already merged to main)." \
  --base main \
  --head test/srp-t1-portal-unit

gh pr create \
  --title "test(SRP-T-2): MCP sidecar unit tests — query_signals + query_ephemeris + lel_query" \
  --body "Adds 3 test files covering FIX-3/4/5/6 from the SRP MCP fixes session.
- platform-mcp/src/tools/__tests__/query_signals.test.ts
- platform-mcp/src/tools/__tests__/query_ephemeris.test.ts
- platform-mcp/src/tools/__tests__/lel_query.test.ts
55 tests, 0 failures. Depends on: fix/srp-f2-mcp-fixes (already merged to main)." \
  --base main \
  --head test/srp-t2-mcp-unit

gh pr create \
  --title "test(SRP-T-3): integration tests — MCP primitives live DB (CI-safe skip guards)" \
  --body "Adds integration test suite for MCP primitives against live DB via proxy.
- platform/src/__tests__/integration/mcp_primitives.integration.test.ts
23 tests, all skip when DB_PROXY_PORT absent (CI-safe).
Run locally: DB_PROXY_PORT=5433 INTEGRATION_TEST_BASE_URL=http://localhost:3001 npx vitest run src/__tests__/integration/" \
  --base main \
  --head test/srp-t3-integration

gh pr create \
  --title "test(SRP-T-4): system tests — portal pipeline E2E smoke (CI-safe skip guards)" \
  --body "Adds system-level E2E smoke suite for the portal pipeline.
- platform/src/__tests__/system/portal_pipeline.system.test.ts
15 tests, all skip when SMOKE_SESSION_COOKIE absent (CI-safe).
Run locally: SMOKE_SESSION_COOKIE=\$COOKIE SMOKE_BASE_URL=http://localhost:3002 npx vitest run src/__tests__/system/" \
  --base main \
  --head test/srp-t4-system

echo ""
echo "=== PR list ==="
gh pr list --state open | grep -E "SRP-T|srp-t"
```

If `gh` is NOT available, print the URLs for manual PR creation:

```bash
if ! gh --version > /dev/null 2>&1; then
  REMOTE=$(git remote get-url origin)
  echo ""
  echo "Open these PRs manually in your browser:"
  echo "  T-1: $REMOTE/compare/main...test/srp-t1-portal-unit"
  echo "  T-2: $REMOTE/compare/main...test/srp-t2-mcp-unit"
  echo "  T-3: $REMOTE/compare/main...test/srp-t3-integration"
  echo "  T-4: $REMOTE/compare/main...test/srp-t4-system"
fi
```

---

## STEP 7 — Print deploy commands for you to run

The following are OPERATOR commands. Print them clearly so the operator can
copy-paste and run them in sequence.

```bash
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║          SRP DEPLOY — Run these commands manually               ║"
echo "╠══════════════════════════════════════════════════════════════════╣"
echo "║                                                                  ║"
echo "║  1. Deploy amjis-web (FIX-1/2/6/7 — portal fixes)              ║"
echo "║                                                                  ║"
echo "║     cd /Users/Dev/Vibe-Coding/Apps/Madhav                       ║"
echo "║     git push origin main   (already done in Step 4)             ║"
echo "║     # CI/CD picks up main push and deploys automatically        ║"
echo "║     # OR trigger manually:                                       ║"
echo "║     gcloud builds submit --config cloudbuild.yaml \\             ║"
echo "║       --project madhav-astrology                                 ║"
echo "║                                                                  ║"
echo "║  2. Deploy amjis-mcp sidecar (FIX-3/4/5 — MCP fixes)           ║"
echo "║                                                                  ║"
echo "║     cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform-mcp          ║"
echo "║     # Check deploy script (may be separate build config):        ║"
echo "║     cat /Users/Dev/Vibe-Coding/Apps/Madhav/deploy.yml           ║"
echo "║     # Deploy sidecar job:                                        ║"
echo "║     gcloud builds submit --config cloudbuild.yaml \\             ║"
echo "║       --substitutions=_DEPLOY_TARGET=sidecar \\                  ║"
echo "║       --project madhav-astrology                                 ║"
echo "║                                                                  ║"
echo "║  3. After both deploys are live — verify:                        ║"
echo "║                                                                  ║"
echo "║     gcloud run services list --region asia-south1 \\             ║"
echo "║       --project madhav-astrology                                 ║"
echo "║     # Confirm amjis-web + amjis-mcp show new revisions           ║"
echo "║                                                                  ║"
echo "╠══════════════════════════════════════════════════════════════════╣"
echo "║  WHAT CHANGES IN PRODUCTION:                                     ║"
echo "║  amjis-web:  primitives_registry now whitelists 37 tools (was    ║"
echo "║              23); forward_looking reads params; lel v1.7 source  ║"
echo "║  amjis-mcp:  valence enum matches DB; sample_step is integer;    ║"
echo "║              significance field name + type corrected            ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
```

---

That completes the Stream 1 ship sequence.
Run Steps 1–7 now. Stop and report at any step that fails.
