variable "account_name" {
  type        = string
  description = "Globally unique storage account name (3-24 lowercase alphanumeric)."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name."
}

variable "location" {
  type        = string
  description = "Azure region."
}

variable "container_name" {
  type        = string
  description = "Private blob container name for uploaded documents."
}

variable "replication_type" {
  type        = string
  description = "Storage replication type."
  default     = "LRS"
}

variable "blob_soft_delete_retention_days" {
  type        = number
  description = "Blob soft-delete retention in days."
  default     = 7
}

variable "lifecycle_expire_days" {
  type        = number
  description = "Delete block blobs after N days since modification. Set to 0 to disable lifecycle policy."
  default     = 90
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to the storage account."
  default     = {}
}
