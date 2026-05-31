#!/usr/bin/env bash
# end_to_end_smoke.sh — post-deploy smoke test
# Called from deploy.yml after new revisions are deployed (no-traffic).
# Exits non-zero on any failure → deploy.yml skips traffic promotion.

set -euo pipefail

WEB_URL="${SMOKE_WEB_URL:-https://amjis-web-938361928218.asia-south1.run.app}"
SIDECAR_URL="${SMOKE_SIDECAR_URL:-https://amjis-sidecar-938361928218.asia-south1.run.app}"
MAX_RETRIES=5
RETRY_DELAY=6  # seconds

check_health() {
  local url="$1"
  local label="$2"
  local attempt=1

  while [ $attempt -le $MAX_RETRIES ]; do
    echo "  [${label}] attempt ${attempt}/${MAX_RETRIES} → ${url}/api/health"
    status=$(curl --silent --max-time 15 --write-out '%{http_code}' --output /dev/null "${url}/api/health" || echo "000")
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

echo "=== Post-deploy smoke ==="
check_health "$WEB_URL"     "amjis-web"
check_health "$SIDECAR_URL" "amjis-sidecar"
echo "=== Smoke PASS ==="
