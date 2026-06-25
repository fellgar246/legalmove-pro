data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  documents_bucket_name = coalesce(
    var.s3_bucket_name,
    "${var.project_name}-${var.environment}-documents-${data.aws_caller_identity.current.account_id}",
  )

  api_ecr_repository_name    = "${var.project_name}-${var.environment}-api-go"
  worker_ecr_repository_name = "${var.project_name}-${var.environment}-worker-ai"
}

module "ecr" {
  source = "../../modules/ecr"

  api_repository_name    = local.api_ecr_repository_name
  worker_repository_name = local.worker_ecr_repository_name
  image_tag_mutability   = var.ecr_image_tag_mutability
  max_image_count        = var.ecr_max_image_count
  tags                   = local.common_tags
}

module "s3_documents" {
  source = "../../modules/s3_documents"

  bucket_name           = local.documents_bucket_name
  enable_versioning     = var.s3_enable_versioning
  lifecycle_expire_days = var.s3_lifecycle_expire_days
  tags                  = local.common_tags
}

module "sqs_analysis" {
  source = "../../modules/sqs_analysis"

  project_name               = var.project_name
  environment                = var.environment
  visibility_timeout_seconds = var.sqs_visibility_timeout_seconds
  message_retention_seconds  = var.sqs_message_retention_seconds
  receive_wait_time_seconds  = var.sqs_receive_wait_time_seconds
  max_receive_count          = var.sqs_max_receive_count
  tags                       = local.common_tags
}

module "iam_service_policies" {
  source = "../../modules/iam_service_policies"

  project_name          = var.project_name
  environment           = var.environment
  documents_bucket_arn  = module.s3_documents.bucket_arn
  documents_bucket_name = module.s3_documents.bucket_name
  s3_object_prefix      = var.s3_object_prefix
  analysis_queue_arn    = module.sqs_analysis.analysis_queue_arn
  tags                  = local.common_tags
}
