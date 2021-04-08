locals {
  organizations = toset(var.organizations)
}

data "tfe_workspace_ids" "all" {
  for_each     = local.organizations
  names        = ["*"]
  organization = each.key
}

locals {
  org_ws_map = { for v in data.tfe_workspace_ids.all : v.organization => values(v.external_ids) }
  flatten    = transpose(local.org_ws_map)
  ws_org_map = { for k, v in local.flatten : k => v[0] }
}

resource "tfe_variable" "cloudrail_api_key" {
  for_each     = local.ws_org_map
  key          = "CLOUDRAIL_API_KEY"
  value        = var.cloudrail_token
  category     = "env"
  workspace_id = each.key
  sensitive    = true
  description  = "Cloudrail API Key"
}

resource "tfe_variable" "cloud_account_id" {
  for_each     = local.ws_org_map
  key          = "CLOUD_ACCOUNT_ID"
  value        = var.cloud_account_id
  category     = "env"
  workspace_id = each.key
  description  = "Cloudrail Cloud Account ID"
}


resource "tfe_policy_set" "cloudrail" {
  for_each      = local.organizations
  name          = "cloudrail-policy-set"
  description   = "A Cloudrail integration with TFE"
  organization  = each.key
  workspace_ids = local.org_ws_map[each.key]
  policies_path = "policies"
}

// eventually this should be replaced with a real TFE resource
// see TFE provider issue: https://github.com/hashicorp/terraform-provider-tfe/issues/289
resource "shell_script" "upload_policy_data" {
  for_each      = local.organizations
  lifecycle_commands {
    create = file("${path.module}/scripts/create.sh")
    delete = file("${path.module}/scripts/delete.sh")
  }

  environment = {
    POLICY_SET_ID = tfe_policy_set.cloudrail[each.key].id
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
