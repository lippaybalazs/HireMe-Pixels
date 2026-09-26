output "acr_name" {
  description = "Azure Container Registry name."
  value       = azurerm_container_registry.main.name
}

output "acr_login_server" {
  description = "Azure Container Registry login server."
  value       = azurerm_container_registry.main.login_server
}

output "postgres_host" {
  description = "PostgreSQL server hostname."
  value       = azurerm_postgresql_flexible_server.main.fqdn
}

output "postgres_database" {
  description = "PostgreSQL database name."
  value       = azurerm_postgresql_flexible_server_database.main.name
}

output "entra_client_id" {
  value     = azuread_application.main.client_id
  sensitive = true
}

output "entra_client_secret" {
  value     = azuread_application_password.main.value
  sensitive = true
}