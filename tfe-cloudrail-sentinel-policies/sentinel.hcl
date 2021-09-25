policy "cloudrail-advisory" {
  source            = "./cloudrail-advisory.sentinel"
  enforcement_level = "advisory"
}

policy "cloudrail-soft-mandatory" {
  source            = "./cloudrail-soft-mandatory.sentinel"
  enforcement_level = "soft-mandatory"
}