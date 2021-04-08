#!/usr/bin/env bash

set -euo pipefail
SECONDS=0

install_dependencies () {
  if [[ "${airgap_install}" == "true" ]]; then
    echo "INFO: Detected airgap_install flag is set to true."

    if [[ -z "$(command -v jq)" ]]; then 
      echo "ERROR: jq not detected on system. Ensure jq is installed on image before deploying."
      exit_script 2
    fi

    if [[ -z "$(command -v unzip)" ]]; then
      echo "ERROR: unzip not detected on system. Ensure unzip is installed on image before running."
      exit_script 3
    fi

    if [[ -z "$(command -v docker)" ]]; then
      echo "ERROR: docker was not detected on system. Ensure docker is installed on image before running."
      exit_script 4
    fi

    if [[ -z "$(command -v aws)" ]]; then
      echo "ERROR: awscli not detected on system. Ensure awscli is installed on image before running."
      exit_script 5
    fi
  
  elif [[ -n "$(command -v yum)" ]]; then 
    echo "INFO: Detected OS with yum package manager. Installing dependencies."
    sudo yum update -y
    sudo yum install -y jq unzip
    install_awscli

  elif [[ -n "$(command -v apt-get)" ]]; then
    echo "INFO: Detected OS with apt package manager. Installing dependencies."
    apt-get update -y
    apt-get install jq unzip -y
    install_awscli

  else
    echo "ERROR: Unable to detect OS package manager."
    exit_script 1
  fi
}


install_awscli () {
  if [[ -n "$(command -v aws)" ]]; then 
    echo "INFO: Detected awscli is already installed. Skipping awscli install."
  else
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
  fi
}


retrieve_license_from_s3 () {
  echo "INFO: Copying ${tfe_license_filepath} to $TFE_LICENSE_PATH."
  aws s3 cp "${tfe_license_filepath}" "$TFE_LICENSE_PATH"
}


retrieve_license_from_local () {
  echo "INFO: Decoding ${tfe_license_filepath} and copying to $TFE_LICENSE_PATH."
  cat > /tmp/license.rli.base64 << EOF
${tfe_license_filepath}
EOF
  
  base64 --decode /tmp/license.rli.base64 > $TFE_LICENSE_PATH
}


retrieve_airgap_bundle_from_s3 () {
  if [[ "${tfe_airgap_bundle_path}" == "" ]]; then
    echo "ERROR: Did not detect valid tfe_airgap_bundle_path."
    exit_script 30
  else
    echo "INFO: Copying ${tfe_airgap_bundle_path} to $TFE_AIRGAP_PATH..."
    aws s3 cp "${tfe_airgap_bundle_path}" "$TFE_AIRGAP_PATH"
  fi
}


retrieve_replicated_bundle_from_s3 () {
  if [[ "${replicated_bundle_path}" == "" ]]; then
    echo "ERROR: Did not detect valid replicated_bundle_path. Exiting."
    exit_script 31
  else
    echo "INFO: Copying ${replicated_bundle_path} to $REPL_BUNDLE_PATH..."
    aws s3 cp "${replicated_bundle_path}" "$REPL_BUNDLE_PATH"
  fi
}


validate_aws_secretsmanager_arn () {
  if [[ "${aws_secretsmanager_secret_arn}" == "" ]]; then
    echo "ERROR: aws_secretsmanager_secret_arn is not set."
    exit_script 40
  fi
}


retrieve_console_password () {
  if [[ "${console_password}" == "aws_secretsmanager" ]]; then
    echo "INFO: Retrieving console_password from AWS Secrets Manager."
    validate_aws_secretsmanager_arn
    CONSOLE_PASSWORD=$(aws secretsmanager get-secret-value --region ${s3_app_bucket_region} --secret-id ${aws_secretsmanager_secret_arn} --query SecretString --output text | jq -r '.console_password')
  else
    echo "INFO: Retrieving console_password from Terraform input variable."
    CONSOLE_PASSWORD=${console_password}
  fi
}


