locals {
  name_prefix = "${var.project_name}-${var.environment}"

  log_analytics_workspace_name = coalesce(
    var.log_analytics_workspace_name,
    "log-${local.name_prefix}",
  )

  container_apps_environment_name = coalesce(
    var.container_apps_environment_name,
    "cae-${local.name_prefix}",
  )

  infrastructure_resource_group_name = "${var.resource_group_name}-cae-infra"
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = local.log_analytics_workspace_name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_analytics_retention_days

  tags = var.tags
}

resource "azurerm_container_app_environment" "this" {
  name                       = local.container_apps_environment_name
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id

  infrastructure_subnet_id           = var.container_apps_subnet_id
  infrastructure_resource_group_name = local.infrastructure_resource_group_name

  internal_load_balancer_enabled = var.container_apps_internal_load_balancer_enabled
  zone_redundancy_enabled        = var.container_apps_zone_redundancy_enabled

  # VNet integration requires a workload profile (Consumption for dev/serverless).
  workload_profile {
    name                  = "Consumption"
    workload_profile_type = var.container_apps_workload_profile_type
  }

  tags = var.tags
}
