terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Local state for the preliminary dev foundation.
  # Migrate to azurerm remote backend before shared environments.
  backend "local" {
    path = "terraform.tfstate"
  }
}