retrieve_enc_password () {
  if [[ "${enc_password}" == "aws_secretsmanager" ]]; then
    echo "INFO: Retrieving enc_password from AWS Secrets Manager."
    validate_aws_secretsmanager_arn
    ENC_PASSWORD=$(aws secretsmanager get-secret-value --region ${s3_app_bucket_region} --secret-id ${aws_secretsmanager_secret_arn} --query SecretString --output text | jq -r '.enc_password')
  else
    echo "INFO: Retrieving enc_password from Terraform input variable."
    ENC_PASSWORD=${enc_password}
  fi
}


retrieve_tfe_initial_admin_password () {
  if [[ "${tfe_initial_admin_username}" == "" ]]; then
    return 0
  elif [[ "${tfe_initial_admin_username}" != "" ]] && [[ "${tfe_initial_admin_password}" == "aws_secretsmanager" ]]; then
    echo "INFO: Retrieving tfe_initial_admin_password from AWS Secrets Manager."
    validate_aws_secretsmanager_arn
    TFE_INITIAL_ADMIN_PASSWORD=$(aws secretsmanager get-secret-value --region ${s3_app_bucket_region} --secret-id ${aws_secretsmanager_secret_arn} --query SecretString --output text | jq -r '.tfe_initial_admin_password')
  elif [[ "${tfe_initial_admin_username}" != "" ]] && [[ "${tfe_initial_admin_password}" == "" ]]; then
    echo "ERROR: A value for tfe_initial_admin_user was specified so tfe_initial_admin_password must also be specified."
    exit_script 41
  elif [[ "${tfe_initial_admin_username}" != "" ]] && [[ "${tfe_initial_admin_password}" != "aws_secretsmanager" ]]; then
    echo "INFO: Retrieving tfe_initial_admin_password from Terraform variable."
    TFE_INITIAL_ADMIN_PASSWORD=${tfe_initial_admin_password}
  else
    echo "WARNING: An unexpected condition occured in retrieving tfe_initial_admin_password."
  fi
}


tfe_bootstrap_initial_admin_user () {
  echo "INFO: Creating Initial Admin User: ${tfe_initial_admin_username}."
  
  # retrieve Initial Admin Creation Token (IACT)
  IACT=$(replicated admin --tty=0 retrieve-iact)

  # build payload for TFE Initial Admin User API call
  cat > $TFE_CONFIG_DIR/tfe_initial_admin_user.json << EOF
{
  "username": "${tfe_initial_admin_username}",
  "email": "${tfe_initial_admin_email}",
  "password": "$TFE_INITIAL_ADMIN_PASSWORD"
}
EOF

  # POST request to create Initial Admin User and store token
  IAUT=$(curl \
           -k \
           --header "Content-Type: application/json" \
           --request POST \
           --data @$TFE_CONFIG_DIR/tfe_initial_admin_user.json \
           "https://$EC2_PRIVATE_IP/admin/initial-admin-user?token=$IACT" | jq -r '.token'
        )
}


tfe_bootstrap_initial_organization () {
  echo "INFO: Preparing to create TFE Organization: ${tfe_initial_org_name}."
  
  # check if Initial Admin User Token has already been used to be idempotent
  if [[ "$IAUT" == "null" ]]; then
    echo "INFO: Detected Initial Admin User Token (IAUT) has already been used."
    echo "INFO: Skipping TFE Organization creation."
    return 0
  
  else
    # build payload for initial TFE Organization creation
    cat > $TFE_CONFIG_DIR/tfe_initial_org.json << EOF
{
  "data": {
    "type": "organizations",
    "attributes": {
      "name": "${tfe_initial_org_name}",
      "email": "${tfe_initial_org_email}"
    }
  }
}
EOF
    
    # POST request to create initial TFE Organization
    echo "INFO: Creating TFE Organization: ${tfe_initial_org_name}."
    curl \
      -k \
      --header "Authorization: Bearer $IAUT" \
      --header "Content-Type: application/vnd.api+json" \
      --request POST \
      --data @$TFE_CONFIG_DIR/tfe_initial_org.json "https://$EC2_PRIVATE_IP/api/v2/organizations"
  fi
}


cleanup_tfe_files () {
  rm -f $TFE_CONFIG_DIR/tfe_initial_admin_user.json
}


