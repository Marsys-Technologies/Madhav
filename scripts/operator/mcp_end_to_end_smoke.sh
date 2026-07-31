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
#
# B-MCP-LOG-REDACT (DVA Ruling 64 / SAMAPTI_DVARAPALA_LEDGER.md INC-4, 2026-07-30):
# Probe 4 (URL-token fallback, `?api_key=...`) no longer sends the real canary key
# over the wire. Cloud Run logs `httpRequest.requestUrl` (full path + query string)
# automatically for EVERY request, independent of anything this app logs itself —
# so the old Probe 4 wrote a live, production-capable bearer credential into Cloud
# Logging in plaintext on every single deploy. That is INC-4: a NEW, ACTIVE,
# RECURRING credential exposure, same class as this campaign's earlier INC-1/2/3
# static-file leaks but worse because it re-fired on a schedule rather than being a
# one-time historical leak.
#
# Probe 4 below therefore checks something narrower and HONEST about it: that the
# `/mcp` route accepts request framing with an `api_key` query parameter present
# (i.e. it exercises route-matching + query-string parsing on the live candidate
# revision) using an obviously-fake placeholder value, and expects the SAME 401
# auth-rejection shape Probe 2 (no-auth) gets — proving the endpoint didn't error
# out (500/404/etc.) on that request shape. It does NOT prove a valid credential
# successfully authenticates via this path on the live revision — that would
# require putting a real secret in the URL, which is exactly the leak this fix
# closes. The actual "does ?api_key=<valid-key> authenticate correctly" assertion
# now lives in `platform-mcp/src/__tests__/auth_url_token.test.ts`, run on every CI
# build (not just deploys) against the real `resolveAuthHeader()` +
# `validateMcpKeyFromHeader()` code path, in-process, with a mocked platform
# response — no live network call, no Secret Manager value, ever.

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

# Probe 4 (URL-token fallback — WIRING CHECK ONLY, see B-MCP-LOG-REDACT banner above):
# uses an obviously-fake placeholder, never the real canary key. Confirms the /mcp
# route accepts an api_key= query parameter and produces the standard auth-rejection
# shape (401), i.e. the route + query-string parsing are live on this revision. This
# does NOT verify that a VALID credential authenticates via this path — see
# platform-mcp/src/__tests__/auth_url_token.test.ts for that assertion.
probe_url_token_wiring() {
  local url="$1"
  local status
  status=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 -X POST "${url}/mcp?api_key=smoke-test-placeholder-not-a-real-credential" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d "$INIT_BODY")
  echo "  [probe: url-token-wiring] POST /mcp?api_key=<placeholder> -> ${status} (expect 401 — wiring check only, NOT an auth-success verification; see script banner)"
  [ "$status" = "401" ]
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
  echo "  FAIL: MCP_CANARY_KEY not set — cannot run the Bearer-auth probe."
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
fi

# Probe 4 uses a placeholder, not CANARY_KEY — runs regardless of whether the
# canary key is set (see B-MCP-LOG-REDACT banner above for why).
if probe_url_token_wiring "$MCP_URL"; then
  echo "  PASS: URL-token (?api_key=) route + query-string parsing is wired (wiring check only — see banner)"
else
  echo "  FAIL: URL-token (?api_key=) route did not produce the expected 401 auth-rejection shape"
  FAIL=1
fi

if [ "$FAIL" -ne 0 ]; then
  echo "=== Smoke FAIL ==="
  exit 1
fi

echo "=== Smoke PASS ==="
