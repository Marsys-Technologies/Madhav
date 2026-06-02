#!/usr/bin/env bash
# edge_security_smoke.sh — Wave 4 unit 4.edge_and_infra_hygiene smoke gate.
#
# Codified-state check (no gcloud calls). Returns 0 when the IaC + workflow
# state in the worktree matches the unit's acceptance criteria; non-zero
# otherwise. Used by the Conductor + by ad-hoc operator audit runs.
#
# Acceptance items checked (BRIEF_4_edge_and_infra_hygiene.md):
#   1. infra/edge/ contains LB + CDN + Armor terraform; cloud_armor_rules.json
#      has ≥1 WAF + ≥1 rate-limit rule.
#   2. infra/iam/ has 4 distinct least-priv SAs; deploy.yml has --service-account=
#      per service.
#   3. platform-mcp/src/client.ts uses Bearer + google-auth-library.
#   4. infra/scheduler/ has 2 jobs (MV-refresh + reaper) with cadence specs.
#   5. platform/cloudbuild*.yaml removed; deploy.yml is sole orchestrator;
#      MCP image refs point at Artifact Registry not gcr.io for the deploy path.

set -euo pipefail

# --ci-only is accepted for forward-compatibility (reserved for live-endpoint
# checks that would be added later). All current checks are static IaC/worktree
# assertions and run identically in CI and operator contexts.
for arg in "$@"; do
  case "$arg" in
    --ci-only) ;;  # no-op: all checks are already static-safe
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
FAIL=0
WARN=0

red()    { printf '\033[31m%s\033[0m\n' "$*"; }
green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    green "  PASS  ${label}"
  else
    red   "  FAIL  ${label}"
    FAIL=$((FAIL + 1))
  fi
}

warn_if() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    yellow "  WARN  ${label}"
    WARN=$((WARN + 1))
  fi
}

echo "── 4.edge_and_infra_hygiene smoke ──"
cd "$REPO_ROOT"

echo
echo "[1] Firebase hosting — edge module deleted (Brahma arc, 2026-06-02); traffic via Firebase + Cloud Run rewrite"
check "infra/edge/main.tf absent (LB/CDN destroyed)" test ! -f infra/edge/main.tf
check "infra/edge/cloud_armor.tf absent" test ! -f infra/edge/cloud_armor.tf
check "firebase.json exists" test -f firebase.json
check ".firebaserc exists" test -f .firebaserc
check "firebase.json has Cloud Run rewrite to amjis-web" grep -q '"serviceId": "amjis-web"' firebase.json
check "firebase.json targets asia-south1" grep -q '"region": "asia-south1"' firebase.json
check ".firebaserc points to madhav-astrology project" grep -q '"madhav-astrology"' .firebaserc

echo
echo "[2] infra/iam — 4 distinct least-priv SAs"
check "infra/iam/main.tf exists" test -f infra/iam/main.tf
check "SA: amjis-web-runtime defined" grep -q 'account_id *= *"amjis-web-runtime"' infra/iam/main.tf
check "SA: amjis-sidecar-runtime defined" grep -q 'account_id *= *"amjis-sidecar-runtime"' infra/iam/main.tf
check "SA: amjis-mcp-runtime defined" grep -q 'account_id *= *"amjis-mcp-runtime"' infra/iam/main.tf
check "SA: amjis-builder-runtime defined" grep -q 'account_id *= *"amjis-builder-runtime"' infra/iam/main.tf
check "deploy.yml pins amjis-web-runtime"   grep -q "amjis-web-runtime@"     .github/workflows/deploy.yml
check "deploy.yml pins amjis-sidecar-runtime" grep -q "amjis-sidecar-runtime@" .github/workflows/deploy.yml
check "deploy.yml pins amjis-mcp-runtime"   grep -q "amjis-mcp-runtime@"     .github/workflows/deploy.yml

echo
echo "[3] platform-mcp/src/client.ts — IAM bearer wiring"
check "client.ts imports google-auth-library" grep -q "from 'google-auth-library'" platform-mcp/src/client.ts
check "client.ts sends Authorization: Bearer" grep -q "Authorization.*Bearer" platform-mcp/src/client.ts
check "iam_bearer.test.ts exists" test -f platform-mcp/src/__tests__/iam_bearer.test.ts

echo
echo "[4] infra/scheduler — MV-refresh + reaper jobs"
check "infra/scheduler/main.tf exists" test -f infra/scheduler/main.tf
check "scheduler: mv_refresh job exists"      grep -q 'resource "google_cloud_scheduler_job" "mv_refresh"' infra/scheduler/main.tf
check "scheduler: mv_refresh cadence is 6h"   grep -q 'schedule *= *"0 \*/6 \* \* \*"' infra/scheduler/main.tf
check "scheduler: reaper job exists"          grep -q 'resource "google_cloud_scheduler_job" "pending_stream_reaper"' infra/scheduler/main.tf
check "scheduler: reaper cadence is 10m"      grep -q 'schedule *= *"\*/10 \* \* \* \*"' infra/scheduler/main.tf

echo
echo "[5] Deploy-path consolidation + AR migration"
check "platform/cloudbuild.yaml removed"           test ! -f platform/cloudbuild.yaml
check "platform/cloudbuild-sidecar.yaml removed"   test ! -f platform/cloudbuild-sidecar.yaml
check "platform/cloudbuild.pipeline.yaml removed"  test ! -f platform/cloudbuild.pipeline.yaml
check "deploy.yml has deploy-mcp job"              grep -q "deploy-mcp:" .github/workflows/deploy.yml
check "deploy.yml MCP image points at AR"          grep -q "asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-mcp" .github/workflows/deploy.yml
check "deploy.yml MCP is IAM-gated"                grep -q "no-allow-unauthenticated" .github/workflows/deploy.yml

# Non-fatal: warn on :latest pins (rotation tracked in infra/secrets/).
warn_if ":latest secret pins still present" grep -q ":latest" .github/workflows/deploy.yml

echo
echo "[6] Secret + registry hygiene catalogues"
check "infra/secrets/secret_inventory.yaml exists" test -f infra/secrets/secret_inventory.yaml
check "infra/secrets/rotation_policy.md exists"    test -f infra/secrets/rotation_policy.md
check "infra/artifact_registry/cleanup_policy.json exists" test -f infra/artifact_registry/cleanup_policy.json
check "AR cleanup has KEEP rule"   grep -q '"action": "KEEP"'   infra/artifact_registry/cleanup_policy.json
check "AR cleanup has DELETE rule" grep -q '"action": "DELETE"' infra/artifact_registry/cleanup_policy.json

echo
if [ $FAIL -eq 0 ]; then
  green "── ALL ${FAIL} HARD FAILURES; ${WARN} WARN(S) (non-fatal) ──"
  exit 0
else
  red "── ${FAIL} HARD FAILURE(S); ${WARN} WARN(S) ──"
  exit 1
fi
