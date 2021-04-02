terraform {
  backend "remote" {
    hostname = "cloudrail-tfe-integration.com"
    organization = "TestOrg"

    workspaces {
      name = "test_deploy"
    }
  }
}

resource "null_resource" "penguins" {
  triggers = {
    always = timestamp()
 }
  provisioner "local-exec" {
      command = "echo hello"
    }
}