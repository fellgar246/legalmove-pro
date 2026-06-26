output "vnet_id" {
  description = "LegalMove Pro virtual network ID."
  value       = azurerm_virtual_network.this.id
}

output "vnet_name" {
  description = "LegalMove Pro virtual network name."
  value       = azurerm_virtual_network.this.name
}

output "postgres_subnet_id" {
  description = "Delegated subnet ID for PostgreSQL Flexible Server."
  value       = azurerm_subnet.postgres.id
}

output "container_apps_subnet_id" {
  description = "Subnet ID reserved for future Container Apps Environment."
  value       = azurerm_subnet.container_apps.id
}

output "private_dns_zone_id" {
  description = "Private DNS zone ID for PostgreSQL private link."
  value       = azurerm_private_dns_zone.postgres.id
}

output "private_dns_zone_name" {
  description = "Private DNS zone name (privatelink.postgres.database.azure.com)."
  value       = azurerm_private_dns_zone.postgres.name
}
