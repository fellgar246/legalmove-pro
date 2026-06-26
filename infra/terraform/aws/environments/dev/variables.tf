variable "aws_region" {
  type        = string
  description = "AWS region for all foundation resources."
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Project identifier used in resource names and tags."
  default     = "legalmove-pro"
}

variable "environment" {
  type        = string
  description = "Deployment environment name."
  default     = "dev"
}

variable "s3_bucket_name" {
  type        = string
  description = "Optional globally unique S3 bucket name. Defaults to legalmove-pro-dev-documents-<account_id>."
  default     = null
}

variable "s3_object_prefix" {
  type        = string
  description = "Application key prefix for IAM scoping and future runtime config (S3_PREFIX)."
  default     = "dev"
}

variable "s3_enable_versioning" {
  type        = bool
  description = "Enable versioning on the documents bucket."
  default     = true
}

variable "s3_lifecycle_expire_days" {
  type        = number
  description = "Expire document objects after N days in dev. Set to 0 to disable."
  default     = 90
}

variable "sqs_visibility_timeout_seconds" {
  type        = number
  description = "SQS visibility timeout for analysis jobs. Should be >= worker processing time."
  default     = 60
}

variable "sqs_message_retention_seconds" {
  type        = number
  description = "SQS message retention for main queue and DLQ."
  default     = 345600
}

variable "sqs_receive_wait_time_seconds" {
  type        = number
  description = "SQS long polling wait time."
  default     = 10
}

variable "sqs_max_receive_count" {
  type        = number
  description = "Receive attempts before a message is moved to the DLQ."
  default     = 5
}

variable "ecr_image_tag_mutability" {
  type        = string
  description = "ECR tag mutability. MUTABLE is practical for dev image iteration."
  default     = "MUTABLE"
}

variable "ecr_max_image_count" {
  type        = number
  description = "Maximum number of images retained per ECR repository."
  default     = 10
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the LegalMove Pro VPC."
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "Public subnet CIDR blocks (one per AZ)."
  default     = ["10.20.1.0/24", "10.20.2.0/24"]
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "Private subnet CIDR blocks (one per AZ)."
  default     = ["10.20.11.0/24", "10.20.12.0/24"]
}

variable "enable_nat_gateway" {
  type        = bool
  description = "Create a NAT gateway for private subnet internet egress. Default false to reduce dev cost."
  default     = false
}

variable "db_name" {
  type        = string
  description = "Initial PostgreSQL database name."
  default     = "legalmove"
}

variable "db_username" {
  type        = string
  description = "Master PostgreSQL username."
  default     = "legalmove"
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance class."
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  type        = number
  description = "RDS allocated storage in GB."
  default     = 20
}

variable "db_engine_version" {
  type        = string
  description = "PostgreSQL engine version."
  default     = "16.6"
}

variable "db_backup_retention_period" {
  type        = number
  description = "Automated backup retention in days."
  default     = 7
}

variable "db_deletion_protection" {
  type        = bool
  description = "Enable RDS deletion protection."
  default     = false
}

variable "db_skip_final_snapshot" {
  type        = bool
  description = "Skip final snapshot when destroying RDS (dev-friendly)."
  default     = true
}

variable "ecs_image_tag" {
  type        = string
  description = "Container image tag referenced by ECS task definitions."
  default     = "latest"
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

variable "openai_api_key_secret_arn" {
  type        = string
  description = "Optional Secrets Manager ARN for OPENAI_API_KEY (plain string secret). Required for real worker AI runs."
  default     = null
}

variable "worker_use_mock_result" {
  type        = bool
  description = "When true, worker skips OpenAI and writes mock results."
  default     = false
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
