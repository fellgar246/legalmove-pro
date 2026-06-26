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

  tags = local.common_tags

  depends_on = [
    module.blob_documents,
    module.service_bus_analysis,
    module.key_vault,
  ]
}
