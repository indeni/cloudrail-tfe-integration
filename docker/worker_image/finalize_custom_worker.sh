#!/bin/bash
set -o allexport
# read all files into environment variables
for filename in ./env/*; do
  variableName=$(basename $filename)
  variableValue=$(cat $filename)
  eval ${variableName}=`echo -ne \""${variableValue}"\"`
done

# do not run cloudrail if cloudrail_api_key is not set
[ -z "$CLOUDRAIL_API_KEY"] && exit 0

# only run cloudrail during plan. check if assessment has already run for run_id
assessments=$(curl https://api.cloudrail.app/assessments -H "X-Api-Key: ${CLOUDRAIL_API_KEY}")
curAssessment=$(echo $assessments | jq ".page_results[] | select(.execution_source_identifier == \"${TFE_RUN_ID}\")")
if [ -z "$curAssessment" ]
then
  cd /terraform
  cloudrail run -p terraform.tfplan --auto-approve --origin ci --build-link https://app.terraform.io --cloud-account-id $CLOUD_ACCOUNT_ID --execution-source-identifier $TFE_RUN_ID
  status=$?
  ## return exit code if not 0 or 1 ## 
  if [[ $status -eq 0 || $status -eq 1 ]]; then exit 0; else exit $status; fi
fi