exit_script () {
  cleanup_tfe_files
  DURATION=$SECONDS
  echo "INFO: $(($DURATION / 60)) minutes and $(($DURATION % 60)) seconds elapsed."
  
  if [[ "$1" == 0 ]]; then
    echo "INFO: TFE user_data script finished successfully!"
  else
    echo "ERROR: TFE user_data script finished with error code "$1"."
  fi
  
  exit "$1"
}


main () {
  echo "INFO: Beginning TFE user_data script."

  # determine OS, update packages, and install software dependencies
  install_dependencies

  # set up variables, file paths, and directories 
  TFE_INSTALLER_DIR="/opt/tfe/installer"
  TFE_CONFIG_DIR="/opt/tfe/config"
  TFE_SETTINGS_PATH="$TFE_CONFIG_DIR/settings.json"
  TFE_LICENSE_PATH="$TFE_CONFIG_DIR/license.rli"
  TFE_AIRGAP_PATH="$TFE_INSTALLER_DIR/tfe-bundle.airgap"
  REPL_BUNDLE_PATH="$TFE_INSTALLER_DIR/replicated.tar.gz"
  REPL_CONF_PATH="/etc/replicated.conf"

  mkdir -p $TFE_INSTALLER_DIR
  mkdir -p $TFE_CONFIG_DIR
  
  # collect AWS EC2 instance metadata
  EC2_PRIVATE_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)
  
  # retrieve TFE license file
  if [[ "${tfe_license_filepath_type}" == "s3" ]]; then
    retrieve_license_from_s3
  elif [[ "${tfe_license_filepath_type}" == "local" ]]; then
    retrieve_license_from_local
  else
    echo "ERROR: Did not detect valid value for tfe_license_filepath_type."
    exit_script 20
  fi

  # retrieve TFE install bits
  if [[ "${airgap_install}" == "true" ]]; then
    retrieve_replicated_bundle_from_s3
    retrieve_airgap_bundle_from_s3
  else
    # retrieve install.sh online
    echo "INFO: Retrieving TFE install script directly from Replicated."
    curl https://install.terraform.io/ptfe/stable -o "$TFE_INSTALLER_DIR/install.sh"
  fi
  
  # retrieve install secrets
  retrieve_console_password
  retrieve_enc_password
  retrieve_tfe_initial_admin_password

  # generate Replicated configuration file
  # https://help.replicated.com/docs/native/customer-installations/automating/
  echo "INFO: Generating $REPL_CONF_PATH file."
  cat > $REPL_CONF_PATH << EOF
{
  "DaemonAuthenticationType": "password",
  "DaemonAuthenticationPassword": "$CONSOLE_PASSWORD",
  "ImportSettingsFrom": "$TFE_SETTINGS_PATH",
%{ if airgap_install == true ~}
  "LicenseBootstrapAirgapPackagePath": "$TFE_AIRGAP_PATH",
%{ endif ~}
  "LicenseFileLocation": "$TFE_LICENSE_PATH",
  "TlsBootstrapType": "${tls_bootstrap_type}",
  "TlsBootstrapHostname": "${tfe_hostname}",
%{ if tls_bootstrap_type == "server-path" ~}
  "TlsBootstrapCert": "${tls_bootstrap_cert}",
  "TlsBootstrapKey": "${tls_bootstrap_key}",
%{ endif ~}
  "RemoveImportSettingsFrom": ${remove_import_settings_from},
  "BypassPreflightChecks": true
}
EOF

  # generate TFE application settings file
  # https://www.terraform.io/docs/enterprise/install/automating-the-installer.html#available-settings
  echo "INFO: Generating $TFE_SETTINGS_PATH file."
  cat > $TFE_SETTINGS_PATH << EOF
{
    "aws_access_key_id": {},
    "aws_instance_profile": {
        "value": "1"
    },
    "aws_secret_access_key": {},
    "azure_account_key": {},
    "azure_account_name": {},
    "azure_container": {},
    "azure_endpoint": {},
    "backup_token": {},
    "ca_certs": {},
    "capacity_concurrency": {
        "value": "${capacity_concurrency}"
    },
    "capacity_memory": {
        "value": "${capacity_memory}"
    },
    "tbw_image": {
        "value": "custom_image"
    },
    "custom_image_tag": {
      "value": "${custom_image_tag}"
    },
    "disk_path": {},
    "enable_metrics_collection": {
        "value": "1"
    },
    "enc_password": {
        "value": "$ENC_PASSWORD"
    },
    "extern_vault_addr": {},
    "extern_vault_enable": {
        "value": "0"
    },
    "extern_vault_path": {},
    "extern_vault_propagate": {},
    "extern_vault_role_id": {},
    "extern_vault_secret_id": {},
    "extern_vault_token_renew": {},
    "extra_no_proxy": {},
    "gcs_bucket": {},
    "gcs_credentials": {},
    "gcs_project": {},
    "hostname": {
        "value": "${tfe_hostname}"
    },
    "iact_subnet_list": {},
    "iact_subnet_time_limit": {
        "value": "60"
    },
    "installation_type": {
        "value": "production"
    },
    "pg_dbname": {
        "value": "${pg_dbname}"
    },
    "pg_extra_params": {
        "value": "sslmode=require"
    },
    "pg_netloc": {
        "value": "${pg_netloc}"
    },
    "pg_password": {
        "value": "${pg_password}"
    },
    "pg_user": {
        "value": "${pg_user}"
    },
    "placement": {
        "value": "placement_s3"
    },
    "production_type": {
        "value": "external"
    },
    "s3_bucket": {
        "value": "${s3_app_bucket_name}"
    },
    "s3_endpoint": {},
    "s3_region": {
        "value": "${s3_app_bucket_region}"
    },%{ if kms_key_arn != "" }
    "s3_sse": {
        "value": "aws:kms"
    },
    "s3_sse_kms_key_id": {
        "value": "${kms_key_arn}"
    },%{ else }
    "s3_sse": {},
    "s3_sse_kms_key_id": {},%{ endif }
    "tls_vers": {
        "value": "tls_1_2_tls_1_3"
    }
}
EOF

  # execute the TFE installer script
  # TODO: add in logic to optionally support http-proxy
  cd $TFE_INSTALLER_DIR
  if [[ "${airgap_install}" == "true" ]]; then
    
    # start Docker
    echo "INFO: Starting docker service."
    sudo systemctl start docker.service

    # unzip Replicated bundle and install with airgap flag
    echo "INFO: Extracting Replicated bundle for airgap install."
    tar xzf $REPL_BUNDLE_PATH -C $TFE_INSTALLER_DIR
    
    echo "INFO: Executing TFE install in airgap mode."
    bash ./install.sh \
      no-proxy \
      airgap \
      private-address=$EC2_PRIVATE_IP \
      public-address=$EC2_PRIVATE_IP
  
  else
    # install in online mode
    echo "INFO: Executing TFE install in online mode."
    bash ./install.sh \
      no-proxy \
      private-address=$EC2_PRIVATE_IP \
      public-address=$EC2_PRIVATE_IP
  fi

  # enable Docker
  echo "INFO: enabling docker service."
  sudo systemctl enable docker.service

  # sleep at beginning of TFE install
  echo "INFO: Sleeping for a minute while TFE initializes..."
  sleep 60

  # health check until app becomes ready
  echo "INFO: Beginning to poll TFE health check endpoint."
  while ! curl -ksfS --connect-timeout 5 https://$EC2_PRIVATE_IP/_health_check; do
    sleep 5
  done

  # evaluate inputs for advanced bootstrap
  if [[ "${tfe_initial_admin_username}" != "" ]] && [[ "${is_secondary}" == "false" ]]; then
    tfe_bootstrap_initial_admin_user
    
    if [[ "$IAUT" == "null" ]]; then
      echo "INFO: Detected Initial Admin User Token (IAUT) has already been used."
      exit_script 0
    
    else
      if [[ "${tfe_initial_org_name}" != "" ]]; then
        tfe_bootstrap_initial_organization
        exit_script 0
      else
        exit_script 0
      fi
    fi

  else
    exit_script 0
  fi
} # end of main() function


# main script entrypoint
main "$@"