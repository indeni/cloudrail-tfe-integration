# Multi-Region
The TFE application logic does not natively support multi-region failover or Disaster Recovery scenarios  at the application layer today. However, a multi-region architecture can be achieved by leveraging some of the features and functionality of the AWS services that are in play. Multi-region in this context means an _active_ TFE instance in the "Primary" region and a _passive_ TFE instance in the "Secondary" region. At the storage layer, S3 Cross-Region Replication (CRR) and an Aurora global database are the features used to replicate the data across regions. At the application (compute) layer, an Auto Scaling Group (ASG) and Launch Template are provisioned in the Secondary region with  an ASG instance count of `0` (instead of `1`) and slightly different `user_data` arguments within the Launch Template than that of the Primary region. The idea is that when a disaster is declared, the following needs to happen to recover TFE in the Secondary region:

1. Database in the Secondary region is promoted to the primary role so it can take on read/write workloads
2. ASG instance count is bumped up from `0` to `1` in Secondary region
3. DNS is changed so the Alias or CNAME record resolves to the load balancer in the Secondary region and away from the load balancer in the Primary region
4. EC2 instance automatically spins up, installs TFE, and connects to the External Services (RDS and S3) in the Secondary region
<p>&nbsp;</p>

_Note: this configuration and failover/failback still needs to be tested and vetted before running in a Production environment_.

## Usage
The recommendation is to separate out the "Primary" and "Secondary" TFE instances into their own Terraform configurations and thus their own Terraform states. This minimizes blast radius and will allow for making changes to each instance more comfortably and independently, especially if a Disaster Recovery scenario were to arise.

_Note: In this example scenario, Route53 and ACM are leveraged for DNS and TLS/SSL. The installation method is **online** and the load balancer exposure is **public**. However, the multi-region configuration would apply to any of the other scenarios depicted in the [examples](../) section._

### Step 1: Deploy "Primary" TFE instance without S3 bucket replication stanza
```hcl
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
  source = "<path/to/module>"

  is_secondary         = false
  friendly_name_prefix = "acme"
  common_tags = {
    App          = "TFE"
    Environment  = "Production"
    Is_Secondary = "False"
    Owner        = "YourName"
  }

  tfe_bootstrap_bucket          = "acme-tfe-bootstrap-bucket-primary"
  tfe_license_filepath          = "s3://acme-tfe-bootstrap-bucket-primary/tfe-license.rli"
  tfe_release_sequence          = 504
  tfe_hostname                  = "tfe.acme.com"
  console_password              = "aws_secretsmanager"
  enc_password                  = "aws_secretsmanager"
  aws_secretsmanager_secret_arn = "arn:aws:secretsmanager:us-east-1:000000000000:secret:tfe-bootstrap-secrets-abcdef"
  
  vpc_id                      = "vpc-00000000000000000"
  alb_subnet_ids              = ["subnet-11111111111111111", "subnet-22222222222222222", "subnet-33333333333333333"]
  ec2_subnet_ids              = ["subnet-44444444444444444", "subnet-55555555555555555", "subnet-66666666666666666"]
  rds_subnet_ids              = ["subnet-44444444444444444", "subnet-55555555555555555", "subnet-66666666666666666"]
  load_balancer_is_internal   = false
  route53_hosted_zone_public  = "acme.com"
  create_route53_alias_record = true

  asg_instance_count          = 1
  os_distro                   = "ubuntu"

  ssh_key_pair                = "acme_tfe_keypair_us_east_1"
  ingress_cidr_alb_allow      = ["0.0.0.0/0"]
  ingress_cidr_console_allow  = ["10.1.10.1/24"]
  ingress_cidr_ec2_allow      = ["10.1.10.1/24", "10.1.20.1/24"]

  rds_engine_version          = 11.9
  rds_master_password         = "abcdefg1234567"
  rds_replica_count           = 1
}

output "tfe_primary" {
  value = {
    tfe_url               = module.tfe-primary.tfe_url
    tfe_admin_console_url = module.tfe-primary.tfe_admin_console_url
    rds_global_cluster_id = module.tfe-primary.rds_global_cluster_id
    rds_cluster_arn       = module.tfe-primary.rds_cluster_arn
    rds_cluster_members   = module.tfe-primary.rds_cluster_members
    s3_bucket_name        = module.tfe-primary.s3_bucket_name
    s3_crr_iam_role       = module.tfe-primary.s3_crr_iam_role_arn
  }
}
```

