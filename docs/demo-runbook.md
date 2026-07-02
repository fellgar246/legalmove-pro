# Demo runbook

Operator-facing runbook for the public LegalMove Pro demo. For the architecture behind these
resources, see [`docs/architecture-azure.md`](architecture-azure.md). For the original
provisioning/QA evidence, see [Milestone 5.3](milestone-5.3-public-demo-qa.md).

## Live demo walkthrough

1. Open the public frontend: `https://witty-bush-05c2c6e10.7.azurestaticapps.net`
   (re-derive with `terraform output -raw frontend_static_web_app_url`).
2. Go to **New Analysis** → upload an **ORIGINAL** contract PDF and its **AMENDMENT** PDF.
   Sample pair: `apps/worker-ai/data/test_contracts/pair1_{original,amendment}.pdf`
   (regenerate with `python apps/worker-ai/scripts/generate_test_pdf.py` if needed).
3. Submit → redirected to the detail page, which polls `GET /analyses/{id}` every 3s until
   `COMPLETED` (or `FAILED` / `NEEDS_REVIEW`).
4. Review, in order:
   - **Executive summary** + overall risk level
   - **Risk summary / risk badges** (per-change `LOW`/`MEDIUM`/`HIGH`)
   - **Changes table** (before/after text, section reference, evidence)
   - **Validation warnings** (if any)
   - **Human review recommendations**
   - **Raw JSON** toggle — the full `FinalAnalysisReport` v1 payload
   - **Legal disclaimer**: "AI-generated review support. Not legal advice. All outputs should
     be reviewed by a qualified human."

