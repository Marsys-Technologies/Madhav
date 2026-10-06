#!/usr/bin/env bash
# KĀLA-YANTRA preflight — run before `kalayantra_fleet.sh up`. Refuses to pass on anything the fleet cannot run without.
# Writes $KY_ROOT/run/PREFLIGHT_OK (the B-3 detector) only when every REQUIRED check passes. Idempotent.
set -uo pipefail
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"
CAMP="$KY_ROOT/wt/campaign"; RUN="$KY_ROOT/run"; EPHE="${SE_EPHE_PATH:-$KY_ROOT/ephe}"
mkdir -p "$RUN" "$EPHE" "$KY_ROOT/logs" "$RUN/reviews"
FAIL=0; req() { if eval "$2" >/dev/null 2>&1; then echo "✓ $1"; else echo "✗ $1"; FAIL=1; fi; }
warn() { if eval "$2" >/dev/null 2>&1; then echo "✓ $1"; else echo "△ $1 (optional: $3)"; fi; }

echo "── tools"
req "codex CLI"                     "command -v codex && codex --version"
req "gh authenticated"              "gh auth status"
req "git worktree root (campaign)"  "git -C $CAMP rev-parse --is-inside-work-tree"
req "docker daemon"                 "docker info"
req "python venv imports"           "$CAMP/platform/python-sidecar/venv/bin/python -c 'import pytest, psycopg, swisseph'"
req "node modules (platform)"       "test -d $CAMP/platform/node_modules || (cd $CAMP/platform && npm ci)"
req "node modules (platform-mcp)"   "test -d $CAMP/platform-mcp/node_modules || (cd $CAMP/platform-mcp && npm ci)"
req "homebrew python3 for tracker"  "test -x /opt/homebrew/bin/python3"

echo "── Swiss ephemeris (pinned)"
PINS="$CAMP/platform/python-sidecar/services/gochara_kernel/ephemeris_pins.py"
BASE="https://storage.googleapis.com/madhav-ephemeris/se1"
for f in sepl_18.se1 semo_18.se1 seas_18.se1; do
  want="$(grep -oE "\"$f\": \"[0-9a-f]{64}\"" "$PINS" | grep -oE '[0-9a-f]{64}')"
  [ -f "$EPHE/$f" ] || curl -fsSL -o "$EPHE/$f" "$BASE/$f" || true
  have="$(shasum -a 256 "$EPHE/$f" 2>/dev/null | cut -d' ' -f1)"
  if [ -n "$want" ] && [ "$want" = "$have" ]; then echo "✓ $f sha256 ok"; else echo "✗ $f sha256 mismatch or missing (want ${want:-?})"; FAIL=1; fi
done

echo "── control plane"
req "plan model parses"             "/opt/homebrew/bin/python3 -c 'import json; json.load(open(\"$CAMP/00_ARCHITECTURE/control/kalayantra/plan_model.json\"))'"
warn "tracker on 8767"              "curl -fs -m 3 http://127.0.0.1:8767/api/health" "run fleet/install_tracker.sh (B-2)"
warn "ky CLI"                       "test -x $KY_ROOT/bin/ky" "installed by install_tracker.sh"
warn "Pravāha tracker on 8766 (absorbed campaign)" "curl -fs -m 3 http://127.0.0.1:8766/api/health" "launchd com.madhav.pravaha.tracker"
warn "Pravāha CLI"                  "test -x /Users/Dev/pravaha/bin/pravaha" "needed by the J lane"

echo "── credentials present in THIS shell (presence only; values never printed)"
warn "KY_BUILDER_DATABASE_URL"      "test -n \"\${KY_BUILDER_DATABASE_URL:-}\"" "production dispatch items (J-2/J-3/J-4/K9-4) defer until exported"
warn "KY_OWNER_DATABASE_URL"        "test -n \"\${KY_OWNER_DATABASE_URL:-}\"" "D-TEARDOWN alternative applies"
warn "read-only pgenv"              "test -f /Users/Dev/.config/pravaha/pgenv.sh" "db_query detectors read unmeasured"
warn "gcloud account"               "gcloud auth list --format='value(account)' | grep -q ." "Cloud Run builds defer"

echo "── coexistence"
warn "NIRMANA_HOLD present (Nirmāṇa paused; not ours)" "test -f /Users/Dev/Vibe-Coding/Apps/Madhav/NIRMANA_HOLD" "if absent, another fleet may be live — SŪTRADHĀRA checks the coordination file"
req "campaign branch pushed"        "git -C $CAMP ls-remote --exit-code origin campaign/kalayantra"

echo
if [ $FAIL -eq 0 ]; then date -u +%Y-%m-%dT%H:%M:%SZ > "$RUN/PREFLIGHT_OK"; echo "PREFLIGHT OK → $RUN/PREFLIGHT_OK"; else rm -f "$RUN/PREFLIGHT_OK"; echo "PREFLIGHT FAILED — fix the ✗ lines"; fi
exit $FAIL
