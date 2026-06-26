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
