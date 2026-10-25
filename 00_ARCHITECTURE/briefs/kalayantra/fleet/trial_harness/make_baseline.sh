#!/usr/bin/env bash
# The 12-class all-null baseline (its own oracle): run the DEFAULT policy on a code export of origin/main, resume on exit 75 until done, then write baseline_12.json.
#   usage: make_baseline.sh <code export or checkout of origin/main> <40-hex head sha> <out_dir> [baseline_12.json]
#   e.g.   git -C <repo> archive <sha> platform | tar -x -C <dir>      (a `git archive` export is not a git work tree, hence the explicit head)
#   env:   TRIAL_CLASSES=a,b,.. (TR-26: the 26; default the 12 — pass the SAME list the trial will run; the DEST is then baseline_26.json by the caller's 4th argument)
#          TRIAL_BUDGET_S (default 330: one chunk fits a 10-minute foreground limit)   BASELINE_MAX_CHUNKS (default 40)
# Exit: 0 baseline written · 1 the oracle failed or the build had a defect (no baseline written) · 2 refused · 3 chunk limit reached.
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
CHECKOUT="${1:?usage: make_baseline.sh <checkout> <head sha> <out_dir> [baseline_12.json]}"
HEAD_SHA="${2:?head sha}"
OUT="${3:?out_dir}"
DEST="${4:-$HERE/baseline_12.json}"
PY="${TRIAL_PYTHON:-/Users/Dev/kalayantra/venv/bin/python}"
chunks=0
while :; do
  chunks=$((chunks + 1))
  rc=0
  TRIAL_BASELINE_MODE=1 TRIAL_POLICY=default TRIAL_CODE_HEAD="$HEAD_SHA" TRIAL_BUDGET_S="${TRIAL_BUDGET_S:-330}" TRIAL_LABEL=baseline TRIAL_BASELINE="$HERE/baseline_report_4class.json" \
    "$HERE/run_trial.sh" "$CHECKOUT" "$OUT" || rc=$?
  if [ "$rc" -eq 75 ]; then
    if [ "$chunks" -ge "${BASELINE_MAX_CHUNKS:-40}" ]; then echo "chunk limit reached"; exit 3; fi
    continue
  fi
  if [ "$rc" -ne 0 ]; then echo "run ended with exit $rc: no baseline written"; exit "$rc"; fi
  break
done
bargs=(baseline --report "$OUT/baseline_report.json" --out "$DEST" --prior-4class "$HERE/baseline_report_4class.json")
if [ -n "${TRIAL_CLASSES:-}" ]; then bargs+=(--classes "$TRIAL_CLASSES"); fi      # TR-26: run_trial.sh already reads TRIAL_CLASSES for the build; the baseline writer must be told the same list
"$PY" -I -X utf8 "$HERE/trial_slice.py" "${bargs[@]}"
