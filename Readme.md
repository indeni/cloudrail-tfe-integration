# Cloudrail TFE Integration
Prerequisite – have TFE deployed. See example configuration code in /terraform/tfe-deployment

## Create Cloudrail base worker image
1)	Create base Ubuntu image with cloudrails installed on it
a.	This image also has a finalizer script to run cloudrail after Terraform plan for workspaces with CLOUDRAIL_API_KEY environment variable set. Alternatively, you could require customers to add this finalizer script themselves, although this seems less convenient
2)	Upload custom worker image to dockerhub.io

## Configure TFE to use Cloudrail image
3)	Reference docker image in TFE application settings file (or manually via Admin console): https://www.terraform.io/docs/enterprise/install/automating-the-installer.html#custom_image_tag
a.	Container size increased memory to at least 1GB for cloudrails to run.
4)	Restart TFE service to enable custom worker image to be used for runs
5)	Create Sentinel policy set with three policies, one for each level (advisory, soft-mandatory, hard-mandatory) and attach these policies to each workspace in organization that is to be integrated with cloudrails (can be automated with Terraform or bash script)
6)	Create a workspace in TFE
a.	Set the CLOUDRAIL_API_KEY environment variable. This is required by the finalizer script. Alternatively, this environment variable could be provided by TFE Admins when building custom worker image.
b.	Set some environment variable for specifying cloud account id, if more than one account id specified. Not sure what this is?
7)	Queue run in workspace
