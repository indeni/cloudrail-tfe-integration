data "aws_availability_zones" "available" {}

locals {
  az_length = length(data.aws_availability_zones.available) > 3 ? 3 : length(data.aws_availability_zones.available)
  azs       = slice(data.aws_availability_zones.available.names, 0, local.az_length)
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = var.project_name
  cidr = "10.0.0.0/16"

  azs              = data.aws_availability_zones.available.names
  private_subnets  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets   = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  database_subnets = ["10.0.21.0/24", "10.0.22.0/24", "10.0.23.0/24"]

  create_database_subnet_group = true
  enable_nat_gateway           = true
  enable_vpn_gateway           = true

  tags = var.common_tags
}

locals {
  password_targets = ["initial_admin", "console", "enc", "rds"]
}

resource "random_password" "password" {
  for_each = toset(local.password_targets)
  length   = 16
  special  = false
  //override_special = "_%@/'\""
}

resource "aws_kms_key" "key" {}

resource "tls_private_key" "key" {
  algorithm = "RSA"
}

resource "local_file" "private_key" {
  filename          = "${path.module}/tfe.pem"
  sensitive_content = tls_private_key.key.private_key_pem
  file_permission   = "0400"
}

resource "aws_key_pair" "key_pair" {
  key_name   = "tfe-key"
  public_key = tls_private_key.key.public_key_openssh
}

resource "aws_s3_bucket" "license" {
  bucket = "${var.project_name}-tfe-license"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.key.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }
}

resource "aws_s3_bucket_object" "license" {
  bucket = aws_s3_bucket.license.bucket
  key    = "license.rli"
  source = "${path.module}/license.rli"
  etag   = filemd5("${path.module}/license.rli")
}

module "tfe" {
  source = "./modules/tfe"

  friendly_name_prefix       = var.project_name
  common_tags                = var.common_tags
  tfe_bootstrap_bucket       = aws_s3_bucket_object.license.bucket
  tfe_license_filepath       = "s3://indeni-tfe-license/license.rli"
  tfe_hostname               = var.tfe_hostname
  tfe_initial_admin_username = var.tfe_initial_admin_username
  tfe_initial_admin_password = random_password.password["initial_admin"].result
  tfe_initial_org_name       = var.tfe_initial_org_name
  tfe_initial_org_email      = var.tfe_initial_org_email
  console_password           = random_password.password["console"].result
  enc_password               = random_password.password["enc"].result
  vpc_id                     = module.vpc.vpc_id
  alb_subnet_ids             = module.vpc.public_subnets
  //ec2_subnet_ids             = module.vpc.public_subnets #for ssh access
  //ingress_cidr_ec2_allow = ["0.0.0.0/0"] #for ssh access
  ec2_subnet_ids             = module.vpc.private_subnets
  route53_hosted_zone_public = var.route53_hosted_zone_public
  ingress_cidr_console_allow = ["0.0.0.0/0"]
  instance_size              = "m5.large"
  kms_key_arn                = aws_kms_key.key.arn
  ssh_key_pair               = aws_key_pair.key_pair.key_name
  rds_subnet_ids             = module.vpc.database_subnets
  rds_availability_zones     = local.azs
  rds_master_username        = "tfe"
  rds_master_password        = random_password.password["rds"].result
  rds_skip_final_snapshot    = true
  rds_replica_count          = 0
  rds_instance_class         = "db.r5.large"
  custom_image_tag           = "swinkler/indeni-cloudrail:latest"
}
