#-------------------------------------------------------------------------------------------------------------------------------------------
# Common
#-------------------------------------------------------------------------------------------------------------------------------------------
variable "is_secondary" {
  type        = bool
  description = "Boolean indicating whether TFE instance deployment is for Primary region or Secondary region."
  default     = false
}

variable "friendly_name_prefix" {
  type        = string
  description = "String value for freindly name prefix for AWS resource names."
}

variable "common_tags" {
  type        = map(string)
  description = "Map of common tags for taggable AWS resources."
  default     = {}
}

#-------------------------------------------------------------------------------------------------------------------------------------------
# TFE Installation Settings
#-------------------------------------------------------------------------------------------------------------------------------------------
variable "tfe_bootstrap_bucket" {
  type        = string
  description = "Name of existing S3 bucket containing prerequisite files for TFE automated install. Typically would contain TFE license file and airgap files if `airgap_install` is `true`."
  default     = ""
}

variable "tfe_license_filepath" {
  type        = string
  description = "Full filepath of TFE license file (.rli file extension). A local filepath or S3 is supported."
}

variable "airgap_install" {
  type        = bool
  description = "Boolean indicating whether TFE install is airgap (true) or online (false)."
  default     = false
}

variable "replicated_bundle_path" {
  type        = string
  description = "Full path of Replicated bundle (replicated.tar.gz) in S3 bucket. A local filepath is not supported because the Replicated bundle is too large for user_data. Only specify if `airgap_install` is `true`."
  default     = ""
}

variable "tfe_airgap_bundle_path" {
  type        = string
  description = "Full path of TFE airgap bundle in S3 bucket. A local filepath is not supported because the airgap bundle is too large for user_data. Only specify if `airgap_install` is `true`."
  default     = ""
}

variable "tfe_release_sequence" {
  type        = string
  description = "TFE application version release sequence number within Replicated. Leave default for latest version. Not needed if `airgap_install` is `true`."
  default     = ""
}

variable "tls_bootstrap_type" {
  type        = string
  description = "Type of TLS cert to use. If set to `server-path`, variables `tls_bootstrap_cert` and `tls_bootstrap_key` are also required."
  default     = "self-signed"
}

variable "tls_bootstrap_cert" {
  type        = string
  description = "Path to certificate file in PEM format on TFE server if TLS/SSL is terminated at the instance-level. Only specify if `tls_bootstrap_type` is `server-path`."
  default     = ""
}

variable "tls_bootstrap_key" {
  type        = string
  description = "Path to certificate private key in PEM format on TFE server if TLS/SSL is terminated at the instance-level. Only specify if `tls_bootstrap_type` is `server-path`."
  default     = ""
}

variable "remove_import_settings_from" {
  type        = bool
  description = "Replicated setting to automatically remove the settings.json file (referred to as `ImportSettingsFrom` by Replicated) after installation."
  default     = false
}

variable "tfe_hostname" {
  type        = string
  description = "Hostname/FQDN of TFE instance. This name should resolve to the load balancer DNS name."
}

variable "tfe_initial_admin_username" {
  type        = string
  description = "Username for initial TFE local administrator account. Only specify if it is desired to have the Initial Admin User created during the automated install."
  default     = ""
}

variable "tfe_initial_admin_email" {
  type        = string
  description = "Email address for initial TFE local administrator account. Only specify if it is desired to have the Initial Admin User created during the automated install."
  default     = ""
}

variable "tfe_initial_admin_password" {
  type        = string
  description = "Password of TFE Initial Admin User. Required only if `tfe_initial_admin_username` is also specified. Specify `aws_secretsmanager` to retrieve from AWS Secrets Manager via `aws_secretsmanager_secret_arn` input."
  default     = ""
}

variable "tfe_initial_org_name" {
  type        = string
  description = "Name of initial TFE Organization created by the bootstrap (user_data) process."
  default     = ""
}

variable "tfe_initial_org_email" {
  type        = string
  description = "Email address of initial TFE Organization created by bootstrap (user_data) process."
  default     = ""
}

