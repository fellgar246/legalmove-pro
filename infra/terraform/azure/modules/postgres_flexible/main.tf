locals {
  name_prefix = "${var.project_name}-${var.environment}"

  database_url = format(
    "postgres://%s:%s@%s:5432/%s?sslmode=require",
    var.admin_username,
    urlencode(random_password.admin.result),
    azurerm_postgresql_flexible_server.this.fqdn,
    var.database_name,
  )

  credentials_json = jsonencode({
    host     = azurerm_postgresql_flexible_server.this.fqdn
    port     = 5432
    dbname   = var.database_name
    username = var.admin_username
    password = random_password.admin.result
    engine   = "postgres"
  })
}

resource "random_password" "admin" {
  length  = var.password_length
  special = true

  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "azurerm_postgresql_flexible_server" "this" {
  name                          = var.server_name
  resource_group_name           = var.resource_group_name
  location                      = var.location
  version                       = var.postgres_version
  sku_name                      = var.sku_name
  storage_mb                    = var.storage_mb
  backup_retention_days         = var.backup_retention_days
  geo_redundant_backup_enabled  = false
  public_network_access_enabled = false

  administrator_login    = var.admin_username
  administrator_password = random_password.admin.result

  delegated_subnet_id = var.postgres_subnet_id
  private_dns_zone_id = var.private_dns_zone_id

  zone = var.availability_zone

  dynamic "high_availability" {
    for_each = var.high_availability_enabled ? [1] : []
    content {
      mode = "ZoneRedundant"
    }
  }

  tags = var.tags
}

resource "azurerm_postgresql_flexible_server_database" "this" {
  name      = var.database_name
  server_id = azurerm_postgresql_flexible_server.this.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_key_vault_secret" "database_url" {
  name         = var.database_url_secret_name
  value        = local.database_url
  key_vault_id = var.key_vault_id

  content_type = "text/plain"

  tags = var.tags
}

resource "azurerm_key_vault_secret" "database_credentials" {
  count = var.create_credentials_json_secret ? 1 : 0

  name         = var.credentials_json_secret_name
  value        = local.credentials_json
  key_vault_id = var.key_vault_id

  content_type = "application/json"

  tags = var.tags
}
