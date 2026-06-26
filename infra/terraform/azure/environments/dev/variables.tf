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
