# GISMCP Remediation — Prep Prompt
# Paste this ENTIRE prompt into a Claude Code chat session.
# Folder: /Users/Dev/Vibe-Coding/Apps/Madhav
# Purpose: Create 2 worktrees, write .claude/settings.local.json, verify env,
#          print readiness table. Run this ONCE before launching Stream 1 and Stream 2.
# ─────────────────────────────────────────────────────────────────────────────

You are preparing the environment for GISMCP Remediation — 2-stream autonomous execution.
Run every step in order. Report each outcome before proceeding.

---

## STEP 0 — Write dangerouslySkipPermissions to main worktree

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
mkdir -p .claude
cat > .claude/settings.local.json << 'EOF'
{
  "dangerouslySkipPermissions": true
}
EOF
echo "Main worktree .claude/settings.local.json written"
cat .claude/settings.local.json
```

---

## STEP 1 — Verify local main is clean

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git status --short
git fetch origin main --quiet
git log origin/main..main --oneline | wc -l | xargs echo "Commits ahead of origin/main:"
```

Expected: no uncommitted changes (or only untracked files). If there are staged/modified tracked files, STOP and report.

---

## STEP 2 — Create 2 git worktrees

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

echo "=== Creating Stream 1 worktree ==="
git worktree add ../MadhavGISMCP-S1 -b fix/gismcp-r1-r2
echo "Stream 1 exit: $?"

echo "=== Creating Stream 2 worktree ==="
git worktree add ../MadhavGISMCP-S2 -b fix/gismcp-r3
echo "Stream 2 exit: $?"

echo "=== Verify worktrees ==="
git worktree list
```

Expected: both worktrees created at `/Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1` and `/Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2`.

---

## STEP 3 — Write .claude/settings.local.json to both worktrees

```bash
for wt in /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1 \
           /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2; do
  mkdir -p "$wt/.claude"
  cat > "$wt/.claude/settings.local.json" << 'EOF'
{
  "dangerouslySkipPermissions": true
}
EOF
  echo "Written: $wt/.claude/settings.local.json"
done
```

---

## STEP 4 — npm install in both worktrees

```bash
echo "=== Stream 1: platform ==="
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform && npm install --quiet
echo "platform exit: $?"

echo "=== Stream 1: platform-mcp ==="
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform-mcp && npm install --quiet
echo "platform-mcp exit: $?"

echo "=== Stream 2: platform (shares node_modules via symlink or separate) ==="
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2/platform && npm install --quiet
echo "platform exit: $?"
```

---

## STEP 5 — Verify DB proxy is running

```bash
echo "=== Check DB proxy on port 5433 ==="
nc -z localhost 5433 && echo "DB proxy RUNNING on 5433" || echo "DB proxy NOT running — start it before running integration tests"

echo ""
echo "=== If not running, start with: ==="
echo "cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform && bash scripts/start_db_proxy.sh"
```

Note: DB proxy is NOT required for Stream 1 R1 sessions. It IS required for R2-T1 and all R3 sessions.

---

## STEP 6 — Re-mint session cookie (for smoke tests)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
echo "=== Re-mint session cookie ==="
npx tsx scripts/mint_session_cookie.ts 2>&1 | tail -5
```

If the script produces a __session value, note it for SMOKE_SESSION_COOKIE when running R2-T2 smoke tests.

---

## STEP 7 — Verify all conductor files are present

```bash
echo "=== Conductor file checklist ==="
for f in \
  "00_ARCHITECTURE/BRIEFS/GISMCP_REMEDIATION_PLAN_v1_0.md" \
  "00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/STREAM1_CONDUCTOR_PROMPT.md" \
  "00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/STREAM2_CONDUCTOR_PROMPT.md" \
  "00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/session_queue_s1.yaml" \
  "00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/session_queue_s2.yaml" \
  "00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R1_S1_BRIEF.md" \
  "00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R1_T1_BRIEF.md" \
  "00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R2_S1_BRIEF.md" \
  "00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R2_S2_BRIEF.md" \
  "00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R2_T1_BRIEF.md" \
  "00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R2_T2_BRIEF.md" \
  "00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R3_S1_BRIEF.md" \
  "00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R3_S2_BRIEF.md" \
  "00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R3_T1_BRIEF.md" \
  "00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R3_SEAL_BRIEF.md"; do
  test -f "/Users/Dev/Vibe-Coding/Apps/Madhav/$f" \
    && echo "  ✓ $f" \
    || echo "  ✗ MISSING: $f"
done
```

All 15 files should show ✓.

---

## STEP 8 — Print readiness table

```bash
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║           GISMCP REMEDIATION — READINESS SUMMARY                ║"
echo "╠══════════════════════════════════════════════════════════════════╣"

# Stream 1 worktree
test -d /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1 \
  && echo "║  Stream 1 worktree (MadhavGISMCP-S1):  READY                    ║" \
  || echo "║  Stream 1 worktree (MadhavGISMCP-S1):  MISSING — re-run Step 2  ║"

# Stream 2 worktree
test -d /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2 \
  && echo "║  Stream 2 worktree (MadhavGISMCP-S2):  READY                    ║" \
  || echo "║  Stream 2 worktree (MadhavGISMCP-S2):  MISSING — re-run Step 2  ║"

# Settings files
test -f /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/.claude/settings.local.json \
  && echo "║  Stream 1 dangerouslySkipPermissions:  SET                      ║" \
  || echo "║  Stream 1 dangerouslySkipPermissions:  MISSING — re-run Step 3  ║"

test -f /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2/.claude/settings.local.json \
  && echo "║  Stream 2 dangerouslySkipPermissions:  SET                      ║" \
  || echo "║  Stream 2 dangerouslySkipPermissions:  MISSING — re-run Step 3  ║"

# DB proxy
nc -z localhost 5433 2>/dev/null \
  && echo "║  DB proxy (port 5433):                 RUNNING                  ║" \
  || echo "║  DB proxy (port 5433):                 NOT running (integration tests will skip) ║"

echo "╠══════════════════════════════════════════════════════════════════╣"
echo "║  NEXT: Open 2 chat panels in Antigravity IDE                    ║"
echo "║  Panel 1 → folder MadhavGISMCP-S1 → paste STREAM1_CONDUCTOR    ║"
echo "║  Panel 2 → folder MadhavGISMCP-S2 → paste STREAM2_CONDUCTOR    ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
```

---

That completes prep. Run Steps 0–8 now. Both streams can launch simultaneously once the readiness table shows all READY.
