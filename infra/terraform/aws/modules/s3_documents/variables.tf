variable "bucket_name" {
  type        = string
  description = "Globally unique S3 bucket name for uploaded documents."
}

variable "enable_versioning" {
  type        = bool
  description = "Enable object versioning (recommended for dev recovery)."
  default     = true
}

variable "lifecycle_expire_days" {
  type        = number
  description = "Expire current object versions after N days. Set to 0 to disable lifecycle expiration."
  default     = 90
}

variable "tags" {
  type        = map(string)
  description = "Common tags applied to all resources."
  default     = {}
}
