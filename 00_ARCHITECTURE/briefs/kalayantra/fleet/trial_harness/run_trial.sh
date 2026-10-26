#!/usr/bin/env bash
# TRIAL_SLICE v2: the 12-class (TR-26: 26-class, TRIAL_CLASSES + TRIAL_PROFILE=gate_profile.tr26.json) trial under a named result policy (default window_qualification/1), passed explicitly.
#   usage: run_trial.sh <code checkout> [out_dir]
#   env:   TRIAL_POLICY=window_qualification/1|all_null_candidate/1|default   (default window_qualification/1)
#          TRIAL_BUDGET_S=300         stop launching work after N s and exit 75 (run the SAME command again to resume) — for a 10-minute foreground limit
#          TRIAL_GATE_ENTRY=module:function   the numerical-window gate, if not the gate module's own generation_verdict
#          TRIAL_BASELINE=<baseline_12.json> (default: baseline_12.json next to this script)   TRIAL_PROFILE=<gate profile JSON>
#          TRIAL_VERIFY=1             run the verification job inline after the build (G-4)
#          TRIAL_CROSSCHECK=1         run the G-6 cross-check after the build            TRIAL_CROSSCHECK_SEED=<int>
#          TRIAL_CERT_AUDIT=1         TR-26: the read-only certificate-size / truncation audit of the trial database (counts only), before the database is dropped
#          TRIAL_CODE_HEAD=<40-hex>   REQUIRED for a `git archive` export (not a git work tree)
#          TRIAL_CLASSES=a,b,..       default: the 12 classes   TRIAL_LABEL=trial   TRIAL_KEEP_DB=1   TRIAL_DISPATCH_MODULES=<json {module: sha256}>
#          TRIAL_SOLVER_MODULE=pkg.module   where the checkout's solver lives (default services.gochara_kernel.window_solver)
#          TRIAL_PYTHON=<python>      default /Users/Dev/kalayantra/venv/bin/python
#          TRIAL_DECISION_TABLE=<json>  the G-3 decision table (default: g3_decision_table.json next to this script) — loaded and validated on EVERY run
#          TRIAL_DISPATCH_DIGESTS=<json>  the dispatch head's digests record (G-8)
#          TRIAL_READY_REPO=<clean work tree at the head>  run the merged TRIAL_READY/1 evaluator   TRIAL_READY_JSON=<trial_ready.json>  or supply its result   TRIAL_READY_TIMEOUT_S
#          TRIAL_EQ_REPO=<git repo containing the head>  emit EQUIVALENCE_RECORD/1   TRIAL_EQ_TOOL=<equivalence_record.py>   TRIAL_EQ_PINNED_EXTRA=<json>
#          TRIAL_IMAGE_DIGEST=sha256:..  provenance of the image the run executed in
#          TRIAL_LANE_DB=ky_lane_head  the named head-chain database the TRIAL_READY/1 evaluator reads (only ky_lane_* names). The harness itself exports TRIAL_READY_LANE_DSN (that
#                                      database) and TRIAL_READY_TRIAL_DSN (this run's ky_trial_* database, while it exists) around the trial-ready stage — loopback, no credential.
#          TRIAL_COLLECT=1            COLLECT mode (diagnostic / PRETR): do not stop a class at its first defect; run every remaining grain, fail the class at the END with the full list (default: stop-at-first, the TR shape)
#          TRIAL_BASELINE_MODE=1      BASELINE mode (SR-BASELINE-OVERLAY-SKIP; set only by make_baseline.sh; needs TRIAL_POLICY=default and TRIAL_LABEL=baseline, else refused): a mandatory overlay migration the
#                                     checkout lacks is skipped BY NAME and recorded, only when the checkout also lacks the code that requires it; a trial run (any other policy) always refuses
#          TRIAL_CENTURY_STAGED=1     SR-TR26-G7-RESUME: stage the build as a CENTURY run (a build_runs row carrying the staged century config; the writer records its committed-substep ledger).  TRIAL_ABORT_AFTER_SUBSTEP and
#                                     TRIAL_WRITER_RESUME imply it (the kill+resume legs ARE century runs, so the resume reaches the ledger); on its own it is the fresh uninterrupted reference the resumed generation is compared with
#          TRIAL_AMD64_DOCKER=1       AMD64-DOCKER (SR-T24-AMD64-DOCKER): run the 4-class slice of TRIAL_CODE_HEAD (REQUIRED) in a linux/amd64 DOCKER CONTAINER against a PG 15 / locale C sibling container
#                                     on a private network; <code checkout> is a git repo holding the head (exported with git archive) or an export; TRIAL_CLASSES = a subset of the four;
#                                     TRIAL_IMAGE_DIGEST = use that local image by digest instead of building; TRIAL_EQ_REPO/TRIAL_EQ_TOOL/TRIAL_EQ_PINNED_EXTRA as above (host side);
#                                     TRIAL_BUDGET_S bounds the slice (exit 75 = run the SAME command again: the PG container is kept for it).  The report gets `platform` (wall_comparable
#                                     false under emulation: G-5 reads NOT_EVALUATED) and the record gets runtime.kind qualifying_run, arch read INSIDE the container, the emulation note.
#          TRIAL_DRY_RUN=1            print the command (one argument per line) and exit 0
# Portable: bash or zsh can run it (arguments are built as an ARRAY — the v1 launcher relied on zsh-only word handling and lost `--gate-entry`/`--budget-s`).
# Writes <out_dir>/trial_report.json (+ report.json, state.json, gate_verdict.json for a numerical policy with a baseline).  The throwaway database is dropped at
# the end of a completed run.
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
CHECKOUT="${1:?usage: run_trial.sh <checkout> [out_dir]}"
OUT="${2:-${JOB_SCRATCH:?no out_dir given and JOB_SCRATCH is not set}/trial_$(date -u +%Y%m%dT%H%M%SZ)}"
PY="${TRIAL_PYTHON:-/Users/Dev/kalayantra/venv/bin/python}"
if [ "${TRIAL_AMD64_DOCKER:-}" = "1" ]; then
  aargs=(amd64-run --head "${TRIAL_CODE_HEAD:?TRIAL_AMD64_DOCKER=1 needs TRIAL_CODE_HEAD (the TR head, 40 hex)}" --repo "$CHECKOUT" --out "$OUT")
  if [ -n "${TRIAL_CLASSES:-}" ]; then aargs+=(--classes "$TRIAL_CLASSES"); fi
  if [ -n "${TRIAL_IMAGE_DIGEST:-}" ]; then aargs+=(--image-digest "$TRIAL_IMAGE_DIGEST"); fi
  if [ -n "${TRIAL_BUDGET_S:-}" ]; then aargs+=(--budget-s "$TRIAL_BUDGET_S"); fi
  if [ -n "${TRIAL_EQ_REPO:-}" ]; then aargs+=(--eq-repo "$TRIAL_EQ_REPO"); fi
  if [ -n "${TRIAL_EQ_TOOL:-}" ]; then aargs+=(--eq-tool "$TRIAL_EQ_TOOL"); fi
  if [ -n "${TRIAL_EQ_PINNED_EXTRA:-}" ]; then aargs+=(--pinned-extra "$TRIAL_EQ_PINNED_EXTRA"); fi
  if [ "${TRIAL_DRY_RUN:-}" = "1" ]; then printf '%s\n' "$PY" -I -X utf8 "$HERE/trial_slice.py" "${aargs[@]}"; exit 0; fi
  exec "$PY" -I -X utf8 "$HERE/trial_slice.py" "${aargs[@]}"
fi
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
if [ "${TRIAL_CERT_AUDIT:-}" = "1" ]; then args+=(--cert-audit); fi
if [ "${TRIAL_KEEP_DB:-}" = "1" ]; then args+=(--keep-db); fi
if [ "${TRIAL_COLLECT:-}" = "1" ]; then args+=(--collect); fi
if [ "${TRIAL_BASELINE_MODE:-}" = "1" ]; then args+=(--baseline-mode); fi
if [ "${TRIAL_DRY_RUN:-}" = "1" ]; then printf '%s\n' "$PY" -I -X utf8 "$HERE/trial_slice.py" "${args[@]}"; exit 0; fi
exec "$PY" -I -X utf8 "$HERE/trial_slice.py" "${args[@]}"
