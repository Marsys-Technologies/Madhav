#!/usr/bin/env bash
# run_gated.sh <executor args...>: the ONLY way to start the real dry run / apply of orphan_receipts_exec.py.
# Runs prerun_gate.py (deploy runs + builds in flight, both must be 0, fail closed); only if it exits 0 does it exec
# orphan_receipts_exec.py with the given arguments. The gate's counts are printed first.
set -u
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$here/prerun_gate.py"
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "run_gated: pre-run gate exit=$rc; executor NOT started" >&2
  exit 1
fi
exec python3 "$here/orphan_receipts_exec.py" "$@"
