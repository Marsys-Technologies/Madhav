#!/usr/bin/env bash
# KĀLA-YANTRA preflight v1.1 — two modes (charter §7; Astra KY-26).
#   preflight.sh bootstrap   repairs campaign-local dependencies (venv, ephemeris, node modules); never writes a launch receipt
#   preflight.sh launch      requires everything the fleet needs to run safely; writes run/LAUNCH_RECEIPT.json (B-3 detector)
set -uo pipefail
MODE="${1:-bootstrap}"; KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"; CAMP="$KY_ROOT/wt/campaign"; RUN="$KY_ROOT/run"; EPHE="${SE_EPHE_PATH:-$KY_ROOT/ephe}"
mkdir -p "$RUN" "$EPHE" "$KY_ROOT/logs"; FAIL=0; declare -a REPORT=()
req()  { if eval "$2" >/dev/null 2>&1; then echo "✓ $1"; REPORT+=("ok:$1"); else echo "✗ $1"; REPORT+=("FAIL:$1"); FAIL=1; fi; }
warn() { if eval "$2" >/dev/null 2>&1; then echo "✓ $1"; REPORT+=("ok:$1"); else echo "△ $1 ($3)"; REPORT+=("warn:$1"); fi; }
echo "── mode: $MODE"
echo "── tools"
req "codex CLI" "command -v codex"; req "gh authenticated" "gh auth status"
req "campaign worktree" "git -C $CAMP rev-parse --is-inside-work-tree"; req "docker daemon" "docker info"; req "homebrew python3" "test -x /opt/homebrew/bin/python3"
req "campaign venv" "test -x $KY_ROOT/venv/bin/python || (python3 -m venv $KY_ROOT/venv && $KY_ROOT/venv/bin/pip install -q -r $CAMP/platform/python-sidecar/requirements.txt && $KY_ROOT/venv/bin/pip install -q -r $CAMP/platform/python-sidecar/requirements-ci.txt)"
req "venv imports" "$KY_ROOT/venv/bin/python -c 'import pytest, psycopg, swisseph'"
req "node modules (platform)" "test -d $CAMP/platform/node_modules || (cd $CAMP/platform && npm ci)"; req "node modules (platform-mcp)" "test -d $CAMP/platform-mcp/node_modules || (cd $CAMP/platform-mcp && npm ci)"
echo "── Swiss ephemeris (pinned)"
PINS="$CAMP/platform/python-sidecar/services/gochara_kernel/ephemeris_pins.py"; BASE="https://storage.googleapis.com/madhav-ephemeris/se1"
for f in sepl_18.se1 semo_18.se1 seas_18.se1; do
  want="$(grep -oE "\"$f\": \"[0-9a-f]{64}\"" "$PINS" | grep -oE '[0-9a-f]{64}')"; [ -f "$EPHE/$f" ] || curl -fsSL -o "$EPHE/$f" "$BASE/$f" || true
  have="$(shasum -a 256 "$EPHE/$f" 2>/dev/null | cut -d' ' -f1)"; if [ -n "$want" ] && [ "$want" = "$have" ]; then echo "✓ $f"; REPORT+=("ok:$f"); else echo "✗ $f sha256"; REPORT+=("FAIL:$f"); FAIL=1; fi
