output "resource_group_name" {
  description = "Resource group name."
  value       = module.resource_group.name
}

output "resource_group_location" {
  description = "Resource group Azure region."
  value       = module.resource_group.location
}

output "acr_name" {
  description = "Azure Container Registry name."
  value       = module.acr.name
}

output "acr_login_server" {
  description = "ACR login server (docker login / image push target)."
  value       = module.acr.login_server
}

output "storage_account_name" {
  description = "Documents storage account name."
  value       = module.blob_documents.account_name
}

output "storage_account_id" {
  description = "Documents storage account resource ID."
  value       = module.blob_documents.account_id
}

output "documents_container_name" {
  description = "Private blob container for uploaded documents."
  value       = module.blob_documents.container_name
}

output "servicebus_namespace_name" {
  description = "Service Bus namespace name."
  value       = module.service_bus_analysis.namespace_name
}

output "servicebus_namespace_id" {
  description = "Service Bus namespace resource ID."
  value       = module.service_bus_analysis.namespace_id
}

output "servicebus_queue_name" {
  description = "Analysis jobs queue name."
  value       = module.service_bus_analysis.queue_name
}

output "servicebus_queue_id" {
  description = "Analysis jobs queue resource ID."
  value       = module.service_bus_analysis.queue_id
}

output "servicebus_dead_letter_queue_path" {
  description = "Built-in dead-letter subqueue path for failed/expired analysis messages."
  value       = module.service_bus_analysis.dead_letter_queue_path
}

output "key_vault_name" {
  description = "Key Vault name."
  value       = module.key_vault.name
}

output "key_vault_id" {
  description = "Key Vault resource ID."
  value       = module.key_vault.id
}

output "key_vault_uri" {
  description = "Key Vault URI for secret references."
  value       = module.key_vault.uri
}

output "api_identity_name" {
  description = "API user-assigned managed identity name (null if create_managed_identities=false)."
  value       = var.create_managed_identities ? module.managed_identities[0].api_identity_name : null
}

output "api_identity_client_id" {
  description = "API managed identity client ID for AZURE_CLIENT_ID in Container Apps."
  value       = var.create_managed_identities ? module.managed_identities[0].api_identity_client_id : null
}

output "worker_identity_name" {
  description = "Worker user-assigned managed identity name (null if create_managed_identities=false)."
  value       = var.create_managed_identities ? module.managed_identities[0].worker_identity_name : null
}

output "worker_identity_client_id" {
  description = "Worker managed identity client ID for AZURE_CLIENT_ID in Container Apps."
  value       = var.create_managed_identities ? module.managed_identities[0].worker_identity_client_id : null
}

output "expected_acr_image_tags" {
  description = "Suggested image repository:tag values when pushing to ACR."
  value = {
    api_go    = "${module.acr.login_server}/api-go:latest"
    worker_ai = "${module.acr.login_server}/worker-ai:latest"
  }
}
