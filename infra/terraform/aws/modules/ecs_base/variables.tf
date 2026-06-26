variable "project_name" {
  type        = string
  description = "Project identifier used in resource names."
}

variable "environment" {
  type        = string
  description = "Deployment environment (for example dev, staging)."
}

variable "aws_region" {
  type        = string
  description = "AWS region for ECS task definitions and logs."
}

variable "api_image" {
  type        = string
  description = "Full ECR image URI for the API container (including tag)."
}

variable "worker_image" {
  type        = string
  description = "Full ECR image URI for the worker container (including tag)."
}

variable "api_policy_arn" {
  type        = string
  description = "IAM policy ARN with S3/SQS permissions for the API task role."
}

variable "worker_policy_arn" {
  type        = string
  description = "IAM policy ARN with S3/SQS permissions for the worker task role."
}

variable "db_secret_arn" {
  type        = string
  description = "Secrets Manager ARN containing database_url for ECS secret injection."
}

variable "openai_api_key_secret_arn" {
  type        = string
  description = "Optional Secrets Manager ARN for OPENAI_API_KEY (plain string secret recommended)."
  default     = null
}

variable "s3_bucket" {
  type        = string
  description = "Documents S3 bucket name."
}

variable "s3_prefix" {
  type        = string
  description = "S3 object key prefix (maps to S3_PREFIX)."
}

variable "sqs_queue_url" {
  type        = string
  description = "SQS analysis jobs queue URL."
}

variable "ecs_api_cpu" {
  type        = number
  description = "Fargate CPU units for the API task definition."
  default     = 256
}

variable "ecs_api_memory" {
  type        = number
  description = "Fargate memory (MiB) for the API task definition."
  default     = 512
}

variable "ecs_worker_cpu" {
  type        = number
  description = "Fargate CPU units for the worker task definition."
  default     = 512
}

variable "ecs_worker_memory" {
  type        = number
  description = "Fargate memory (MiB) for the worker task definition."
  default     = 1024
}

variable "api_container_port" {
  type        = number
  description = "Container port exposed by the API."
  default     = 8080
}

variable "worker_use_mock_result" {
  type        = bool
  description = "When true, worker skips OpenAI and writes mock results."
  default     = false
}

variable "sqs_visibility_timeout" {
  type        = number
  description = "SQS visibility timeout for worker consumption."
  default     = 60
}

variable "sqs_wait_time_seconds" {
  type        = number
  description = "SQS long polling wait time for worker."
  default     = 10
}

variable "document_temp_dir" {
  type        = string
  description = "Temporary directory for materialized documents inside the worker container."
  default     = "/tmp/legalmove-documents"
}

variable "pdf_max_bytes" {
  type        = number
  description = "Maximum PDF size accepted by the worker."
  default     = 20971520
}

variable "pdf_min_text_chars" {
  type        = number
  description = "Minimum extracted text characters for native PDF parsing."
  default     = 32
}

variable "log_retention_days" {
  type        = number
  description = "CloudWatch log retention in days."
  default     = 7
}

variable "tags" {
  type        = map(string)
  description = "Common tags applied to all resources."
  default     = {}
}
