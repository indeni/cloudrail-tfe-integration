#-------------------------------------------------------------------------------------------------------------------------------------------
# AMI
#-------------------------------------------------------------------------------------------------------------------------------------------
data "aws_ami" "amzn2" {
  owners      = ["amazon"]
  most_recent = true

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-2.0*-x86_64-gp2"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

data "aws_ami" "ubuntu" {
  owners      = ["099720109477", "513442679011"]
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

locals {
  ami_lookups      = var.os_distro == "ubuntu" ? data.aws_ami.ubuntu.id : data.aws_ami.amzn2.id
  image_id_list    = list(var.ami_id, local.ami_lookups)
  root_device_name = lookup({ "amzn2" = "/dev/xvda", "ubuntu" = "/dev/sda1" }, var.os_distro, "/dev/sda1")
}

#-------------------------------------------------------------------------------------------------------------------------------------------
# Launch Template
#-------------------------------------------------------------------------------------------------------------------------------------------
locals {
  tfe_license_filepath_type = substr(var.tfe_license_filepath, 0, 5) == "s3://" ? "s3" : "local"
  tfe_default_email_domain  = join(".", slice(split(".", var.tfe_hostname), 1, length(split(".", var.tfe_hostname))))
  tfe_initial_admin_email   = var.tfe_initial_admin_email == "" ? "admin@${local.tfe_default_email_domain}" : var.tfe_initial_admin_email
  tfe_initial_org_email     = var.tfe_initial_org_email == "" ? "tfe-admins@${local.tfe_default_email_domain}" : var.tfe_initial_org_email

  tfe_user_data_vars = {
    is_secondary                  = var.is_secondary
    airgap_install                = var.airgap_install
    replicated_bundle_path        = var.replicated_bundle_path
    tfe_airgap_bundle_path        = var.tfe_airgap_bundle_path
    tfe_license_filepath_type     = local.tfe_license_filepath_type
    tfe_license_filepath          = local.tfe_license_filepath_type == "s3" ? var.tfe_license_filepath : filebase64(var.tfe_license_filepath)
    tfe_release_sequence          = var.tfe_release_sequence
    tls_bootstrap_type            = var.tls_bootstrap_type
    tls_bootstrap_cert            = var.tls_bootstrap_cert
    tls_bootstrap_key             = var.tls_bootstrap_key
    remove_import_settings_from   = var.remove_import_settings_from
    tfe_hostname                  = var.tfe_hostname
    tfe_initial_admin_username    = var.tfe_initial_admin_username
    tfe_initial_admin_email       = local.tfe_initial_admin_email
    tfe_initial_admin_password    = var.tfe_initial_admin_password
    tfe_initial_org_name          = var.tfe_initial_org_name
    tfe_initial_org_email         = local.tfe_initial_org_email
    console_password              = var.console_password
    enc_password                  = var.enc_password
    capacity_concurrency          = var.capacity_concurrency
    capacity_memory               = var.capacity_memory
    aws_secretsmanager_secret_arn = var.aws_secretsmanager_secret_arn
    s3_app_bucket_name            = aws_s3_bucket.tfe_app.id
    s3_app_bucket_region          = data.aws_region.current.name
    kms_key_arn                   = var.kms_key_arn
    pg_netloc                     = aws_rds_cluster.tfe.endpoint
    pg_dbname                     = aws_rds_cluster.tfe.database_name
    pg_user                       = aws_rds_cluster.tfe.master_username
    pg_password                   = var.rds_master_password
    custom_image_tag              = var.custom_image_tag
  }
}


resource "aws_launch_template" "tfe_lt" {
  name          = "${var.friendly_name_prefix}-tfe-ec2-asg-lt"
  image_id      = coalesce(local.image_id_list...)
  instance_type = var.instance_size
  key_name      = var.ssh_key_pair
  user_data     = base64encode(templatefile("${path.module}/templates/tfe_user_data.sh.tpl", local.tfe_user_data_vars))

  iam_instance_profile {
    name = aws_iam_instance_profile.tfe_instance_profile.name
  }

  vpc_security_group_ids = [
    aws_security_group.tfe_ec2_allow.id,
    aws_security_group.tfe_outbound_allow.id
  ]

  block_device_mappings {
    device_name = local.root_device_name

    ebs {
      volume_type = "gp2"
      volume_size = 50
    }
  }

  tag_specifications {
    resource_type = "instance"

    tags = merge(
      { "Name" = "${var.friendly_name_prefix}-tfe-ec2" },
      { "Type" = "autoscaling-group" },
      { "OS_Distro" = var.os_distro },
      var.common_tags
    )
  }

  tags = merge({ "Name" = "${var.friendly_name_prefix}-tfe-ec2-launch-template" }, var.common_tags)
}

#-------------------------------------------------------------------------------------------------------------------------------------------
# Autoscaling Group
#-------------------------------------------------------------------------------------------------------------------------------------------
resource "aws_autoscaling_group" "tfe_asg" {
  name                      = "${var.friendly_name_prefix}-tfe-asg"
  min_size                  = 0
  max_size                  = 1
  desired_capacity          = var.asg_instance_count
  vpc_zone_identifier       = var.ec2_subnet_ids
  health_check_grace_period = 900
  health_check_type         = "ELB"

  launch_template {
    id      = aws_launch_template.tfe_lt.id
    version = "$Latest"
  }

  target_group_arns = [
    aws_lb_target_group.tfe_tg_443.arn,
    aws_lb_target_group.tfe_tg_8800.arn
  ]

  tag {
    key                 = "Name"
    value               = "${var.friendly_name_prefix}-tfe-asg"
    propagate_at_launch = false
  }

  dynamic "tag" {
    for_each = var.common_tags

    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = false
    }
  }

  depends_on = [aws_rds_cluster_instance.tfe]
}
