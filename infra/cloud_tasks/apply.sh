#!/usr/bin/env bash
# MARSYS-JIS Platform Modernization — Wave 4 unit 4.build_trigger
#
# Idempotent apply script for the `amjis-build-queue` Cloud Tasks IaC.
# Mirrors infra/memorystore/apply.sh. DO NOT run from a feature/Conductor
# worktree — state must be shared with main.
#
# Usage:
#   cd infra/cloud_tasks
#   ./apply.sh plan
#   ./apply.sh apply
#   ./apply.sh destroy

set -euo pipefail

CMD="${1:-plan}"
PROJECT="${TF_VAR_gcp_project:-madhav-astrology}"
REGION="${TF_VAR_gcp_region:-asia-south1}"
STATE_BUCKET="${TF_STATE_BUCKET:-${PROJECT}-tf-state}"
STATE_PREFIX="cloud_tasks/amjis-build-queue"

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
    echo "BUILD_TASK_QUEUE=$(terraform output -raw queue_name)"
    echo "BUILD_TASK_QUEUE_LOCATION=$(terraform output -raw queue_location)"
    echo "BUILD_TASK_INVOKER_SA=$(terraform output -raw task_invoker_sa_email)"
    echo "BUILD_TASK_AUDIENCE=$(terraform output -raw task_handler_audience)"
    echo
    echo "Wire these into .github/workflows/deploy.yml env_vars: then redeploy."
    ;;
  destroy)
    terraform destroy -auto-approve -var "gcp_project=${PROJECT}" -var "gcp_region=${REGION}"
    ;;
  *)
    echo "usage: $0 {plan|apply|destroy}" >&2
    exit 2
    ;;
esac
