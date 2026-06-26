output "api_policy_arn" {
  description = "ARN of the IAM policy to attach to the future API ECS task role."
  value       = aws_iam_policy.api.arn
}

output "worker_policy_arn" {
  description = "ARN of the IAM policy to attach to the future worker ECS task role."
  value       = aws_iam_policy.worker.arn
}
