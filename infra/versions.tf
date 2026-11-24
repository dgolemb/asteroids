terraform {
  required_version = "~> 1.15"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-AI-native-asteroids-training"
    storage_account_name = "terraformasteroids"
    container_name       = "tfstate"
    key                  = "asteroids.tfstate"
    use_azuread_auth     = true
  }
}
