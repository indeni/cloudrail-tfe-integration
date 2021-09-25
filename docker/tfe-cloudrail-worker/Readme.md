# Building you own Terraform Alternative Worker


## Docker file

The Dockerfile includes the common instructions to build a [Terraform Alternative Worker](https://www.terraform.io/docs/enterprise/install/installer.html#alternative-terraform-worker-image) and the requirements to install Cloudrail CLI. See a detailed tutorial in the [Cloudrail Blog](https://indeni.com/blog/)

## init_custom_worker.sh

The script is executed before Terraform plan, apply or destroy. Not currently needed for the integration.


## finalize_custom_worker.sh
The script is executed after Terraform plan, apply or destroy and has been customized to analyze with Cloudrail the Terraform planned changes.


## Building the Docker image

Build the Docker image and upload it to your Docker Hub or Repository

```
$ docker build . -t company/tfe-cloudrail-worker
Sending build context to Docker daemon  10.24kB
Step 1/12 : FROM ubuntu:focal
 ---> fb52e22af1b0
…
$ docker push company/tfe-cloudrail-worker
Using default tag: latest
...

```

