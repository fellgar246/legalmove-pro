locals {
  name_prefix = "${var.project_name}-${var.environment}"

  api_container_app_name = coalesce(
    var.api_container_app_name,
    "ca-api-${local.name_prefix}",
  )

  worker_container_app_name = coalesce(
    var.worker_container_app_name,
    "ca-worker-${local.name_prefix}",
  )

  api_image    = "${var.acr_login_server}/${var.api_image_name}:${var.container_image_tag}"
  worker_image = "${var.acr_login_server}/${var.worker_image_name}:${var.container_image_tag}"

  database_url_secret_ref_name   = "database-url"
  openai_api_key_secret_ref_name = "openai-api-key"

  openai_secret_id = "${var.key_vault_id}/secrets/${var.openai_api_key_secret_name}"
}

resource "azurerm_container_app" "api" {
  name                         = local.api_container_app_name
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  workload_profile_name        = var.workload_profile_name

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

  ingress {
    external_enabled           = true
    target_port                = var.api_port
    transport                  = "auto"
    allow_insecure_connections = false

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = var.api_min_replicas
    max_replicas = var.api_max_replicas

    container {
      name   = "api"
      image  = local.api_image
      cpu    = var.api_cpu
      memory = var.api_memory

      liveness_probe {
        transport = "HTTP"
        port      = var.api_port
        path      = "/health"
      }

      readiness_probe {
        transport = "HTTP"
        port      = var.api_port
        path      = "/health"
      }

      env {
        name  = "APP_ENV"
        value = var.environment
      }

      env {
        name  = "API_PORT"
        value = tostring(var.api_port)
      }

      env {
        name  = "STORAGE_PROVIDER"
        value = "azure_blob"
      }

      env {
        name  = "QUEUE_PROVIDER"
        value = "azure_service_bus"
      }

      env {
        name  = "AZURE_STORAGE_ACCOUNT_NAME"
        value = var.storage_account_name
      }

      env {
        name  = "AZURE_STORAGE_CONTAINER_NAME"
        value = var.storage_container_name
      }

      env {
        name  = "AZURE_SERVICE_BUS_NAMESPACE"
        value = var.servicebus_namespace_name
      }

      env {
        name  = "AZURE_SERVICE_BUS_QUEUE_NAME"
        value = var.servicebus_queue_name
      }

      env {
        name  = "AZURE_CLIENT_ID"
        value = var.api_managed_identity_client_id
      }

      env {
        name        = "DATABASE_URL"
        secret_name = local.database_url_secret_ref_name
      }
    }
  }

  lifecycle {
    ignore_changes = [secret]
  }
}

resource "azurerm_container_app" "worker" {
  name                         = local.worker_container_app_name
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  workload_profile_name        = var.workload_profile_name

  tags = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [var.worker_managed_identity_id]
  }

  registry {
    server   = var.acr_login_server
    identity = var.worker_managed_identity_id
  }

  secret {
    name                = local.database_url_secret_ref_name
    identity            = var.worker_managed_identity_id
    key_vault_secret_id = var.database_url_secret_id
  }

  dynamic "secret" {
    for_each = var.worker_use_mock_result ? [] : [1]
    content {
      name                = local.openai_api_key_secret_ref_name
      identity            = var.worker_managed_identity_id
      key_vault_secret_id = local.openai_secret_id
    }
  }

  template {
    min_replicas = var.worker_min_replicas
    max_replicas = var.worker_max_replicas

    container {
      name   = "worker"
      image  = local.worker_image
      cpu    = var.worker_cpu
      memory = var.worker_memory

      env {
        name  = "QUEUE_PROVIDER"
        value = "azure_service_bus"
      }

      env {
        name  = "AZURE_STORAGE_ACCOUNT_NAME"
        value = var.storage_account_name
      }

      env {
        name  = "AZURE_STORAGE_CONTAINER_NAME"
        value = var.storage_container_name
      }

      env {
        name  = "AZURE_SERVICE_BUS_NAMESPACE"
        value = var.servicebus_namespace_name
      }

      env {
        name  = "AZURE_SERVICE_BUS_QUEUE_NAME"
        value = var.servicebus_queue_name
      }

      env {
        name  = "AZURE_SERVICE_BUS_WAIT_TIME_SECONDS"
        value = tostring(var.azure_service_bus_wait_time_seconds)
      }

      env {
        name  = "AZURE_CLIENT_ID"
        value = var.worker_managed_identity_client_id
      }

      env {
        name  = "DOCUMENT_TEMP_DIR"
        value = var.document_temp_dir
      }

      env {
        name  = "PDF_MAX_BYTES"
        value = tostring(var.pdf_max_bytes)
      }

      env {
        name  = "PDF_MIN_TEXT_CHARS"
        value = tostring(var.pdf_min_text_chars)
      }

      env {
        name  = "WORKER_USE_MOCK_RESULT"
        value = var.worker_use_mock_result ? "true" : "false"
      }

      env {
        name  = "WORKER_POLL_INTERVAL_SECONDS"
        value = tostring(var.worker_poll_interval_seconds)
      }

      env {
        name        = "DATABASE_URL"
        secret_name = local.database_url_secret_ref_name
      }

      dynamic "env" {
        for_each = var.worker_use_mock_result ? [] : [1]
        content {
          name        = "OPENAI_API_KEY"
          secret_name = local.openai_api_key_secret_ref_name
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [secret]
  }
}
