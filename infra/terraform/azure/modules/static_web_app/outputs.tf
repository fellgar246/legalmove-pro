output "name" {
  description = "Static Web App name."
  value       = azurerm_static_web_app.this.name
}

output "id" {
  description = "Static Web App resource ID."
  value       = azurerm_static_web_app.this.id
}

output "default_host_name" {
  description = "Auto-generated hostname (e.g. nice-meadow-xxx.azurestaticapps.net)."
  value       = azurerm_static_web_app.this.default_host_name
}

output "url" {
  description = "Public HTTPS URL for the Static Web App."
  value       = "https://${azurerm_static_web_app.this.default_host_name}"
}