### Step 2: Deploy "Secondary" TFE instance

Plug the following two Terraform outputs from step 1 into the "Secondary" Terraform configuration:

- `module.tfe_primary.rds_global_cluster_id` --> `rds_global_cluster_id`
- `module.tfe_primary.rds_cluster_arn` --> `rds_replication_source_identifier`

```hcl
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
  source = "<path/to/module>"

  is_secondary         = true
  friendly_name_prefix = "acme"
  common_tags = {
    App          = "TFE"
    Environment  = "Production"
    Is_Secondary = "True"
    Owner        = "Alex"
  }

  tfe_bootstrap_bucket          = "acme-tfe-bootstrap-bucket-replica"
  tfe_license_filepath          = "s3://acme-tfe-bootstrap-bucket-replica/tfe-license.rli"
  tfe_release_sequence          = 504
  tfe_hostname                  = "tfe.acme.com"
  console_password              = "aws_secretsmanager"
  enc_password                  = "aws_secretsmanager"
  aws_secretsmanager_secret_arn = "arn:aws:secretsmanager:us-west-2:000000000000:secret:tfe-bootstrap-secrets-abcdef"

  vpc_id                      = "vpc-aaaaaaaaaaaaaaaaa"
  alb_subnet_ids              = ["subnet-bbbbbbbbbbbbbbbbb", "subnet-ccccccccccccccccc", "subnet-ddddddddddddddddd"]
  ec2_subnet_ids              = ["subnet-eeeeeeeeeeeeeeeee", "subnet-fffffffffffffffff", "subnet-ggggggggggggggggg"]
  rds_subnet_ids              = ["subnet-eeeeeeeeeeeeeeeee", "subnet-fffffffffffffffff", "subnet-ggggggggggggggggg"]
  load_balancer_is_internal   = false
  route53_hosted_zone_public  = "acme.com"
  create_route53_alias_record = false

  asg_instance_count          = 0
  os_distro                   = "ubuntu"

  ssh_key_pair                = "acme_tfe_keypair_us_west_2"
  ingress_cidr_alb_allow      = ["0.0.0.0/0"]
  ingress_cidr_console_allow  = ["10.1.10.1/24"]
  ingress_cidr_ec2_allow      = ["10.1.10.1/24", "10.1.20.1/24"]

  rds_global_cluster_id             = "acme-tfe-rds-global-cluster"
  rds_replication_source_identifier = "arn:aws:rds:us-east-1:000000000000:cluster:acme-tfe-rds-cluster-us-east-1"
  source_region                     = "us-east-1"
  rds_master_password               = "abcdefg1234567"
  rds_replica_count                 = 0
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
```

### Step 3: Add S3 bucket replication input to "Primary" TFE configuration

Circle back and plug the following Terraform output from step 2 into the "Primary" Terraform configuration:

- `module.tfe_secondary.s3_bucket_arn` --> `bucket_replication_configuration` (within the `destination` block)

```hcl
module "tfe-primary" {
  ...
  ...
  bucket_replication_configuration = {
    rules = [
      {
        id     = "TFE"
        status = "Enabled"

        destination = {
          bucket = "arn:aws:s3:::acme-tfe-app-us-west-2-000000000000"
        }
      }
    ]
  }
}
```
<p>&nbsp;</p>


## Issues/Caveats

- Right now the Aurora global replication breaks when attempting to encrypt the source and destination RDS clusters with a KMS key (see https://github.com/hashicorp/terraform-provider-aws/issues/16362)
- AWS's SLA for promoting an Aurora global database secondary cluster after a Region-wide outage is 1 minute, but the SLA for S3 CRR is less specific (99% of objects within 5 minutes, 99.99% of objects within 15 minutes)
- An operator needs to modify the `asg_instance_count` input from `0` to `1` when a region-level failover is desired
- An operator needs to modify DNS when a region-level failover is desired
- Failover and failback need more testing as it relates to the Terraform configurations
- This solution overall needs more testing and vetting