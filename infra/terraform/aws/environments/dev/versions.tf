terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Local state for the preliminary dev foundation.
  # Block 4.x can migrate to remote state (S3 + DynamoDB) before shared environments.
  backend "local" {
    path = "terraform.tfstate"
  }
}