done
echo "── secrets must NOT be in this shell (the fleet refuses otherwise)"
for v in DATABASE_URL KY_BUILDER_DATABASE_URL KY_OWNER_DATABASE_URL PGPASSWORD; do if [ -n "${!v:-}" ]; then echo "✗ $v is set in this shell — launch the fleet from a shell without it (charter §7)"; FAIL=1; else echo "✓ $v absent"; fi; done
echo "── a real agent start under the exact lane environment (profile, login, models, tools, no credential-like variable)"
if bash "$CAMP/00_ARCHITECTURE/briefs/kalayantra/fleet/kalayantra_fleet.sh" smoke; then REPORT+=("ok:lane smoke"); else REPORT+=("FAIL:lane smoke"); FAIL=1; fi
echo "── control plane"
req "plan model parses" "/opt/homebrew/bin/python3 -c 'import json; json.load(open(\"$CAMP/00_ARCHITECTURE/control/kalayantra/plan_model.json\"))'"
if [ "$MODE" = launch ]; then
  echo "── launch requirements"
  req "specification hashes verified (B-0)" "test -s $RUN/SPEC_HASHES_OK"
  req "tracker install receipt accepted (B-2)" "/opt/homebrew/bin/python3 -c 'import json,sys; d=json.load(open(\"$RUN/TRACKER_INSTALL_RECEIPT.json\")); sys.exit(0 if d.get(\"accepted\") else 1)'"
  req "tracker package is the copied one on main" "grep -q '$KY_ROOT/wt/campaign/platform/scripts/governance' $RUN/TRACKER_GOV"
  req "control-plane acceptance (B-1c)" "test -s $RUN/CONTROL_PLANE_ACCEPTED.json"
  req "tracker health" "curl -fs -m 3 http://127.0.0.1:8767/api/health | grep -q '\"ok\": true'"
  req "ky audit runs" "KY_STREAM=S $KY_ROOT/bin/ky audit --since kickoff"
  req "SESSION_OPEN present (B-4)" "test -s $CAMP/00_ARCHITECTURE/briefs/kalayantra/sessions/SESSION_OPEN_kalayantra.yaml"
  req "Pravāha hand-over recorded (B-5)" "test -s $CAMP/00_ARCHITECTURE/briefs/pravaha/decisions/NATIVE_DIRECT_RULINGS_20261006.md"
  req "executor capabilities fresh (B-6)" "/opt/homebrew/bin/python3 -c 'import json,sys,time,datetime; d=json.load(open(\"$RUN/ops/CAPABILITIES.json\")); t=datetime.datetime.fromisoformat(d[\"ts\"]); sys.exit(0 if (datetime.datetime.now(datetime.timezone.utc)-t).total_seconds()<900 else 1)'"
  req "executor reads its operations table from main (B-6)" "grep -q '\"ops_table_on_main\": true' $RUN/ops/CAPABILITIES.json"
  req "fleet runs from its snapshot" "test -x $KY_ROOT/fleet_live/kalayantra_fleet.sh || test -f $KY_ROOT/fleet_live/kalayantra_fleet.sh"
  req "precheck alignment recorded (B-3b)" "test -s $RUN/PRECHECK_ALIGNMENT.md"
  for l in sutradhara adhikarin v1 v2 v3 k1 k2 k3 k4 k5 k6 k7 k8; do req "worktree $l" "test -d $KY_ROOT/wt/$l/platform"; done
  for l in k1 k2 k3 k4 k5 k6 k7 k8 v1 v2 v3; do req "local DB ky_$l" "PGPASSWORD=postgres psql -h 127.0.0.1 -p 55433 -U postgres -d ky_$l -tAc 'select 1'"; done
  warn "builder capability (production dispatch items)" "grep -q '\"builder\": true' $RUN/ops/CAPABILITIES.json" "J-2a…J-4e, K9-4a block on capability_missing"
  warn "owner capability (small-test teardown)" "grep -q '\"owner\": true' $RUN/ops/CAPABILITIES.json" "D-TEARDOWN → blocked; J-2a blocks"
  warn "NIRMANA_HOLD present (Nirmāṇa paused)" "test -f /Users/Dev/Vibe-Coding/Apps/Madhav/NIRMANA_HOLD" "another fleet may be live — SŪTRADHĀRA checks the coordination file"
fi
echo
if [ $FAIL -eq 0 ]; then
  if [ "$MODE" = launch ]; then
    /opt/homebrew/bin/python3 - "$RUN/LAUNCH_RECEIPT.json" "$CAMP" "${REPORT[@]}" <<'PYEOF'
import hashlib, json, pathlib, subprocess, sys, time
out, camp, *report = sys.argv[1:]
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
k = pathlib.Path(camp) / "00_ARCHITECTURE"
rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "mode": "launch", "checks": report,
       "campaign_head": subprocess.run(["git", "-C", camp, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
       "charter_sha256": sha(k / "briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md"), "model_sha256": sha(k / "control/kalayantra/plan_model.json"),
       "fleet_sha256": sha(k / "briefs/kalayantra/fleet/kalayantra_fleet.sh"), "executor_sha256": sha(k / "briefs/kalayantra/fleet/executor.py")}
pathlib.Path(out).write_text(json.dumps(rec, indent=1)); print("LAUNCH RECEIPT →", out)
PYEOF
  else echo "BOOTSTRAP PREFLIGHT OK (no launch receipt in this mode)"; fi
else echo "PREFLIGHT FAILED — fix the ✗ lines"; [ "$MODE" = launch ] && rm -f "$RUN/LAUNCH_RECEIPT.json"; fi
exit $FAIL
