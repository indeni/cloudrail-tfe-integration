#!/bin/bash
set -o allexport
# read all files into environment
for filename in ./env/*; do
  variableName=$(basename $filename)
  variableValue=$(cat $filename)
  eval ${variableName}=`echo -ne \""${variableValue}"\"`
done

# run cloudrails
cd /terraform
cloudrail run -p terraform.tfplan --auto-approve --origin ci --build-link https://app.terraform.io --cloud-account-id $CLOUD_ACCOUNT_ID --execution-source-identifier $TFE_RUN_ID
exit 0