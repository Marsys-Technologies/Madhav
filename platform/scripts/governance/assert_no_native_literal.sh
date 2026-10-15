#!/usr/bin/env bash
# assert_no_native_literal.sh — G4 gate (Unit 2a) + native-literal ratchet (SS N-380 PR-S5).
#
# PART 1 (unchanged). Asserts that NO `NATIVE_CHART_ID` or `DEFAULT_CHART_ID` identifier
# literal appears in `platform/src/lib/retrieval/` outside:
#   - test files     (*.test.ts, *.test.tsx, *_test.ts, __tests__/, __smoke__/)
#   - eval/         (eval harness — golden-result test infrastructure)
#   - chart_context.ts       (the resolver module that documents what it forbids)
#   - chart_agnostic_gate.ts (the gate module that defines the forbidden constant)
#
# PART 2 (ratchet). Asserts that `platform/scripts` carries NO literal of the native's
# birth/identity data (CLAUDE.md section B: that data lives in the `chart_facts` / `charts`
# tables and is read from there, never embedded in code):
#   name        the native's given name, case-insensitive. This also catches the chart-constant
#               names built on it, legacy `<given>_<family>` native_id slugs and the
#               personal-email local-part / OS-user forms, which all contain it
#   surname     the family name, case-insensitive, EXCEPT on lines that name the second
#               (consented) test chart, whose owner shares the family name
#   dob         the birth date, ISO form
#   birth-time  the birth clock time on a line that also carries a birth context
#               (birthplace, year, IST/+05:30, the word birth)
#   phantom     the dead phantom chart id (its first two UUID groups, i.e. the full form; the bare
#               8-hex prefix inside a refusal guard is correct and is not matched)
#   anchor      the FORENSIC birth-anchor oracle labels (birth-tithi subject, birth-karana label)
#
# Every file that legitimately carries a token is listed in
# platform/scripts/governance/native_literal_allowlist.txt as `<path relative to
# platform/scripts><TAB><reason>`. The ratchet runs both ways:
#   - a file with a token that is NOT on the allowlist fails the gate (no new literal);
#   - an allowlist entry whose file no longer has any token (or no longer exists) is STALE and
#     also fails the gate: remove the entry, so the list can only shrink.
# This script, its allowlist and its self-test build the tokens from fragments so they never
# match themselves; no self-exclusion is needed.
#
# Exits 0 (GREEN) if nothing offends. Exits 1 (RED) and prints the offenders otherwise.
#
# Run from the repo root:
#   $ ./platform/scripts/governance/assert_no_native_literal.sh
#
# Set G4_VERBOSE=1 to see what was scanned even on success.
# Test hooks (used by governance/__tests__/test_assert_no_native_literal.py only):
#   G4_RETRIEVAL_DIR, G4_SCRIPTS_DIR, G4_SCRIPTS_ALLOWLIST

set -euo pipefail
export LC_ALL=C

repo_root="$(cd "$(dirname "$0")"/../../.. && pwd)"
target_dir="${G4_RETRIEVAL_DIR:-${repo_root}/platform/src/lib/retrieval}"

if [ ! -d "${target_dir}" ]; then
  echo "G4 gate: target directory ${target_dir} not found." >&2
  exit 2
fi

# ───────────────────────── PART 1: retrieval identifiers ─────────────────────────
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

# ───────────────────────── PART 2: native-literal ratchet ─────────────────────────
scripts_dir="${G4_SCRIPTS_DIR:-${repo_root}/platform/scripts}"
allowlist="${G4_SCRIPTS_ALLOWLIST:-${repo_root}/platform/scripts/governance/native_literal_allowlist.txt}"

if [ ! -d "${scripts_dir}" ]; then
  echo "G4 gate: scripts directory ${scripts_dir} not found." >&2
  exit 2
fi
if [ ! -f "${allowlist}" ]; then
  echo "G4 gate: allowlist ${allowlist} not found." >&2
  exit 2
fi

# Tokens, built from fragments so this file never matches itself.
t_name='abhi''sek'
t_surname='moh''anty'
t_dob='1984''-02-05'
t_time='10''Q43'; t_time="${t_time/Q/:}"
t_time_ctx='bhubaneswar|1984|(^|[^A-Za-z])IST([^A-Za-z]|$)|\+05:30|birth'
t_phantom='362f9f17''-95a5'
t_anchor='TITHI_''BIRTH|Karana = Gara''ja|"karana": "Gara''ja"|karana: .Gara''ja.'
t_second_chart='abhinandan'

