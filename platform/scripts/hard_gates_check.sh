#!/bin/bash
# ACC2: Hard Gates Check — 15 gates (8 original + 7 infra)
#
# Returns: 0 if no gate is RED, 1 if any gate is RED.
#
# SAMĀPTI B-N8-CI-GATES / finding F-26 (2026-07-30) — this script previously
# CLAIMED "Returns: 0 if all GREEN, 1 if any RED" and contained ZERO `exit`
# statements, so it exited 0 unconditionally (the exit status of its final
# `printf`). A gate script that cannot return non-zero cannot gate. Two defects
# were fixed together, because fixing only the first would have produced a
# script that CAN fail but still never DOES:
#
#   1. The missing exit. `exit 1` on any RED now actually happens (bottom of file).
#   2. NINE of the fifteen gates — G1, G3, G5, G7, G8, G11, G12, G13, G15 — had
#      no RED branch at all: every arm of their conditional called
#      `check ... "GREEN"`, several with notes literally reading "acceptable".
#      (The register said eight; the correct count is nine. G6 additionally had
#      a fake-green fallback on top of its real RED branch, so ten branches
#      were rewritten in total.) Each fallback was re-classified by what it
#      actually means:
#        - G5, G7, G8, G11 -> RED. A real assertion was hiding behind the fake
#          green; its failure is a genuine defect.
#        - G3, G6-fallback, G12, G13 -> STALE. The check cannot run because the
#          path it targets no longer exists. Not a violation, and not a pass.
#        - G1 -> NOT_ASSERTED. Both arms are legitimately fine; this gate never
#          validated anything and is no longer counted as a passing gate.
#
# CURRENT STATE ON main (2026-07-30): exit 2 — 12 GREEN, 0 RED, 1 NOT_ASSERTED,
# 2 STALE (G3 globs for a Python-era test_chart_facts*.py that no longer exists;
# G12 globs for build_chart.py, superseded by the orchestrator per
# L1_GANITA_CLOSURE). Both were reported GREEN before this fix. Repointing those
# two detectors is a follow-up work item, deliberately not done in this lane —
# choosing their new targets is a build-layer judgment, not a CI-plumbing one.
#
# STATUS VOCABULARY:
#   GREEN        — the gate's assertion was checked and holds.
#   RED          — the gate's assertion was checked and fails. Exit code 1.
#   NOT_ASSERTED — this gate checks nothing that can fail. Counted separately;
#                  never contributes to the passed count, never fails the run.
#   STALE        — the check COULD NOT RUN because the path it targets no longer
#                  exists (the layout moved out from under the detector). Exit
#                  code 2. This is deliberately NOT reported as RED: a detector
#                  that lost its target has not found a violation, and dressing
#                  one up as the other is the same sin as the fake GREEN, just
#                  inverted. It is also deliberately NOT green — an unperformed
#                  check is never a pass (SAMAPTI conductor manual s8).
#
# EXIT CODES: 0 = every performed check passed and none are stale.
#             1 = at least one gate RED (a violation was detected).
#             2 = no violations, but at least one detector is STALE, so this
#                 run's coverage is incomplete and must not be read as "clean".
#
# SCOPE NOTE (reported, deliberately not fixed here): no GitHub workflow invokes
# this script. Fixing the exit code makes its header claim true for the operator
# runbooks that DO call it by hand; it does not make it a live CI gate. Wiring
# it in belongs to the F-02 "gates that claim to be CI gates but do not run in
# CI" work item, not to this lane.

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PASS=0
FAIL=0
SKIP=0
STALE=0
declare -a GATES

check() {
  local gate="$1"
  local status="$2"
  local note="$3"
  # Escape quotes in note for JSON safety
  local safe_note
  safe_note=$(printf '%s' "$note" | sed 's/"/\\"/g')
  case "$status" in
    GREEN)        PASS=$((PASS+1)) ;;
    NOT_ASSERTED) SKIP=$((SKIP+1)) ;;
    STALE)        STALE=$((STALE+1)) ;;
    *)            FAIL=$((FAIL+1)) ;;
  esac
  GATES+=("{\"gate\":\"$gate\",\"status\":\"$status\",\"note\":\"$safe_note\"}")
}

# G1: Naming CI — check recent BUILD-ORCH commits follow conventional format
RECENT=$(git -C "$REPO_ROOT" log --oneline -20 --grep=BUILD-ORCH 2>/dev/null || true)
if [ -n "$RECENT" ]; then
  check "G1_naming_ci" "NOT_ASSERTED" "BUILD-ORCH commits found, but this gate never validates their format — both arms passed before F-26; reported honestly rather than counted as a pass"
else
  check "G1_naming_ci" "NOT_ASSERTED" "No BUILD-ORCH commits in last 20 — nothing to check"
fi

# G2: No jh_oracle/test_jh_parity artifacts — enforce [[no-jh-parity-anywhere]]
# GREEN = absent (correct), RED = present (violation)
JH_ORACLE=$(find "$REPO_ROOT" -name "jh_oracle.json" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | head -1)
JH_PARITY=$(find "$REPO_ROOT" -name "test_jh_parity*" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | head -1)
if [ -n "$JH_ORACLE" ] || [ -n "$JH_PARITY" ]; then
  check "G2_no_jh_parity_artifacts" "RED" "Banned artifact found: jh_oracle=${JH_ORACLE:-absent} jh_parity=${JH_PARITY:-absent}"
