output "aws_region" {
  description = "AWS region where resources were created."
  value       = data.aws_region.current.name
}

output "aws_account_id" {
  description = "AWS account ID where resources were created."
  value       = data.aws_caller_identity.current.account_id
}

output "api_ecr_repository_url" {
  description = "ECR repository URL for the Go API container image."
  value       = module.ecr.api_repository_url
}

output "worker_ecr_repository_url" {
  description = "ECR repository URL for the Python worker container image."
  value       = module.ecr.worker_repository_url
}

output "documents_bucket_name" {
  description = "Private S3 bucket for uploaded documents."
  value       = module.s3_documents.bucket_name
}

output "documents_bucket_arn" {
  description = "ARN of the documents S3 bucket."
  value       = module.s3_documents.bucket_arn
}

output "analysis_queue_url" {
  description = "SQS queue URL for analysis jobs."
  value       = module.sqs_analysis.analysis_queue_url
}

output "analysis_queue_arn" {
  description = "SQS queue ARN for analysis jobs."
  value       = module.sqs_analysis.analysis_queue_arn
}

output "analysis_dlq_url" {
  description = "SQS dead-letter queue URL for failed analysis jobs."
  value       = module.sqs_analysis.analysis_dlq_url
}

output "analysis_dlq_arn" {
  description = "SQS dead-letter queue ARN for failed analysis jobs."
  value       = module.sqs_analysis.analysis_dlq_arn
}

output "api_policy_arn" {
  description = "IAM policy ARN to attach to the future API ECS task role."
  value       = module.iam_service_policies.api_policy_arn
}

output "worker_policy_arn" {
  description = "IAM policy ARN to attach to the future worker ECS task role."
  value       = module.iam_service_policies.worker_policy_arn
}

output "s3_object_prefix" {
  description = "Configured S3 key prefix for application runtime (maps to S3_PREFIX)."
  value       = var.s3_object_prefix
}

output "vpc_id" {
  description = "LegalMove Pro VPC ID for future ECS and ALB."
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs for future ALB."
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs for future ECS services and RDS."
  value       = module.networking.private_subnet_ids
}

output "alb_security_group_id" {
  description = "Security group ID for the future public ALB."
  value       = module.networking.alb_security_group_id
}

output "api_security_group_id" {
  description = "Security group ID for the future API ECS service."
  value       = module.networking.api_security_group_id
}

output "worker_security_group_id" {
  description = "Security group ID for the future worker ECS service."
  value       = module.networking.worker_security_group_id
}

output "rds_security_group_id" {
  description = "Security group ID attached to RDS."
  value       = module.networking.rds_security_group_id
}

output "nat_gateway_enabled" {
  description = "Whether private subnets have NAT gateway internet egress."
  value       = module.networking.nat_gateway_enabled
}

output "db_instance_endpoint" {
  description = "RDS PostgreSQL hostname (credentials are in Secrets Manager)."
  value       = module.rds_postgres.db_instance_endpoint
}

output "db_instance_port" {
  description = "RDS PostgreSQL port."
  value       = module.rds_postgres.db_instance_port
}

output "db_name" {
  description = "Initial PostgreSQL database name."
  value       = module.rds_postgres.db_name
}

output "db_secret_arn" {
  description = "Secrets Manager ARN with username, password, host, port, dbname, and database_url."
  value       = module.rds_postgres.db_secret_arn
}

output "database_url_secret_arn" {
  description = "Alias for db_secret_arn; secret JSON includes database_url for ECS tasks."
  value       = module.rds_postgres.database_url_secret_arn
}

output "ecs_cluster_id" {
  description = "ECS cluster ID."
  value       = module.ecs_base.ecs_cluster_id
}

output "ecs_cluster_name" {
  description = "ECS cluster name."
  value       = module.ecs_base.ecs_cluster_name
}

output "api_task_definition_arn" {
  description = "ARN of the API ECS task definition (no ECS service yet)."
  value       = module.ecs_base.api_task_definition_arn
}

output "worker_task_definition_arn" {
  description = "ARN of the worker ECS task definition (no ECS service yet)."
  value       = module.ecs_base.worker_task_definition_arn
}

output "api_task_role_arn" {
  description = "IAM task role ARN for API ECS tasks."
  value       = module.ecs_base.api_task_role_arn
}

output "worker_task_role_arn" {
  description = "IAM task role ARN for worker ECS tasks."
  value       = module.ecs_base.worker_task_role_arn
}

output "ecs_execution_role_arn" {
  description = "IAM execution role ARN for ECS tasks."
  value       = module.ecs_base.ecs_execution_role_arn
}

output "api_log_group_name" {
  description = "CloudWatch log group for API ECS tasks."
  value       = module.ecs_base.api_log_group_name
}

output "worker_log_group_name" {
  description = "CloudWatch log group for worker ECS tasks."
  value       = module.ecs_base.worker_log_group_name
}