work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT
hits="${work}/hits.tsv"        # path <TAB> line <TAB> token-class
: > "${hits}"

scan() {  # scan <class> ; reads grep -n style "path:line:text" lines on stdin
  awk -F: -v cls="$1" '{ p=$1; sub(/^\.\//, "", p); print p "\t" $2 "\t" cls }' >> "${hits}"
}

(
  cd "${scripts_dir}"
  # the allowlist itself names files (some file names contain a token), so it is never scanned
  common=(-rIn --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude-dir=.git --exclude=native_literal_allowlist.txt)
  { grep "${common[@]}" -i -e "${t_name}" . || true; }                                   | scan name
  { grep "${common[@]}" -i -e "${t_surname}" . | grep -vi -e "${t_second_chart}" || true; } | scan surname
  { grep "${common[@]}" -e "${t_dob}" . || true; }                                        | scan dob
  { grep "${common[@]}" -e "${t_time}" . | grep -iE -e "${t_time_ctx}" || true; }         | scan birth-time
  { grep "${common[@]}" -e "${t_phantom}" . || true; }                                    | scan phantom
  { grep "${common[@]}" -E -e "${t_anchor}" . || true; }                                  | scan anchor
)

cut -f1 "${hits}" | sort -u > "${work}/files_with_hits.txt"

# Parse the allowlist: `<path><TAB><reason>`; '#' lines and blank lines ignored.
allowed="${work}/allowed.txt"
: > "${allowed}"
bad_allowlist=0
lineno=0
while IFS= read -r raw || [ -n "${raw}" ]; do
  lineno=$((lineno + 1))
  case "${raw}" in ''|'#'*) continue ;; esac
  path="${raw%%$'\t'*}"
  reason=""
  case "${raw}" in *$'\t'*) reason="${raw#*$'\t'}" ;; esac
  if [ -z "${path}" ] || [ -z "${reason// /}" ]; then
    echo "G4 GATE FAILED — allowlist line ${lineno} has no '<path><TAB><reason>': ${raw}" >&2
    bad_allowlist=1
    continue
  fi
  if grep -qxF -e "${path}" "${allowed}"; then
    echo "G4 GATE FAILED — allowlist line ${lineno} duplicates an earlier entry: ${path}" >&2
    bad_allowlist=1
    continue
  fi
  printf '%s\n' "${path}" >> "${allowed}"
done < "${allowlist}"
sort -u "${allowed}" -o "${allowed}"

new_literals="$(comm -23 "${work}/files_with_hits.txt" "${allowed}")"
stale_entries="$(comm -13 "${work}/files_with_hits.txt" "${allowed}")"

status=0
if [ "${bad_allowlist}" -ne 0 ]; then status=1; fi

if [ -n "${new_literals}" ]; then
  status=1
  echo "G4 GATE FAILED — native birth/identity literal found in platform/scripts (not allowlisted):" >&2
  while IFS= read -r f; do
    awk -F'\t' -v f="${f}" '$1 == f && n < 5 { printf "  %s:%s  [%s]\n", $1, $2, $3; n++ }' "${hits}" >&2
  done <<EOF
${new_literals}
EOF
  echo "" >&2
  echo "Fix: read the value from the chart_facts / charts tables (or take it as a required argument);" >&2
  echo "     use platform/src/lib/schools/__fixtures__/synthetic_chart.ts or the consented second chart in fixtures." >&2
  echo "     Only if the file is a genuine oracle / historical record, add '<path><TAB><reason>' to" >&2
  echo "     platform/scripts/governance/native_literal_allowlist.txt." >&2
fi

if [ -n "${stale_entries}" ]; then
  status=1
  echo "G4 GATE FAILED — STALE allowlist entries (file no longer carries a native literal, or no longer exists):" >&2
  while IFS= read -r f; do echo "  ${f}" >&2; done <<EOF
${stale_entries}
EOF
  echo "Fix: delete these lines from platform/scripts/governance/native_literal_allowlist.txt (the ratchet only tightens)." >&2
fi

if [ "${status}" -ne 0 ]; then
  exit 1
fi

if [ "${G4_VERBOSE:-0}" = "1" ]; then
  echo "G4 gate: scanned ${target_dir}"
  echo "G4 gate: no NATIVE_CHART_ID / DEFAULT_CHART_ID literal found in production paths."
  echo "G4 gate: scanned ${scripts_dir}: $(wc -l < "${work}/files_with_hits.txt" | tr -d ' ') file(s) with native tokens, all allowlisted; $(wc -l < "${allowed}" | tr -d ' ') allowlist entries, none stale."
fi

exit 0
