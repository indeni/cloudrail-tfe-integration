resource "aws_acm_certificate" "tfe_cert" {
  count = var.tls_certificate_arn == null && var.route53_hosted_zone_public != null ? 1 : 0

  domain_name       = var.tfe_hostname
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = merge({ "Name" = "${var.friendly_name_prefix}-tfe-alb-acm-cert" }, var.common_tags)
}

resource "aws_acm_certificate_validation" "tfe_cert_validation" {
  count = length(aws_acm_certificate.tfe_cert) == 1 ? 1 : 0

  certificate_arn         = aws_acm_certificate.tfe_cert[0].arn
  validation_record_fqdns = [aws_route53_record.tfe_cert_validation_record[0].fqdn]
}