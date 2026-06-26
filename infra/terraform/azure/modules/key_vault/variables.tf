variable "name" {
  type        = string
  description = "Key Vault name (3-24 alphanumeric/hyphen characters, globally unique)."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name."
}

variable "location" {
  type        = string
  description = "Azure region."
}

variable "sku_name" {
  type        = string
  description = "Key Vault SKU (standard or premium)."
  default     = "standard"

  validation {
    condition     = contains(["standard", "premium"], lower(var.sku_name))
    error_message = "sku_name must be standard or premium."
  }
}

variable "soft_delete_retention_days" {
  type        = number
  description = "Soft-delete retention in days."
  default     = 7
}

variable "purge_protection_enabled" {
  type        = bool
  description = "Prevent permanent deletion during retention. Default false for dev."
  default     = false
}

variable "public_network_access_enabled" {
  type        = bool
  description = "Allow public network access to the vault."
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to the key vault."
  default     = {}
}
