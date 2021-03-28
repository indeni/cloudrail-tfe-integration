# Custom DNS and TLS
This scenario does not leverage Amazon Route53 for DNS nor AWS Certificate Manager (ACM) for the TLS/SSL certificate. Thus, DNS and TLS/SSL will need to be handled outside of AWS (via other Terraform providers or manually). The key difference from the module perspective in this scenario versus the route53-and-acm scenario is that a TLS/SSL certificate will need to be imported into ACM or IAM as a **prerequisite**, such that it can be specified by ARN within the input variable `tls_certificate_arn`. The TLS/SSL certificate Common Name should match the value specified for the `tfe_hostname` input variable.
<p>&nbsp;</p>


## Ideal Use Case
- Custom/internal DNS service is required and not Amazon Route53
- Custom/internal/private CA is required to issue TLS/SSL certificate and not AWS Certificate Manager (ACM)
<p>&nbsp;</p>


## Public vs Private
Either public or private subnet IDs can be specified for the `alb_subnet_ids` input in this scenario. However, if the VCS and/or CI/CD tooling is publicly/externally hosted (SaaS), then the `alb_subnet_ids` input must contain public subnet IDs for the VCS integration to function properly. If `alb_subnet_ids` does contain private subnet IDs, then the input `load_balancer_is_internal` should be set to `true`. TFE and the VCS must be able to resolve each other and trust each other.
<p>&nbsp;</p>


## Post Step
The caveat with this scenario is that the module by default will not handle DNS or TLS/SSL resources outside of AWS. It is possible to make custom additions to the code if Terraform providers exist for the chosen systems handling DNS and TLS/SSL. Either way, in this scenario it is the user's responsibility to create a DNS CNAME record for the `tfe_hostname` resolving to the AWS Application Load Balancer DNS name once it is known. This is why the `tfe_alb_dns_name` output exists in the examples below.
<p>&nbsp;</p>


## Online Install - Private Load Balancer Exposure
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

module "tfe" {
  source = "github.com/hashicorp/is-terraform-aws-tfe-standalone"

  friendly_name_prefix = "cloudteam"
  common_tags = {
    "App"               = "TFE"
    "Environment"       = "Production"
    "Is_Secondary"      = "False"
    "Owner"             = "YourName"
    "Provisioning_Tool" = "Terraform"
  }
  
  tfe_bootstrap_bucket          = "my-tfe-bootstrap-bucket"
  tfe_license_filepath          = "s3://my-tfe-bootstrap-bucket/tfe-license.rli"
  tfe_release_sequence          = 504
  tfe_hostname                  = "my-tfe-instance.whatever.com"
  console_password              = "aws_secretsmanager"
  enc_password                  = "aws_secretsmanager"
  aws_secretsmanager_secret_arn = "arn:aws:secretsmanager:us-east-1:000000000000:secret:tfe-bootstrap-secrets-abcdef"
  
  vpc_id                     = "vpc-00000000000000000"
  alb_subnet_ids             = ["subnet-33333333333333333", "subnet-44444444444444444", "subnet-55555555555555555"] # private subnet IDs
  ec2_subnet_ids             = ["subnet-33333333333333333", "subnet-44444444444444444", "subnet-55555555555555555"] # private subnet IDs
  rds_subnet_ids             = ["subnet-33333333333333333", "subnet-44444444444444444", "subnet-55555555555555555"] # private subnet IDs
  load_balancer_is_internal  = true
  tls_certificate_arn        = "arn:aws:acm:us-east-1:000000000000:certificate/00000000-1111-2222-3333-444444444444"
  
  os_distro                     = "amzn2"
  ssh_key_pair                  = "my-key-pair-us-east-1"

  ingress_cidr_alb_allow        = ["3.3.3.3/32", "4.4.4.4/32", "5.5.5.0/32"] # my VCS IP, my CI/CD tool IP, TFE users subnet
  ingress_cidr_console_allow    = ["1.1.1.1/32", "2.2.2.0/24"] # my workstation IP, IT admins workstation subnet
  ingress_cidr_ec2_allow        = ["1.1.1.1/32", "6.6.6.6/32"] # my workstation IP, my Bastion host IP
  kms_key_arn                   = "arn:aws:kms:us-east-1:000000000000:key/00000000-1111-2222-3333-444444444444"
}

output "tfe_alb_dns_name" {
  value = module.tfe.tfe_alb_dns_name
}

output "tfe_url" {
  value = module.tfe.tfe_url
}

