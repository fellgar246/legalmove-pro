output "ecs_cluster_id" {
  description = "ECS cluster ID."
  value       = aws_ecs_cluster.this.id
}

output "ecs_cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.this.name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN."
  value       = aws_ecs_cluster.this.arn
}

output "api_task_definition_arn" {
  description = "ARN of the API ECS task definition (no service yet)."
  value       = aws_ecs_task_definition.api.arn
}

output "worker_task_definition_arn" {
  description = "ARN of the worker ECS task definition (no service yet)."
  value       = aws_ecs_task_definition.worker.arn
}

output "api_task_role_arn" {
  description = "IAM task role ARN for the API ECS tasks."
  value       = aws_iam_role.api_task.arn
}

output "worker_task_role_arn" {
  description = "IAM task role ARN for the worker ECS tasks."
  value       = aws_iam_role.worker_task.arn
}

output "ecs_execution_role_arn" {
  description = "IAM execution role ARN for ECS task startup (ECR, logs, secrets)."
  value       = aws_iam_role.ecs_execution.arn
}

output "api_log_group_name" {
  description = "CloudWatch log group for API ECS tasks."
  value       = aws_cloudwatch_log_group.api.name
}

output "worker_log_group_name" {
  description = "CloudWatch log group for worker ECS tasks."
  value       = aws_cloudwatch_log_group.worker.name
}
