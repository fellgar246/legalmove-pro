variable "location" {
  type        = string
  description = "Azure region for all foundation resources."
  default     = "centralus"
}

variable "project_name" {
  type        = string
  description = "Project identifier used in resource names and tags."
  default     = "legalmove-pro"
}

variable "environment" {
  type        = string
  description = "Deployment environment name."
  default     = "dev"
}

variable "resource_group_name" {
  type        = string
  description = "Optional resource group name override. Defaults to rg-<project>-<environment>."
  default     = null
}

variable "acr_name" {
  type        = string
  description = "Optional ACR name override (5-50 alphanumeric, globally unique)."
  default     = null
}

variable "acr_sku" {
  type        = string
  description = "ACR SKU."
  default     = "Basic"
}

variable "storage_account_name" {
  type        = string
  description = "Optional storage account name override (3-24 lowercase alphanumeric, globally unique)."
  default     = null
}

variable "storage_container_name" {
  type        = string
  description = "Private blob container for uploaded documents."
  default     = "documents"
}

variable "storage_replication_type" {
  type        = string
  description = "Storage account replication type."
  default     = "LRS"
}

variable "storage_blob_soft_delete_retention_days" {
  type        = number
  description = "Blob soft-delete retention in days."
  default     = 7
}

variable "storage_lifecycle_expire_days" {
  type        = number
  description = "Expire dev document blobs after N days. Set to 0 to disable."
  default     = 90
}

variable "servicebus_namespace_name" {
  type        = string
  description = "Optional Service Bus namespace name override (6-50 chars, globally unique)."
  default     = null
}

variable "servicebus_sku" {
  type        = string
  description = "Service Bus namespace SKU. Standard supports queue DLQ and future features."
  default     = "Standard"
}

variable "servicebus_queue_name" {
  type        = string
  description = "Analysis jobs queue name."
  default     = "analysis-jobs"
}

variable "servicebus_max_delivery_count" {
  type        = number
  description = "Delivery attempts before a message is dead-lettered."
  default     = 5
}

variable "servicebus_lock_duration" {
  type        = string
  description = "ISO 8601 lock duration for received messages."
  default     = "PT1M"
}

variable "servicebus_message_ttl" {
  type        = string
  description = "ISO 8601 default message TTL."
  default     = "P4D"
}

variable "key_vault_name" {
  type        = string
  description = "Optional Key Vault name override (3-24 alphanumeric/hyphen, globally unique)."
  default     = null
}

variable "key_vault_sku_name" {
  type        = string
  description = "Key Vault SKU."
  default     = "standard"
}

variable "key_vault_soft_delete_retention_days" {
  type        = number
  description = "Key Vault soft-delete retention in days."
  default     = 7
}

variable "key_vault_purge_protection_enabled" {
  type        = bool
  description = "Enable purge protection on Key Vault. Default false for dev."
  default     = false
}

variable "create_managed_identities" {
  type        = bool
  description = "Create user-assigned managed identities and RBAC for future Container Apps."
  default     = true
}

variable "vnet_cidr" {
  type        = string
  description = "Address space for the LegalMove Pro VNet."
  default     = "10.30.0.0/16"
}

variable "postgres_subnet_cidr" {
  type        = string
  description = "Delegated subnet for PostgreSQL Flexible Server."
  default     = "10.30.11.0/24"
}

variable "container_apps_subnet_cidr" {
  type        = string
  description = "Subnet reserved for future Container Apps Environment (/23 recommended)."
  default     = "10.30.20.0/23"
}

variable "postgres_server_name" {
  type        = string
  description = "Optional PostgreSQL Flexible Server name override (3-63 chars, globally unique)."
  default     = null
}

variable "postgres_version" {
  type        = string
  description = "PostgreSQL major version."
  default     = "16"
}

variable "postgres_sku_name" {
  type        = string
  description = "Flexible Server SKU."
  default     = "B_Standard_B1ms"
}

variable "postgres_storage_mb" {
  type        = number
  description = "Allocated storage in megabytes."
  default     = 32768
}

variable "postgres_backup_retention_days" {
  type        = number
  description = "Backup retention in days."
  default     = 7
}

variable "postgres_admin_username" {
  type        = string
  description = "PostgreSQL administrator login."
  default     = "legalmove"
}

variable "postgres_database_name" {
  type        = string
  description = "Application database name."
  default     = "legalmove"
}

variable "postgres_zone" {
  type        = string
  description = "Optional availability zone for PostgreSQL (1, 2, or 3)."
  default     = null
}

variable "postgres_high_availability_enabled" {
  type        = bool
  description = "Enable zone-redundant high availability."
  default     = false
}

variable "postgres_password_length" {
  type        = number
  description = "Length of the generated administrator password."
  default     = 32
}

variable "database_url_secret_name" {
  type        = string
  description = "Key Vault secret name for DATABASE_URL."
  default     = "DATABASE-URL"
}

variable "create_postgres_credentials_json_secret" {
  type        = bool
  description = "Also store DATABASE-CREDENTIALS JSON in Key Vault."
  default     = false
}

variable "create_container_apps_environment" {
  type        = bool
  description = "Create Log Analytics workspace and Container Apps Environment (Block 4.D)."
  default     = true
}

variable "log_analytics_workspace_name" {
  type        = string
  description = "Optional Log Analytics workspace name override."
  default     = null
}

variable "container_apps_environment_name" {
  type        = string
  description = "Optional Container Apps Environment name override."
  default     = null
}

variable "log_analytics_retention_days" {
  type        = number
  description = "Log Analytics workspace retention in days."
  default     = 30
}

variable "container_apps_internal_load_balancer_enabled" {
  type        = bool
  description = "Use an internal load balancer on the Container Apps Environment."
  default     = false
}

variable "container_apps_zone_redundancy_enabled" {
  type        = bool
  description = "Enable zone redundancy for the Container Apps Environment."
  default     = false
}

variable "container_apps_workload_profile_type" {
  type        = string
  description = "Workload profile type for VNet-integrated Container Apps Environment."
  default     = "Consumption"
}

variable "create_container_apps" {
  type        = bool
  description = "Deploy API and worker Container Apps (Block 4.F). Requires CAE, identities, and images in ACR."
  default     = true
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
  description = "When true, worker skips OPENAI-API-KEY Key Vault reference."
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

variable "openai_api_key_secret_name" {
  type        = string
  description = "Key Vault secret name for OPENAI-API-KEY."
  default     = "OPENAI-API-KEY"
}

variable "create_migration_job" {
  type        = bool
  description = "Deploy manual Container Apps Job for SQL migrations (Block 4.G). Requires Container Apps."
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
  description = "Default MIGRATION_DIRECTION for the migration job (up or down)."
  default     = "up"
}
