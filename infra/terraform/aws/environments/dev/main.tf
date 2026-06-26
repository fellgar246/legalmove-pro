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

module "networking" {
  source = "../../modules/networking"

  project_name         = var.project_name
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  enable_nat_gateway   = var.enable_nat_gateway
  tags                 = local.common_tags
}

module "rds_postgres" {
  source = "../../modules/rds_postgres"

  project_name               = var.project_name
  environment                = var.environment
  private_subnet_ids         = module.networking.private_subnet_ids
  security_group_ids         = [module.networking.rds_security_group_id]
  db_name                    = var.db_name
  db_username                = var.db_username
  db_instance_class          = var.db_instance_class
  db_allocated_storage       = var.db_allocated_storage
  db_engine_version          = var.db_engine_version
  db_backup_retention_period = var.db_backup_retention_period
  db_deletion_protection     = var.db_deletion_protection
  db_skip_final_snapshot     = var.db_skip_final_snapshot
  tags                       = local.common_tags
}

module "ecs_base" {
  source = "../../modules/ecs_base"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  api_image    = "${module.ecr.api_repository_url}:${var.ecs_image_tag}"
  worker_image = "${module.ecr.worker_repository_url}:${var.ecs_image_tag}"

  api_policy_arn    = module.iam_service_policies.api_policy_arn
  worker_policy_arn = module.iam_service_policies.worker_policy_arn
  db_secret_arn     = module.rds_postgres.db_secret_arn

  openai_api_key_secret_arn = var.openai_api_key_secret_arn

  s3_bucket     = module.s3_documents.bucket_name
  s3_prefix     = var.s3_object_prefix
  sqs_queue_url = module.sqs_analysis.analysis_queue_url

  ecs_api_cpu            = var.ecs_api_cpu
  ecs_api_memory         = var.ecs_api_memory
  ecs_worker_cpu         = var.ecs_worker_cpu
  ecs_worker_memory      = var.ecs_worker_memory
  api_container_port     = var.api_container_port
  worker_use_mock_result = var.worker_use_mock_result
  sqs_visibility_timeout = var.sqs_visibility_timeout_seconds
  sqs_wait_time_seconds  = var.sqs_receive_wait_time_seconds
  document_temp_dir      = var.document_temp_dir
  pdf_max_bytes          = var.pdf_max_bytes
  pdf_min_text_chars     = var.pdf_min_text_chars

  tags = local.common_tags
}
