variable "project_name" {
  type        = string
  description = "Project identifier used in identity names."
}

variable "environment" {
  type        = string
  description = "Deployment environment name."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name."
}

variable "location" {
  type        = string
  description = "Azure region."
}

variable "documents_container_scope_id" {
  type        = string
  description = "ARM scope ID for the documents blob container."
}

variable "servicebus_queue_id" {
  type        = string
  description = "Service Bus analysis queue resource ID."
}

variable "key_vault_id" {
  type        = string
  description = "Key Vault resource ID."
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to managed identities."
  default     = {}
}
