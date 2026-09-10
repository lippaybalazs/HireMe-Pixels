variable "environment" {
  description = "Deployment environment."
  type        = string

  validation {
    condition     = contains(["development", "production", "ci"], var.environment)
    error_message = "Environment must be either development or production."
  }
}

variable "location" {
  description = "Azure region in which resources are deployed."
  type        = string
}

variable "acr_sku" {
  description = "Azure Container Registry SKU."
  type        = string

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.acr_sku)
    error_message = "ACR SKU must be Basic, Standard, or Premium."
  }
}

variable "deploy_apps" {
  description = "Whether to deploy the frontend and backend Container Apps."
  type        = bool
  default     = false
}

variable "postgres_admin_username" {
  description = "Administrator username for PostgreSQL."
  type        = string
}

variable "postgres_admin_password" {
  description = "Administrator password for PostgreSQL."
  type        = string
  sensitive   = true
}

# Used to force redeploy docker images each push
variable "deployment_id" {
  type    = string
  default = ""
}