variable "project_name" {
  type        = string
  description = "Project identifier used in resource names."
}

variable "environment" {
  type        = string
  description = "Deployment environment name."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name."
}

variable "location" {
  type        = string
  description = "Azure region."
}

variable "container_app_environment_id" {
  type        = string
  description = "Container Apps Environment resource ID."
}

variable "acr_login_server" {
  type        = string
  description = "ACR login server hostname (e.g. myregistry.azurecr.io)."
}

variable "api_managed_identity_id" {
  type        = string
  description = "API user-assigned managed identity resource ID."
}

variable "api_managed_identity_client_id" {
  type        = string
  description = "API managed identity client ID for AZURE_CLIENT_ID."
}

variable "worker_managed_identity_id" {
  type        = string
  description = "Worker user-assigned managed identity resource ID."
}

variable "worker_managed_identity_client_id" {
  type        = string
  description = "Worker managed identity client ID for AZURE_CLIENT_ID."
}

variable "storage_account_name" {
  type        = string
  description = "Documents storage account name."
}

variable "storage_container_name" {
  type        = string
  description = "Documents blob container name."
}

variable "servicebus_namespace_name" {
  type        = string
  description = "Service Bus namespace name."
}

variable "servicebus_queue_name" {
  type        = string
  description = "Service Bus analysis queue name."
}

variable "key_vault_id" {
  type        = string
  description = "Key Vault resource ID."
}

variable "database_url_secret_id" {
  type        = string
  description = "Key Vault secret resource ID for DATABASE-URL."
}

variable "database_url_secret_name" {
  type        = string
  description = "Key Vault secret name for DATABASE-URL (used in secret reference name)."
  default     = "DATABASE-URL"
}

variable "openai_api_key_secret_name" {
  type        = string
  description = "Key Vault secret name for OPENAI-API-KEY."
  default     = "OPENAI-API-KEY"
}

variable "container_image_tag" {
  type        = string
  description = "Container image tag for API and worker."
  default     = "latest"
}

variable "api_image_name" {
  type        = string
  description = "API image repository name in ACR."
  default     = "api-go"
}

variable "worker_image_name" {
  type        = string
  description = "Worker image repository name in ACR."
  default     = "worker-ai"
}

variable "api_container_app_name" {
  type        = string
  description = "Optional API Container App name override."
  default     = null
}

variable "worker_container_app_name" {
  type        = string
  description = "Optional worker Container App name override."
  default     = null
}

variable "api_min_replicas" {
  type        = number
  description = "Minimum API replicas."
  default     = 1
}

variable "api_max_replicas" {
  type        = number
  description = "Maximum API replicas."
  default     = 2
}

variable "worker_min_replicas" {
  type        = number
  description = "Minimum worker replicas."
  default     = 1
}

variable "worker_max_replicas" {
  type        = number
  description = "Maximum worker replicas."
  default     = 1
}

variable "api_cpu" {
  type        = number
  description = "API container vCPU allocation."
  default     = 0.5
}

variable "api_memory" {
  type        = string
  description = "API container memory allocation."
  default     = "1Gi"
}

variable "worker_cpu" {
  type        = number
  description = "Worker container vCPU allocation."
  default     = 1.0
}

variable "worker_memory" {
  type        = string
  description = "Worker container memory allocation."
  default     = "2Gi"
}

variable "api_port" {
  type        = number
  description = "API container port and ingress target port."
  default     = 8080
}

variable "cors_allowed_origins" {
  type        = string
  description = "Comma-separated browser origins allowed by the API CORS middleware."
  default     = "http://localhost:3000"
}

variable "worker_use_mock_result" {
  type        = bool
  description = "When true, worker skips OPENAI-API-KEY secret reference."
  default     = false
}

variable "document_temp_dir" {
  type        = string
  description = "Worker temp directory for materialized documents."
  default     = "/tmp/legalmove-documents"
}

variable "pdf_max_bytes" {
  type        = number
  description = "Worker PDF_MAX_BYTES setting."
  default     = 20971520
}

variable "pdf_min_text_chars" {
  type        = number
  description = "Worker PDF_MIN_TEXT_CHARS setting."
  default     = 32
}

variable "worker_poll_interval_seconds" {
  type        = number
  description = "Worker poll interval between queue checks."
  default     = 5
}

variable "azure_service_bus_wait_time_seconds" {
  type        = number
  description = "Worker Service Bus long-poll wait time."
  default     = 10
}

variable "workload_profile_name" {
  type        = string
  description = "Container Apps Environment workload profile name."
  default     = "Consumption"
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to Container Apps."
  default     = {}
}

variable "create_migration_job" {
  type        = bool
  description = "Deploy a manual Container Apps Job to apply SQL migrations (Block 4.G)."
  default     = true
}

variable "migration_job_name" {
  type        = string
  description = "Optional migration Container Apps Job name override."
  default     = null
}

variable "migration_image_name" {
  type        = string
  description = "Migration runner image repository name in ACR."
  default     = "legalmove-migrations"
}

variable "migration_image_tag" {
  type        = string
  description = "Migration runner image tag in ACR."
  default     = "latest"
}

variable "migration_replica_timeout_in_seconds" {
  type        = number
  description = "Timeout for a single migration job execution."
  default     = 300
}

variable "migration_cpu" {
  type        = number
  description = "Migration job container vCPU allocation."
  default     = 0.25
}

variable "migration_memory" {
  type        = string
  description = "Migration job container memory allocation."
  default     = "0.5Gi"
}

variable "migration_direction" {
  type        = string
  description = "Default MIGRATION_DIRECTION env for the job container (up or down)."
  default     = "up"

  validation {
    condition     = contains(["up", "down"], var.migration_direction)
    error_message = "migration_direction must be up or down."
  }
}
