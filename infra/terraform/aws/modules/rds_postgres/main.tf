locals {
  name_prefix      = "${var.project_name}-${var.environment}"
  parameter_family = "postgres${split(".", var.db_engine_version)[0]}"
  secret_name      = "${var.project_name}/${var.environment}/database"
}

resource "random_password" "master" {
  length  = 32
  special = true

  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_db_subnet_group" "this" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-db-subnet-group"
  })
}

resource "aws_db_parameter_group" "this" {
  name   = "${local.name_prefix}-postgres"
  family = local.parameter_family

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-postgres-params"
  })
}

resource "aws_db_instance" "this" {
  identifier = "${local.name_prefix}-postgres"

  engine         = "postgres"
  engine_version = var.db_engine_version
  instance_class = var.db_instance_class

  db_name  = var.db_name
  username = var.db_username
  password = random_password.master.result

  allocated_storage = var.db_allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = var.security_group_ids
  parameter_group_name   = aws_db_parameter_group.this.name
  publicly_accessible    = false
  multi_az               = false

  backup_retention_period = var.db_backup_retention_period
  deletion_protection     = var.db_deletion_protection
  skip_final_snapshot     = var.db_skip_final_snapshot
  apply_immediately       = var.apply_immediately

  auto_minor_version_upgrade = true
  copy_tags_to_snapshot      = true

  tags = merge(var.tags, {
    Name    = "${local.name_prefix}-postgres"
    Service = "postgres"
  })
}

resource "aws_secretsmanager_secret" "database" {
  name        = local.secret_name
  description = "LegalMove Pro PostgreSQL credentials and connection details."

  tags = merge(var.tags, {
    Name    = "${local.name_prefix}-database-secret"
    Service = "postgres"
  })
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id

  secret_string = jsonencode({
    username     = var.db_username
    password     = random_password.master.result
    host         = aws_db_instance.this.address
    port         = aws_db_instance.this.port
    dbname       = var.db_name
    engine       = "postgres"
    database_url = "postgres://${var.db_username}:${urlencode(random_password.master.result)}@${aws_db_instance.this.address}:${aws_db_instance.this.port}/${var.db_name}?sslmode=require"
  })
}
