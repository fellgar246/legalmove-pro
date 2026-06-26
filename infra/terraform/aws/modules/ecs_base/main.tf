locals {
  name_prefix = "${var.project_name}-${var.environment}"

  api_log_group_name    = "/ecs/${var.project_name}/${var.environment}/api-go"
  worker_log_group_name = "/ecs/${var.project_name}/${var.environment}/worker-ai"

  secret_arns = compact([
    var.db_secret_arn,
    var.openai_api_key_secret_arn,
  ])

  api_secrets = [
    {
      name      = "DATABASE_URL"
      valueFrom = "${var.db_secret_arn}:database_url::"
    },
  ]

  worker_secrets = concat(
    [
      {
        name      = "DATABASE_URL"
        valueFrom = "${var.db_secret_arn}:database_url::"
      },
    ],
    var.openai_api_key_secret_arn != null ? [
      {
        name      = "OPENAI_API_KEY"
        valueFrom = var.openai_api_key_secret_arn
      },
    ] : [],
  )
}

resource "aws_ecs_cluster" "this" {
  name = local.name_prefix

  setting {
    name  = "containerInsights"
    value = "disabled"
  }

  tags = merge(var.tags, {
    Name = local.name_prefix
  })
}

resource "aws_cloudwatch_log_group" "api" {
  name              = local.api_log_group_name
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name    = local.api_log_group_name
    Service = "api-go"
  })
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = local.worker_log_group_name
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name    = local.worker_log_group_name
    Service = "worker-ai"
  })
}

resource "aws_iam_role" "ecs_execution" {
  name = "${local.name_prefix}-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      },
    ]
  })

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-ecs-execution"
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name = "${local.name_prefix}-ecs-execution-secrets"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadTaskSecrets"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
        ]
        Resource = local.secret_arns
      },
    ]
  })
}

resource "aws_iam_role" "api_task" {
  name = "${local.name_prefix}-api-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      },
    ]
  })

  tags = merge(var.tags, {
    Name    = "${local.name_prefix}-api-task"
    Service = "api-go"
  })
}

resource "aws_iam_role_policy_attachment" "api_task_service" {
  role       = aws_iam_role.api_task.name
  policy_arn = var.api_policy_arn
}

resource "aws_iam_role" "worker_task" {
  name = "${local.name_prefix}-worker-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      },
    ]
  })

  tags = merge(var.tags, {
    Name    = "${local.name_prefix}-worker-task"
    Service = "worker-ai"
  })
}

resource "aws_iam_role_policy_attachment" "worker_task_service" {
  role       = aws_iam_role.worker_task.name
  policy_arn = var.worker_policy_arn
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.ecs_api_cpu)
  memory                   = tostring(var.ecs_api_memory)
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.api_task.arn

  container_definitions = jsonencode([
    {
      name      = "api-go"
      image     = var.api_image
      essential = true
      portMappings = [
        {
          containerPort = var.api_container_port
          hostPort      = var.api_container_port
          protocol      = "tcp"
        },
      ]
      environment = [
        { name = "APP_ENV", value = var.environment },
        { name = "API_PORT", value = tostring(var.api_container_port) },
        { name = "STORAGE_PROVIDER", value = "s3" },
        { name = "QUEUE_PROVIDER", value = "sqs" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "S3_BUCKET", value = var.s3_bucket },
        { name = "S3_PREFIX", value = var.s3_prefix },
        { name = "SQS_QUEUE_URL", value = var.sqs_queue_url },
      ]
      secrets = local.api_secrets
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    },
  ])

  tags = merge(var.tags, {
    Name    = "${local.name_prefix}-api"
    Service = "api-go"
  })
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.name_prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.ecs_worker_cpu)
  memory                   = tostring(var.ecs_worker_memory)
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.worker_task.arn

  container_definitions = jsonencode([
    {
      name      = "worker-ai"
      image     = var.worker_image
      essential = true
      environment = [
        { name = "APP_ENV", value = var.environment },
        { name = "QUEUE_PROVIDER", value = "sqs" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "S3_BUCKET", value = var.s3_bucket },
        { name = "S3_PREFIX", value = var.s3_prefix },
        { name = "SQS_QUEUE_URL", value = var.sqs_queue_url },
        { name = "SQS_WAIT_TIME_SECONDS", value = tostring(var.sqs_wait_time_seconds) },
        { name = "SQS_VISIBILITY_TIMEOUT", value = tostring(var.sqs_visibility_timeout) },
        { name = "DOCUMENT_TEMP_DIR", value = var.document_temp_dir },
        { name = "WORKER_USE_MOCK_RESULT", value = tostring(var.worker_use_mock_result) },
        { name = "PDF_MAX_BYTES", value = tostring(var.pdf_max_bytes) },
        { name = "PDF_MIN_TEXT_CHARS", value = tostring(var.pdf_min_text_chars) },
      ]
      secrets = local.worker_secrets
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.worker.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    },
  ])

  tags = merge(var.tags, {
    Name    = "${local.name_prefix}-worker"
    Service = "worker-ai"
  })
}
