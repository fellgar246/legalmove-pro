variable "name" {
  type        = string
  description = "ACR name (5-50 alphanumeric characters, globally unique)."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name."
}

variable "location" {
  type        = string
  description = "Azure region."
}

variable "sku" {
  type        = string
  description = "ACR SKU (Basic, Standard, Premium)."
  default     = "Basic"

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.sku)
    error_message = "sku must be Basic, Standard, or Premium."
  }
}

variable "public_network_access_enabled" {
  type        = bool
  description = "Allow public network access to the registry."
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to the registry."
  default     = {}
}
