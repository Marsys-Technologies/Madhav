#!/usr/bin/env bash
# GATE_V2 launcher: run_gated.sh <target> [args...]
# The ONLY way to start a production data-plane executor / dispatch wrapper. Runs prerun_gate.py (deploy runs not completed
# + builds in flight, both must be 0, source-checked, role-checked, fail closed); ONLY if it exits 0 does it set the launch
# marker GATE_V2_LAUNCH and `exec "$@"` (target and arguments passed through intact, no word splitting).
# The gate's lines go to STDERR (stdout stays clean for a caller parsing the executor's stdout JSON).
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

die() { echo "GATE_V2 FAIL $1" >&2; exit "$2"; }

# (c) refuse the test evidence root / pytest environment outside the test harness (the gate refuses again on its own)
if [ "${GATE_V2_UNDER_TEST:-}" != "1" ]; then
  if [ -n "${ORPH_TEST_EVIDENCE_ROOT+x}" ]; then
    die "test_env_refused (run_gated.sh): ORPH_TEST_EVIDENCE_ROOT is set; run by operators, not by a test harness" 95
  fi
  if [ -n "${PYTEST_CURRENT_TEST+x}" ]; then
    die "test_env_refused (run_gated.sh): PYTEST_CURRENT_TEST is set; run by operators, not by a test harness" 95
  fi
fi
[ "$#" -ge 1 ] || die "usage: run_gated.sh <target> [args...]" 64

# binaries resolved ONCE, as absolute paths, printed, and handed to the gate
resolve() {
  local p
  p="$(command -v "$1" 2>/dev/null || true)"
  case "$p" in
    /*) if [ -x "$p" ]; then printf '%s' "$p"; return 0; fi ;;
  esac
  die "missing_binary: $1 not found as an absolute executable path" 94
}
PY="$(resolve python3)"
GH="$(resolve gh)"
PSQL="$(resolve psql)"
BASH_BIN="$(resolve bash)"
echo "run_gated: python3=$PY gh=$GH psql=$PSQL bash=$BASH_BIN" >&2

rc=0
GATE_V2_GH="$GH" GATE_V2_PSQL="$PSQL" GATE_V2_BASH="$BASH_BIN" "$PY" "$here/prerun_gate.py" 1>&2 || rc=$?
if [ "$rc" -ne 0 ]; then
  echo "run_gated: gate exit=$rc; target NOT started" >&2
  exit "$rc"
fi

# set only here, only after the gate exited 0; executors verify it (executor_standards.py)
marker="$("$PY" "$here/executor_standards.py" make-marker "$here/prerun_gate.py" "$here/run_gated.sh")"
export GATE_V2_LAUNCH="$marker"
echo "run_gated: gate OK; GATE_V2_LAUNCH set; starting target" >&2
exec "$@"
