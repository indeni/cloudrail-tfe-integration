variable "tfe_hostname" {
  type    = string
  default = "app.terraform.io"
}

variable "tfe_token" {
  type    = string
}


variable "organizations" {
  type    = list(string)
}

variable "cloudrail_token" {
  type      = string
  sensitive = true
}

variable "cloud_account_id" {
  type = string
}