variable "capacity_concurrency" {
  type        = string
  description = "Total concurrent Terraform Runs (Plans/Applies) within TFE."
  default     = "10"
}

variable "capacity_memory" {
  type        = string
  description = "Maxium amount of memory (MB) that a Terraform Run (Plan/Apply) can consume within TFE."
  default     = "512"
}

variable "console_password" {
  type        = string
  description = "Password to unlock TFE Admin Console accessible via port 8800. Specify `aws_secretsmanager` to retrieve from AWS Secrets Manager via `aws_secretsmanager_secret_arn` input."
}

variable "enc_password" {
  type        = string
  description = "Password to protect unseal key and root token of TFE embedded Vault. Specify `aws_secretsmanager` to retrieve from AWS Secrets Manager via `aws_secretsmanager_secret_arn` input."
}

#-------------------------------------------------------------------------------------------------------------------------------------------
# Network
#-------------------------------------------------------------------------------------------------------------------------------------------
variable "vpc_id" {
  type        = string
  description = "VPC ID that TFE will be deployed into."
}

variable "alb_subnet_ids" {
  type        = list(string)
  description = "List of subnet IDs to use for the load balancer."
}

variable "ec2_subnet_ids" {
  type        = list(string)
  description = "List of subnet IDs to use for the EC2 instance. Private subnets is the best practice."
}

variable "load_balancer_is_internal" {
  type        = bool
  description = "Boolean indicating if Application Load Balancer exposure is internal or external. Only specify `true` for internal."
  default     = false
}

variable "route53_hosted_zone_public" {
  type        = string
  description = "Public Route53 Hosted Zone name where `tfe_hostname` Alias record and Certificate Validation CNAME record will reside. Required if `tls_certificate_arn` is not specified."
  default     = null
}

variable "create_route53_alias_record" {
  type        = bool
  description = "Boolean indicating whether to create Route53 Alias Record resolving to Load Balancer DNS name (true) or not (false) when `route53_hosted_zone_public` is also specified. This variable is only relevant when route53_hosted_zone_public is also specified."
  default     = true
}

#-------------------------------------------------------------------------------------------------------------------------------------------
# Security
#-------------------------------------------------------------------------------------------------------------------------------------------
variable "ingress_cidr_alb_allow" {
  type        = list(string)
  description = "List of CIDR ranges to allow web traffic ingress to TFE load balancer."
  default     = ["0.0.0.0/0"]
}

variable "ingress_cidr_console_allow" {
  type        = list(string)
  description = "List of CIDR ranges to allow TFE Replicated admin console (port 8800) traffic ingress to TFE load balancer."
  default     = null
}

variable "ingress_cidr_ec2_allow" {
  type        = list(string)
  description = "List of CIDR ranges to allow SSH ingress to TFE EC2 instance (i.e. Bastion host IP, workstation IP, etc.)."
  default     = []
}

variable "tls_certificate_arn" {
  type        = string
  description = "ARN of ACM or IAM certificate to be used for Application Load Balancer HTTPS listeners. Required if route53_hosted_zone_public is not specified."
  default     = null
}

variable "kms_key_arn" {
  type        = string
  description = "ARN of KMS key to encrypt TFE RDS and S3 resources."
  default     = ""
}

variable "ssh_key_pair" {
  type        = string
  description = "Name of SSH key pair for TFE EC2 instance."
  default     = ""
}

variable "aws_secretsmanager_secret_arn" {
  type        = string
  description = "ARN of secret metadata stored in AWS Secrets Manager. If specified, secret must contain key/value pairs for console_password and enc_password; and optionally tfe_initial_admin_pw."
  default     = ""
}

#-------------------------------------------------------------------------------------------------------------------------------------------
# Compute
#-------------------------------------------------------------------------------------------------------------------------------------------
variable "os_distro" {
  type        = string
  description = "Linux OS distribution for TFE EC2 instance. Choose from amzn2, ubuntu, centos, rhel."
  default     = "amzn2"
}

