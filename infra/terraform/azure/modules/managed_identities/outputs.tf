output "api_identity_name" {
  description = "API user-assigned managed identity name."
  value       = azurerm_user_assigned_identity.api.name
}

output "api_identity_id" {
  description = "API user-assigned managed identity resource ID."
  value       = azurerm_user_assigned_identity.api.id
}

output "api_identity_client_id" {
  description = "API managed identity client ID (AZURE_CLIENT_ID when assigned to Container App)."
  value       = azurerm_user_assigned_identity.api.client_id
}

output "api_identity_principal_id" {
  description = "API managed identity principal ID."
  value       = azurerm_user_assigned_identity.api.principal_id
}

output "worker_identity_name" {
  description = "Worker user-assigned managed identity name."
  value       = azurerm_user_assigned_identity.worker.name
}

output "worker_identity_id" {
  description = "Worker user-assigned managed identity resource ID."
  value       = azurerm_user_assigned_identity.worker.id
}

output "worker_identity_client_id" {
  description = "Worker managed identity client ID (AZURE_CLIENT_ID when assigned to Container App)."
  value       = azurerm_user_assigned_identity.worker.client_id
}

output "worker_identity_principal_id" {
  description = "Worker managed identity principal ID."
  value       = azurerm_user_assigned_identity.worker.principal_id
}
