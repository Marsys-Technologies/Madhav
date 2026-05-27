# SRP — One-Time Environment Setup
# Run this ONCE in the main worktree before starting either stream.
# Paste into Claude Code (--dangerously-skip-permissions) at:
#   /Users/Dev/Vibe-Coding/Apps/Madhav

You are setting up the System Repair Plan (SRP) execution environment.
This is a one-time setup. Run all commands. Report any failures.

## Step 1 — Verify clean main

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git status
git log --oneline -3
```

Confirm:
- Working tree is clean (no uncommitted changes)
- On `main` branch
- Latest commit is the most recent known good state

## Step 2 — Create Stream 1 worktrees (Phase 1 + 2)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Phase 1: Fix sessions
git worktree add ../MadhavSRP-F1 -b fix/srp-f1-portal-fixes
git worktree add ../MadhavSRP-F2 -b fix/srp-f2-mcp-fixes

# Phase 2: Test sessions
git worktree add ../MadhavSRP-T1 -b test/srp-t1-portal-unit
git worktree add ../MadhavSRP-T2 -b test/srp-t2-mcp-unit
git worktree add ../MadhavSRP-T3 -b test/srp-t3-integration
git worktree add ../MadhavSRP-T4 -b test/srp-t4-system
```

## Step 3 — Create Stream 2 worktrees (Phase 3)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Phase 3: Architecture sessions
git worktree add ../MadhavSRP-A1 -b arch/srp-a1-tech-debt
git worktree add ../MadhavSRP-A2 -b arch/srp-a2-arch-report
```

## Step 4 — Install dependencies in all worktrees

```bash
for wt in MadhavSRP-F1 MadhavSRP-F2 MadhavSRP-T1 MadhavSRP-T2 MadhavSRP-T3 MadhavSRP-T4; do
  echo "=== Installing platform deps in $wt ==="
  cd /Users/Dev/Vibe-Coding/Apps/$wt/platform && npm install --silent
  echo "=== Installing platform-mcp deps in $wt ==="
  cd /Users/Dev/Vibe-Coding/Apps/$wt/platform-mcp && npm install --silent
done

for wt in MadhavSRP-A1 MadhavSRP-A2; do
  echo "=== Installing platform deps in $wt ==="
  cd /Users/Dev/Vibe-Coding/Apps/$wt/platform && npm install --silent
done
```

(This will take a few minutes. npm install is idempotent — safe to re-run.)

## Step 5 — Start DB proxy (required for T-3 integration tests)

```bash
# Check if already running
pgrep -f "cloud_sql_proxy\|start_db_proxy" && echo "DB proxy already running" || {
  echo "Starting DB proxy..."
  nohup bash /Users/Dev/Vibe-Coding/Apps/Madhav/platform/scripts/start_db_proxy.sh \
    > /tmp/db_proxy.log 2>&1 &
  sleep 3
  pgrep -f "cloud_sql_proxy\|cloud-sql-proxy" && echo "DB proxy started" || echo "WARN: DB proxy may not have started — check /tmp/db_proxy.log"
}
```

## Step 6 — Mint session cookie (required for T-4 system tests)

```bash
# This generates the __session cookie for E2E smoke tests
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
SESSION_COOKIE=$(npx tsx scripts/mint_session_cookie.ts 2>/dev/null)
if [ -n "$SESSION_COOKIE" ]; then
  echo "export SMOKE_SESSION_COOKIE=$SESSION_COOKIE" > /tmp/srp_env.sh
  echo "Session cookie minted. Sourced into /tmp/srp_env.sh"
  echo "Run: source /tmp/srp_env.sh  before starting the Stream 1 Conductor."
else
  echo "WARN: Could not mint session cookie. T-4 system tests will skip gracefully."
  echo "You can mint manually later: cd platform && npx tsx scripts/mint_session_cookie.ts"
fi
```

## Step 7 — Verify worktrees

```bash
git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree list
```

Expected output: 9 entries (main + 8 SRP worktrees).

## Step 8 — Verify tool availability

```bash
echo "=== Node ===" && node --version
echo "=== npm ===" && npm --version
echo "=== git ===" && git --version
echo "=== vitest (platform) ===" && cd /Users/Dev/Vibe-Coding/Apps/MadhavSRP-F1/platform && npx vitest --version
echo "=== vitest (platform-mcp) ===" && cd /Users/Dev/Vibe-Coding/Apps/MadhavSRP-F2/platform-mcp && npx vitest --version
```

## Step 9 — Print readiness summary

```bash
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║         SRP Environment Setup Complete               ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Worktrees created:  8                               ║"
echo "║  Stream 1 queue: 00_ARCHITECTURE/CONDUCTOR/srp/stream1_queue.yaml  ║"
echo "║  Stream 2 queue: 00_ARCHITECTURE/CONDUCTOR/srp/stream2_queue.yaml  ║"
echo "║                                                      ║"
echo "║  NEXT STEPS:                                         ║"
echo "║  1. source /tmp/srp_env.sh  (if file exists)         ║"
echo "║  2. Open two new Claude Code terminal windows        ║"
echo "║  3. Window 1: paste STREAM1_CONDUCTOR_KICKOFF.md     ║"
echo "║  4. Window 2: paste STREAM2_CONDUCTOR_KICKOFF.md     ║"
echo "║  Both run: claude --dangerously-skip-permissions     ║"
echo "╚══════════════════════════════════════════════════════╝"
```

## Done

Report which steps passed and which (if any) need attention.
Do NOT start any fix, test, or architecture work — this session is setup only.
