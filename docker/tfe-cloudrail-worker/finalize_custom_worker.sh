#!/bin/bash
set -o allexport

# Read all files into environment variables
for filename in /env/*; do
  variableName=$(basename $filename)
  variableValue=$(cat $filename)
  eval ${variableName}=`echo -ne \""${variableValue}"\"`
done

# Debug
function debug(){
  if [ "$CLOUDRAIL_DEBUG" = true ]
  then
    echo "Environment Variables:"
    env
    cloudrail --version
    terraform --version
    echo "TFE run result: " $tfe_result
    echo "TFE run status: " $tfe_status
    echo "Cloudrail run status: " $cloudrailStatus    
    exit 1  #Force error to print debug messages    
  fi
}

# If CLOUDRAIL_API_KEY is not set, exit
if [ -z "$CLOUDRAIL_API_KEY" ]
then
  echo "Cloudrail CLOUDRAIL_API_KEY environment variable not set. Will not run Cloudrail"
  debug
  exit 0
fi

# Get Terraform run status from TFE API
tfe_result=$(curl -s --header "Authorization: Bearer $ATLAS_TOKEN" --header "Content-Type: application/vnd.api+json" ${ATLAS_ADDRESS}/api/v2/runs/${TFE_RUN_ID})
tfe_status=$(echo $tfe_result | jq -r '.data.attributes.status')

# Only run cloudrail during plan, check value of plan status
[ "$tfe_status" != "planning" ] && exit 0

# Set Cloudrail analysis
if [ "${CLOUDRAIL_STATIC:-false}" = true ] 
then
  # Do Cloudrail Static Analysis --no-cloud-account
  CLOUDRAIL_MODE="--no-cloud-account"
elif [ -n "$CLOUD_ACCOUNT_ID" ]
then
  # Do Cloudrail Dynamic Analysis --cloud-account-id
  CLOUDRAIL_MODE="--cloud-account-id $CLOUD_ACCOUNT_ID"
else
  # No static or dynamic. Nothing to do.
  debug
  exit 0
fi

# Run Cloudrail
# Use CLOUDRAIL_EXTRA_VARS for --upload-log, --drift-track (execute 'cloudrail run --help' for other options)
cd /terraform
ORG_NAME=$(echo ${TF_VAR_TFC_WORKSPACE_SLUG} | cut -d "/" -f 1)
WS_NAME=$(echo ${TF_VAR_TFC_WORKSPACE_SLUG} | cut -d "/" -f 2)
BUILD_LINK="${ATLAS_ADDRESS}/app/${ORG_NAME}/workspaces/${WS_NAME}/runs/$TFE_RUN_ID"

cloudrail run -d /terraform$TF_ATLAS_DIR -p terraform.tfplan --auto-approve --origin ci $CLOUDRAIL_MODE --build-link $BUILD_LINK --execution-source-identifier $TFE_RUN_ID $CLOUDRAIL_EXTRA_VARS
cloudrailStatus=$?

#Print debug info
debug

#Not running sentinel, report errors in console if any
if [ "$CLOUDRAIL_SENTINEL" = false ]
then
  exit $cloudrailStatus;
else # CLOUDRAIL_SENTINEL true or not defined: Sentinel will report issues later on, accepts status 0 (ok) or 1 (mandated rules found violations) as sucess and continue to Sentinel
  if [[ $cloudrailStatus -eq 0 || $cloudrailStatus -eq 1 ]]; then exit 0; else exit $cloudrailStatus; fi
fi
