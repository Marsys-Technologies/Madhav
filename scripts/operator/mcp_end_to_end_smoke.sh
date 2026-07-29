#!/usr/bin/env bash
# mcp_end_to_end_smoke.sh — post-deploy smoke test for amjis-mcp
#
# Called from deploy.yml's deploy-mcp job after a new amjis-mcp revision is
# deployed with --no-traffic (candidate build, 0% real traffic). Runs against
# the REVISION-specific URL (deploy-cloudrun's steps.deploy.outputs.url), not
# the public service URL, so this genuinely probes the candidate before any
# user sees it. Mirrors end_to_end_smoke.sh's conventions (retry-loop health
# check, clear PASS/FAIL echoes, non-zero exit on any failure -> deploy.yml
# skips the traffic-promotion step).
#
# Probe shape is the 4-probe pattern documented in
# 00_ARCHITECTURE/CONDUCTOR/MCP_DEPLOY_AND_VERIFY_PROMPT_v1_0.md (health /
# no-auth-rejected / Bearer-auth-works / URL-token-fallback-works), which was
# previously only ever run by hand from a human-operated terminal. This script
# is the first automated version, wired into the deploy pipeline itself
# (PARISHODHANA brief §3 Phase C item 2 — deploy-pipeline parity with amjis-web,
# closing the twice-recurred traffic-pin class).
#
# Requires MCP_CANARY_KEY: a valid mcp_api_keys Bearer credential, held in
# Secret Manager as `mcp-canary-key` and fetched by the calling workflow step
# (see deploy.yml's "Fetch MCP canary key for post-deploy smoke" step). Without
# it, this script still runs the health + no-auth probes but FAILS LOUDLY on
# the missing auth probes rather than silently skipping them — a canary that
# cannot authenticate does not verify the one thing this gate exists to check.

set -euo pipefail

MCP_URL="${SMOKE_MCP_URL:?SMOKE_MCP_URL env var required (revision-specific URL from the deploy-cloudrun step outputs.url)}"
CANARY_KEY="${MCP_CANARY_KEY:-}"
MAX_RETRIES=5
RETRY_DELAY=6  # seconds

# Minimal valid MCP JSON-RPC initialize call — same envelope used by the manual
# 4-probe pattern in MCP_DEPLOY_AND_VERIFY_PROMPT_v1_0.md.
INIT_BODY='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"deploy-smoke","version":"1.0"}}}'

check_health() {
  local url="$1"
  local attempt=1
  local status="000"

  while [ $attempt -le $MAX_RETRIES ]; do
    echo "  [health] attempt ${attempt}/${MAX_RETRIES} -> ${url}/health"
    status=$(curl --silent --max-time 15 --write-out '%{http_code}' --output /dev/null "${url}/health" || echo "000")
    if [ "$status" = "200" ]; then
      echo "  [health] OK (HTTP 200)"
      return 0
    fi
    echo "  [health] got HTTP ${status} — retrying in ${RETRY_DELAY}s"
    sleep $RETRY_DELAY
    attempt=$((attempt + 1))
  done

  echo "ERROR: [health] health check failed after ${MAX_RETRIES} attempts (last status: ${status})"
  return 1
}

# Probe 2 (no-auth): POST /mcp with no Authorization header must be rejected.
probe_no_auth() {
  local url="$1"
  local status
  status=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 -X POST "${url}/mcp" \
    -H "Content-Type: application/json" \
    -d "$INIT_BODY")
  echo "  [probe: no-auth] POST /mcp (no auth) -> ${status} (expect 401)"
  [ "$status" = "401" ]
}

# Probe 3 (Bearer header): the canonical auth path.
probe_bearer_auth() {
  local url="$1" key="$2"
  local status
  status=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 -X POST "${url}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -H "Authorization: Bearer ${key}" \
    -d "$INIT_BODY")
  echo "  [probe: bearer-auth] POST /mcp + Authorization: Bearer -> ${status} (expect 200)"
  [ "$status" = "200" ]
}

# Probe 4 (URL-token fallback): ?api_key=... query-param path.
probe_url_token() {
  local url="$1" key="$2"
  local status
  status=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 -X POST "${url}/mcp?api_key=${key}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d "$INIT_BODY")
  echo "  [probe: url-token-fallback] POST /mcp?api_key=... -> ${status} (expect 200)"
  [ "$status" = "200" ]
}

echo "=== Post-deploy smoke: amjis-mcp (${MCP_URL}) ==="

FAIL=0

check_health "$MCP_URL" || FAIL=1

if probe_no_auth "$MCP_URL"; then
  echo "  PASS: no-auth correctly rejected"
else
  echo "  FAIL: expected 401 rejecting an unauthenticated /mcp call"
  FAIL=1
fi

if [ -z "$CANARY_KEY" ]; then
  echo "  FAIL: MCP_CANARY_KEY not set — cannot run the Bearer-auth / URL-token-fallback probes."
  echo "        A canary that cannot authenticate does not verify the auth path this deploy"
  echo "        gate exists to protect. See the PARISHODHANA Phase-C deploy-pipeline-parity PR"
  echo "        and deploy.yml's 'Fetch MCP canary key for post-deploy smoke' step for the"
  echo "        Secret Manager IAM binding this probe depends on."
  FAIL=1
else
  if probe_bearer_auth "$MCP_URL" "$CANARY_KEY"; then
    echo "  PASS: Authorization: Bearer auth path works"
  else
    echo "  FAIL: Authorization: Bearer auth path rejected a valid canary key"
    FAIL=1
  fi

  if probe_url_token "$MCP_URL" "$CANARY_KEY"; then
    echo "  PASS: URL-token (?api_key=) fallback auth path works"
  else
    echo "  FAIL: URL-token (?api_key=) fallback auth path rejected a valid canary key"
    FAIL=1
  fi
fi

if [ "$FAIL" -ne 0 ]; then
  echo "=== Smoke FAIL ==="
  exit 1
fi

echo "=== Smoke PASS ==="
