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

variable "container_apps_subnet_id" {
  type        = string
  description = "Subnet ID for Container Apps Environment VNet integration (delegated to Microsoft.App/environments)."
}

variable "log_analytics_workspace_name" {
  type        = string
  description = "Optional Log Analytics workspace name override."
  default     = null
}

variable "container_apps_environment_name" {
  type        = string
  description = "Optional Container Apps Environment name override."
  default     = null
}

variable "log_analytics_retention_days" {
  type        = number
  description = "Log Analytics workspace retention in days."
  default     = 30
}

variable "container_apps_internal_load_balancer_enabled" {
  type        = bool
  description = "Use an internal load balancer. Set false to allow public API ingress in Block 4.E."
  default     = false
}

variable "container_apps_zone_redundancy_enabled" {
  type        = bool
  description = "Enable zone redundancy for the Container Apps Environment."
  default     = false
}

variable "container_apps_workload_profile_type" {
  type        = string
  description = "Workload profile type for VNet-integrated environments. Consumption is the dev default."
  default     = "Consumption"
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to Log Analytics and Container Apps Environment."
  default     = {}
}
