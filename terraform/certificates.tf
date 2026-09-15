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