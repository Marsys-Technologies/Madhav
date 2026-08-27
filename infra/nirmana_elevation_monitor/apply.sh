#!/usr/bin/env bash
# Dedicated IaC wrapper for the Nirmana elevation monitor.
# A reviewed GCP-native release may apply only the exact saved plan it produced.

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

require_gcp_native_reviewed_apply() {
  if [[ "${IAC_APPLY_ENVIRONMENT:-}" != "production" || ! "${GOOGLE_CLOUD_RELEASE_APPROVAL:-}" =~ ^[A-Za-z0-9][A-Za-z0-9._:/-]{7,127}$ ]]; then
    echo "apply is allowed only through a GCP-native reviewed release with IAC_APPLY_ENVIRONMENT=production and a recorded GOOGLE_CLOUD_RELEASE_APPROVAL" >&2
    exit 2
  fi

  # The release must use short-lived Application Default Credentials or service
  # account impersonation. Static key files cannot provide a trustworthy release
  # boundary or a useful Cloud Audit Logs principal.
  if [[ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
    echo "GCP-native reviewed release refuses GOOGLE_APPLICATION_CREDENTIALS; use Application Default Credentials or service-account impersonation" >&2
    exit 2
  fi

  if ! command -v gcloud >/dev/null 2>&1 || ! gcloud auth application-default print-access-token >/dev/null 2>&1; then
    echo "GCP-native reviewed release requires valid Application Default Credentials from the approved GCP release identity" >&2
    exit 2
  fi
}

case "$CMD" in
  plan)
    [[ -n "$PLAN_FILE" ]] || usage
    ;;
  apply)
    [[ -n "$PLAN_FILE" && -f "$PLAN_FILE" ]] || { echo "apply requires the downloaded saved plan artifact" >&2; exit 2; }
    require_gcp_native_reviewed_apply
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
