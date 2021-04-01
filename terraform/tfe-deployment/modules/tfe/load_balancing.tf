resource "aws_lb" "tfe_alb" {
  name               = "${var.friendly_name_prefix}-tfe-web-alb"
  internal           = var.load_balancer_is_internal
  load_balancer_type = "application"
  subnets            = var.alb_subnet_ids

  security_groups = [
    aws_security_group.tfe_lb_allow.id,
    aws_security_group.tfe_outbound_allow.id
  ]

  tags = merge({ "Name" = "${var.friendly_name_prefix}-tfe-alb" }, var.common_tags)
}

resource "aws_lb_listener" "tfe_listener_443" {
  count = var.tls_certificate_arn == null && length(aws_acm_certificate.tfe_cert) == 0 ? 0 : 1

  load_balancer_arn = aws_lb.tfe_alb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = element(coalescelist(aws_acm_certificate.tfe_cert[*].arn, list(var.tls_certificate_arn)), 0)

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tfe_tg_443.arn
  }

  depends_on = [aws_acm_certificate.tfe_cert]
}

resource "aws_lb_listener" "tfe_listener_80_rd" {
  load_balancer_arn = aws_lb.tfe_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = 443
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "tfe_listener_8800" {
  count = var.tls_certificate_arn == null && length(aws_acm_certificate.tfe_cert) == 0 ? 0 : 1

  load_balancer_arn = aws_lb.tfe_alb.arn
  port              = 8800
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = element(coalescelist(aws_acm_certificate.tfe_cert[*].arn, list(var.tls_certificate_arn)), 0)

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tfe_tg_8800.arn
  }

  depends_on = [aws_acm_certificate.tfe_cert]
}

resource "aws_lb_target_group" "tfe_tg_443" {
  name     = "${var.friendly_name_prefix}-tfe-alb-tg-443"
  port     = 443
  protocol = "HTTPS"
  vpc_id   = var.vpc_id

  health_check {
    path                = "/_health_check"
    protocol            = "HTTPS"
    matcher             = 200
    healthy_threshold   = 5
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 15
  }

  tags = merge(
    { "Name" = "${var.friendly_name_prefix}-tfe-alb-tg-443" },
    { "Description" = "ALB Target Group for TFE web application HTTPS traffic" },
    var.common_tags
  )
}

resource "aws_lb_target_group" "tfe_tg_8800" {
  name     = "${var.friendly_name_prefix}-tfe-alb-tg-8800"
  port     = 8800
  protocol = "HTTPS"
  vpc_id   = var.vpc_id

  health_check {
    path     = "/ping"
    protocol = "HTTPS"
    matcher  = "200-399"
  }

  tags = merge(
    { "Name" = "${var.friendly_name_prefix}-tfe-alb-tg-8800" },
    { "Description" = "ALB Target Group for TFE/Replicated web admin console traffic over port 8800" },
    var.common_tags
  )
}