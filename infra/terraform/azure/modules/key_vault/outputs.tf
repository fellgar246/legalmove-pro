output "name" {
  description = "Key Vault name."
  value       = azurerm_key_vault.this.name
}

output "id" {
  description = "Key Vault resource ID."
  value       = azurerm_key_vault.this.id
}

output "uri" {
  description = "Key Vault URI."
  value       = azurerm_key_vault.this.vault_uri
}

output "deployer_secrets_officer_role_assignment_id" {
  description = "RBAC assignment granting the Terraform deployer Key Vault Secrets Officer."
  value       = azurerm_role_assignment.deployer_secrets_officer.id
}
