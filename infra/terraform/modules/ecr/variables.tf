variable "api_repository_name" {
  type        = string
  description = "ECR repository name for the Go API."
}

variable "worker_repository_name" {
  type        = string
  description = "ECR repository name for the Python worker."
}

variable "image_tag_mutability" {
  type        = string
  description = "MUTABLE allows overwriting tags such as latest in dev; IMMUTABLE is safer for prod."
  default     = "MUTABLE"

  validation {
    condition     = contains(["MUTABLE", "IMMUTABLE"], var.image_tag_mutability)
    error_message = "image_tag_mutability must be MUTABLE or IMMUTABLE."
  }
}

variable "max_image_count" {
  type        = number
  description = "Maximum number of images to retain per repository."
  default     = 10
}

variable "tags" {
  type        = map(string)
  description = "Common tags applied to all resources."
  default     = {}
}
