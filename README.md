# LegalMove Pro

AI-assisted contract amendment review: compare an original agreement with an amendment and surface structured changes, risks, and human-review recommendations.

## Stack

| Component | Path | Role |
|-----------|------|------|
| Go API | `apps/api-go` | Upload documents, create analysis jobs, serve results |
| Python Worker | `apps/worker-ai` | Poll queue, materialize documents, run AI pipeline |
| Next.js Frontend | `apps/web` | Upload UI, job polling, result view |

PostgreSQL is the **source of truth** for jobs, documents, results, and statuses. S3 and SQS are optional cloud-ready extensions.

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

## Cloud-ready (S3 + SQS)

Requires AWS dev resources (S3 bucket, SQS queue) and matching credentials.

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

## AWS foundation (Terraform)

Shared dev resources (ECR, S3, SQS, IAM policies) are defined under `infra/terraform/`.

```bash
cd infra/terraform/environments/dev
terraform init
terraform fmt -recursive ../../..
terraform validate
terraform plan
```

See [Milestone 4.1 — Terraform AWS foundation](docs/milestone-4.1-terraform-foundation.md) for variables, outputs, and env mapping.

## Documentation

- [Milestone 2.3 — PDF native + S3/SQS](docs/milestone-2.3-pdf-native.md) — full architecture and block history
- [Milestone 3 — Frontend MVP](docs/milestone-3-frontend-mvp.md) — UI flows and local setup
- [Milestone 4.1 — Terraform AWS foundation](docs/milestone-4.1-terraform-foundation.md) — ECR, S3, SQS, IAM (Block 4.1)

## Milestone status

Milestone 2.3 (Blocks 1–8) is **complete** for local and cloud-ready paths:

- PDF native parsing (worker)
- PDF + image upload (frontend)
- Local and S3 storage (API)
- S3 document materialization (worker)
- Postgres and SQS job queues
- PostgreSQL remains source of truth

**In progress:** Milestone 4 — AWS deployment preliminar.

- Block 4.1 (Terraform foundation): ECR, S3, SQS, IAM policies — see `infra/terraform/`
- Next blocks: RDS (4.2), ECS (4.3+), CI/CD, frontend hosting
