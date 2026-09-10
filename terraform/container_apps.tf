resource "azurerm_log_analytics_workspace" "container_apps" {
  name                = "hireme-pixels-${var.environment}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  sku               = "PerGB2018"
  retention_in_days = 30
}

resource "azurerm_container_app_environment" "main" {
  name                       = "hireme-pixels-${var.environment}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  logs_destination           = "log-analytics"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.container_apps.id
}

resource "azurerm_container_app" "backend" {
  count = var.deploy_apps ? 1 : 0

  name                         = "hp-${var.environment}-backend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  secret {
    name  = "db-password"
    value = var.postgres_admin_password
  }

  template {
    container {
      name   = "backend"
      image  = "${azurerm_container_registry.main.login_server}/hireme-pixels-backend:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "DB_HOST"
        value = azurerm_postgresql_flexible_server.main.fqdn
      }

      env {
        name  = "DB_PORT"
        value = "5432"
      }

      env {
        name  = "DB_NAME"
        value = azurerm_postgresql_flexible_server_database.main.name
      }

      env {
        name  = "DB_USER"
        value = var.postgres_admin_username
      }

      env {
        name        = "DB_PASSWORD"
        secret_name = "db-password"
      }

      env {
        name  = "ALLOWED_HOSTS"
        value = "*"
      }

      env {
        name  = "CORS_ALLOWED_ORIGINS"
        value = "*"
      }

      env {
        name  = "DEPLOYMENT_ID"
        value = var.deployment_id
      }
    }

    min_replicas = 1
    max_replicas = 1
  }
}

resource "azurerm_container_app" "frontend" {
  count = var.deploy_apps ? 1 : 0

  name                         = "hp-${var.environment}-frontend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  ingress {
    external_enabled = true
    target_port      = 8080
    transport        = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  template {
    container {
      name   = "frontend"
      image  = "${azurerm_container_registry.main.login_server}/hireme-pixels-frontend:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "API_URL"
        value = "https://${azurerm_container_app.backend[0].ingress[0].fqdn}/api"
      }

      env {
        name  = "DEPLOYMENT_ID"
        value = var.deployment_id
      }
    }

    min_replicas = 1
    max_replicas = 1
  }
}