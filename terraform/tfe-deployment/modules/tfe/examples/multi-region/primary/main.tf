terraform {
  required_providers {
    aws      = "~> 3.25.0"
    template = "~> 2.2.0"
  }
}

provider "aws" {
  region = "us-east-1"
}

module "tfe-primary" {
  source = "../../.."

  is_secondary         = var.is_secondary
  friendly_name_prefix = var.friendly_name_prefix
  common_tags          = var.common_tags

  tfe_bootstrap_bucket = var.tfe_bootstrap_bucket
  tfe_license_filepath = var.tfe_license_filepath
  tfe_release_sequence = var.tfe_release_sequence
  tfe_hostname         = var.tfe_hostname
  console_password     = var.console_password
  enc_password         = var.enc_password

  vpc_id                      = var.vpc_id
  alb_subnet_ids              = var.alb_subnet_ids
  ec2_subnet_ids              = var.ec2_subnet_ids
  rds_subnet_ids              = var.rds_subnet_ids
  load_balancer_is_internal   = var.load_balancer_is_internal
  route53_hosted_zone_public  = var.route53_hosted_zone_public
  create_route53_alias_record = var.create_route53_alias_record

  asg_instance_count = var.asg_instance_count
  os_distro          = var.os_distro
  ssh_key_pair       = var.ssh_key_pair

  ingress_cidr_alb_allow     = var.ingress_cidr_alb_allow
  ingress_cidr_console_allow = var.ingress_cidr_console_allow
  ingress_cidr_ec2_allow     = var.ingress_cidr_ec2_allow
  #kms_key_arn                = var.kms_key_arn

  rds_engine_version      = var.rds_engine_version
  rds_master_password     = var.rds_master_password
  rds_replica_count       = var.rds_replica_count
  rds_skip_final_snapshot = var.rds_skip_final_snapshot

  bucket_replication_configuration = var.bucket_replication_configuration
}

output "tfe_primary" {
  value = {
    tfe_url               = module.tfe-primary.tfe_url
    tfe_admin_console_url = module.tfe-primary.tfe_admin_console_url
    rds_global_cluster_id = module.tfe-primary.rds_global_cluster_id
    rds_cluster_arn       = module.tfe-primary.rds_cluster_arn
    rds_cluster_members   = module.tfe-primary.rds_cluster_members
    s3_bucket_name        = module.tfe-primary.s3_bucket_name
    s3_bucket_arn         = module.tfe-primary.s3_bucket_arn
    s3_crr_iam_role       = module.tfe-primary.s3_crr_iam_role_arn
  }
}