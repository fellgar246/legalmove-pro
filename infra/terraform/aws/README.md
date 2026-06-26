# Terraform — AWS (archived)

> **Status: deprecated.** LegalMove Pro migrated its cloud target from AWS to Azure in Milestone 4, Block 4.A. This tree is preserved for reference and to avoid losing Blocks 4.1–4.3 work. Do **not** extend it for new features.

## What this contains

Historical AWS foundation delivered in Blocks 4.1–4.3:

| Block | Scope |
|-------|-------|
| 4.1 | ECR, S3 documents bucket, SQS + DLQ, IAM service policies |
| 4.2 | VPC, subnets, security groups, RDS PostgreSQL, Secrets Manager |
| 4.3 | ECS cluster, CloudWatch log groups, execution/task roles, Fargate task definitions |

**Not implemented:** ECS services, ALB, CI/CD (planned Block 4.4+ on AWS — cancelled).

## Layout

```text
infra/terraform/aws/
├── modules/
│   ├── ecr/
│   ├── s3_documents/
│   ├── sqs_analysis/
│   ├── iam_service_policies/
│   ├── networking/
│   ├── rds_postgres/
│   └── ecs_base/
└── environments/
    └── dev/
```

## Operator commands (historical)

```bash
cd infra/terraform/aws/environments/dev

terraform init
terraform fmt -recursive ../../..
terraform validate
terraform plan
# terraform apply  — only if you still need to tear down or inspect existing AWS resources
```

## Prerequisites (historical)

- Terraform `>= 1.5`, Docker, AWS CLI
- IAM permissions for ECR, S3, SQS, IAM, EC2/VPC, RDS, Secrets Manager, ECS, CloudWatch Logs

## Docker build (still valid for Azure)

Production Dockerfiles are cloud-agnostic and live in the application repos:

```bash
docker build -f apps/api-go/Dockerfile -t legalmove-api-go:local apps/api-go
docker build -f apps/worker-ai/Dockerfile -t legalmove-worker-ai:local apps/worker-ai
```

Images built locally can be pushed to **Azure Container Registry** in later blocks.

## Documentation

- [Milestone 4.1 — Terraform AWS foundation](../../docs/milestone-4.1-terraform-foundation.md) *(archived)*
- [Milestone 4.2 — RDS + networking](../../docs/milestone-4.2-rds-networking.md) *(archived)*
- [Milestone 4.3 — ECS task definitions](../../docs/milestone-4.3-ecs-task-definitions.md) *(archived)*
- [Milestone 4.A — Azure migration plan](../../docs/milestone-4.a-azure-migration.md) *(active)*

## State

Dev used local state. Do not commit `terraform.tfstate` or `.terraform/`.
