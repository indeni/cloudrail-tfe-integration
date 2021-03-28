variable "aws" {
  type = object({profile= string, region = string})
}

variable "project_name" {
  type = string
}

variable "tfe_hostname" {
  type = string
}

variable "tfe_initial_admin_username" {
  type = string
}

variable "tfe_initial_org_email" {
  type = string
}

variable "tfe_initial_org_name" {
  type = string
  default = "Admin"
}

variable "route53_hosted_zone_public" {
  type = string
}

variable "common_tags" {
  type = map(string)
  default = { project = "tfe" }
}