resource "azuread_application" "main" {
  display_name = "HireMe-Pixels"

  group_membership_claims = ["SecurityGroup"]

  web {
    redirect_uris = [
      "https://${var.backend_hostname}/api/auth/callback/"
    ]
  }
}

resource "azuread_service_principal" "main" {
  client_id = azuread_application.main.client_id
}

resource "azuread_application_password" "main" {
  application_id = azuread_application.main.id

  display_name = "HireMe-Pixels Django"
  end_date     = var.entra_credential_end_date
}

