# SRP Pre-Conductor Preparation Prompt
# Paste this ENTIRE prompt into a Claude Code chat session.
#
# HOW TO OPEN THE SESSION:
#   1. Open the folder /Users/Dev/Vibe-Coding/Apps/Madhav in Antigravity IDE
#      (File → Open Folder → /Users/Dev/Vibe-Coding/Apps/Madhav)
#   2. Open the Claude Code chat panel (extension sidebar)
#   3. Paste everything below this header block into the chat and send it
#
# DO NOT open any worktree folder (MadhavSRP-*) for this step.
# The main Madhav folder is correct.
# ─────────────────────────────────────────────────────────────────────────────

You are preparing the SRP (System Repair Plan) execution environment in the
/Users/Dev/Vibe-Coding/Apps/Madhav repository. Run every step below in order.
Do not skip steps. Report each step's outcome before moving to the next.
Use bash for all shell commands.

---

## STEP 0 — Enable dangerouslySkipPermissions for this workspace

Write the following file so that all Claude Code sessions in this workspace
(and any sub-agent sessions spawned from it) skip permission prompts:

```bash
mkdir -p /Users/Dev/Vibe-Coding/Apps/Madhav/.claude
cat > /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/settings.local.json << 'EOF'
{
  "dangerouslySkipPermissions": true
}
EOF
echo "dangerouslySkipPermissions: written"
cat /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/settings.local.json
```

Also write the same file into every SRP worktree so sub-agents inherit it:

```bash
for wt in MadhavSRP-F1 MadhavSRP-F2 MadhavSRP-T1 MadhavSRP-T2 \
           MadhavSRP-T3 MadhavSRP-T4 MadhavSRP-A1 MadhavSRP-A2; do
  mkdir -p /Users/Dev/Vibe-Coding/Apps/$wt/.claude
  cp /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/settings.local.json \
     /Users/Dev/Vibe-Coding/Apps/$wt/.claude/settings.local.json
  echo "$wt: settings.local.json written"
done
```

---

## STEP 1 — Confirm we are on the right branch in the main worktree

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
echo "Branch: $(git branch --show-current)"
echo "Status:"
git status --short
echo "Last commit:"
git log --oneline -1
```

Expected: branch is `main`, working tree is clean.
If there are uncommitted changes, report them — do NOT stash or discard anything.

---

## STEP 2 — Verify all 8 SRP worktrees exist with correct branches

```bash
echo "=== Worktree list ==="
git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree list

echo ""
echo "=== Per-worktree branch check ==="
for wt in MadhavSRP-F1 MadhavSRP-F2 MadhavSRP-T1 MadhavSRP-T2 \
           MadhavSRP-T3 MadhavSRP-T4 MadhavSRP-A1 MadhavSRP-A2; do
  path="/Users/Dev/Vibe-Coding/Apps/$wt"
  if [ -d "$path" ]; then
    branch=$(git -C "$path" branch --show-current 2>/dev/null || echo "DETACHED/ERROR")
    echo "$wt: $branch"
  else
    echo "$wt: MISSING — worktree does not exist!"
  fi
done
```

Expected branches:
  MadhavSRP-F1  → fix/srp-f1-portal-fixes
  MadhavSRP-F2  → fix/srp-f2-mcp-fixes
  MadhavSRP-T1  → test/srp-t1-portal-unit
  MadhavSRP-T2  → test/srp-t2-mcp-unit
  MadhavSRP-T3  → test/srp-t3-integration
  MadhavSRP-T4  → test/srp-t4-system
  MadhavSRP-A1  → arch/srp-a1-tech-debt
  MadhavSRP-A2  → arch/srp-a2-arch-report

If any worktree is MISSING, re-create it:

```bash
# Run ONLY the missing ones. Safe to skip if all present.
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Fix worktrees
# git worktree add ../MadhavSRP-F1 -b fix/srp-f1-portal-fixes
# git worktree add ../MadhavSRP-F2 -b fix/srp-f2-mcp-fixes

# Test worktrees
# git worktree add ../MadhavSRP-T1 -b test/srp-t1-portal-unit
# git worktree add ../MadhavSRP-T2 -b test/srp-t2-mcp-unit
# git worktree add ../MadhavSRP-T3 -b test/srp-t3-integration
# git worktree add ../MadhavSRP-T4 -b test/srp-t4-system

