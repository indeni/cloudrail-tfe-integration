data "aws_route53_zone" "public" {
  count = var.route53_hosted_zone_public != null ? 1 : 0

  name         = var.route53_hosted_zone_public
  private_zone = false
}

resource "aws_route53_record" "tfe_alb_alias_record" {
  count = var.route53_hosted_zone_public != null && var.create_route53_alias_record == true ? 1 : 0

  name    = var.tfe_hostname
  zone_id = data.aws_route53_zone.public[0].zone_id
  type    = "A"

  alias {
    name                   = aws_lb.tfe_alb.dns_name
    zone_id                = aws_lb.tfe_alb.zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "tfe_cert_validation_record" {
  count = length(aws_acm_certificate.tfe_cert) == 1 && var.route53_hosted_zone_public != null ? 1 : 0

  name            = element(aws_acm_certificate.tfe_cert[0].domain_validation_options[*].resource_record_name, 0)
  type            = element(aws_acm_certificate.tfe_cert[0].domain_validation_options[*].resource_record_type, 0)
  records         = aws_acm_certificate.tfe_cert[0].domain_validation_options[*].resource_record_value
  zone_id         = data.aws_route53_zone.public[0].zone_id
  ttl             = 60
  allow_overwrite = true
}