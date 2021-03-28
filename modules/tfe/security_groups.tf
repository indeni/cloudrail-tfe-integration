#-------------------------------------------------------------------------------------------------------------------------------------------
# Load Balancer
#-------------------------------------------------------------------------------------------------------------------------------------------
resource "aws_security_group" "tfe_lb_allow" {
  name   = "${var.friendly_name_prefix}-tfe-lb-allow"
  vpc_id = var.vpc_id

  tags = merge({ "Name" = "${var.friendly_name_prefix}-tfe-lb-allow" }, var.common_tags)
}

resource "aws_security_group_rule" "tfe_lb_allow_inbound_https" {
  type        = "ingress"
  from_port   = 443
  to_port     = 443
  protocol    = "tcp"
  cidr_blocks = var.ingress_cidr_alb_allow
  description = "Allow HTTPS (port 443) traffic inbound to TFE LB"

  security_group_id = aws_security_group.tfe_lb_allow.id
}

resource "aws_security_group_rule" "tfe_lb_allow_inbound_http" {
  type        = "ingress"
  from_port   = 80
  to_port     = 80
  protocol    = "tcp"
  cidr_blocks = var.ingress_cidr_alb_allow
  description = "Allow HTTP (port 80) traffic inbound to TFE LB"

  security_group_id = aws_security_group.tfe_lb_allow.id
}

resource "aws_security_group_rule" "tfe_lb_allow_inbound_console" {
  type        = "ingress"
  from_port   = 8800
  to_port     = 8800
  protocol    = "tcp"
  cidr_blocks = var.ingress_cidr_console_allow == null ? var.ingress_cidr_alb_allow : var.ingress_cidr_console_allow
  description = "Allow admin console (port 8800) traffic inbound to TFE LB for TFE Replicated admin console"

  security_group_id = aws_security_group.tfe_lb_allow.id
}

#-------------------------------------------------------------------------------------------------------------------------------------------
# EC2
#-------------------------------------------------------------------------------------------------------------------------------------------
resource "aws_security_group" "tfe_ec2_allow" {
  name   = "${var.friendly_name_prefix}-tfe-ec2-allow"
  vpc_id = var.vpc_id
  tags   = merge({ "Name" = "${var.friendly_name_prefix}-tfe-ec2-allow" }, var.common_tags)
}

resource "aws_security_group_rule" "tfe_ec2_allow_https_inbound_from_lb" {
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.tfe_lb_allow.id
  description              = "Allow HTTPS (port 443) traffic inbound to TFE EC2 instance from TFE LB"

  security_group_id = aws_security_group.tfe_ec2_allow.id
}

resource "aws_security_group_rule" "tfe_ec2_allow_8800_inbound_from_lb" {
  type                     = "ingress"
  from_port                = 8800
  to_port                  = 8800
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.tfe_lb_allow.id
  description              = "Allow admin console (port 8800) traffic inbound to TFE EC2 instance from TFE LB"

  security_group_id = aws_security_group.tfe_ec2_allow.id
}

resource "aws_security_group_rule" "tfe_ec2_allow_from_self" {
  type                     = "ingress"
  from_port                = 0
  to_port                  = 0
  protocol                 = "-1"
  source_security_group_id = aws_security_group.tfe_ec2_allow.id
  description              = "Allow all traffic from self"

  security_group_id = aws_security_group.tfe_ec2_allow.id
}

resource "aws_security_group_rule" "tfe_ec2_allow_inbound_ssh" {
  count       = length(var.ingress_cidr_ec2_allow) > 0 ? 1 : 0
  type        = "ingress"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = var.ingress_cidr_ec2_allow
  description = "Allow SSH inbound to TFE EC2 instance CIDR ranges listed"

  security_group_id = aws_security_group.tfe_ec2_allow.id
}

resource "aws_security_group" "tfe_outbound_allow" {
  name   = "${var.friendly_name_prefix}-tfe-outbound-allow"
  vpc_id = var.vpc_id
  tags   = merge({ "Name" = "${var.friendly_name_prefix}-tfe-outbound-allow" }, var.common_tags)
}

resource "aws_security_group_rule" "tfe_outbound_allow_all" {
  type        = "egress"
  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]
  description = "Allow all traffic outbound from TFE"

  security_group_id = aws_security_group.tfe_outbound_allow.id
}

#-------------------------------------------------------------------------------------------------------------------------------------------
# RDS
#-------------------------------------------------------------------------------------------------------------------------------------------
resource "aws_security_group" "tfe_rds_allow" {
  name   = "${var.friendly_name_prefix}-tfe-rds-allow"
  vpc_id = var.vpc_id
  tags   = merge({ "Name" = "${var.friendly_name_prefix}-tfe-rds-allow" }, var.common_tags)
}

resource "aws_security_group_rule" "tfe_rds_allow_pg_from_ec2" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.tfe_ec2_allow.id
  description              = "Allow PostgreSQL traffic inbound to TFE RDS from TFE EC2 Security Group"

  security_group_id = aws_security_group.tfe_rds_allow.id
}