#!/usr/bin/env bash
# assert_no_native_literal.sh — G4 gate for Unit 2a.
#
# Asserts that NO `NATIVE_CHART_ID` or `DEFAULT_CHART_ID` identifier literal
# appears in `platform/src/lib/retrieval/` outside:
#   - test files     (*.test.ts, *.test.tsx, *_test.ts, __tests__/, __smoke__/)
#   - eval/         (eval harness — golden-result test infrastructure)
#   - chart_context.ts       (the resolver module that documents what it forbids)
#   - chart_agnostic_gate.ts (the gate module that defines the forbidden constant)
#
# Exits 0 (GREEN) if no offending matches.
# Exits 1 (RED) and prints offending matches if any are found.
#
# Run from the repo root:
#   $ ./platform/scripts/governance/assert_no_native_literal.sh
#
# Set G4_VERBOSE=1 to see what files were scanned even on success.

set -euo pipefail

repo_root="$(cd "$(dirname "$0")"/../../.. && pwd)"
target_dir="${repo_root}/platform/src/lib/retrieval"

if [ ! -d "${target_dir}" ]; then
  echo "G4 gate: target directory ${target_dir} not found." >&2
  exit 2
fi

# grep for the two forbidden identifiers as whole words.
#   -R   recursive
#   -n   show line numbers in any error output
#   -w   match whole words (so NATIVE_CHART_ID_X doesn't trigger)
#   -E   extended regex (alternation)
# Exclude test/fixture/smoke files and the resolver module itself.
matches=$(
  grep -RnwE 'NATIVE_CHART_ID|DEFAULT_CHART_ID' "${target_dir}" \
    --exclude-dir=__tests__ \
    --exclude-dir=__smoke__ \
    --exclude-dir=eval \
    --exclude='*.test.ts' \
    --exclude='*.test.tsx' \
    --exclude='*_test.ts' \
    --exclude='chart_context.ts' \
    --exclude='chart_agnostic_gate.ts' \
    || true
)

if [ -n "${matches}" ]; then
  echo "G4 GATE FAILED — NATIVE_CHART_ID/DEFAULT_CHART_ID literal found in production paths:" >&2
  echo "${matches}" >&2
  echo "" >&2
  echo "Fix: replace literal with retrieval/chart_context.requireChartId(input.chart_id)." >&2
  exit 1
fi

if [ "${G4_VERBOSE:-0}" = "1" ]; then
  echo "G4 gate: scanned ${target_dir}"
  echo "G4 gate: no NATIVE_CHART_ID / DEFAULT_CHART_ID literal found in production paths."
fi

exit 0
