#!/usr/bin/env bash
# regenerate_generated.sh -- ONE command that regenerates every committed, machine-derived aggregate and then runs all of its checks.
#
# THE RULE (N-301/N-302): never hand-merge these files. On a merge conflict or a stale-aggregate CI failure, take EITHER side of the
# conflicted file and run this command. The outputs are deterministic functions of the source tree, so the result does not depend on which
# side you took.
#
#   platform/scripts/regenerate_generated.sh           regenerate everything, then check everything
#   platform/scripts/regenerate_generated.sh --check   check only (what CI does); writes nothing
#
# Order matters (each step reads the previous step's output):
#   1. platform/src/generated/nirmana-writer-digests.json         (sidecar writer source hashes)
#   2. platform/src/generated/capability_estate_census.json       (hashes the file above as one of its sources)
#   3. platform/src/generated/capability_knowledge.snapshot.json  (compiled from the census)
#   4. 00_ARCHITECTURE/control/registry_coverage_report.json      (independent of 1-3)
# It does NOT write the registry-fingerprint pin in test_e6_1_p1_registry_rollup.py (a hand-edited test constant); if the registry
# fingerprint is not pinned there it prints the exact line to add and exits non-zero.
#
# Exit codes: 0 all current; 1 a step or a check failed; 2 usage.
set -euo pipefail

MODE="write"
case "${1:-}" in
  "") ;;
  --check) MODE="check" ;;
  *) echo "usage: $0 [--check]" >&2; exit 2 ;;
esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="${PYTHON:-python3}"
SNAPSHOT="$ROOT/platform/src/generated/capability_knowledge.snapshot.json"
REPORT="$ROOT/00_ARCHITECTURE/control/registry_coverage_report.json"
PIN_TEST="$ROOT/platform/scripts/governance/__tests__/test_e6_1_p1_registry_rollup.py"
FAILED=0

say() { printf '\n== %s\n' "$*"; }

# ensure LABEL CHECK_CMD WRITE_CMD: a step writes ONLY when its own check fails, so an already-current aggregate is never touched (no churn, no
# needless diff line such as the registry report's inspector_commit pointer, which the report's own check deliberately does not compare).
ensure() {
  local label="$1" check_cmd="$2" write_cmd="$3"
  if bash -c "$check_cmd" >/dev/null 2>&1; then
    printf '  current  %s (left untouched)\n' "$label"
  else
    printf '  writing  %s\n' "$label"
    bash -c "$write_cmd"
  fi
}

if [ "$MODE" = "write" ]; then
  say "regenerating (in dependency order; a step writes only if its check fails)"
  ensure "1/4 writer digests" \
    "cd '$ROOT/platform/python-sidecar' && '$PY' -m pipeline.orchestrator.provenance_inventory --check" \
    "cd '$ROOT/platform/python-sidecar' && '$PY' -m pipeline.orchestrator.provenance_inventory"
  ensure "2/4 capability estate census" \
    "cd '$ROOT/platform' && npm run -s codegen:capability-estate-census:check" \
    "cd '$ROOT/platform' && npx tsx --conditions=react-server scripts/generate_capability_estate_census.ts"
  # The snapshot stores a reviewed generated_at; keep the committed value (never invent a new timestamp) so a refresh does not rewrite that line.
  STAMP="$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["generated_at"])' "$SNAPSHOT")"
  ensure "3/4 capability knowledge snapshot" \
    "cd '$ROOT/platform' && npm run -s codegen:capability-knowledge:check" \
    "cd '$ROOT/platform' && npx tsx --conditions=react-server scripts/generate_capability_knowledge.ts '--generated-at=$STAMP'"
  ensure "4/4 registry coverage report" \
    "cd '$ROOT' && '$PY' platform/scripts/governance/asset_census.py --registry-check --check" \
    "cd '$ROOT' && '$PY' platform/scripts/governance/asset_census.py --registry-check"
fi

say "checks"
run_check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf '  ok    %s\n' "$label"
  else
    printf '  FAIL  %s\n' "$label"
    FAILED=1
  fi
}
run_check "writer digests current" bash -c "cd '$ROOT/platform/python-sidecar' && '$PY' -m pipeline.orchestrator.provenance_inventory --check"
run_check "capability estate census current" bash -c "cd '$ROOT/platform' && npm run -s codegen:capability-estate-census:check"
run_check "capability knowledge snapshot current" bash -c "cd '$ROOT/platform' && npm run -s codegen:capability-knowledge:check"
run_check "registry coverage report current" bash -c "cd '$ROOT' && '$PY' platform/scripts/governance/asset_census.py --registry-check --check"

say "registry fingerprint pin"
FP="$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["registry_fingerprint"])' "$REPORT")"
REV="$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["registry_revision"])' "$REPORT")"
if [ -f "$PIN_TEST" ] && ! grep -q "$FP" "$PIN_TEST"; then
  printf '  FAIL  registry revision %s fingerprint %s is not pinned in\n        %s\n        add under PINNED_FINGERPRINTS:  %s: "%s",\n' "$REV" "$FP" "$PIN_TEST" "$REV" "$FP"
  FAILED=1
else
  printf '  ok    revision %s fingerprint is pinned\n' "$REV"
fi

if [ "$FAILED" -ne 0 ]; then
  say "NOT CURRENT. Re-run without --check to regenerate (or fix the line above), and never hand-merge these files."
  exit 1
fi
say "all generated aggregates are current"
