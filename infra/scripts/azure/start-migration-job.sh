#!/usr/bin/env bash
# Starts the Azure Container Apps migration job (Block 4.G).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="${TF_DIR:-${SCRIPT_DIR}/../../terraform/azure/environments/dev}"

cd "$TF_DIR"

JOB_NAME="$(terraform output -raw migration_job_name)"
RESOURCE_GROUP="$(terraform output -raw resource_group_name)"

if [[ -z "$JOB_NAME" || "$JOB_NAME" == "null" ]]; then
  echo "ERROR: migration_job_name output is empty. Set create_migration_job=true and apply Terraform." >&2
  exit 1
fi

echo "Starting migration job: ${JOB_NAME} (resource group: ${RESOURCE_GROUP})"
az containerapp job start \
  --name "$JOB_NAME" \
  --resource-group "$RESOURCE_GROUP"

echo
echo "Check execution status:"
echo "  az containerapp job execution list --name ${JOB_NAME} --resource-group ${RESOURCE_GROUP} -o table"
echo
echo "Tail job logs (replace EXECUTION_NAME from the list above):"
echo "  az containerapp job logs show --name ${JOB_NAME} --resource-group ${RESOURCE_GROUP} --execution EXECUTION_NAME --follow"
