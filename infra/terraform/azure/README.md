# Terraform — Azure (active)

> **Status: Block 4.B complete.** Shared Azure foundation for dev/staging. Container Apps and PostgreSQL come in Blocks 4.C–4.E.

## Layout

```text
infra/terraform/azure/
├── modules/
│   ├── resource_group/
│   ├── acr/
│   ├── blob_documents/
│   ├── service_bus_analysis/
│   ├── key_vault/
│   └── managed_identities/
└── environments/
    └── dev/
        ├── main.tf
        ├── variables.tf
        ├── outputs.tf
        ├── providers.tf
        ├── versions.tf
        └── terraform.tfvars.example
```

## Block 4.B scope

- Resource group (`rg-legalmove-pro-dev` by default)
- Azure Container Registry (Basic SKU, admin disabled)
- Storage Account + private blob container (`documents`)
- Service Bus namespace (Standard) + analysis jobs queue with DLQ subqueue
- Key Vault (RBAC, soft delete, no secrets in Terraform)
- User-assigned managed identities + RBAC for API and worker

**Not in this block:** Container Apps, PostgreSQL, VNet, private endpoints, CI/CD, app adapters.

## Prerequisites

- Terraform `>= 1.5`, Docker
- Azure CLI: `az login` and subscription selected
- IAM: Contributor on subscription or target RG; `User Access Administrator` (or equivalent) to create RBAC role assignments

## Commands (dev)

```bash
az login
az account set --subscription "<subscription-id>"

cd infra/terraform/azure/environments/dev
cp terraform.tfvars.example terraform.tfvars   # optional overrides

terraform init
terraform fmt -recursive ../..
terraform validate
terraform plan
# terraform apply
```

## Destroy dev resources

```bash
cd infra/terraform/azure/environments/dev
terraform destroy
```

Key Vault soft-deleted vaults may remain until retention expires. With `purge_protection_enabled = false`, purge manually if needed:

```bash
az keyvault purge --name <key-vault-name>
```

## Push images to ACR (after apply)

```bash
ACR=$(terraform output -raw acr_login_server)
az acr login --name $(terraform output -raw acr_name)

docker build -f apps/api-go/Dockerfile -t "$ACR/api-go:latest" apps/api-go
docker build -f apps/worker-ai/Dockerfile -t "$ACR/worker-ai:latest" apps/worker-ai

docker push "$ACR/api-go:latest"
docker push "$ACR/worker-ai:latest"
```

## Manual secrets (after Key Vault exists)

Do **not** put real secrets in Terraform state. Create them with Azure CLI:

```bash
VAULT=$(terraform output -raw key_vault_name)

# After Block 4.C creates PostgreSQL:
# az keyvault secret set --vault-name "$VAULT" --name DATABASE-URL --value "postgres://..."

az keyvault secret set \
  --vault-name "$VAULT" \
  --name OPENAI-API-KEY \
  --value "<secret>"
```

Your deploying principal needs `Key Vault Secrets Officer` on the vault (RBAC).

## Application env mapping (future — Block 4.F)

| Variable | Source |
|----------|--------|
| `STORAGE_PROVIDER=azure_blob` | Container Apps env |
| `QUEUE_PROVIDER=azure_service_bus` | Container Apps env |
| `AZURE_STORAGE_ACCOUNT_NAME` | `terraform output storage_account_name` |
| `AZURE_STORAGE_CONTAINER_NAME` | `terraform output documents_container_name` |
| `AZURE_SERVICE_BUS_NAMESPACE` | `terraform output servicebus_namespace_name` |
| `AZURE_SERVICE_BUS_QUEUE_NAME` | `terraform output servicebus_queue_name` |
| `AZURE_KEY_VAULT_NAME` | `terraform output key_vault_name` |
| `AZURE_CLIENT_ID` | API/worker identity client ID outputs |
| `DATABASE_URL` | Key Vault secret `DATABASE-URL` |
| `OPENAI_API_KEY` | Key Vault secret `OPENAI-API-KEY` |

## Documentation

- [Milestone 4.B — Azure Terraform foundation](../../docs/milestone-4.b-azure-foundation.md)
- [Milestone 4.A — Azure migration plan](../../docs/milestone-4.a-azure-migration.md)

## State

Dev uses local state. Do not commit `terraform.tfstate` or `.terraform/`. Commit `.terraform.lock.hcl`.