# Architecture worktrees
# git worktree add ../MadhavSRP-A1 -b arch/srp-a1-tech-debt
# git worktree add ../MadhavSRP-A2 -b arch/srp-a2-arch-report
```

(Uncomment only the lines for missing worktrees.)

---

## STEP 3 — Verify npm install is complete in all worktrees

```bash
echo "=== Checking node_modules in all worktrees ==="
for wt in MadhavSRP-F1 MadhavSRP-F2 MadhavSRP-T1 MadhavSRP-T2 \
           MadhavSRP-T3 MadhavSRP-T4 MadhavSRP-A1 MadhavSRP-A2; do
  plat_nm="/Users/Dev/Vibe-Coding/Apps/$wt/platform/node_modules"
  mcp_nm="/Users/Dev/Vibe-Coding/Apps/$wt/platform-mcp/node_modules"

  if [ -d "$plat_nm" ]; then
    echo "$wt/platform: node_modules OK"
  else
    echo "$wt/platform: MISSING node_modules — running npm install..."
    cd /Users/Dev/Vibe-Coding/Apps/$wt/platform && npm install --silent
    echo "$wt/platform: install done"
  fi

  # platform-mcp only exists in F1, F2, T1, T2, T3, T4 (not A1, A2)
  if [ -d "/Users/Dev/Vibe-Coding/Apps/$wt/platform-mcp" ]; then
    if [ -d "$mcp_nm" ]; then
      echo "$wt/platform-mcp: node_modules OK"
    else
      echo "$wt/platform-mcp: MISSING node_modules — running npm install..."
      cd /Users/Dev/Vibe-Coding/Apps/$wt/platform-mcp && npm install --silent
      echo "$wt/platform-mcp: install done"
    fi
  fi
done
```

---

## STEP 4 — Verify DB proxy is running (required for T-3 integration tests)

```bash
echo "=== DB proxy check ==="
if pgrep -f "cloud_sql_proxy\|cloud-sql-proxy\|start_db_proxy" > /dev/null 2>&1; then
  echo "DB proxy: RUNNING"
  pgrep -af "cloud_sql_proxy\|cloud-sql-proxy" | head -3
else
  echo "DB proxy: NOT RUNNING — starting..."
  nohup bash /Users/Dev/Vibe-Coding/Apps/Madhav/platform/scripts/start_db_proxy.sh \
    > /tmp/db_proxy.log 2>&1 &
  sleep 5
  if pgrep -f "cloud_sql_proxy\|cloud-sql-proxy" > /dev/null 2>&1; then
    echo "DB proxy: started successfully"
  else
    echo "DB proxy: FAILED to start — check /tmp/db_proxy.log"
    tail -20 /tmp/db_proxy.log
    echo "WARN: T-3 integration tests will need the proxy; T-1/T-2/T-4/A-1/A-2 are unaffected."
  fi
fi

echo ""
echo "=== Port 5433 check ==="
lsof -i :5433 2>/dev/null | head -5 || echo "Port 5433: no listener found"
```

---

## STEP 5 — Mint (or re-mint) the session cookie for T-4 system tests

```bash
echo "=== Minting session cookie ==="
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform

SESSION_COOKIE=$(npx tsx scripts/mint_session_cookie.ts 2>/dev/null)

if [ -n "$SESSION_COOKIE" ]; then
  echo "Session cookie: MINTED (${#SESSION_COOKIE} chars)"
  echo "export SMOKE_SESSION_COOKIE='$SESSION_COOKIE'" > /tmp/srp_env.sh
  echo "export DB_PROXY_PORT=5433" >> /tmp/srp_env.sh
  echo "export INTEGRATION_TEST_BASE_URL=http://localhost:3001" >> /tmp/srp_env.sh
  echo "export INTEGRATION_CHART_ID=362f9f17-95a5-490b-a5a7-027d3e0efda0" >> /tmp/srp_env.sh
  echo "export SMOKE_BASE_URL=http://localhost:3002" >> /tmp/srp_env.sh
  echo "export SMOKE_CHART_ID=362f9f17-95a5-490b-a5a7-027d3e0efda0" >> /tmp/srp_env.sh
  echo "Env file written to /tmp/srp_env.sh"
  echo "Contents:"
  cat /tmp/srp_env.sh
