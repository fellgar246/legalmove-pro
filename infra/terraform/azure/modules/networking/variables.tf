variable "project_name" {
  type        = string
  description = "Project identifier used in resource names."
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

variable "vnet_cidr" {
  type        = string
  description = "Address space for the LegalMove Pro VNet."
  default     = "10.30.0.0/16"
}

variable "postgres_subnet_cidr" {
  type        = string
  description = "Subnet for PostgreSQL Flexible Server (delegated)."
  default     = "10.30.11.0/24"
}

variable "container_apps_subnet_cidr" {
  type        = string
  description = "Subnet reserved for future Container Apps Environment (/23 recommended)."
  default     = "10.30.21.0/23"
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to networking resources."
  default     = {}
}
