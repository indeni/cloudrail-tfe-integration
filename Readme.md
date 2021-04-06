# Cloudrail TFE Integration
Prerequisite – have TFE deployed. See example configuration code in [/terraform/tfe-deployment](/terraform/tfe-deployment).

Follow the guide below to integrate Cloudrail into your workspaces. This will require using a custom docker image, which will contain the Cloudrail CLI code as well as a finalizer script. In addition, Sentinel policies will be added in order to use Cloudrail's output as part of the Terraform Enterprise runs.

## Create Cloudrail base worker image
1. Create base Ubuntu image with Cloudrail installed on it.
1.a.	This image also has a finalizer script to run `cloudrail run` after Terraform plan for workspaces with CLOUDRAIL_API_KEY environment variable set. Alternatively, you could require customers to add this finalizer script themselves, although this seems less convenient
2. Upload custom worker image to dockerhub.io

## Configure TFE to use Cloudrail image
3. Reference docker image in TFE application settings file (or manually via Admin console): https://www.terraform.io/docs/enterprise/install/automating-the-installer.html#custom_image_tag
3.a. Increase container memory to at least 1GB for Cloudrail to run successfully.
4. Restart TFE service to enable custom worker image to be used for runs.
5. Create Sentinel policy set with three policies, one for each level (advisory, soft-mandatory, hard-mandatory) and attach these policies to each workspace in organization that is to be integrated with Cloudrail (can be automated with Terraform or bash script). Sample Sentinel policies are available in [/sentinel](/sentinel).
6. Create a workspace in TFE
6.a. Set the CLOUDRAIL_API_KEY environment variable. This is required by the finalizer script. Alternatively, this environment variable could be provided by TFE Admins when building custom worker image.
6.b. Set the CLOUD_ACCOUNT_ID for specific workspaces. This is the identifier of the cloud account (for example, 12 digits for AWS accounts), against which you'd like to run Cloudrail. As a reminder, Cloudrail inspects a Terraform plan by merging it (in memory) with a recent snapshot of the target cloud account, in order to generate a full prediction of how the account will look like if the plan were to be applied.
7. Queue run in workspace.
8. Voila!
