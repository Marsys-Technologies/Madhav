#!/usr/bin/env bash
# Dedicated IaC wrapper for the Nirmana elevation monitor.
# A local/worktree invocation may create a plan for review, but only the
# protected-main workflow may apply the exact plan artifact it produced.

set -euo pipefail

CMD="${1:-plan}"
PLAN_FILE="${2:-}"
PROJECT="${TF_VAR_gcp_project:-madhav-astrology}"
REGION="${TF_VAR_gcp_region:-asia-south1}"
STATE_BUCKET="${TF_STATE_BUCKET:-${PROJECT}-tf-state}"
STATE_PREFIX="scheduler/nirmana-elevation-monitor"

usage() {
  echo "usage: $0 plan <saved-plan-file> | apply <saved-plan-file>" >&2
  exit 2
}

require_protected_main_apply() {
  if [[ "${GITHUB_ACTIONS:-}" != "true" || "${GITHUB_REF:-}" != "refs/heads/main" || "${GITHUB_REF_PROTECTED:-}" != "true" || "${IAC_APPLY_ENVIRONMENT:-}" != "production" ]]; then
    echo "apply is allowed only from a protected main ref in the production workflow" >&2
    exit 2
  fi
}

case "$CMD" in
  plan)
    [[ -n "$PLAN_FILE" ]] || usage
    ;;
  apply)
    [[ -n "$PLAN_FILE" && -f "$PLAN_FILE" ]] || { echo "apply requires the downloaded saved plan artifact" >&2; exit 2; }
    require_protected_main_apply
    ;;
  *)
    usage
    ;;
esac

command -v terraform >/dev/null 2>&1 || { echo "terraform CLI not on PATH" >&2; exit 1; }

terraform init -lockfile=readonly \
  -backend-config="bucket=${STATE_BUCKET}" \
  -backend-config="prefix=${STATE_PREFIX}"

case "$CMD" in
  plan)
    terraform plan -out="$PLAN_FILE" -var "gcp_project=${PROJECT}" -var "gcp_region=${REGION}"
    ;;
  apply)
    terraform apply "$PLAN_FILE"
    ;;
esac
