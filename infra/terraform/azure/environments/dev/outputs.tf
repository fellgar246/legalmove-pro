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

output "api_managed_identity_id" {
  description = "API user-assigned managed identity resource ID."
  value       = var.create_managed_identities ? module.managed_identities[0].api_identity_id : null
}

output "api_managed_identity_client_id" {
  description = "Alias for api_identity_client_id (Block 4.E wiring)."
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

output "worker_managed_identity_id" {
  description = "Worker user-assigned managed identity resource ID."
  value       = var.create_managed_identities ? module.managed_identities[0].worker_identity_id : null
}

output "worker_managed_identity_client_id" {
  description = "Alias for worker_identity_client_id (Block 4.E wiring)."
  value       = var.create_managed_identities ? module.managed_identities[0].worker_identity_client_id : null
}

output "expected_acr_image_tags" {
  description = "Suggested image repository:tag values when pushing to ACR."
  value = {
    api_go    = "${module.acr.login_server}/api-go:latest"
    worker_ai = "${module.acr.login_server}/worker-ai:latest"
  }
}

output "vnet_id" {
  description = "LegalMove Pro virtual network ID."
  value       = module.networking.vnet_id
}

output "postgres_subnet_id" {
  description = "Delegated subnet ID for PostgreSQL Flexible Server."
  value       = module.networking.postgres_subnet_id
}

output "container_apps_subnet_id" {
  description = "Subnet ID reserved for future Container Apps Environment."
  value       = module.networking.container_apps_subnet_id
}

output "postgres_private_dns_zone_id" {
  description = "Private DNS zone ID for PostgreSQL private link."
  value       = module.networking.private_dns_zone_id
}

output "postgres_server_name" {
  description = "PostgreSQL Flexible Server name."
  value       = module.postgres_flexible.server_name
}

output "postgres_server_fqdn" {
  description = "Private FQDN for PostgreSQL (VNet/private DNS only)."
  value       = module.postgres_flexible.server_fqdn
}

output "postgres_database_name" {
  description = "Application database name."
  value       = module.postgres_flexible.database_name
}

output "database_url_secret_id" {
  description = "Key Vault secret resource ID for DATABASE-URL."
  value       = module.postgres_flexible.database_url_secret_id
}

output "database_url_secret_name" {
  description = "Key Vault secret name for DATABASE-URL."
  value       = module.postgres_flexible.database_url_secret_name
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID (null if create_container_apps_environment=false)."
  value       = var.create_container_apps_environment ? module.container_apps_environment[0].log_analytics_workspace_id : null
}

output "log_analytics_workspace_name" {
  description = "Log Analytics workspace name (null if create_container_apps_environment=false)."
  value       = var.create_container_apps_environment ? module.container_apps_environment[0].log_analytics_workspace_name : null
}

output "container_apps_environment_id" {
  description = "Container Apps Environment resource ID (null if create_container_apps_environment=false)."
  value       = var.create_container_apps_environment ? module.container_apps_environment[0].container_apps_environment_id : null
}

output "container_apps_environment_name" {
  description = "Container Apps Environment name (null if create_container_apps_environment=false)."
  value       = var.create_container_apps_environment ? module.container_apps_environment[0].container_apps_environment_name : null
}

output "container_apps_default_domain" {
  description = "Default domain suffix for future Container Apps ingress (null if create_container_apps_environment=false)."
  value       = var.create_container_apps_environment ? module.container_apps_environment[0].container_apps_default_domain : null
}

output "api_container_app_name" {
  description = "API Container App name (null if create_container_apps=false)."
  value       = local.deploy_container_apps ? module.container_apps[0].api_container_app_name : null
}

output "api_container_app_id" {
  description = "API Container App resource ID (null if create_container_apps=false)."
  value       = local.deploy_container_apps ? module.container_apps[0].api_container_app_id : null
}

output "api_container_app_url" {
  description = "Public HTTPS URL for the API Container App (null if create_container_apps=false)."
  value       = local.deploy_container_apps ? module.container_apps[0].api_container_app_url : null
}

output "api_revision_name" {
  description = "Latest API Container App revision name (null if create_container_apps=false)."
  value       = local.deploy_container_apps ? module.container_apps[0].api_revision_name : null
}

output "worker_container_app_name" {
  description = "Worker Container App name (null if create_container_apps=false)."
  value       = local.deploy_container_apps ? module.container_apps[0].worker_container_app_name : null
}

output "worker_container_app_id" {
  description = "Worker Container App resource ID (null if create_container_apps=false)."
  value       = local.deploy_container_apps ? module.container_apps[0].worker_container_app_id : null
}

output "worker_revision_name" {
  description = "Latest worker Container App revision name (null if create_container_apps=false)."
  value       = local.deploy_container_apps ? module.container_apps[0].worker_revision_name : null
}
