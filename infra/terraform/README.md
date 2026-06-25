# Terraform — LegalMove Pro

Infrastructure as code for AWS deployment. Milestone 4 is delivered in small, verifiable blocks.

## Layout

```text
infra/terraform/
├── modules/
│   ├── ecr/                   # Container registries (api-go, worker-ai)
│   ├── s3_documents/          # Private documents bucket
│   ├── sqs_analysis/            # Analysis jobs queue + DLQ
│   └── iam_service_policies/  # Standalone IAM policies for future ECS roles
└── environments/
    └── dev/                   # Preliminary dev/staging foundation
```

## Block 4.1 scope

Creates shared AWS foundation resources only:

- ECR repositories for API and worker
- Private S3 bucket for documents
- SQS main queue + DLQ with redrive policy
- Minimal IAM policies (not yet attached to ECS task roles)

Does **not** create ECS, RDS, ALB, CloudFront, CI/CD, or frontend hosting.

## Prerequisites

- Terraform `>= 1.5`
- AWS CLI configured (`aws configure` or ambient credentials)
- IAM permissions to manage ECR, S3, SQS, and IAM policies in the target account/region

## Commands (dev environment)

```bash
cd infra/terraform/environments/dev

terraform init
terraform fmt -recursive ../../..
terraform validate
terraform plan
# terraform apply   # when ready to provision real AWS resources
```

After apply:

```bash
terraform output
```

## Mapping outputs to application env

| Terraform output | API env | Worker env |
|------------------|---------|------------|
| `aws_region` | `AWS_REGION` | `AWS_REGION` |
| `documents_bucket_name` | `S3_BUCKET` | `S3_BUCKET` |
| `s3_object_prefix` | `S3_PREFIX` | `S3_PREFIX` |
| `analysis_queue_url` | `SQS_QUEUE_URL` | `SQS_QUEUE_URL` |

Cloud runtime (future ECS block):

```env
STORAGE_PROVIDER=s3
QUEUE_PROVIDER=sqs
```

Local development remains unchanged with `STORAGE_PROVIDER=local` and `QUEUE_PROVIDER=postgres`.

## Documentation

- [Milestone 4.1 — Terraform AWS foundation](../../docs/milestone-4.1-terraform-foundation.md)

## State

Dev uses local state (`terraform.tfstate` in the environment directory). Do not commit state files. Remote state can be introduced in a later block before shared staging/prod.
