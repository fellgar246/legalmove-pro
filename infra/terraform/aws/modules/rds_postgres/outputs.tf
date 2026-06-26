output "db_instance_id" {
  description = "RDS instance identifier."
  value       = aws_db_instance.this.id
}

output "db_instance_endpoint" {
  description = "RDS connection endpoint (hostname only)."
  value       = aws_db_instance.this.address
}

output "db_instance_port" {
  description = "RDS PostgreSQL port."
  value       = aws_db_instance.this.port
}

output "db_name" {
  description = "Initial database name."
  value       = var.db_name
}

output "db_username" {
  description = "Master database username."
  value       = var.db_username
  sensitive   = true
}

output "db_subnet_group_name" {
  description = "DB subnet group name."
  value       = aws_db_subnet_group.this.name
}

output "db_parameter_group_name" {
  description = "DB parameter group name."
  value       = aws_db_parameter_group.this.name
}

output "db_secret_arn" {
  description = "Secrets Manager ARN containing database credentials and database_url."
  value       = aws_secretsmanager_secret.database.arn
}

output "database_url_secret_arn" {
  description = "Alias for db_secret_arn; the secret JSON includes database_url."
  value       = aws_secretsmanager_secret.database.arn
}
