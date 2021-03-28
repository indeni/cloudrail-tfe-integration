terraform {
  required_providers {
    aws      = "~> 3.25.0"
    template = "~> 2.2.0"
  }
}

provider "aws" {
  region = "us-west-2"
}

module "tfe-secondary" {
  source = "../../.."

  is_secondary         = true
  friendly_name_prefix = "winterfell"
  common_tags = {
    App          = "TFE"
    Environment  = "Production"
    Is_Secondary = "True"
    Tool         = "Terraform"
    Owner        = "Alex"
  }

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

  rds_global_cluster_id             = var.rds_global_cluster_id
  rds_replication_source_identifier = var.rds_replication_source_identifier
  source_region                     = var.source_region
  rds_master_password               = var.rds_master_password
  rds_replica_count                 = var.rds_replica_count
  rds_skip_final_snapshot           = var.rds_skip_final_snapshot
}

output "tfe_secondary" {
  value = {
    tfe_url               = module.tfe-secondary.tfe_url
    tfe_admin_console_url = module.tfe-secondary.tfe_admin_console_url
    rds_global_cluster_id = module.tfe-secondary.rds_global_cluster_id
    rds_cluster_arn       = module.tfe-secondary.rds_cluster_arn
    rds_cluster_members   = module.tfe-secondary.rds_cluster_members
    s3_bucket_name        = module.tfe-secondary.s3_bucket_name
  }
}