data "aws_region" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_s3_bucket" "bootstrap_bucket" {
  count = var.tfe_bootstrap_bucket != "" ? 1 : 0

  bucket = var.tfe_bootstrap_bucket
}