output "vpc_id" {
  description = "ID of the LegalMove Pro VPC."
  value       = aws_vpc.this.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC."
  value       = aws_vpc.this.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of public subnets for future ALB."
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of private subnets for future ECS and RDS."
  value       = aws_subnet.private[*].id
}

output "availability_zones" {
  description = "Availability zones used by the subnets."
  value       = local.azs
}

output "nat_gateway_enabled" {
  description = "Whether a NAT gateway was created for private subnet egress."
  value       = var.enable_nat_gateway
}

output "nat_gateway_id" {
  description = "NAT gateway ID when enabled."
  value       = try(aws_nat_gateway.this[0].id, null)
}

output "alb_security_group_id" {
  description = "Security group ID for the future public ALB."
  value       = aws_security_group.alb.id
}

output "api_security_group_id" {
  description = "Security group ID for the future API ECS service."
  value       = aws_security_group.api.id
}

output "worker_security_group_id" {
  description = "Security group ID for the future worker ECS service."
  value       = aws_security_group.worker.id
}

output "rds_security_group_id" {
  description = "Security group ID attached to RDS."
  value       = aws_security_group.rds.id
}
