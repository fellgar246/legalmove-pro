variable "name" {
  type        = string
  description = "Static Web App name (2-60 alphanumeric/hyphen, globally unique)."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name."
}

variable "location" {
  type        = string
  description = "Azure region. centralus is supported for Static Web Apps."
}

variable "sku_tier" {
  type        = string
  description = "Static Web App SKU tier (Free or Standard)."
  default     = "Free"

  validation {
    condition     = contains(["Free", "Standard"], var.sku_tier)
    error_message = "sku_tier must be Free or Standard."
  }
}

variable "sku_size" {
  type        = string
  description = "Static Web App SKU size (Free or Standard)."
  default     = "Free"

  validation {
    condition     = contains(["Free", "Standard"], var.sku_size)
    error_message = "sku_size must be Free or Standard."
  }
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to the Static Web App."
  default     = {}
}
