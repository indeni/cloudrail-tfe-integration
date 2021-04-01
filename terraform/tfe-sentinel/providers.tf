terraform {
  required_providers {
    shell = {
      source = "scottwinkler/shell"
      version = "1.7.7"
    }
  }
}

provider "tfe" {
  hostname = var.tfe_hostname
  token    = var.tfe_token
}

provider "shell" {
  sensitive_environment = {
    TFE_TOKEN = var.tfe_token
  }
}