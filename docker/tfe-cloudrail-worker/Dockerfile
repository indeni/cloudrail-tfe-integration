# This Dockerfile builds the image used for the worker containers.
# https://www.terraform.io/docs/enterprise/install/installer.html
# 
FROM ubuntu:focal

# Pull in private CA in PEM format, add it to trusted certs, update by calling update-ca-certificates
RUN mkdir -p /usr/share/ca-certificates/extra && \
  echo "extra/ca-certificates.crt" >> /etc/ca-certificates.conf
ADD ca-certificates.crt /usr/share/ca-certificates/extra/ca-certificates.crt

# Install software used by Terraform Enterprise.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    sudo unzip daemontools git-core awscli ssh wget curl psmisc iproute2 openssh-client redis-tools netcat-openbsd ca-certificates jq pip

# Run update-ca-certificates to rebuild /etc/ssl/certs/ca-certificates.crt
RUN update-ca-certificates

#Change shell to have source command available and install Cloudrail
SHELL ["/bin/bash", "-c"] 
RUN pip install virtualenv
RUN virtualenv cloudrail
RUN source cloudrail/bin/activate
RUN pip install cloudrail 

#This script, and all commands it invokes, will be executed before a Terraform Enterprise run executes terraform init. This initialize script will be executed during both plans and applies.
ADD init_custom_worker.sh /usr/local/bin/init_custom_worker.sh

#This script, and all commands it invokes, will be executed after a Terraform Enterprise run finishes executing terraform plan or terraform apply. This finalize script will be executed during both plans and applies.
ADD finalize_custom_worker.sh /usr/local/bin/finalize_custom_worker.sh