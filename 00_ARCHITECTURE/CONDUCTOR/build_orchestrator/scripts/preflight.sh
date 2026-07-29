#!/bin/bash
# MARSYS Build Orchestrator — Pre-flight checks
set -e
REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
cd "$REPO"

echo "=== PREFLIGHT ==="

# 1. Repo state
git checkout main && git pull origin main
DIRTY=$(git status --porcelain | wc -l | tr -d ' ')
[ "$DIRTY" -gt 2 ] && echo "WARNING: repo has $DIRTY modified files (CLAUDECODE_BRIEF.md + untracked OK)" || echo "OK: repo state"

# 2. DB proxy
if ps aux | grep -q "[c]loud-sql-proxy"; then
  echo "OK: cloud-sql-proxy running"
  PGPASSWORD="${PGPASSWORD:?}" psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "SELECT 1;" >/dev/null 2>&1 && echo "OK: DB reachable" || echo "WARN: DB not reachable"
else
  echo "WARN: cloud-sql-proxy not running — start with: bash platform/scripts/start_db_proxy.sh &"
fi

# 3. GCP
gcloud auth list --format='value(account)' 2>/dev/null | head -1 | xargs echo "OK: gcloud account:" || echo "WARN: gcloud not configured"
gcloud config get-value project 2>/dev/null | xargs echo "OK: project:" || echo "WARN: project not set"

# 4. Node deps
[ -d platform/node_modules ] && echo "OK: node_modules present" || (echo "Installing node deps..." && pnpm install)

# 5. Python deps
python3 -c "import swisseph; print('OK: swisseph')" 2>/dev/null || echo "WARN: swisseph not installed"
python3 -c "import psycopg2; print('OK: psycopg2')" 2>/dev/null || echo "WARN: psycopg2 not installed"

# 6. Tracker
curl -s http://localhost:8765 | grep -q 'html' && echo "OK: tracker on :8765" || echo "WARN: tracker not running — start: cd 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/tracker && python3 -m http.server 8765 &"

# 7. Worktrees
WCOUNT=$(git worktree list | grep 'MadhavBO' | wc -l | tr -d ' ')
echo "OK: $WCOUNT worktrees present (expect 13)"

echo "=== PREFLIGHT DONE ==="
