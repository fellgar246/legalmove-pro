variable "project_name" {
  type        = string
  description = "Project identifier used in policy names."
}

variable "environment" {
  type        = string
  description = "Deployment environment (for example dev, staging)."
}

variable "documents_bucket_arn" {
  type        = string
  description = "ARN of the documents S3 bucket."
}

variable "documents_bucket_name" {
  type        = string
  description = "Name of the documents S3 bucket."
}

variable "s3_object_prefix" {
  type        = string
  description = "Optional key prefix used by the application (for example dev). Empty allows all keys in the bucket."
  default     = ""
}

variable "analysis_queue_arn" {
  type        = string
  description = "ARN of the main analysis jobs SQS queue."
}

variable "tags" {
  type        = map(string)
  description = "Common tags applied to all resources."
  default     = {}
}
