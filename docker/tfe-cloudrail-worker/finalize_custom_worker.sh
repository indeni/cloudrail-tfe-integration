#!/bin/bash
set -o allexport
# read all files into environment variables
for filename in /env/*; do
  variableName=$(basename $filename)
  variableValue=$(cat $filename)
  eval ${variableName}=`echo -ne \""${variableValue}"\"`
done

# Debug
if [ "$CLOUDRAIL_DEBUG" = true ]
then
  for filename in /env/*; do
    variableName=$(basename $filename)
    variableValue=$(cat $filename)
    echo $variableName = $variableValue 
  done
  cloudrail --version
  terraform --version
fi

# do not run cloudrail if cloudrail_api_key is not set
[ -z "$CLOUDRAIL_API_KEY" ] && exit 0

# only run cloudrail during plan. check if assessment has already run for run_id
assessments=$(curl https://api.cloudrail.app/v1/assessments?query=$TFE_RUN_ID -H "X-Api-Key: ${CLOUDRAIL_API_KEY}")
curAssessment=$(echo $assessments | jq ".page_results[] | select(.execution_source_identifier == \"${TFE_RUN_ID}\")")

if [ -z "$curAssessment" ]
  #create link to run
  ORG_NAME=$(echo ${TF_VAR_TFC_WORKSPACE_SLUG} | cut -d "/" -f 1)
  WS_NAME=$(echo ${TF_VAR_TFC_WORKSPACE_SLUG} | cut -d "/" -f 2)
  BUILD_LINK="${ATLAS_ADDRESS}/app/${ORG_NAME}/workspaces/${WS_NAME}/runs/$TFE_RUN_ID"
then
  cd /terraform
  # -p                The file path that was used in "terraform plan -out=file" call
  # -d                The root directory of the .tf files /terraform$TF_ATLAS_DIR
  # --auto-approve    Should we auto approve sending the filtered plan to the Cloudrail Service
  # --origin ci       Where is Cloudrail being used "workstation" or "ci"
  # --build-link      Supply a link directly to the build in TFE
  # --execution-source-identifier   An identifier that will help users understand the context of execution for this run
  # CLOUDRAIL_EXTRA_VARS: can contain --upload-log
  cloudrail run -d /terraform$TF_ATLAS_DIR -p terraform.tfplan --auto-approve --origin ci --build-link $BUILD_LINK --cloud-account-id $CLOUD_ACCOUNT_ID --execution-source-identifier $TFE_RUN_ID $CLOUDRAIL_EXTRA_VARS
  status=$?
  #if [[ $status -eq 0 || $status -eq 1 ]]; then exit 0; else exit $status; fi

  if [ "$CLOUDRAIL_DEBUG" = true ]
  then
    echo cloudrail run -d /terraform$TF_ATLAS_DIR -p terraform.tfplan --auto-approve --origin ci --build-link $BUILD_LINK --cloud-account-id $CLOUD_ACCOUNT_ID --execution-source-identifier $TFE_RUN_ID $CLOUDRAIL_EXTRA_VARS
    echo "status = " $status
    exit 1
  fi
  #Not running sentinel, report errors
  if [ "$CLOUDRAIL_SENTINEL" = false ]
  then
    exit $status;
  else # CLOUDRAIL_SENTINEL true or not defined: Sentinel will report issues, accepts status 0 (ok) or 1 (error)
    if [[ $status -eq 0 || $status -eq 1 ]]; then exit 0; else exit $status; fi
  fi

fi