> The public demo runs the worker in **mock mode** — the result is a schema-complete but
> synthetic report, not a real AI analysis. See [Demo mode](../README.md#demo-mode-mock-vs-real-openai).

## Pre-demo checklist

- [ ] `curl -s <API_URL>/health` → `{"status":"ok","service":"legalmove-api"}`
- [ ] Frontend `/`, `/analyses`, `/analyses/new` all return 200
- [ ] `az containerapp revision list --name ca-worker-legalmove-pro-dev -g rg-legalmove-pro-dev -o table` → worker revision `Running`
- [ ] Service Bus queue is drained: `activeMessageCount: 0`, `deadLetterMessageCount: 0`
- [ ] Legal disclaimer renders on the analysis detail page

## Operate the demo

### Mock mode vs real OpenAI mode

Controlled by `WORKER_USE_MOCK_RESULT` (worker env) / `worker_use_mock_result` (Terraform var,
`apps/worker-ai/src/config.py` reads it).

```bash
cd infra/terraform/azure/environments/dev
# terraform.tfvars
worker_use_mock_result = false   # switch to real OpenAI analyses
```

Real mode requires the `OPENAI-API-KEY` Key Vault secret:

```bash
az keyvault secret set \
  --vault-name $(terraform output -raw key_vault_name) \
  --name OPENAI-API-KEY \
  --value "<secret>"
```

Then `terraform apply` to roll the worker with the updated env var. Switch back to
`worker_use_mock_result = true` to avoid OpenAI spend once done.

### Rebuild / push the API image

```bash
cd infra/terraform/azure/environments/dev
ACR_NAME=$(terraform output -raw acr_name)
ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server)
az acr login --name "$ACR_NAME"

docker build --platform linux/amd64 -f ../../../../apps/api-go/Dockerfile \
  -t "$ACR_LOGIN_SERVER/api-go:latest" ../../../../apps/api-go
docker push "$ACR_LOGIN_SERVER/api-go:latest"

# Force a new revision (the :latest tag alone won't trigger one):
az containerapp update --name ca-api-legalmove-pro-dev -g rg-legalmove-pro-dev \
  --image "$ACR_LOGIN_SERVER/api-go:latest" --revision-suffix "manual$(date +%Y%m%d)"
```

Same pattern for the worker with `worker-ai:latest` and `ca-worker-legalmove-pro-dev`.

> **Note:** any code change that isn't rebuilt/pushed and rolled will not take effect —
> this was the root cause of the CORS bug documented in
> [Milestone 5.3 § Fixes applied](milestone-5.3-public-demo-qa.md#fixes-applied).

### Deploy the frontend

**Canonical path — GitHub Actions** (`.github/workflows/azure-static-web-apps.yml`, triggers on
push to `main` touching `apps/web/**`, or manually via `workflow_dispatch`). One-time setup:

1. **Secret** `AZURE_STATIC_WEB_APPS_API_TOKEN` — GitHub → Settings → Secrets and variables →
   Actions → New repository secret. Value:
   ```bash
   az staticwebapp secrets list \
     --name $(terraform output -raw frontend_static_web_app_name) \
     --query "properties.apiKey" -o tsv
   ```
2. **Variable** `NEXT_PUBLIC_API_BASE_URL` — same location, "Variables" tab. Value:
   `terraform output -raw api_container_app_url`.
3. Push to `main` (or run **Actions → Deploy – Azure Static Web Apps → Run workflow**).
4. Check the **Actions** tab for the run status.

**Manual fallback:**

```bash
cd apps/web
NEXT_PUBLIC_API_BASE_URL=$(cd ../../infra/terraform/azure/environments/dev && terraform output -raw api_container_app_url) \
  npm run build
npx @azure/static-web-apps-cli deploy ./out --deployment-token <token> --env production
```

### Run migrations

```bash
cd infra/terraform/azure/environments/dev
ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server)
docker build --platform linux/amd64 -f ../../../../apps/api-go/Dockerfile.migrations \
  -t "$ACR_LOGIN_SERVER/legalmove-migrations:latest" ../../../../apps/api-go
docker push "$ACR_LOGIN_SERVER/legalmove-migrations:latest"

./infra/scripts/azure/start-migration-job.sh
# or:
az containerapp job start \
  --name "$(terraform output -raw migration_job_name)" \
  --resource-group "$(terraform output -raw resource_group_name)"
```

Verify:

```bash
az containerapp job execution list --name "$(terraform output -raw migration_job_name)" \
  --resource-group "$(terraform output -raw resource_group_name)" -o table
az containerapp job logs show --name "$(terraform output -raw migration_job_name)" \
  --resource-group "$(terraform output -raw resource_group_name)" --execution <EXECUTION_NAME> --follow
```

### Check Azure logs

```bash
RG=$(terraform output -raw resource_group_name)
az containerapp logs show --name $(terraform output -raw api_container_app_name) -g "$RG" --tail 200
az containerapp logs show --name $(terraform output -raw worker_container_app_name) -g "$RG" --tail 200
```

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| **CORS error** on public frontend | API origin not allowed, or the deployed image predates the multi-origin CORS middleware (`internal/httpserver/cors.go`). Verify the `OPTIONS` preflight **echoes the requesting origin** — if it returns a fixed/different origin, rebuild + push `api-go:latest` and roll with a unique `--revision-suffix`. |
| **Static fallback fails** (deep-route hard refresh 404s) | Check `apps/web/public/staticwebapp.config.json` → `navigationFallback.rewrite: /index.html` and its `exclude` globs; confirm it's present in `out/` after build. |
| **API 5xx** | `az containerapp logs show` on the API app; check `DATABASE_URL` Key Vault reference and that the migration job has run against the current schema. |
| **Worker not consuming** | Check the worker revision is `Running` (`az containerapp revision list`); worker logs should show `claimed job`. Verify Service Bus managed-identity role assignments (Data Sender/Receiver). |
| **Service Bus messages stuck** (`activeMessageCount > 0`) | Worker down or erroring — inspect worker logs and the dead-letter subqueue (`analysis-jobs/$deadletterqueue`). |
| **Blob RBAC issues for operator** | The Azure CLI operator identity typically lacks data-plane Blob RBAC. Use `--account-key $(az storage account keys list ...)` for read-only listing, or grant `Storage Blob Data Reader`. |
| **Migration job failed** | `az containerapp job execution list` to find the execution, then `logs show --execution <name>`. Common cause: stale `DATABASE_URL` secret or a migration already applied (check `schema_migrations` table). |
| **GitHub Actions deploy failed** | Confirm `AZURE_STATIC_WEB_APPS_API_TOKEN` secret and `NEXT_PUBLIC_API_BASE_URL` variable exist and are correctly scoped to the repo; re-run via `workflow_dispatch`. Fallback to the manual `swa-cli` deploy above. |
| **OpenAI key missing** | Only relevant in real mode. Set `worker_use_mock_result = true` to keep demoing without a key, or set the `OPENAI-API-KEY` Key Vault secret and re-apply. |

## Related docs

- [`docs/architecture-azure.md`](architecture-azure.md)
- [Milestone 5.4 — Demo package](milestone-5.4-demo-package.md)
- [Milestone 5.3 — Public demo QA](milestone-5.3-public-demo-qa.md)
- [`infra/terraform/azure/README.md`](../infra/terraform/azure/README.md)
