variable "project_name" {
  type        = string
  description = "Project identifier used in resource names."
}

variable "environment" {
  type        = string
  description = "Deployment environment (for example dev, staging)."
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for the DB subnet group."
}

variable "security_group_ids" {
  type        = list(string)
  description = "Security groups attached to the RDS instance."
}

variable "db_name" {
  type        = string
  description = "Initial database name."
  default     = "legalmove"
}

variable "db_username" {
  type        = string
  description = "Master username for PostgreSQL."
  default     = "legalmove"
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance class for dev workloads."
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  type        = number
  description = "Allocated storage in GB."
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
  description = "Prevent accidental RDS deletion."
  default     = false
}

variable "db_skip_final_snapshot" {
  type        = bool
  description = "Skip final snapshot on destroy (dev-friendly)."
  default     = true
}

variable "apply_immediately" {
  type        = bool
  description = "Apply modifications immediately instead of during maintenance window."
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "Common tags applied to all resources."
  default     = {}
}
