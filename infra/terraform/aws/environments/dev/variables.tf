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