output "tfe_admin_console_url" {
  value = module.tfe.tfe_admin_console_url
}
```

_Note: if TFE needs to be external-facing, set `load_balancer_is_internal` to `false`, specify a list of public subnet IDs for `alb_subnet_ids`, and ensure that the TLS/SSL referenced in `tls_certificate_arn` was signed by a publicly trusted Certificate Authority._
<p>&nbsp;</p>


## Airgap Install - Private Load Balancer Exposure
The key differences in terms of input variables to specify when the _installation method_ is **airgap** are:

- remove `tfe_release_sequence` (this is for **online** installs only)
- add `tfe_airgap_bundle_path` and `replicated_bundle_path` (files should be staged in `tfe_bootstrap_bucket` as a prereq)
- add `ami_id` if it wasn't in use already (see [Software Dependencies](#Software-Dependencies) section below)

### Software Dependencies
Ensure the custom AMI has the following dependencies installed (in a true airgap scenario, the module assumes software package repositories cannot be reached over the Internet by default):
 - `jq`
 - `unzip`
 - `docker` (see [Replicated docs](https://help.replicated.com/docs/native/customer-installations/supported-operating-systems/) for supported versions)
 - `awscli` ([version 2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html))

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

module "tfe" {
  source = "github.com/hashicorp/is-terraform-aws-tfe-standalone"

  friendly_name_prefix = "cloudteam"
  common_tags = {
    "App"               = "TFE"
    "Environment"       = "Production"
    "Is_Secondary"      = "False"
    "Owner"             = "YourName"
    "Provisioning_Tool" = "Terraform"
  }
  
  tfe_bootstrap_bucket          = "my-tfe-bootstrap-bucket"
  tfe_license_filepath          = "s3://my-tfe-bootstrap-bucket/tfe-license.rli"
  replicated_bundle_path        = "s3://my-tfe-bootstrap-bucket-primary/replicated.tar.gz"
  tfe_airgap_bundle_path        = "s3://my-tfe-bootstrap-bucket-primary/tfe-504.airgap"
  tfe_hostname                  = "my-tfe-instance.whatever.com"
  console_password              = "aws_secretsmanager"
  enc_password                  = "aws_secretsmanager"
  aws_secretsmanager_secret_arn = "arn:aws:secretsmanager:us-east-1:000000000000:secret:tfe-bootstrap-secrets-abcdef"
  
  vpc_id                     = "vpc-00000000000000000"
  alb_subnet_ids             = ["subnet-33333333333333333", "subnet-44444444444444444", "subnet-55555555555555555"] # private subnet IDs
  ec2_subnet_ids             = ["subnet-33333333333333333", "subnet-44444444444444444", "subnet-55555555555555555"] # private subnet IDs
  rds_subnet_ids             = ["subnet-33333333333333333", "subnet-44444444444444444", "subnet-55555555555555555"] # private subnet IDs
  load_balancer_is_internal  = true
  tls_certificate_arn        = "arn:aws:acm:us-east-1:000000000000:certificate/00000000-1111-2222-3333-444444444444"
  
  os_distro                     = "amzn2"
  ssh_key_pair                  = "my-key-pair-us-east-1"

  ingress_cidr_alb_allow        = ["3.3.3.3/32", "4.4.4.4/32", "5.5.5.0/32"] # my VCS IP, my CI/CD tool IP, TFE users subnet
  ingress_cidr_console_allow    = ["1.1.1.1/32", "2.2.2.0/24"] # my workstation IP, IT admins workstation subnet
  ingress_cidr_ec2_allow        = ["1.1.1.1/32", "6.6.6.6/32"] # my workstation IP, my Bastion host IP
  kms_key_arn                   = "arn:aws:kms:us-east-1:000000000000:key/00000000-1111-2222-3333-444444444444"
}

output "tfe_alb_dns_name" {
  value = module.tfe.tfe_alb_dns_name
}

output "tfe_url" {
  value = module.tfe.tfe_url
}

output "tfe_admin_console_url" {
  value = module.tfe.tfe_admin_console_url
}
```
<p>&nbsp;</p>


## Minimum Required Inputs (Bare Bones)
```hcl
module "tfe" {
  source = "github.com/hashicorp/is-terraform-aws-tfe-standalone"

  friendly_name_prefix = "cloudteam"
  tfe_license_filepath = "./tfe-license.rli"
  tfe_hostname         = "my-tfe-instance.whatever.com"
  console_password     = "ConsolePasswd123!"
  enc_password         = "EncPasswd123!"
  vpc_id               = "vpc-00000000000000000"
  alb_subnet_ids       = ["subnet-00000000000000000", "subnet-11111111111111111", "subnet-22222222222222222"] # public subnet IDs
  ec2_subnet_ids       = ["subnet-33333333333333333", "subnet-44444444444444444", "subnet-55555555555555555"] # private subnet IDs
  rds_subnet_ids       = ["subnet-33333333333333333", "subnet-44444444444444444", "subnet-55555555555555555"] # private subnet IDs
  tls_certificate_arn  = "arn:aws:acm:us-east-1:000000000000:certificate/00000000-1111-2222-3333-444444444444"
  rds_master_password  = "MyRdsPasswd123!"
}
```
