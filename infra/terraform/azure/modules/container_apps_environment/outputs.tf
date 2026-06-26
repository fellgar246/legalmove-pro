output "log_analytics_workspace_id" {
  description = "Log Analytics workspace resource ID."
  value       = azurerm_log_analytics_workspace.this.id
}

output "log_analytics_workspace_name" {
  description = "Log Analytics workspace name."
  value       = azurerm_log_analytics_workspace.this.name
}

output "container_apps_environment_id" {
  description = "Container Apps Environment resource ID."
  value       = azurerm_container_app_environment.this.id
}

output "container_apps_environment_name" {
  description = "Container Apps Environment name."
  value       = azurerm_container_app_environment.this.name
}

output "container_apps_default_domain" {
  description = "Default domain suffix for future Container Apps ingress (Block 4.E)."
  value       = azurerm_container_app_environment.this.default_domain
}

output "container_apps_static_ip" {
  description = "Static IP for the environment ingress (when VNet integrated)."
  value       = azurerm_container_app_environment.this.static_ip_address
}
