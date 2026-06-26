variable "project_name" {
  type        = string
  description = "Project identifier used in resource names."
}

variable "environment" {
  type        = string
  description = "Deployment environment (for example dev, staging)."
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC."
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for public subnets (one per AZ)."
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private subnets (one per AZ)."
}

variable "enable_nat_gateway" {
  type        = bool
  description = "Create a NAT gateway for private subnet egress. Disabled by default in dev to reduce cost."
  default     = false
}

variable "api_container_port" {
  type        = number
  description = "Container port exposed by the future API ECS service."
  default     = 8080
}

variable "tags" {
  type        = map(string)
  description = "Common tags applied to all resources."
  default     = {}
}
