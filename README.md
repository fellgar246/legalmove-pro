# LegalMove Pro

AI-assisted contract amendment review: compare an original agreement with an amendment and surface structured changes, risks, and human-review recommendations.

## Stack

| Component | Path | Role |
|-----------|------|------|
| Go API | `apps/api-go` | Upload documents, create analysis jobs, serve results |
| Python Worker | `apps/worker-ai` | Poll queue, materialize documents, run AI pipeline |
| Next.js Frontend | `apps/web` | Upload UI, job polling, result view |

PostgreSQL is the **source of truth** for jobs, documents, results, and statuses. Cloud storage and queues are optional extensions (local defaults below; Azure planned for deployment).

## Quick start (local)

```bash
# 1. Environment
cp .env.example .env

# 2. PostgreSQL
docker compose up -d
docker exec -i legalmove-postgres psql -U legalmove -d legalmove \
  < apps/api-go/migrations/000001_init.up.sql
docker exec -i legalmove-postgres psql -U legalmove -d legalmove \
  < apps/api-go/migrations/000002_detected_changes_granular.up.sql
docker exec -i legalmove-postgres psql -U legalmove -d legalmove \
  < apps/api-go/migrations/000003_document_storage_provider.up.sql

# 3. API
mkdir -p apps/api-go/uploads
cd apps/api-go && go run ./cmd/server

# 4. Worker (separate terminal)
cd apps/worker-ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python src/main.py

# 5. Frontend (separate terminal)
cd apps/web && npm install && npm run dev
```

Open http://localhost:3000. API health: `curl -s http://localhost:8080/health`.

### Local defaults

```env
STORAGE_PROVIDER=local
QUEUE_PROVIDER=postgres
UPLOADS_DIR=./uploads
WORKER_USE_MOCK_RESULT=false   # set true to skip OpenAI during worker QA
```

## Cloud-ready (legacy AWS: S3 + SQS)

Requires AWS dev resources and matching credentials. **New deployments target Azure** — see [Milestone 4.A](docs/milestone-4.a-azure-migration.md).

**API:**

```env
STORAGE_PROVIDER=s3
QUEUE_PROVIDER=sqs
AWS_REGION=us-east-1
S3_BUCKET=your-bucket
S3_PREFIX=dev
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/ACCOUNT/queue-name
```

**Worker:**

```env
QUEUE_PROVIDER=sqs
AWS_REGION=us-east-1
S3_BUCKET=your-bucket
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/ACCOUNT/queue-name
DOCUMENT_TEMP_DIR=./tmp/documents
```

`QUEUE_PROVIDER` must match between API and worker.

## Tests

```bash
# API
cd apps/api-go && go test ./... -count=1

# Worker
cd apps/worker-ai && PYTHONPATH=src .venv/bin/python -m pytest -q

# Frontend (no npm test script)
cd apps/web && npm run lint && npm run build
```

## Cloud infrastructure (Terraform)

**Active provider: Azure** (Block 4.B foundation ready). AWS work from Blocks 4.1–4.3 is archived under `infra/terraform/aws/`.

```bash
az login
az account set --subscription "<subscription-id>"

cd infra/terraform/azure/environments/dev
terraform init && terraform validate && terraform plan
```

See [Milestone 4.B — Azure foundation](docs/milestone-4.b-azure-foundation.md) and [Milestone 4.A — migration plan](docs/milestone-4.a-azure-migration.md).

Archived AWS docs: [4.1](docs/milestone-4.1-terraform-foundation.md), [4.2](docs/milestone-4.2-rds-networking.md), [4.3](docs/milestone-4.3-ecs-task-definitions.md).

## Documentation

- [Milestone 2.3 — PDF native + S3/SQS](docs/milestone-2.3-pdf-native.md) — full architecture and block history
- [Milestone 3 — Frontend MVP](docs/milestone-3-frontend-mvp.md) — UI flows and local setup
- [Milestone 4.C — Azure PostgreSQL + networking](docs/milestone-4.c-azure-postgres-networking.md) — VNet, private PostgreSQL, DATABASE-URL (Block 4.C)
- [Milestone 4.B — Azure Terraform foundation](docs/milestone-4.b-azure-foundation.md) — ACR, Blob, Service Bus, Key Vault (Block 4.B)
- [Milestone 4.A — Azure migration plan](docs/milestone-4.a-azure-migration.md) — cloud roadmap
- [Milestone 4.1–4.3 — AWS Terraform](docs/milestone-4.1-terraform-foundation.md) — archived reference

## Milestone status

Milestone 2.3 (Blocks 1–8) is **complete** for local and cloud-ready paths:

- PDF native parsing (worker)
- PDF + image upload (frontend)
- Local and S3 storage (API)
- S3 document materialization (worker)
- Postgres and SQS job queues
- PostgreSQL remains source of truth

**In progress:** Milestone 4 — Azure deployment.

- Block 4.A (AWS → Azure reorientation): architecture, archive AWS Terraform, roadmap — **done**
- Block 4.B (Terraform Azure foundation): RG, ACR, Blob, Service Bus, Key Vault, managed identities — **done**
- Block 4.C (PostgreSQL + networking): VNet, private PostgreSQL, `DATABASE-URL` in Key Vault — **done**
- Block 4.D (next): Container Apps Environment + VNet integration
- Blocks 4.E–4.H: Container Apps services, app adapters, CI/CD

Archived AWS blocks (reference only): 4.1 (ECR/S3/SQS), 4.2 (VPC/RDS), 4.3 (ECS task defs). Dockerfiles remain reusable for Azure Container Apps.
