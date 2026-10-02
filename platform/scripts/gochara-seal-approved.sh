#!/usr/bin/env bash
# The GATED job's one executable unit (R12-2): re-verify the retained brief, extract THIS run's approval, and only then call Stream A's seal job — which owns the ONE
# transaction (recompute under the seal locks -> publish -> authoritative seal -> receipt; any failure rolls back publication too).
# Every refusal stops here with a non-zero status BEFORE the seal job is invoked; the seal job's own non-zero status is propagated unchanged
# (0 sealed / 2 refused, nothing written / 3 approval mismatch / 4 identity / 5 error). The sealer credential (GOCHARA_SEALER_DB_URL) is only ever in THIS job's environment.
set -Eeuo pipefail
set +x
umask 077

: "${BRIEF_FILE:?}" "${BRIEF_COMPACT_FILE:?}" "${BRIEF_ENVELOPE_FILE:?}" "${APPROVALS_FILE:?}" "${CHART_ID:?}" "${GENERATION:?}" "${EXPECTED_SEALING_COMMIT:?}" "${GITHUB_RUN_ID:?}" "${GITHUB_RUN_ATTEMPT:?}" "${TRIGGERING_ACTOR:?}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SEAL_JOB_CMD="${SEAL_JOB_CMD:-$PYTHON_BIN -m pipeline.orchestrator.seal_job}"
APPROVAL_FILE="${APPROVAL_FILE:-$(mktemp)}"
ENVIRONMENT_NAME="${ENVIRONMENT_NAME:-gochara-seal}"

# the sealing revision this job runs from IS the reviewed revision the brief was produced for
[ "${GITHUB_SHA:-$EXPECTED_SEALING_COMMIT}" = "$EXPECTED_SEALING_COMMIT" ] || { echo "REFUSED: this job runs from ${GITHUB_SHA}, not the reviewed sealing revision $EXPECTED_SEALING_COMMIT" >&2; exit 2; }

BRIEF_DIGEST="$("$PYTHON_BIN" "$HERE/gochara_seal_brief_check.py" --brief-file "$BRIEF_FILE" --compact-file "$BRIEF_COMPACT_FILE" --chart-id "$CHART_ID" --generation "$GENERATION" --sealing-commit "$EXPECTED_SEALING_COMMIT")" \
  || { echo "REFUSED: the retained brief did not verify — nothing was sealed" >&2; exit 2; }
if [ -n "${EXPECTED_BRIEF_DIGEST:-}" ] && [ "$BRIEF_DIGEST" != "$EXPECTED_BRIEF_DIGEST" ]; then
  echo "REFUSED: the retained brief's digest $BRIEF_DIGEST is not the digest the brief job published ($EXPECTED_BRIEF_DIGEST)" >&2; exit 2
fi
# R13-3: the retained envelope (the EXECUTED resource the brief job verified) is for THIS run, attempt, commit and brief — a brief or envelope of another attempt is never reused
BRIEF_ID="$("$PYTHON_BIN" "$HERE/gochara_seal_execution_check.py" check-envelope --envelope-file "$BRIEF_ENVELOPE_FILE" --compact-file "$BRIEF_COMPACT_FILE" --run-id "$GITHUB_RUN_ID" \
  --attempt "$GITHUB_RUN_ATTEMPT" --sealing-commit "$EXPECTED_SEALING_COMMIT" --brief-digest "$BRIEF_DIGEST")" \
  || { echo "REFUSED: the retained execution envelope does not match this run, attempt, commit and brief — nothing was sealed (start a fresh run)" >&2; exit 2; }
"$PYTHON_BIN" "$HERE/gochara_seal_approval.py" --approvals-file "$APPROVALS_FILE" --environment "$ENVIRONMENT_NAME" --run-id "$GITHUB_RUN_ID" \
  --attempt "$GITHUB_RUN_ATTEMPT" --brief-digest "$BRIEF_DIGEST" --brief-id "$BRIEF_ID" --triggering-actor "$TRIGGERING_ACTOR" --out "$APPROVAL_FILE" \
  || { echo "REFUSED: no valid approval for this run and attempt — nothing was sealed" >&2; exit 2; }

export GOCHARA_SEALING_COMMIT="$EXPECTED_SEALING_COMMIT"
# the seal job requires the approval note's actor to be THIS run's triggering actor (it reads GITHUB_TRIGGERING_ACTOR): refuse any disagreement, then export the one value
if [ -n "${GITHUB_TRIGGERING_ACTOR:-}" ] && [ "$GITHUB_TRIGGERING_ACTOR" != "$TRIGGERING_ACTOR" ]; then
  echo "REFUSED: GITHUB_TRIGGERING_ACTOR ($GITHUB_TRIGGERING_ACTOR) differs from the workflow's triggering actor ($TRIGGERING_ACTOR)" >&2; exit 2
fi
export GITHUB_TRIGGERING_ACTOR="$TRIGGERING_ACTOR"
set +e
# shellcheck disable=SC2086
$SEAL_JOB_CMD --chart "$CHART_ID" --generation "$GENERATION" --approval-file "$APPROVAL_FILE"
rc=$?
set -e
case "$rc" in
  0) echo "SEALED: brief $BRIEF_DIGEST, receipt written in the sealing transaction." ;;
  2) echo "SEAL JOB REFUSED (nothing written)." >&2 ;;
  3) echo "SEAL JOB: the approval does not match what is now recomputed (a changed candidate invalidates the approval); nothing published." >&2 ;;
  4) echo "SEAL JOB: identity check failed (not the sealer); nothing written." >&2 ;;
  *) echo "SEAL JOB FAILED (exit $rc): the sealing transaction rolled back; verify the generation is still a candidate before retrying." >&2 ;;
esac
exit "$rc"
