# Route53 and AWS Certificate Manager (ACM)
This scenario, if achievable given the environment and requirements, is generally the easiest approach to deploying TFE on AWS. This is because both DNS and TLS/SSL are fully automated within AWS via Terraform in one sweep. An Amazon Route53 alias record is created based on the `tfe_hostname` input and resolves to the Application Load Balancer (ALB) DNS name. A certificate is provisioned via AWS Certificate Manager (ACM) with a Common Name of the `tfe_hostname` input, and is automatically validated via the DNS certificate validation method via ACM and Route53. The Route53 Hosted Zone specified in the `route53_hosted_zone_public` input must be of the type **public** for the DNS certificate validation method to work properly and be fully automated by Terraform. **Although the Route53 Hosted Zone must be public, the Load Balancer subnets and exposure can be either private or public.** It also would be possible to leverage two separate Route53 Hosted Zones; a public one for the certificate validation CNAME record, and a private one for the `tfe_hostname` alias record. The module does not directly support this configuration at this time but if there is any interest for this configuration, please submit an issue to this repo.
<p>&nbsp;</p>


## Ideal Use Case
 - Version Control System (VCS) and/or CI/CD tooling is hosted publicly/externally (SaaS)
 - Desirable to use only AWS services (including DNS and TLS/SSL)
 - Desirable to automate as much of the TFE deployment and installation as possible in a single Terraform run
 - Able to use Amazon Route53 Hosted Zone that is of the type **public** for DNS certificate validation CNAME record
 - Able to use AWS Certificate Manager (ACM) to automatically create and validate TLS/SSL certificate
<p>&nbsp;</p>


## Public vs. Private
As stated above, the Route53 Hosted Zone specified must be of the type **public** in this scenario. However, either public or private subnet IDs can be specified for the `alb_subnet_ids` input. If the VCS and/or CI/CD tooling is publicly/externally hosted (SaaS), then the `alb_subnet_ids` input should contain public subnet IDs and the `load_balancer_is_internal` input should be set to `false` for the VCS integration to function properly. On the contrary if the VCS is privately/internally hosted, then the `alb_subnet_ids` input should contain private subnet IDs and the `load_balancer_is_internal` input should be set to `true`. TFE and the VCS must be able to resolve each other and trust each other.
<p>&nbsp;</p>


## Online Install
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
  alb_subnet_ids             = ["subnet-00000000000000000", "subnet-11111111111111111", "subnet-22222222222222222"] # public or private subnet IDs
  ec2_subnet_ids             = ["subnet-33333333333333333", "subnet-44444444444444444", "subnet-55555555555555555"] # private subnet IDs
  rds_subnet_ids             = ["subnet-33333333333333333", "subnet-44444444444444444", "subnet-55555555555555555"] # private subnets IDs
  load_balancer_is_internal  = false
  route53_hosted_zone_public = "whatever.com"
  
  os_distro    = "ubuntu"
  ssh_key_pair = "my-key-pair-us-east-1"

  ingress_cidr_alb_allow     = ["0.0.0.0/0"]
  ingress_cidr_console_allow = ["1.1.1.1/32", "2.2.2.0/24"] # my workstation IP, IT admins workstation subnet
  ingress_cidr_ec2_allow     = ["1.1.1.1/32", "3.3.3.3/32"] # my workstation IP, my Bastion host IP
  kms_key_arn                = "arn:aws:kms:us-east-1:000000000000:key/00000000-1111-2222-3333-444444444444"

  rds_master_password = "MyRdsPasswd123!"
}

output "tfe_url" {
  value = module.tfe.tfe_url
}

output "tfe_admin_console_url" {
  value = module.tfe.tfe_admin_console_url
}
```
<p>&nbsp;</p>


## Airgap Install
It is probably unlikely that one would choose an _installation method_ of **aigrap** while also being able to leverage a **public** Route53 Hosted Zone in combination with AWS Certificate Manager, but this configuration technically could work as long as the networking is setup properly and there is access to the VPC (Direct Connect, Virtual Private Gateway, VPN, Transit VPC, etc.). The key differences in terms of input variables to specify when the _installation method_ is **airgap** are:

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
  rds_subnet_ids             = ["subnet-33333333333333333", "subnet-44444444444444444", "subnet-55555555555555555"] # private subnets IDs
  load_balancer_is_internal  = true
  route53_hosted_zone_public = "whatever.com"
  
  os_distro    = "ubuntu"
  ami_id       = "ami-00000000000000000"
  ssh_key_pair = "my-key-pair-us-east-1"

  ingress_cidr_alb_allow     = ["5.5.5.0/24", "4.4.4.4/32"] # TFE users subnet, my internal VCS IP
  ingress_cidr_console_allow = ["1.1.1.1/32", "2.2.2.0/24"] # my workstation IP, IT admins workstation subnet
  ingress_cidr_ec2_allow     = ["1.1.1.1/32", "3.3.3.3/32"] # my workstation IP, my Bastion host IP
  kms_key_arn                = "arn:aws:kms:us-east-1:000000000000:key/00000000-1111-2222-3333-444444444444"
  
  rds_master_password = "MyRdsPasswd123!"
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

  friendly_name_prefix       = "cloudteam"
  tfe_license_filepath       = "./tfe-license.rli"
  tfe_hostname               = "my-tfe-instance.whatever.com"
  console_password           = "ConsolePasswd123!"
  enc_password               = "EncPasswd123!"
  vpc_id                     = "vpc-00000000000000000"
  alb_subnet_ids             = ["subnet-00000000000000000", "subnet-11111111111111111", "subnet-22222222222222222"] # public subnet IDs
  ec2_subnet_ids             = ["subnet-33333333333333333", "subnet-44444444444444444", "subnet-55555555555555555"] # private subnets IDs
  rds_subnet_ids             = ["subnet-33333333333333333", "subnet-44444444444444444", "subnet-55555555555555555"] # private subnets IDs
  route53_hosted_zone_public = "whatever.com"
  rds_master_password        = "MyRdsPasswd123!"
}
```
