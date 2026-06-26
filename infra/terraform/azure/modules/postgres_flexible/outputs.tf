output "server_name" {
  description = "PostgreSQL Flexible Server name."
  value       = azurerm_postgresql_flexible_server.this.name
}

output "server_id" {
  description = "PostgreSQL Flexible Server resource ID."
  value       = azurerm_postgresql_flexible_server.this.id
}

output "server_fqdn" {
  description = "Private FQDN for PostgreSQL (resolves via private DNS zone)."
  value       = azurerm_postgresql_flexible_server.this.fqdn
}

output "database_name" {
  description = "Application database name."
  value       = azurerm_postgresql_flexible_server_database.this.name
}

output "admin_username" {
  description = "Administrator login name (password is not exported)."
  value       = var.admin_username
  sensitive   = true
}

output "database_url_secret_id" {
  description = "Key Vault secret resource ID for DATABASE-URL."
  value       = azurerm_key_vault_secret.database_url.id
}

output "database_url_secret_name" {
  description = "Key Vault secret name for DATABASE-URL."
  value       = azurerm_key_vault_secret.database_url.name
}

output "database_credentials_secret_id" {
  description = "Key Vault secret ID for optional credentials JSON (null if disabled)."
  value       = var.create_credentials_json_secret ? azurerm_key_vault_secret.database_credentials[0].id : null
}
