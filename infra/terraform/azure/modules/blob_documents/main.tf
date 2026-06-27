resource "azurerm_storage_account" "this" {
  name                     = var.account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = var.replication_type
  min_tls_version          = "TLS1_2"

  allow_nested_items_to_be_public = false
  # Terraform provider needs shared key access to read the blob data plane after create.
  # Runtime API/worker use managed identity only (shared_access_key_enabled does not affect MI auth).
  shared_access_key_enabled = true

  blob_properties {
    delete_retention_policy {
      days = var.blob_soft_delete_retention_days
    }

    container_delete_retention_policy {
      days = var.blob_soft_delete_retention_days
    }
  }

  tags = var.tags
}

resource "azurerm_storage_container" "documents" {
  name                  = var.container_name
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}

resource "azurerm_storage_management_policy" "this" {
  count = var.lifecycle_expire_days > 0 ? 1 : 0

  storage_account_id = azurerm_storage_account.this.id

  rule {
    name    = "expire-dev-documents"
    enabled = true

    filters {
      prefix_match = [""]
      blob_types   = ["blockBlob"]
    }

    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = var.lifecycle_expire_days
      }
    }
  }
}
