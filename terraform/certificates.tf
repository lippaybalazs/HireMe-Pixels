resource "azurerm_container_app_environment_managed_certificate" "frontend" {
  count = var.deploy_apps ? 1 : 0

  name                         = "frontend-managed-cert"
  container_app_environment_id = azurerm_container_app_environment.main.id
  subject_name                 = var.frontend_hostname
  domain_control_validation    = "CNAME"

  depends_on = [
    azurerm_container_app_custom_domain.frontend,
  ]
}

resource "azurerm_container_app_environment_managed_certificate" "backend" {
  count = var.deploy_apps ? 1 : 0

  name                         = "backend-managed-cert"
  container_app_environment_id = azurerm_container_app_environment.main.id
  subject_name                 = var.backend_hostname
  domain_control_validation    = "CNAME"

  depends_on = [
    azurerm_container_app_custom_domain.backend,
  ]
}

resource "azapi_resource_action" "frontend_custom_domain_binding" {
  count = var.deploy_apps ? 1 : 0

  type        = "Microsoft.App/containerApps@2023-05-01"
  resource_id = azurerm_container_app.frontend[0].id
  method      = "PATCH"

  body = {
    properties = {
      configuration = {
        ingress = {
          customDomains = [
            {
              name          = var.frontend_hostname
              bindingType   = "SniEnabled"
              certificateId = azurerm_container_app_environment_managed_certificate.frontend[0].id
            }
          ]
        }
      }
    }
  }

  response_export_values = ["*"]

  depends_on = [
    azurerm_container_app_environment_managed_certificate.frontend,
  ]
}

resource "azapi_resource_action" "backend_custom_domain_binding" {
  count = var.deploy_apps ? 1 : 0

  type        = "Microsoft.App/containerApps@2023-05-01"
  resource_id = azurerm_container_app.backend[0].id
  method      = "PATCH"

  body = {
    properties = {
      configuration = {
        ingress = {
          customDomains = [
            {
              name          = var.backend_hostname
              bindingType   = "SniEnabled"
              certificateId = azurerm_container_app_environment_managed_certificate.backend[0].id
            }
          ]
        }
      }
    }
  }

  response_export_values = ["*"]

  depends_on = [
    azurerm_container_app_environment_managed_certificate.backend,
  ]
}

resource "azapi_resource_action" "frontend_custom_domain_binding_destroy" {
  count = var.deploy_apps ? 1 : 0

  type        = "Microsoft.App/containerApps@2023-05-01"
  resource_id = azurerm_container_app.frontend[0].id
  method      = "PATCH"

  body = {
    properties = {
      configuration = {
        ingress = {
          customDomains = []
        }
      }
    }
  }

  response_export_values = ["*"]

  when = "destroy"

  depends_on = [
    azapi_resource_action.frontend_custom_domain_binding,
  ]
}

resource "azapi_resource_action" "backend_custom_domain_binding_destroy" {
  count = var.deploy_apps ? 1 : 0

  type        = "Microsoft.App/containerApps@2023-05-01"
  resource_id = azurerm_container_app.backend[0].id
  method      = "PATCH"

  body = {
    properties = {
      configuration = {
        ingress = {
          customDomains = []
        }
      }
    }
  }

  response_export_values = ["*"]

  when = "destroy"

  depends_on = [
    azapi_resource_action.backend_custom_domain_binding,
  ]
}