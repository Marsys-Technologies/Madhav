#!/usr/bin/env bash
# Dedicated reviewed-release wrapper for Nirmana conductor IaC.
set -euo pipefail

CMD="${1:-plan}"
PLAN_FILE="${2:-}"
PROJECT="${TF_VAR_gcp_project:-madhav-astrology}"
REGION="${TF_VAR_gcp_region:-asia-south1}"
STATE_BUCKET="${TF_STATE_BUCKET:-${PROJECT}-tf-state}"
STATE_PREFIX="scheduler/nirmana-elevation-conductor"

usage() { echo "usage: $0 plan <saved-plan-file> | apply <saved-plan-file>" >&2; exit 2; }

attestation_file() { printf '%s.attestation' "$1"; }

sha256_file() { shasum -a 256 "$1" | awk '{print $1}'; }

source_sha() { git rev-parse HEAD; }

assert_create_only_plan() {
  local plan_file="$1"
  local actions
  actions="$(terraform show -json "$plan_file" | jq -r '.resource_changes[]?.change.actions | join(",")' | sort -u)"
  if [[ -n "$actions" && "$actions" != "create" ]]; then
    echo "reviewed conductor foundation apply permits only create actions; got: ${actions//$'\n'/ }" >&2
    exit 2
  fi
}

write_attestation() {
  local plan_file="$1"
  local plan_sha source
  plan_sha="$(sha256_file "$plan_file")"
  source="$(source_sha)"
  printf 'source_sha=%s\nplan_sha256=%s\nactions=create-only\n' "$source" "$plan_sha" > "$(attestation_file "$plan_file")"
}

verify_attestation() {
  local plan_file="$1"
  local attestation source plan_sha expected_source expected_plan
  attestation="$(attestation_file "$plan_file")"
  [[ -f "$attestation" ]] || { echo "apply requires the reviewed plan attestation" >&2; exit 2; }
  source="$(source_sha)"
  plan_sha="$(sha256_file "$plan_file")"
  expected_source="$(awk -F= '$1=="source_sha" {print $2}' "$attestation")"
  expected_plan="$(awk -F= '$1=="plan_sha256" {print $2}' "$attestation")"
  [[ "$source" = "$expected_source" && "$plan_sha" = "$expected_plan" ]] || { echo "apply refuses a plan whose source SHA or digest changed after review" >&2; exit 2; }
  [[ "${GOOGLE_CLOUD_RELEASE_APPROVAL:-}" = *"$plan_sha"* && "${GOOGLE_CLOUD_RELEASE_APPROVAL:-}" = *"$source"* ]] || { echo "apply approval must bind both the exact source SHA and saved-plan digest" >&2; exit 2; }
  assert_create_only_plan "$plan_file"
}

require_reviewed_non_personal_apply() {
  if [[ "${IAC_APPLY_ENVIRONMENT:-}" != "production" ]]; then
    echo "apply requires a recorded GCP-native production release approval" >&2
    exit 2
  fi
  if [[ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
    echo "apply refuses static credential files; use the reviewed workload identity" >&2
    exit 2
  fi
  if ! command -v gcloud >/dev/null 2>&1; then
    echo "apply requires gcloud Application Default Credentials from the reviewed release identity" >&2
    exit 2
  fi
  local account
  account="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | head -n 1)"
  if [[ ! "$account" =~ ^[a-z0-9-]+@madhav-astrology\.iam\.gserviceaccount\.com$ ]]; then
    echo "apply refuses a personal or unscoped gcloud identity; impersonate the reviewed madhav-astrology release service account" >&2
    exit 2
  fi
  gcloud auth application-default print-access-token >/dev/null
}

case "$CMD" in
  plan) [[ -n "$PLAN_FILE" ]] || usage ;;
  apply) [[ -n "$PLAN_FILE" && -f "$PLAN_FILE" ]] || { echo "apply requires the reviewed saved plan" >&2; exit 2; }; require_reviewed_non_personal_apply ;;
  *) usage ;;
esac

command -v terraform >/dev/null 2>&1 || { echo "terraform CLI not on PATH" >&2; exit 1; }
terraform init -lockfile=readonly -backend-config="bucket=${STATE_BUCKET}" -backend-config="prefix=${STATE_PREFIX}"
if [[ "$CMD" == plan ]]; then
  terraform plan -out="$PLAN_FILE" -var "gcp_project=${PROJECT}" -var "gcp_region=${REGION}"
  assert_create_only_plan "$PLAN_FILE"
  write_attestation "$PLAN_FILE"
else
  verify_attestation "$PLAN_FILE"
  terraform apply "$PLAN_FILE"
fi
