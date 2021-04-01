variable "tfe_hostname" {
  type    = string
  default = "app.terraform.io"
}

variable "tfe_token" {
  type    = string
}


variable "organizations" {
  type    = list(string)
  default = ["TestOrg"]
}

variable "cloudrail_token" {
  type      = string
  sensitive = true
}
