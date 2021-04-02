locals {
  organizations = toset(var.organizations)
}

resource "tfe_policy_set" "cloudrail" {
  for_each      = local.organizations
  name          = "cloudrail-policy-set"
  description   = "A cloudrails integration with TFE"
  organization  = each.key
  global        = true
  policies_path = "policies"
}

// eventually this should be replaced with a real TFE resource
// see TFE provider issue: https://github.com/hashicorp/terraform-provider-tfe/issues/289
resource "shell_script" "upload_policy_data" {
  lifecycle_commands {
    create = file("${path.module}/scripts/create.sh")
    delete = file("${path.module}/scripts/delete.sh")
  }

  environment = {
    POLICY_SET_ID = tfe_policy_set.cloudrail["TestOrg"].id
    TFE_HOSTNAME  = var.tfe_hostname
  }
}

resource "tfe_policy_set_parameter" "cloudrail" {
  for_each      = local.organizations
  key           = "cloudrailToken"
  value         = var.cloudrail_token
  policy_set_id = tfe_policy_set.cloudrail[each.key].id
  sensitive     = true
}
