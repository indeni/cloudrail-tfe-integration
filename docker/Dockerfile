# This Dockerfile builds the image used for the worker containers.
#FROM ubuntu:focal
FROM swinkler/indeni-derived:latest
# Inject the ssl certificates (If i had any)
#ADD ca-certificates.crt /etc/ssl/certs/ca-certificates.crt

# Install software used by TFE
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo unzip daemontools git-core ssh wget curl psmisc iproute2 openssh-client redis-tools netcat-openbsd
    
# Install other software
RUN apt-get install -y jq
RUN apt-get update
RUN apt install -y ca-certificates

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && ./aws/install

# Install pip3
RUN apt-get update && apt-get -y install python3-pip

ADD finalize_custom_worker.sh /usr/local/bin/finalize_custom_worker.sh