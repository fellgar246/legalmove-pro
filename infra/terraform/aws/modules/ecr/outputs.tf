output "api_repository_url" {
  description = "URL of the api-go ECR repository."
  value       = aws_ecr_repository.api.repository_url
}

output "worker_repository_url" {
  description = "URL of the worker-ai ECR repository."
  value       = aws_ecr_repository.worker.repository_url
}

output "api_repository_arn" {
  description = "ARN of the api-go ECR repository."
  value       = aws_ecr_repository.api.arn
}

output "worker_repository_arn" {
  description = "ARN of the worker-ai ECR repository."
  value       = aws_ecr_repository.worker.arn
}
