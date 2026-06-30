# Terraform — Azure (active)

> **Status: Milestone 5 in progress (Blocks 5.1–5.3 done).** Shared Azure foundation, private PostgreSQL, Container Apps Environment, API/Worker Container Apps, migration job, E2E QA (Milestone 4 closed); Azure Static Web App **provisioned and deployed** with CORS allowing the public host, full public-demo QA complete (Block 5.3). Live frontend: `https://witty-bush-05c2c6e10.7.azurestaticapps.net`.

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
│   ├── container_apps_environment/  # Block 4.D
│   ├── container_apps/              # Block 4.F + migration job (4.G)
│   └── static_web_app/              # Block 5.1 — frontend public demo
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

## Block 4.F scope

- Container App API (`ca-api-legalmove-pro-dev`) — external ingress, port 8080, `/health`
- Container App Worker (`ca-worker-legalmove-pro-dev`) — no ingress
- ACR images with managed-identity pull
- Key Vault secret refs for `DATABASE_URL` (+ optional `OPENAI_API_KEY`)
- Cloud env vars for `azure_blob` / `azure_service_bus`

## Block 4.G scope

- Container Apps Job (`caj-migrate-legalmove-pro-dev`) — manual trigger, no schedule
- ACR image `legalmove-migrations:latest` (`psql` + SQL files)
- Key Vault secret ref `DATABASE-URL` via API managed identity
- Applies migrations `000001`–`000004` with `schema_migrations` ledger

## Block 5.1 scope

- `modules/static_web_app/` — single `azurerm_static_web_app` resource (Free SKU default, `centralus`)
- Gated in `environments/dev` via `create_frontend_static_web_app` (default `true`)
- Outputs: `frontend_static_web_app_name`, `frontend_static_web_app_id`, `frontend_static_web_app_default_hostname`, `frontend_static_web_app_url`
- Deployment token (`api_key`) is in Terraform state but **not surfaced as an output** — fetch at deploy time: `az staticwebapp secrets list --name <name> --query "properties.apiKey" -o tsv`
- CORS: after `terraform apply`, set `cors_allowed_origins = "http://localhost:3000,https://<swa-hostname>"` in `terraform.tfvars` and re-apply. Changing the env var creates a new API revision (no image rebuild for the env var itself). **Caveat (found in 5.3):** the running `api-go` image must contain the multi-origin CORS middleware (`internal/httpserver/cors.go`). If the `OPTIONS` preflight returns a fixed origin instead of echoing the requesting origin, the deployed image is stale — rebuild + push `api-go:latest` and roll the API with a unique `--revision-suffix`.

See [Milestone 5.1 — Azure Static Web Apps strategy](../../../docs/milestone-5.1-azure-static-web-apps-strategy.md) for the strategy and [Milestone 5.3 — Public demo QA](../../../docs/milestone-5.3-public-demo-qa.md) for the provisioning/deploy + QA runbook.

**Not yet:** custom domain, auth, full CI/CD, KEDA scaling. See [Milestone 4.H](../../../docs/milestone-4.h-cloud-e2e-closure.md) for Milestone 4 closure checklist.

## Prerequisites

- Terraform `>= 1.5`, Docker, Azure CLI
- `az login` and subscription selected
- IAM: Contributor + `User Access Administrator` for RBAC
- **Before Block 4.F apply:** push `api-go:latest` and `worker-ai:latest` to ACR
- **Before Block 4.G apply:** push `legalmove-migrations:latest` to ACR

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

## Push images (required before Container Apps apply)

```bash
cd infra/terraform/azure/environments/dev
ACR_NAME=$(terraform output -raw acr_name)
ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server)
az acr login --name "$ACR_NAME"

docker build --platform linux/amd64 -f ../../../../apps/api-go/Dockerfile \
  -t "$ACR_LOGIN_SERVER/api-go:latest" ../../../../apps/api-go
docker push "$ACR_LOGIN_SERVER/api-go:latest"

docker build --platform linux/amd64 -f ../../../../apps/worker-ai/Dockerfile \
  -t "$ACR_LOGIN_SERVER/worker-ai:latest" ../../../../apps/worker-ai
docker push "$ACR_LOGIN_SERVER/worker-ai:latest"

docker build --platform linux/amd64 -f ../../../../apps/api-go/Dockerfile.migrations \
  -t "$ACR_LOGIN_SERVER/legalmove-migrations:latest" ../../../../apps/api-go
docker push "$ACR_LOGIN_SERVER/legalmove-migrations:latest"
```

## Run SQL migrations (Block 4.G)

After `terraform apply`:

```bash
./infra/scripts/azure/start-migration-job.sh
```

Or:

```bash
az containerapp job start \
  --name "$(terraform output -raw migration_job_name)" \
  --resource-group "$(terraform output -raw resource_group_name)"
```

See [Milestone 4.G](../../docs/milestone-4.g-cloud-migrations-qa.md) for execution verification, schema checks, and E2E QA.

## Validate API (after migrations)

```bash
curl -sS "$(terraform output -raw api_container_app_url)/health"
curl -sS "$(terraform output -raw api_container_app_url)/analyses"
```

## Read DATABASE-URL

```bash
az keyvault secret show \
  --vault-name $(terraform output -raw key_vault_name) \
  --name DATABASE-URL \
  --query value -o tsv
```

PostgreSQL is private — reachable from Container Apps via VNet integration.

## Manual OPENAI-API-KEY

Required when `worker_use_mock_result = false`:

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

## Application env mapping (Container Apps — Block 4.F)

Configured automatically by Terraform. See [Milestone 4.F](../../docs/milestone-4.f-container-apps-deploy.md) for full list.

| Variable | Source |
|----------|--------|
| `STORAGE_PROVIDER=azure_blob` | API Container App env |
| `QUEUE_PROVIDER=azure_service_bus` | API + Worker env |
| `DATABASE_URL` | Key Vault secret `DATABASE-URL` |
| `OPENAI_API_KEY` | Key Vault secret `OPENAI-API-KEY` (worker, unless mock) |
| `CORS_ALLOWED_ORIGINS` | API Container App env (default `http://localhost:3000`) |
| `AZURE_CLIENT_ID` | Managed identity client ID outputs |

## Documentation

- [Milestone 5.3 — Public demo QA](../../../docs/milestone-5.3-public-demo-qa.md)
- [Milestone 5.2 — Frontend public deploy](../../../docs/milestone-5.2-frontend-public-deploy.md)
- [Milestone 5.1 — Azure Static Web Apps strategy](../../../docs/milestone-5.1-azure-static-web-apps-strategy.md)
- [Milestone 4.H — Cloud E2E closure](../../../docs/milestone-4.h-cloud-e2e-closure.md)
- [Milestone 4.G — Cloud migrations + QA](../../../docs/milestone-4.g-cloud-migrations-qa.md)
- [Milestone 4.F — Container Apps deploy](../../../docs/milestone-4.f-container-apps-deploy.md)
- [Milestone 4.E — Azure adapters](../../../docs/milestone-4.e-azure-adapters.md)
- [Milestone 4.D — Container Apps Environment](../../../docs/milestone-4.d-container-apps-environment.md)
- [Milestone 4.C — PostgreSQL + networking](../../../docs/milestone-4.c-azure-postgres-networking.md)
- [Milestone 4.B — Azure Terraform foundation](../../../docs/milestone-4.b-azure-foundation.md)
- [Milestone 4.A — Azure migration plan](../../../docs/milestone-4.a-azure-migration.md)

## State

Dev uses local state. Do not commit `terraform.tfstate` or `.terraform/`. Commit `.terraform.lock.hcl`.
