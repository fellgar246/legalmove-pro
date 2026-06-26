variable "location" {
  type        = string
  description = "Azure region for all foundation resources."
  default     = "eastus"
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

variable "resource_group_name" {
  type        = string
  description = "Optional resource group name override. Defaults to rg-<project>-<environment>."
  default     = null
}

variable "acr_name" {
  type        = string
  description = "Optional ACR name override (5-50 alphanumeric, globally unique)."
  default     = null
}

variable "acr_sku" {
  type        = string
  description = "ACR SKU."
  default     = "Basic"
}

variable "storage_account_name" {
  type        = string
  description = "Optional storage account name override (3-24 lowercase alphanumeric, globally unique)."
  default     = null
}

variable "storage_container_name" {
  type        = string
  description = "Private blob container for uploaded documents."
  default     = "documents"
}

variable "storage_replication_type" {
  type        = string
  description = "Storage account replication type."
  default     = "LRS"
}

variable "storage_blob_soft_delete_retention_days" {
  type        = number
  description = "Blob soft-delete retention in days."
  default     = 7
}

variable "storage_lifecycle_expire_days" {
  type        = number
  description = "Expire dev document blobs after N days. Set to 0 to disable."
  default     = 90
}

variable "servicebus_namespace_name" {
  type        = string
  description = "Optional Service Bus namespace name override (6-50 chars, globally unique)."
  default     = null
}

variable "servicebus_sku" {
  type        = string
  description = "Service Bus namespace SKU. Standard supports queue DLQ and future features."
  default     = "Standard"
}

variable "servicebus_queue_name" {
  type        = string
  description = "Analysis jobs queue name."
  default     = "analysis-jobs"
}

variable "servicebus_max_delivery_count" {
  type        = number
  description = "Delivery attempts before a message is dead-lettered."
  default     = 5
}

variable "servicebus_lock_duration" {
  type        = string
  description = "ISO 8601 lock duration for received messages."
  default     = "PT1M"
}

variable "servicebus_message_ttl" {
  type        = string
  description = "ISO 8601 default message TTL."
  default     = "P4D"
}

variable "key_vault_name" {
  type        = string
  description = "Optional Key Vault name override (3-24 alphanumeric/hyphen, globally unique)."
  default     = null
}

variable "key_vault_sku_name" {
  type        = string
  description = "Key Vault SKU."
  default     = "standard"
}

variable "key_vault_soft_delete_retention_days" {
  type        = number
  description = "Key Vault soft-delete retention in days."
  default     = 7
}

variable "key_vault_purge_protection_enabled" {
  type        = bool
  description = "Enable purge protection on Key Vault. Default false for dev."
  default     = false
}

variable "create_managed_identities" {
  type        = bool
  description = "Create user-assigned managed identities and RBAC for future Container Apps."
  default     = true
}

variable "vnet_cidr" {
  type        = string
  description = "Address space for the LegalMove Pro VNet."
  default     = "10.30.0.0/16"
}

variable "postgres_subnet_cidr" {
  type        = string
  description = "Delegated subnet for PostgreSQL Flexible Server."
  default     = "10.30.11.0/24"
}

variable "container_apps_subnet_cidr" {
  type        = string
  description = "Subnet reserved for future Container Apps Environment (/23 recommended)."
  default     = "10.30.21.0/23"
}

variable "postgres_server_name" {
  type        = string
  description = "Optional PostgreSQL Flexible Server name override (3-63 chars, globally unique)."
  default     = null
}

variable "postgres_version" {
  type        = string
  description = "PostgreSQL major version."
  default     = "16"
}

variable "postgres_sku_name" {
  type        = string
  description = "Flexible Server SKU."
  default     = "B_Standard_B1ms"
}

variable "postgres_storage_mb" {
  type        = number
  description = "Allocated storage in megabytes."
  default     = 32768
}

variable "postgres_backup_retention_days" {
  type        = number
  description = "Backup retention in days."
  default     = 7
}

variable "postgres_admin_username" {
  type        = string
  description = "PostgreSQL administrator login."
  default     = "legalmove"
}

variable "postgres_database_name" {
  type        = string
  description = "Application database name."
  default     = "legalmove"
}

variable "postgres_zone" {
  type        = string
  description = "Optional availability zone for PostgreSQL (1, 2, or 3)."
  default     = null
}

variable "postgres_high_availability_enabled" {
  type        = bool
  description = "Enable zone-redundant high availability."
  default     = false
}

variable "postgres_password_length" {
  type        = number
  description = "Length of the generated administrator password."
  default     = 32
}

variable "database_url_secret_name" {
  type        = string
  description = "Key Vault secret name for DATABASE_URL."
  default     = "DATABASE-URL"
}

variable "create_postgres_credentials_json_secret" {
  type        = bool
  description = "Also store DATABASE-CREDENTIALS JSON in Key Vault."
  default     = false
}
