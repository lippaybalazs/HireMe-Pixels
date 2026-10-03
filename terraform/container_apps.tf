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

  lifecycle {
    ignore_changes = [
      workload_profile,
    ]
  }
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

  secret {
    name  = "entra-client-secret"
    value = azuread_application_password.main.value
  }

  secret {
    name = "redis-url"

    value = "redis://:${random_password.redis[0].result}@hp-${var.environment}-redis:6379/0"
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
        value = var.backend_hostname
      }

      env {
        name  = "CORS_ALLOWED_ORIGINS"
        value = "https://${var.frontend_hostname}"
      }

      env {
        name  = "DEPLOYMENT_ID"
        value = var.deployment_id
      }

      env {
        name  = "ENTRA_CLIENT_ID"
        value = azuread_application.main.client_id
      }

      env {
        name        = "ENTRA_CLIENT_SECRET"
        secret_name = "entra-client-secret"
      }

      env {
        name  = "ENTRA_TENANT_ID"
        value = data.azuread_client_config.current.tenant_id
      }

      env {
        name  = "BACKEND_HOSTNAME"
        value = var.backend_hostname
      }

      env {
        name  = "FRONTEND_URL"
        value = "https://${var.frontend_hostname}"
      }

      env {
        name  = "ENTRA_ADMIN_GROUP_ID"
        value = var.ENTRA_ADMIN_GROUP_ID
      }

      env {
        name  = "DJANGO_SECRET_KEY"
        value = var.DJANGO_SECRET_KEY
      }

      env {
        name        = "REDIS_URL"
        secret_name = "redis-url"
      }
    }

    min_replicas = var.backend_min_replicas
    max_replicas = var.backend_max_replicas

    http_scale_rule {
      name                = "http"
      concurrent_requests = var.backend_http_concurrency
    }
  }

  depends_on = [
    azurerm_container_app.redis
  ]
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
        value = "https://${var.backend_hostname}/api"
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

resource "azurerm_container_app" "redis" {
  count = var.deploy_apps ? 1 : 0

  name                         = "hp-${var.environment}-redis"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  secret {
    name  = "redis-password"
    value = random_password.redis[0].result
  }

  template {
    min_replicas = 1
    max_replicas = 1

    container {
      name   = "redis"
      image  = "${azurerm_container_registry.main.login_server}/hireme-pixels-redis:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name        = "REDIS_PASSWORD"
        secret_name = "redis-password"
      }

      env {
        name  = "DEPLOYMENT_ID"
        value = var.deployment_id
      }

      liveness_probe {
        transport = "TCP"
        port      = 6379
      }

      readiness_probe {
        transport = "TCP"
        port      = 6379
      }
    }
  }

  ingress {
    external_enabled = false
    target_port      = 6379
    transport        = "tcp"

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
}

resource "random_password" "redis" {
  count = var.deploy_apps ? 1 : 0

  length           = 32
  special          = true
  override_special = "!$%&*+-=_"
}