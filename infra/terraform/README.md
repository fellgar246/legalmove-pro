# Terraform — LegalMove Pro

Infrastructure as code for cloud deployment. **Azure is the active cloud provider** (Milestone 4, from Block 4.A onward).

## Layout

```text
infra/terraform/
├── aws/     # Archived AWS work (Blocks 4.1–4.3) — deprecated, reference only
└── azure/   # Active Azure infrastructure (starting Block 4.B)
```

## Active path: Azure

See [infra/terraform/azure/README.md](./azure/README.md), [Milestone 4.B — Azure foundation](../../docs/milestone-4.b-azure-foundation.md), and [Milestone 4.A — migration plan](../../docs/milestone-4.a-azure-migration.md).

```bash
az login
az account set --subscription "<subscription-id>"

cd infra/terraform/azure/environments/dev
terraform init
terraform fmt -recursive ../..
terraform validate
terraform plan
```

## Archived path: AWS

The AWS foundation (ECR, S3, SQS, VPC, RDS, ECS task definitions) lives under `infra/terraform/aws/`. It is **not deleted** but **not the deployment target**.

See [infra/terraform/aws/README.md](./aws/README.md) for historical operator notes.

## Local development

Local mode does **not** use Terraform. Defaults remain:

```env
STORAGE_PROVIDER=local
QUEUE_PROVIDER=postgres
UPLOADS_DIR=./uploads
```

## Documentation

| Doc | Status |
|-----|--------|
| [Milestone 4.B — Azure foundation](../../docs/milestone-4.b-azure-foundation.md) | **Active — Block 4.B** |
| [Milestone 4.A — Azure migration](../../docs/milestone-4.a-azure-migration.md) | Roadmap |
| [Milestone 4.1–4.3 — AWS blocks](../../docs/milestone-4.1-terraform-foundation.md) | Archived reference |
