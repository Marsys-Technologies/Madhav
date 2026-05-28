#!/usr/bin/env bash
# MARSYS-JIS Platform Modernization — Wave 4 unit 4.memorystore_caching
#
# Idempotent apply script for the Memorystore Redis IaC. Intended to be
# invoked by the zero-touch deploy pipeline (or manually by the operator)
# once IaC is on main. DO NOT run from a feature/Conductor worktree —
# state must be shared with main.
#
# Usage:
#   cd infra/memorystore
#   ./apply.sh plan    # show diff
#   ./apply.sh apply   # apply (requires gcloud auth + terraform-state bucket)

set -euo pipefail

CMD="${1:-plan}"
PROJECT="${TF_VAR_gcp_project:-madhav-astrology}"
REGION="${TF_VAR_gcp_region:-asia-south1}"
STATE_BUCKET="${TF_STATE_BUCKET:-${PROJECT}-tf-state}"
STATE_PREFIX="memorystore/amjis-cache"

if ! command -v terraform >/dev/null 2>&1; then
  echo "terraform CLI not on PATH" >&2
  exit 1
fi

terraform init \
  -backend-config="bucket=${STATE_BUCKET}" \
  -backend-config="prefix=${STATE_PREFIX}"

case "$CMD" in
  plan)
    terraform plan -var "gcp_project=${PROJECT}" -var "gcp_region=${REGION}"
    ;;
  apply)
    terraform apply -auto-approve -var "gcp_project=${PROJECT}" -var "gcp_region=${REGION}"
    echo
    echo "REDIS_HOST=$(terraform output -raw redis_host)"
    echo "REDIS_PORT=$(terraform output -raw redis_port)"
    echo
    echo "Wire these into .github/workflows/deploy.yml env_vars: section then redeploy."
    ;;
  destroy)
    terraform destroy -auto-approve -var "gcp_project=${PROJECT}" -var "gcp_region=${REGION}"
    ;;
  *)
    echo "usage: $0 {plan|apply|destroy}" >&2
    exit 2
    ;;
esac
