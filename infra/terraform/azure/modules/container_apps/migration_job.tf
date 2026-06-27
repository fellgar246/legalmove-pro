resource "azurerm_container_app_job" "migration" {
  count = var.create_migration_job ? 1 : 0

  name                         = local.migration_job_name
  location                     = var.location
  resource_group_name          = var.resource_group_name
  container_app_environment_id = var.container_app_environment_id

  replica_timeout_in_seconds = var.migration_replica_timeout_in_seconds
  replica_retry_limit        = 0

  manual_trigger_config {
    parallelism              = 1
    replica_completion_count = 1
  }

  tags = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [var.api_managed_identity_id]
  }

  registry {
    server   = var.acr_login_server
    identity = var.api_managed_identity_id
  }

  secret {
    name                = local.database_url_secret_ref_name
    identity            = var.api_managed_identity_id
    key_vault_secret_id = var.database_url_secret_id
  }

  template {
    container {
      name   = "migrations"
      image  = local.migration_image
      cpu    = var.migration_cpu
      memory = var.migration_memory

      env {
        name        = "DATABASE_URL"
        secret_name = local.database_url_secret_ref_name
      }

      env {
        name  = "MIGRATION_DIRECTION"
        value = var.migration_direction
      }
    }
  }

  lifecycle {
    ignore_changes = [secret]
  }
}
