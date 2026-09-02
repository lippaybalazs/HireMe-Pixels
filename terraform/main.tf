terraform {
  cloud {
    organization = "lippaybalazs-HireMe-Pixels"

    workspaces {
      name = "development" // Keep development default, CD will handle production
    }
  }

  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = "hireme-pixels-${var.environment}"
  location = var.location
}

resource "azurerm_container_registry" "main" {
  name                = "hiremepixels${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.acr_sku
}