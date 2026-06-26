locals {
  normalized_prefix = trim(var.s3_object_prefix, "/")

  s3_object_arns = local.normalized_prefix == "" ? [
    "${var.documents_bucket_arn}/*",
    ] : [
    "${var.documents_bucket_arn}/${local.normalized_prefix}/*",
  ]

  s3_list_prefixes = local.normalized_prefix == "" ? ["*"] : [
    "${local.normalized_prefix}/*",
    "${local.normalized_prefix}",
  ]
}

resource "aws_iam_policy" "api" {
  name        = "${var.project_name}-${var.environment}-api"
  description = "Minimal S3 and SQS permissions for the LegalMove Pro API task role."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ListDocumentsBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
        ]
        Resource = var.documents_bucket_arn
        Condition = {
          StringLike = {
            "s3:prefix" = local.s3_list_prefixes
          }
        }
      },
      {
        Sid    = "ReadWriteDocuments"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
        ]
        Resource = local.s3_object_arns
      },
      {
        Sid    = "PublishAnalysisJobs"
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = var.analysis_queue_arn
      },
    ]
  })

  tags = merge(var.tags, {
    Service = "api-go"
  })
}

resource "aws_iam_policy" "worker" {
  name        = "${var.project_name}-${var.environment}-worker"
  description = "Minimal S3 and SQS permissions for the LegalMove Pro worker task role."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ListDocumentsBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
        ]
        Resource = var.documents_bucket_arn
        Condition = {
          StringLike = {
            "s3:prefix" = local.s3_list_prefixes
          }
        }
      },
      {
        Sid    = "ReadDocuments"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
        ]
        Resource = local.s3_object_arns
      },
      {
        Sid    = "ConsumeAnalysisJobs"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:ChangeMessageVisibility",
          "sqs:GetQueueAttributes",
        ]
        Resource = var.analysis_queue_arn
      },
    ]
  })

  tags = merge(var.tags, {
    Service = "worker-ai"
  })
}
