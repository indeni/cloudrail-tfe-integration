data "template_file" "instance_role_policy" {
  template = file("${path.module}/templates/tfe-instance-role-policy.json")

  vars = {
    app_bucket_arn                = aws_s3_bucket.tfe_app.arn
    bootstrap_bucket_arn          = var.tfe_bootstrap_bucket != "" ? data.aws_s3_bucket.bootstrap_bucket[0].arn : ""
    kms_key_arn                   = var.kms_key_arn
    aws_secretsmanager_secret_arn = var.aws_secretsmanager_secret_arn
  }
}

resource "aws_iam_role" "tfe_instance_role" {
  name               = "${var.friendly_name_prefix}-tfe-instance-role-${data.aws_region.current.name}"
  path               = "/"
  assume_role_policy = file("${path.module}/templates/tfe-instance-role.json")

  tags = merge({ "Name" = "${var.friendly_name_prefix}-tfe-instance-role" }, var.common_tags)
}

resource "aws_iam_role_policy" "tfe_instance_role_policy" {
  name   = "${var.friendly_name_prefix}-tfe-instance-role-policy-${data.aws_region.current.name}"
  policy = data.template_file.instance_role_policy.rendered
  role   = aws_iam_role.tfe_instance_role.id
}

resource "aws_iam_instance_profile" "tfe_instance_profile" {
  name = "${var.friendly_name_prefix}-tfe-instance-profile-${data.aws_region.current.name}"
  path = "/"
  role = aws_iam_role.tfe_instance_role.name
}