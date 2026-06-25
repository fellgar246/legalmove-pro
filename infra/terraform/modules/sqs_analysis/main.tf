resource "aws_sqs_queue" "analysis_dlq" {
  name                      = "${var.project_name}-${var.environment}-analysis-jobs-dlq"
  message_retention_seconds = var.message_retention_seconds

  tags = merge(var.tags, {
    Purpose = "analysis-jobs-dlq"
  })
}

resource "aws_sqs_queue" "analysis" {
  name                       = "${var.project_name}-${var.environment}-analysis-jobs"
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds
  receive_wait_time_seconds  = var.receive_wait_time_seconds

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.analysis_dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = merge(var.tags, {
    Purpose = "analysis-jobs"
  })
}
