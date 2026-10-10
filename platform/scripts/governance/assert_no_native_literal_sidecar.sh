#!/usr/bin/env bash
# assert_no_native_literal_sidecar.sh -- native-data ratchet for python-sidecar routers/services/brahmagyan.
# SS N-384 (PR-S6). Sibling of assert_no_native_literal.sh (platform/src/lib/retrieval).
#
# Runs the detector's self-test (it must flag a synthetic offender, pass a clean file, and enforce the
# allowlist ratchet + stale-entry checks) and then scans the repo. Pure stdlib python3.
#
# Exit 0 clean, 1 violation(s), 2 invocation error.   Usage:  bash platform/scripts/governance/assert_no_native_literal_sidecar.sh
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
tool="${here}/assert_no_native_literal_sidecar.py"

if [ ! -f "${tool}" ]; then
  echo "sidecar native-literal gate: ${tool} not found." >&2
  exit 2
fi

python3 "${tool}" --self-test
python3 "${tool}" "$@"
