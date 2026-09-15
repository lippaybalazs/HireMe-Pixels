resource "azurerm_dns_cname_record" "frontend" {
  count = var.deploy_apps ? 1 : 0

  name                = trimsuffix(var.frontend_hostname, ".lippay.ro")
  zone_name           = data.azurerm_dns_zone.lippay.name
  resource_group_name = data.azurerm_dns_zone.lippay.resource_group_name
  ttl                 = 300

  record = azurerm_container_app.frontend[0].ingress[0].fqdn
}

resource "azurerm_dns_cname_record" "backend" {
  count = var.deploy_apps ? 1 : 0

  name                = trimsuffix(var.backend_hostname, ".lippay.ro")
  zone_name           = data.azurerm_dns_zone.lippay.name
  resource_group_name = data.azurerm_dns_zone.lippay.resource_group_name
  ttl                 = 300

  record = azurerm_container_app.backend[0].ingress[0].fqdn
}

resource "azurerm_dns_txt_record" "frontend_verification" {
  count = var.deploy_apps ? 1 : 0

  name                = "asuid.${trimsuffix(var.frontend_hostname, ".lippay.ro")}"
  zone_name           = data.azurerm_dns_zone.lippay.name
  resource_group_name = data.azurerm_dns_zone.lippay.resource_group_name
  ttl                 = 300

  record {
    value = azurerm_container_app.frontend[0].custom_domain_verification_id
  }
}

resource "azurerm_dns_txt_record" "backend_verification" {
  count = var.deploy_apps ? 1 : 0

  name                = "asuid.${trimsuffix(var.backend_hostname, ".lippay.ro")}"
  zone_name           = data.azurerm_dns_zone.lippay.name
  resource_group_name = data.azurerm_dns_zone.lippay.resource_group_name
  ttl                 = 300

  record {
    value = azurerm_container_app.backend[0].custom_domain_verification_id
  }
}

resource "azurerm_container_app_custom_domain" "frontend" {
  count = var.deploy_apps ? 1 : 0

  name                     = var.frontend_hostname
  container_app_id         = azurerm_container_app.frontend[0].id
  certificate_binding_type = "Disabled"

  depends_on = [
    azurerm_dns_cname_record.frontend,
    azurerm_dns_txt_record.frontend_verification,
  ]

  lifecycle {
    ignore_changes = [
      certificate_binding_type,
      container_app_environment_certificate_id,
    ]
  }
}

resource "azurerm_container_app_custom_domain" "backend" {
  count = var.deploy_apps ? 1 : 0

  name                     = var.backend_hostname
  container_app_id         = azurerm_container_app.backend[0].id
  certificate_binding_type = "Disabled"

  depends_on = [
    azurerm_dns_cname_record.backend,
    azurerm_dns_txt_record.backend_verification,
  ]

  lifecycle {
    ignore_changes = [
      certificate_binding_type,
      container_app_environment_certificate_id,
    ]
  }
}