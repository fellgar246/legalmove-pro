resource "random_string" "suffix" {
  length  = 4
  lower   = true
  upper   = false
  numeric = true
  special = false
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  name_suffix = random_string.suffix.result

  resource_group_name = coalesce(
    var.resource_group_name,
    "rg-${var.project_name}-${var.environment}",
  )

  # Storage account: 3-24 lowercase alphanumeric, globally unique.
  storage_account_name = coalesce(
    var.storage_account_name,
    substr("lmprodev${local.name_suffix}", 0, 24),
  )

  # ACR: 5-50 alphanumeric, globally unique.
  acr_name = coalesce(
    var.acr_name,
    substr("lmprodevacr${local.name_suffix}", 0, 50),
  )

  # Key Vault: 3-24 alphanumeric/hyphen, globally unique.
  key_vault_name = coalesce(
    var.key_vault_name,
    substr("kv-lmpro-${var.environment}-${local.name_suffix}", 0, 24),
  )

  # Service Bus namespace: 6-50 chars, globally unique.
  servicebus_namespace_name = coalesce(
    var.servicebus_namespace_name,
    substr("sb-lmpro-${var.environment}-${local.name_suffix}", 0, 50),
  )

  # PostgreSQL Flexible Server: 3-63 chars, globally unique.
  postgres_server_name = coalesce(
    var.postgres_server_name,
    substr("psql-lmpro-${var.environment}-${local.name_suffix}", 0, 63),
  )
}

module "resource_group" {
  source = "../../modules/resource_group"

  name     = local.resource_group_name
  location = var.location
  tags     = local.common_tags
}

module "acr" {
  source = "../../modules/acr"

  name                          = local.acr_name
  resource_group_name           = module.resource_group.name
  location                      = module.resource_group.location
  sku                           = var.acr_sku
  public_network_access_enabled = true
  tags                          = local.common_tags
}

module "blob_documents" {
  source = "../../modules/blob_documents"

  account_name                    = local.storage_account_name
  resource_group_name             = module.resource_group.name
  location                        = module.resource_group.location
  container_name                  = var.storage_container_name
  replication_type                = var.storage_replication_type
  blob_soft_delete_retention_days = var.storage_blob_soft_delete_retention_days
  lifecycle_expire_days           = var.storage_lifecycle_expire_days
  tags                            = local.common_tags
}

module "service_bus_analysis" {
  source = "../../modules/service_bus_analysis"

  namespace_name      = local.servicebus_namespace_name
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
  sku                 = var.servicebus_sku
  queue_name          = var.servicebus_queue_name
  max_delivery_count  = var.servicebus_max_delivery_count
  lock_duration       = var.servicebus_lock_duration
  message_ttl         = var.servicebus_message_ttl
  tags                = local.common_tags
}

module "key_vault" {
  source = "../../modules/key_vault"

  name                          = local.key_vault_name
  resource_group_name           = module.resource_group.name
  location                      = module.resource_group.location
  sku_name                      = var.key_vault_sku_name
  soft_delete_retention_days    = var.key_vault_soft_delete_retention_days
  purge_protection_enabled      = var.key_vault_purge_protection_enabled
  public_network_access_enabled = true
  tags                          = local.common_tags
}

module "managed_identities" {
  source = "../../modules/managed_identities"
  count  = var.create_managed_identities ? 1 : 0

  project_name        = var.project_name
  environment         = var.environment
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location

  documents_container_scope_id = module.blob_documents.container_resource_manager_id
  servicebus_queue_id          = module.service_bus_analysis.queue_id
  key_vault_id                 = module.key_vault.id
  acr_id                       = module.acr.id

  tags = local.common_tags

  depends_on = [
    module.acr,
    module.blob_documents,
    module.service_bus_analysis,
    module.key_vault,
  ]
}

module "networking" {
  source = "../../modules/networking"

  project_name               = var.project_name
  environment                = var.environment
  resource_group_name        = module.resource_group.name
  location                   = module.resource_group.location
  vnet_cidr                  = var.vnet_cidr
  postgres_subnet_cidr       = var.postgres_subnet_cidr
  container_apps_subnet_cidr = var.container_apps_subnet_cidr
  tags                       = local.common_tags
}

module "postgres_flexible" {
  source = "../../modules/postgres_flexible"

  project_name        = var.project_name
  environment         = var.environment
  server_name         = local.postgres_server_name
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
  postgres_subnet_id  = module.networking.postgres_subnet_id
  private_dns_zone_id = module.networking.private_dns_zone_id
  key_vault_id        = module.key_vault.id

  postgres_version               = var.postgres_version
  sku_name                       = var.postgres_sku_name
  storage_mb                     = var.postgres_storage_mb
  backup_retention_days          = var.postgres_backup_retention_days
  admin_username                 = var.postgres_admin_username
  database_name                  = var.postgres_database_name
  availability_zone              = var.postgres_zone
  high_availability_enabled      = var.postgres_high_availability_enabled
  password_length                = var.postgres_password_length
  database_url_secret_name       = var.database_url_secret_name
  create_credentials_json_secret = var.create_postgres_credentials_json_secret

  tags = local.common_tags

  depends_on = [module.networking, module.key_vault]
}

module "container_apps_environment" {
  source = "../../modules/container_apps_environment"
  count  = var.create_container_apps_environment ? 1 : 0

  project_name             = var.project_name
  environment              = var.environment
  resource_group_name      = module.resource_group.name
  location                 = module.resource_group.location
  container_apps_subnet_id = module.networking.container_apps_subnet_id

  log_analytics_workspace_name                  = var.log_analytics_workspace_name
  container_apps_environment_name               = var.container_apps_environment_name
  log_analytics_retention_days                  = var.log_analytics_retention_days
  container_apps_internal_load_balancer_enabled = var.container_apps_internal_load_balancer_enabled
  container_apps_zone_redundancy_enabled        = var.container_apps_zone_redundancy_enabled
  container_apps_workload_profile_type          = var.container_apps_workload_profile_type

  tags = local.common_tags

  depends_on = [module.networking]
}
