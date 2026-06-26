variable "project_name" {
  type        = string
  description = "Project identifier used in resource names."
}

variable "environment" {
  type        = string
  description = "Deployment environment name."
}

variable "server_name" {
  type        = string
  description = "Globally unique PostgreSQL Flexible Server name."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name."
}

variable "location" {
  type        = string
  description = "Azure region."
}

variable "postgres_subnet_id" {
  type        = string
  description = "Delegated subnet ID for private PostgreSQL access."
}

variable "private_dns_zone_id" {
  type        = string
  description = "Private DNS zone ID for PostgreSQL private link."
}

variable "key_vault_id" {
  type        = string
  description = "Key Vault ID where DATABASE-URL will be stored."
}

variable "postgres_version" {
  type        = string
  description = "PostgreSQL major version."
  default     = "16"
}

variable "sku_name" {
  type        = string
  description = "Flexible Server SKU (e.g. B_Standard_B1ms for dev Burstable)."
  default     = "B_Standard_B1ms"
}

variable "storage_mb" {
  type        = number
  description = "Allocated storage in megabytes."
  default     = 32768
}

variable "backup_retention_days" {
  type        = number
  description = "Backup retention in days."
  default     = 7
}

variable "admin_username" {
  type        = string
  description = "Administrator login name."
  default     = "legalmove"
}

variable "database_name" {
  type        = string
  description = "Application database name."
  default     = "legalmove"
}

variable "availability_zone" {
  type        = string
  description = "Optional availability zone for the server (e.g. 1, 2, 3)."
  default     = null
}

variable "high_availability_enabled" {
  type        = bool
  description = "Enable zone-redundant high availability."
  default     = false
}

variable "password_length" {
  type        = number
  description = "Length of the generated administrator password."
  default     = 32
}

variable "database_url_secret_name" {
  type        = string
  description = "Key Vault secret name for the DATABASE_URL connection string."
  default     = "DATABASE-URL"
}

variable "create_credentials_json_secret" {
  type        = bool
  description = "Also store host/port/dbname/username/password JSON in Key Vault."
  default     = false
}

variable "credentials_json_secret_name" {
  type        = string
  description = "Key Vault secret name for optional credentials JSON."
  default     = "DATABASE-CREDENTIALS"
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to PostgreSQL resources."
  default     = {}
}
