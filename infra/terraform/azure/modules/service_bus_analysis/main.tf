resource "azurerm_servicebus_namespace" "this" {
  name                = var.namespace_name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.sku

  tags = var.tags
}

resource "azurerm_servicebus_queue" "analysis" {
  name         = var.queue_name
  namespace_id = azurerm_servicebus_namespace.this.id

  max_delivery_count  = var.max_delivery_count
  lock_duration       = var.lock_duration
  default_message_ttl = var.message_ttl

  dead_lettering_on_message_expiration = true
  requires_duplicate_detection         = false
}
