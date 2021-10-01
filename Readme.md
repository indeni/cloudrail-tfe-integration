# Cloudrail TFE Integration

## Prerequisites
* Working installation of [Terraform Enterprise](https://www.terraform.io/docs/enterprise/index.html). See example configuration code in [/terraform/tfe-deployment](terraform/tfe-deployment).
* Public or private version control system (VCS)
* Cloud account in AWS or Azure
* [Cloudrail account](https://web.cloudrail.app/), with the API key, and your cloud account added
* [Docker Repository](https://hub.docker.com/)

Follow the guide below to integrate Cloudrail into your Terraform Enterprise workspaces or see a detailed tutorial in the [Cloudrail Blog](https://indeni.com/blog/). This will require using a custom docker image, which will contain the Cloudrail CLI code as well as a finalizer script. 

## Create Cloudrail base worker image
1. Create base Ubuntu Docker image with Cloudrail installed on it. See example in [/docker/tfe-cloudrail-worker](docker/tfe-cloudrail-worker).

        docker build . -t company/tfe-cloudrail-worker

    This image also has a finalizer script to run `cloudrail run` after Terraform plan for workspaces with `CLOUDRAIL_API_KEY` environment variable set.
2. Upload custom worker image to dockerhub.io

        docker push company/tfe-cloudrail-worker

 
## Configure TFE to use Cloudrail image
1. Reference docker image in [TFE application settings file]((https://www.terraform.io/docs/enterprise/install/automating-the-installer.html#custom_image_tag)), or [manually via Admin console](https://www.terraform.io/docs/enterprise/install/installer.html#alternative-terraform-worker-image): 

2. Increase container memory to at least 1GB for Cloudrail to run successfully.
3. Restart TFE service to enable custom worker image to be used for runs.
4. Create Sentinel policy set with two policies, one for each level (advisory, mandatory) and [attach these policies to each workspace](https://www.terraform.io/docs/cloud/sentinel/manage-policies.html#managing-policy-sets) tha requires Cloudrail integration.  Sample Sentinel policies are available in [/tfe-cloudrail-sentinel-policies](tfe-cloudrail-sentinel-policies).
6. Create a workspace in TFE

    6.a. Set the `CLOUDRAIL_API_KEY` environment variable. 
    
    This is required by the finalizer script. Alternatively, this environment variable could be provided by TFE Admins when building custom worker image.
    
    6.b. Set the `CLOUD_ACCOUNT_ID` for specific workspaces. 
    
    This is the identifier of the cloud account (for example, 12 digits for AWS accounts), against which you'd like to run Cloudrail. 
    
    As a reminder, Cloudrail inspects a Terraform plan by merging it (in memory) with a recent snapshot of the target cloud account, in order to generate a full prediction of how the account will look like if the plan were to be applied.
5. Queue run in workspace.
6. You have successfully completed a [Cloudrail Dynamic Analysis](https://indeni.com/cloudrail/).