else
  echo "Session cookie: EMPTY — T-4 system tests will skip gracefully (this is acceptable)"
  # Still write the env file without the cookie so other vars are available
  echo "export DB_PROXY_PORT=5433" > /tmp/srp_env.sh
  echo "export INTEGRATION_TEST_BASE_URL=http://localhost:3001" >> /tmp/srp_env.sh
  echo "export INTEGRATION_CHART_ID=362f9f17-95a5-490b-a5a7-027d3e0efda0" >> /tmp/srp_env.sh
  echo "export SMOKE_BASE_URL=http://localhost:3002" >> /tmp/srp_env.sh
  echo "export SMOKE_CHART_ID=362f9f17-95a5-490b-a5a7-027d3e0efda0" >> /tmp/srp_env.sh
  echo "Env file written to /tmp/srp_env.sh (no cookie)"
fi

source /tmp/srp_env.sh
echo "Env sourced into current shell."
```

---

## STEP 6 — Smoke-test vitest in one fix worktree

This confirms test infrastructure is operational before the Conductor spawns
test sub-agents.

```bash
echo "=== Vitest smoke check in MadhavSRP-F1/platform ==="
cd /Users/Dev/Vibe-Coding/Apps/MadhavSRP-F1/platform
# Run with --reporter=verbose and bail after 1 failure
# We expect existing tests to pass (pre-fix state — nothing broken yet)
npx vitest run --reporter=verbose 2>&1 | tail -30

echo ""
echo "=== Vitest smoke check in MadhavSRP-F2/platform-mcp ==="
cd /Users/Dev/Vibe-Coding/Apps/MadhavSRP-F2/platform-mcp
npx vitest run --reporter=verbose 2>&1 | tail -30
```

If vitest exits 0 or "no test files found": OK — report pass.
If vitest exits non-zero with test failures: report the failures verbatim.
Do NOT attempt to fix them — this is pre-fix state and failures may be expected.

---

## STEP 7 — Verify all conductor queue and brief files exist

```bash
echo "=== Conductor + brief file verification ==="
FILES=(
  "00_ARCHITECTURE/CONDUCTOR/srp/stream1_queue.yaml"
  "00_ARCHITECTURE/CONDUCTOR/srp/stream2_queue.yaml"
  "00_ARCHITECTURE/CONDUCTOR/srp/STREAM1_CONDUCTOR_KICKOFF.md"
  "00_ARCHITECTURE/CONDUCTOR/srp/STREAM2_CONDUCTOR_KICKOFF.md"
  "00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_F1_PORTAL_FIXES.md"
  "00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_F2_MCP_FIXES.md"
  "00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_T1_PORTAL_UNIT_TESTS.md"
  "00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_T2_MCP_UNIT_TESTS.md"
  "00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_T3_INTEGRATION_TESTS.md"
  "00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_T4_SYSTEM_TESTS.md"
  "00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_A1_TECH_DEBT_AUDIT.md"
  "00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_SRP_A2_ARCHITECTURE_REPORT.md"
)

cd /Users/Dev/Vibe-Coding/Apps/Madhav
all_ok=true
for f in "${FILES[@]}"; do
  if [ -f "$f" ]; then
    echo "  OK  $f"
  else
    echo "  MISSING  $f"
    all_ok=false
  fi
done

if $all_ok; then
  echo "All conductor + brief files present."
else
  echo "WARN: Some files are missing. The Conductor will fail for missing-brief sessions."
fi
```

---

## STEP 8 — Verify git remotes are accessible and branches are pushed

The Conductor merges branches from `origin` — branches must exist on the remote
before the merge step.

```bash
echo "=== Checking that SRP branches are pushed to origin ==="
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch --all --quiet 2>&1 | head -5

echo ""
BRANCHES=(
  "fix/srp-f1-portal-fixes"
  "fix/srp-f2-mcp-fixes"
  "test/srp-t1-portal-unit"
  "test/srp-t2-mcp-unit"
  "test/srp-t3-integration"
  "test/srp-t4-system"
  "arch/srp-a1-tech-debt"
  "arch/srp-a2-arch-report"
)

for br in "${BRANCHES[@]}"; do
  if git ls-remote --exit-code origin "$br" > /dev/null 2>&1; then
    echo "  origin/$br: EXISTS"
  else
    echo "  origin/$br: NOT YET PUSHED (OK — sub-agents push after first commit)"
  fi