else
  check "G2_no_jh_parity_artifacts" "GREEN" "No jh_oracle.json or test_jh_parity artifacts present"
fi

# G3: E-08 test suite (chart_facts integrity)
CF_TEST=$(find "$REPO_ROOT/platform" -name "test_chart_facts*.py" 2>/dev/null | head -1)
if [ -n "$CF_TEST" ]; then
  check "G3_internal_invariants" "GREEN" "chart_facts test suite found: $CF_TEST"
else
  check "G3_internal_invariants" "STALE" "No test_chart_facts*.py anywhere under platform/ — this gate still globs for the Python-era suite, but chart_facts coverage now lives in TypeScript tests (platform/src/lib/retrieval/registry/layers/chart_facts_query_*.test.ts, platform-mcp/src/__tests__/chart_facts_ayanamsha.test.ts). Detector needs repointing; it was a fake GREEN 'Test suite location acceptable' before F-26"
fi

# G4: Auth checks — look for auth middleware in API routes
AUTH=$(grep -rl "requireAuth\|getServerSession\|verifyToken\|withAuth\|firebaseAuth\|verifyIdToken" "$REPO_ROOT/platform/src/app/api" 2>/dev/null | head -1)
if [ -n "$AUTH" ]; then
  check "G4_authz_live" "GREEN" "Auth checks found in API routes"
else
  check "G4_authz_live" "RED" "No auth checks found in API routes"
fi

# G5: chart_output schema / provider types
if [ -f "$REPO_ROOT/platform/src/lib/providers/types.ts" ]; then
  check "G5_contract" "GREEN" "Provider types.ts found"
else
  CO=$(find "$REPO_ROOT/platform" -name "chart_output*.ts" 2>/dev/null | head -1)
  if [ -n "$CO" ]; then
    check "G5_contract" "GREEN" "chart_output types found: $CO"
  else
    check "G5_contract" "RED" "Neither platform/src/lib/providers/types.ts nor any chart_output*.ts found — no chart-output contract (was a fake GREEN 'Chart output contract acceptable' before F-26)"
  fi
fi

# G6: No narrative text in chart_facts writers
if [ -d "$REPO_ROOT/platform/python-sidecar/pipeline/writers" ]; then
  NARRATIVE=$(grep -r "fact_value_text" "$REPO_ROOT/platform/python-sidecar/pipeline/writers" 2>/dev/null | grep -v "#" | grep -i "prose\|narrative\|therefore\|however\|additionally" | wc -l || echo "0")
  if [ "$NARRATIVE" -eq 0 ]; then
    check "G6_no_native_lit" "GREEN" "No narrative text in chart_facts writers"
  else
    check "G6_no_native_lit" "RED" "Possible narrative text in chart_facts writers: $NARRATIVE occurrences"
  fi
else
  check "G6_no_native_lit" "STALE" "platform/python-sidecar/pipeline/writers not found — the narrative-text grep could not run. An unperformed check is not a pass (was a fake GREEN 'Writers directory acceptable' before F-26)"
fi

# G7: onFinish DB writes
ONFINISH=$(grep -rl "onFinish\|onComplete\|saveToDb\|insertRow" "$REPO_ROOT/platform/src/app/api" 2>/dev/null | wc -l || echo "0")
if [ "$ONFINISH" -gt 0 ]; then
  check "G7_onfinish" "GREEN" "onFinish/DB writes found: $ONFINISH files"
else
  check "G7_onfinish" "RED" "No onFinish/onComplete/saveToDb/insertRow anywhere under platform/src/app/api — the persistence hook this gate exists to require is absent (was a fake GREEN 'onFinish pattern acceptable' before F-26)"
fi

# G8: MCP tool coverage
MCP_TOOLS=$(find "$REPO_ROOT/platform-mcp/src" -name "*.ts" 2>/dev/null | wc -l || echo "0")
if [ "$MCP_TOOLS" -gt 0 ]; then
  check "G8_tool_coverage" "GREEN" "MCP tool files found: $MCP_TOOLS"
else
  check "G8_tool_coverage" "RED" "Zero .ts files under platform-mcp/src — the MCP tool surface is missing (was a fake GREEN 'MCP tools in platform-mcp' before F-26)"
fi

# G9: IAM — jobInvoker config for Cloud Run Job
JI=$(find "$REPO_ROOT/platform" -name "jobInvoker*" 2>/dev/null | head -1)
if [ -n "$JI" ]; then
  check "G9_iam_verification" "GREEN" "jobInvoker found: $(basename $JI)"
else
  check "G9_iam_verification" "RED" "jobInvoker not found"
fi

# G10: Secret reference
SECRET=$(grep -rl "amjis-pipeline-db-url\|DB_URL\|pipeline-db" "$REPO_ROOT/platform" 2>/dev/null | grep -v "node_modules\|\.git\|__pycache__" | head -1)
if [ -n "$SECRET" ]; then
  check "G10_secret_drift" "GREEN" "DB secret reference found"
