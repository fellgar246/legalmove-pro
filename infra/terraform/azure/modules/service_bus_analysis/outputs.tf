output "namespace_name" {
  description = "Service Bus namespace name."
  value       = azurerm_servicebus_namespace.this.name
}

output "namespace_id" {
  description = "Service Bus namespace resource ID."
  value       = azurerm_servicebus_namespace.this.id
}

output "queue_name" {
  description = "Analysis jobs queue name."
  value       = azurerm_servicebus_queue.analysis.name
}

output "queue_id" {
  description = "Analysis jobs queue resource ID."
  value       = azurerm_servicebus_queue.analysis.id
}

output "dead_letter_queue_path" {
  description = "Relative path of the built-in dead-letter subqueue for the analysis queue."
  value       = "${azurerm_servicebus_queue.analysis.name}/$deadletterqueue"
}