done
```

Branches that are NOT YET PUSHED are fine — each sub-agent pushes its branch
after its first commit. The Conductor's merge step runs AFTER F-1 and F-2
sub-agents have completed and pushed.

---

## STEP 9 — Write a final readiness report

```bash
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║       SRP Pre-Conductor Readiness Report                         ║"
echo "╠══════════════════════════════════════════════════════════════════╣"

# dangerouslySkipPermissions
if [ -f /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/settings.local.json ]; then
  echo "║  dangerouslySkipPermissions  WRITTEN                             ║"
else
  echo "║  dangerouslySkipPermissions  MISSING — re-run Step 0             ║"
fi

# Worktrees
wt_ok=0; wt_fail=0
for wt in MadhavSRP-F1 MadhavSRP-F2 MadhavSRP-T1 MadhavSRP-T2 \
           MadhavSRP-T3 MadhavSRP-T4 MadhavSRP-A1 MadhavSRP-A2; do
  [ -d /Users/Dev/Vibe-Coding/Apps/$wt ] && wt_ok=$((wt_ok+1)) || wt_fail=$((wt_fail+1))
done
echo "║  Worktrees present           $wt_ok/8                                    ║"

# DB proxy
if pgrep -f "cloud_sql_proxy\|cloud-sql-proxy\|start_db_proxy" > /dev/null 2>&1; then
  echo "║  DB proxy                    RUNNING                             ║"
else
  echo "║  DB proxy                    NOT RUNNING (T-3 will fail)         ║"
fi

# Session cookie
if [ -n "$SMOKE_SESSION_COOKIE" ]; then
  echo "║  Session cookie              MINTED (T-4 live tests enabled)     ║"
else
  echo "║  Session cookie              EMPTY  (T-4 tests will skip)        ║"
fi

# Env file
if [ -f /tmp/srp_env.sh ]; then
  echo "║  Env file /tmp/srp_env.sh    PRESENT                             ║"
else
  echo "║  Env file /tmp/srp_env.sh    MISSING — re-run Step 5             ║"
fi

echo "╠══════════════════════════════════════════════════════════════════╣"
echo "║                                                                  ║"
echo "║  NEXT: Launch both Conductor streams (see instructions below)    ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
```

---

## STEP 10 — HOW TO LAUNCH THE TWO CONDUCTOR STREAMS

After all steps above report green (or acceptable warnings), do the following.

### Both streams run in the SAME folder: /Users/Dev/Vibe-Coding/Apps/Madhav
You do NOT need to open a different folder for the streams.
The sub-agents navigate to their worktrees internally via their prompts.

### Stream 1 (Phase 1 Fixes + Phase 2 Tests)

1. In Antigravity IDE, with /Users/Dev/Vibe-Coding/Apps/Madhav still open,
   open a NEW Claude Code chat panel (or a new chat in the same panel).
2. Read the file:
     00_ARCHITECTURE/CONDUCTOR/srp/STREAM1_CONDUCTOR_KICKOFF.md
3. Paste the ENTIRE CONTENTS of that file into the new chat and send it.
4. The Conductor will take over. Do not interrupt it.
   It will spawn F-1 and F-2 sub-agents in parallel, run the merge step,
   then spawn T-1/T-2 in parallel, then T-3/T-4 with dev servers.

### Stream 2 (Phase 3 Architecture — can start simultaneously with Stream 1)

1. Open ANOTHER new Claude Code chat panel in the same Antigravity IDE window.
2. Read the file:
     00_ARCHITECTURE/CONDUCTOR/srp/STREAM2_CONDUCTOR_KICKOFF.md
3. Paste the ENTIRE CONTENTS of that file into this second chat and send it.
4. Stream 2 runs fully independently (all read-only analysis, never touches
   production code modified by Stream 1).

### Monitoring

Both Conductors log to:
  /tmp/srp_stream1_log.txt   (Stream 1)
  /tmp/srp_stream2_log.txt   (Stream 2)

To tail either log in bash:
  tail -f /tmp/srp_stream1_log.txt
  tail -f /tmp/srp_stream2_log.txt

### When done

Stream 1 prints a completion table showing PASS/BLOCK for each of:
  SRP-F-1, SRP-F-2, MERGE, SRP-T-1, SRP-T-2, SRP-T-3, SRP-T-4

Stream 2 prints a completion table showing PASS/BLOCK for each of:
  SRP-A-1, SRP-A-2

Review any BLOCKED sessions. Each BLOCKED session reports its reason inline.

---

That completes pre-conductor preparation. Run Steps 0–9 now.
