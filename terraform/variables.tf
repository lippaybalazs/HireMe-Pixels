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