variable "ami_id" {
  type        = string
  description = "Custom AMI ID for TFE EC2 Launch Template.  If specified, value os_distro must coincide with this AMI OS distro."
  default     = null
}

variable "instance_size" {
  type        = string
  description = "EC2 instance type for TFE Launch Template."
  default     = "m5.xlarge"
}

variable "asg_instance_count" {
  type        = number
  description = "Number of EC2 instances to run in Autoscaling Group. Normally the TFE Primary instance should be set to 1 and Secondary should be set to 0."
  default     = 1
}

#-------------------------------------------------------------------------------------------------------------------------------------------
# External Services - RDS
#-------------------------------------------------------------------------------------------------------------------------------------------
variable "rds_subnet_ids" {
  type        = list(string)
  description = "List of subnet IDs to use for RDS Database Subnet Group. Private subnets is the best practice."
}

variable "rds_availability_zones" {
  type        = list(string)
  description = "List of Availability Zones to spread RDS Cluster across."
  default     = null
}

variable "rds_replica_count" {
  type        = number
  description = "Amount of Aurora Replica instances to deploy within the Database Cluster within the same region."
  default     = 1
}

variable "rds_engine" {
  type        = string
  description = "Name of database engine."
  default     = "aurora-postgresql"
}

variable "rds_engine_version" {
  type        = number
  description = "Version of Aurora PostgreSQL Global Database engine."
  default     = 11.9
}

variable "rds_engine_mode" {
  type        = string
  description = "RDS engine mode."
  default     = "provisioned"
}

variable "rds_database_name" {
  type        = string
  description = "Name of database."
  default     = "tfe"
}

variable "rds_master_username" {
  type        = string
  description = "Username for the master DB user."
  default     = "tfe"
}

variable "rds_master_password" {
  type        = string
  description = "Password for RDS master DB user."
}

variable "rds_instance_class" {
  type        = string
  description = "Instance class size for RDS Aurora."
  default     = "db.r5.xlarge"
}

variable "rds_storage_capacity" {
  type        = string
  description = "Size capacity (GB) of RDS PostgreSQL database."
  default     = "50"
}

variable "rds_replication_source_identifier" {
  type        = string
  description = "ARN of a source DB cluster or DB instance if this DB cluster is to be created as a Read Replica. Intended to be used by RDS Cluster Instance in Secondary region."
  default     = null
}

variable "rds_skip_final_snapshot" {
  type        = bool
  description = "Boolean indicating whether to perform an RDS final snapshot (true) or not (false)."
  default     = false
}

variable "rds_preferred_backup_window" {
  type        = string
  description = "Daily time range (UTC) for RDS backup to occur. Must not overlap with maintenance_window if specified."
  default     = "04:00-04:30"
}

variable "rds_backup_retention_period" {
  type        = string
  description = "Daily time range (UTC) for RDS backup to occur. Must not overlap with maintenance_window if specified."
  default     = 7
}

variable "rds_preferred_maintenance_window" {
  type        = string
  description = "Window (UTC) to perform RDS database maintenance. Must not overlap with rds_backup_window if specified."
  default     = "Sun:08:00-Sun:09:00"
}

variable "rds_global_cluster_id" {
  type        = string
  description = "RDS Global Cluster identifier. Intended to be used by RDS Cluster Instance in Secondary region."
  default     = null
}

variable "source_region" {
  type        = string
  description = "Source region for RDS Cross-Region Replication. Only specify for Secondary instance."
  default     = null
}

#-------------------------------------------------------------------------------------------------------------------------------------------
# External Services - S3
#-------------------------------------------------------------------------------------------------------------------------------------------
variable "bucket_replication_configuration" {
  description = "Map containing S3 Cross-Region Replication configuration."
  type        = any
  default     = {}
}

variable "destination_bucket" {
  type        = string
  description = "Destination S3 Bucket for Cross-Region Replication configuration. Should exist in Secondary region."
  default     = ""
}