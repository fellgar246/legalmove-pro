variable "project_name" {
  type        = string
  description = "Project identifier used in resource names."
}

variable "environment" {
  type        = string
  description = "Deployment environment (for example dev, staging)."
}

variable "visibility_timeout_seconds" {
  type        = number
  description = "Visibility timeout for the main analysis jobs queue."
  default     = 60
}

variable "message_retention_seconds" {
  type        = number
  description = "Message retention for both main queue and DLQ."
  default     = 345600
}

variable "receive_wait_time_seconds" {
  type        = number
  description = "Long polling wait time for ReceiveMessage."
  default     = 10
}

variable "max_receive_count" {
  type        = number
  description = "Number of receives before a message is sent to the DLQ."
  default     = 5
}

variable "tags" {
  type        = map(string)
  description = "Common tags applied to all resources."
  default     = {}
}
