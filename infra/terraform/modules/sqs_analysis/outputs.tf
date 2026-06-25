output "analysis_queue_url" {
  description = "URL of the main analysis jobs SQS queue."
  value       = aws_sqs_queue.analysis.url
}

output "analysis_queue_arn" {
  description = "ARN of the main analysis jobs SQS queue."
  value       = aws_sqs_queue.analysis.arn
}

output "analysis_dlq_url" {
  description = "URL of the analysis jobs dead-letter queue."
  value       = aws_sqs_queue.analysis_dlq.url
}

output "analysis_dlq_arn" {
  description = "ARN of the analysis jobs dead-letter queue."
  value       = aws_sqs_queue.analysis_dlq.arn
}
