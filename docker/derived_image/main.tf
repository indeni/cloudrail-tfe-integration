resource "null_resource" {
  provisioner "local-exec" {
    command = "echo hello"
  }
}