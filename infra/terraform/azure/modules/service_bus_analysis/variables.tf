variable "namespace_name" {
  type        = string
  description = "Service Bus namespace name (6-50 alphanumeric/hyphen characters, globally unique)."
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
  description = "Service Bus namespace SKU. Standard recommended for queue DLQ and future features."
  default     = "Standard"

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.sku)
    error_message = "sku must be Basic, Standard, or Premium."
  }
}

variable "queue_name" {
  type        = string
  description = "Analysis jobs queue name."
}

variable "max_delivery_count" {
  type        = number
  description = "Delivery attempts before a message is dead-lettered."
  default     = 5
}

variable "lock_duration" {
  type        = string
  description = "ISO 8601 lock duration for received messages (e.g. PT1M)."
  default     = "PT1M"
}

variable "message_ttl" {
  type        = string
  description = "ISO 8601 default message TTL (e.g. P4D)."
  default     = "P4D"
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to the namespace."
  default     = {}
}
