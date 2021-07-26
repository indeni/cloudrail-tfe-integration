# This Dockerfile builds the image used for the worker containers.
FROM ubuntu:focal

# Install software used by Terraform Enterprise.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    sudo unzip daemontools git-core awscli ssh wget curl psmisc iproute2 openssh-client redis-tools netcat-openbsd ca-certificates

# Install cloudrail
RUN apt-get install python3-pip -y
RUN pip3 install cloudrail

# Include all necessary CA certificates. (if using)
#ADD example-root-ca.crt /usr/local/share/ca-certificates/
#ADD example-intermediate-ca.crt /usr/local/share/ca-certificates/

# Update the CA certificates bundle to include newly added CA certificates.
#RUN update-ca-certificates

ADD finalize_custom_worker.sh /usr/local/bin/finalize_custom_worker.sh