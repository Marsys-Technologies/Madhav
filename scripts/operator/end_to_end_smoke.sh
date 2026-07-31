#!/usr/bin/env bash
# end_to_end_smoke.sh — post-deploy smoke test for amjis-web
# Called from deploy.yml after new revisions are deployed (no-traffic).
# Exits non-zero on any failure → deploy.yml skips traffic promotion.
#
# SAMĀPTI B-N8-CI-GATES / finding F-32 (2026-07-30). Before this revision the whole
# gate standing between a broken build and 100% of production traffic was:
#
#     check_health "$WEB_URL"     "amjis-web"     "/api/health"
#     check_health "$SIDECAR_URL" "amjis-sidecar" "/health"
#
# Two problems, and the promotion step depended on both:
#
#  1. /api/health is `export function GET() { return NextResponse.json({status:'ok'}) }`
#     — a static literal, no imports, no auth, no DB, no application code. It proves
#     the container booted and Next.js is routing. It cannot tell a healthy revision
#     from one whose every real route 500s. Promoting all traffic on that signal is a
#     proxy, not a check.
#  2. SMOKE_SIDECAR_URL is never passed by deploy.yml's deploy-web job, so SIDECAR_URL
#     silently fell back to a hardcoded literal pointing at the ALREADY-LIVE sidecar —
#     a different service, unrelated to the candidate being promoted. A green there
#     said nothing about the artifact about to receive traffic, yet counted toward the
#     gate exactly as if it did.
#
# What changed:
#  - Added probe_auth_enforced: a real application probe against the CANDIDATE. An
#    unauthenticated GET of the auth-guarded /api/sidecar/health must return 401,
#    which exercises Next.js dynamic-route handling, the cookies() runtime, the auth
#    guard and response serialization on the new revision. Deterministic and
#    credential-free — getServerUser() returns null on a missing __session cookie
#    before ever touching Firebase Admin — so it cannot false-red on secret access.
#  - The sidecar probe is labelled a DEPENDENCY check, not a candidate check, and says
#    so loudly when it is using the hardcoded fallback instead of a supplied URL.
#  - Probes accumulate into FAIL and report together (matching
#    mcp_end_to_end_smoke.sh's convention) rather than aborting on the first failure.
#
# Honestly NOT covered, and deliberately not claimed: no DB round-trip, no
# authenticated request, no chart render. Those need a web canary credential that
# does not exist yet — the same class of gap deploy.yml already documents for the MCP
# canary key. Recorded as a residual rather than papered over.

set -uo pipefail

WEB_URL="${SMOKE_WEB_URL:-https://amjis-web-938361928218.asia-south1.run.app}"
SIDECAR_URL_DEFAULT="https://amjis-sidecar-938361928218.asia-south1.run.app"
SIDECAR_URL="${SMOKE_SIDECAR_URL:-$SIDECAR_URL_DEFAULT}"
MAX_RETRIES=5
RETRY_DELAY=6  # seconds

check_health() {
  local url="$1"
  local label="$2"
  local path="${3:-/api/health}"
  local attempt=1
  local status="000"

  while [ $attempt -le $MAX_RETRIES ]; do
    echo "  [${label}] attempt ${attempt}/${MAX_RETRIES} → ${url}${path}"
    status=$(curl --silent --max-time 15 --write-out '%{http_code}' --output /dev/null "${url}${path}" || echo "000")
    if [ "$status" = "200" ]; then
      echo "  [${label}] OK (HTTP 200)"
      return 0
    fi
    echo "  [${label}] got HTTP ${status} — retrying in ${RETRY_DELAY}s"
    sleep $RETRY_DELAY
    attempt=$((attempt + 1))
  done

  echo "ERROR: [${label}] health check failed after ${MAX_RETRIES} attempts (last status: ${status})"
  return 1
}

# F-32: a real application probe against the CANDIDATE revision.
# /api/sidecar/health is auth-guarded, so unauthenticated MUST be 401. A 200 would
# mean the guard is not running; a 5xx means the app code is broken on this revision.
# Neither is visible to the static /api/health route.
probe_auth_enforced() {
  local url="$1"
  local status
  status=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "${url}/api/sidecar/health")
  echo "  [probe: auth-enforced] GET /api/sidecar/health (no session cookie) → ${status} (expect 401)"
  [ "$status" = "401" ]
}

echo "=== Post-deploy smoke: amjis-web (${WEB_URL}) ==="

FAIL=0

# 1. Liveness of the candidate revision. Static route — proves boot + routing only.
if check_health "$WEB_URL" "amjis-web boot" "/api/health"; then
  echo "  PASS: candidate revision boots and routes (static /api/health — boot evidence only)"
else
  FAIL=1
fi

# 2. Real application behaviour on the candidate revision.
if probe_auth_enforced "$WEB_URL"; then
  echo "  PASS: auth guard enforced on the candidate revision"
else
  echo "  FAIL: unauthenticated /api/sidecar/health did not return 401 on the candidate."
  echo "        Either the auth guard is not running or the route is erroring — do not promote."
  FAIL=1
fi

# 3. Dependency check. NOT a check of the candidate — the sidecar is a separate,
#    already-serving service. Labelled so a green here is never mistaken for
#    evidence about the revision being promoted.
if [ -z "${SMOKE_SIDECAR_URL:-}" ]; then
  echo "  NOTE: SMOKE_SIDECAR_URL not supplied; using hardcoded default ${SIDECAR_URL_DEFAULT}."
  echo "        This probes the LIVE sidecar as a dependency — it says nothing about the candidate."
fi
if check_health "$SIDECAR_URL" "amjis-sidecar (dependency, not the candidate)" "/health"; then
  echo "  PASS: sidecar dependency reachable"
else
  echo "  FAIL: sidecar dependency unreachable — the new web revision would depend on a down service."
  FAIL=1
fi

if [ "$FAIL" -ne 0 ]; then
  echo "=== Smoke FAIL ==="
  exit 1
fi

echo "=== Smoke PASS ==="
