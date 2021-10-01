
# Cloudrail module: checks asessment results
module "cloudrail" {
  source = "./modules/cloudrail.sentinel"
}

# Sentinel Enforcement Levels
# hard-mandatory: requires that the policy passes. If a policy fails, the run is halted and may not be applied until the failure is resolved.
# soft-mandatory: is much like hard-mandatory, but allows any user with the Manage Policy Overrides permission to override policy failures on a case-by-case basis.
# advisory: will never interrupt the run, and instead will only surface policy failures as informational to the user.

# Check Cloudrail for advisory rules
policy "cloudrail-advisory" {
  source            = "./cloudrail-advisory.sentinel"
  enforcement_level = "advisory"
}

# Check Cloudrail for mandatory company rules.
policy "cloudrail-mandatory" {
  source            = "./cloudrail-mandatory.sentinel"
  enforcement_level = "hard-mandatory"    # Change to "soft-mandatory" if user should be able to by pass rules manadatory company rules.
}
