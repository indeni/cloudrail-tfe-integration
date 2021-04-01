#!/bin/bash

# do POST
resp=$(curl \
  --header "Authorization: Bearer ${TFE_TOKEN}" \
  --header "Content-Type: application/vnd.api+json" \
  --request POST \
  https://${TFE_HOSTNAME}/api/v2/policy-sets/${POLICY_SET_ID}/versions)

echo $resp
upload_url=$(echo $resp | jq -r .data.links.upload)
echo $upload_url
resp=$(curl \
  --header "Content-Type: application/octet-stream" \
  --request PUT \
  --data-binary @policies.tar.gz \
  ${upload_url})

echo $resp