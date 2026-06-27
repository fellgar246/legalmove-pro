output "api_container_app_name" {
  description = "API Container App name."
  value       = azurerm_container_app.api.name
}

output "api_container_app_id" {
  description = "API Container App resource ID."
  value       = azurerm_container_app.api.id
}

output "api_container_app_url" {
  description = "Public HTTPS URL for the API Container App."
  value       = "https://${azurerm_container_app.api.ingress[0].fqdn}"
}

output "api_revision_name" {
  description = "Latest active revision name for the API Container App."
  value       = azurerm_container_app.api.latest_revision_name
}

output "worker_container_app_name" {
  description = "Worker Container App name."
  value       = azurerm_container_app.worker.name
}

output "worker_container_app_id" {
  description = "Worker Container App resource ID."
  value       = azurerm_container_app.worker.id
}

output "worker_revision_name" {
  description = "Latest active revision name for the worker Container App."
  value       = azurerm_container_app.worker.latest_revision_name
}

output "api_image" {
  description = "Full ACR image reference used by the API Container App."
  value       = local.api_image
}

output "worker_image" {
  description = "Full ACR image reference used by the worker Container App."
  value       = local.worker_image
}
