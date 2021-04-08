FROM ubuntu:20.04 as files
COPY ./cli /cloudrail/cli
COPY ./cloud_rail/utils /cloudrail/cloud_rail/utils
COPY ./cloud_rail/api/dtos /cloudrail/cloud_rail/api/dtos
COPY ./cloud_rail/api/handshake_version /cloudrail/cloud_rail/api/
COPY ./cloud_rail/environment_context/common /cloudrail/cloud_rail/environment_context/common
COPY ./cloud_rail/rules/checkov /cloudrail/cloud_rail/rules/checkov
RUN chmod +x /cloudrail/cli/cloudrail
## ------------------------------------------------------------------------------
FROM swinkler/indeni-base:latest as release
## ------------------------------------------------------------------------------
ARG CLI_VERSION
ENV PYTHONPATH "/cloudrail"
ENV CLOUDRAIL_CONFIG_PATH "/indeni/.cloudrail/config"
COPY cli.docker-entrypoint.sh /docker-entrypoint.sh
COPY --chown=indeni:indeni --from=files /cloudrail /cloudrail
RUN pip install -r /cloudrail/cli/requirements.txt \
  && echo "__version__ = '${CLI_VERSION}'" > /cloudrail/cli/_version.py \
  && mv /cloudrail/cli/cloudrail /usr/local/bin/cloudrail
#USER indeni

#ENV HOME /indeni
#WORKDIR /
#ENTRYPOINT ["/docker-entrypoint.sh"]
#CMD ["--help"]