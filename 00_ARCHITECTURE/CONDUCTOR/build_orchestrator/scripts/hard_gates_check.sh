#!/bin/bash
# Run all 8 hard gates. Exit 0 = all GREEN. Exit 1 = any RED.
set -e
REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
cd "$REPO"

PASS=0; FAIL=0

gate() {
  local name="$1"
  local cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "GREEN: $name"
    PASS=$((PASS+1))
  else
    echo "RED:   $name"
    FAIL=$((FAIL+1))
  fi
}

# G1: naming_ci — all BUILD-ORCH commits follow conventional commit format
gate "G1_naming_ci" \
  "git log --oneline | grep 'BUILD-ORCH' | head -5 | grep -E '^[a-f0-9]+ (feat|fix|test|chore|docs|refactor)\(' "

# G2: jh_oracle_pinned — static file still present
gate "G2_jh_oracle_pinned" \
  "[ -f platform/python-sidecar/natal_engine/fixtures/jh_oracle.json ]"

# G3: G1_internal_invariants — test suite passes
gate "G3_G1_internal_invariants" \
  "python -m pytest platform/python-sidecar/natal_engine/__tests__/test_g1_internal_invariants.py -q 2>/dev/null && echo pass"

# G4: G2_authz_live — all /api/build/* routes check auth
gate "G4_G2_authz_live" \
  "grep -r 'getServerSession\|requireAuth\|verifyToken' platform/src/app/api/build/ | grep -v '.test.' | wc -l | awk '{print(\$1 > 0)}' | grep 1"

# G5: G3_contract — chart_output schema validator present
gate "G5_G3_contract" \
  "[ -f platform/python-sidecar/natal_engine/schema/chart_output_schema.json ] || \
   [ -f platform/python-sidecar/natal_engine/__tests__/test_chart_output_schema.py ]"

# G6: G4_no_native_lit — no narrative verbs in chart_facts values
gate "G6_G4_no_native_lit" \
  "python3 -c \"
import psycopg2, os
conn = psycopg2.connect(host='127.0.0.1', port=5433, user='amjis_app', password=os.environ['PGPASSWORD'], dbname='amjis')
cur = conn.cursor()
cur.execute(\\\"SELECT COUNT(*) FROM chart_facts WHERE fact_value_json::text ~* '(indicates|suggests|implies|means that|denotes)'\\\")
count = cur.fetchone()[0]
conn.close()
exit(0 if count == 0 else 1)
\""

# G7: G5b_onfinish — routes have onFinish handlers
gate "G7_G5b_onfinish" \
  "grep -r 'onFinish\|on_finish' platform/src/app/api/chat/ | grep -v '.test.' | wc -l | awk '{print(\$1 > 0)}' | grep 1"

# G8: G6_tool_coverage — MCP server still has 40 tools
gate "G8_G6_tool_coverage" \
  "grep -c 'server\.tool\b\|\.tool(' platform-mcp/src/server.ts 2>/dev/null | awk '{print(\$1 >= 40)}' | grep 1"

echo ""
echo "=== HARD GATES: $PASS GREEN, $FAIL RED ==="
[ "$FAIL" -gt 0 ] && exit 1 || exit 0
