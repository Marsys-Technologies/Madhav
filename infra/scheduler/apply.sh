#!/usr/bin/env bash
# MARSYS-JIS Platform Modernization — Wave 4 unit 4.edge_and_infra_hygiene.
# Idempotent apply for Cloud Scheduler IaC. DO NOT run from a worktree.

set -euo pipefail
CMD="${1:-plan}"
PROJECT="${TF_VAR_gcp_project:-madhav-astrology}"
REGION="${TF_VAR_gcp_region:-asia-south1}"
STATE_BUCKET="${TF_STATE_BUCKET:-${PROJECT}-tf-state}"
STATE_PREFIX="scheduler/amjis"

command -v terraform >/dev/null 2>&1 || { echo "terraform CLI not on PATH" >&2; exit 1; }

terraform init \
  -backend-config="bucket=${STATE_BUCKET}" \
  -backend-config="prefix=${STATE_PREFIX}"

case "$CMD" in
  plan)    terraform plan -var "gcp_project=${PROJECT}" -var "gcp_region=${REGION}" ;;
  apply)   terraform apply -auto-approve -var "gcp_project=${PROJECT}" -var "gcp_region=${REGION}" ;;
  destroy) terraform destroy -auto-approve -var "gcp_project=${PROJECT}" -var "gcp_region=${REGION}" ;;
  *) echo "usage: $0 {plan|apply|destroy}" >&2; exit 2 ;;
esac
