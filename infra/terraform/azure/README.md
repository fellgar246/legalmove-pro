# Terraform — Azure (active)

> **Status: Block 4.D complete.** Shared Azure foundation, private PostgreSQL, and Container Apps Environment for dev/staging. Container Apps (API/Worker) come in Block 4.E.

## Layout

```text
infra/terraform/azure/
├── modules/
│   ├── resource_group/
│   ├── acr/
│   ├── blob_documents/
│   ├── service_bus_analysis/
│   ├── key_vault/
│   ├── managed_identities/
│   ├── networking/                  # Block 4.C (+ subnet delegation in 4.D)
│   ├── postgres_flexible/           # Block 4.C
│   └── container_apps_environment/  # Block 4.D
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

- Resource group, ACR, Blob Storage, Service Bus, Key Vault, managed identities

## Block 4.C scope

- VNet (`10.30.0.0/16`) with PostgreSQL delegated subnet + Container Apps subnet (`/23`)
- Private DNS zone for PostgreSQL private link
- PostgreSQL Flexible Server (private, `B_Standard_B1ms` dev SKU)
- Database `legalmove`
- Key Vault secret `DATABASE-URL` (password in state/KV only — not output)

## Block 4.D scope

- Log Analytics workspace (30-day retention default)
- Container Apps Environment (`cae-legalmove-pro-dev`) on `snet-container-apps`
- Consumption workload profile for VNet integration
- `AcrPull` on ACR for API and worker managed identities
- Subnet delegation `Microsoft.App/environments` on existing Container Apps subnet

**Not yet:** Container Apps (API/Worker), migration runner, app adapters, bastion/VPN.

## Prerequisites

- Terraform `>= 1.5`, Docker
- Azure CLI: `az login` and subscription selected
- IAM: Contributor on subscription or target RG; `User Access Administrator` for RBAC; `Key Vault Secrets Officer` to create `DATABASE-URL`

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

## Validate Container Apps Environment (after apply)

```bash
az containerapp env show \
  --name $(terraform output -raw container_apps_environment_name) \
  --resource-group $(terraform output -raw resource_group_name)
```

## Read DATABASE-URL

Created automatically by Block 4.C. Requires Key Vault read access:

```bash
az keyvault secret show \
  --vault-name $(terraform output -raw key_vault_name) \
  --name DATABASE-URL \
  --query value -o tsv
```

**Note:** PostgreSQL is private — this URL is only reachable from inside the VNet (e.g. future Container Apps). Local dev still uses Docker Compose PostgreSQL.

## Manual OPENAI-API-KEY

```bash
az keyvault secret set \
  --vault-name $(terraform output -raw key_vault_name) \
  --name OPENAI-API-KEY \
  --value "<secret>"
```

## Destroy dev resources

```bash
cd infra/terraform/azure/environments/dev
terraform destroy
```

PostgreSQL Flexible Server and Container Apps Environment may take several minutes to delete. Key Vault soft-deleted vaults may require manual purge.

## Push images to ACR (after Block 4.B apply)

```bash
ACR=$(terraform output -raw acr_login_server)
az acr login --name $(terraform output -raw acr_name)

docker build -f apps/api-go/Dockerfile -t "$ACR/api-go:latest" apps/api-go
docker push "$ACR/api-go:latest"

docker build -f apps/worker-ai/Dockerfile -t "$ACR/worker-ai:latest" apps/worker-ai
docker push "$ACR/worker-ai:latest"
```

## Application env mapping (future — Block 4.F)

| Variable | Source |
|----------|--------|
| `STORAGE_PROVIDER=azure_blob` | Container Apps env |
| `QUEUE_PROVIDER=azure_service_bus` | Container Apps env |
| `DATABASE_URL` | Key Vault secret `DATABASE-URL` |
| `OPENAI_API_KEY` | Key Vault secret `OPENAI-API-KEY` |
| `AZURE_STORAGE_ACCOUNT_NAME` | `terraform output storage_account_name` |
| `AZURE_STORAGE_CONTAINER_NAME` | `terraform output documents_container_name` |
| `AZURE_SERVICE_BUS_NAMESPACE` | `terraform output servicebus_namespace_name` |
| `AZURE_SERVICE_BUS_QUEUE_NAME` | `terraform output servicebus_queue_name` |
| `AZURE_KEY_VAULT_NAME` | `terraform output key_vault_name` |
| `AZURE_CLIENT_ID` | `terraform output api_managed_identity_client_id` / worker |

## Documentation

- [Milestone 4.D — Container Apps Environment](../../docs/milestone-4.d-container-apps-environment.md)
- [Milestone 4.C — PostgreSQL + networking](../../docs/milestone-4.c-azure-postgres-networking.md)
- [Milestone 4.B — Azure Terraform foundation](../../docs/milestone-4.b-azure-foundation.md)
- [Milestone 4.A — Azure migration plan](../../docs/milestone-4.a-azure-migration.md)

## State

Dev uses local state. Do not commit `terraform.tfstate` or `.terraform/`. Commit `.terraform.lock.hcl`.