else
  check "G10_secret_drift" "RED" "DB secret reference not found"
fi

# G11: DB_URL canonical naming
DBURL=$(grep -rl "DB_URL" "$REPO_ROOT/platform/python-sidecar" 2>/dev/null | head -1)
if [ -n "$DBURL" ]; then
  check "G11_env_naming" "GREEN" "DB_URL canonical naming used"
else
  check "G11_env_naming" "RED" "No DB_URL reference under platform/python-sidecar — canonical env naming not in use (was a fake GREEN 'DB_URL env naming acceptable' before F-26)"
fi

# G12: --chart-id argument in build_chart.py
BCHART=$(find "$REPO_ROOT/platform/python-sidecar" -name "build_chart.py" 2>/dev/null | head -1)
if [ -n "$BCHART" ]; then
  if grep -q "chart.id\|chart_id\|--chart" "$BCHART" 2>/dev/null; then
    check "G12_containerargs" "GREEN" "build_chart.py accepts chart_id argument"
  else
    check "G12_containerargs" "RED" "build_chart.py found at $BCHART but takes no chart_id/--chart argument (was a fake GREEN 'build_chart.py argument present' before F-26)"
  fi
else
  check "G12_containerargs" "STALE" "build_chart.py not found under platform/python-sidecar (nor anywhere in the repo) — superseded by the orchestrator per L1_GANITA_CLOSURE, so this detector has no target left. Needs repointing at the orchestrator entry point; it was a fake GREEN 'build_chart.py argument acceptable' before F-26"
fi

# G13: Dockerfile.pipeline consistency
if [ -f "$REPO_ROOT/platform/python-sidecar/Dockerfile.pipeline" ]; then
  check "G13_image_freshness" "GREEN" "Dockerfile.pipeline found"
else
  check "G13_image_freshness" "STALE" "platform/python-sidecar/Dockerfile.pipeline not found — the file this gate tracks is gone, so the check could not run (was a fake GREEN 'Dockerfile.pipeline reference acceptable' before F-26)"
fi

# G14: No dynamic imports in /api/build/
if [ -d "$REPO_ROOT/platform/src/app/api/build" ]; then
  DYN_IMPORTS=$(grep -r "import(" "$REPO_ROOT/platform/src/app/api/build" 2>/dev/null | grep -v "//\|test\|spec" | wc -l || echo "0")
  if [ "$DYN_IMPORTS" -eq 0 ]; then
    check "G14_dynamic_import_lint" "GREEN" "No dynamic imports in /api/build/"
  else
    check "G14_dynamic_import_lint" "RED" "Dynamic imports found in /api/build/: $DYN_IMPORTS"
  fi
else
  check "G14_dynamic_import_lint" "GREEN" "/api/build/ not present — not applicable"
fi

# G15: CI not all red
CI_IGNORED=$(git -C "$REPO_ROOT" tag -l "ci-red-ignored-*" 2>/dev/null | wc -l || echo "0")
if [ "$CI_IGNORED" -lt 5 ]; then
  check "G15_ci_green" "GREEN" "CI ignored tags: $CI_IGNORED (below the threshold of 5)"
else
  check "G15_ci_green" "RED" "CI ignored tags: $CI_IGNORED — at or above the threshold of 5, CI red is being routinely waived (was a fake GREEN 'review recommended but not blocking' before F-26)"
fi

# Output JSON
OVERALL="GREEN"
if [ "$STALE" -gt 0 ]; then OVERALL="GREEN_INCOMPLETE"; fi
if [ "$FAIL" -gt 0 ]; then OVERALL="RED"; fi

printf '{\n'
printf '  "total": %d,\n' "$((PASS+FAIL+SKIP+STALE))"
printf '  "passed": %d,\n' "$PASS"
printf '  "failed": %d,\n' "$FAIL"
printf '  "not_asserted": %d,\n' "$SKIP"
printf '  "stale_detectors": %d,\n' "$STALE"
printf '  "status": "%s",\n' "$OVERALL"
printf '  "gates": [\n'
for i in "${!GATES[@]}"; do
  if [ $i -lt $((${#GATES[@]}-1)) ]; then
    printf '    %s,\n' "${GATES[$i]}"
  else
    printf '    %s\n' "${GATES[$i]}"
  fi
done
printf '  ]\n'
printf '}\n'

# F-26: the exit statement this script's own header promised and never had.
# Without it every invocation returned 0 — the exit status of the printf above —
# so "returns 1 if any RED" was a claim with no mechanism behind it.
if [ "$FAIL" -gt 0 ]; then
  printf 'hard_gates_check: %d gate(s) RED — failing.\n' "$FAIL" >&2
  exit 1
fi
if [ "$STALE" -gt 0 ]; then
  printf 'hard_gates_check: no violations, but %d detector(s) STALE (target path gone).\n' "$STALE" >&2
  printf '  Coverage is INCOMPLETE — do not read this run as clean. Repoint or retire them.\n' >&2
  exit 2
fi
exit 0
