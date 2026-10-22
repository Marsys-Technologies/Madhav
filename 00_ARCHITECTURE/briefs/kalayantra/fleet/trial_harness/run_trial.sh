#!/usr/bin/env bash
# TRIAL_SLICE v2: the 12-class trial under a named result policy (default window_qualification/1), passed explicitly.
#   usage: run_trial.sh <code checkout> [out_dir]
#   env:   TRIAL_POLICY=window_qualification/1|all_null_candidate/1|default   (default window_qualification/1)
#          TRIAL_BUDGET_S=300         stop launching work after N s and exit 75 (run the SAME command again to resume) — for a 10-minute foreground limit
#          TRIAL_GATE_ENTRY=module:function   the numerical-window gate, if not the gate module's own generation_verdict
#          TRIAL_BASELINE=<baseline_12.json> (default: baseline_12.json next to this script)   TRIAL_PROFILE=<gate profile JSON>
#          TRIAL_VERIFY=1             run the verification job inline after the build (G-4)
#          TRIAL_CROSSCHECK=1         run the G-6 cross-check after the build            TRIAL_CROSSCHECK_SEED=<int>
#          TRIAL_CODE_HEAD=<40-hex>   REQUIRED for a `git archive` export (not a git work tree)
#          TRIAL_CLASSES=a,b,..       default: the 12 classes   TRIAL_LABEL=trial   TRIAL_KEEP_DB=1   TRIAL_DISPATCH_MODULES=<json {module: sha256}>
#          TRIAL_SOLVER_MODULE=pkg.module   where the checkout's solver lives (default services.gochara_kernel.window_solver)
#          TRIAL_PYTHON=<python>      default /Users/Dev/kalayantra/venv/bin/python
#          TRIAL_DECISION_TABLE=<json>  the G-3 decision table (default: g3_decision_table.json next to this script) — loaded and validated on EVERY run
#          TRIAL_DISPATCH_DIGESTS=<json>  the dispatch head's digests record (G-8)
#          TRIAL_READY_REPO=<clean work tree at the head>  run the merged TRIAL_READY/1 evaluator   TRIAL_READY_JSON=<trial_ready.json>  or supply its result   TRIAL_READY_TIMEOUT_S
#          TRIAL_EQ_REPO=<git repo containing the head>  emit EQUIVALENCE_RECORD/1   TRIAL_EQ_TOOL=<equivalence_record.py>   TRIAL_EQ_PINNED_EXTRA=<json>
#          TRIAL_IMAGE_DIGEST=sha256:..  provenance of the image the run executed in
#          TRIAL_DRY_RUN=1            print the command (one argument per line) and exit 0
# Portable: bash or zsh can run it (arguments are built as an ARRAY — the v1 launcher relied on zsh-only word handling and lost `--gate-entry`/`--budget-s`).
# Writes <out_dir>/trial_report.json (+ report.json, state.json, gate_verdict.json for a numerical policy with a baseline).  The throwaway database is dropped at
# the end of a completed run.
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
CHECKOUT="${1:?usage: run_trial.sh <checkout> [out_dir]}"
OUT="${2:-${JOB_SCRATCH:?no out_dir given and JOB_SCRATCH is not set}/trial_$(date -u +%Y%m%dT%H%M%SZ)}"
PY="${TRIAL_PYTHON:-/Users/Dev/kalayantra/venv/bin/python}"
args=(run --checkout "$CHECKOUT" --result-policy "${TRIAL_POLICY:-window_qualification/1}" --out "$OUT" --label "${TRIAL_LABEL:-trial}"
      --baseline "${TRIAL_BASELINE:-$HERE/baseline_12.json}")
if [ -n "${TRIAL_BUDGET_S:-}" ]; then args+=(--budget-s "$TRIAL_BUDGET_S"); fi
if [ -n "${TRIAL_GATE_ENTRY:-}" ]; then args+=(--gate-entry "$TRIAL_GATE_ENTRY"); fi
if [ -n "${TRIAL_PROFILE:-}" ]; then args+=(--profile "$TRIAL_PROFILE"); fi
if [ -n "${TRIAL_CODE_HEAD:-}" ]; then args+=(--code-head "$TRIAL_CODE_HEAD"); fi
# the verification job names its runner by GOCHARA_RUNNER_COMMIT or the checkout's git HEAD (window_gate.runner_identity); a `git archive` export has no
# HEAD, so the harness names it by the commit it was exported from (the same TRIAL_CODE_HEAD the run records). An explicit value is never overridden.
if [ -n "${TRIAL_CODE_HEAD:-}" ] && [ -z "${GOCHARA_RUNNER_COMMIT:-}" ]; then export GOCHARA_RUNNER_COMMIT="$TRIAL_CODE_HEAD"; fi
if [ -n "${TRIAL_CLASSES:-}" ]; then args+=(--classes "$TRIAL_CLASSES"); fi
if [ -n "${TRIAL_CROSSCHECK_SEED:-}" ]; then args+=(--crosscheck-seed "$TRIAL_CROSSCHECK_SEED"); fi
if [ -n "${TRIAL_SOLVER_MODULE:-}" ]; then args+=(--solver-module "$TRIAL_SOLVER_MODULE"); fi
if [ -n "${TRIAL_DISPATCH_MODULES:-}" ]; then args+=(--dispatch-modules "$TRIAL_DISPATCH_MODULES"); fi
if [ -n "${TRIAL_DECISION_TABLE:-}" ]; then args+=(--decision-table "$TRIAL_DECISION_TABLE"); fi
if [ -n "${TRIAL_DISPATCH_DIGESTS:-}" ]; then args+=(--dispatch-digests "$TRIAL_DISPATCH_DIGESTS"); fi
if [ -n "${TRIAL_READY_REPO:-}" ]; then args+=(--trial-ready-repo "$TRIAL_READY_REPO"); fi
if [ -n "${TRIAL_READY_JSON:-}" ]; then args+=(--trial-ready-json "$TRIAL_READY_JSON"); fi
if [ -n "${TRIAL_READY_TIMEOUT_S:-}" ]; then args+=(--trial-ready-timeout-s "$TRIAL_READY_TIMEOUT_S"); fi
if [ -n "${TRIAL_EQ_REPO:-}" ]; then args+=(--eq-repo "$TRIAL_EQ_REPO"); fi
if [ -n "${TRIAL_EQ_TOOL:-}" ]; then args+=(--eq-tool "$TRIAL_EQ_TOOL"); fi
if [ -n "${TRIAL_EQ_PINNED_EXTRA:-}" ]; then args+=(--eq-pinned-extra "$TRIAL_EQ_PINNED_EXTRA"); fi
if [ -n "${TRIAL_IMAGE_DIGEST:-}" ]; then args+=(--image-digest "$TRIAL_IMAGE_DIGEST"); fi
if [ "${TRIAL_VERIFY:-}" = "1" ]; then args+=(--verify); fi
if [ "${TRIAL_CROSSCHECK:-}" = "1" ]; then args+=(--crosscheck); fi
if [ "${TRIAL_KEEP_DB:-}" = "1" ]; then args+=(--keep-db); fi
if [ "${TRIAL_DRY_RUN:-}" = "1" ]; then printf '%s\n' "$PY" -I -X utf8 "$HERE/trial_slice.py" "${args[@]}"; exit 0; fi
exec "$PY" -I -X utf8 "$HERE/trial_slice.py" "${args[@]}"
