data "azurerm_client_config" "current" {}

data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}

data "azurerm_user_assigned_identity" "acr_pull" {
  name                = var.managed_identity_name
  resource_group_name = data.azurerm_resource_group.main.name
}

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_service_plan" "main" {
  name                = "asp-${var.project_name}"
  resource_group_name = data.azurerm_resource_group.main.name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "F1"
}

resource "azurerm_linux_web_app" "main" {
  name                = "app-${var.project_name}-${random_string.suffix.result}"
  resource_group_name = data.azurerm_resource_group.main.name
  location            = var.location
  service_plan_id     = azurerm_service_plan.main.id
  https_only          = true

  identity {
    type         = "UserAssigned"
    identity_ids = [data.azurerm_user_assigned_identity.acr_pull.id]
  }

  site_config {
    always_on                                     = false
    container_registry_use_managed_identity       = true
    container_registry_managed_identity_client_id = data.azurerm_user_assigned_identity.acr_pull.client_id

    application_stack {
      docker_image_name   = var.docker_image
      docker_registry_url = "https://${var.acr_login_server}"
    }
  }

  app_settings = {
    WEBSITES_PORT = "80"
  }
}
