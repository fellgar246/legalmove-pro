output "account_name" {
  description = "Storage account name."
  value       = azurerm_storage_account.this.name
}

output "account_id" {
  description = "Storage account resource ID."
  value       = azurerm_storage_account.this.id
}

output "container_name" {
  description = "Documents blob container name."
  value       = azurerm_storage_container.documents.name
}

output "container_id" {
  description = "Documents blob container resource ID."
  value       = azurerm_storage_container.documents.id
}

output "container_resource_manager_id" {
  description = "ARM resource ID for the documents container (RBAC scope)."
  value       = "${azurerm_storage_account.this.id}/blobServices/default/containers/${azurerm_storage_container.documents.name}"
}
